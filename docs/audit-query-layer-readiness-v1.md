# Audit Query Layer Readiness v1

## Decision

- Decision: `AUDIT_QUERY_LAYER_READINESS_WITH_TESTS`
- Contract version: `audit-query-layer-readiness/1`
- Implementation surface: `src/aegis/core/audit_query_layer.py`
- Test surface: `tests/test_core/test_audit_query_layer.py`
- Latest related sprint: UI/Electron clickability triage found no browser reproduction and made no runtime change.

This sprint adds a pure readiness contract for future audit query planning. It
does not execute queries, read raw journal or evidence files, query a database,
scan a repository, read files, call models, call tools, call MCP, query the web,
retrieve memory/context, create exports, create evidence, mark verifier success,
or wire into runtime/API/frontend behavior.

## Scope

The Audit Query Layer represents a future backend-owned query planning boundary.
It validates caller-supplied projection metadata and classifies whether a query
plan is:

- ready for a bounded projection
- ready for an explicitly complete supplied projection
- future-gated
- unavailable or clarification-required
- blocked by missing metadata, authority claims, evidence claims, execution
  claims, unsafe related decisions, or invalid full-history claims

The output is non-authoritative. Audit query metadata cannot grant permission,
approval, lease, capability, evidence, verifier success, runtime dispatch, or
frontend authority.

## Why Audit Query Readiness Exists

Aegis has many truthful but separate projection surfaces: command lifecycle,
approvals, evidence audit, verifier status, maintenance, passive observe mode,
policy, model readiness, context policy, memory governance, identity scope,
repo-audit readiness, plugin review, compliance evidence, and developer work
passport references.

Future operators need a way to ask bounded audit questions across these
surfaces without turning the query layer into a new source of runtime truth. This
contract defines that boundary before any live query execution exists.

## Query Categories

Supported query categories:

- `command_lifecycle_query`
- `approval_query`
- `clarification_query`
- `policy_decision_query`
- `evidence_query`
- `verifier_query`
- `replay_debt_query`
- `journal_integrity_query`
- `maintenance_projection_query`
- `passive_observe_query`
- `model_provider_readiness_query`
- `local_model_inventory_query`
- `capability_lease_query`
- `context_policy_query`
- `memory_governance_query`
- `identity_scope_query`
- `repo_audit_readiness_query`
- `plugin_review_query`
- `compliance_evidence_query`
- `developer_work_passport_query`
- `future_action_attribution_query`
- `future_system_drift_query`
- `future_integrity_monitor_query`
- `unknown`

Future action-attribution, system-drift, and integrity-monitor queries remain
future-gated. They are not implemented as live monitors or live queries.

## Query Operations

Supported operations:

- `classify_query`
- `propose_projection_query`
- `propose_time_window_query`
- `propose_ref_lookup`
- `propose_risk_summary`
- `propose_debt_summary`
- `propose_state_summary`
- `propose_operator_attention_summary`
- `propose_export_future`
- `unknown`

`propose_export_future` is future-gated. It does not create exports, reports,
artifacts, files, signatures, evidence, or verifier success.

## Projection Source Classes

Supported projection source classes:

- `caller_supplied_projection`
- `maintenance_scan_projection`
- `passive_observe_projection`
- `command_lifecycle_projection`
- `approval_projection`
- `evidence_audit_projection`
- `replay_diagnostics_projection`
- `policy_projection`
- `model_readiness_projection`
- `context_policy_projection`
- `memory_governance_projection`
- `identity_scope_projection`
- `repo_audit_readiness_projection`
- `future_action_attribution_projection`
- `future_system_drift_projection`
- `unknown`

Projection metadata is not raw access. It does not authorize raw journal reads,
raw evidence reads, database queries, repo scans, file reads, or history
reconstruction.

## Completeness, Freshness, and Trust

Completeness classes:

- `complete_for_supplied_projection`
- `bounded_projection_only`
- `partial_projection`
- `stale_projection`
- `unknown_completeness`
- `unavailable`

Freshness classes:

- `current_supplied`
- `recent_supplied`
- `stale`
- `historical`
- `unknown`

Trust levels:

- `backend_projection`
- `caller_supplied_metadata`
- `frontend_supplied_low_trust`
- `model_output_low_trust`
- `mcp_output_low_trust`
- `tool_output_low_trust`
- `unknown`

