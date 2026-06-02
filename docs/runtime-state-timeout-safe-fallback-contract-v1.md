# Runtime State Timeout Safe Fallback Contract v1

Status: implemented as a backend-owned read-only contract and maintenance diagnostic.

## Scope

This contract classifies runtime command/lifecycle phases that are within budget,
overdue, stale, or retry-exhausted. It is intentionally not a watchdog, timer
loop, executor hook, approval resolver, browser/process recovery routine, or
frontend state contract.

Source of truth is backend command lifecycle state:

- command records from `ApprovalManager.snapshot()`
- pending approval and clarification records
- active command snapshot fields
- backend-owned record metadata such as deadline, heartbeat, retry, browser, and
  restored-pending markers

Frontend state can render this diagnostic but cannot create timeout authority,
grant approval, resume execution, satisfy verification, or rewrite backend
history.

## Phases

The v1 classifier covers:

- `received`
- `classified`
- `guarded`
- `approval_pending`
- `clarification_pending`
- `queued`
- `dispatching`
- `executing`
- `browser_dispatching`
- `verifying`
- `recording_evidence`
- `finalizing`
- `restored_pending`
- `unknown`

## Timeout Taxonomy

- `none`: the phase is inside the runtime-owned budget.
- `insufficient_timing`: no deadline or elapsed timing is available, so no
  timeout is classified.
- `pre_dispatch_stale`: a pre-dispatch phase is overdue; dispatch permission is
  not granted.
- `approval_stale`: approval has waited too long; approval is not granted,
  denied, or resumed.
- `clarification_stale`: clarification has waited too long; no intent is
  inferred and no command executes.
- `execution_timeout`: dispatch/execution is overdue; safe fallback requires
  negative evidence before a failure claim.
- `browser_dispatch_timeout`: browser dispatch is overdue; browser metadata is
  preserved and no process/browser kill is performed.
- `verifier_timeout`: verification is overdue; verifier state remains
  unverified.
- `evidence_recording_timeout`: evidence recording is overdue; fallback cannot
  mark success.
- `finalization_timeout`: finalization is overdue; history must not be
  rewritten.
- `restored_pending_stale`: a restored pending decision is stale; operator
  review is required and auto-resume is forbidden.
- `retry_exhausted`: retry budget is exhausted; no implicit retry is launched.
- `unknown_stale`: an unknown phase is overdue; operator review is required.

## Safety Invariants

Timeout is not success. Safe fallback is not success. Retry is not success.
Dispatch success is not verification success. Evidence exists does not mean
verified. A stale approval is not approval. A stale clarification is not an
answer. A restored pending decision is not permission to resume.

The v1 decision shape always keeps these authority fields false:

- `runtime_dispatch_allowed`
- `approval_granted`
- `auto_resume_allowed`
- `frontend_authority_allowed`
- `verified_success`
- `mutation_performed`
- `fallback_executed`

## Retry Behavior

Retry counts are classified only as budget state. Exhaustion produces
`retry_exhausted` and the disposition `retry_boundary_exhausted`.

The contract does not schedule, enqueue, or execute retries. Any future retry
execution path must pass through a separate runtime policy, approval, executor,
verifier, evidence gate, and journal path.

## Browser Behavior

Browser timeout diagnostics may preserve requested/final URL and browser runtime
metadata. Bot challenge evidence, including Google `/sorry/` outcomes, is not a
timeout by itself when elapsed timing or a deadline is unavailable.

The v1 contract does not click, kill a browser, kill a process, refresh a page,
restart browser state, or mark a browser action verified.

## Maintenance Diagnostic

`run_read_only_maintenance_scan()` includes `checks.runtime_timeout_diagnostics`.
This is a read-only observation over backend command lifecycle snapshots.

The diagnostic reports:

- evaluated record count
- finding count
- overdue count
- retry exhausted count
- negative evidence required count
- phase counts
- timeout-kind counts
- immutable safety flags

It performs no mutation and records `actions_performed=[]`.

## Intentionally Not Implemented

- no runtime watchdog loop
- no new runtime FSM state
- no command status mutation on timeout
- no approval expiry resolver
- no clarification expiry resolver
- no executor cancellation or process/browser kill
- no browser click or desktop click implementation
- no verifier criteria change
- no frontend authority
- no cleanup, archive, compaction, journal rewrite, or history hiding
