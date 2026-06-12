# Provider Probe Maintenance Surface UI Readiness
## Decision

Decision: PROVIDER_PROBE_MAINTENANCE_SURFACE_UI_READINESS_WITH_TESTS

This sprint adds a pure provider-probe maintenance surface display readiness contract.

## Scope

Implemented:

- `src/aegis/core/local_provider_probe_surface_display.py`
- `tests/test_core/test_local_provider_probe_surface_display.py`

The helper validates caller-supplied display metadata for future Maintenance Scan, Mission Control, or diagnostic surfaces. It does not implement a visible frontend panel, provider probing, retry actions, endpoint polling, runtime health mutation, evidence, verifier success, approval, capability, or lease grants.

## Why Surface UI Readiness Exists

The read-only endpoint `GET /maintenance/local-provider/probe-projection` can expose projection states such as `no_projection_available`, `not_observed`, metadata candidates, and negative candidates. Future UI surfaces need a stable display contract so those states are not accidentally rendered as runtime failures, verified provider health, verified model availability, retry authorization, or frontend authority.

## Why This Is Not Frontend Implementation

This sprint adds no visible UI, no React component, no polling hook, no button, and no retry control. It is a backend-owned display/readiness validator for future UI consumers.

## Why This Is Not Provider Probing

The helper does not:

- call `/v1/models`
- open sockets
- perform HTTP requests
- call local provider endpoints
- call model generation, embedding, reranking, or multimodal endpoints
- send prompts, context, memory, repo data, journal data, or evidence data
- read API keys or send Authorization headers
- inspect model files or directories

## Why This Is Not Runtime Health Mutation

Display status and severity are display metadata only. The helper always returns:

- `runtime_health_mutated=false`
- `maintenance_health_mutated=false`
- `mutation_performed=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_provider_probe_surface_display`

## Display Source Classes

- `maintenance_probe_projection_api`
- `local_provider_probe_projection`
- `manual_smoke_projection_fixture`
- `synthetic_fixture`
- `mission_control_future`
- `maintenance_scan_future`
- `unknown`

`unknown` requires clarification and is blocked.

## Display State Classes

- `no_projection_available`
- `not_observed`
- `not_configured`
- `metadata_candidate`
- `model_list_candidate`
- `empty_model_list_candidate`
- `unreachable_negative_candidate`
- `timeout_negative_candidate`
- `connection_refused_negative_candidate`
- `invalid_response_negative_candidate`
- `unauthorized_negative_candidate`
- `unsupported_endpoint_negative_candidate`
- `cancelled_negative_candidate`
- `blocked_by_policy`
- `future_gated`
- `unknown`

`unknown` requires clarification and is blocked.

## UI Meaning Classes

Allowed:

- `neutral_no_data`
- `informational_candidate`
- `warning_negative_candidate`
- `operator_review_recommended`
- `retry_requires_operator_approval`
- `blocked`
- `future_gated`
- `unknown`

`unknown` remains blocked until clarified.

## Forbidden UI Meanings

Forbidden:

- `runtime_failure`
- `provider_health_verified`
- `model_availability_verified`
- `model_unavailable_proof`
- `verifier_success`
- `evidence_available`
- `retry_authorized`
- `execution_ready`
- `auto_mode_selected`
- `frontend_authority`

These meanings are rejected because frontend display cannot become runtime truth, provider proof, model proof, retry permission, evidence, verifier success, execution readiness, Auto Mode selection, or authority.

## Recommended Wording

- `no_projection_available`: "No current provider probe projection is available."
- `not_observed`: "Provider probe has not been observed."
- `unreachable_negative_candidate`: "Provider endpoint was unreachable during the observed probe; this is a negative candidate, not a runtime failure."
- `metadata_candidate`: "Metadata candidate only; not provider health proof."
- `model_list_candidate`: "Model-list metadata candidate only; not model availability proof."
- `empty_model_list_candidate`: "Empty model-list candidate; not runtime failure."
- retry guidance: "Retry requires explicit operator approval."

Display wording that claims runtime failure, verified health, verified model availability, evidence availability, verifier success, retry authorization, execution readiness, or Auto Mode selection is rejected.

## Color And Severity Guidance

