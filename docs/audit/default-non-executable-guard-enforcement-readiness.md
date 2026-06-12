# Default Non-Executable Guard Enforcement Readiness

Status: not ready for default enforcement.

This audit answers whether the context-gated non-executable guard boundary can
be made default runtime behavior later. It does not enable default guard
enforcement and does not remove `enable_non_executable_guard_boundary`.

## Current Default Runtime Behavior

When `request.context["enable_non_executable_guard_boundary"]` is absent:

- ready actions continue through the existing orchestrator path;
- `ACTION_STARTED` can still be emitted before executor dispatch;
- `executor.execute(...)` is still called for executable older paths;
- compatibility preflight guard still runs before execution;
- medium-risk older approvals still use `APPROVAL_REQUIRED` via
  `ws_bridge.emit_approval_required(...)`;
- older command lifecycle still records `pending_approval` through
  `ApprovalManager.register_pending(...)`;
- generic `click` can still reach older approval/execution paths depending on
  risk and approval context;
- non-executable guard events are not emitted by default;
- `runtime_snapshot["non_executable_decisions"]` is journal-derived, but will
  only show non-executable state when the journal contains the new canonical
  events;
- `action_timeline` remains journal-derived and only shows
  `approval_requested`, `clarification_requested`, or `blocked_by_policy` when
  those events exist.

Default behavior is unchanged today. The existing default-path regression tests
still cover low-risk execution and older approved click execution.

## Gated Harness Coverage

The gated harness currently proves:

- `approval_required` prevents `executor.execute(...)`;
- `clarification_required` prevents `executor.execute(...)`;
- `blocked` prevents `executor.execute(...)`;
- non-executable decisions do not emit `ACTION_STARTED`;
- non-executable payloads do not include `execution_evidence`;
- non-executable payloads do not set `success=true`, `verified=true`, or
  `action_started=true`;
- new approval semantics use `APPROVAL_REQUESTED`, not older
  `APPROVAL_REQUIRED`;
- ready `read_file` still executes under the flag;
- unresolved generic `click` is quarantined under the flag;
- `ws_bridge.append_non_executable_decision(...)` is used under the flag;
- live ws_bridge sequence allocation is used under the flag;
- repeated gated calls keep sequence numbers unique and monotonic;
- journal-derived snapshot projection exposes `pending_approval`,
  `pending_clarification`, and `last_blocked_action`;
- `action_timeline` projects `approval_requested`,
  `clarification_requested`, and `blocked_by_policy`.

This is strong harness coverage, but it is still harness coverage. The default
runtime path is not yet covered for non-executable behavior because it is not
enabled.

## Blockers Before Default Enforcement

Default guard enforcement is not ready until these are addressed:

- approval resolve lifecycle is not implemented;
- clarification resolve lifecycle is not implemented;
- pending clarification exists as a command lifecycle state, but there is no
  endpoint or worker handoff that can resolve it;
- older `APPROVAL_REQUIRED` preflight still coexists with new
  `APPROVAL_REQUESTED`;
- enabling all guard decisions by default can produce duplicate approval
  semantics unless compatibility preflight is migrated or fenced;
- generic click can still execute or resume through older default paths;
- frontend protocol types exist, but there is no UI consuming
  `non_executable_decisions`, `pending_clarifications`, or new
  `APPROVAL_REQUESTED`/`CLARIFICATION_REQUESTED` payloads;
- command queue semantics for `WAITING_FOR_CLARIFICATION` are not fully
  defined;
- cancellation behavior for pending approval/clarification needs direct tests;
- mixed executable and non-executable replay is partly covered, but default
  path replay needs explicit coverage;
- tests prove gated behavior, not default behavior.

## Readiness Decision

`default_guard_enforcement_ready`: no.

Must fix before default enforcement:

- resolve or explicitly defer approval resolution semantics;
- resolve or explicitly defer clarification resolution semantics;
- fence older `APPROVAL_REQUIRED` so a single decision cannot emit both compatibility
  and new approval events;
- define queue/command lifecycle behavior for waiting approval and waiting
  clarification under default mode;
- add default-path tests for the first enabled category;
- add cancellation tests for pending approval and pending clarification;
- verify snapshot and timeline behavior with mixed executable and
  non-executable events from the default path.

Nice to have before default enforcement:

- frontend UI for pending approval and pending clarification;
- live browser smoke showing backend-derived pending decision state;
- richer snapshot replay tests across process restart;
- a small migration note for older approval event consumers.

## Safe Partial Enforcement Analysis

### A. Generic Click Only

Safe now: almost, but not yet default-ready.

Risk:

