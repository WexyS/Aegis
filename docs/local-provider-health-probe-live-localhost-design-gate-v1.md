# Local Provider Health Probe Live Localhost Design Gate v1

## Decision

- Decision: `LOCAL_PROVIDER_PROBE_LIVE_GATE_WITH_TESTS`
- Contract version: `local-provider-health-probe-live-gate/1`
- Implementation surface: `src/aegis/core/local_provider_probe_live_gate.py`
- Test surface: `tests/test_core/test_local_provider_probe_live_gate.py`
- Previous sprint: `LOCAL_PROVIDER_PROBE_MOCK_RUNNER_WITH_TESTS`

This sprint adds a pure live-localhost probe design gate. It is the final
readiness contract before any real local LM Studio or local OpenAI-compatible
provider probe could be considered.

It does not call LM Studio, OpenAI-compatible endpoints, `/v1/models`, `/models`,
provider root, health, generation, chat/completion, embeddings, rerank,
multimodal, audio, file upload, or tool-call endpoints. It does not open sockets,
perform HTTP requests, use real transport, load models, call models, validate
API keys, read secrets, create evidence, mark verifier success, create runtime
routes or commands, or mutate runtime state.

## Scope

The helper validates caller-supplied live gate metadata only. It classifies:

- live gate class
- live gate status class
- future live transport class
- endpoint host class
- endpoint scope class
- payload policy class
- logging/redaction class
- timeout policy class
- cancellation policy class
- future result class
- paired probe boundary, wiring, and mock runner references
- related decision references

The output is not:

- a live probe
- provider access
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
- `execution_permission=not_granted_by_local_provider_probe_live_gate`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_live_gate=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `api_route_added=false`
- `runtime_command_added=false`
- `scheduler_added=false`
- `live_probe_performed=false`
- `real_endpoint_probed=false`
- `socket_opened=false`
- `http_request_performed=false`
- `provider_probed=false`
- `real_transport_used=false`
- `mock_transport_only=false`
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
- `response_body_logged=false`
- `secret_logged=false`
- `provider_health_verified=false`
- `model_availability_verified=false`
- `model_identity_verified=false`
- `benchmark_claim_verified=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`

## Why Live Localhost Design Gate Exists

The mock transport runner proved mock result classification without real
transport. The next risk is live localhost probing. Before any real endpoint
request exists, Aegis needs a final design gate that documents the preconditions
and blocks unsafe assumptions.

This contract records the required future gates for transport, endpoint,
payload, timeout, cancellation, logging, negative result semantics, evidence,
verifier, and operator review.

## Why This Is Not Real Provider Probing

No real transport is accepted or used. The helper does not accept an HTTP client,
does not call a callable, does not open sockets, does not send HTTP, does not
send payloads, and does not read secrets.

`future_httpx_localhost_only` and similar classes are future metadata. They are
not active transport.

## Live Gate Classes

Supported classes:

- `localhost_metadata_probe_gate`
- `localhost_model_list_probe_gate`
- `localhost_health_metadata_probe_gate`
- `live_probe_rollout_gate`
- `operator_review_gate`
- `evidence_semantics_gate`
- `verifier_semantics_gate`
- `blocked`
- `unknown`

Rollout, operator review, evidence semantics, and verifier semantics gates are
future-gated review surfaces. `blocked` and `unknown` cannot be ready.

## Live Gate Status Classes

Supported classes:

- `design_gate_ready_metadata_only`
- `requires_policy_gate`
- `requires_operator_review`
- `requires_capability_lease_future`
- `requires_timeout_cancellation`
- `requires_negative_evidence_semantics`
- `requires_redaction_policy`
- `requires_result_classifier`
- `requires_mock_runner`
- `blocked_by_missing_boundary`
- `blocked_by_missing_wiring`
- `blocked_by_missing_mock_runner`
- `blocked_by_host`
- `blocked_by_endpoint`
- `blocked_by_payload`
- `blocked_by_secret_policy`
- `future_gated`
- `unknown`

Only `design_gate_ready_metadata_only` can produce a ready design-gate decision.
Future-gated statuses stay future-gated and do not execute anything.

## Future Live Transport Classes

Supported classes:

- `no_transport`
- `future_injected_http_client`
- `future_httpx_localhost_only`
- `future_requests_localhost_only`
- `blocked_real_transport`
- `unknown`

`no_transport` means no execution. Future HTTP transport classes are future
gates and not active clients. Blocked real transport and unknown transport are
rejected.

## Endpoint Scope Classes

Allowed future candidate scopes:

- `provider_root_metadata_future`
- `models_list_metadata_future`
- `health_metadata_future`

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

Model-list metadata is not model availability proof.

## Payload Policy Classes

Allowed classes:

- `no_payload`
- `empty_metadata_request_only`

Blocked classes:

- `prompt_payload_blocked`
- `context_payload_blocked`
- `memory_payload_blocked`
- `repo_payload_blocked`
- `raw_journal_payload_blocked`
- `raw_evidence_payload_blocked`
- `secret_payload_blocked`
- `unknown`

No prompt, context, memory, repo, journal, evidence, or secret payload may be
sent by this gate.

## Logging and Redaction Classes

Allowed classes:

- `no_payload_logging`
- `endpoint_only_redacted`
- `status_code_only_future`
- `response_shape_only_future`

Blocked classes:

- `response_body_logging_blocked`
- `secret_logging_blocked`
- `unknown`

