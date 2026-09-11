# Validation status — 2026-09-11

Technocore integration is considered validated, as confirmed by the operator. Inference is optional and interchangeable, not a prerequisite for VERITAS operation.

## Automated local checks

38 tests passed in 5.185 seconds after provider decoupling. Coverage includes stable Ed25519 identities and DIDs, signatures, evidence integrity, offline verification, replay, malicious inputs, network controls, quotas and deduplication.

The autonomous signed-job cycle is tested with a simulated Technocore service: processing, attestation publication, evidence validation, replay and duplicate prevention. Two controlled provider implementations can be injected without changing the core. Arithmetic never calls inference. Research without inference still produces signed evidence with INSUFFICIENT_EVIDENCE.

Provider selection defaults to none. Explicit Ollama/external selection and unknown-provider rejection are tested without calling a model. The three deterministic demonstrations remain covered: VERIFIED for 10+20+30=60, CONTRADICTED for =61, and INSUFFICIENT_EVIDENCE for an inaccessible source.

## Previously executed live checks

- Retrieved the official Technocore authentication document over HTTPS and preserved its snapshot.
- Published the signed attestation for job_public_research to /r/veritas, receipt sequence 1. Independently read it back and verified both transport and attestation signatures.
- Offline bundle verification and replay succeeded for that research job.
- Local Ollama/qwen3:4b responded, but its purported verbatim quote did not match the source. VERITAS rejected the analysis and returned INSUFFICIENT_EVIDENCE. This was not successful semantic verification.

The earlier room-cap rejection and unavailable-Ollama report are superseded by these results. No further Qwen optimization or additional public messages were needed for provider modularity.

## Operational scope and limits

The command `veritas agent` provides the autonomous loop while its process is running; `veritas agent --once` performs a bounded cycle. No persistent operating-system service has been installed or started. A complete incoming signed JOB through the live daemon is not claimed: that full chain was tested with a simulated service, separately from successful live publication/readback.

Other inference APIs require an adapter implementing InferenceProvider.generate(prompt, context) and local factory wiring or direct injection, not changes to the verification core. The bundled external adapter uses the Ollama-compatible chat protocol. Semantic quality remains conditional on the provider and evidence; missing or invalid analysis must not be represented as completed verification.

Replay checks saved evidence and reproducible deterministic results; it does not rerun a model or establish real-world truth. Signatures prove authorship and integrity, not truth.

Source discovery covers submitted URLs, not the whole web. PDFs, arbitrary natural-language arithmetic, dashboards, distributed consensus, reputation, payments and FLOP integration remain outside this MVP scope.
