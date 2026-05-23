# Live Non-Executable Orchestrator Wiring Readiness v2

Status: readiness only. Default guard enforcement is still off.

## Scope

This report covers the remaining runtime blockers before the gated
`enable_non_executable_guard_boundary` harness can become default behavior.
It does not enable live guard enforcement, real non-executable event emission,
global snapshot mutation, approval resolution, click implementation, target
resolution, executor changes, parser changes, frontend UI changes, or Ultron
integration.

## Current Live Event And Journal Path

Canonical runtime events are represented by `RuntimeEvent` in
`src/aegis/core/protocol.py`.

Live sequence allocation currently happens when a `RuntimeEvent` is constructed:

- `RuntimeEvent.sequence_num` uses the `_next_sequence()` default factory.
- `create_event(...)` constructs `RuntimeEvent` values and therefore consumes
  the canonical process-local sequence counter.
- `RuntimeEvent.from_dict(...)` hydrates persisted events with an explicit
  `sequence_num` and does not consume the counter.
- `RuntimeEventJournal._load_existing_tail()` and `_sync_from_disk_locked()`
  call `ensure_sequence_at_least(max_sequence)` to hydrate the in-process
  counter from persisted journal state.

The canonical live append path is `ws_bridge._create_and_append_event(...)`:

- it holds `_journal_emit_lock`;
- it calls `create_event(...)` while holding that lock;
- it appends through `get_runtime_journal().append(...)`;
- then higher-level emitters fan out the serialized event.

This matters because event construction, not journal append, consumes the
sequence number. Creating events outside `_journal_emit_lock` can assign
sequence numbers in a different order than disk persistence under concurrent
emissions.

`RuntimeEventJournal.append(...)` finalizes the hash chain and persists JSONL.
It does not allocate sequence numbers. It does suppress duplicate `event_id`
values and exposes replay by `events_after(sequence_num)`.

Replay and timeline projections must order by `sequence_num`, with timestamp
only as a secondary fallback.

## Sequence Allocation Decision

Recommended sequence strategy: **ws_bridge-owned batch creation and append under
one lock**.

Future default wiring should not pass prebuilt live `RuntimeEvent` batches with
caller-supplied sequence numbers. Instead, add a ws_bridge-owned function such
as:

```text
append_non_executable_decision(...)
```

That function should:

- accept the `GuardDecision` plus `command_id`, `trace_id`, `span_id`,
  `action_id`, and `causation_id`;
- hold `_journal_emit_lock`;
- create the canonical non-executable events in order using `create_event(...)`;
- append each event to `get_runtime_journal()`;
- fan out each event in appended order;
- return the appended events and journal-derived projections to the caller.

The existing pure adapter can continue to serve dry-run and isolated tests.
For live runtime, it should either expose event payload specs or be adapted so
ws_bridge owns construction of `RuntimeEvent` objects. The current prebuilt
`starting_sequence_num` path remains valid for isolated tests only.

Options evaluated:

- A. Adapter accepts a sequence allocator callback: acceptable for tests, but it
  still risks allocating outside the ws_bridge append lock unless the callback
  is only invoked inside ws_bridge.
- B. ws_bridge assigns sequence numbers to batch entries: correct if ws_bridge
  constructs events under `_journal_emit_lock`; unsafe if it mutates prebuilt
  event numbers after construction.
- C. Orchestrator asks ws_bridge for event batch append with sequence allocation:
  recommended. Orchestrator supplies decision/context, ws_bridge owns live event
  construction, append, and fan-out.
- D. Keep prebuilt sequence numbers only in isolated tests: keep this for the
  current adapter and harness.

Duplicate sequence risk: high if live orchestrator uses
`build_non_executable_event_batch(... starting_sequence_num=...)` directly.
That path cannot know concurrent emissions already consumed sequence numbers.

Files likely to change in actual wiring:

- `src/aegis/api/ws_bridge.py`
- `src/aegis/core/non_executable_runtime_adapter.py`
- `src/aegis/orchestrator/orchestrator.py`
- `tests/test_api/test_ws_bridge.py`
- `tests/test_runtime/test_command_lifecycle.py`
- `tests/test_runtime/test_event_journal.py`

Tests required before default enforcement:

