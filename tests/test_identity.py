import tempfile
import unittest
from pathlib import Path
from veritas.identity.keys import Identity
from veritas.identity.did import public_from_did
from veritas.identity.signing import sign, verify
from veritas.attestation.canonical import canonical, parse_json
from veritas.errors import VeritasError


class IdentityTests(unittest.TestCase):
    def test_stable_local_identity(self):
        with tempfile.TemporaryDirectory() as d:
            first = Identity.load(d, create=True)
            second = Identity.load(d, create=True)
            self.assertEqual(first.did, second.did)
            self.assertTrue(first.did.startswith("did:key:z6Mk"))
            self.assertTrue(verify(first.did, sign(first.key, b"hello"), b"hello"))
            self.assertFalse(verify(first.did, sign(first.key, b"hello"), b"changed"))
            self.assertFalse(verify(first.did, "A" * 86, b"hello"))

    def test_bad_did_and_encoding(self):
        for did in ("did:key:fake", "did:key:z" + "0"*48, "../key", "", None):
            with self.assertRaises(VeritasError):
                public_from_did(did)

    def test_canonical_and_duplicates(self):
        self.assertEqual(canonical({"b":2,"a":1}), b'{"a":1,"b":2}')
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.2}', b'bad'):
            with self.assertRaises(VeritasError):
                parse_json(raw)


if __name__ == "__main__":
    unittest.main()
