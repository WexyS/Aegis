# Local Provider Health Probe Implementation Boundary
## Decision

- Decision: `LOCAL_PROVIDER_PROBE_BOUNDARY_METADATA_ONLY_WITH_TESTS`
- Contract version: `local-provider-health-probe-boundary/1`
- Implementation surface: `src/aegis/core/local_provider_probe_boundary.py`
- Test surface: `tests/test_core/test_local_provider_probe_boundary.py`
- Previous sprint: `REPO_AUDIT_SOURCE_PLAN_DISPLAY_READINESS_WITH_TESTS`

This sprint adds a metadata-only implementation boundary for future local
provider health probes. It does not call LM Studio, OpenAI-compatible local
endpoints, Ollama, vLLM, cloud providers, LAN endpoints, or remote endpoints. It
does not open sockets, perform HTTP requests, load models, call models, generate
embeddings, rerank, run multimodal inference, send prompts, send context, read
secrets, validate API keys, mutate runtime state, create evidence, or mark
verifier success.

## Scope

The helper validates caller-supplied probe boundary metadata only. It classifies:

- provider class
- endpoint host class
- endpoint URL metadata
- metadata endpoint class
- probe phase and scope
- timeout policy
- payload class
- secret policy
- truthfulness boundaries
- related decision references

The output is not:

- a performed provider probe
- provider health proof
- model availability proof
- model identity proof
- benchmark proof
- Auto Mode selection
- execution permission
- approval, lease, or capability grant
- evidence or verifier success

Every decision preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_local_provider_probe_boundary`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_probe=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `provider_probed=false`
- `endpoint_probed=false`
- `http_request_performed=false`
- `socket_opened=false`
- `model_loaded=false`
- `model_call_performed=false`
- `generation_performed=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `multimodal_inference_performed=false`
- `data_sent_external=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`

## Why This Boundary Exists

Local model support needs a first implementation boundary before any real health
probe is safe. Existing readiness and probe-design contracts describe future
provider health behavior, but they do not provide a hardened shape for the
actual probe boundary.

This contract defines what future probe metadata may look like and what must be
blocked before any endpoint request exists.

## Why No Actual Probe Was Implemented

The safe choice for this sprint is metadata-only. A real localhost probe would
need runtime/API wiring, timeout handling, cancellation behavior, HTTP client
injection, negative evidence recording rules, and operator policy gates. Those
are future implementation surfaces and were intentionally not added here.

## Provider Classes

Supported provider boundary classes:

- `lm_studio_localhost_openai_compatible_metadata`
- `openai_compatible_localhost_metadata`
- `mock_test_provider_metadata`
- `unknown`

`unknown` is blocked. Provider class metadata is not provider health proof and
does not authorize a probe.

## Host Rules

Supported endpoint host classes:

- `localhost`
- `loopback`
- `lan`
- `remote`
- `cloud`
- `unknown`

Only `localhost` and `loopback` can become metadata-only probe candidates. The
validator checks the supplied endpoint URL metadata and blocks mismatch or spoof
cases such as `localhost.evil.test`. LAN, remote, cloud, and unknown hosts are
blocked.

Accepted loopback URL metadata includes:

- `http://localhost:...`
- `http://127.0.0.1:...`
- `http://[::1]:...`

This is still not a live connection and not endpoint reachability proof.

## Endpoint Rules

Allowed metadata endpoint classes:

- `provider_root_metadata_candidate`
- `models_list_metadata_candidate`
- `health_metadata_candidate`
- `mock_metadata_candidate`
- `unknown`

`unknown` is blocked. Allowed metadata paths are limited to root, provider
metadata, model-list metadata, health metadata, and mock metadata shapes.

Blocked endpoint/action classes include:

- generation
- chat completion
- completion
- embeddings
- reranker
- multimodal
- audio
- file upload
- tool call
- unknown endpoint path

A model-list metadata candidate is not model availability proof and cannot
become execution permission.

## Payload and Secret Rules

Allowed payload classes:

- `no_payload`
- `empty_get`
- `empty_head`

Blocked payload classes:

- prompt payload
- context payload
- memory payload
- repo payload
- raw journal payload
- raw evidence payload
- secret payload
- unknown payload

Allowed secret policies:

- `no_secret`
- `no_auth_header`

Blocked secret behavior:

- Authorization header use
- API key validation
- secret reads
- unknown secret policy

The boundary does not read or validate API keys and does not send secret-bearing
headers.

