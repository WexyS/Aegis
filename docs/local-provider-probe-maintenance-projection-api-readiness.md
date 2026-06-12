# Local Provider Probe Maintenance Projection API Readiness
## Decision

Decision: LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_READINESS_WITH_TESTS

This sprint adds a pure backend-owned readiness contract for representing local provider probe projection metadata in future maintenance, diagnostic, Mission Control, API-response, or CLI summary surfaces.

## Scope

The helper validates caller-supplied projection metadata and related readiness decisions. It classifies how a local provider probe projection may be surfaced without adding API routes, runtime commands, scheduler jobs, frontend UI, provider probing, model execution, runtime health mutation, evidence, verifier success, approval, lease, or capability grants.

## Why Maintenance Projection API Readiness Exists

Local provider probe results need a safe representation before future maintenance/API surfaces expose them. A previous manual smoke can be useful operator metadata, but it must remain display-only:

- `unreachable_negative_candidate` is not runtime failure
- timeout or refused is not runtime failure
- successful metadata is not provider health proof
- model-list metadata is not model availability proof
- retry guidance is not retry authorization
- display severity is not runtime health

## Not Provider Probing, Runtime Health Mutation, Or Frontend Implementation

This contract does not:

- call `/v1/models`
- open sockets
- perform HTTP requests
- probe provider endpoints
- send prompt, context, memory, repo, journal, or evidence payloads
- read API keys or secrets
- send Authorization headers
- load, call, benchmark, embed, rerank, or inspect models
- add API routes
- add runtime commands
- add scheduler jobs
- add frontend UI
- mutate maintenance health or runtime health
- mutate runtime, journal, evidence, or replay state
- create evidence or verifier success

## Projection API Source Classes

- `local_provider_probe_projection`
- `manual_smoke_projection`
- `mock_runner_projection`
- `future_live_runner_projection`
- `maintenance_scan_future_projection`
- `mission_control_future_projection`
- `diagnostic_api_future_projection`
- `caller_supplied_metadata`
- `unknown`

## API Exposure Readiness Classes

- `api_projection_metadata_only`
- `maintenance_projection_candidate`
- `diagnostic_projection_candidate`
- `mission_control_projection_candidate`
- `requires_projection_helper`
- `requires_policy_gate`
- `requires_operator_review_for_retry`
- `blocked_by_missing_projection`
- `blocked_by_truth_label`
- `future_gated`
- `unknown`

Readiness is metadata only. It does not add an API route or authorize any consumer.

## Maintenance Category Classes

- `provider_probe_status`
- `local_provider_reachability`
- `local_model_list_metadata`
- `local_provider_negative_candidate`
- `local_provider_retry_guidance`
- `local_provider_unknown`
- `unknown`

## Consumer Surface Classes

- `maintenance_scan_future`
- `mission_control_future`
- `diagnostic_panel_future`
- `api_response_future`
- `cli_summary_future`
- `unknown`

Consumer surfaces are future display targets only. They are not implemented by this sprint.

## Display Contract Classes

- `non_authoritative_status_card`
- `negative_candidate_notice`
- `metadata_candidate_notice`
- `retry_requires_operator_approval_notice`
- `not_runtime_failure_notice`
- `not_provider_health_proof_notice`
- `not_model_availability_proof_notice`
- `unknown`

Display contract metadata cannot become frontend authority, API authority, health mutation, or retry permission.

## Negative Candidate Semantics

The contract preserves negative result distinctions:

- `unreachable_negative_candidate`
- `timeout_negative_candidate`
- `connection_refused_negative_candidate`
- `invalid_response_negative_candidate`
- `unauthorized_negative_candidate`
- `unsupported_endpoint_negative_candidate`
- `cancelled_negative_candidate`

These are projection candidates, not runtime failures, not provider health proof, not verifier success, and not evidence.

## Unreachable, Timeout, Refused, Invalid, Unauthorized

Unreachable, timeout, connection-refused, invalid response, unauthorized, unsupported endpoint, and cancelled results should remain distinct when supplied by the source projection. Future consumers should not collapse them into verified health failure.

## Retry Requires Operator Approval

Retryable negative candidates preserve `retry_requires_operator_approval`.

This means:

