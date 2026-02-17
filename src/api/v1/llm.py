from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import hashlib
import time

from src.services.model_registry import get_db
from src.services.llm_gateway import LLMGateway

router = APIRouter()

# --- Pydantic Schemas ---

class CompletionRequest(BaseModel):
    model: str = Field(..., description="モデル名")
    prompt: str = Field(..., description="プロンプト")
    max_tokens: int = Field(100, description="最大トークン数")
    temperature: float = Field(0.7, description="温度パラメータ")

class ChatMessage(BaseModel):
    role: str = Field(..., description="ロール (user, system, assistant)")
    content: str = Field(..., description="メッセージ内容")

class ChatRequest(BaseModel):
    model: str = Field(..., description="モデル名")
    messages: List[ChatMessage] = Field(..., description="チャットメッセージ履歴")
    system_prompt: Optional[str] = Field(None, description="システムプロンプト")

class EmbeddingRequest(BaseModel):
    model: str = Field(..., description="モデル名")
    text: str = Field(..., description="テキスト")

class FineTuneJobRequest(BaseModel):
    base_model: str = Field(..., description="ベースモデル")
    training_file_id: str = Field(..., description="学習ファイルID")
    hyperparams: Optional[Dict[str, Any]] = Field(None, description="ハイパーパラメータ")

class FineTuneJobResponse(BaseModel):
    id: str
    status: str
    base_model: str
    created_at: int

    model_config = ConfigDict(from_attributes=True)

# --- Dependencies ---

def get_gateway(db: AsyncSession = Depends(get_db)):
    return LLMGateway(db)

# --- Endpoints ---

@router.post("/llm/completions")
async def create_completion(
    request: CompletionRequest,
    gateway: LLMGateway = Depends(get_gateway)
):
    """
    テキスト補完を生成します。
    """
    # レート制限 (User IDは仮)
    user_id = "test_user"
    if not await gateway.apply_rate_limit(user_id, request.model):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # キャッシュチェック
    cache_key = hashlib.md5(f"{request.model}:{request.prompt}".encode()).hexdigest()
    cached = await gateway.get_cached_response(cache_key)
    if cached:
        return cached

    # リクエスト処理
    response = await gateway.route_request(
        model=request.model,
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    # ログ記録 (簡易計算)
    prompt_tokens = len(request.prompt.split())
    # completion_tokens is dummy 10 in gateway
    completion_tokens = 10
    cost = (prompt_tokens + completion_tokens) * 0.00002 # dummy cost

    await gateway.log_usage(
        model=request.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        latency_ms=100 # dummy
    )

    # キャッシュ保存
    await gateway.cache_response(cache_key, response)

    return response

@router.post("/llm/chat")
async def create_chat_completion(
    request: ChatRequest,
    gateway: LLMGateway = Depends(get_gateway)
):
    """
    チャット応答を生成します。
    """
    # 簡易実装: Chatメッセージをプロンプトに変換してroute_requestに投げる
    prompt = ""
    if request.system_prompt:
        prompt += f"System: {request.system_prompt}\n"
    for msg in request.messages:
        prompt += f"{msg.role}: {msg.content}\n"

    return await gateway.route_request(request.model, prompt)

@router.post("/llm/embeddings")
async def create_embeddings(
    request: EmbeddingRequest,
    gateway: LLMGateway = Depends(get_gateway)
):
    """
    テキスト埋め込みを生成します。
    """
    # Embedding専用の処理が必要だが、ここではモック
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3], # dummy
                "index": 0
            }
        ],
        "model": request.model,
        "usage": {
            "prompt_tokens": len(request.text.split()),
            "total_tokens": len(request.text.split())
        }
    }

@router.post("/llm/fine-tune/jobs", response_model=FineTuneJobResponse)
async def create_fine_tune_job(
    request: FineTuneJobRequest,
    gateway: LLMGateway = Depends(get_gateway)
):
    """
    ファインチューニングジョブを作成します。
    """
    # ジョブ作成ロジック (Mock)
    return {
        "id": f"ft-{int(time.time())}",
        "status": "pending",
        "base_model": request.base_model,
        "created_at": int(time.time())
    }

@router.get("/llm/fine-tune/jobs/{job_id}", response_model=FineTuneJobResponse)
async def get_fine_tune_job(
    job_id: str,
    gateway: LLMGateway = Depends(get_gateway)
):
    """
    ファインチューニングジョブの状態を取得します。
    """
    return {
        "id": job_id,
        "status": "running",
        "base_model": "gpt-3.5-turbo",
        "created_at": int(time.time()) - 100
    }
