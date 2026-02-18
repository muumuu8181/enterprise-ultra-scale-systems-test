import math
from typing import Dict, List, Optional, Tuple

class GLOSACalculator:
    """
    GLOSA (Green Light Optimal Speed Advisory) 計算クラス
    信号機の状況に合わせて車両の推奨速度を計算し、停止回数を減らすことを目的とする。
    """

    def __init__(self, max_speed_limit: float = 16.6):
        """
        Args:
            max_speed_limit (float): 道路の制限速度 (m/s). デフォルトは60km/h
        """
        self.max_speed_limit = max_speed_limit

    def calculate_advisory_speed(
        self,
        distance_to_intersection: float,
        current_speed: float,
        signal_phase: str,
        time_to_change: float
    ) -> float:
        """
        推奨速度を計算する。

        Args:
            distance_to_intersection (float): 交差点までの距離 (m)
            current_speed (float): 現在の速度 (m/s)
            signal_phase (str): 現在の信号フェーズ ("RED", "GREEN", "YELLOW")
            time_to_change (float): 次のフェーズまでの時間 (秒)

        Returns:
            float: 推奨速度 (m/s)。計算不能または停止推奨の場合は0.0または適切な減速値を返す。
        """
        if distance_to_intersection <= 0:
            return current_speed

        if signal_phase == "RED":
            # 赤信号の場合、青になるタイミングに合わせて到着するように速度調整
            # target_time = time_to_change (青になるまでの時間)
            if time_to_change <= 0:
                return current_speed # すぐ変わるなら現状維持(あるいは安全確認)

            target_speed = distance_to_intersection / time_to_change

            # 制限速度を超えない範囲で
            return min(target_speed, self.max_speed_limit)

        elif signal_phase == "GREEN":
            # 青信号の場合、赤になる前に通過できるか判定
            time_to_arrive = distance_to_intersection / max(current_speed, 0.1) # 0除算防止

            if time_to_arrive < time_to_change:
                # 現在速度で通過可能なら、制限速度内で維持または加速
                return min(max(current_speed, self.max_speed_limit), self.max_speed_limit)
            else:
                # 通過不能なら、次の青まで待つ必要があるが、ここでは単純に減速指示等は複雑になるため
                # "停止準備"として、緩やかな減速を促すロジック等が考えられる
                # 簡易的に、現在は無理しない速度(または次のサイクル計算が必要)を返す
                # ここでは安全のため徐行を返す例とする
                return 0.0

        elif signal_phase == "YELLOW":
            # 黄色は停止推奨
            return 0.0

        return current_speed

    def predict_phase_transition(self, current_phase: str, timing_info: Dict) -> str:
        """
        次フェーズを予測する (簡易実装)。

        Args:
            current_phase (str): 現在のフェーズ
            timing_info (Dict): タイミング情報 (例: {"RED": 30, "GREEN": 30, "YELLOW": 3})

        Returns:
            str: 次のフェーズ
        """
        sequence = ["GREEN", "YELLOW", "RED"]
        try:
            current_idx = sequence.index(current_phase)
            next_idx = (current_idx + 1) % len(sequence)
            return sequence[next_idx]
        except ValueError:
            return "UNKNOWN"

    def get_optimal_speed_profile(
        self,
        distance: float,
        start_speed: float,
        target_speed: float
    ) -> List[float]:
        """
        最適速度プロファイルを生成する (加速度制約考慮)。
        簡易的に、一定加速度で目標速度へ遷移するプロファイルを返す。

        Args:
            distance (float): 距離 (m)
            start_speed (float): 初速 (m/s)
            target_speed (float): 目標速度 (m/s)

        Returns:
            List[float]: 時間ステップごとの速度リスト (1秒刻み)
        """
        profile = []
        current_s = start_speed
        accel = 1.0 if target_speed > start_speed else -1.0

        # 目標速度に達するまで
        while (accel > 0 and current_s < target_speed) or (accel < 0 and current_s > target_speed):
            current_s += accel
            if (accel > 0 and current_s > target_speed) or (accel < 0 and current_s < target_speed):
                current_s = target_speed
            profile.append(current_s)

        # 残りの距離分(簡易計算)などを考慮すべきだが、ここでは速度遷移のみ返す
        return profile
