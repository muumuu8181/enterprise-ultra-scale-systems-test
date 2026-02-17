from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from sse_starlette.sse import EventSourceResponse
from src.services.training_orchestrator import TrainingOrchestrator

router = APIRouter()

# シングルトンとして扱うための簡易的な依存性注入
orchestrator = TrainingOrchestrator()

class TrainingJobCreate(BaseModel):
    dataset_path: str
    model_type: str
    hyperparams: Dict[str, Any]

class TrainingJobResponse(BaseModel):
    job_id: str
    status: str

@router.post("/jobs", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_training_job(job_data: TrainingJobCreate):
    """
    新しいトレーニングジョブを作成します。
    """
    job_id = await orchestrator.submit_job(
        dataset_path=job_data.dataset_path,
        model_type=job_data.model_type,
        hyperparams=job_data.hyperparams
    )
    return TrainingJobResponse(job_id=job_id, status="pending")

@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job_status(job_id: str):
    """
    ジョブの現在のステータスを取得します。
    """
    try:
        status_val = await orchestrator.monitor_job(job_id)
        return TrainingJobResponse(job_id=job_id, status=status_val)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_training_job(job_id: str):
    """
    実行中のジョブをキャンセルします（未実装）。
    """
    # 本来はorchestratorにcancelメソッドを実装して呼び出す
    try:
        # jobが存在するか確認
        await orchestrator.monitor_job(job_id)
        # キャンセル処理 (モック)
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/jobs/{job_id}/logs")
async def stream_training_logs(job_id: str):
    """
    ジョブのログをSSE (Server-Sent Events) でストリーミング配信します。
    """
    try:
        # ジョブの存在確認
        await orchestrator.monitor_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        # ログをポーリングして配信する簡易実装
        # 実際にはRedis Pub/SubやKafka、またはファイル末尾監視などを使用する
        logs_sent = 0
        while True:
            try:
                # Orchestratorの_jobsに直接アクセスするのは行儀が悪いが、
                # get_logsメソッドがイテレータではなくリストを返すように修正するか、
                # ここでうまく処理する必要がある。
                # サービスのget_logsはgeneratorとして実装したが、
                # 既存のログを全て返して終了してしまう。
                # SSEでは継続的に送る必要があるため、ここではポーリングを行う。

                # jobの状態を再取得
                current_status = await orchestrator.monitor_job(job_id)

                # サービスから全ログ取得 (実装依存: _jobsはpublicではないがアクセス可能)
                # 正しくは orchestrator に `get_new_logs(from_index)` のようなメソッドが必要
                # ここでは簡易的に全ログを取得し、差分を送る

                # サービスの get_logs は generator なので一度呼ぶと終わる。
                # 今回の要件ではSSEなので、常に新しいログを待ち受ける必要がある。

                # 簡易実装: 1秒ごとにチェック
                job = orchestrator._jobs.get(job_id) # 直接アクセス (デモ用)
                if not job:
                    break

                current_logs = job.get("logs", [])
                if len(current_logs) > logs_sent:
                    for log in current_logs[logs_sent:]:
                        yield {"data": log}
                    logs_sent = len(current_logs)

                if current_status in ["completed", "failed"]:
                    yield {"data": f"Job finished with status: {current_status}"}
                    break

                await asyncio.sleep(1)
            except Exception as e:
                yield {"event": "error", "data": str(e)}
                break

    return EventSourceResponse(event_generator())
