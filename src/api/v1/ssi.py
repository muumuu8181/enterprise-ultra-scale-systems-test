from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Union
import uuid
from src.services.vc_service import VCService

router = APIRouter(prefix="/ssi", tags=["SSI"])

# In-memory store for challenges (use Redis in production)
challenges: Dict[str, str] = {}

class ChallengeResponse(BaseModel):
    challenge: str

class VerifyRequest(BaseModel):
    presentation: str
    challenge: str

class VerifyResponse(BaseModel):
    verified: bool
    holder: str
    claims: List[Dict]

class ConsentRequest(BaseModel):
    requester: str
    data_types: List[str]

class ConsentResponse(BaseModel):
    consent_id: str
    status: str

@router.post("/auth/challenge", response_model=ChallengeResponse)
async def create_challenge():
    """
    Generates a random challenge for authentication.
    """
    challenge = str(uuid.uuid4())
    challenges[challenge] = challenge
    return {"challenge": challenge}

@router.post("/auth/verify", response_model=VerifyResponse)
async def verify_presentation(request: VerifyRequest):
    """
    Verifies a Verifiable Presentation.
    """
    if request.challenge not in challenges:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    # 1. Verify VP signature and validity
    try:
        # VP is also a signed JWT, so we can use verify_credential logic
        vp_payload = await VCService.verify_credential(request.presentation)
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Invalid presentation: {str(e)}")

    # 2. Check nonce/challenge
    if vp_payload.get("nonce") != request.challenge:
        raise HTTPException(status_code=400, detail="Challenge mismatch")

    # 3. Verify embedded VCs
    vp_data = vp_payload.get("vp", {})
    vcs = vp_data.get("verifiableCredential", [])
    if isinstance(vcs, str):
        vcs = [vcs]

    verified_claims = []
    for vc_jwt in vcs:
        try:
            vc_payload = await VCService.verify_credential(vc_jwt)
            verified_claims.append(vc_payload.get("vc", {}).get("credentialSubject", {}))
        except Exception as e:
             raise HTTPException(status_code=400, detail=f"Invalid VC in presentation: {str(e)}")

    # Clean up challenge
    if request.challenge in challenges:
        del challenges[request.challenge]

    return {
        "verified": True,
        "holder": vp_payload.get("iss"),
        "claims": verified_claims
    }

@router.post("/consent", response_model=ConsentResponse)
async def create_consent(request: ConsentRequest):
    """
    Records user consent.
    """
    consent_id = str(uuid.uuid4())
    return {
        "consent_id": consent_id,
        "status": "granted"
    }
