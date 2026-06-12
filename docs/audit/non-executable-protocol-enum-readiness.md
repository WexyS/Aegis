# Non-Executable Decision Protocol Enum Readiness

**Date:** 2026-05-22

**Sprint:** Non-Executable Decision Protocol Enum Readiness

**Scope:** Protocol/event enum readiness audit plus source-contract tests. No orchestrator wiring, executor behavior change, parser behavior change, frontend change, real event emission, approval endpoint, snapshot schema migration, click implementation, target resolution, model adapter, voice, Ultron bridge, or broad refactor.

**Superseded note:** This readiness decision was superseded by the follow-up `Non-Executable Protocol Enum + Frontend Mirror Contract` sprint, which added the backend and frontend enum values together. The original deferral remains documented below as the reason backend-only enum addition was not safe.

## Decision

`enum_values_added: no`

`deferred_reason: backend ProtocolEventType must exactly mirror frontend EventTypeEnum and frontend WebSocketEvent; adding backend enum values alone would break the existing protocol parity contract. Adding the full set safely requires a frontend protocol mirror and payload registry update, which is out of scope for this sprint.`

The non-executable projection event names remain design/projection-only for now. They are contract-tested in `non_executable_projection.py` outputs, but they are not canonical runtime `ProtocolEventType` values yet.

## Definitions Found

| Surface | Location | Role |
| --- | --- | --- |
| Backend canonical event enum | `src/aegis/core/protocol.py::ProtocolEventType` | Python runtime event type source. File states values must match frontend. |
| Backend runtime event envelope | `src/aegis/core/protocol.py::RuntimeEvent` | Uses `type`, `timestamp`, `trace_id`, `causation_id`, `span_id`, `sequence_num`, and `payload`. |
| Runtime event journal | `src/aegis/core/event_journal.py` | Persists `RuntimeEvent` objects; no separate enum is defined there. |
| WebSocket bridge emission | `src/aegis/api/ws_bridge.py` | Emits `ProtocolEventType` through `emit_event`; existing approval/block flows use `APPROVAL_REQUIRED` and `COMMAND_BLOCKED`. |
| Frontend Zod protocol mirror | `frontend/src/contracts/protocol.ts::EventTypeEnum` | Exhaustive frontend event enum; must mirror backend. |
| Frontend runtime enum mirror | `frontend/src/types/runtime.ts::WebSocketEvent` | Secondary frontend enum mirror used by runtime code. |
| Frontend payload registry | `frontend/src/contracts/protocol.ts::PayloadRegistry` | Maps event types to payload schemas; currently knows `APPROVAL_REQUIRED` and `COMMAND_BLOCKED`, not the new projection events. |
| Frontend socket handlers | `frontend/src/lib/socket.ts` | Handles current `APPROVAL_REQUIRED` and `COMMAND_BLOCKED` with command-status style payloads. |

Existing parity test:

- `tests/test_runtime/test_protocol.py::test_frontend_protocol_event_enum_matches_backend`

This test requires backend `ProtocolEventType`, frontend `EventTypeEnum`, and frontend `WebSocketEvent` to contain the exact same values.

## Event Name Readiness Matrix

| Proposed event | Current status | Canonical decision | Payload category | Replay meaning | Belongs in ProtocolEventType now? | Frontend mirror later? | Migration needed? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `COMMAND_CLASSIFIED` | Missing backend/frontend | Keep proposed canonical name | Guard classification | Rebuild `last_guard_decision` and causation links | No, deferred | Yes | Yes, protocol enum + payload registry |
| `APPROVAL_REQUESTED` | Missing backend/frontend; overlaps current `APPROVAL_REQUIRED` concept | Prefer `APPROVAL_REQUESTED` for first-class `ApprovalRequest` projection | Approval request | Reconstruct pending approval without execution | No, deferred | Yes | Yes, distinguish from older `APPROVAL_REQUIRED` payload |
| `CLARIFICATION_REQUESTED` | Missing backend/frontend | Keep proposed canonical name | Clarification request | Reconstruct pending clarification without execution | No, deferred | Yes | Yes |
| `ACTION_BLOCKED_BY_POLICY` | Missing backend/frontend | Keep proposed canonical name | Policy block | Reconstruct terminal non-executed blocked action | No, deferred | Yes | Yes |
| `COMMAND_WAITING_FOR_APPROVAL` | Missing backend/frontend | Keep proposed canonical name or collapse into `COMMAND_STATUS_CHANGED` later after payload design | Command lifecycle | Command is waiting, not failed | No, deferred | Yes if kept explicit | Yes |
| `COMMAND_WAITING_FOR_CLARIFICATION` | Missing backend/frontend | Keep proposed canonical name or collapse into `COMMAND_STATUS_CHANGED` later after payload design | Command lifecycle | Command is waiting, not failed | No, deferred | Yes if kept explicit | Yes |
| `COMMAND_BLOCKED` | Exists backend/frontend | Existing canonical command lifecycle name can remain | Command lifecycle | Command terminal blocked status | Already exists | Already exists | Payload expansion may be needed for `terminal_non_executed` |
| `APPROVAL_RESOLVED` | Missing backend/frontend | Keep proposed canonical name | Approval resolution | Update approval status; approved is permission only | No, deferred | Yes | Yes |
| `APPROVAL_EXPIRED` | Missing backend/frontend | Keep proposed canonical name, or represent as `APPROVAL_RESOLVED(status=expired)` after final protocol design | Approval expiration | Terminal non-executed approval result | No, deferred | Yes if kept explicit | Yes |
| `CLARIFICATION_RESOLVED` | Missing backend/frontend | Keep proposed canonical name | Clarification resolution | Clear pending clarification or create new plan reference | No, deferred | Yes | Yes |

