# Capability Lease Design v1

## 1. Decision

- Decision: `LEASE_DESIGN_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T02:06:42+03:00`
- Repository checkpoint before sprint: `a2c761a09ff5b2ffdb173df5823c4e4c6f63ea45`
- Foundation tag: `foundation-v1-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This sprint defines the future capability lease model as a design contract only.
It does not add runtime lease enforcement, dispatch behavior, executor/planner
integration, MCP/tool integration, Memory OS, Model Router, plugin/skill
execution, vertical pack behavior, cleanup/archive/compaction execution, or any
new permission grant.

## 2. Purpose and Non-Goals

A future capability lease is a scoped, temporary, revocable,
provenance-backed permission contract. It is intended to connect a backend
policy decision, risk tier, capability category, approval record when required,
evidence expectation, expiry, audit record, and revocation state.

A lease is not:

- execution by itself
- approval by itself unless explicitly tied to an approval event
- evidence
- verifier success
- frontend authority
- model, memory, context, plugin, skill, or MCP authority
- a bypass around runtime policy checks
- a broad permanent permission
- a cleanup/archive/compaction action

Even a future active lease must be rechecked against backend policy and runtime
state at use time. The lease design never makes approval alone, policy alone, or
context alone into execution permission.

## 3. Relationship to Current Policy-as-Code

Authoritative current policy extension surface:

- `src/aegis/core/policy_boundary.py`
- `POST_FOUNDATION_POLICY_VERSION=post-foundation-policy-extension/1`
- `evaluate_capability_policy_contract()`

Current policy extension behavior:

- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_policy_extension`
- unknown capability is denied
- unknown risk tier is denied
- untrusted authority is denied
- side-effecting risk without approval is denied
- executable action without evidence expectation is denied
- cleanup archive/compaction without operator boundary is denied

Future relationship:

- Policy may decide whether a lease proposal is eligible for review.
- Policy does not automatically create, activate, extend, or refresh a lease.
- A lease does not override policy.
- Runtime must re-check policy at lease use time in a later explicit integration
  sprint.
- Policy helper output remains non-dispatchable until a later runtime boundary
  explicitly wires enforcement and tests.

## 4. Lease Lifecycle

| State | Creator | Can authorize runtime dispatch? | Required audit/evidence | Allowed transitions | Forbidden transitions |
| --- | --- | --- | --- | --- | --- |
| `proposed` | backend policy review flow or operator request, future only | no | proposal provenance and policy rule reference | `pending_approval`, `denied`, `invalid`, `superseded` | `active` without policy and approval checks |
| `pending_approval` | backend approval lifecycle, future only | no | approval request id, policy rule, risk tier, scope | `active`, `denied`, `expired`, `revoked`, `invalid` | dispatch or use before approval resolution |
| `active` | backend lease authority after policy and approval gates, future only | not in this sprint; future use still requires recheck | activation audit, approval event if required, evidence expectation | `consumed`, `expired`, `revoked`, `superseded` | scope expansion, silent refresh, use after expiry/revocation |
| `expired` | time-bound lease evaluator, future only | no | expiry audit | `superseded` through a new proposal only | refresh in place, dispatch, reuse |
| `revoked` | operator or backend policy authority, future only | no | revocation actor, reason, timestamp | `superseded` through a new proposal only | dispatch, reuse, automatic unrevocation |
| `consumed` | future lease use recorder | no unless remaining uses exist in a new evaluated state | use audit and evidence refs | `expired`, `revoked`, `superseded` | hidden reuse beyond `max_uses` |
| `denied` | backend policy or approval lifecycle | no | denial reason and source | `superseded` through a new proposal only | activation without a new policy review |
| `invalid` | schema/policy/runtime validator | no | validation failure details | `superseded` through a corrected proposal only | dispatch, approval reuse, silent repair |
| `superseded` | backend lease authority, future only | no | replacement lease reference | none, except audit/read-only display | dispatch using old lease |

This lifecycle is a future contract. No lease state machine is implemented or
connected in this sprint.

## 5. Future Lease Schema

Required future fields:

