# Legacy Router Model-Call Boundary Guard v1

## Decision

LEGACY_ROUTER_MODEL_CALL_BOUNDARY_GUARD_WITH_TESTS

## Scope

This sprint hardens the legacy router/orchestrator/parser boundary so legacy
model hints cannot authorize model calls, provider selection, Auto Mode,
approval, leases, capability grants, evidence, or verifier success.

This is not model integration. No model was loaded, called, probed, downloaded,
or authenticated.

## Why This Guard Exists

The legacy router historically selected a `planner_model` from simple text
heuristics. The orchestrator then passed that value into the parser. The current
deterministic parser does not use the value for normal parsing, but if older AI
fallback flags were enabled, that path could reach `AIParser` and
`LLMProvider`.

That legacy metadata must not bypass the newer post-foundation contracts:

- Local Model Inventory is role metadata only.
- Future Auto Mode must decide provider selection explicitly.
- Future provider health checks must prove availability before claims.
- Policy, approval, lease, evidence, and verifier gates remain authoritative.

## Behavior

`RoutingVerdict.planner_model` may still be populated for legacy metadata, but
the verdict now explicitly marks it as:

- `model_hint_status=legacy_hint_only`
- `model_hint_authoritative=false`
- `model_call_authorized=false`
- `provider_selection_granted=false`
- `auto_mode_decision_granted=false`
- `execution_permission=not_granted_by_legacy_router_hint`
- `evidence_created=false`
- `verifier_success=false`

The orchestrator no longer forwards the legacy router model hint into
`IntentParser.parse(...)`.

`IntentParser.parse(..., model=...)` treats `model` as an ignored legacy hint.
AI fallback requires an explicit `model_call_authorized=true` flag.

`AIParser.parse(...)` and `AIParser.fix_execution_failure(...)` default to
closed behavior and return no AI intents unless explicitly authorized.

## Local Model Inventory Relationship

Local Model Inventory metadata does not authorize model calls. It does not grant
runtime dispatch, provider selection, Auto Mode execution, approval, lease,
capability, evidence, verifier success, or model output authority.

## Future Auto Mode Requirement

Future Model Auto Mode / Provider Selection work must provide a separate,
validated backend decision before any model call can be attempted. That decision
must be tied to:

- local/cloud/passive mode policy
- provider health status
- context policy
- privacy/data-sensitivity rules
- resource constraints
- approval/lease/capability gates where required
- evidence and verifier expectations

## Intentionally Not Done

- No Model Auto Mode implementation.
- No local provider health check.
- No LM Studio, Ollama, vLLM, or OpenAI-compatible endpoint probe.
- No API key validation.
- No provider authentication.
- No model loading or inference.
- No context retrieval, memory, vector storage, MCP gateway, or frontend work.
- No evidence or verifier semantics changed.
- No runtime journal/evidence/replay mutation.

## Tests Added

Focused tests cover:

- router model hints are non-authoritative metadata only
- parser ignores legacy model hints even when `agent_loop` is enabled
- Local Model Inventory metadata alone does not authorize model calls
- AI fallback requires explicit model-call authorization
- AIParser default behavior does not call the LLM provider
- orchestrator does not pass legacy router hints to the parser
- legacy hints do not create execution, evidence, verifier success, approval,
  lease, or capability grants

## Remaining Risks

The legacy router still computes a `planner_model` string for compatibility.
That field should be removed or replaced by a future Auto Mode decision object
after provider selection is designed and tested.

Older config and dependency surfaces still imply model/vector readiness in ways
that should be reconciled before provider execution work begins.
