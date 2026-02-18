import math
import logging
import random
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.models.ml_models import MLModel
from src.models.monitoring_models import ModelAlert

logger = logging.getLogger(__name__)

class DriftDetector:
    """
    データドリフト検知サービス
    PSI (Population Stability Index) を計算し、共変量シフトを検知します。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_psi(self, expected_dist: List[float], actual_dist: List[float]) -> float:
        """
        PSI (Population Stability Index) を計算します。

        Args:
            expected_dist: 期待される分布（学習データなど）。確率のリスト（合計1.0）。
            actual_dist: 実際の分布（推論データなど）。確率のリスト（合計1.0）。

        Returns:
            float: PSI値
        """
        if len(expected_dist) != len(actual_dist):
            raise ValueError("Distributions must have the same number of buckets")

        psi_value = 0.0
        epsilon = 1e-10  # ゼロ除算防止用

        for expected_p, actual_p in zip(expected_dist, actual_dist):
            # 確率が0の場合の対策
            e = max(expected_p, epsilon)
            a = max(actual_p, epsilon)

            psi_value += (a - e) * math.log(a / e)

        return psi_value

    async def detect_covariate_drift(self, model_id: int) -> Tuple[float, bool]:
        """
        指定されたモデルのデータドリフトを検知します。
        現在はデータをモックしています。

        Returns:
            (psi, drift_detected): PSI値とドリフト検知フラグ(True/False)
        """
        # モデルの存在確認
        stmt = select(MLModel).where(MLModel.id == model_id)
        result = await self.db.execute(stmt)
        model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        # --- データ取得のモック ---
        # 実際には inference_logs テーブルなどからデータを集計して分布を作成する
        # ここではランダムな分布を生成してシミュレーションする

        # 期待される分布 (例: 10個のバケット)
        expected_dist = [0.1] * 10

        # 実際の分布 (ランダムに変動させる)
        # ドリフトをシミュレートするために少し偏らせる
        actual_raw = [random.random() for _ in range(10)]
        total = sum(actual_raw)
        actual_dist = [x / total for x in actual_raw]

        # PSI計算
        psi = self.calculate_psi(expected_dist, actual_dist)

        drift_detected = False
        if psi > 0.2:
            drift_detected = True
            await self.trigger_retraining(model_id)

        return psi, drift_detected

    async def trigger_retraining(self, model_id: int):
        """
        PSI > 0.2 の場合に自動再学習をトリガーします。
        """
        logger.info(f"Drift detected for model {model_id}. Triggering retraining...")

        # ここではログ出力とDB上のステータス更新のみを行う
        # 実際にはAirflow DAGのトリガーやMLパイプラインの実行を行う

        # アラートを記録する (オプション)
        # alert = ModelAlert(
        #     model_id=model_id,
        #     metric="psi",
        #     threshold=0.2,
        #     current_value=0.25, # 例
        #     triggered_at=datetime.now(timezone.utc)
        # )
        # self.db.add(alert)
        # await self.db.commit()

        pass

    async def generate_drift_report(self, model_id: int) -> Dict[str, Any]:
        """
        ドリフトレポートを生成します。
        """
        psi, drift_detected = await self.detect_covariate_drift(model_id)

        return {
            "model_id": model_id,
            "drift_detected": drift_detected,
            "psi_value": psi,
            "threshold": 0.2,
            "report_generated_at": datetime.now(timezone.utc).isoformat()
        }
