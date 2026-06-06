# Local Provider Health Probe Mock Transport Runner v1

## Decision

- Decision: `LOCAL_PROVIDER_PROBE_MOCK_RUNNER_WITH_TESTS`
- Contract version: `local-provider-health-probe-mock-runner/1`
- Implementation surface: `src/aegis/core/local_provider_probe_mock_runner.py`
- Test surface: `tests/test_core/test_local_provider_probe_mock_runner.py`
- Previous sprint: `LOCAL_PROVIDER_PROBE_WIRING_READINESS_WITH_TESTS`

This sprint adds a pure mock-transport runner contract for future local provider
health probes. It classifies injected mock result metadata for provider root,
model-list, health metadata, timeout, refused, invalid response, unauthorized,
unsupported endpoint, and malformed metadata cases.

It does not call LM Studio, OpenAI-compatible endpoints, `/v1/models`, `/models`,
provider root, health, generation, chat/completion, embeddings, rerank,
multimodal, audio, file upload, or tool-call endpoints. It does not open sockets,
perform HTTP requests, use real transport, load models, call models, validate
API keys, read secrets, create evidence, mark verifier success, or mutate
runtime state.

## Scope

The helper validates caller-supplied mock runner metadata only. It classifies:

- runner request class
- mock result class
- runner readiness class
- metadata response shape class
- paired probe wiring reference
- paired probe boundary reference
- related decision references
- mock success and negative result semantics
- non-authority and non-execution invariants

The output is not:

- a performed provider probe
- real provider access
- HTTP/socket behavior
- runtime/API/frontend wiring
- provider health proof
- model availability proof
- model identity proof
- benchmark proof
- Auto Mode selection
- execution permission
- evidence or verifier success

Every decision preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_local_provider_probe_mock_runner`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_mock_probe=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `api_route_added=false`
- `runtime_command_added=false`
- `scheduler_added=false`
- `real_endpoint_probed=false`
- `socket_opened=false`
- `http_request_performed=false`
- `provider_probed=false`
- `mock_transport_only=true`
- `real_transport_used=false`
- `model_loaded=false`
- `model_call_performed=false`
- `generation_performed=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `multimodal_inference_performed=false`
- `prompt_payload_sent=false`
- `context_payload_sent=false`
- `memory_payload_sent=false`
- `repo_payload_sent=false`
- `raw_journal_payload_sent=false`
- `raw_evidence_payload_sent=false`
- `api_key_validated=false`
- `secret_read=false`
- `authorization_header_sent=false`
- `cloud_provider_called=false`
- `lan_or_remote_endpoint_called=false`
- `data_sent_external=false`
- `provider_health_verified=false`
- `model_availability_verified=false`
- `model_identity_verified=false`
- `benchmark_claim_verified=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`

## Why Mock Transport Runner Exists

The previous wiring readiness sprint defined how a future probe runner could be
wired without adding runtime/API behavior. This sprint adds the next safe layer:
a backend-owned mock-result classifier that can validate future runner result
shapes without any real provider access.

It lets Aegis test success and failure semantics before live localhost probing
exists.

## Why This Is Not Real Provider Probing

No real transport is accepted or used. The helper accepts only caller-supplied
mock result metadata. It does not accept a callable, does not open sockets, does
not send HTTP, does not send payloads, and does not read secrets.

Mock transport runner readiness is still not runtime execution.

## Runner Request Classes

Supported classes:

- `mock_provider_root_probe`
- `mock_models_list_probe`
- `mock_health_metadata_probe`
- `mock_invalid_response_probe`
- `mock_timeout_probe`
- `mock_connection_refused_probe`
- `mock_unauthorized_probe`
- `mock_unsupported_endpoint_probe`
- `unknown`

`unknown` is blocked. Negative result classes must match the corresponding
runner request class.

## Mock Result Classes

Supported classes:

- `mock_success_metadata_candidate`
- `mock_timeout_negative_candidate`
- `mock_connection_refused_negative_candidate`
- `mock_invalid_response_negative_candidate`
- `mock_unauthorized_negative_candidate`
- `mock_unsupported_endpoint_negative_candidate`
- `mock_malformed_metadata_negative_candidate`
- `not_executed`
- `unknown`

Mock success is candidate metadata only. Negative mock results are candidate
metadata only and are not runtime failures.

## Runner Readiness Classes

Supported classes:

- `mock_runner_ready`
- `requires_probe_wiring`
- `requires_probe_boundary`
- `blocked_by_transport`
- `blocked_by_endpoint_scope`
- `blocked_by_payload`
- `blocked_by_secret_policy`
- `blocked_by_timeout_policy`
- `blocked_by_unknown_host`
- `blocked_by_real_transport`
- `future_gated`
- `unknown`

Only `mock_runner_ready` can produce a ready mock candidate. `future_gated` is
preserved as future-gated and not executed. Blocked/readiness-required classes
remain blocked or require the missing reference.

## Metadata Response Shape Classes

Supported classes:

