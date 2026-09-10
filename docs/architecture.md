# Architecture

The package has one synchronous pipeline, a CLI and an optional daemon. Modules follow the specification: identity, security, verification, inference, storage, attestation, technocore and agent. No runtime dependency on Codex or a paid API exists.

Pipeline order: structural validation → claim preservation → bounded public retrieval → accessibility/content validation → deterministic calculations → semantic analysis → source contradiction search → verdict → evidence manifest → attestation → signature → optional publication.

Claim extraction conservatively retains the whole claim as one unit. The numerical shortcut is anchored to a complete supported grammar and requires the submitted result to match. General research uses the inference adapter; arithmetic results alone cannot establish real-world operands.

Every job has its own `data/jobs/<job_id>/` containing input.json, result.json, verdict.json, attestation.json and evidence/. Evidence contains job.json, claims.json, sources.json, checks.json, verdict.json, snapshots, manifest.json and attestation.json. Attestations also have a local index under data/attestations/. SQLite stores deduplication, progress, quotas, transport nonces, cursors and receipts. data/logs/events.jsonl stores safe events. The data/evidence directory is reserved; bundles themselves remain with their job to avoid duplicate sources.

The command process holds a local lock. Jobs run sequentially. A crash during computation leaves a processing/failed record that is not silently rerun under the same identifier. The operator inspects it and submits a new job ID and nonce if needed. Completed jobs with uncertain publication retain a persistent outbox entry. An uncertain transport write is searched for before any retry; unresolved ambiguity stops processing for review rather than risking duplicates.

LocalInferenceProvider implements the real Ollama `/api/chat` API. ExternalInferenceProvider optionally targets a remote Ollama-compatible HTTPS endpoint, selected by local configuration only. It is not a universal adapter for every vendor. Both use InferenceProvider.generate(prompt, context). A future FLOP provider can implement that abstraction when its official API exists; no FLOP adapter or protocol is invented now.

References: [Technocore manual](https://technocore.chat/llms.txt), [OpenAPI](https://technocore.chat/openapi.json), [Ollama chat API](https://docs.ollama.com/api/chat). Retrieved 2026-09-10.
