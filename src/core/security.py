from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import uuid
from passlib.context import CryptContext
from jose import jwt, JWTError
from src.core.config import settings
import redis.asyncio as redis
from fastapi import HTTPException, status

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redisクライアントの初期化
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文のパスワードとハッシュ化されたパスワードを検証します。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化します。
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成します。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTリフレッシュトークンを生成します。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    JWTトークンをデコードし、ペイロードを返します。
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def add_to_blacklist(token: str, expiration: int):
    """
    トークンをブラックリスト（Redis）に追加します。
    expiration: トークンの有効期限（秒）
    """
    # トークンの残存期間を計算（または単純にexpirationを使用）
    # ここでは簡易的に、トークン自体のexpクレームから計算されたTTLを受け取ると想定、
    # もしくは固定の最大TTLを使用。
    await redis_client.setex(f"blacklist:{token}", expiration, "blacklisted")

async def is_token_blacklisted(token: str) -> bool:
    """
    トークンがブラックリストに登録されているか確認します。
    """
    exists = await redis_client.get(f"blacklist:{token}")
    return exists is not None

class RateLimiter:
    """
    Redisを使用したスライディングウィンドウ方式のレート制限クラス。
    """
    def __init__(self, requests_limit: int = 100, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """
        リクエストが許可されるかどうかを判定します。
        key: 識別子（IPアドレスやユーザーIDなど）
        """
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_seconds
        redis_key = f"rate_limit:{key}"

        async with redis_client.pipeline(transaction=True) as pipe:
            # 期限切れの古いリクエストを削除
            await pipe.zremrangebyscore(redis_key, 0, window_start)
            # 現在のリクエストを追加
            await pipe.zadd(redis_key, {str(now): now})
            # 期間内のリクエスト数を取得
            await pipe.zcard(redis_key)
            # キーの有効期限を設定（ウィンドウサイズ+1秒）
            await pipe.expire(redis_key, self.window_seconds + 1)

            results = await pipe.execute()

        request_count = results[2]
        return request_count <= self.requests_limit
