# STEP 7: 交差点管理・衝突回避 (STEP7_INTERSECTION.md)

## 1. 概要
交差点は自動運転における最大のボトルネックかつ危険箇所である。本システムでは、信号機情報 (SPAT) と地図情報 (MAP) を活用した信号協調走行 (GLOSA) と、車両間通信 (V2V) による自律的調停 (AIM: Autonomous Intersection Management) を実装し、交差点通過効率と安全性を最大化する。

## 2. 交差点管理システム

### 2.1 GLOSA (Green Light Optimal Speed Advisory)
*   **目的**: 赤信号停止を回避し、燃料消費と排出ガスを削減。
*   **入力**: RSUからのSPAT (信号フェーズ・残り時間) とMAP (交差点形状)。
*   **出力**: 推奨通過速度。

### 2.2 AIM (Autonomous Intersection Management)
*   **Reservation-based**: 車両が交差点内の時空間スロット (Time-Space Slot) を予約。
*   **Trajectory Optimization**: 予約スロットに合わせて加減速を調整。
*   **Fallback**: 通信途絶時は通常の信号ルールまたは一時停止ルールに従う。

## 3. クラス設計 (Python Implementation)

### 3.1 IntersectionManager
交差点への接近、通過、予約を管理する。

```python
from typing import List, Optional
from .v2x_types import SPATMessage, MAPMessage, SlotAllocation

class IntersectionManager:
    def __init__(self):
        self.current_phase = None
        self.next_phase_time = 0.0

    def process_spat_message(self, spat: SPATMessage, intersection_id: int) -> 'PhaseState':
        """信号情報の更新"""
        phase = spat.intersections[intersection_id].states[0]
        self.current_phase = phase.event_state # red/green/yellow
        self.next_phase_time = phase.min_end_time
        return self.current_phase

    def calculate_glosa_speed(self, distance_m: float, phase: 'PhaseState') -> float:
        """青信号で通過するための最適速度を計算"""
        if phase == 'green':
            # そのまま通過できるか？
            if distance_m / self.current_speed < self.next_phase_time:
                return self.current_speed # Maintain
            else:
                return 0.0 # Prepare to stop (or coasting)
        elif phase == 'red':
            time_to_green = self.next_phase_time
            return distance_m / time_to_green # Target speed to arrive at green
        return 0.0

    def request_intersection_slot(self, ego: 'EgoState', eta: float) -> Optional[SlotAllocation]:
        """交差点予約リクエスト (V2I)"""
        req = SlotRequest(ego.id, eta, ego.trajectory)
        response = self.v2x_client.send_request(req)

        if response.granted:
            return response.allocation
        else:
            return None # Must retry or slow down

    def predict_intersection_conflicts(self, trajectories: List['Trajectory']) -> List['Conflict']:
        """他車両の軌道との交差判定"""
        conflicts = []
        for t1 in trajectories:
            if self.check_collision(self.ego_traj, t1):
                conflicts.append(Conflict(t1, time_to_collision))
        return conflicts

    def coordinate_emergency_vehicle(self, ev_request: 'EmergencyVehicleRequest') -> 'PreemptionPlan':
        """緊急車両接近時の優先制御"""
        # Yield to EV
        if ev_request.priority > self.priority:
            return PreemptionPlan(action='pull_over')
        return PreemptionPlan(action='maintain')

    def manage_merging_zone(self, zone: 'MergingZone', vehicles: List['Vehicle']) -> 'MergeSchedule':
        """合流部でのジッパー合流制御"""
        # Assign order based on distance to merge point
        sorted_vehicles = sorted(vehicles, key=lambda v: v.dist_to_merge)
        return MergeSchedule(order=sorted_vehicles)

    def compute_arrival_time_window(self, distance: float, speed: float) -> 'TimeWindow':
        """到着予想時間の幅 (不確実性考慮)"""
        t_min = distance / (speed * 1.1)
        t_max = distance / (speed * 0.9)
        return TimeWindow(start=t_min, end=t_max)
```

### 3.2 CollisionAvoidanceSystem
衝突回避のための安全監視システム。

```python
class CollisionAvoidanceSystem:
    def __init__(self):
        self.active = True

    def compute_collision_probability(self, ego: 'EgoState', obstacle: 'TrackedObject') -> float:
        """衝突確率の計算 (モンテカルロ法またはカルマンフィルタ共分散)"""
        # Integrate overlapping PDF of ego and obstacle
        prob = self.calculate_overlap(ego.prediction, obstacle.prediction)
        return prob

    def generate_evasive_maneuver(self, collision_risk: 'CollisionRisk') -> 'ControlCommand':
        """回避行動の生成"""
        if collision_risk.ttc < 1.0:
             # Full braking
             return ControlCommand(brake=1.0, steer=0.0)
        elif collision_risk.ttc < 2.5:
             # Steering avoidance if clear
             if self.check_lane_free(left=True):
                 return ControlCommand(steer=-0.5)
             else:
                 return ControlCommand(brake=0.5)
        return ControlCommand()

    def activate_autonomous_emergency_braking(self, ttc: float, deceleration: float):
        """AEB (自動緊急ブレーキ) の作動"""
        if ttc < self.AEB_THRESHOLD:
            self.brakes.apply_max_force()
            self.alert_driver("COLLISION WARNING")

    def post_crash_notification(self, crash_data: 'CrashData') -> None:
        """eCall / ERA-GLONASS 自動通報"""
        # Send MSD (Minimum Set of Data) via Cellular
        msd = self.create_msd(crash_data)
        self.telematics.send_emergency_call(msd)
```

## 4. シナリオ対応

### 4.1 右折 (Right Turn)
*   **課題**: 対向直進車の速度・距離推定の難しさ。
*   **対策**: RSUからの対向車情報 (CPM) を利用し、死角を補完。ギャップアクセプタンス (Gap Acceptance) ロジックで安全なタイミングを判定。

### 4.2 無信号交差点
*   **ルール**: 優先道路、左方優先などを地図属性から取得。
*   **協調**: V2V通信で「お先にどうぞ (Handshake)」の意思疎通を行う。

### 4.3 ラウンドアバウト
*   **進入**: 環道内車両の優先。
*   **退出**: ウィンカー信号の認識と自車の意思表示。
