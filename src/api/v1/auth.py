from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.auth_service import AuthService, SECRET_KEY, ALGORITHM
from src.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    GuestLoginRequest, LinkAccountRequest
)
from jose import jwt, JWTError

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=TokenResponse)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await auth_service.register_user(db, request)
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user_auth = await auth_service.authenticate_user(db, request.email, request.password)
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": str(user_auth.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/guest", response_model=TokenResponse)
async def create_guest(
    request: GuestLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user_id = await auth_service.create_guest(db, request)
    access_token = auth_service.create_access_token(data={"sub": str(user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/link-account", response_model=TokenResponse)
async def link_account(
    request: LinkAccountRequest,
    authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid Token")

    user_auth = await auth_service.link_account(db, user_id, request)
    access_token = auth_service.create_access_token(data={"sub": str(user_auth.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google")
async def google_auth():
    return {"message": "Google OAuth2 not implemented yet"}

@router.get("/apple")
async def apple_auth():
    return {"message": "Apple OAuth2 not implemented yet"}