## Timeout and Negative Result Metadata

The helper requires timeout metadata and blocks invalid or oversized timeout
policies. Because no actual probe is performed, timeout/refused/unreachable
results are represented only as future negative candidate metadata.

Negative candidate metadata is not runtime failure evidence and is not verifier
success.

## Truthfulness Rules

The boundary rejects claims that:

- provider metadata is truth
- model-list metadata is truth
- provider health is proven
- model availability is execution-ready
- a probe candidate selects Auto Mode
- a probe candidate is model profile or eval proof
- quality or benchmark status is verified
- self-reported provider/model identity is authoritative

Provider or model self-reporting remains untrusted metadata until a future
backend-owned verifier and evidence chain exists.

## Related Decision Handling

The validator accepts related readiness decisions as references only:

- Local Provider Health
- Local Provider Probe Design
- Model Auto Mode
- Local Model Inventory
- Local Model Context Profile
- Policy Extension
- Context Policy
- Memory Governance
- Identity Scope
- Capability Lease

Unsafe related decisions are rejected if they claim authority, runtime dispatch,
approval, capability, lease, evidence, verifier success, provider health proof,
model availability proof, model calls, probe execution, payload transfer,
secret reads, external calls, or runtime mutations.

A capability lease candidate cannot authorize probe execution in this sprint.

## Relationship to Provider Readiness and Probe Design

Provider readiness and probe design may describe future health-check intent, but
they cannot authorize a performed probe. This boundary adds a stricter
metadata-only contract for the first implementation-adjacent layer.

## Relationship to Model Auto Mode

Auto Mode can later consume provider health metadata, but this boundary never
selects a provider or model for execution. `probe_allowed_candidate` means only
that supplied metadata passed the boundary checks.

## Relationship to Local Model Inventory and Context Profiles

Local Model Inventory and Local Model Context Profile metadata may describe
candidate model roles, modality, resource needs, and eval readiness. They cannot
authorize a provider probe, prove model availability, or turn model output into
truth.

## Relationship to Context, Memory, Identity, and Policy

Context Policy, Memory Governance, Identity Scope, and Policy-as-Code remain
separate gates. This boundary does not retrieve context, read memory, send
private repo data, read journals, read evidence, or bypass policy.

## Tests Added

Focused tests cover:

- valid LM Studio localhost metadata candidate
- valid OpenAI-compatible localhost metadata candidate
- mock provider metadata candidate
- missing required fields
- localhost, IPv4 loopback, and IPv6 loopback metadata
- LAN, remote, cloud, and unknown host blocking
- localhost spoof blocking
- malformed and non-HTTP endpoint blocking
- generation, embedding, reranker, multimodal, audio, upload, and tool endpoint blocking
- prompt/context/memory/repo/journal/evidence/secret payload blocking
- API key, secret, and Authorization header blocking
- timeout policy blocking
- authority, grant, evidence, verifier, health-proof, model-proof, and benchmark-proof rejection
- unsafe related decision rejection
- input immutability
- output invariants proving no probe, model call, payload transfer, runtime mutation, evidence, or verifier success

## Intentionally Not Done

This sprint did not:

- perform a real localhost probe
- implement an HTTP client
- open sockets
- call LM Studio or OpenAI-compatible endpoints
- request `/v1/models`
- load or call models
- generate embeddings
- rerank
- run multimodal probes
- inspect model files
- validate API keys
- read secrets
- wire runtime/API/frontend behavior
- mutate runtime/journal/evidence/replay
- create evidence or verifier success
- grant approval, leases, or capabilities

## Future Implementation Notes

A future real local provider probe should remain:

- explicit opt-in
- localhost/loopback only
- timeout-bounded
- cancellation-aware
- no prompt payload
- no context, memory, repo, journal, or evidence payload
- no Authorization header by default
- no generation, embedding, reranking, or multimodal endpoint calls
- negative-evidence aware
- backend-owned
- policy-gated
- evidence/verifier separated

It should use injected test clients in tests and must not perform live endpoint
calls unless a later sprint explicitly authorizes live smoke behavior.

## Remaining Risks

- Real probe behavior still needs a separate API/runtime wiring readiness sprint.
- Negative evidence rules for future live probes are not implemented here.
- Provider endpoint quirks are not verified because no endpoint is contacted.
- Model-list metadata may still be self-reported in future work and must remain
  non-authoritative unless backed by explicit evidence and verifier checks.
