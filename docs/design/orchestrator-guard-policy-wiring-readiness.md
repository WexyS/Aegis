# Orchestrator Guard Policy Wiring Readiness

**Date:** 2026-05-22

**Sprint:** Non-Executable Guard Decision Orchestrator Wiring Readiness

**Status:** Audit/design only. No runtime behavior, orchestrator behavior, executor behavior, parser behavior, frontend behavior, real event emission, journal append mutation, snapshot mutation, approval endpoint, UI, click blocking, target resolution, LLM planner, model adapter, voice, Ultron bridge, or broad refactor is implemented here.

## Decision Output

| Field | Decision |
| --- | --- |
| `recommended_guard_insertion_point` | Per intent/action inside `Orchestrator.process`, after parser/decomposition and planner normalization, after the step `ExecutionContext` exists, and immediately before `emit_action_started(...)` and `self.executor.execute(...)`. |
| `wiring_ready` | No. The placement is clear, but the runtime still needs a small canonical event-emission/projection adapter and command lifecycle status mapping before behavior wiring. |
| `blockers_before_wiring` | Existing legacy approval event/status path conflicts with new `APPROVAL_REQUESTED` flow; snapshot schema lacks first-class `pending_clarification`/`last_blocked_action`; `action_timeline` only projects execution/verification events; generic `click` remains executable through legacy paths; current `CommandStatus` has no explicit `waiting_for_clarification`. |
| `tests_required_before_wiring` | Add executor-spy, event-order, journal-append, snapshot-projection, action-timeline, click-quarantine, monotonic-sequence, and replay tests listed below before or in the wiring sprint. |
| `runtime_files_likely_to_change` | `src/aegis/orchestrator/orchestrator.py`, `src/aegis/api/ws_bridge.py`, `src/aegis/core/runtime_authority.py`, `src/aegis/core/commands.py`, `src/aegis/core/action_timeline.py`, `src/aegis/core/non_executable_projection.py`, and tests under `tests/test_runtime`/`tests/test_core`. |
| `protocol_frontend_files` | Protocol enum/frontend mirror likely remain unchanged for the already-canonical event names. Frontend rendering may later need explicit handling for pending clarification/blocked timeline rows, but this sprint does not require frontend changes. |
| `recommended_next_sprint` | Implement a runtime non-executable event/projection adapter behind tests, then wire `classify_intent_risk` at the executor boundary for one narrow path. |

## 1. Current Orchestrator Execution Path

### Entry points

HTTP commands enter through `src/aegis/api/routes_command.py::handle_command(...)`, which cleans input, builds a `CommandRequest`, and calls `get_orchestrator().process(...)` directly.

WebSocket commands enter through `src/aegis/api/ws_bridge.py::_process_command(...)`, which creates an approval-manager `CommandRecord`, queues a `QueuedCommand`, emits a queued `COMMAND_RECEIVED`, and lets `_command_worker_loop(...)` call `get_orchestrator().process(...)` serially.

### ID creation

`Orchestrator.process(...)` creates a root `ExecutionContext` via `ExecutionContext.create_root()`. That creates:

- `trace_id`
- root `span_id`
- no parent span

The current `command_id` is `request.context["command_id"]` when supplied by the queue/approval resume path, otherwise it falls back to the root `trace_id`.

Per executable step, the orchestrator creates `step_ctx = ctx.create_child(step_index=len(all_actions))`. The current `action_id` is `str(step_ctx.span_id)`.

### Intent entry and planning

`IntentResult` objects enter the orchestrator after:

1. `self.router.route(request)`
2. `self.parser.parse(current_goal, model=routing.planner_model)`
3. `self.planner.plan(intents)`
4. `PlanSimulator.simulate(plan)`

The planner currently mutates/enriches normalized executable intents with app resolution metadata and focus requirements before execution.

### Current risk, guard, approval, and cancellation logic

Current guard logic is legacy `self.guard.evaluate(intent)` from `aegis.guard.action_guard`, not `aegis.core.guard_policy.classify_intent_risk(...)`.

