# Security model

Trust only local operator configuration and cryptographic integrity checks. Job text, submitted results, source content, room metadata and model output are untrusted. There are no model tools, shell execution hooks, remote configuration changes or package installation capabilities. The only subprocesses in identity initialization are fixed Windows account/ACL utilities, invoked without a shell and without job-controlled arguments.

## Identity and evidence

Private keys are generated locally after creating a restricted directory. POSIX checks owner-only key mode; Windows removes inherited ACL entries and grants the current account access. Keys are raw local Ed25519 material, not password-encrypted. Administrators/account compromise, inherited ownership policies on unusual filesystems and hostile local filesystem races are outside the protection provided by the application. Use a private local NTFS/POSIX data directory, never a shared writable directory. Back up identity securely outside the repository. Do not run different OS accounts against the same identity directory.

No CLI operation prints private material. The repository ignores data, key files and .env. Public deliverables include only code and public evidence. Logs use fixed event names and safe fields. Exception handling avoids dumping model/provider request bodies, tokens or arbitrary remote errors.

Offline verification checks signature and schema, manifest digest, every required file hash, safe paths and links, job ID and verdict/attestation consistency. Transferring only an attestation cannot demonstrate evidence integrity. No DID resolver or network is used. A valid signature is not a guarantee of truth.

## Network and untrusted inputs

Only public HTTP/HTTPS source URLs on standard ports are accepted. Credentials, fragments, control characters, backslashes and private/link-local/reserved targets are rejected. All DNS answers must be public. Connections use a validated address directly and preserve TLS hostname verification; each redirect is checked again. No environment proxy, cookies or authentication is attached to source retrieval. Known Technocore write URLs are rejected as sources. Arbitrary HTTP GET services can have side effects; operators should restrict source domains further for high-risk deployments.

Response bodies, redirections, source counts, JSON size, prompt context and numerical expression size are bounded. Response body reading has a total deadline. DNS uses a bounded-wait daemon thread; an OS resolver stalled beyond its deadline may keep its thread alive until it returns. Sequential processing and job quotas limit accumulation, but a production daemon may need OS-level DNS controls. Unsupported media (including PDFs) is recorded as accessible but unusable rather than treated as supporting evidence.

The local Ollama adapter is a separately configured loopback capability. Job URLs cannot reach it. External inference requires explicit local selection and HTTPS; no automatic paid fallback exists. Model context never contains identity keys or provider credentials. Model replies must match a strict schema and cite exact source substrings. These measures do not make LLM judgment immune to adversarial persuasion or misleading excerpts. Treat results as inspectable attestations of performed checks, not truth certificates.

## Abuse and recovery

Incoming jobs require independently reverified transport signatures and matching requester DID. Persistent ID/nonce uniqueness, job/post quotas, bounded inference, a single-process lock and daemon backoff prevent basic replay/spam. Signatures authenticate a key, not a real-world person; Sybil resistance is not implemented.

Network failure after a write can mean the write succeeded. Store the outgoing signed envelope before transmission and reconcile by signature, DID, nonce and text. Do not silently retry an unresolved write. Review stalled computations, missing room history and rejected publications explicitly. Tests cover these boundaries; no formal security audit or absolute prompt-injection immunity is claimed.
