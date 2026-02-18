from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class GachaPullRequest(BaseModel):
    banner_id: int
    count: int = 1  # 1 or 10

class GachaResultItem(BaseModel):
    item_id: str
    rarity: int
    is_pickup: bool

class GachaPullResponse(BaseModel):
    results: List[GachaResultItem]
    currency_remaining: int

class GachaBannerResponse(BaseModel):
    id: int
    name: str
    start_time: datetime
    end_time: datetime

class GachaLogResponse(BaseModel):
    id: int
    item_id: str
    rarity: int
    created_at: datetime

class EventResponse(BaseModel):
    id: int
    name: str
    start_time: datetime
    end_time: datetime

class EventPlayRequest(BaseModel):
    points: int

class EventRankingItem(BaseModel):
    user_id: int
    score: int
    rank: int

class PurchaseVerifyRequest(BaseModel):
    receipt_id: str
    receipt_data: str
    platform: str # 'ios' or 'android'
    amount: int # In real app, amount comes from receipt validation
    currency_to_add: int

class PurchaseVerifyResponse(BaseModel):
    success: bool
    currency_added: int
    current_balance: int

# Guild Schemas

class GuildCreate(BaseModel):
    """
    ギルド作成リクエスト
    """
    name: str
    description: Optional[str] = None
    max_members: int = 10

class GuildResponse(BaseModel):
    """
    ギルド情報レスポンス
    """
    id: int
    name: str
    description: Optional[str]
    leader_id: int
    level: int
    exp: int
    members_count: int
    max_members: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GuildMemberResponse(BaseModel):
    """
    ギルドメンバー情報レスポンス
    """
    id: int
    guild_id: int
    user_id: int
    role: str
    joined_at: datetime
    contribution_points: int
    model_config = ConfigDict(from_attributes=True)

class GuildBattleCreate(BaseModel):
    """
    ギルドバトル開始リクエスト
    """
    opponent_guild_id: int

class GuildBattleResponse(BaseModel):
    """
    ギルドバトル情報レスポンス
    """
    id: int
    guild_a_id: int
    guild_b_id: int
    winner_id: Optional[int]
    started_at: datetime
    ended_at: Optional[datetime]
    scores: Optional[dict]
    model_config = ConfigDict(from_attributes=True)
