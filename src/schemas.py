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

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class GuestLoginRequest(BaseModel):
    device_id: str
    fcm_token: str = "dummy_token"
    platform: str = "ios"

class LinkAccountRequest(BaseModel):
    email: str
    password: str
