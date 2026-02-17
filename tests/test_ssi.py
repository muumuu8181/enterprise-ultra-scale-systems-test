import pytest
from unittest.mock import MagicMock, patch
from src.core.crypto import Ed25519KeyPair
from src.services.did_service import DIDService
from src.services.vc_service import VCService
from src.api.v1.ssi import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def keys():
    issuer_key = Ed25519KeyPair()
    holder_key = Ed25519KeyPair()
    return issuer_key, holder_key

@pytest.fixture
def dids():
    return "did:web:issuer.example.com", "did:web:holder.example.com"

@pytest.mark.asyncio
async def test_did_creation():
    did = DIDService.create_did(method="web", domain="example.com")
    assert did == "did:web:example.com"

@pytest.mark.asyncio
async def test_vc_issuance_and_verification(keys, dids):
    issuer_key, holder_key = keys
    issuer_did, holder_did = dids

    # Create DID Document for issuer
    issuer_did_doc = DIDService.create_did_document(issuer_did, issuer_key)

    # Setup mock for httpx.AsyncClient
    async def async_get(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = issuer_did_doc
        return mock_resp

    mock_client = MagicMock()
    mock_client.__aenter__.return_value.get.side_effect = async_get
    mock_client.__aexit__.return_value = None

    with patch("src.services.did_service.httpx.AsyncClient", return_value=mock_client):
        # Issue VC
        claims = {"name": "Alice", "role": "admin"}
        vc_jwt = VCService.issue_credential(issuer_did, holder_did, claims, issuer_key)

        assert vc_jwt is not None

        # Verify VC
        verified = await VCService.verify_credential(vc_jwt)
        assert verified["iss"] == issuer_did
        assert verified["vc"]["credentialSubject"]["name"] == "Alice"

@pytest.mark.asyncio
async def test_api_flow(keys, dids):
    issuer_key, holder_key = keys
    issuer_did, holder_did = dids

    # 1. Challenge
    resp = client.post("/ssi/auth/challenge")
    assert resp.status_code == 200
    challenge = resp.json()["challenge"]

    # 2. Create VC and VP
    issuer_did_doc = DIDService.create_did_document(issuer_did, issuer_key)
    holder_did_doc = DIDService.create_did_document(holder_did, holder_key)

    async def side_effect(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        # Simple string check in url
        if "issuer" in url:
            mock_resp.json.return_value = issuer_did_doc
        elif "holder" in url:
            mock_resp.json.return_value = holder_did_doc
        else:
            mock_resp.status_code = 404
        return mock_resp

    mock_client = MagicMock()
    mock_client.__aenter__.return_value.get.side_effect = side_effect
    mock_client.__aexit__.return_value = None

    with patch("src.services.did_service.httpx.AsyncClient", return_value=mock_client):
        # Issue VC
        claims = {"email": "alice@example.com"}
        vc_jwt = VCService.issue_credential(issuer_did, holder_did, claims, issuer_key)

        # Create VP
        vp_jwt = VCService.create_presentation([vc_jwt], holder_did, holder_key, challenge)

        # 3. Verify via API
        verify_req = {
            "presentation": vp_jwt,
            "challenge": challenge
        }

        resp = client.post("/ssi/auth/verify", json=verify_req)
        if resp.status_code != 200:
            print(resp.json())
        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is True
        assert data["holder"] == holder_did
        assert data["claims"][0]["email"] == "alice@example.com"
