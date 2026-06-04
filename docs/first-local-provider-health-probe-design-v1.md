# First Local Provider Health Probe Design v1

## Decision

- Decision: `LOCAL_PROVIDER_PROBE_DESIGN_WITH_TESTS`
- Contract version: `first-local-provider-health-probe-design/1`
- Implementation surface: `src/aegis/core/local_provider_probe_design.py`
- Test surface: `tests/test_core/test_local_provider_probe_design.py`
- Previous sprint: `CAPABILITY_LEASE_CONTRACT_WITH_TESTS`

This sprint designs the first future local provider health probe boundary. It
does not probe endpoints, open sockets, call LM Studio/Ollama/vLLM/OpenAI-
compatible APIs, list models, load models, call models, generate text, generate
embeddings, rerank, run multimodal probes, authenticate providers, validate API
keys, read secrets, inspect provider processes, inspect live model files,
integrate with runtime/API/frontend, create evidence, create verifier success,
use leases, or mutate runtime, journal, evidence, or replay state.

## Scope

The contract validates caller-supplied design metadata only. It classifies:

- provider target class
- endpoint host class
- future probe phase
- timeout, retry, redirect, method, and path constraints
- no-payload constraints
- local-only and no-external-network constraints
- operator review and future lease requirements
- related readiness boundaries
- future evidence candidate types
- future negative evidence candidate types

Every decision preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_provider_probe_design`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_probe_design=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `probe_executed=false`
- `endpoint_probed=false`
- `socket_opened=false`
- `provider_authenticated=false`
- `api_key_validated=false`
- `secret_read=false`
- `model_list_requested=false`
- `model_loaded=false`
- `model_call_performed=false`
- `minimal_generation_performed=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `multimodal_probe_performed=false`
- `provider_process_inspected=false`
- `live_model_files_inspected=false`
- `context_payload_sent=false`
- `memory_payload_sent=false`
- `repo_payload_sent=false`
- `journal_payload_sent=false`
- `evidence_payload_sent=false`
- `data_sent_external=false`
- `health_verified=false`
- `provider_selected_for_execution=false`
- `model_selected_for_execution=false`

## Why First Provider Probe Design Exists

Aegis has local model inventory, Auto Mode, local provider health readiness, and
capability lease contracts. A future provider probe still needs its own boundary
before implementation because "provider reachable" can easily be overclaimed.

This design makes the first probe boundary explicit before any live provider
health runner exists.

## What A Future Probe May Prove

A future properly gated probe may prove only narrow provider-health facts:

- a local endpoint attempt was made
- a local endpoint appeared reachable or unreachable
- provider metadata returned a syntactically valid metadata response
- a model-list endpoint returned a syntactically valid model-list response
- timeout, refused connection, invalid response, unauthorized response, or
  unsupported provider failures happened

Those facts may support provider health status only. They are not task success.

## What A Future Probe May Never Prove

A future probe may never prove:

- model output is trustworthy
- a model is suitable for a user task
- a model call is approved
- context may be sent to a provider
- memory may be retrieved
- repo code may be read
- policy has been satisfied
- a lease is active
- runtime command success
- verifier success for a user task
- evidence for anything beyond provider health

Endpoint reachable is not permission, model usability, task success, policy
approval, evidence for user work, or verifier success.

## Provider Target Classes

Supported target classes:

- `lm_studio_local_openai_compatible`
- `ollama_local_optional`
- `vllm_local`
- `generic_openai_compatible_local`
- `mock_test_provider`
- `unsupported_remote`
- `unsupported_cloud`
- `unknown`

Remote, cloud, and unknown target classes are blocked.

## Endpoint Host Class Rules

Allowed future metadata candidates:

- `localhost`
- `loopback`

Blocked:

- `lan`
- `remote`
- `cloud`
- `unknown`

Allowed host classes still do not prove health in this sprint. They only mean
the design metadata is locally scoped enough to be considered later.

## Probe Phases

Future candidate phases:

- `endpoint_reachability_probe_future`
- `provider_metadata_probe_future`
- `model_list_probe_future`
- `model_role_match_probe_future`

Blocked for now:

- `minimal_generation_probe_future_blocked_for_now`
- `embedding_probe_future_blocked_for_now`
- `reranker_probe_future_blocked_for_now`
- `multimodal_probe_future_blocked_for_now`

`unknown` is blocked.

## Probe Constraints

Probe design metadata must include:

- `max_timeout_ms`
- `max_retries`
- `max_redirects`
- `allowed_methods`
- `allowed_paths`
- `disallowed_paths`
- `no_auth_required`
- `no_secret_logging`
- `no_prompt_payload`
- `no_user_context_payload`
- `no_repo_context_payload`
- `no_memory_context_payload`
- `no_raw_journal_payload`
- `no_raw_evidence_payload`
- `no_external_network`
- `local_only`
- `cancellable`
- `rate_limited`
- `requires_operator_review`
- `requires_capability_lease_future`
- `requires_policy_check`
- `requires_negative_evidence_on_failure`

Rules:

