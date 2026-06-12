# Local Provider Health Probe Real Localhost Runner
## Decision

Decision: LOCAL_PROVIDER_PROBE_REAL_LOCALHOST_RUNNER_WITH_TESTS

This sprint adds a narrow localhost-only provider metadata probe runner contract for Aegis. The runner can call only an explicitly supplied localhost or loopback endpoint through an injected transport object. Automated tests use mock transport only.

## Scope

The runner supports metadata-only GET probes for future LM Studio or OpenAI-compatible local provider checks:

- provider root metadata
- models-list metadata
- health metadata

It does not wire into the parser, orchestrator, Auto Mode, runtime command handling, API routes, scheduler, or frontend.

## Why This Runner Exists

Aegis needs a first real local provider metadata probe path before provider health can become operator-visible product behavior. The runner provides a bounded local-only transport boundary so future manual smoke can test endpoint reachability without sending prompts, repo content, memory, secrets, or runtime journals.

## Localhost-Only Boundary

Allowed hosts:

- `localhost`
- loopback IPs such as `127.0.0.1`
- IPv6 loopback such as `::1`

Blocked before transport:

- LAN addresses
- remote/cloud hosts
- unknown hosts
- malformed URLs
- spoofed localhost names such as `localhost.evil.test`
- URL credentials

The runner does not support LAN, remote, or cloud provider probing.

## Endpoint Restrictions

Allowed endpoint classes:

- `provider_root_metadata`
- `models_list_metadata`
- `health_metadata`

Blocked endpoint classes:

- `generation`
- `chat_completion`
- `completion`
- `embeddings`
- `rerank`
- `multimodal`
- `audio`
- `file_upload`
- `tool_call`
- `unknown`

Blocked endpoint paths are rejected before transport, including chat, completion, embedding, rerank, audio, file, tool, and generation-like paths.

## Payload, Secret, And Logging Restrictions

The runner is GET-only:

- no request body
- no prompt payload
- no context payload
- no memory payload
- no repo payload
- no raw journal payload
- no raw evidence payload
- no Authorization header
- no API key validation
- no secret reads
- no response body logging
- no secret logging

Transport calls are created with empty headers and `body=None`.

## Timeout And Cancellation

The request must supply bounded timeout metadata. Timeout values must be positive and short. Injected transports can surface:

- `TimeoutError`
- `ConnectionRefusedError`
- `OSError`
- `LocalProviderProbeCancelled`

These become negative metadata candidates, not runtime failures.

## Result Semantics

Allowed result classes:

- `metadata_success_candidate`
- `model_list_success_candidate`
- `health_metadata_success_candidate`
- `timeout_negative_candidate`
- `connection_refused_negative_candidate`
- `unreachable_negative_candidate`
- `invalid_response_negative_candidate`
- `unauthorized_negative_candidate`
- `unsupported_endpoint_negative_candidate`
- `cancelled_negative_candidate`
- `not_executed`
- `unknown`

Successful metadata is not provider health proof. A successful model list is not model availability proof. Self-reported provider or model identity is not authority. Negative probe results are not runtime failures.

## Related Decision Handling

The runner can reference prior readiness decisions, including:

- Local Provider Probe Live Gate
- Local Provider Probe Wiring
- Local Provider Probe Boundary
- Local Provider Probe Mock Runner
- Local Provider Health
- Model Auto Mode
- Local Model Inventory
- Local Model Context Profile
- Context Policy
- Identity Scope
- Memory Governance
- Policy Extension
- Capability Lease
- Mission Control
- Tool Simulation

Related decisions are references only. Any related decision claiming authority, dispatch, grants, evidence, verifier success, model calls, payload transfer, secret use, external calls, or runtime mutation is rejected.

## Non-Authority Invariants

The runner always reports:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_local_provider_probe_runner`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_probe_runner=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `provider_health_verified=false`
- `model_availability_verified=false`
- `model_identity_verified=false`
- `benchmark_claim_verified=false`
- `model_call_performed=false`
- `prompt_payload_sent=false`
- `context_payload_sent=false`
- `memory_payload_sent=false`
- `repo_payload_sent=false`
- `raw_journal_payload_sent=false`
- `raw_evidence_payload_sent=false`
- `authorization_header_sent=false`
- `cloud_provider_called=false`
- `lan_or_remote_endpoint_called=false`
- `data_sent_external=false`
- `response_body_logged=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `read_only_projection=true`

## Tests Added

Focused tests cover:

- valid localhost provider root probe using injected mock transport
- valid localhost models-list probe using injected mock transport
- loopback URL acceptance
- timeout, refused, unreachable, unauthorized, invalid, unsupported, and cancelled negative candidates
- LAN/remote/cloud/spoofed/malformed URL blocking before transport
- blocked generation/chat/completion/embedding/rerank/multimodal/audio/upload/tool endpoints before transport
- payload, secret, Authorization, API key, response-body logging, and secret logging rejection
- safe live gate reference handling
- unsafe related decision rejection
- truthfulness overclaim rejection
- no mutation of inputs or related decisions
- output non-authority invariants

## Intentionally Not Done

This sprint did not:

- call generation/chat/completion endpoints
- call embedding/reranker/multimodal/audio endpoints
- send prompts or context
- send repo, memory, journal, evidence, or secret payloads
- read or validate API keys
- inspect model files or directories
- load or benchmark models
- add parser/orchestrator model calls
- add API routes, runtime commands, scheduler jobs, or frontend UI
- mutate runtime, journal, evidence, or replay state
- create evidence or verifier success
- grant approval, capability, or lease

## Manual Smoke Notes

Manual smoke remains optional and operator-gated. If performed later, it should target only explicit localhost or loopback metadata/model-list endpoints, use no request body and no Authorization headers, and report only metadata candidates.

## Remaining Risks

- Provider response shapes vary; the runner classifies only coarse shapes.
- Endpoint availability is not model availability.
- Provider self-reported metadata can drift or be inaccurate.
- Real operator smoke still needs separate procedure and reporting.
- This runner is intentionally not connected to Auto Mode or provider routing.
