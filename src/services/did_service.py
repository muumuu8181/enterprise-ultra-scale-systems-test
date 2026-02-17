import httpx
from src.core.crypto import Ed25519KeyPair

class DIDService:
    @staticmethod
    def create_did(method: str = "web", **kwargs) -> str:
        """
        Creates a DID string.
        For did:web, it expects a domain in kwargs.
        """
        if method == "web":
            domain = kwargs.get("domain")
            if not domain:
                raise ValueError("Domain is required for did:web")
            return f"did:web:{domain}"
        raise ValueError(f"Unsupported DID method: {method}")

    @staticmethod
    async def resolve_did(did: str) -> dict:
        """
        Resolves a DID to a DID Document.
        """
        if did.startswith("did:web:"):
            domain = did[8:]
            # Basic handling for did:web (no path support for now)
            url = f"https://{domain}/.well-known/did.json"

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    raise ValueError(f"Failed to resolve DID {did}: {str(e)}")

        raise ValueError(f"Unsupported DID method for resolution: {did}")

    @staticmethod
    def create_did_document(did: str, public_key: Ed25519KeyPair) -> dict:
        """
        Helper to create a DID Document structure for a given key.
        """
        jwk = public_key.get_public_jwk()
        verification_method_id = f"{did}#key-1"

        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/jws-2020/v1"
            ],
            "id": did,
            "verificationMethod": [{
                "id": verification_method_id,
                "type": "JsonWebKey2020",
                "controller": did,
                "publicKeyJwk": jwk
            }],
            "authentication": [verification_method_id],
            "assertionMethod": [verification_method_id]
        }
