from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from src.services.crypto_service import CryptoService
from src.models.crypto_models import CryptoAlgorithm

router = APIRouter()

async def get_crypto_service():
    return CryptoService()

# Request Models
class KeyGenerationRequest(BaseModel):
    algorithm: CryptoAlgorithm
    owner_id: int

class EncryptRequest(BaseModel):
    plaintext: str
    public_key: str

class DecryptRequest(BaseModel):
    ciphertext_uri: str
    key_id: int

class SignRequest(BaseModel):
    data: str
    key_id: int

class VerifyRequest(BaseModel):
    data: str
    signature: str
    public_key: str

class CertificateIssueRequest(BaseModel):
    csr: str
    lifetime_days: int

# Response Models
class KeyPairResponse(BaseModel):
    id: int
    owner_id: int
    algorithm: str
    public_key: str
    key_size: int

    model_config = ConfigDict(from_attributes=True)

class EncryptedDataResponse(BaseModel):
    id: int
    ciphertext_uri: str
    nonce: str
    tag: str
    original_size_bytes: int

    model_config = ConfigDict(from_attributes=True)

@router.post("/keys/generate", response_model=KeyPairResponse)
async def generate_key(request: KeyGenerationRequest, service: CryptoService = Depends(get_crypto_service)):
    try:
        keypair = await service.generate_keypair(request.algorithm.value, request.owner_id)
        return keypair
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/keys/{id}/public")
async def get_public_key(id: int, service: CryptoService = Depends(get_crypto_service)):
    # Mock retrieval
    return {"public_key": "mock_public_key", "id": id}

@router.post("/encrypt", response_model=EncryptedDataResponse)
async def encrypt_data(request: EncryptRequest, service: CryptoService = Depends(get_crypto_service)):
    data_bytes = request.plaintext.encode('utf-8')
    encrypted = await service.hybrid_encrypt(data_bytes, request.public_key)
    return encrypted

@router.post("/decrypt")
async def decrypt_data(request: DecryptRequest, service: CryptoService = Depends(get_crypto_service)):
    # Mock decryption
    return {"plaintext": "mock_decrypted_text"}

@router.post("/sign")
async def sign_data(request: SignRequest, service: CryptoService = Depends(get_crypto_service)):
    # Mock signing
    return {"signature": "mock_signature"}

@router.post("/verify")
async def verify_signature(request: VerifyRequest, service: CryptoService = Depends(get_crypto_service)):
    data_bytes = request.data.encode('utf-8')
    sig_bytes = request.signature.encode('utf-8')
    is_valid = await service.verify_signature(data_bytes, sig_bytes, request.public_key)
    return {"valid": is_valid}

@router.get("/certificates/{id}")
async def get_certificate(id: int, service: CryptoService = Depends(get_crypto_service)):
    return {"certificate": "mock_certificate_pem"}

@router.post("/certificates/issue")
async def issue_certificate(request: CertificateIssueRequest, service: CryptoService = Depends(get_crypto_service)):
    return {"certificate": "mock_issued_certificate_pem"}
