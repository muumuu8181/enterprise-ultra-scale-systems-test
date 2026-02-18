import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.identity_models import DigitalIdentity, VerifiableCredential
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json
import hashlib

# Test setup
@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    return _get_db

@pytest.fixture
async def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_identity(client, mock_db_session):
    # Mock refresh to set ID and defaults
    async def mock_refresh(obj):
        obj.id = 1
        if not hasattr(obj, 'created_at') or obj.created_at is None:
            obj.created_at = datetime.utcnow()
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {"user_id": "user123"}
    response = await client.post("/api/v1/identity/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user123"
    assert data["did"].startswith("did:web:example.com:")
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_did_document(client, mock_db_session):
    did = "did:web:example.com:test-did"
    mock_identity = DigitalIdentity(id=1, user_id="u1", did=did, public_key="pk1")

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_identity
    mock_db_session.execute.return_value = mock_result

    response = await client.get(f"/api/v1/identity/{did}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == did
    assert data["verificationMethod"][0]["publicKeyBase58"] == "pk1"

@pytest.mark.asyncio
async def test_issue_credential(client, mock_db_session):
    did = "did:web:example.com:test-did"
    mock_identity = DigitalIdentity(id=1, user_id="u1", did=did, public_key="pk1")

    # First call is to find identity
    mock_result_ident = MagicMock()
    mock_result_ident.scalars.return_value.first.return_value = mock_identity
    mock_db_session.execute.return_value = mock_result_ident

    async def mock_refresh(obj):
        obj.id = 100
        obj.issued_at = datetime.utcnow()
        obj.expires_at = datetime.utcnow()
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "identity_did": did,
        "type": "UniversityDegree",
        "claims": {"degree": "BSc", "university": "Test Univ"}
    }

    response = await client.post("/api/v1/identity/credentials/issue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "UniversityDegree"
    assert data["claims"]["degree"] == "BSc"
    assert "signature" in data
    # Ensure issuer is correct
    assert data["issuer"] == did

@pytest.mark.asyncio
async def test_verify_credential(client, mock_db_session):
    did = "did:web:example.com:test-did"
    pk = "pk1"

    claims = {"degree": "BSc"}
    payload_str = json.dumps(claims, sort_keys=True)
    signature = hashlib.sha256(f"{payload_str}{pk}".encode()).hexdigest()

    # Construct the simulated JWT content
    jwt_data = {
        "claims": claims,
        "signature": signature,
        "issuer": did
    }
    credential_jwt = json.dumps(jwt_data)

    mock_identity = DigitalIdentity(id=1, user_id="u1", did=did, public_key=pk)

    # Mock DB calls: find issuer by DID
    mock_result_ident = MagicMock()
    mock_result_ident.scalars.return_value.first.return_value = mock_identity

    mock_db_session.execute.side_effect = [mock_result_ident]

    payload = {"credential_jwt": credential_jwt}
    response = await client.post("/api/v1/identity/credentials/verify", json=payload)
    assert response.status_code == 200
    assert response.json()["valid"] == True

@pytest.mark.asyncio
async def test_verify_credential_invalid_signature(client, mock_db_session):
    did = "did:web:example.com:test-did"
    pk = "pk1"

    claims = {"degree": "BSc"}
    signature = "invalid_signature"

    jwt_data = {
        "claims": claims,
        "signature": signature,
        "issuer": did
    }
    credential_jwt = json.dumps(jwt_data)

    mock_identity = DigitalIdentity(id=1, user_id="u1", did=did, public_key=pk)

    mock_result_ident = MagicMock()
    mock_result_ident.scalars.return_value.first.return_value = mock_identity

    mock_db_session.execute.side_effect = [mock_result_ident]

    payload = {"credential_jwt": credential_jwt}
    response = await client.post("/api/v1/identity/credentials/verify", json=payload)
    assert response.status_code == 200
    assert response.json()["valid"] == False
