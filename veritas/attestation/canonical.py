"""VERITAS-C14N-1: restricted JSON, integer numbers only, ASCII escapes."""
import hashlib
import json
from veritas.errors import VeritasError


def canonical(value):
    def check(x):
        if type(x) is str:
            if any(0xD800 <= ord(c) <= 0xDFFF for c in x):
                raise VeritasError('invalid_unicode_scalar')
            return
        if x is None or type(x) is bool:
            return
        if type(x) is int and abs(x) <= 9007199254740991:
            return
        if type(x) is list:
            for v in x:
                check(v)
            return
        if type(x) is dict and all(type(k) is str for k in x):
            for k in x:
                check(k)
            for v in x.values():
                check(v)
            return
        raise VeritasError("unsupported_canonical_value")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def parse_json(raw, maximum=65536):
    if len(raw) > maximum:
        raise VeritasError("oversized_json")
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise VeritasError("duplicate_json_key")
            obj[key] = value
        return obj
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        canonical(value)
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise VeritasError("invalid_json") from exc
