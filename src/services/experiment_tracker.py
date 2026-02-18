import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from src.models.ml_models import Experiment, Run

class ExperimentTracker:
    """
    実験トラッキングサービス
    Service for tracking experiments, runs, parameters, and metrics.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experiment(self, name: str, description: Optional[str] = None, tags: Optional[Dict[str, Any]] = None) -> Experiment:
        """
        実験を作成する
        Create a new experiment.
        """
        # 重複チェック
        stmt = select(Experiment).where(Experiment.name == name)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Experiment '{name}' already exists.")

        exp = Experiment(name=name, description=description, tags=tags)
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def start_run(self, experiment_id: int) -> Run:
        """
        Runを開始する (UUID生成)
        Start a new run for an experiment.
        """
        # 実験存在確認
        exp = await self.db.get(Experiment, experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found.")

        run_id = str(uuid.uuid4())
        run = Run(
            id=run_id,
            experiment_id=experiment_id,
            status="running",
            start_time=datetime.now(),
            params={},
            metrics={},
            artifacts={}
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def log_metrics(self, run_id: str, metrics: Dict[str, float]) -> Run:
        """
        メトリクスを記録する (数値バリデーション付き)
        Log metrics for a run. Validate that values are numbers.
        """
        run = await self.db.get(Run, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found.")

        if run.status != "running":
            raise ValueError("Cannot log metrics to a non-running run.")

        # バリデーション
        for k, v in metrics.items():
            if not isinstance(v, (int, float)):
                raise ValueError(f"Metric {k} must be a number.")

        # 既存メトリクスの更新 (Dictのコピーを作成して更新)
        current_metrics = dict(run.metrics) if run.metrics else {}
        current_metrics.update(metrics)

        # SQLAlchemyに変更を検知させるため再代入
        run.metrics = current_metrics

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def log_params(self, run_id: str, params: Dict[str, Any]) -> Run:
        """
        パラメータを記録する
        Log parameters for a run.
        """
        run = await self.db.get(Run, run_id)
        if not run:
             raise ValueError(f"Run {run_id} not found.")

        if run.status != "running":
            raise ValueError("Cannot log params to a non-running run.")

        current_params = dict(run.params) if run.params else {}
        current_params.update(params)

        run.params = current_params

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def finish_run(self, run_id: str, status: str = "completed") -> Run:
        """
        Runを完了する (duration計算、ベストモデル判定のための情報更新)
        Finish a run.
        """
        run = await self.db.get(Run, run_id)
        if not run:
             raise ValueError(f"Run {run_id} not found.")

        run.end_time = datetime.now()
        run.status = status

        # Durationは start_time と end_time から計算可能

        await self.db.commit()
        await self.db.refresh(run)

        return run

    async def get_runs(self, experiment_id: int, sort_by: str = "start_time", order: str = "desc") -> List[Run]:
        """
        Run一覧取得 (ソート対応)
        Get list of runs for an experiment.
        """
        stmt = select(Run).where(Run.experiment_id == experiment_id)

        # 簡易的なソート実装
        if sort_by == "start_time":
            if order == "desc":
                stmt = stmt.order_by(Run.start_time.desc())
            else:
                stmt = stmt.order_by(Run.start_time.asc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
