from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from src.models.ml_models import Base

def utc_now():
    return datetime.now(timezone.utc)

class LLMUsageLog(Base):
    """
    LLM使用ログ (LLM Usage Log)

    属性:
        id: ログID
        model: 使用モデル名
        prompt_tokens: プロンプトトークン数
        completion_tokens: 生成トークン数
        cost_usd: コスト (USD)
        latency_ms: レイテンシ (ミリ秒)
        created_at: 作成日時
    """
    __tablename__ = "llm_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model: Mapped[str] = mapped_column(String, index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    completion_tokens: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
