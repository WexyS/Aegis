# Passive Observe-Only Product Mode Readiness
## Decision

- Decision: `PASSIVE_OBSERVE_MODE_READINESS_WITH_TESTS`
- Contract version: `passive-observe-only-product-mode-readiness/1`
- Implementation surface: `src/aegis/core/passive_observe_mode.py`
- Test surface: `tests/test_core/test_passive_observe_mode.py`
- Previous sprint: `LOCAL_PROVIDER_PROBE_DESIGN_WITH_TESTS`

This sprint defines a pure observe-only readiness contract for future Aegis
product surfaces. It does not implement a runtime mode, background watcher,
file watcher, process watcher, model call, provider probe, endpoint probe,
repo scan, memory retrieval, context retrieval, web query, tool call, MCP call,
API call, frontend UI, runtime integration, evidence creation, verifier
success, approval grant, capability grant, lease grant, or state mutation.

## Scope

Passive Observe-Only Product Mode is a future product mode boundary. The helper
validates caller-supplied metadata and classifies whether it may be displayed as
read-only projection. It can summarize existing backend-owned state references
or readiness decisions, but it cannot observe live systems by itself.

Every decision preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_passive_observe_mode`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_observe_mode=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `tool_call_performed=false`
- `model_call_performed=false`
- `provider_probe_performed=false`
- `endpoint_probed=false`
- `repo_scan_performed=false`
- `file_watch_started=false`
- `process_watch_started=false`
- `memory_retrieval_performed=false`
- `context_retrieval_performed=false`
- `web_query_performed=false`
- `runtime_state_mutated=false`
- `journal_mutated=false`
- `evidence_mutated=false`
- `replay_mutated=false`
- `data_sent_external=false`
- `generated_artifact_created=false`
- `fake_health_created=false`
- `fake_evidence_created=false`
- `fake_verifier_success_created=false`
- `requires_backend_validation=true`
- `read_only_projection=true`

## Why Observe-Only Exists

Aegis needs a product-friendly way to show local system, readiness, provider,
model, policy, maintenance, and onboarding state without turning display into
authority. Observe-only mode gives the frontend and Mission Control a safe
metadata contract before any future ambient cockpit, passive dashboard, or
onboarding surface is implemented.

The important boundary is simple:

- observed metadata is not live observation unless backend evidence says so
- display state is not runtime truth
- readiness metadata is not implementation
- unavailable, stale, unknown, historical, and future-gated states must remain
  visible
- frontend or user-supplied projections cannot become backend authority

## Observe Scopes

Supported observe scopes are:

- `runtime_status_summary`
- `maintenance_projection_summary`
- `pending_decision_summary`
- `app_registry_summary`
- `tool_registry_summary`
- `provider_readiness_summary`
- `model_inventory_summary`
- `policy_boundary_summary`
- `context_policy_summary`
- `memory_governance_summary`
- `identity_scope_summary`
- `lease_readiness_summary`
- `probe_design_summary`
- `repo_audit_readiness_summary`
- `evidence_debt_summary`
- `replay_debt_summary`
- `system_resource_summary`
- `product_onboarding_summary`
- `unknown`

Unsupported scopes are rejected as unavailable metadata. A supported scope still
does not authorize a runtime watcher, data fetch, endpoint probe, model call, or
tool execution.

## Display States

Supported display states are:

- `available_from_backend_state`
- `unavailable`
- `unknown`
- `stale`
- `historical_debt`
- `current_blocker`
- `future_gated`
- `blocked_by_policy`
- `needs_operator_attention`
- `not_implemented`
- `not_configured`
- `no_mutation_performed`
- `read_only_projection`

`available_from_backend_state` may only describe a reference to backend-owned
state. It does not mean success, verifier success, health, evidence, approval,
or implementation.

## Risk Levels

Supported risk levels are:

- `info`
- `low`
- `medium`
- `high`
- `critical`
- `unknown`

Failures are surfaced as high-risk metadata. Historical debt, stale state, and
operator attention remain visible as medium-risk metadata. Unknown and
unavailable states remain unknown rather than being upgraded into success.

## Truthfulness Rules

The helper preserves the following truth boundaries:

- frontend-supplied state cannot claim backend truth
- unknown state cannot become available state
- historical debt cannot become current success
- future-gated readiness cannot become implementation
- stale metadata cannot become live runtime truth
- fake health, fake evidence, and fake verifier success are rejected
- readiness metadata cannot become implementation metadata

Blocked or forbidden claims return policy-blocked or unavailable projection
state, depending on the failure type. They never become runtime success.

## Related Decision Handling

The helper may accept existing readiness decisions as related references:

- Identity Scope
- Memory Governance
- Policy Extension
- Context Policy
- Model Auto Mode
- Local Provider Health
- Local Provider Probe Design
- Capability Lease
- Local Model Inventory
- Mission Control
- Tool Simulation
- Repo Audit
- Compliance Evidence
- Developer Work Passport
- Plugin Review

Related decisions are always reference-only. If a related decision claims
authority, dispatch, grants, evidence, verifier success, execution, mutation,
fake state, model/tool/API/MCP behavior, retrieval, watcher behavior, repo scan,
or external data transfer, the observe-only decision is blocked as unsafe.

## Relationship To Runtime Truth

Observe-only mode is not RuntimeAuthority. It does not read the event journal,
write the event journal, create runtime events, update command lifecycle state,
emit evidence, verify completion, or change runtime health.

Future product surfaces must still read backend-owned truth surfaces through
separate APIs and preserve the distinction between:

- backend truth
- backend projection
- caller-supplied metadata
- frontend projection
- stale metadata
- future-gated readiness

## Relationship To Models And Providers

Observe-only mode can display model inventory, Auto Mode, provider health, or
probe design metadata as read-only projection only. It cannot:

- load a model
- call a model
- probe an endpoint
- authenticate a provider
- select a provider for execution
- send context, memory, repo code, journal data, or evidence to a provider
- treat model output as authority

Provider readiness and local model metadata remain candidates until later
explicit runtime, policy, privacy, evidence, and verifier gates exist.

## Relationship To Policy, Approval, And Leases

Observe-only mode cannot grant policy permission, approval, capability, or a
lease. It can only show reference-only summaries of existing policy, approval,
or lease readiness metadata. Approval alone remains not execution permission,
and lease readiness remains not an active lease.

## Relationship To Evidence And Verifier

Observe-only mode creates no evidence and no verifier success. It may display
evidence references or evidence debt summaries only when those references are
caller-supplied metadata or backend-owned state references. Missing, failed,
unknown-era, historical, and replay debt must remain visible.

## Relationship To Frontend UX

The future frontend can use this contract for a passive dashboard or onboarding
surface, but the frontend remains non-authoritative. A frontend projection may
not claim backend truth, runtime health, verifier success, or implementation.

## Tests Added

Focused tests cover:

- valid backend runtime summary metadata
- current blocker vs historical debt preservation
- model inventory metadata not becoming usable models
- provider readiness not becoming health proof
- lease readiness not becoming active permission
- missing required fields and provenance blocking display
- unknown, stale, historical, current, future-gated, unavailable, not
  implemented, and not configured states
- frontend-supplied state rejected as backend truth
- stale config metadata not becoming live runtime truth
- tool/model/provider/repo/watch/retrieval/web/mutation/external/artifact flags
  rejected
- authority, grants, fake state, evidence, verifier, and implementation claims
  rejected
- unsafe related decisions rejected
- safe related decisions summarized as reference-only
- input and related decisions not mutated
- output never enabling dispatch or fake success

## Intentionally Not Done

This sprint intentionally does not:

- implement a product mode switch
- implement background monitoring
- start file or process watchers
- read files, directories, runtime journals, evidence, memory, or context
- call models, tools, MCP, APIs, web, or providers
- probe endpoints
- create runtime events
- create evidence
- create verifier success
- mutate journal, evidence, replay, or runtime state
- implement frontend UI
- generate reports, exports, screenshots, images, or product assets

## Future Implementation Notes

A future implementation sprint may build an API or UI around this contract only
after separate gates prove:

- backend source surfaces are explicit
- stale vs live state is preserved
- frontend projection is not authority
- evidence and verifier semantics are unchanged
- historical, unknown-era, replay, and resource debt remain visible
- provider/model/context/memory/repo-audit metadata remains proposal-only

## Remaining Risks

- Product UX can still overstate readiness if copy ignores display states.
- A future dashboard may be tempted to collapse stale, unknown, and historical
  debt into simplified health.
- Related readiness decisions can drift unless future integrations keep
  rejecting authority, dispatch, evidence, verifier success, and behavior
  claims.
- A future ambient mode must not become a hidden runtime watcher without an
  explicit boundary sprint.