- `lease_id`
- `lease_version`
- `capability_category`
- `risk_tier`
- `scope`
- `subject`
- `requested_by`
- `approved_by`
- `approval_event_id`
- `policy_rule_id`
- `policy_decision_ref`
- `evidence_expectation_id`
- `created_at`
- `expires_at`
- `revoked_at`
- `revocation_reason`
- `provenance_refs`
- `audit_refs`
- `constraints`
- `max_uses`
- `use_count`
- `runtime_dispatch_allowed=false` until a later explicit integration
- `execution_permission=not_granted_by_lease_design`

Required future derived flags:

- `expired`
- `revoked`
- `scope_match`
- `approval_required`
- `approval_present`
- `evidence_expectation_present`
- `policy_recheck_required=true`
- `audit_write_required=true`
- `journal_write_required_for_use=true`
- `context_can_authorize=false`
- `memory_can_authorize=false`
- `model_can_authorize=false`
- `plugin_can_authorize=false`
- `frontend_can_authorize=false`

Forbidden schema shortcuts:

- broad implicit wildcard scope
- missing expiry
- missing provenance
- missing policy rule
- missing approval event for side-effecting capabilities
- missing evidence expectation for executable actions
- frontend-only authority
- context/memory/model/plugin-derived permission
- hidden runtime dispatch flags

## 6. Scope Model

Future lease scopes should be explicit, narrow, and machine-checkable.

Scope dimensions:

- command scope: command id, trace id, task id, session id
- app scope: app identity, alias, executable path, process/window verifier
  expectations
- file path scope: normalized path, workspace containment, operation class,
  write mode
- tool scope: tool id, tool version, action family, allowed parameters
- network/external scope: host, method, data class, credential boundary
- memory namespace scope: namespace id, operation, sensitivity level
- model/provider scope: provider id, model id, routing reason, cost/privacy
  boundary
- plugin/skill scope: manifest id, action id, risk tier, rollback plan
- vertical pack scope: pack id, read/write mode, eval contract
- cleanup scope: journal/export id, backup path, restore rehearsal id, replay
  validation id, hash-chain validation id

Scope rules:

- Broad wildcard scopes are denied by default.
- Scope expansion requires a new lease proposal.
- Scope mismatch denies future use.
- Expired lease denies future use.
- Revoked lease denies future use.
- Missing approval denies side-effecting lease activation.
- Missing evidence expectation denies executable lease activation.
- Missing audit/journal write capability blocks future use.

## 7. Expiry and Revocation

Every future lease must expire. No lease may be permanent by default.

Rules:

- `expires_at` is required.
- expired leases cannot be used
- expired leases cannot be refreshed silently
- lease extension requires a new policy review
- lease extension requires a new approval where side effects or boundary risk
  apply
- every lease must be revocable
- revoked leases cannot be reused
- revocation must include actor, reason, timestamp, and audit reference
- revocation must win over remaining use count
- revocation must be visible in future operator UI and maintenance diagnostics

Recommended initial expiry defaults for future implementation:

- read-only review leases: short session-bound lifetime
- local state read leases: short session-bound lifetime
- side-effecting leases: command/task-bound and single-use by default
- cleanup/archive/compaction leases: boundary-sprint-bound and operator
  checkpoint-bound

These defaults are design recommendations only.

## 8. Provenance and Audit

Future lease records must reference:

- policy decision
- policy rule id
- capability category
- risk tier
- approval event when approval is required
- source request/context as provenance only
- evidence expectation
- operator boundary approval when required
- audit records for proposal, activation, use, expiry, revocation, denial, and
  supersession

Future use rules:

- every lease use must be journaled
- every side-effecting use must produce execution evidence or explicit negative
  evidence
- failure to write audit blocks future execution
- failure to write journal blocks future execution
- failure to define evidence expectation blocks future execution
- verifier failure remains failure; it cannot be repaired by lease state

Source request, Context Compiler package, memory retrieval, model output,
frontend projection, plugin manifest, or MCP discovery may be provenance refs.
They cannot be authority refs.

## 9. Relationship to Context Compiler

Context Compiler cannot:

- create a lease
- activate a lease
- refresh a lease
- extend expiry
- expand scope
- satisfy approval
- satisfy evidence
- satisfy verifier checks
- reduce risk tier
- grant command permission
- grant execution permission

Context Compiler may only provide bounded context/provenance for human review or
backend policy review. Any future runtime usage must re-check policy after
context compilation and before lease proposal or use.

## 10. Relationship to Memory, Model, Plugin, Skill, and MCP

