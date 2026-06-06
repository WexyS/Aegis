# Local Provider Probe Result Projection / Maintenance Surface Readiness v1

## Decision

Decision: LOCAL_PROVIDER_PROBE_PROJECTION_READINESS_WITH_TESTS

This sprint adds a pure projection contract for representing local provider probe result metadata in future Maintenance Scan, Mission Control, or diagnostic surfaces.

## Scope

The projection helper accepts caller-supplied probe result metadata and related readiness decisions. It classifies how a result may be displayed without performing provider probing, changing runtime health, creating evidence, creating verifier success, or granting execution permission.

## Why Probe Result Projection Exists

Local provider probes can produce useful metadata candidates, including negative candidates such as `unreachable_negative_candidate`. Aegis needs a way to surface these results honestly:

- unreachable is not a runtime failure
- timeout is not a runtime failure
- connection refused is not a runtime failure
- successful metadata is not provider health proof
- model-list metadata is not model availability proof
- projection is not execution permission

## Not Provider Probing Or Runtime Health Mutation

This contract does not:

- perform live probes
- open sockets
- perform HTTP requests
- call provider endpoints
- add API routes, runtime commands, or scheduler jobs
- mutate maintenance health
- mutate runtime health
- mutate journal, evidence, or replay state
- create evidence or verifier success

## Projection Source Classes

- `manual_smoke_result`
- `mock_runner_result`
- `future_live_runner_result`
- `provider_probe_runner_result`
- `maintenance_scan_projection_future`
- `mission_control_projection_future`
- `caller_supplied_metadata`
- `unknown`

## Probe Result Classes

- `metadata_success_candidate`
- `model_list_success_candidate`
- `health_metadata_success_candidate`
- `unreachable_negative_candidate`
- `timeout_negative_candidate`
- `connection_refused_negative_candidate`
- `invalid_response_negative_candidate`
- `unauthorized_negative_candidate`
- `unsupported_endpoint_negative_candidate`
- `cancelled_negative_candidate`
- `empty_model_list_candidate`
- `not_observed`
- `not_executed`
- `unknown`

## Maintenance Surface Status Classes

- `provider_probe_not_configured`
- `provider_probe_candidate_ok`
- `provider_probe_negative_candidate`
- `provider_probe_unreachable_candidate`
- `provider_probe_timeout_candidate`
- `provider_probe_invalid_response_candidate`
- `provider_probe_blocked_by_policy`
- `provider_probe_future_gated`
- `provider_probe_unknown`
- `unknown`

## Truth Label Classes

- `metadata_candidate_only`
- `negative_candidate_only`
- `not_runtime_failure`
- `not_provider_health_proof`
- `not_model_availability_proof`
- `not_verifier_success`
- `operator_review_recommended`
- `retry_requires_operator_approval`
- `unknown`

## Display Severity Classes

- `info`
- `low`
- `medium`
- `warning`
- `high`
- `critical`
- `unknown`

Severity is display metadata only. It is not runtime health mutation and cannot create a blocker by itself.

## Freshness Classes

- `current_manual_smoke`
- `recent_candidate`
- `stale_candidate`
- `historical_candidate`
- `unknown_freshness`

Stale, historical, or unknown freshness may recommend review, but does not authorize retry or probing.

## Negative Candidate Semantics

Negative candidates are preserved as metadata:

- `unreachable_negative_candidate`
- `timeout_negative_candidate`
- `connection_refused_negative_candidate`
- `invalid_response_negative_candidate`
- `unauthorized_negative_candidate`
- `unsupported_endpoint_negative_candidate`
- `cancelled_negative_candidate`

They are not runtime failures, not verifier failures, not health proof, and not evidence.

## Result Distinctions

Unreachable, timeout, refused, invalid, unauthorized, unsupported, and cancelled results are separate. Future surfaces should not collapse them into a generic failure if the source metadata distinguishes them.

Retryable negative candidates such as unreachable, timeout, refused, and invalid response preserve `retry_requires_operator_approval`.

## Empty Model List Semantics

`empty_model_list_candidate` is metadata only. It does not prove a provider is unhealthy, does not prove no local models exist, does not prove no model can be loaded later, and does not create runtime failure.

## Manual Smoke Result Interpretation

The previous manual smoke against `http://127.0.0.1:1234/v1/models` produced:

- `unreachable_negative_candidate`
- `not_observed` response shape
- no response status code
- no model count candidate

This projection contract represents that result as a negative candidate only and preserves that retry requires operator approval.

## Truthfulness Rules

The projection rejects claims that:

- unreachable, timeout, refused, or empty model list is a runtime failure
- metadata success is provider health proof
- model-list success is model availability proof
- downloaded models are loaded or served availability proof
- self-reported provider or model identity is authority
- benchmark or quality is verified
- Auto Mode can select a model from projection
- Local Model Inventory can prove availability from projection

## Relationship To Real Localhost Runner

The Real Localhost Runner can supply result metadata. Projection can surface that metadata, but cannot rerun the probe, open sockets, perform HTTP, or turn runner output into provider health proof.

## Relationship To Live Gate

The Live Gate can inform result semantics and safety boundaries. Projection cannot authorize live probing or bypass the live gate.

## Relationship To Mock Runner / Wiring / Boundary

Mock Runner, Wiring, and Boundary decisions are references only. Mock results do not become real provider proof. Wiring and boundary metadata do not become runtime/API surfaces.

## Relationship To Provider Health / Local Model Inventory

Provider Health readiness and Local Model Inventory may consume projection metadata later. Projection does not verify provider health, model availability, model identity, loaded state, or benchmark quality.

## Relationship To Model Auto Mode

Projection cannot authorize Auto Mode, provider selection, model selection, model calls, fallback routing, or execution.

## Relationship To Local Model Context Profile

Context profile metadata cannot authorize model use from projection. Projection does not evaluate model quality or context suitability.

## Relationship To Context Policy / Identity / Memory Governance

Context Policy, Identity Scope, and Memory Governance cannot be bypassed. Projection does not retrieve context, memory, repo content, evidence, web data, or documents.

## Relationship To Capability Lease

A capability lease candidate cannot authorize retry, probing, model execution, or provider access through projection.

## Not Proof, Evidence, Verifier Success, Or Runtime Failure

Probe result projection is not:

- provider health
- model availability
- model identity
- benchmark proof
- evidence
- verifier success
- execution permission
- runtime health mutation
- maintenance scan mutation

## Intentionally Not Done

This sprint did not:

- perform provider probing
- call `/v1/models`
- open sockets
- perform HTTP requests
- add API routes
- add runtime commands
- add scheduler jobs
- add frontend UI
- call models
- load models
- generate embeddings
- rerank
- send prompts or context
- read or validate secrets
- mutate runtime, journal, evidence, or replay state
- create evidence or verifier success

## Future Implementation Notes

Future Maintenance Scan or Mission Control surfaces can consume this projection contract to display probe result candidates. Any real retry must remain operator-gated and must go through the safe local provider runner and live gate.

## Remaining Risks

- Projection can only be as accurate as supplied metadata.
- Stale probe metadata can mislead operators if freshness is not visible.
- Future UI/API surfaces must not convert display severity into runtime health.
- Future retry workflows need a separate operator-gated execution boundary.