- `provider_metadata_shape_candidate`
- `models_list_shape_candidate`
- `health_metadata_shape_candidate`
- `empty_response_negative_candidate`
- `malformed_response_negative_candidate`
- `unknown_shape`

Provider metadata, model-list, and health metadata shapes are candidates only.
Empty and malformed response shapes are negative candidates. Unknown shape
requires review.

## Mock Success Rules

Mock success can classify only supplied metadata. It cannot prove:

- provider health
- endpoint reachability
- model availability
- model identity
- model quality
- benchmark status
- verifier success
- evidence

Mock model-list data is not model availability proof.

## Mock Negative Result Rules

Mock timeout, connection refused, invalid response, unauthorized, unsupported
endpoint, and malformed metadata outcomes are negative candidate metadata only.

They are not:

- runtime failures
- evidence
- verifier failures
- provider health proof
- model unavailability proof

## Truthfulness Rules

The contract rejects claims that:

- mock success is provider health proof
- mock model list is model availability proof
- mock health metadata is verifier success
- negative mock result is runtime failure
- provider metadata is truth
- model-list metadata is truth
- provider health is proven
- model availability is execution-ready
- self-reported identity is authoritative
- benchmark or quality status is verified
- Auto Mode can select a provider/model from the mock result
- Local Model Inventory proves availability

## Relationship to Local Provider Probe Wiring

Probe Wiring metadata can inform mock runner readiness, but it cannot authorize
live probing. Safe wiring decisions are references only. Unsafe wiring decisions
that claim real endpoint probing, HTTP/socket behavior, runtime/API surfaces,
evidence, verifier success, grants, or model behavior are rejected.

## Relationship to Local Provider Probe Boundary

Probe Boundary metadata must remain metadata-only. It can supply boundary
context for a mock runner, but it cannot authorize execution or prove provider
health.

## Relationship to Probe Design, Provider Health, and Local Model Inventory

Probe Design can describe future phases. Provider Health can classify metadata
readiness. Local Model Inventory can describe model metadata. None can authorize
mock runner output as proof, model availability, model execution, or runtime
truth.

## Relationship to Model Auto Mode

Model Auto Mode cannot select a provider or model from mock runner readiness.
Mock runner output grants no routing permission.

## Relationship to Local Model Context Profile

Local Model Context Profile metadata cannot authorize model use, eval proof,
benchmark proof, context delivery, or mock runner execution.

## Relationship to Context Policy, Identity, and Memory Governance

Context Policy, Identity Scope, and Memory Governance remain separate gates.
This contract does not retrieve context, access memory, send private repo data,
read journals, read evidence, or bypass policy.

## Relationship to Capability Lease

Capability Lease metadata is reference-only. No lease is created, granted, or
used. A lease candidate cannot authorize probe execution in this sprint.

## Why Mock Metadata Is Not Proof

Mock metadata is useful for validating future runner classifications and
negative-result semantics. It is not runtime truth because no backend-owned live
probe, evidence chain, verifier boundary, or policy-gated execution occurred.

## Tests Added

Focused tests cover:

- valid mock provider root metadata probe
- valid mock models-list metadata probe
- valid mock health metadata probe
- mock success as candidate-only
- mock timeout negative metadata
- mock connection-refused negative metadata
- mock invalid-response negative metadata
- mock unauthorized negative metadata
- missing required fields
- missing source refs/provenance
- missing probe wiring reference
- missing probe boundary reference
- metadata response shape classification
- unknown response shape handling
- truthfulness overclaim rejection
- unsafe related decision rejection
- blocked runner readiness classes
- future-gated runner readiness
- real transport, HTTP/socket, runtime/API, model, payload, secret, cloud/LAN/remote, evidence, verifier, and grant flag rejection
- mock_transport_only=false rejection for candidate results
- input and related decision immutability
- output invariants proving no real transport, no provider probe, no runtime mutation, no evidence, and no verifier success

## Intentionally Not Done

This sprint did not:

- perform a real endpoint probe
- open sockets
- perform HTTP requests
- call LM Studio
- request `/v1/models`
- add API routes
- add runtime commands
- add schedulers
- add frontend UI
- use real transport
- load or call models
- generate embeddings
- rerank
- run multimodal inference
- send prompts or context
- read memory
- read repo files
- read journal or evidence
- validate API keys
- read secrets
- mutate runtime/journal/evidence/replay
- create evidence or verifier success
- grant approval, lease, or capability

## Future Implementation Notes

The next safe layer could be a live-localhost design gate that still blocks
execution while specifying injected HTTP-client requirements, cancellation,
timeout enforcement, negative evidence handling, and operator policy gates.

Any later live probe must remain localhost/loopback only, explicit opt-in,
backend-owned, no-payload, no-secret, and separate from evidence/verifier
success.

## Remaining Risks

- Real transport behavior remains unimplemented and unverified.
- Runtime/API exposure still needs a separate readiness sprint.
- Live negative evidence semantics remain future work.
- Mock metadata may be mistaken for operational truth unless later consumers
  preserve these non-authority labels.
