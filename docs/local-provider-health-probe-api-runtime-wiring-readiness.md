# Local Provider Health Probe API/Runtime Wiring Readiness
## Decision

- Decision: `LOCAL_PROVIDER_PROBE_WIRING_READINESS_WITH_TESTS`
- Contract version: `local-provider-health-probe-wiring-readiness/1`
- Implementation surface: `src/aegis/core/local_provider_probe_wiring.py`
- Test surface: `tests/test_core/test_local_provider_probe_wiring.py`
- Previous sprint: `LOCAL_PROVIDER_PROBE_BOUNDARY_METADATA_ONLY_WITH_TESTS`

This sprint adds a pure API/runtime wiring readiness contract for future local
provider health probes. It does not add an API route, runtime command,
scheduler, HTTP client, socket behavior, live localhost probe, LM Studio call,
OpenAI-compatible request, model load, model call, embedding generation,
reranking, multimodal inference, context transfer, memory retrieval, repo read,
web call, evidence creation, verifier success, approval, lease, or capability
grant.

## Scope

The helper validates caller-supplied wiring metadata only. It classifies:

- probe wiring request class
- execution mode class
- transport class
- endpoint host class
- endpoint scope class
- payload class
- secret policy class
- timeout policy class
- cancellation policy class
- mock result metadata
- runtime/API readiness metadata
- related decision references

The output is not:

