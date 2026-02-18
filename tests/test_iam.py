import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from src.models.iam_models import Identity, Role, ResourcePolicy, IdentityStatus, RoleScope, PrincipalType, PolicyEffect
from src.services.authz_service import evaluate_policy, compute_effective_permissions, detect_anomalous_access, RiskSignal
from src.api.v1.identity import router as identity_router

# --- Setup ---
app = FastAPI()
app.include_router(identity_router)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# --- Service Tests ---

@pytest.mark.asyncio
async def test_evaluate_policy():
    allowed = await evaluate_policy(1, "resource", "read")
    assert allowed is True
    denied = await evaluate_policy(0, "resource", "read")
    assert denied is False

@pytest.mark.asyncio
async def test_compute_effective_permissions():
    perms = await compute_effective_permissions(1)
    assert len(perms) > 0
    assert perms[0].effect == "allow"

@pytest.mark.asyncio
async def test_detect_anomalous_access():
    event = {"ip_address": "192.168.0.1", "user_agent": "Mozilla/5.0"}
    signal = await detect_anomalous_access(1, event)
    assert isinstance(signal, RiskSignal)
    assert signal.risk_score > 0.5
    assert signal.severity == "high"

    safe_event = {"ip_address": "10.0.0.1", "user_agent": "Mozilla/5.0"}
    signal_safe = await detect_anomalous_access(1, safe_event)
    assert signal_safe.risk_score < 0.5

# --- API Tests ---

@pytest.mark.asyncio
async def test_create_identity(async_client):
    response = await async_client.post("/identities/create", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["status"] == "active"

@pytest.mark.asyncio
async def test_get_identity_permissions(async_client):
    response = await async_client.get("/identities/1/permissions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "resource" in data[0]

@pytest.mark.asyncio
async def test_enable_mfa(async_client):
    response = await async_client.post("/identities/1/mfa/enable", json={"method": "totp"})
    assert response.status_code == 200
    assert response.json()["message"] == "MFA enabled"

@pytest.mark.asyncio
async def test_login_success(async_client):
    response = await async_client.post("/auth/login", json={
        "client_id": "client123",
        "code_verifier": "verifier123",
        "code": "code123",
        "grant_type": "authorization_code"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_grant(async_client):
    response = await async_client.post("/auth/login", json={
        "client_id": "client123",
        "code_verifier": "verifier123",
        "grant_type": "password" # Invalid
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_refresh_token(async_client):
    response = await async_client.post("/auth/token/refresh", params={"refresh_token": "old_token"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_logout(async_client):
    response = await async_client.delete("/auth/sessions/session123")
    assert response.status_code == 200
    assert response.json()["message"] == "Session terminated"

# --- Model Tests ---

def test_identity_model():
    identity = Identity(username="user", email="email@test.com", status=IdentityStatus.PENDING)
    assert identity.username == "user"
    assert identity.status == IdentityStatus.PENDING

def test_role_model():
    role = Role(name="admin", permissions={"admin": True}, scope=RoleScope.GLOBAL)
    assert role.name == "admin"
    assert role.scope == RoleScope.GLOBAL

def test_policy_model():
    policy = ResourcePolicy(
        resource_type="s3",
        resource_id="bucket1",
        principal_type=PrincipalType.USER,
        effect=PolicyEffect.ALLOW
    )
    assert policy.effect == PolicyEffect.ALLOW
