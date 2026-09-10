# MVP acceptance — 2026-09-10

**The software is implemented, but the full MVP acceptance is NOT yet satisfied.** Two runtime/service dependencies prevent the remaining live validations: Ollama/qwen3:4b is unavailable locally, and Technocore currently refuses creation of the requested room.

## Executed successfully

- 32 automated tests passed in the final suite (4.759 seconds); Python compilation and dependency consistency checks passed.
- Python 3.12.14 development environment, editable installation and CLI entry point.
- Ed25519 generation/loading, stable did:key, local key permissions, signing and rejection of modified signatures/payloads.
- Strict job validation, deterministic arithmetic and simple source conflicts.
- Complete source/evidence storage, SHA-256 manifest and attestation signature.
- Three requested demos: VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE; each replayed and validated offline.
- Public evidence copies are included in the release, without any identity key or runtime database.
- Real HTTPS retrieval of the official Technocore authentication document, with a preserved snapshot and hash. The resulting research job correctly reports insufficient evidence because semantic inference was unavailable.
- Real read of `/r/veritas` and one bounded daemon read cycle. The room is empty/nonexistent and no job was injected publicly.
- Automated tests for transport authentication, long-poll request construction, daemon job processing, publication signatures, persistent quotas, malformed messages and uncertain-write reconciliation. These use a local fake service and are not represented as live publication success.
- Automated tests for SSRF/DNS/redirect controls, size limits, path traversal, duplicate JSON, unsupported versions, fake DIDs, modified evidence and offline verification without a private key.

## Live dependencies not validated

**Ollama:** no executable found on PATH or in the two standard Windows installation paths checked, and no service responded at 127.0.0.1:11434. The real provider is implemented and configured for qwen3:4b; no model was downloaded, no paid substitute was used and no semantic inference success is claimed. Install/start Ollama and pull the model, then submit a new research job ID/nonce to complete this check.

**Technocore publication:** the official POST endpoint returned HTTP 400 explaining that the server's room cap of 163840 was reached and `/r/veritas` would be a new room. The diagnostic retry used the same signed envelope and was also rejected. No successful public message or room creation occurred. The local outbox preserves the rejection. Complete the live acceptance only when that room can be created or an operator-authorized deployment provides it. Do not publish into an unrelated room merely to pass a test.

## Scope and known limits

The advanced phases are intentionally not implemented: dashboard, distributed consensus, broad contradiction discovery, reputation, payments and FLOP integration. Semantic behavior is tested with controlled fixtures, not a live model. Source discovery covers submitted URLs, not the whole web; PDFs and arbitrary natural-language arithmetic are not supported. The local daemon is not installed as a persistent OS service.

To finish full acceptance: restore the two dependencies, run a useful signed JOB through the live room and local Ollama, confirm its signed ATTEST receipt, transfer the evidence bundle and validate it offline. Until then, report local tests as passing and full live MVP acceptance as incomplete.