- a performed provider probe
- real provider access
- runtime/API wiring
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
- `execution_permission=not_granted_by_local_provider_probe_wiring`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_probe_wiring=false`
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

## Why API/Runtime Wiring Readiness Exists

The previous probe boundary sprint defined a metadata-only local provider probe
boundary. The next risk is wiring: a future runner might be exposed through an
API route, runtime command, scheduler, or backend service too early.

This contract defines the readiness metadata for those future surfaces while
keeping all execution blocked. It gives Aegis a shape for future mocked transport
tests and policy gates without adding runtime behavior now.

## Why This Is Not Real Provider Probing

This sprint does not call `/v1/models`, `/models`, provider root, health,
generation, chat/completion, embeddings, rerank, multimodal, audio, file upload,
or tool-call endpoints. It does not create a real transport. It does not use
LM Studio. It does not open sockets.

`mock_transport_only` is metadata classification, not a performed request.
`future_httpx_localhost_transport` is a future gate, not an active HTTP client.

## Probe Wiring Request Classes

Supported classes:

- `local_provider_metadata_probe_wiring`
- `local_model_list_probe_wiring`
- `mock_transport_probe_wiring`
- `api_route_readiness_future`
- `runtime_command_readiness_future`
- `scheduler_readiness_future`
- `unknown`

Future API/runtime/scheduler classes are future-gated. `unknown` is blocked.

## Execution Mode Classes

Supported classes:

- `metadata_only`
- `mock_transport_only`
- `dry_run_only`
- `future_live_localhost_probe`
- `blocked`
- `unknown`

`future_live_localhost_probe` remains future-gated and not executed. `blocked`
and `unknown` are blocked.

## Transport Classes

Supported classes:

- `no_transport`
- `injected_mock_transport`
- `future_httpx_localhost_transport`
- `future_requests_localhost_transport`
- `unsupported_real_transport`
- `unknown`

`no_transport` means no execution. `injected_mock_transport` is allowed only in
`mock_transport_only` mode. Future HTTP transports are future-gated metadata.
Unsupported real transport and unknown transport are blocked.

## Endpoint Host Classes

Supported classes:

- `localhost`
- `loopback`
- `lan`
- `remote`
- `cloud`
- `unknown`

Only `localhost` and `loopback` can become candidates. LAN, remote, cloud, and
unknown hosts are blocked.

## Endpoint Scope Classes

Allowed candidate scopes:

- `provider_root_metadata_candidate`
- `models_list_metadata_candidate`
- `health_metadata_candidate`

Blocked scopes:

- `generation_blocked`
- `chat_completion_blocked`
- `completion_blocked`
- `embeddings_blocked`
- `rerank_blocked`
- `multimodal_blocked`
- `audio_blocked`
- `file_upload_blocked`
- `tool_call_blocked`
- `unknown`

Model-list metadata is not model availability proof and cannot grant execution.

## Payload Classes

Allowed payload classes:

- `no_payload`
- `metadata_only_empty_request`

Blocked payload classes:

- `prompt_payload_blocked`
- `context_payload_blocked`
- `memory_payload_blocked`
- `repo_payload_blocked`
- `raw_journal_payload_blocked`
- `raw_evidence_payload_blocked`
- `secret_payload_blocked`
- `unknown`

No prompt, context, memory, repo, journal, evidence, or secret payload may be
sent.

## Secret Policy Classes

Allowed classes:

- `no_secret`
- `no_authorization_header`

Blocked or future-gated classes:

- `api_key_future_gated`
- `secret_read_blocked`
- `api_key_validation_blocked`
- `unknown`

This sprint does not read secrets, validate API keys, or send Authorization
headers.

## Timeout Policy Classes

Supported classes:

- `bounded_short_timeout`
- `bounded_medium_timeout`
- `missing_timeout`
- `excessive_timeout`
- `unknown`

Bounded timeout metadata is required. Missing, excessive, or unknown timeout
policy is blocked.

## Cancellation Policy Classes

Supported classes:

- `cancellation_supported_candidate`
- `cancellation_not_modeled`
- `missing_cancellation_policy`
- `unknown`

Explicit cancellation policy metadata is required. `cancellation_not_modeled`
can be represented as metadata, but it remains a future review risk.

## Probe Result Classes

Supported classes:

- `not_executed`
- `mock_success_metadata_candidate`
- `mock_timeout_negative_candidate`
- `mock_connection_refused_negative_candidate`
- `mock_invalid_response_negative_candidate`
- `mock_unauthorized_negative_candidate`
- `future_live_success_metadata_candidate`
- `future_live_negative_candidate`
- `unknown`

Mock result metadata requires injected mock transport. Negative mock results are
candidate metadata only and are not runtime failures. Future live result claims
are blocked in this sprint.

## Runtime/API Readiness Classes

Supported classes:

- `no_runtime_wiring`
- `api_contract_candidate`
- `runtime_command_contract_candidate`
- `requires_policy_gate`
- `requires_capability_lease_future`
- `requires_operator_approval_future`
- `blocked`
- `unknown`

Contract candidates are future-gated. No API route, runtime command, scheduler,
or frontend entry point is added.

## Mock Transport Rules

Mock transport is allowed only as metadata for future tests:

- execution mode must be `mock_transport_only`
- transport class must be `injected_mock_transport`
- mock success is not provider health proof
- mock negative result is not runtime failure
- no real HTTP or socket behavior is permitted

## Future Localhost HTTP Rules

A future real local provider probe must remain:

- explicit opt-in
- backend-owned
- localhost/loopback only
- timeout-bounded
- cancellation-aware
- policy-gated
- no prompt payload
- no context, memory, repo, journal, or evidence payload
- no Authorization header by default
- no generation, embedding, reranking, multimodal, upload, or tool endpoint calls
- negative-evidence aware
- separate from evidence/verifier success

Those rules are documented here but not implemented as runtime behavior.

## Host and Endpoint Restrictions

The contract blocks LAN, remote, cloud, unknown host classes, and all endpoint
scopes that could invoke generation, chat/completion, embeddings, reranking,
multimodal/audio behavior, file upload, or tool execution.

## Payload and Secret Restrictions

Only no-payload or metadata-empty request classes can pass. All prompt, context,
memory, repo, journal, evidence, and secret payload classes are blocked.

API key handling and Authorization headers are out of scope.

## Timeout and Cancellation Requirements

The request must include bounded timeout metadata and explicit cancellation
policy metadata. This does not enforce a real timeout because no request is
performed; it records the future contract expectation.

## Negative Result Classification

Mock timeout, connection refused, invalid response, and unauthorized outcomes
are represented as negative candidate metadata only. They are not evidence,
runtime failures, or verifier outcomes.

## Truthfulness Rules

The contract rejects claims that:

- provider metadata is truth
- model-list metadata is truth
- mock success is provider health proof
- negative mock result is runtime failure
- provider health is proven
- model availability is execution-ready
- probe candidate selects Auto Mode
- benchmark or quality is verified
- self-reported identity is authoritative
- model inventory proves availability

## Relationship to Local Provider Probe Boundary

Probe Boundary metadata can inform wiring readiness. It still cannot authorize a
live probe or prove health. Unsafe probe boundary decisions are rejected.

## Relationship to Probe Design, Provider Health, and Local Model Inventory

Probe Design can describe future phases, Provider Health can classify readiness,
and Local Model Inventory can describe model metadata. None can authorize probe
execution, prove provider health, or prove model availability.

## Relationship to Model Auto Mode

Model Auto Mode cannot select a provider or model based on this wiring readiness
contract. This sprint grants no routing or model-call permission.

## Relationship to Local Model Context Profile

Local Model Context Profile metadata cannot authorize model use, eval proof,
benchmark proof, context delivery, or probe execution.

## Relationship to Context Policy, Identity, and Memory Governance

Context Policy, Identity Scope, and Memory Governance remain separate gates.
This contract does not retrieve context, access memory, send private repo data,
read journals, read evidence, or bypass policy.

## Relationship to Capability Lease

Capability Lease metadata is reference-only. A lease candidate cannot authorize
probe execution in this sprint, and no active lease is created or used.

## Why Metadata and Mock Results Are Not Proof

Provider metadata, model-list metadata, and mock transport results are useful
for future planning, but they are not runtime truth. A real future probe would
need backend-owned execution, evidence, verifier boundaries, and policy gates
before any operational claim could be made.

## Tests Added

Focused tests cover:

- valid metadata-only wiring request
- valid mock transport wiring request
- future HTTP transport future-gating
- mock timeout and connection-refused negative metadata
- missing required fields
- localhost/loopback acceptance
- LAN/remote/cloud/unknown host blocking
- unsupported real transport blocking
- mock transport mode restrictions
- metadata endpoint candidates
- generation/chat/completion/embedding/rerank/multimodal/audio/upload/tool endpoint blocking
- payload blocking
- secret/API-key/Authorization blocking
- timeout and cancellation policy blocking
- truthfulness overclaim rejection
- unsafe related decision rejection
- input immutability
- output invariants proving no probe, no HTTP, no socket, no runtime/API route, no model behavior, no payload transfer, no evidence, and no verifier success

## Intentionally Not Done

This sprint did not:

- perform a real provider probe
- open sockets
- perform HTTP requests
- request `/v1/models`
- call LM Studio
- add FastAPI routes
- add runtime commands
- add schedulers
- add frontend UI
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

The next safe layer could define a mock transport runner that accepts injected
transport objects and still performs no live endpoint calls. Any later live
localhost probe should come only after explicit API/runtime boundary review,
operator policy gates, timeout/cancellation implementation, negative evidence
rules, and tests proving blocked endpoints and payloads cannot execute.

## Remaining Risks

- Real transport behavior remains unimplemented and unverified.
- Runtime/API exposure still needs a separate readiness sprint before any route
  or command exists.
- Negative evidence semantics for live probe failures remain future work.
- Provider self-reported model metadata must remain non-authoritative in later
  implementation.
