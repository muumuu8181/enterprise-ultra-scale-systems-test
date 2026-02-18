from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.auth_models import UserAuth, DeviceToken
from src.models.user import User
from src.schemas import UserRegisterRequest, GuestLoginRequest, LinkAccountRequest

# Secret key settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def verify_password(self, plain_password, hashed_password):
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def get_user_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(UserAuth).where(UserAuth.email == email))
        return result.scalars().first()

    async def register_user(self, db: AsyncSession, request: UserRegisterRequest):
        # Check if email exists
        existing_user = await self.get_user_by_email(db, request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create User
        new_user = User(name=request.username)
        db.add(new_user)
        await db.flush() # get ID

        # Create UserAuth
        hashed_pw = self.get_password_hash(request.password)
        new_auth = UserAuth(
            user_id=new_user.id,
            provider="email",
            provider_id=request.email,
            email=request.email,
            hashed_password=hashed_pw
        )
        db.add(new_auth)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def authenticate_user(self, db: AsyncSession, email: str, password: str):
        user_auth = await self.get_user_by_email(db, email)
        if not user_auth:
            return None
        if not self.verify_password(password, user_auth.hashed_password):
            return None
        return user_auth

    async def create_guest(self, db: AsyncSession, request: GuestLoginRequest):
        # Check if device_id exists
        result = await db.execute(select(UserAuth).where(
            (UserAuth.provider == "guest") & (UserAuth.provider_id == request.device_id)
        ))
        existing_guest = result.scalars().first()

        if existing_guest:
             return existing_guest.user_id

        # New Guest
        new_user = User(name=f"Guest_{request.device_id[:8]}")
        db.add(new_user)
        await db.flush()

        new_auth = UserAuth(
            user_id=new_user.id,
            provider="guest",
            provider_id=request.device_id,
            last_login=datetime.now(timezone.utc)
        )
        db.add(new_auth)

        # Register device token
        new_device = DeviceToken(
            user_id=new_user.id,
            device_id=request.device_id,
            fcm_token=request.fcm_token,
            platform=request.platform
        )
        db.add(new_device)

        await db.commit()
        return new_user.id

    async def link_account(self, db: AsyncSession, user_id: int, request: LinkAccountRequest):
        # User is currently logged in (user_id from token)
        result = await db.execute(select(UserAuth).where(UserAuth.user_id == user_id))
        user_auth = result.scalars().first()

        if not user_auth:
            # Should not happen if token is valid, unless user deleted
            raise HTTPException(status_code=404, detail="User not found")

        # Logic: If current auth is guest, upgrade it. If it's already email, maybe change email?
        # Assuming we only link guest accounts
        if user_auth.provider != "guest":
             raise HTTPException(status_code=400, detail="Account already linked or not a guest account")

        # Check if target email already exists
        existing_email = await self.get_user_by_email(db, request.email)
        if existing_email:
             raise HTTPException(status_code=400, detail="Email already linked to another account")

        # Update UserAuth
        user_auth.provider = "email"
        user_auth.provider_id = request.email
        user_auth.email = request.email
        user_auth.hashed_password = self.get_password_hash(request.password)

        await db.commit()
        return user_auth
