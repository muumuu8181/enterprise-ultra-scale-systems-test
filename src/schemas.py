from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

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

class FriendRequestCreate(BaseModel):
    target_user_id: int

class FriendRequestResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str
    created_at: datetime

class FriendResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime

class GiftSendRequest(BaseModel):
    friend_id: int
    item_id: str
    message: Optional[str] = None

class GiftResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    item_id: str
    message: Optional[str]
    sent_at: datetime

class FeedItem(BaseModel):
    type: str
    content: str
    created_at: datetime
