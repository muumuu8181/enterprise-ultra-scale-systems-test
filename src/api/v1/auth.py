from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from src.database import get_db
from src.models import Customer
from src.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    add_to_blacklist,
    is_token_blacklisted,
    RateLimiter
)
from src.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# レート制限の設定（例: 1分間に5回まで）
login_rate_limiter = RateLimiter(requests_limit=5, window_seconds=60)

class LoginRequest(BaseModel):
    customer_id: str = Field(..., description="顧客ID")
    pin: str = Field(..., description="暗証番号")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="リフレッシュトークン")

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="リフレッシュトークン（オプション）")

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    顧客IDとPINを使用してログインし、JWTトークンを発行します。
    """
    # レート制限チェック (IPアドレスベース)
    client_ip = request.client.host
    if not await login_rate_limiter.is_allowed(f"login:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="試行回数が制限を超えました。しばらく待ってから再試行してください。"
        )

    # 顧客の取得
    result = await db.execute(select(Customer).where(Customer.id == login_data.customer_id))
    customer = result.scalars().first()

    if not customer or not verify_password(login_data.pin, customer.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="顧客IDまたはPINが間違っています。",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="アカウントが無効です。"
        )

    # トークン生成
    access_token = create_access_token(data={"sub": customer.id})
    refresh_token = create_refresh_token(data={"sub": customer.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest
):
    """
    リフレッシュトークンを使用して新しいアクセストークンとリフレッシュトークンを発行します。
    古いリフレッシュトークンは無効化（ブラックリスト登録）されます。
    """
    token = refresh_data.refresh_token

    # ブラックリスト確認
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このリフレッシュトークンは既に使用済みか無効です。"
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです。"
        )

    customer_id = payload.get("sub")

    # トークンローテーション: 古いトークンをブラックリストに追加
    # 有効期限まで保持する必要があるため、expを取得して計算、あるいはデフォルト設定で追加
    exp = payload.get("exp") # timestamp
    current_ts = request.state.timestamp if hasattr(request.state, "timestamp") else None
    # 簡易的に、設定されたリフレッシュトークン期間分のTTLを設定
    # より厳密には exp - now だが、ここでは十分に長い時間を設定しておく
    await add_to_blacklist(token, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)

    # 新しいトークン生成
    new_access_token = create_access_token(data={"sub": customer_id})
    new_refresh_token = create_refresh_token(data={"sub": customer_id})

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    logout_data: Optional[LogoutRequest] = None
):
    """
    ログアウト処理を行います。現在のアクセストークンをブラックリストに追加します。
    リフレッシュトークンが提供された場合は、それもブラックリストに追加します。
    """
    # Middlewareで検証済みのアクセストークンを取得
    access_token = getattr(request.state, "token", None)
    if access_token:
        # アクセストークンの有効期限分だけブラックリストに入れれば良いが、
        # ここでは簡易的にアクセストークンの寿命設定を使用
        await add_to_blacklist(access_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    if logout_data and logout_data.refresh_token:
         await add_to_blacklist(logout_data.refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)

    return {"message": "ログアウトしました。"}
