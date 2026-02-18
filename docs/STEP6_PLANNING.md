# STEP 6: 経路計画・協調走行制御 (STEP6_PLANNING.md)

## 1. 概要
経路計画モジュールは、Perception結果、HD Map、V2X情報に基づき、安全かつ効率的な走行軌道 (Trajectory) を生成する。グローバル経路計画 (Global Planning)、行動計画 (Behavior Planning)、ローカル経路計画 (Local Planning) の3層構造を採用し、車両運動制御 (Vehicle Control) へ指令を送る。

## 2. 計画アルゴリズム

### 2.1 Global Planning
*   **アルゴリズム**: A* (A-Star) または Dijkstra。
*   **データ構造**: Lanelet2 Routing Graph。
*   **出力**: Lanelet IDのシーケンス (Waypoint)。

### 2.2 Behavior Planning
*   **アルゴリズム**: 有限ステートマシン (FSM: Finite State Machine) または MPDM (Multiple Policy Decision Making)。
*   **状態**: Lane Keeping, Lane Change Left/Right, Stop, Yield, Emergency Stop。
*   **機能**: 交通ルールの遵守、他車両との相互作用、車線変更の判断。

### 2.3 Local Planning
*   **アルゴリズム**: モデル予測制御 (MPC: Model Predictive Control) または Frenet Frameベースの最適化。
*   **評価関数**: 安全性 (障害物距離)、快適性 (ジャーク最小化)、効率性 (速度維持)、追従性 (中心線からの偏差)。
*   **制約条件**: 車両運動モデル (Kinematic Bicycle Model)、最大加速度、操舵角制限。

### 2.4 Cooperative Driving (協調走行)
*   **Platooning (隊列走行)**: CACC (Cooperative Adaptive Cruise Control) により、車間距離を短縮し空気抵抗を低減。
*   **Merge Coordination**: 合流部での譲り合い制御。
*   **Intersection Coordination**: 交差点通過順序の交渉。

## 3. クラス設計 (C++ Implementation)

### 3.1 MotionPlanner
計画・制御の統合管理クラス。

```cpp
#include <vector>
#include "types.hpp"
#include "mpc_solver.hpp"

class MotionPlanner {
public:
    MotionPlanner(const Config& config);

    // グローバル経路計画 (カーナビレベル)
    Trajectory planGlobalRoute(const Pose& start, const Pose& goal) {
        // A* Search on Lanelet2 Graph
        auto route = routing_engine_.route(start, goal);
        return convertRouteToTrajectory(route);
    }

    // ローカル軌道生成 (制御入力レベル)
    Trajectory planLocalTrajectory(const EgoState& ego, const ObjectList& obstacles) {
        // 1. Prediction: 障害物の未来位置予測
        // 2. Behavior Selection: 車線変更するか維持するか
        // 3. Trajectory Generation: 候補軌道の生成 (Polynomial Spirals)
        // 4. Evaluation: コスト関数による最適軌道選択

        BehaviorState behavior = decideBehavior(current_context_);
        Trajectory ref_traj = generateReference(behavior);

        ControlCommand cmd = computeMPCControl(ref_traj, ego);
        return ref_traj; // For visualization
    }

    // 行動決定 (FSM)
    BehaviorState decideBehavior(const SituationContext& context) {
        // State Machine Update
        // e.g., if (obstacle_ahead && gap_available) -> LaneChange
        return current_behavior_state_;
    }

    // MPCによる制御指令計算
    ControlCommand computeMPCControl(const Trajectory& ref, const EgoState& current) {
        // Solve QP (Quadratic Programming) problem
        // Minimize: (x - x_ref)^2 + (v - v_ref)^2 + u^2 + du^2
        // Subject to: x(k+1) = f(x(k), u(k)), u_min < u < u_max

        MPCSolution sol = mpc_solver_.solve(current, ref);
        return ControlCommand(sol.steering_angle, sol.acceleration);
    }

    // 軌道の物理的実現可能性チェック
    bool checkTrajectoryFeasibility(const Trajectory& traj, const VehicleModel& model) {
        // Check curvature, max acceleration, collision
        for (const auto& point : traj) {
            if (abs(point.curvature) > model.max_curvature) return false;
            if (isColliding(point, obstacles_)) return false;
        }
        return true;
    }

    // 緊急停止 (ASIL-D)
    void performEmergencyStop(EmergencyStopReason reason) {
        // Maximum deceleration
        control_interface_.sendBrakeCommand(1.0); // 100% Brake
        hazard_lights_.activate();
        logError("Emergency Stop Triggered: " + toString(reason));
    }

    // TTC (Time-To-Collision) 計算
    float computeTTC(const TrackedObject& obstacle) {
        float rel_speed = current_speed_ - obstacle.velocity.x;
        if (rel_speed <= 0) return std::numeric_limits<float>::infinity();
        return (obstacle.position.x - current_position_.x) / rel_speed;
    }

    // THW (Time Headway) 計算
    float computeTHW(const TrackedObject& lead) {
        if (current_speed_ <= 0.1) return std::numeric_limits<float>::infinity();
        return (lead.position.x - current_position_.x) / current_speed_;
    }

private:
    RoutingEngine routing_engine_;
    MPCSolver mpc_solver_;
    VehicleModel vehicle_model_;
    BehaviorState current_behavior_state_;
};
```

### 3.2 CooperativeDrivingManager
V2X通信を用いた協調走行管理クラス。

```cpp
class CooperativeDrivingManager {
public:
    // 隊列への参加
    void joinPlatoon(PlatoonID id, PlatoonRole role) {
        // Request specific gap and position
        sendJoinRequest(id);
        current_platoon_role_ = role; // LEADER / FOLLOWER
    }

    // 車線変更の協調 (Negotiation)
    void negotiateLaneChange(const LaneChangeRequest& req, const V2XNeighborList& neighbors) {
        // Send "Lane Change Request" via V2V
        // Wait for "Ack" or "Nack"
        if (allNeighborsAccepted(req)) {
            planner_->executeLaneChange();
        } else {
            planner_->abortLaneChange();
        }
    }

    // 自車の意図配信
    void broadcastIntention(const DrivingIntention& intention) {
        // Create V2X message (MCM: Maneuver Coordination Message)
        // Send via C-V2X
    }

    // 協調認識メッセージ (CPM) の受信
    void receiveCooperativePerception(const CPM& cpm) {
        // Update local world model with remote sensor data
        fusion_engine_->addRemoteObjects(cpm.objects);
    }

    PlatoonState getPlatoonState() const;

    // 隊列解散
    void disbandPlatoon(DisconnectReason reason) {
        sendDisbandRequest();
        mode_ = DrivingMode::AUTONOMOUS;
    }

private:
    V2XInterface* v2x_interface_;
    MotionPlanner* planner_;
};
```

## 4. 安全設計 (Functional Safety)

### 4.1 冗長化
*   **プランナー冗長化**: メインプランナー (MLベース) と安全プランナー (ルールベース) の並列実行。
*   **チェッカー**: メインプランナーの出力が安全範囲内かを常に監視 (Safety Cage)。

### 4.2 フェイルセーフ (Fail-Safe)
*   **MRM (Minimum Risk Maneuver)**: システム故障時、路肩へ安全に停止する制御。
*   **Degraded Mode**: センサー故障時、最高速度を制限して走行継続、または徐行運転へ移行。