There are two current guard passes:

- A preflight pass over the whole plan before the execution loop. It emits `GUARD_EVALUATED`, accumulates risk/warnings, may mark blocked, may register `PENDING_APPROVAL`, or may mark the command `RUNNING`.
- A second per-step pass inside the execution loop. It emits another `GUARD_EVALUATED` and can block before `ACTION_STARTED`.

Current approval behavior is legacy command lifecycle approval:

- `approval_manager.register_pending(...)`
- `ws_bridge.emit_approval_required(...)`
- `CommandStatus.PENDING_APPROVAL`
- HTTP/WebSocket approve re-runs `Orchestrator.process(...)` with `approval_granted=True`

Cancellation exists through `CancellationToken`. It is checked before execution and inside the execution loop. HTTP/WebSocket cancel endpoints mark the token/record cancelled and emit `COMMAND_CANCELLED`.

### Executor call boundary

The executable boundary is currently:

1. create `step_ctx`
2. legacy per-step guard evaluation
3. `action_id = str(step_ctx.span_id)`
4. `ws_bridge.emit_action_started(...)`
5. `await self.executor.execute(intent, step_ctx, cancellation_token=cancellation_token)`
6. semantic verification and process/window evidence gate
7. `emit_action_completed(...)` or `emit_action_failed(...)`

This is the exact future cut point for non-executable guard decisions.

### RuntimeEvent emission and journal append

Protocol `RuntimeEvent` objects are created by `ws_bridge.emit_event(...)`, which delegates to `_create_and_append_event(...)`.

`_create_and_append_event(...)` is the canonical runtime event append path:

- creates a `RuntimeEvent` via `create_event(...)`
- assigns `sequence_num` from the global protocol counter
- appends to `RuntimeEventJournal`
- serializes creation and append under `_journal_emit_lock`

`RuntimeEventJournal.append(...)` finalizes hash-chain fields and persists to `logs/runtime_events.jsonl`.

Separate from the runtime event journal, `Orchestrator.process(...)` also writes:

- `self.event_logger.log(...)` for legacy/local logs
- `self.journal.record(...)` in `aegis.replay.golden_journal` after final status resolution

The non-executable wiring should use the runtime event journal path, not only legacy event logger or golden trace.

### Snapshot and action timeline projection

`ws_bridge._build_runtime_snapshot(...)` composes the backend snapshot from:

- runtime authority snapshot
- approval-manager command snapshot
- maintenance scan state
- app registry
- tool registry
- `project_action_timeline(journal.recent_events(), ...)`

`RuntimeAuthority` mutates on selected event emissions:

- `COMMAND_RECEIVED` with `trace_id` starts active command
- `ACTION_STARTED` sets active span/tool
- `RECOVERY_TRIGGERED` updates recovery depth
- `TASK_FINISHED` clears active command
- `emit_state_change(...)` mutates FSM state

The current `action_timeline` only projects `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`, `VERIFICATION_PASSED`, and `VERIFICATION_FAILED`. It does not yet project `APPROVAL_REQUESTED`, `CLARIFICATION_REQUESTED`, or `ACTION_BLOCKED_BY_POLICY`.

### Terminal command status

At the end of `Orchestrator.process(...)`, final status is derived from `all_actions`:

- all successful actions -> `EXECUTED`
- any cancelled action/token -> `CANCELLED`
- any blocked action -> `BLOCKED`
- otherwise -> `FAILED`

Pending approval returns early and avoids the final status block.

## 2. Proposed Guard Insertion Point

Future `classify_intent_risk(intent, params, context)` should run per intent/action, inside the orchestrator worker execution path, after parser/decomposition and planner normalization, and before any executor dispatch.

Recommendation:

