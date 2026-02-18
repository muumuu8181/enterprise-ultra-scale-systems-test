from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.identity_models import DigitalIdentity, VerifiableCredential, ConsentRecord
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
import json

router = APIRouter(prefix="/identity", tags=["identity"])

# Pydantic Schemas
class IdentityCreate(BaseModel):
    user_id: str

class IdentityResponse(BaseModel):
    id: int
    user_id: str
    did: str
    public_key: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CredentialIssueRequest(BaseModel):
    identity_did: str
    type: str
    claims: Dict[str, Any]

class CredentialResponse(BaseModel):
    id: int
    identity_id: int
    type: str
    issuer: str
    claims: Dict[str, Any]
    issued_at: datetime
    expires_at: Optional[datetime]
    signature: str
    model_config = ConfigDict(from_attributes=True)

class CredentialVerifyRequest(BaseModel):
    credential_jwt: str
    # Simulating JWT as a JSON string containing claims and signature

# Endpoints

@router.post("/create", response_model=IdentityResponse)
async def create_identity(request: IdentityCreate, db: AsyncSession = Depends(get_db)):
    """
    Generate DID (did:web method) and create Digital Identity
    """
    # Generate DID
    did_suffix = str(uuid.uuid4())
    did = f"did:web:example.com:{did_suffix}"

    # Generate Mock Key Pair (In production, use proper crypto lib)
    public_key = f"pub_key_{did_suffix}"

    new_identity = DigitalIdentity(
        user_id=request.user_id,
        did=did,
        public_key=public_key
    )

    db.add(new_identity)
    await db.commit()
    await db.refresh(new_identity)
    return new_identity

@router.get("/{did}", response_model=Dict[str, Any])
async def get_did_document(did: str, db: AsyncSession = Depends(get_db)):
    """
    Get DID Document
    """
    result = await db.execute(select(DigitalIdentity).where(DigitalIdentity.did == did))
    identity = result.scalars().first()

    if not identity:
        raise HTTPException(status_code=404, detail="DID not found")

    # Construct DID Document
    did_doc = {
        "@context": "https://www.w3.org/ns/did/v1",
        "id": identity.did,
        "verificationMethod": [{
            "id": f"{identity.did}#key-1",
            "type": "Ed25519VerificationKey2018",
            "controller": identity.did,
            "publicKeyBase58": identity.public_key # Mock representation
        }],
        "authentication": [f"{identity.did}#key-1"]
    }
    return did_doc

@router.post("/credentials/issue", response_model=CredentialResponse)
async def issue_credential(request: CredentialIssueRequest, db: AsyncSession = Depends(get_db)):
    """
    Issue a Verifiable Credential
    """
    # Find identity
    result = await db.execute(select(DigitalIdentity).where(DigitalIdentity.did == request.identity_did))
    identity = result.scalars().first()

    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Mock Signature
    # In reality, issuer signs the VC. Here we simulate it.
    payload_str = json.dumps(request.claims, sort_keys=True)
    signature = hashlib.sha256(f"{payload_str}{identity.public_key}".encode()).hexdigest()

    vc = VerifiableCredential(
        identity_id=identity.id,
        type=request.type,
        issuer=identity.did, # Use identity DID as issuer
        claims=request.claims,
        signature=signature,
        expires_at=datetime.utcnow() + timedelta(days=365)
    )

    db.add(vc)
    await db.commit()
    await db.refresh(vc)
    return vc

@router.post("/credentials/verify")
async def verify_credential(request: CredentialVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify Credential (Stateless verification using stored DID public keys)
    """
    try:
        # Simulate JWT decoding
        # We assume the credential_jwt is a JSON string of the VC data
        # containing claims, signature, and issuer
        data = json.loads(request.credential_jwt)
        claims = data.get("claims")
        signature = data.get("signature")
        issuer_did = data.get("issuer")

        if not (claims and signature and issuer_did):
             return {"valid": False, "reason": "Invalid credential format"}

        # Find issuer identity to get public key
        result = await db.execute(select(DigitalIdentity).where(DigitalIdentity.did == issuer_did))
        identity = result.scalars().first()

        if not identity:
            return {"valid": False, "reason": "Issuer identity not found"}

        # Verify Signature
        payload_str = json.dumps(claims, sort_keys=True)
        expected_signature = hashlib.sha256(f"{payload_str}{identity.public_key}".encode()).hexdigest()

        if signature != expected_signature:
             return {"valid": False, "reason": "Invalid signature"}

        # Check expiration if present in claims or wrapper
        expires_at_str = data.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at < datetime.utcnow():
                    return {"valid": False, "reason": "Credential expired"}
            except ValueError:
                pass # Ignore if invalid format for now

        return {"valid": True, "credential": claims}

    except json.JSONDecodeError:
        return {"valid": False, "reason": "Invalid JSON token"}
    except Exception as e:
        return {"valid": False, "reason": str(e)}

@router.get("/credentials/{id}", response_model=CredentialResponse)
async def get_credential(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get Verifiable Credential by ID
    """
    result = await db.execute(select(VerifiableCredential).where(VerifiableCredential.id == id))
    vc = result.scalars().first()

    if not vc:
        raise HTTPException(status_code=404, detail="Credential not found")

    return vc
