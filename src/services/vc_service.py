import time
import uuid
from typing import List, Dict, Union, Optional
import jwt
from src.core.crypto import Ed25519KeyPair, verify_jws
from src.services.did_service import DIDService

class VCService:
    @staticmethod
    def issue_credential(issuer_did: str, subject_did: str, claims: Dict, issuer_key: Ed25519KeyPair, expires_in: int = 31536000) -> str:
        """
        Issues a JWT Verifiable Credential.
        expires_in defaults to 1 year (365 * 24 * 3600).
        """
        now = int(time.time())
        jti = str(uuid.uuid4())

        # Structure payload according to W3C VC data model (JWT format)
        payload = {
            "iss": issuer_did,
            "sub": subject_did,
            "jti": jti,
            "nbf": now,
            "iat": now,
            "exp": now + expires_in,
            "vc": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1"
                ],
                "type": ["VerifiableCredential"],
                "credentialSubject": claims
            }
        }

        # Sign with Ed25519
        jwt_vc = issuer_key.sign(payload)
        return jwt_vc

    @staticmethod
    async def verify_credential(vc_jwt: str) -> Dict:
        """
        Verifies a JWT Verifiable Credential.
        Returns the payload if valid.
        Checks signature, expiry, nbf, and revocation status (placeholder).
        """
        # 1. Parse without verification to get issuer
        try:
            unverified_claims = jwt.decode(vc_jwt, options={"verify_signature": False})
        except Exception as e:
             raise ValueError(f"Invalid JWT format: {e}")

        issuer_did = unverified_claims.get("iss")

        if not issuer_did:
            raise ValueError("Missing issuer in VC")

        # 2. Resolve DID
        try:
            did_doc = await DIDService.resolve_did(issuer_did)
        except Exception as e:
            raise ValueError(f"Could not resolve issuer DID {issuer_did}: {e}")

        # 3. Extract public key from DID Doc
        verification_methods = did_doc.get("verificationMethod", [])
        if not verification_methods:
            raise ValueError("No verification methods in DID Document")

        # Try to find a suitable key.
        public_key_jwk = None
        # Try to find header kid if available to match specific key
        unverified_header = jwt.get_unverified_header(vc_jwt)
        kid = unverified_header.get("kid")

        if kid:
             # Look for specific key
             for vm in verification_methods:
                if vm.get("id") == kid or vm.get("id").endswith(f"#{kid}"): # loose matching
                     if "publicKeyJwk" in vm:
                        public_key_jwk = vm["publicKeyJwk"]
                        break

        if not public_key_jwk:
            # Fallback to first available JsonWebKey2020
            for vm in verification_methods:
                if vm.get("type") == "JsonWebKey2020" and "publicKeyJwk" in vm:
                    public_key_jwk = vm["publicKeyJwk"]
                    break

        if not public_key_jwk:
            raise ValueError("No suitable public key found in DID Document")

        # 4. Verify signature
        try:
            verified_payload = verify_jws(vc_jwt, public_key_jwk)
        except Exception as e:
            raise ValueError(f"Signature verification failed: {e}")

        # 5. Check exp/nbf
        now = int(time.time())
        if "exp" in verified_payload and verified_payload["exp"] < now:
            raise ValueError("Credential expired")
        if "nbf" in verified_payload and verified_payload["nbf"] > now:
            raise ValueError("Credential not yet valid")

        # 6. Check revocation (Mock implementation)
        # In a real implementation, we would check the 'credentialStatus' field
        # against a revocation list or registry.
        if "credentialStatus" in verified_payload.get("vc", {}):
            # TODO: Implement revocation check (e.g., StatusList2021)
            pass

        return verified_payload

    @staticmethod
    def create_presentation(vc_jwts: List[str], holder_did: str, holder_key: Ed25519KeyPair, nonce: str) -> str:
        """
        Creates a JWT Verifiable Presentation.
        """
        now = int(time.time())
        jti = str(uuid.uuid4())

        payload = {
            "iss": holder_did,
            "jti": jti,
            "nbf": now,
            "iat": now,
            "exp": now + 3600, # Short expiry for presentation
            "nonce": nonce,
            "vp": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1"
                ],
                "type": ["VerifiablePresentation"],
                "verifiableCredential": vc_jwts
            }
        }

        return holder_key.sign(payload)