- **Per command:** use only for aggregate reporting/highest-risk summary, not as the executor cut point.
- **Per intent/action:** yes, this is the primary enforcement unit.
- **Per plan step:** yes, each planned `IntentResult` should be classified independently.
- **Before queue insertion:** no. WebSocket queue intake has raw text only, and HTTP has no queue. Classifying there would duplicate parser/planner assumptions and miss planner-enriched params.
- **After queue insertion but before execution:** yes, indirectly. The worker calls the orchestrator, and the orchestrator should classify before dispatch.
- **Inside worker loop before executor call:** the worker loop should remain a serial dispatcher. The actual guard branch should be inside `Orchestrator.process(...)` immediately before `emit_action_started(...)`.

The future wiring should either replace or strictly supersede the legacy `self.guard.evaluate(...)` decision at the dispatch boundary. Running both as independent blockers risks double events, mismatched statuses, and conflicting approval semantics.

## 3. Future Non-Executable Branch

If `GuardDecision.ready`:

- emit/store `COMMAND_CLASSIFIED` if the wiring sprint chooses to journal ready classifications
- continue to existing `ACTION_STARTED` and executor path
- preserve existing execution, verification, evidence gate, telemetry, and terminal status logic

If `GuardDecision.approval_required`:

- do not call executor
- do not emit `ACTION_STARTED`
- build non-executable runtime events in canonical order
- append journal events through the runtime event append path
- update snapshot/projection so `pending_approval` is backend-derived
- add action timeline entry kind `approval_requested`
- set command lifecycle to waiting/pending approval
- return/wait without marking success
- approval itself is not success and not verification

If `GuardDecision.clarification_required`:

- do not call executor
- do not emit `ACTION_STARTED`
- build non-executable runtime events in canonical order
- append journal events through the runtime event append path
- update snapshot/projection so `pending_clarification` is backend-derived
- add action timeline entry kind `clarification_requested`
- set command lifecycle to waiting for clarification
- no legacy fallback and no partial execution

If `GuardDecision.blocked`:

- do not call executor
- do not emit `ACTION_STARTED`
- build non-executable runtime events in canonical order
- append journal events through the runtime event append path
- update snapshot/projection so `last_blocked_action` is backend-derived
- add action timeline entry kind `blocked_by_policy`
- set command terminal non-executed
- do not create execution evidence

## 4. Executor Call Boundary

Future assertion point:

```text
for each planned intent:
  step_ctx = ctx.create_child(...)
  action_id = str(step_ctx.span_id)
  decision = classify_intent_risk(intent.intent, intent.params, context)
  if decision is non-executable:
      persist/project non-executable branch
      return or break without execution
  emit_action_started(...)
  action_result = await self.executor.execute(...)
```

For `approval_required`, `clarification_required`, and `blocked`:

- `self.executor.execute(...)` must not be called
- registered tool `run(...)` must not be called
- `ACTION_STARTED` must not be emitted
- `execution_evidence` must not be created
- `success`, `verified`, or `verification_state=verified` must not be set

Test spy design:

- Use the existing `tests/test_runtime/test_command_lifecycle.py` fake parser/planner/executor pattern.
- Inject a fake executor with a call counter and fail-fast `execute(...)`.
- Monkeypatch or inject `classify_intent_risk(...)` to return each non-executable decision.
- Monkeypatch `ws_bridge.emit_action_started` to fail if called.
- Inspect runtime journal events after the command to prove no `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`, `VERIFICATION_PASSED`, or `VERIFICATION_FAILED` exists for the command.

## 5. Event Emission Boundary

Future non-executable event flow:

`approval_required`:

1. `COMMAND_CLASSIFIED`
2. `APPROVAL_REQUESTED`
3. `COMMAND_WAITING_FOR_APPROVAL`

`clarification_required`:

1. `COMMAND_CLASSIFIED`
2. `CLARIFICATION_REQUESTED`
3. `COMMAND_WAITING_FOR_CLARIFICATION`

`blocked`:

1. `COMMAND_CLASSIFIED`
2. `ACTION_BLOCKED_BY_POLICY`
3. `COMMAND_BLOCKED`

Ready/executed actions keep the existing execution flow:

