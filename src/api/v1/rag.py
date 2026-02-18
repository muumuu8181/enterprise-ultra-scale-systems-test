from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field

from src.models.rag_models import Document
from src.services.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/rag", tags=["rag"])

# サービスインスタンス (シングルトンとして扱うか、Dependsで注入)
# Service instance
pipeline = RAGPipeline()

# データベース依存関係 (仮実装)
# Database dependency (Stub)
async def get_db() -> AsyncSession: # type: ignore
    """
    データベースセッションを取得する依存関係。
    実際の実装では、sessionmakerからセッションを生成してyieldします。
    テスト時にオーバーライドされます。
    """
    yield None

# --- Pydantic Models ---

class IngestRequest(BaseModel):
    title: str = Field(..., description="文書のタイトル")
    text: str = Field(..., description="文書のテキスト内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ (JSON)")
    source_url: Optional[str] = Field(None, description="ソースURL")
    chunk_size: int = Field(512, description="チャンクサイズ")

class DocumentResponse(BaseModel):
    id: int
    title: str
    chunk_count: int
    ingested_at: datetime
    source_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class QueryRequest(BaseModel):
    question: str = Field(..., description="質問内容")
    top_k: int = Field(5, description="検索する上位チャンク数")
    llm_model: str = Field("gpt-3.5-turbo", description="使用するLLMモデル")

class QueryResponse(BaseModel):
    answer: str
    relevant_chunks: List[str]

# --- Endpoints ---

@router.post("/documents/ingest", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(req: IngestRequest, db: AsyncSession = Depends(get_db)):
    """
    文書を取り込み、チャンク化・埋め込み・保存を行います。
    Ingests a document, chunks/embeds it, and saves it.
    """
    doc = await pipeline.ingest_document(
        session=db,
        title=req.title,
        text=req.text,
        metadata=req.metadata,
        source_url=req.source_url,
        chunk_size=req.chunk_size
    )
    return doc

@router.post("/query", response_model=QueryResponse)
async def query_rag(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    RAGを使用して質問に回答します。
    Answers a question using RAG.
    """
    # 1. 検索
    chunks = await pipeline.retrieve(db, req.question, req.top_k)

    # 2. 生成
    answer = await pipeline.generate(req.question, chunks, req.llm_model)

    return QueryResponse(
        answer=answer,
        relevant_chunks=[c.text for c in chunks]
    )

@router.get("/documents/{id}", response_model=DocumentResponse)
async def get_document(id: int, db: AsyncSession = Depends(get_db)):
    """
    文書情報を取得します。
    Retrieves document information.
    """
    doc = await db.get(Document, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/documents/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(id: int, db: AsyncSession = Depends(get_db)):
    """
    文書を削除します。
    Deletes a document.
    """
    doc = await db.get(Document, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    return None
