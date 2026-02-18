from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import jwt
import base64
import json

class Ed25519KeyPair:
    def __init__(self, private_key=None):
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def get_public_bytes_pem(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_private_bytes_pem(self) -> bytes:
         return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_public_jwk(self) -> dict:
        # Ed25519 JWK format: kty: OKP, crv: Ed25519, x: <base64url>
        x_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(x_bytes).decode('utf-8').rstrip('=')
        }

    def sign(self, payload: dict) -> str:
        # PyJWT allows passing private key object directly for EdDSA
        return jwt.encode(payload, self.private_key, algorithm='EdDSA')

def verify_jws(token: str, public_key) -> dict:
    """
    Verifies a JWS token signature.
    public_key can be PEM bytes or JWK dict.
    Returns the payload if signature is valid.
    Does NOT verify exp/nbf/iat claims (caller should do that).
    """
    # If public_key is JWK dict, convert to PEM/key object
    key = public_key
    if isinstance(public_key, dict):
        if public_key.get("kty") == "OKP" and public_key.get("crv") == "Ed25519":
             # Convert JWK to Ed25519PublicKey
             x_b64 = public_key["x"]
             # Add padding if needed
             x_b64 += '=' * (-len(x_b64) % 4)
             x_bytes = base64.urlsafe_b64decode(x_b64)
             key = ed25519.Ed25519PublicKey.from_public_bytes(x_bytes)
        else:
             raise ValueError("Unsupported JWK type")

    # jwt.decode verifies signature
    # We disable other checks to match previous behavior (manual check in service)
    return jwt.decode(
        token,
        key,
        algorithms=['EdDSA'],
        options={
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iat": False,
            "verify_aud": False
        }
    )