- concurrent live event and non-executable batch append remains strictly
  monotonic;
- no duplicate sequence numbers across mixed event types;
- event append order equals journal order;
- replay uses `sequence_num`, not timestamp;
- prebuilt isolated sequence batches cannot be used on the live global journal.

## Command Lifecycle Status Decision

Runtime FSM states remain unchanged. Command lifecycle state is separate.

Decision:

- `approval_required`: use existing `CommandStatus.PENDING_APPROVAL`.
- `clarification_required`: add and use
  `CommandStatus.WAITING_FOR_CLARIFICATION`.
- `blocked`: use existing `CommandStatus.BLOCKED` and
  `terminal_non_executed=true` in non-executable payload/projection.
- `denied`: use existing `CommandStatus.REJECTED` with reason metadata.
- `expired`: use existing `CommandStatus.REJECTED` with reason metadata until an
  explicit approval-expired command lifecycle migration is scoped.
- `cancelled`: use existing `CommandStatus.CANCELLED`.
- `approved`: use `CommandStatus.APPROVED` only as an eligibility state;
  approval must not imply executed, verified, or successful.

`CommandStatus.WAITING_FOR_CLARIFICATION` is a command lifecycle status, not a
runtime FSM state. No `RuntimeState.WAITING_FOR_CLARIFICATION` should be added.

Current remaining lifecycle gap: `ApprovalManager` has no first-class
`pending_clarifications` collection or `register_waiting_clarification(...)`
method. Until that exists, default live clarification wiring should not be
enabled globally.

## Journal Append Strategy

Future guard wiring should append canonical non-executable events through a
new ws_bridge live helper, not through orchestrator direct journal access.

Requirements for that helper:

- append in canonical order:
  - approval: `COMMAND_CLASSIFIED`, `APPROVAL_REQUESTED`,
    `COMMAND_WAITING_FOR_APPROVAL`;
  - clarification: `COMMAND_CLASSIFIED`, `CLARIFICATION_REQUESTED`,
    `COMMAND_WAITING_FOR_CLARIFICATION`;
  - blocked: `COMMAND_CLASSIFIED`, `ACTION_BLOCKED_BY_POLICY`,
    `COMMAND_BLOCKED`;
- allocate sequence numbers inside `_journal_emit_lock`;
- preserve `command_id`, `trace_id`, `span_id`, `action_id`, and
  `causation_id`;
- reject `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`,
  `ACTION_CANCELLED`, and legacy `APPROVAL_REQUIRED`;
- reject payloads containing `execution_evidence`, `success=true`,
  `verified=true`, or `action_started=true`;
- append to `RuntimeEventJournal`;
- fan out appended `RuntimeEvent` values in journal order;
- return appended events for snapshot/action_timeline projection.

Do not let the orchestrator call `RuntimeEventJournal.append(...)` directly.
That would split event construction, sequencing, append, and fan-out ownership.

## Snapshot And Action Timeline Strategy

Recommended snapshot strategy: **journal-derived backend projection through
ws_bridge snapshot building**.

The source of truth should remain backend journal/snapshot/protocol events, not
frontend inference.

Future `_build_runtime_snapshot(...)` should project non-executable decisions
from journal events and expose them in runtime snapshot data. The exact shape
should be owned by backend runtime contracts, likely:

- `commands.pending_approvals` from `ApprovalManager` for legacy and approved
  lifecycle compatibility;
- `commands.pending_clarifications` added when `ApprovalManager` gets a
  first-class clarification record;
- a journal-derived non-executable decision projection for
  `pending_approval`, `pending_clarification`, `last_blocked_action`,
  `last_guard_decision`, `last_risk_level`, and `terminal_non_executed`.

Recommended action_timeline strategy: keep it journal-derived.

`src/aegis/core/action_timeline.py` already folds non-executable guard events
from the event journal into:

- `approval_requested`;
- `clarification_requested`;
- `blocked_by_policy`.

Default wiring should rely on appended journal events feeding this projection,
not direct action timeline mutation.

Blockers before live use:

- first-class pending clarification lifecycle in `ApprovalManager`;
- live ws_bridge append helper with canonical sequence allocation;
- snapshot projection that is stable beyond the recent journal tail;
- tests showing reconnect snapshot contains pending approval/clarification and
  terminal blocked state without frontend inference.