Memory cannot create, activate, refresh, or extend a lease. Memory cannot
authorize execution and cannot satisfy approval.

Model output cannot create, activate, refresh, or extend a lease. Model output
may suggest a plan, but a future lease must be backed by backend policy,
approval where required, scope, evidence expectation, and audit.

Plugin and skill manifests cannot create, activate, refresh, or extend a lease.
Manifest-declared permissions are requests for backend registration, not
permission grants.

MCP/tool availability cannot create, activate, refresh, or extend a lease. Tool
discovery is not permission. Every future tool call requires backend policy
registration, risk tier, approval rules, evidence expectation, audit plan, and
future lease checks where applicable.

Vertical packs cannot bypass the generic lease contract. Pack-specific actions
must start read-only or approval-gated and reuse the same risk, scope, evidence,
audit, and rollback requirements.

## 11. Cleanup, Archive, and Compaction Lease Handling

Cleanup inventory is read-only and does not require an execution lease.

Archive and compaction are special boundary classes:

- `cleanup_archive` requires explicit operator boundary approval
- `cleanup_compaction` requires explicit operator boundary approval
- backup, restore rehearsal, replay validation, hash-chain validation, and audit
  references are mandatory before any future activation
- replay boundary blockers prevent activation
- hash-chain risk prevents activation
- unknown-era evidence issues cannot be silently reclassified to satisfy a lease
- journal rewrite, truncation, deletion, resequencing, or repair remains
  forbidden unless a later explicit boundary sprint proves it safe

Any future cleanup lease must preserve original journal/evidence artifacts and
must not make runtime health green by hiding historical, unknown-era, replay, or
resource debt.

## 12. Future Test Plan

When the first non-executing lease helper is added, focused tests should assert:

- proposed lease is non-dispatchable
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_lease_design`
- missing approval blocks side-effecting lease activation
- expired lease is invalid
- revoked lease is invalid
- scope mismatch denies use
- wildcard scope is denied by default
- context cannot create a lease
- memory cannot create a lease
- model output cannot create a lease
- plugin/skill manifest cannot create a lease
- MCP/tool discovery cannot create a lease
- cleanup archive/compaction cannot activate without explicit boundary approval
- replay/hash-chain blockers prevent cleanup lease activation
- lease alone is not execution permission
- approval alone is not execution permission
- policy alone is not execution permission
- frontend projection cannot be authority

When runtime enforcement is eventually proposed, tests must also prove:

- executor cannot dispatch from lease presence alone
- planner cannot use lease state as permission
- missing audit write blocks use
- missing journal write blocks use
- failed verifier result remains failed
- negative evidence remains failed or unverified evidence, not success
- revoked lease cannot be raced into dispatch
- expired lease cannot be refreshed implicitly

## 13. Implementation Phases

Recommended future sequence:

1. Lease contract helper, pure and non-dispatching.
2. Lease proposal validator, still non-dispatching.
3. Lease storage design with provenance and audit schema, no runtime use.
4. Operator review UI for lease proposals, no execution.
5. Policy recheck and approval linkage tests, no executor integration.
6. Read-only maintenance diagnostics for lease inventory.
7. Explicit runtime boundary sprint for enforcement, if approved.
8. Tool/MCP integration only after policy, lease, evidence, audit, and rollback
   tests are in place.

Do not collapse these phases. Runtime enforcement must not be introduced through
a design helper, UI display, Context Compiler output, or tool registry metadata.

## 14. Non-Goals

- No runtime lease enforcement.
- No executor, planner, tool, MCP, memory, model router, plugin, skill, or
  vertical pack integration.
- No new runtime permission.
- No new execution path.
- No approval behavior change.
- No existing policy behavior change.
- No verifier behavior change.
- No journal/evidence/replay/runtime mutation.
- No runtime health change.
- No cleanup/archive/compaction execution.
- No frontend authority change.

## 15. Recommended Next Workstream

Recommended next prompt:

`Local Environment Resource Hygiene & Model Storage Readiness v1`

Reason: the foundation still reports resource pressure around disk usage, and
resource hygiene can be designed/readied without changing policy, evidence,
approval, verifier, journal, replay, or execution semantics.

Alternative:

`Context Compiler Read-Only Contract Implementation v1`

Use this only if it remains read-only, non-authoritative, disconnected from
planner/executor/tool execution, and consistent with policy-as-code and future
lease boundaries.