- older click approval/resume tests still expect executable click after
  approval;
- default click behavior needs explicit migration tests;
- UI has no pending clarification handling.

Missing tests:

- default generic click no executor;
- default generic click no `ACTION_STARTED`;
- default generic click emits `CLARIFICATION_REQUESTED`;
- older approved click tests either migrate or remain explicitly compatibility-scoped.

Recommendation: yes as the next narrow implementation candidate, but only after
one readiness-to-implementation sprint with default-path tests.

### B. Unknown Tool Only

Safe now: partial.

Risk:

- parser/decomposition may already represent some unknowns as non-executable
  parser results rather than guard decisions;
- enabling guard interception for unknown tools may overlap parser behavior.

Missing tests:

- default unknown tool no executor;
- no fallback to generic executable tool;
- snapshot and timeline show blocked or clarification state.

Recommendation: not first. Keep behind generic click quarantine.

### C. Blocked Critical Actions Only

Safe now: partial.

Risk:

- existing compatibility preflight already blocks some critical actions;
- duplicate `COMMAND_BLOCKED` or mismatched lifecycle status can occur if both
  paths run.

Missing tests:

- default critical blocked action uses one canonical block path;
- no executor and no `ACTION_STARTED`;
- snapshot/action_timeline terminal state is stable.

Recommendation: good second candidate after older block path is fenced.

### D. Approval Required High-Risk Actions

Safe now: no.

Risk:

- no approval resolve endpoint for new approval semantics;
- older `APPROVAL_REQUIRED` still exists;
- frontend does not handle new approval request lifecycle.

Missing tests:

- default high-risk approval waits safely;
- approval can be cancelled;
- approval does not imply success or verification;
- no dual compatibility/new approval events.

Recommendation: do not enable before approval resolve lifecycle design.

### E. Clarification Required Unknown/Ambiguous Actions

Safe now: no.

Risk:

- no clarification resolution endpoint;
- queue/waiting behavior is not fully defined;
- frontend does not surface pending clarification.

Missing tests:

- default ambiguous command waits safely;
- pending clarification can be cancelled;
- no older executable fallback;
- snapshot survives reconnect/replay.

Recommendation: do not enable broadly before clarification resolve lifecycle
design.

### F. All Non-Executable Guard Decisions

Safe now: no.

Risk:

- combines all blockers at once;
- highest chance of lifecycle mismatch, duplicate events, and UI dead state.

Recommendation: explicitly unsafe for the next sprint.

## Older Generic Click Decision

Recommended next sprint: **Default Generic Click Guard Quarantine**.

Rationale:

- generic click is the clearest known unsafe executable gap;
- `classify_intent_risk("click", {})` already returns non-ready;
- gated harness already proves executor cutoff and no `ACTION_STARTED`;
- it avoids enabling all approval/clarification semantics at once;
- it can be tested without approval or clarification resolution endpoints by
  treating unresolved generic click as non-executed waiting clarification or
  blocked-by-policy.

Do not choose full default non-executable enforcement yet. Do not choose UI
first; backend must define the default runtime truth contract before frontend
consumes it. Approval/clarification resolution design is important, but generic
click quarantine is the narrower safety gap.

## Tests Needed Before Any Default Enforcement

Before enabling any default category:

- default path generic click no executor;
- default path generic click no `ACTION_STARTED`;
- default path generic click emits `CLARIFICATION_REQUESTED` or
  `ACTION_BLOCKED_BY_POLICY`;
- default path ready `read_file` still executes;
- default path ready `open_app` still executes;
- default path write-file policy behavior is explicit;
- default path approval-required command queues or waits safely;
- default path clarification-required command queues or waits safely;
- pending approval can be cancelled;
- pending clarification can be cancelled;
- sequence numbers remain monotonic across mixed executable and non-executable
  events;
- snapshot and action_timeline correctly project mixed executable and
  non-executable events;
- frontend build and protocol type compatibility remain valid.

For generic-click-only enforcement, the first minimal set is:

- generic click no executor;
- generic click no `ACTION_STARTED`;
- generic click appends canonical non-executable events through ws_bridge;
- generic click appears in `non_executable_decisions.pending_clarification`;
- generic click appears in `action_timeline` as `clarification_requested`;
- ready `read_file` and `open_app` still execute;
- older approved click tests are updated or explicitly scoped to older mode.

## Final Recommendation

Do not remove `enable_non_executable_guard_boundary` yet.

Proceed with **Default Generic Click Guard Quarantine** as the next
implementation sprint. Keep it narrow, default-on only for generic unresolved
`click`, with explicit regression tests for ready actions and older approval
paths.
