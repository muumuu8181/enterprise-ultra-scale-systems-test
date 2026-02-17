from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class SanctionsCheckResponse(BaseModel):
    """制裁リスト照合結果レスポンス"""
    id: int = Field(..., description="照合ID")
    customer_id: str = Field(..., description="顧客ID")
    status: str = Field(..., description="照合ステータス (CLEAR, MATCHED, PENDING)")
    matched_list: Optional[str] = Field(None, description="一致したリスト名")
    checked_at: datetime = Field(..., description="照合日時")

    model_config = ConfigDict(from_attributes=True)

class SARRequest(BaseModel):
    """SAR生成リクエスト"""
    customer_id: str = Field(..., description="顧客ID")
    transaction_ids: Optional[List[str]] = Field(None, description="対象取引IDリスト (オプション)")

class SARResponse(BaseModel):
    """SAR生成レスポンス"""
    id: int = Field(..., description="SAR ID")
    customer_id: str = Field(..., description="顧客ID")
    transactions: Dict[str, Any] = Field(..., description="関連取引データ")
    risk_indicators: List[str] = Field(..., description="検知されたリスク指標")
    submitted_at: datetime = Field(..., description="提出日時")

    model_config = ConfigDict(from_attributes=True)

class AMLScoreResponse(BaseModel):
    """AMLスコアレスポンス"""
    customer_id: str = Field(..., description="顧客ID")
    risk_score: float = Field(..., description="AMLリスクスコア (0.0 - 100.0)")
    risk_level: str = Field(..., description="リスクレベル (LOW, MEDIUM, HIGH)")
    analyzed_at: datetime = Field(..., description="分析日時")