- `ACTION_STARTED`
- `ACTION_COMPLETED` / `ACTION_FAILED` / later `ACTION_CANCELLED` if added
- existing verification/evidence events when real execution evidence exists

The future adapter should emit through `ws_bridge` or a `ws_bridge`-owned helper so runtime authority, journal append, and socket fan-out stay centralized.

## 6. Sequence and Causation Plan

Future wiring must use the existing canonical sequence source:

- `RuntimeEvent.sequence_num` default factory in `aegis.core.protocol`
- `ws_bridge._create_and_append_event(...)` under `_journal_emit_lock`
- `RuntimeEventJournal.append(...)`
- `ensure_sequence_at_least(...)` when hydrating persisted journal state

Do not use `build_non_executable_runtime_events(..., starting_sequence_num=...)` directly for live appends, because that helper is pure and intentionally accepts explicit dry-run sequence numbers.

Recommended live causation:

- `COMMAND_CLASSIFIED.causation_id`: previous parser/plan event id if the emitter captures it; otherwise the current command event id when available.
- `APPROVAL_REQUESTED.causation_id`: `COMMAND_CLASSIFIED.event_id`
- `CLARIFICATION_REQUESTED.causation_id`: `COMMAND_CLASSIFIED.event_id`
- `ACTION_BLOCKED_BY_POLICY.causation_id`: `COMMAND_CLASSIFIED.event_id`
- waiting/blocked command lifecycle event causation: the request/block event id

Identifier rules:

- `trace_id`: root `ctx.trace_id`, unchanged for the command.
- `command_id`: approval-manager command id, stable across pending/resume.
- `span_id`: step `step_ctx.span_id` for per-action decisions. Use root span only for command-level classification.
- `action_id`: may be `str(step_ctx.span_id)` for a proposed action, but non-executable events must mark it as proposed/not-executed and must not imply dispatch.
- replay order: always sort by `sequence_num`, not timestamp.
- no duplicate sequence numbers: live non-executable append must create each event under the same append lock used by current runtime events.

## 7. Snapshot and Action Timeline Projection Plan

Existing pure helpers:

- `project_guard_decision_to_snapshot_patch(...)`
- `project_guard_decision_to_timeline_entry(...)`
- `reconstruct_non_executable_decision_from_journal(...)`

Recommendation:

- Do not mutate snapshot ad hoc inside the orchestrator.
- Add a runtime/projection adapter that emits and appends canonical non-executable events, then lets snapshot/timeline projection derive state from the journal and command manager.
- Extend `RuntimeAuthority` only for active command/span/FSM fields if needed.
- Extend `ApprovalManager` or a small command lifecycle projection for pending clarification and terminal non-executed blocked state.
- Extend `project_action_timeline(...)` or add a sibling projection so non-executable entries appear in backend snapshot from journal events.

Backend/journal/snapshot remains the source of truth. The frontend must not infer pending approval, pending clarification, or blocked state from local button clicks, text labels, or optimistic request state.

## 8. Generic Click Quarantine Wiring Plan

Current audit result: generic `click` can still reach executor through legacy parser, AI parser, registry, orchestrator verified-tool/proof lists, and deterministic executor browser-click compatibility paths.

Future enforcement:

- classify generic `click` before executor dispatch.
- generic `click` without resolved `browser_click`/`desktop_click` target becomes `clarification_required` or `blocked`.
- generic `click` with selector, `x`, `y`, or coordinate params is not `ready` by default.
- coordinate click requires explicit coordinates, window/browser context, and policy approval.
- unresolved generic click must not emit `ACTION_STARTED`.
- unresolved generic click must not create `execution_evidence`.
- approval does not replace target resolution.

This sprint does not implement the quarantine. It only identifies the dispatch cut point that will make the quarantine enforceable.

## 9. Approval Resolve Lifecycle, Future Only

Future approval resolution should attach at the existing HTTP/WebSocket approval endpoints only after the non-executable journal flow exists.

Future lifecycle:

