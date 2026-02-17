from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from src.services.authz_service import compute_effective_permissions, Permission

router = APIRouter()

# --- Request/Response Models ---

class IdentityCreate(BaseModel):
    username: str
    email: str
    password: str # In a real app, this would be hashed

class IdentityResponse(BaseModel):
    id: int
    username: str
    email: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    client_id: str
    code_verifier: str # For PKCE
    code: Optional[str] = None # Authorization code
    grant_type: str = "authorization_code"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class MFARequest(BaseModel):
    method: str = "totp"

# --- Endpoints ---

@router.post("/identities/create", response_model=IdentityResponse)
async def create_identity(identity: IdentityCreate):
    # Mock creation logic
    return IdentityResponse(
        id=1,
        username=identity.username,
        email=identity.email,
        status="active"
    )

@router.get("/identities/{id}/permissions", response_model=List[Permission])
async def get_identity_permissions(id: int):
    permissions = await compute_effective_permissions(id)
    return permissions

@router.post("/identities/{id}/mfa/enable")
async def enable_mfa(id: int, mfa_request: MFARequest):
    # Mock MFA enabling logic
    return {"message": "MFA enabled", "method": mfa_request.method}

@router.post("/auth/login", response_model=TokenResponse)
async def login(login_req: LoginRequest):
    # Mock login logic (OAuth2+PKCE flow)
    if login_req.grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant type")

    # In a real implementation, we would verify the code and code_verifier
    return TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        expires_in=3600
    )

@router.post("/auth/token/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    # Mock token refresh logic
    return TokenResponse(
        access_token="new_mock_access_token",
        refresh_token="new_mock_refresh_token",
        expires_in=3600
    )

@router.delete("/auth/sessions/{id}")
async def logout(id: str):
    # Mock logout logic (invalidate session)
    return {"message": "Session terminated"}