## Existing Names And Conflicts

`APPROVAL_REQUIRED` already exists. It currently represents command governance and the frontend payload registry maps it to `ApprovalRequiredPayload` with a command-shaped payload. The new projection event `APPROVAL_REQUESTED` is more specific: it carries an `ApprovalRequest` object, normalized params, confirmation mode, scope, and expiration fields. Reusing `APPROVAL_REQUIRED` for the new payload would be ambiguous and would require payload migration anyway.

`COMMAND_BLOCKED` already exists. It is the right command-lifecycle terminal blocked event, but the new projection contract also needs `ACTION_BLOCKED_BY_POLICY` for the guard-level `BlockedAction` payload. `COMMAND_BLOCKED` can remain canonical for command lifecycle, while `ACTION_BLOCKED_BY_POLICY` should later carry policy-specific block details.

No current canonical protocol event represents `clarification_required`.

## Event Category Rules

The future canonical non-executable protocol events must be categorized as non-execution events:

- They must not imply `ACTION_STARTED`.
- They must not imply action completion.
- They must not imply `success=true`.
- They must not imply `verified=true`.
- They must not carry `execution_evidence`.
- They may carry `policy_evidence`, `guard_notes`, `ambiguities`, or `evidence_refs`.

Execution lifecycle events remain:

- `ACTION_STARTED`
- `ACTION_COMPLETED`
- `ACTION_FAILED`
- `ACTION_RETRY`
- `VERIFICATION_PASSED`
- `VERIFICATION_FAILED`

## Why Enum Addition Is Deferred

Adding only backend enum values is not safe because:

1. Backend `ProtocolEventType` explicitly mirrors frontend `EventTypeEnum`.
2. `tests/test_runtime/test_protocol.py` asserts exact parity between backend enum and frontend mirrors.
3. `frontend/src/contracts/protocol.ts::PayloadRegistry` lacks schemas for the proposed new event payloads.
4. `frontend/src/lib/socket.ts` only handles existing command-governance events, not first-class approval/clarification/block projection events.
5. This sprint forbids frontend changes and schema migration.

Therefore the correct readiness result is to keep the names projection-only until a dedicated protocol enum + frontend mirror sprint.

## Tests Added

`tests/test_runtime/test_non_executable_protocol_enum_readiness.py` locks the current readiness boundary:

- Backend/frontend protocol enums remain mirrored.
- Proposed projection event names are not fully canonical yet.
- Missing proposed names are documented as deferred.
- `COMMAND_BLOCKED` is recognized as the only already canonical proposed name.
- Projection event names are not execution lifecycle events.
- `ACTION_STARTED`, `ACTION_COMPLETED`, and `ACTION_FAILED` remain execution lifecycle events.
- `non_executable_projection.py` output remains projection-only for missing protocol names.

## Required Future Work Before Runtime Wiring

Before `guard_policy` emits real runtime events:

1. Add canonical backend `ProtocolEventType` values.
2. Add matching frontend `EventTypeEnum` values.
3. Add matching `WebSocketEvent` values.
4. Add payload schemas for `ApprovalRequest`, `ClarificationRequest`, and `BlockedAction` projections.
5. Add frontend socket handlers or snapshot-only rendering rules for pending approval, pending clarification, and blocked action cards.
6. Add protocol tests proving non-executable event payloads reject `execution_evidence`, `success=true`, `verified=true`, and `action_started=true`.
7. Only then wire orchestrator guard decisions to real journal/protocol emission.

## Recommendation

Recommended next sprint:

`Non-Executable Protocol Enum + Frontend Mirror Contract`

That sprint should update backend and frontend protocol enums together, add payload schemas, and keep runtime emission disabled until those contracts are green.