## Legacy APPROVAL_REQUIRED Coexistence

Legacy `APPROVAL_REQUIRED` remains command-governance shaped.

Current emitters:

- `orchestrator.process(...)` calls `ws_bridge.emit_approval_required(...)`
  during legacy preflight approval;
- command routes can also call `ws_bridge.emit_approval_required(...)`;
- `ws_bridge.emit_approval_required(...)` emits `APPROVAL_REQUIRED` with
  payload shape `{ "command": <CommandRecord dict> }`;
- frontend socket handling currently listens to `APPROVAL_REQUIRED` and upserts
  that command record.

New approval semantics must use `APPROVAL_REQUESTED`, not `APPROVAL_REQUIRED`.
The new payload carries approval semantics such as `approval_request`,
`approval_id`, `proposed_action`, normalized params, risk, reason, and
`not_executed=true`.

Decision:

- do not remove legacy `APPROVAL_REQUIRED` yet;
- do not overload legacy `APPROVAL_REQUIRED`;
- keep tests that assert non-executable adapters and ws_bridge isolated append
  never emit `APPROVAL_REQUIRED`;
- migrate UI/command governance intentionally in a later approval lifecycle
  sprint.

Conflict risk: while both paths exist, default orchestrator wiring must avoid
emitting both legacy `APPROVAL_REQUIRED` and new `APPROVAL_REQUESTED` for the
same guard decision.

## Generic Click Default Enforcement Readiness

`classify_intent_risk("click", {})` currently returns
`clarification_required` with generic click quarantine / target resolution
wording. Generic click with low-level selector or coordinate-like params is not
ready by default and requires approval under current policy.

Future default enforcement must intercept parser or planner outputs before
executor dispatch:

- after plan step context and `action_id` exist;
- before `ACTION_STARTED`;
- before `executor.execute(...)`;
- before any tool `.run(...)` path;
- before execution evidence can be created.

Default enforcement must also reconcile legacy preflight approval. A medium-risk
legacy `click` can still be captured by the old `APPROVAL_REQUIRED` preflight.
The default migration should prevent dual approval semantics and ensure generic
click uses the new non-executable branch.

Required tests before turning default enforcement on:

- generic `click` with no target does not reach executor;
- generic `click` with selector/x/y still does not become ready by default;
- no `ACTION_STARTED` for unresolved click;
- no execution evidence for unresolved click;
- no legacy `APPROVAL_REQUIRED` for new generic click quarantine;
- ready `read_file` and ready `open_app` still reach executor;
- existing approved legacy command tests either migrate or remain explicitly
  legacy-scoped.

## Default Enable Readiness Decision

Default non-executable guard enforcement is **not ready**.

Resolved in this sprint:

- command lifecycle has a dedicated
  `CommandStatus.WAITING_FOR_CLARIFICATION`;
- sequence strategy is selected: ws_bridge-owned live batch creation/append
  under `_journal_emit_lock`;
- prebuilt adapter sequence numbers are documented and tested as isolated-only;
- legacy `APPROVAL_REQUIRED` and new `APPROVAL_REQUESTED` separation is
  documented and tested;
- generic click policy non-ready behavior is documented and tested.

Remaining blockers:

- implement ws_bridge live append helper with canonical sequence allocation;
- add first-class pending clarification lifecycle in `ApprovalManager`;
- decide how approval expiration maps into command lifecycle records;
- project non-executable pending state into live snapshots from journal/command
  lifecycle without relying on frontend inference;
- migrate or fence legacy `APPROVAL_REQUIRED` preflight to avoid duplicate
  approval events;
- run mixed concurrency tests for live event append order;
- only then remove the `enable_non_executable_guard_boundary` feature flag.

## Recommended Next Sprint

Runtime Non-Executable Live Append Helper v1:

- add `ws_bridge.append_non_executable_decision(...)` for live event creation,
  append, and fan-out under `_journal_emit_lock`;
- keep orchestrator default enforcement off;
- test mixed live sequence monotonicity, journal order, fan-out order, and
  replay reconstruction against an isolated journal/fanout path;
- do not mutate global snapshot directly;
- do not add approval endpoint or click target resolution.
