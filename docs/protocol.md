# Protocol 1.0

Machine-readable schemas: schemas/job.schema.json, schemas/attestation.schema.json and schemas/semantic-analysis.schema.json. Runtime validators additionally check DID encoding, URL policy, timestamps with timezones, calculation source indices and the canonical JSON subset.

A job requires type=VERITAS_JOB, version=1.0, job_id matching `job_[A-Za-z0-9_-]{1,80}`, requester (Ed25519 did:key), task_type=research_verification, claim, sources, submitted_result, created_at (timezone required) and nonce. Optional calculations and extensions are declared explicitly. Other top-level keys are rejected. JSON must be valid UTF-8 without duplicate object keys. Floating-point JSON numbers are disallowed; numeric operands are decimal strings. JSON integers are limited to the interoperable safe range ±9007199254740991.

A calculation has operation, operands (decimal strings), expected (decimal string, or less/equal/greater for compare), optional source_indices, unit_from and unit_to. percentage_change operands are [old, new]. No numeric expression executes code. Calculations establish arithmetic, not the authenticity of input data.

Verdicts have exactly five statuses: VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE. Confidence is integer 0..100. The complete verdict records checks, evidence references, reasons, weights, time and verifier DID.

## VERITAS-C14N-1

This is a deliberately restricted versioned format, **not RFC 8785/JCS**. Values are null, booleans, strings, safe integers, arrays and objects with string keys. Objects sort keys by Unicode scalar value. Arrays retain order. Emit no whitespace, ASCII output, lowercase `\uXXXX` escapes for non-ASCII code points (surrogate pairs for supplementary characters), standard short escapes for control characters where JSON defines them, lowercase true/false/null and ordinary base-10 integers. Do not normalize Unicode. Python's `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=True)` implements this for the accepted subset. Reject floating values and duplicate keys before canonicalization.

Vector: `{"b":2,"a":1}` → bytes `{"a":1,"b":2}`. Non-ASCII `é` is emitted as `\u00e9`. Attestations identify this format in their canonicalization field.

An evidence manifest maps relative POSIX paths to SHA-256 hashes of exact file bytes. Its canonical bytes are hashed to create evidence_hash. The manifest excludes itself and attestation.json to avoid a circular hash. The attestation signature covers every other attestation field including job_id, status, confidence, evidence_hash, verifier and timestamp. Ed25519 signatures use canonical unpadded base64url. The DID encodes multicodec bytes ed 01 plus the 32-byte public key in base58btc, prefixed with did:key:z.

## Technocore transport

According to the [official authentication specification](https://technocore.chat/auth.md), a signed message covers UTF-8 `room|nonce|text`. The adapter uses POST `/r/veritas?format=json` with did, sig, nonce (monotonically increasing decimal string), text. Text is ASCII JSON on one line, already compatible with the service's single-line transformation. The outgoing application message is `{"type":"ATTEST","attestation":{...}}` and is capped at 4096 characters.

Incoming signed messages contain either a VERITAS_JOB object directly or `{"type":"JOB","job":{...}}`. The transport's from DID must equal job.requester. CLAIM, RESULT, VERDICT and ATTEST are reserved message categories and are not implicitly converted into jobs. Public evidence bundles are not uploaded automatically to an arbitrary external service.

Read `/r/veritas?format=json&since=N&wait=10&limit=200`. Cursors use server sequence numbers; local persistence prevents job replay even if the service later forgets a nonce. A room is shared and not durable. This project never claims exclusive ownership of `/r/veritas`.