- retry may be suggested as an operator-reviewed next step
- retry is not authorized by projection
- no live probe is performed
- no socket or HTTP request is opened
- no live gate is bypassed

## Manual Smoke Result Representation

The earlier LM Studio manual smoke can be represented as:

- `projection_api_source_class=manual_smoke_projection`
- `api_exposure_readiness_class=requires_operator_review_for_retry`
- `maintenance_category_class=local_provider_retry_guidance`
- `display_contract_class=retry_requires_operator_approval_notice`
- `probe_result_class=unreachable_negative_candidate`

This preserves the fact that the endpoint was unreachable during that smoke without treating the result as runtime failure or authorizing a retry.

## Truthfulness Rules

The validator rejects claims that:

- negative result is runtime failure
- empty model list is runtime failure
- metadata success is provider health proof
- model-list success is model availability proof
- downloaded models prove served availability
- self-reported model identity is authority
- benchmark or quality is verified
- Auto Mode selected a provider or model
- Local Model Inventory proves availability
- display/API/frontend surfaces become authority

## Relationship To Probe Result Projection

Local Provider Probe Result Projection can provide safe metadata for this readiness helper. It remains a reference only and cannot become runtime health, model availability proof, retry permission, evidence, or verifier success.

## Relationship To Real Localhost Runner

The real localhost runner may later produce probe metadata. This readiness contract does not rerun it, call endpoints, open sockets, or convert runner output into provider health proof.

## Relationship To Live Gate

Live Gate decisions can inform future retry policy, but this helper cannot authorize live probing or bypass operator gates.

## Relationship To Mock Runner / Wiring / Boundary

Mock Runner, Wiring, Boundary, and Design decisions are related references only. Mock results are not real provider proof. Wiring readiness does not add API routes or runtime commands.

## Relationship To Provider Health / Local Model Inventory

Provider Health and Local Model Inventory metadata cannot become verified health, model availability, loaded model proof, model identity proof, or benchmark proof through this contract.

## Relationship To Model Auto Mode

Maintenance projection cannot select a model, choose a provider, authorize fallback, or enable Auto Mode execution.

## Relationship To Local Model Context Profile

Local Model Context Profile metadata cannot authorize model use, context delivery, model quality claims, or benchmark claims through maintenance projection.

## Relationship To Context Policy / Identity / Memory Governance

Context Policy, Identity Scope, and Memory Governance cannot be bypassed. This contract retrieves no memory, reads no context, sends no repo data, and sends no journal or evidence payload.

## Relationship To Capability Lease

A capability lease candidate cannot authorize retry, probing, provider access, model execution, or API exposure through this projection.

## Not Proof, Evidence, Verifier Success, Or Runtime Failure

Maintenance projection API readiness is not:

- runtime health
- maintenance health
- provider health proof
- model availability proof
- model identity proof
- benchmark proof
- retry authorization
- API implementation
- frontend implementation
- evidence
- verifier success
- execution permission

## Tests Added

Added `tests/test_core/test_local_provider_probe_maintenance_projection.py`.

The tests cover valid unreachable, timeout, model-list success, empty model-list, retry guidance, required fields, projection references, taxonomy validation, truthfulness overclaims, related decision safety, non-execution flags, authority/grant/evidence/verifier rejection, immutability, and invariant false outputs.

## Intentionally Not Done

This sprint did not:

- perform live probes
- call `/v1/models`
- open sockets
- perform HTTP requests
- add API routes
- add runtime commands
- add scheduler jobs
- add frontend UI
- call or load models
- generate, embed, rerank, or run multimodal inference
- send prompt, context, memory, repo, journal, or evidence payloads
- read API keys or secrets
- log response bodies
- call cloud, LAN, or remote endpoints
- mutate runtime, journal, evidence, replay, maintenance health, or runtime health
- create evidence or verifier success

## Future Implementation Notes

Future API or UI work should consume this contract as a projection boundary. Any real API route must remain backend-owned, preserve the same false invariant fields, and avoid converting display severity into runtime health. Any retry must go through the live gate and require explicit operator approval.

## Remaining Risks

- Future consumers could still mislabel metadata if they bypass this helper.
- Stale projection metadata can mislead operators if freshness is hidden.
- A future API surface must avoid implying runtime health from display cards.
- Retry workflow still needs a separate operator-gated execution contract.
