# Backend Timeout Event Projection Contract v1

Decision: `BACKEND_TIMEOUT_EVENT_PROJECTION_WITH_TESTS`

## Scope

This sprint defines a backend-owned, non-executing projection contract for
runtime timeout findings. It answers how Aegis can represent a timeout or stale
condition as an auditable projection without enforcing the timeout.

The implementation extends `src/aegis/core/runtime_timeout.py` with pure
projection helpers. It does not emit events, append to the journal, mutate
command lifecycle records, call tools, resolve approvals, execute retries, or
start a watchdog loop.

## Relationship To Timeout Safe Fallback v1

Runtime State Timeout / Safe Fallback Contract v1 classifies timeout conditions.
This contract projects those classified findings into a backend-owned
`TIMEOUT_OBSERVED` RuntimeEvent-shaped object and append-only journal plan.

Classification remains separate from projection, and projection remains separate
from enforcement.

## Projection Taxonomy

- `timeout_observed`
- `stale_pre_dispatch_observed`
- `stale_approval_observed`
- `stale_clarification_observed`
- `execution_timeout_observed`
- `browser_timeout_observed`
- `verifier_timeout_observed`
- `evidence_recording_timeout_observed`
- `retry_exhausted_observed`
- `restored_pending_stale_observed`
- `unknown_stale_observed`

## Projection Fields

Each projection payload includes:

- `projection_version`
- `projection_id`
- `projection_kind`
- `projection_scope`
- `command_id`
- `lifecycle_id`
- `source_timeout_kind`
- `source_phase`
- `observed_at`
- `started_at`
- `updated_at`
- `deadline_at`
- `elapsed_ms`
- `budget_ms`
- `dispatch_attempted`
- `dispatch_succeeded`
- `verification_attempted`
- `verification_state`
- `verified_success=false`
- `evidence_created=false`
- `evidence_required`
- `requires_operator_attention`
- `suggested_operator_action`
- `recovery_proposal`
- `retry_count`
- `max_retries`
- `stale_decision_kind`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_timeout_projection`
- `mutation_performed=false`
- `frontend_authority=false`
- `journal_append_required_for_future_enforcement=true`
- `existing_history_mutation_allowed=false`
- `replay_safe=true`
- `not_executed=true`
- `executed=false`
- `projection_only=true`

Browser projections may also include backend-supplied `browser_metadata`.

## Journal Relationship

The helper creates a RuntimeEvent-shaped projection with event type
`TIMEOUT_OBSERVED`, but it does not append it. The included journal plan is
append-only, `append_now=false`, `existing_history_mutation_allowed=false`, and
`replay_safe=true`.

Future enforcement may append a timeout projection event only as a new event. It
must not rewrite, resequence, compact, archive, repair, or hide existing journal,
evidence, or replay data.

## Frontend Relationship

Frontend code may display backend timeout projections in a future UI. Frontend
state cannot create timeout authority, force timeout resolution, grant approval,
grant execution permission, or mark verification success.

Frontend-only timeout authority produces no projection unless a backend timeout
finding already exists.

## Approval And Clarification Relationship

`stale_approval_observed` does not approve or deny. `stale_clarification_observed`
does not infer intent or execute. `restored_pending_stale_observed` does not
resume restored pending commands.

Any future approval or clarification expiration policy must be explicit,
operator-aware, backend-owned, and separately tested.

## Browser Relationship

`browser_timeout_observed` preserves requested and final URL metadata when the
backend supplied it. It does not verify the URL, bypass interstitials, bypass bot
challenge pages, click, refresh, kill browser state, or kill processes.

A bot challenge is not projected as a timeout unless a backend timeout condition
also exists.

## Retry Relationship

`retry_exhausted_observed` reports retry budget exhaustion only. It does not
enqueue, schedule, or execute a retry. Future retry execution must pass through a
separate runtime policy, executor, verifier, evidence, and journal path.

## Maintenance Relationship

`checks.runtime_timeout_diagnostics` now includes read-only projection summary
fields:

- `projection_status`
- `timeout_projection_count`
- `stale_pending_projection_count`
- `stale_execution_projection_count`
- `projection_mutation_performed=false`
- `projection_dispatch_allowed=false`
- `projection_approval_grant_exposed=false`

Maintenance diagnostics still perform no mutation and expose
`actions_performed=[]`.

## Evidence And Verifier Relationship

Timeout projection is not execution evidence. It cannot create evidence of a
completed action. It cannot set verifier success. Verifier timeout projections
remain unverified. Execution and browser timeout projections may require future
negative evidence handling, but they do not create that evidence themselves.

## Intentionally Not Done

- no autonomous watchdog loop
- no live timeout enforcement
- no command status mutation
- no journal append
- no event bus emission
- no approval or clarification resolver
- no retry execution
- no browser/process/app kill
- no frontend contract change
- no verifier or evidence semantics change
- no cleanup, archive, compaction, repair, or replay rewrite

## Tests Added

Focused tests cover timeout finding projection, non-execution payload shape,
pre-dispatch stale projection, execution timeout projection, verifier timeout,
approval and clarification stale behavior, restored pending behavior, retry
exhaustion, browser metadata preservation, bot challenge non-projection without
timeout, frontend authority rejection, input immutability, maintenance projection
diagnostics, and threat-model authority rejection.

## Remaining Risks

Projection events are not emitted yet. Future watchdog or enforcement work must
define when a backend timeout finding becomes an appended journal event and how
operators review those events without greenwashing runtime health.

## Future Watchdog Notes

A future watchdog must be backend-owned and must consume this projection contract
without broadening authority:

- classify first
- project a non-executing timeout event
- append only, never rewrite
- keep command mutation behind a separate explicit policy
- keep approval and clarification resolution separate
- keep verifier/evidence semantics unchanged
- expose historical and replay debt as debt