- `no_projection_available`, `not_observed`, `not_configured`: neutral/info, not red/fail
- `metadata_candidate`: info/neutral, not green verified
- `model_list_candidate`: info/neutral, not green available
- `empty_model_list_candidate`: info/neutral, not runtime failure
- negative candidates: attention/warning, not runtime fail
- `blocked_by_policy`: blocked/warning, not retry-ready
- `future_gated`: future/neutral, not enabled
- `unknown`: unknown and review-required

Severity is not runtime health.

## No Projection Available Semantics

`no_projection_available` means there is no current durable provider probe projection. It does not mean:

- provider failure
- runtime failure
- model unavailable
- evidence missing failure
- verifier failure
- retry needed

The expected UI meaning is `neutral_no_data`.

## Not Observed Semantics

`not_observed` means provider probing has not been observed. It does not prove that a provider is unreachable, healthy, unhealthy, configured, unavailable, or available.

The expected UI meaning is `neutral_no_data`.

## Negative Candidate Semantics

Negative candidates preserve observed or projected distinctions:

- unreachable
- timeout
- connection refused
- invalid response
- unauthorized
- unsupported endpoint
- cancelled

These are negative candidates only. They are not runtime failures, provider health proof, model availability proof, evidence, verifier success, or retry authorization.

Retryable negative candidates require explicit operator approval before any future retry.

## Metadata And Model-List Candidate Semantics

Metadata candidates are informational only.

Model-list candidates are not model availability proof. Empty model-list candidates are not runtime failure. No display state can claim provider health, model availability, model identity, benchmark quality, or readiness to route Auto Mode.

## Retry Requires Operator Approval

The helper may return retry guidance for retryable negative candidates:

- `retry_guidance=Retry requires explicit operator approval.`
- `retry_authorized=false`
- `retry_control_exposed=false`
- `action_control_exposed=false`

Future retry actions need a separate operator-approved live probe path.

## Relationship To Maintenance Projection API Surface

The Maintenance Projection API Surface exposes read-only projection data. This display helper can reference that response as source metadata, but it cannot convert API fields into authority, provider health, model availability, evidence, verifier success, or retry permission.

## Relationship To Probe Maintenance Projection Readiness

Probe Maintenance Projection Readiness remains the upstream contract for maintenance projection metadata. This helper consumes or references it only as display source metadata.

## Relationship To Probe Result Projection

Probe Result Projection preserves probe-result distinctions. This display helper maps those distinctions into UI-safe meanings without weakening the original non-authority rules.

## Relationship To Real Localhost Runner

The Real Localhost Runner is not invoked. A future runner may produce current projection metadata only through a separate approved live-gate path.

## Relationship To Provider Health / Local Model Inventory

Provider Health and Local Model Inventory metadata cannot authorize display proof. Display readiness cannot prove provider health, model identity, model availability, benchmark quality, or model suitability.

## Relationship To Model Auto Mode

Display readiness cannot select a provider, select a model, route Auto Mode, or authorize model calls. Auto Mode remains a separate future/runtime-controlled decision surface.

## Relationship To Future Mission Control UI

Future Mission Control UI may use this contract to render no-data, informational, warning, blocked, and future-gated states. It must not expose retry/action controls through this helper or hide runtime truth.

## Intentionally Not Done

This sprint did not:

- add visible frontend UI
- change frontend behavior
- add polling
- add retry buttons or action controls
- add API endpoints
- call provider endpoints
- open sockets or perform HTTP requests
- load or call models
- generate embeddings
- rerank
- perform multimodal inference
- read API keys or secrets
- send prompts, context, memory, repo, journal, or evidence payloads
- mutate runtime or maintenance health
- mutate runtime, journal, evidence, or replay state
- create evidence
- create verifier success
- grant approval, capability, or lease

## Future Implementation Notes

A future UI implementation can consume this display contract as a type/schema layer. It should keep no-data states neutral, metadata states informational, negative candidates warning-only, and retry text separate from retry controls. Any retry control must be implemented only after a separate operator-approved live probe action sprint.

## Remaining Risks

- A future UI could still misuse colors or icons if it bypasses this helper.
- A future durable projection source must preserve current/stale/historical/fixture distinctions.
- Future retry UI needs a separate hard gate to avoid turning guidance into authorization.
