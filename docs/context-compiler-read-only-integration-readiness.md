# Context Compiler Read-Only Integration Readiness
## 1. Decision

- Decision: `READINESS_WITH_NON_AUTHORITY_TESTS`
- Recorded at: `2026-05-31T22:39:43+03:00`
- Repository checkpoint before sprint: `ae7237d53f83157e6224427e1b513bd3e6939bfa`
- Foundation tag: `foundation-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This sprint does not implement active Context Compiler runtime integration. It
documents the future read-only integration boundary and adds focused tests around
the existing skeleton so compiler output cannot be mistaken for runtime
authority, command permission, approval, evidence, verifier truth, or memory
authority.

## 2. Existing Skeleton Summary

Authoritative file:

- `src/aegis/core/context_compiler.py`

Current public API:

- `ContextBudget`
- `ContextCompilerInput`
- `compile_context_package(inputs)`

Current inputs:

- explicit request metadata
- runtime snapshot
- command lifecycle snapshot
- policy boundary decision
- non-executable guard state
- evidence audit summary
- maintenance scan summary
- frontend projection reference
- optional runtime events iterable
- generated timestamp and section budget

Current output:

- `schema_version=context-package/1`
- `compiler_version=context-compiler/1`
- bounded summaries for request, runtime, lifecycle, policy, non-executable
  state, evidence audit, maintenance diagnostics, and frontend projection
- source references with authority labels
- omitted-section metadata
- safety warnings
- context budget metadata
- top-level `non_executing=true`
- top-level `capability_grant=false`
- top-level `execution_permission=not_granted_by_context`

Current behavior:

- The compiler is pure over caller-supplied inputs.
- It does not inspect global runtime state.
- It does not call tools.
- It does not write memory.
- It does not mutate journal, evidence, replay, command lifecycle, approval, or
  runtime state.
- It does not expose raw runtime events by default. Runtime events are counted
  and omitted unless a future explicitly approved boundary changes that policy.
- It can report that a policy boundary says approval was granted or dispatch may
  be allowed, but context itself still grants no permission and requires policy
  recheck before dispatch.

Current test coverage:

- schema/provenance
- frontend projection as reference-only
- unavailable/stale inputs
- blocked/non-executable state
- approval/clarification not being execution permission
- policy boundary not becoming context permission
- evidence audit not treating dispatch success as verification
- maintenance diagnostics as read-only
- raw runtime journal omission
- no execution capability introduced by context package
- added in this sprint: evidence classification count preservation,
  approval-grant reporting without context permission, untrusted permission field
  non-promotion, and no mutation of supplied inputs

## 3. Allowed Future Read-Only Source Surfaces

| Source | Source of truth | Allowed fields | Forbidden fields / behavior | Freshness and provenance |
| --- | --- | --- | --- | --- |
| Runtime snapshot | `RuntimeAuthority.snapshot()` / maintenance `checks.runtime_snapshot` | session id, FSM state, queue depth, active command presence, version, staleness | command permission, inferred success, frontend-only state | Include source version, generated time, and stale/unknown status. |
| Command lifecycle snapshot | approval manager snapshot / maintenance `checks.command_lifecycle` | records, pending counts, decision status, verification state, lifecycle state, bounded recent records | local deletion, approval resolution, grant, hidden pending decisions | Include snapshot source and item omissions; unresolved decisions remain visible. |
| Maintenance scan summary | `run_read_only_maintenance_scan()` | read-only flag, runtime health, foundation readiness, findings summary, pending hygiene, replay/evidence summaries | cleanup execution, fake health, suppressed findings, action execution | Include scan version, read-only flag, mutation flag, and stale/unavailable state. |
| Evidence audit summary | `audit_action_evidence()` / `checks.evidence_audit` | status, read-only flag, verified/missing/failed counts, current/historical/unknown split, classification counts | marking evidence verified, converting missing or failed evidence to success | Preserve current/historical/unknown labels and negative evidence semantics. |
| Policy boundary summary | `evaluate_policy_boundary()` | decision status, rule, dispatch allowed by policy, approval granted by policy, resume allowed by policy | context permission, policy override, approval grant by context | Include `context_grants_permission=false` and `requires_policy_recheck_before_dispatch=true`. |
| Pending decision hygiene | `build_pending_decision_hygiene_report()` via maintenance | pending, current-session, restored, stale, approval/clarification split, read-only/mutation flags | local hiding, deletion, auto-deny, approval grant | Preserve backend lifecycle truth and never resolve decisions from context. |
| App registry/discovery summary | registry snapshot and read-only app discovery smoke | identity, aliases, path/process/window/title-only status, read-only flag | launch proof, focus/click action, deterministic verification from title-only match | Preserve path/title/process distinctions and not-launch-proof wording. |
| Docs/reference metadata | curated docs under `docs/` and README | document path, title, version/checkpoint, known caveats | runtime authority, evidence truth, cleanup permission | Treat as reference metadata only. Docs cannot override backend truth. |
| Frontend projection | UI cache/store, if supplied | display state as reference only | authority, permission, evidence, verification, health, deletion | Always label `frontend_reference_non_authoritative` and `used_as_authority=false`. |

Raw event journal data should not be included by default. A future raw journal
mode would require a separate explicit boundary sprint, budget limits, redaction
rules, provenance, and tests proving it cannot become evidence or authority.

## 4. Forbidden Authority Paths

Context Compiler output must never:

- grant capability
- grant approval
- grant execution permission
- override policy
- bypass approval lifecycle
- bypass verifier requirements
- mark evidence verified
- convert missing evidence to verified
- convert failed or negative evidence to success
- hide runtime health `fail`
- hide historical evidence debt
- hide unknown-era evidence issues
- hide replay diagnostics failure
- convert unknown-era state to historical or success without trusted metadata
- write memory
- mutate journal, evidence, replay, command lifecycle, approval, policy, or
  runtime state
- trigger planner execution
- trigger tool execution
- expose raw journal events by default
- treat frontend projection as backend truth
- treat docs, summaries, retrieval, memory, plugin, or model output as
  execution authority

## 5. Proposed Future Context Package Contract

A future runtime-exposed context package should remain additive and
non-authoritative. Required fields:

- `context_package_id`
- `schema_version`
- `compiler_version`
- `generated_at`
- `source_refs`
- `source_versions`
- `staleness`
- `authority=false`
- `capability_grant=false`
- `approval_grant=false`
- `execution_permission=not_granted_by_context`
- `policy_recheck_required=true`
- `memory_mutation=false`
- `journal_mutation=false`
- `evidence_mutation=false`
- `runtime_mutation=false`
- `raw_journal_included=false`
- `known_debt_visible=true` when debt exists in supplied source summaries
- `unknown_era_preserved=true` when unknown-era source labels exist
- `frontend_projection_used_as_authority=false`
- `omitted_sections`
- `safety_warnings`

The current skeleton already has the core non-authority fields:

- `non_executing=true`
- `capability_grant=false`
- `execution_permission=not_granted_by_context`
- source references
- raw journal excluded by default
- frontend projection reference-only metadata

This sprint adds preservation of evidence audit current/historical/unknown count
fields inside the evidence summary. It does not add runtime exposure or a new
endpoint.

## 6. Future Integration Gate

Before any runtime API or UI exposes compiled context, the following must be
true:

1. The context package contract includes explicit non-authority and no-mutation
   fields.
2. Every source reference has source id, version, authority label, provided flag,
   and freshness/staleness status.
3. Unknown, stale, missing, historical, and failed source states remain visible.
4. Frontend projection is reference-only and never used as authority.
5. Policy boundary output requires a policy recheck before dispatch.
6. Approval-granted state, if present in a source, is reported as source truth
   but not promoted to context permission.
7. Raw journal inclusion remains disabled by default.
8. Tests prove context does not grant capability, approval, or execution
   permission.
9. Tests prove context does not mutate supplied inputs or runtime-owned state.
10. No planner, tool, memory, MCP, model, plugin, or vertical pack integration is
    connected to compiled context.

## 7. Test Plan

Tests added or reinforced in this sprint:

- Evidence classification counts remain preserved in context summaries without
  creating verified evidence claims.
- A policy boundary with `approval_granted=true` and `resume_allowed=true` is
  reported as policy source state, but context still grants no execution
  permission.
- Untrusted permission fields from request, maintenance, or frontend projection
  are not promoted into top-level context authority.
- Compiler execution does not mutate supplied request, lifecycle, evidence, or
  maintenance inputs.

Recommended tests for the first runtime exposure sprint:

- A future endpoint, if added, is read-only and has no command dispatch path.
- A future endpoint cannot be called by the executor as permission input.
- Raw journal inclusion remains disabled unless a separate boundary flag is
  explicitly provided and tested.
- Stale maintenance or runtime snapshots render as stale/unavailable, not
  success.
- Unknown-era evidence remains unknown across context package generation.
- Memory write attempts are absent or rejected by contract.

## 8. Non-Goals

- No active Context Compiler runtime integration.
- No runtime endpoint.
- No planner execution.
- No command permission.
- No memory mutation.
- No journal, evidence, replay, command lifecycle, approval, policy, verifier,
  runtime authority, or runtime health semantic change.
- No MCP Gateway, Memory OS, Model Router, plugin/skill execution, tool
  execution, vertical pack behavior, cleanup execution, archive, or compaction.
- No frontend authority changes.

## 9. Recommended Next Workstream

Recommended next prompt:

`Policy-as-code Extension`

Reason: Context Compiler readiness now has a documented non-authority boundary.
The next safest platform layer is to formalize capability/risk policy contracts
before any future context, tool, model, or plugin surface can influence
execution.

Alternative:

`Context Compiler Read-Only Contract Implementation`

Use this only if the operator wants to implement the explicit future contract
fields and any read-only exposure surface with deny-by-default tests. It should
not connect to planner execution, tool execution, memory mutation, or command
permission.