- approval resolve endpoint receives approve/deny
- append `APPROVAL_RESOLVED`
- if denied: command becomes terminal non-executed
- if expired: command becomes terminal non-executed
- if approved: command step becomes eligible for execution
- approved action still goes through `ACTION_STARTED`, executor, evidence, and verification later
- approval does not imply verified success

The current approve path re-runs `Orchestrator.process(...)` with `approval_granted=True`. The wiring sprint should either adapt that resume behavior to consume the recorded approval request safely or defer endpoint changes until the non-executable event/projection adapter is in place.

## 10. Test Plan for Actual Wiring Sprint

Required tests:

- `approval_required` guard decision prevents executor call.
- `clarification_required` guard decision prevents executor call.
- `blocked` guard decision prevents executor call.
- no `ACTION_STARTED` for non-executable decisions.
- non-executable `RuntimeEvent` objects are emitted in canonical order.
- runtime event journal receives non-executable events.
- snapshot `pending_approval` is set from backend projection.
- snapshot `pending_clarification` is set from backend projection.
- blocked action is terminal non-executed.
- action timeline contains `approval_requested`, `clarification_requested`, and `blocked_by_policy` entries.
- generic `click` is intercepted before executor.
- ready low-risk `open_app` still reaches executor.
- ready `read_file` still reaches executor.
- existing successful action behavior does not regress.
- `sequence_num` remains monotonic.
- replay reconstructs non-executable decisions.
- frontend build/types remain valid.

Suggested focused files:

- `tests/test_runtime/test_command_lifecycle.py`
- `tests/test_runtime/test_event_journal.py`
- `tests/test_runtime/test_action_timeline.py`
- `tests/test_runtime/test_protocol.py`
- `tests/test_core/test_non_executable_event_dry_run.py`
- `tests/test_core/test_non_executable_projection.py`
- `tests/test_runtime/test_runtime_truth_e2e_smoke.py`

## 11. Risk Assessment

Known risks before wiring:

- Existing `APPROVAL_REQUIRED` legacy event can conflict with new `APPROVAL_REQUESTED` semantics.
- `CommandStatus.PENDING_APPROVAL` exists, but there is no explicit `waiting_for_clarification` enum value.
- Snapshot schema currently exposes command manager records but not first-class `pending_clarification` or `last_blocked_action`.
- `action_timeline` currently mixes only execution and verification events; adding guard rows must not make them look executed.
- Old generic click tests currently expect executable click behavior.
- Frontend may not render the new events even though enum values exist.
- Approval pending queue/resume path can deadlock or re-run stale plans if command records and queued commands diverge.
- Cancellation can target pending approval or clarification and must become terminal non-executed without executor dispatch.
- Replay ambiguity can occur if causation ids are omitted or duplicated.
- Duplicate sequence numbers can occur if dry-run explicit sequence numbers are reused for live journal append.
- Accidental executor call before guard can happen if classification is added only in preflight and not at the dispatch boundary.
- Existing preflight legacy guard plus new guard-policy branch can double-block, double-approve, or report mismatched risk.

## 12. Recommended Next Sprint

Recommended next sprint: **Runtime Non-Executable Event Adapter v1**.

Scope should be narrow:

- add a `ws_bridge`-owned helper to append/fan-out non-executable decision events using canonical sequence numbers
- extend snapshot/action-timeline projection for non-executable events
- add tests proving journal order, snapshot projection, no execution events, and replay reconstruction
- do not yet classify live orchestrator intents unless the adapter tests are green

After that, run the actual orchestrator wiring sprint at the executor boundary.

## Intentionally Not Done

- No guard-policy wiring into orchestrator.
- No executor behavior change.
- No parser behavior change.
- No real event bus emission for non-executable decisions.
- No journal append mutation for non-executable decisions.
- No runtime snapshot mutation for non-executable decisions.
- No approval resolve endpoint change.
- No UI panel or frontend rendering change.
- No click blocking implementation.
- No browser click or desktop click implementation.
- No target resolution.
- No LLM planner/model adapter/voice/Ultron bridge.
