# Local Provider Probe Maintenance Projection API Surface v1

## Decision

Decision: LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_API_SURFACE_WITH_TESTS

This sprint adds a narrow backend-owned read-only API surface for local provider probe maintenance projection metadata.

## Scope

Implemented:

- a read-only response builder
- a read-only `GET /maintenance/local-provider/probe-projection` endpoint
- focused API tests

The endpoint exposes current projection availability honestly. It does not probe providers, mutate runtime health, create evidence, create verifier success, authorize retry, or imply provider health or model availability.

## Endpoint Added

`GET /maintenance/local-provider/probe-projection`

The endpoint currently returns `no_projection_available` because Aegis does not yet have a durable/current provider probe projection source in backend state.

## Why This Is Read-Only Projection Only

The API response is a projection for future maintenance and diagnostic consumers. It is not a command, action, retry workflow, provider health check, model availability check, model identity check, evidence record, verifier result, or frontend authority source.

## Why This Is Not Provider Probing

The endpoint does not:

- call `/v1/models`
- call provider endpoints
- open sockets
- perform HTTP requests
- invoke the local provider probe runner
- invoke the live gate
- start background tasks
- send Authorization headers
- read API keys or secrets
- log raw response bodies

## Why This Is Not Runtime Health Mutation

The endpoint returns:

- `runtime_health_mutated=false`
- `maintenance_health_mutated=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`

Display status and severity remain display metadata only.

## No-Current-Projection Semantics

If no durable/current provider probe projection source exists, the endpoint returns:

- `projection_result_class=no_projection_available`
- `api_surface_status_class=no_current_probe_result`
- `projection_available=false`
- `current_projection_available=false`
- `source_current=false`
- `probe_result_class=not_observed`

The previous manual smoke result is not replayed as current runtime state.

## Negative Candidate Semantics

Synthetic or future safe projection metadata can represent:

- `provider_probe_unreachable_candidate`
- `provider_probe_timeout_candidate`
- `provider_probe_connection_refused_candidate`
- `provider_probe_invalid_response_candidate`
- `provider_probe_unauthorized_candidate`
- `provider_probe_unsupported_endpoint_candidate`

These are not runtime failures, not provider health proof, not model availability proof, not evidence, and not verifier success.

## Metadata Candidate Semantics

Synthetic or future safe projection metadata can represent:

- `provider_probe_metadata_candidate`
- `provider_probe_model_list_candidate`
- `provider_probe_empty_model_list_candidate`

Metadata candidates are not provider health proof. Model-list candidates are not model availability proof. Empty model-list candidates are not runtime failure.

## Retry Requires Operator Approval

Retryable negative candidates may set `requires_operator_approval_for_retry=true`.

This does not authorize retry:

- `retry_authorized=false`
- `live_probe_performed=false`
- `real_endpoint_probed=false`
- `socket_opened=false`
- `http_request_performed=false`

Any future retry must go through an explicit operator-gated live probe path.

## Relationship To Probe Maintenance Projection Readiness

This API surface consumes the projection readiness contract added in v1. It uses the maintenance projection validator for supplied metadata fixtures and preserves the same non-authority invariants.

## Relationship To Probe Result Projection

Probe Result Projection remains the upstream metadata contract. This API surface does not create probe results and does not treat historical chat/manual smoke metadata as current state.

## Relationship To Real Localhost Runner

The Real Localhost Runner is not imported or invoked. Future runner output can be supplied as backend-owned projection metadata after a separately approved probe path.

## Relationship To Maintenance Scan / Mission Control Future UI

Maintenance Scan and Mission Control can later consume this endpoint as display metadata. They must not turn response fields into authority, provider health proof, retry controls, model availability, or runtime health.

## API And Frontend Authority Boundary

The response includes:

- `frontend_authority=false`
- `api_authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_local_provider_probe_api_surface`

API and frontend consumers cannot become authority through this projection.

## Intentionally Not Done

This sprint did not:

- probe localhost
- call provider endpoints
- call `/v1/models`
- send prompts or context
- read API keys or secrets
- send Authorization headers
- load or call models
- generate embeddings
- rerank
- run multimodal inference
- add POST/action/retry endpoints
- add scheduler/background tasks
- add frontend UI
- mutate runtime health or maintenance health
- mutate runtime, journal, evidence, or replay state
- create evidence or verifier success

## Future Implementation Notes

Future work can connect a durable backend-owned projection source once a separate probe execution path stores or exposes current projection metadata safely. That source must preserve freshness, provenance, and negative-candidate semantics. Any retry action needs a separate operator approval and live gate.

## Remaining Risks

- Future consumers could misread `no_projection_available` as provider failure if labels are hidden.
- A future durable projection source must distinguish current, stale, historical, and fixture metadata.
- Future UI work must avoid adding retry buttons that bypass operator approval.