- timeout must be positive and bounded
- retries must be bounded
- redirects are not allowed
- allowed methods are `GET` and `HEAD`
- generation, embedding, rerank, multimodal, and responses paths are blocked
- generation and embedding paths must be explicitly disallowed
- auth/secrets are out of scope

## Result Taxonomy

Supported result statuses:

- `not_executed`
- `design_only`
- `future_probe_candidate`
- `blocked_by_policy`
- `blocked_by_endpoint_host`
- `blocked_by_secret_boundary`
- `blocked_by_unknown_metadata`
- `blocked_by_missing_lease`
- `blocked_by_missing_operator_review`
- `blocked_by_missing_provider_health_readiness`
- `blocked_by_resource_pressure`
- `blocked_by_timeout_policy`
- `unsupported`
- `unknown`

The current helper returns design/future/blocked statuses only. None are
runtime results.

## Future Evidence Model

Candidate evidence types:

- `provider_probe_attempt_future`
- `endpoint_reachable_future`
- `endpoint_unreachable_future`
- `provider_metadata_response_future`
- `model_list_response_future`
- `timeout_negative_evidence_future`
- `refused_connection_negative_evidence_future`
- `invalid_response_negative_evidence_future`
- `unauthorized_negative_evidence_future`
- `unsupported_provider_negative_evidence_future`

These are metadata candidates, not actual evidence in this sprint.

## Negative Evidence Model

Future failed probes must produce negative evidence instead of disappearing.
Negative evidence should preserve at least:

- attempted local endpoint reference
- timeout/refused/invalid/unauthorized/unsupported classification
- bounded timeout/retry configuration
- cancellation status
- no-secret/no-payload confirmation
- failure reason

Negative provider evidence must not by itself mark runtime unhealthy unless a
later policy explicitly says so.

## Timeout, Rate Limit, And Cancellation

Future probes must be bounded:

- timeout capped
- retry count capped
- redirects disabled
- cancellable
- rate limited
- no infinite retry loop
- failure must remain reportable

This sprint only validates the design metadata for those constraints.

## Secret-Safe Logging Requirements

Future probe logs must not contain:

- API keys
- tokens
- credentials
- prompts
- user context
- repo code
- memory content
- raw journal entries
- raw evidence

The design helper requires `no_secret_logging=true` and `no_auth_required=true`.

## No-Payload Rules

Future first probes are metadata-only. They must not send:

- prompt payload
- user context payload
- repo context payload
- memory context payload
- raw journal payload
- raw evidence payload
- external network payload

The helper rejects any request that claims such payloads were sent.

## Relationship To Local Provider Health Readiness

Local Provider Health Readiness is required before a probe design can become a
future candidate. That readiness remains metadata only and cannot authorize a
probe.

## Relationship To Capability Lease

A future repeated/provider probe may require capability lease metadata. Current
lease candidates are not active leases. A lease candidate cannot activate a
probe, grant permission, or replace operator review.

## Relationship To Model Auto Mode

Auto Mode can name a provider/model candidate later, but it cannot authorize a
probe. Probe design cannot select a provider/model for execution.

## Relationship To Context Policy

Context Policy must prevent user/repo/memory/journal/evidence payloads. A
blocked context policy blocks probe design readiness. Context policy metadata
does not allow probe execution.

## Relationship To Policy-as-Code Extension

Policy-as-code cannot be contradicted. A blocked policy extension blocks the
probe design. Policy metadata cannot create evidence, verifier success, active
leases, or runtime dispatch.

## Relationship To Identity And Memory Governance

Identity Scope and Memory Governance cannot be bypassed. They may be relevant
future related decisions, but they do not authorize provider probes and cannot
turn model/provider metadata into permission.

## Relationship To Local Model Inventory

Local Model Inventory metadata cannot authorize model calls, model loading, or
model-list requests. Model listed is not model loaded. Model loaded, if ever
introduced later, is still not model output trust.

## Intentionally Not Done

This sprint intentionally did not:

- probe endpoints
- open sockets
- call providers
- list models
- load models
- call models
- generate text
- generate embeddings
- rerank
- run multimodal probes
- authenticate providers
- validate API keys
- read secrets
- inspect provider processes
- inspect model files/directories
- add runtime/API/frontend behavior
- create evidence or verifier success
- use leases
- mutate runtime, journal, evidence, or replay

## Future Implementation Notes

A future implementation sprint would need:

- explicit local endpoint allowlist
- socket timeout and cancellation handling
- no-redirect enforcement
- retry bounds
- negative evidence creation
- secret-safe log assertions
- no-payload assertions
- operator review or active lease checks
- policy re-checks
- provider-health-only verifier expectations
- failure classifications that do not hide unavailable providers

## Remaining Risks

- Provider reachability can be overinterpreted by UI or operators.
- Model-list responses can become stale quickly.
- Failed provider probes need careful negative evidence semantics.
- Future probe implementation must not leak prompts, repo code, memory, raw
  journal, or raw evidence.
- A later active lease implementation is still unresolved and cannot be assumed.
