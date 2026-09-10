from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from veritas.errors import VeritasError

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def encode58(raw):
    n, out = int.from_bytes(raw, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + out


def did_from_public(raw):
    if len(raw) != 32:
        raise VeritasError("invalid_public_key")
    return "did:key:z" + encode58(b"\xed\x01" + raw)


def public_from_did(did):
    if not isinstance(did, str) or not did.startswith("did:key:z") or not 40 < len(did) < 65:
        raise VeritasError("invalid_did")
    try:
        n = 0
        for c in did[9:]:
            n = n * 58 + ALPHABET.index(c)
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        if len(raw) != 34 or raw[:2] != b"\xed\x01" or did_from_public(raw[2:]) != did:
            raise ValueError()
        return Ed25519PublicKey.from_public_bytes(raw[2:])
    except (ValueError, OverflowError) as exc:
        raise VeritasError("invalid_did") from exc