Low-trust results cannot become complete history, authority, evidence, verifier
success, policy truth, or runtime truth.

## Full-History Claim Boundary

The contract preserves a strict full-history boundary:

- bounded projections cannot claim full history
- partial, stale, unavailable, or unknown projections cannot claim full history
- frontend/model/MCP/tool output cannot claim full history
- complete history is only valid for an explicitly supplied projection marked
  `complete_for_supplied_projection`
- even a valid complete supplied projection is not evidence, verifier success,
  raw journal access, or runtime truth

## Runtime Truth Relationship

Audit query output is not runtime truth. It can only reference projections whose
source refs and provenance were supplied by the caller. Future live integration
must re-check backend policy, source authority, freshness, evidence boundaries,
and verifier expectations at the time of use.

## Evidence and Verifier Relationship

Audit query output cannot create evidence and cannot mark verifier success.
Evidence and verifier truth remain owned by the backend evidence/verifier
surfaces. Query output may refer to evidence or verifier projection refs, but
those refs are not proof of success.

## Journal, Replay, and Maintenance Relationship

The contract can classify journal integrity, replay debt, and maintenance
projection metadata, but it cannot read raw journals, mutate journals, mutate
evidence, mutate replay data, run cleanup, archive data, compact history, or
hide historical/unknown/replay/resource debt.

Current blockers, historical debt, stale projections, future-gated states,
unknown states, and unavailable states are preserved as distinct fields.

## Passive Observe and Frontend Relationship

Passive Observe Mode and frontend projections may be referenced as lower-risk
projection metadata. Frontend-supplied results stay lower-trust and cannot
become backend authority, complete history, evidence, verifier success, policy
truth, or runtime truth.

## Model, MCP, Tool, and Web Relationship

Model, MCP, tool, and web outputs are lower-trust references. The contract
rejects claims that those outputs are truth, authority, evidence, verifier
success, or proof. It also rejects model calls, MCP calls, tool calls, web
queries, context retrieval, and memory retrieval.

## Repo Audit, Compliance, and Passport Relationship

Repo Audit readiness, Compliance Evidence, and Developer Work Passport
decisions can be referenced as candidate metadata only. Audit query output is
not a repo scan, file read, report, compliance proof, certification, developer
passport proof, or official audit artifact.

## Policy, Approval, Lease, and Capability Relationship

Audit query metadata cannot grant policy permission, approval, leases,
capabilities, or runtime dispatch. Capability lease and policy-extension
metadata remain reference-only unless future explicitly approved integration
adds separate policy, approval, evidence, and audit gates.

## Tests Added

`tests/test_core/test_audit_query_layer.py` covers:

- valid bounded command lifecycle query metadata
- valid complete supplied projection boundary
- bounded projections blocked from claiming full history
- approval, clarification, evidence, verifier, maintenance, model, lease, repo
  audit, compliance, and passport query relationships
- preservation of current blockers, historical debt, stale, unknown,
  unavailable, and future-gated states
- rejection of live query execution, raw journal/evidence reads, database
  queries, repo scans, file reads, model/tool/MCP/web calls, memory/context
  retrieval, exports, mutations, artifacts, and external data transfer
- rejection of authority, grants, evidence, verifier, proof, certification, and
  low-trust truth claims
- unsafe related decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No live query executor
- No database access
- No raw journal read
- No raw evidence read
- No repo scan or file read
- No export/report/artifact generation
- No model/tool/MCP/web/API call
- No memory or context retrieval
- No runtime/API/frontend integration
- No evidence or verifier success
- No approval, lease, capability, or runtime dispatch grant
- No journal/evidence/replay/runtime mutation

## Future Implementation Notes

A future live query implementation should be a separate sprint. It must define:

- backend-owned source adapters
- allowed projection surfaces
- time-window and ref lookup semantics
- raw journal/evidence denial rules
- evidence expectations for every backend query attempt
- verifier/postcondition expectations for query results
- audit logging for query attempts
- operator-facing stale/partial/unknown/future-gated labels
- hard separation between query output and runtime authority

## Remaining Risks

- The contract validates metadata only; it does not prove that supplied refs are
  current, complete, or backed by live backend state.
- Future live adapters can still introduce risk if they bypass source authority,
  freshness, evidence, or verifier boundaries.
- Full-history claims remain safe only for explicitly supplied projections and
  must be revalidated if real backend query execution is introduced later.
