import time
import os
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import create_engine, text
from redis import Redis

router = APIRouter()

@router.get("/health")
def health_check():
    health_status = {"status": "ok", "db": "unknown", "redis": "unknown", "latency": {}}

    # DB接続確認
    db_start = time.time()
    try:
        # 環境変数またはデフォルトを使用
        db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        health_status["db"] = "ok"
    except Exception as e:
        health_status["db"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    finally:
        health_status["latency"]["db"] = time.time() - db_start

    # Redis接続確認
    redis_start = time.time()
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        r = Redis(host=redis_host, port=redis_port, socket_connect_timeout=1)
        if r.ping():
            health_status["redis"] = "ok"
        else:
             health_status["redis"] = "failed"
             health_status["status"] = "degraded"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    finally:
        health_status["latency"]["redis"] = time.time() - redis_start

    return health_status

@router.get("/metrics")
def metrics():
    # Prometheus形式のメトリクスを返す
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
