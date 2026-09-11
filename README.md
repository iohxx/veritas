# VERITAS

Independent verification of public research and agent results, with evidence bundles, deterministic replay and Ed25519 attestations. The first MVP verifies arithmetic, retrieves sources, requests evidence-grounded semantic analysis and searches submitted sources for contradictions.

**Status:** runnable local implementation with validated Technocore publication. Inference is optional and disabled by default. The daemon, arithmetic checks, DID signatures, evidence bundles and replay work without Ollama. Research requiring semantic analysis reports insufficient evidence when no provider is configured. See `docs/acceptance.md` for the validation actually performed.

## Install

Python 3.12+ is required. From the project directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\veritas init
.venv\Scripts\veritas identity
```

Linux/macOS: use `.venv/bin/python` and `.venv/bin/veritas`. `python -m veritas` exposes the same commands. Runtime dependencies are `cryptography` for Ed25519 and `pydantic` for strict schemas. Tests use standard-library `unittest`. No OpenAI key or Codex/ChatGPT runtime is required.

The local development environment supplied in this workspace uses existing runtime packages through `--system-site-packages`; it is not included in the source archive. A new machine should follow the installation above.

## Optional inference

Default: `VERITAS_INFERENCE_PROVIDER=none`. To enable Ollama explicitly in PowerShell:

```powershell
$env:VERITAS_INFERENCE_PROVIDER = 'ollama'
$env:VERITAS_MODEL = 'qwen3:4b'
```

An operator can instead select `external` and configure `VERITAS_INFERENCE_URL` (HTTPS), `VERITAS_MODEL` and optionally `VERITAS_API_KEY`. The bundled external adapter speaks the Ollama-compatible chat protocol; it is not a universal vendor adapter. Other protocols can be implemented behind `InferenceProvider.generate(prompt, context)` without changing the verification core. See `docs/architecture.md`.

Install Ollama from its official distribution, then:

```powershell
ollama pull qwen3:4b
ollama serve
```

If Ollama already runs as a desktop service, do not start a second server. Defaults are `http://127.0.0.1:11434/api/chat` and `qwen3:4b`. Process environment variables override defaults; `.env.example` is documentation, not an automatically executed file. Source retrieval cannot access loopback; only the explicitly configured local inference adapter can.

## Verify, inspect and replay

```powershell
.venv\Scripts\veritas verify examples/job_demo_sum_correct.json
.venv\Scripts\veritas inspect job_demo_sum_correct
.venv\Scripts\veritas replay job_demo_sum_correct
.venv\Scripts\veritas verify-attestation data/jobs/job_demo_sum_correct/attestation.json
.venv\Scripts\python scripts/demo.py
```

The demo uses a separate `data/demo` directory and performs no public writes. It expects VERIFIED, CONTRADICTED and INSUFFICIENT_EVIDENCE, respectively. Repeated jobs/nonces are rejected; use replay to check an existing job. The third example uses a reserved `.invalid` source address.

To verify another person's bundle offline, supply its attestation and `--evidence path/to/evidence`. No key file, daemon, DID registry or network is needed. A complete validation requires the bundle; a valid signature alone cannot validate missing evidence. Signature validity proves authorship and integrity, not truth.

## Technocore and autonomous mode

```powershell
.venv\Scripts\veritas verify path/to/new-job.json --publish
.venv\Scripts\veritas publish job_demo_sum_correct
.venv\Scripts\veritas agent --once
.venv\Scripts\veritas agent
```

Publication is explicit in the CLI and automatic for compatible signed jobs received by the daemon. Each job produces one signed ATTEST message carrying its attestation; the full bundle stays local and must be transferred separately. The first useful publication creates `/r/veritas` if it does not exist. No heartbeat, farming or synthetic chat traffic is emitted.

Incoming jobs must have a valid Technocore transport signature and a matching requester DID. Local files are explicitly submitted by the operator; their requester field is an assertion, not proof of requester identity. Invalid jobs never reach inference. The daemon persists cursors, job/nonces, quotas and outbox receipts in SQLite. It rejects other message types, reconciles ambiguous writes and stops for history gaps or unresolved publication ambiguity. `agent --since N` is an explicit operator choice after reviewing a gap.

## Security and limits

Identity keys are stored locally in ignored `data/identity`. Windows uses a restricted NTFS directory ACL; POSIX uses owner-only permissions. Keys are not encrypted at rest; protect the account and disk. Never copy the identity directory with a public evidence bundle. The CLI only displays the public DID. Logs contain controlled fields and no raw requests or credentials.

Untrusted data has no shell, filesystem or configuration capabilities. Public source retrieval checks IPs, pins the connection to a validated address, revalidates redirects, blocks internal targets and limits size/deadline. Prompt injection can still mislead semantic judgments: quoted evidence and conservative verdict rules reduce this risk but cannot guarantee factual accuracy. See `docs/security.md`.

Limits and confidence weights are configured locally. Confidence is an integer **0–100 measuring verification strength**, not probability of truth. Absence of Ollama does not affect pure arithmetic or offline verification.

## Contribute

Read `AGENTS.md` before changing code. Run `python -m unittest discover -v` and `python scripts/export_schemas.py`. Add tests for meaningful failure modes, keep changes small and never commit secrets or runtime data. No FLOP API, distributed consensus, dashboard, reputation points or payments are implemented. License: MIT.

VERITAS is an independent community-built agent infrastructure experiment. It is not an official FLOP Labs product and makes no claims about airdrop eligibility or rewards.
