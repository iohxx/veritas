import base64
from cryptography.exceptions import InvalidSignature
from veritas.identity.did import public_from_did
from veritas.errors import VeritasError


def sign(key, payload):
    return base64.urlsafe_b64encode(key.sign(payload)).decode("ascii").rstrip("=")


def verify(did, signature, payload):
    try:
        if not isinstance(signature, str) or len(signature) != 86:
            return False
        raw = base64.b64decode(signature + "==", altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode().rstrip("=") != signature:
            return False
        public_from_did(did).verify(raw, payload)
        return True
    except (VeritasError, InvalidSignature, ValueError, TypeError):
        return False