Future live probes must not log response bodies or secrets by default.

## Future Result Classes

Supported classes:

- `future_metadata_success_candidate`
- `future_model_list_candidate`
- `future_timeout_negative_candidate`
- `future_connection_refused_negative_candidate`
- `future_invalid_response_negative_candidate`
- `future_unauthorized_negative_candidate`
- `future_unsupported_endpoint_negative_candidate`
- `future_cancelled_negative_candidate`
- `not_executed`
- `unknown`

Future negative results require negative evidence semantics gates. They are not
runtime failures in this sprint.

## Host Restrictions

Only `localhost` and `loopback` are future candidates. LAN, remote, cloud, and
unknown host classes are blocked.

## Endpoint and Action Restrictions

Generation, chat/completion, embeddings, rerank, multimodal/audio, file upload,
and tool-call scopes are blocked. This design gate allows only future metadata
endpoint classes.

## Payload and Secret Restrictions

Payload policy must be no-payload or empty metadata request only. Secret-bearing
payloads, Authorization headers, API key validation, and secret reads are out of
scope and are rejected by behavior flags.

## Timeout and Cancellation Requirements

Bounded timeout metadata is required. Excessive, missing, or unknown timeout
policy is blocked. Cancellation policy metadata is required. If cancellation is
not modeled, the result is review metadata only.

## Logging and Redaction Requirements

The gate permits only redacted metadata logging plans. Response body logging and
secret logging are blocked.

## Future Negative Result Semantics

Timeout, connection refused, invalid response, unauthorized, unsupported
endpoint, and cancellation outcomes may be future negative candidates only when
negative evidence semantics are separately gated.

They are not runtime failures, evidence, or verifier outcomes in this sprint.

## Truthfulness Rules

The contract rejects claims that:

- future success is provider health proof
- future model list is model availability proof
- future negative result is runtime failure
- provider metadata is truth
- model-list metadata is truth
- provider health is proven
- model availability is execution-ready
- self-reported identity is authoritative
- benchmark or quality is verified
- Auto Mode can select a provider/model from live gate readiness
- Local Model Inventory proves availability

## Relationship to Mock Runner

Mock Runner metadata can inform the live gate, but it remains mock-only and
cannot authorize live transport. Unsafe mock runner decisions are rejected.

## Relationship to Probe Wiring

Probe Wiring can describe future API/runtime design, but it cannot authorize
runtime routes, commands, schedulers, or live probes.

## Relationship to Probe Boundary

Probe Boundary can inform host, endpoint, payload, and secret rules. It cannot
authorize live provider access.

## Relationship to Probe Design, Provider Health, and Local Model Inventory

Probe Design can describe phases. Provider Health can classify readiness. Local
Model Inventory can describe model metadata. None can prove health, availability,
identity, quality, or execution safety.

## Relationship to Model Auto Mode

Model Auto Mode cannot select a provider or model from this design gate. The
gate grants no routing permission.

## Relationship to Local Model Context Profile

Local Model Context Profile metadata cannot authorize model use, eval proof,
benchmark proof, context delivery, or live probe execution.

## Relationship to Context Policy, Identity, and Memory Governance

Context Policy, Identity Scope, and Memory Governance remain separate gates.
This contract does not retrieve context, access memory, send private repo data,
read journals, read evidence, or bypass policy.

## Relationship to Capability Lease

Capability Lease metadata is reference-only. No lease is created, granted, or
used. A lease candidate cannot authorize live probe execution in this sprint.

## Why Future Results Are Not Proof

Future provider metadata, model-list metadata, and negative results are design
targets only. They are not runtime truth because no backend-owned live probe,
evidence chain, verifier boundary, or policy-gated execution occurred.

## Tests Added

Focused tests cover:

- valid localhost metadata/model-list/health design gates
- operator review, evidence semantics, and verifier semantics gates
- missing required fields
- missing source refs/provenance
- missing probe boundary/wiring/mock runner references
- localhost/loopback candidate handling
- LAN/remote/cloud/unknown host blocking
- future transport future-gating
- blocked real transport rejection
- metadata endpoint candidates
- generation/chat/completion/embedding/rerank/multimodal/audio/upload/tool endpoint blocking
- no-payload and empty metadata request policies
- prompt/context/memory/repo/journal/evidence/secret payload blocking
- redacted logging policies
- response body and secret logging blocking
- timeout and cancellation policy requirements
- future negative result semantics
- truthfulness overclaim rejection
- unsafe related decision rejection
- input and related decision immutability
- output invariants proving no live probe, no HTTP/socket, no real transport, no runtime/API route, no model behavior, no payload transfer, no logging of response bodies/secrets, no evidence, and no verifier success

## Intentionally Not Done

This sprint did not:

- perform a live endpoint probe
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
- log response bodies
- mutate runtime/journal/evidence/replay
- create evidence or verifier success
- grant approval, lease, or capability

## Future Implementation Notes

The next live runner sprint should be explicitly approved. It should use an
injected HTTP client, localhost/loopback enforcement, timeout and cancellation
enforcement, no-payload request construction, response-shape-only logging,
negative evidence semantics, operator policy gates, and tests proving blocked
endpoints and payloads cannot execute.

## Remaining Risks

- Real transport behavior remains unimplemented and unverified.
- Runtime/API exposure still needs a separate explicit sprint.
- Live negative evidence semantics remain future work.
- Future consumers must preserve the distinction between design-gate readiness
  and operational truth.
