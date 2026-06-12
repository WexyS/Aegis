# Non-Executable Decision Runtime Projection Design
**Date:** 2026-05-21

**Sprint:** Non-Executable Decision Runtime Projection Design

**Goal:** Define how `approval_required`, `clarification_required`, and `blocked` guard decisions should appear in runtime snapshot, journal, `action_timeline`, and replay before `guard_policy` is wired into orchestrator execution.

**Status:** Design-only. No runtime behavior, orchestrator wiring, executor behavior, parser behavior, frontend behavior, event emission, endpoint, schema migration, click implementation, target resolution, LLM/model adapter, voice, Ultron bridge, or broad refactor is implemented by this document.

## Core Decision

A non-executable guard decision is runtime truth, not an action execution.

The runtime must make the decision visible, journaled, replayable, and auditable without pretending that the executor ran. A pending approval, pending clarification, or blocked action must never produce `ACTION_STARTED`, must never contain fake `execution_evidence`, and must never be displayed as verified action success.

The authoritative surfaces remain:

- backend runtime snapshot
- protocol events
- event journal
- action timeline projection
- replay/projection state
- execution evidence only when an action actually ran

## 1. Decision Categories

| State | Runtime meaning | Executed? | Terminal? | Evidence meaning |
| --- | --- | --- | --- | --- |
| `ready` | Guard policy allows the concrete intent/action to proceed to the execution phase. | Not yet | No | May require future execution evidence after dispatch. |
| `approval_required` | Guard policy has a concrete proposed action, but user approval is required before dispatch. | No | Pending until resolved | May include policy evidence or evidence references, not execution evidence. |
| `clarification_required` | Guard policy cannot safely resolve intent, target, params, or context. | No | Pending until answered, expired, or cancelled | May include ambiguity notes, not execution evidence. |
| `blocked` | Guard policy forbids the proposed action in the current context. | No | Yes | May include policy evidence, not execution evidence. |
| `unverified` | Executor ran, but verifier/evidence gate did not prove success. | Yes | Yes | Contains execution evidence that failed or was insufficient for verification. |
| `failed` | Execution failed, hard failure occurred, or evidence gate produced a failure result. | Attempted or failed before completion | Yes | May contain failure proof or execution evidence. |
| `cancelled` | User or system cancelled before or during execution. | Maybe | Yes | If no dispatch happened, no execution evidence is present. If cancelled during execution, partial evidence may exist. |

Clarifications:

- `approval_required` is non-executed and not failed.
- `approval_required` is not unverified.
- Approval is permission to attempt execution later; approval is not success and not verification.
- `clarification_required` is non-executed and must not fall through to a older executable action.
- `blocked` is terminal non-executed and must not be converted to `approval_required` unless a future explicit appeal policy exists.
- `unverified` always means an action ran and the evidence contract did not prove success.
- `failed` means execution failed, not that approval was denied or clarification was unresolved.

## 2. Journal Projection

Non-executable decisions need first-class journal events so replay can reconstruct the same state without invoking the executor.

### Event Summary

| Event | Purpose | Replay meaning |
| --- | --- | --- |
| `COMMAND_CLASSIFIED` | Records the guard decision for a parsed intent or command step. | Rebuilds `last_guard_decision` and causation links. |
| `APPROVAL_REQUESTED` | Records an `ApprovalRequest`. | Reconstructs pending approval without executing it. |
| `CLARIFICATION_REQUESTED` | Records a `ClarificationRequest`. | Reconstructs pending clarification without executing it. |
| `ACTION_BLOCKED_BY_POLICY` | Records a `BlockedAction`. | Reconstructs blocked terminal non-executed decision. |
| `COMMAND_WAITING_FOR_APPROVAL` | Marks command lifecycle as waiting on approval. | Keeps command pending, not failed. |
| `COMMAND_WAITING_FOR_CLARIFICATION` | Marks command lifecycle as waiting on user clarification. | Keeps command waiting, not failed. |
| `COMMAND_BLOCKED` | Marks command terminal non-executed because policy blocked it. | Restores terminal blocked command status. |
| `APPROVAL_RESOLVED` | Records approved, denied, expired, or cancelled approval decision. | Updates approval status; does not prove execution success. |
| `CLARIFICATION_RESOLVED` | Records user answer, expiration, or cancellation. | Clears pending clarification or starts a new classified plan. |

### Required Fields

Every proposed journal event should include:

- `event_id`
- `event_type`
- `command_id`
- `trace_id`
- `span_id` if applicable
- `sequence_num`
- `causation_id`
- `timestamp`
- `decision_status`
- `risk_level`
- `policy_rule`
- `reason`
- `user_message`
- `evidence_refs`
- `payload`

### Event Details

| Event | Required payload fields | Notes |
| --- | --- | --- |
| `COMMAND_CLASSIFIED` | `intent`, `normalized_params`, `decision_status`, `risk_level`, `policy_rule`, `requires_approval`, `requires_clarification`, `blocked` | This is the guard result. It is not an execution event. |
| `APPROVAL_REQUESTED` | `approval_request`, `proposed_action`, `approval_scope`, `required_confirmation_mode`, `expires_at` | Creates or replaces `pending_approval` for the command. |
| `CLARIFICATION_REQUESTED` | `clarification_request`, `ambiguity_type`, `question`, `options`, `blocked_until_answer`, `expires_at` | Creates or replaces `pending_clarification` for the command. |
| `ACTION_BLOCKED_BY_POLICY` | `blocked_action`, `policy_rule`, `safe_alternatives`, `retry_allowed` | Terminal guard decision for that proposed action. |
| `COMMAND_WAITING_FOR_APPROVAL` | `approval_id`, `command_status`, `blocked_execution: true` | Command is pending approval, not failed. |
| `COMMAND_WAITING_FOR_CLARIFICATION` | `clarification_id`, `command_status`, `blocked_execution: true` | Command is waiting on an answer, not failed. |
| `COMMAND_BLOCKED` | `blocked_id`, `command_status`, `terminal: true`, `executed: false` | Command cannot continue unless a future new command is created. |
| `APPROVAL_RESOLVED` | `approval_id`, `approval_status`, `resolved_by`, `resolved_at`, `reason` | `approved` permits a later execution phase. `denied`, `expired`, and `cancelled` are terminal non-executed outcomes for that request. |
| `CLARIFICATION_RESOLVED` | `clarification_id`, `resolution_status`, `answer`, `new_plan_id` if any | A clarification answer may produce a new normalized plan. It does not mutate the system by itself. |

### Causation Rules

- `COMMAND_CLASSIFIED` is caused by the parser/decomposition result or command step it classified.
- `APPROVAL_REQUESTED`, `CLARIFICATION_REQUESTED`, and `ACTION_BLOCKED_BY_POLICY` are caused by `COMMAND_CLASSIFIED`.
- Waiting/blocked command lifecycle events are caused by the corresponding request/block event.
- Resolution events are caused by user/system approval or clarification input.
- No non-executable event should be caused by `ACTION_STARTED`, because no action started.

## 3. Runtime Snapshot Projection

The runtime snapshot should expose pending and terminal non-executable decisions explicitly.

Proposed snapshot fields:

```yaml
active_command:
  command_id: string
  text: string
  status: string
active_trace_id: string | null
pending_approval: ApprovalRequest | null
pending_clarification: ClarificationRequest | null
last_blocked_action: BlockedAction | null
last_guard_decision: GuardDecisionSummary | null
queue_depth: integer
command_status: string
last_risk_level: none | low | medium | high | critical
cancellation_requested: boolean
```

`GuardDecisionSummary` should be a projection-safe subset:

```yaml
GuardDecisionSummary:
  decision_status: ready | approval_required | clarification_required | blocked | unverified | failed | cancelled
  risk_level: none | low | medium | high | critical
  reason: string
  policy_rule: string
  requires_approval: boolean
  requires_clarification: boolean
  blocked: boolean
  evidence_required: boolean
  rollback_required: boolean
  safe_alternatives: list
```

Snapshot behavior:

- `approval_required` sets `pending_approval`, clears `pending_clarification` for the same command step, sets `last_guard_decision`, and leaves command status as waiting/pending approval.
- `clarification_required` sets `pending_clarification`, clears `pending_approval` for the same command step, sets `last_guard_decision`, and leaves command status as waiting/pending clarification.
- `blocked` sets `last_blocked_action`, clears pending approval/clarification for the blocked command step, sets `last_guard_decision`, and marks command terminal non-executed.
- Denied approval becomes terminal non-executed.
- Expired approval becomes terminal non-executed.
- Cancelled approval becomes terminal non-executed.
- Approved approval clears `pending_approval` and allows the next execution phase later. Approval itself does not set success, verified, or unverified.
- Resolved clarification may create a new normalized plan. The clarification response itself is not execution.
- `queue_depth` should not count pending approval/clarification as active execution.

## 4. Action Timeline Projection

The action timeline must distinguish execution events from guard decisions.

Proposed timeline entry kinds:

| Kind | Executed? | Verified success possible? | Evidence field |
| --- | --- | --- | --- |
| `action_started` | Yes | No, not yet | May include dispatch context, not final evidence. |
| `action_completed_verified` | Yes | Yes | `execution_evidence` required. |
| `action_completed_unverified` | Yes | No | `execution_evidence` required, `verified: false`. |
| `action_failed` | Attempted or failed before completion | No | Failure evidence/proof if available. |
| `action_cancelled` | Maybe | No | Optional partial evidence only if execution started. |
| `approval_requested` | No | No | `guard_evidence`, `policy_evidence`, or `evidence_refs`. |
| `clarification_requested` | No | No | Ambiguity details, options, `evidence_refs`. |
| `blocked_by_policy` | No | No | Policy rule, reason, `evidence_refs`. |
| `approval_denied` | No | No | Approval resolution metadata. |
| `approval_expired` | No | No | Approval expiration metadata. |

Projection rules:

- Non-executable entries must use `executed: false`.
- Non-executable entries must not include fake `execution_evidence`.
- Non-executable entries may include `guard_evidence`, `policy_evidence`, `ambiguities`, `guard_notes`, or `evidence_refs`.
- Timeline UI must never render `approval_requested`, `clarification_requested`, or `blocked_by_policy` as verified success.
- `approval_requested` may reference the proposed action, but the proposed action is not an action row that started.
- If a command contains multiple planned steps, blocking one step must not create partial success for earlier steps unless those earlier steps actually executed and produced evidence.

## 5. Replay Semantics

Replay must reconstruct decisions, not re-decide them opportunistically.

Replay requirements:

- Reconstruct `ApprovalRequest` from `APPROVAL_REQUESTED`.
- Reconstruct `ClarificationRequest` from `CLARIFICATION_REQUESTED`.
- Reconstruct `BlockedAction` from `ACTION_BLOCKED_BY_POLICY`.
- Preserve `sequence_num` order.
- Preserve `causation_id`, `command_id`, `trace_id`, and `span_id`.
- Do not execute pending approvals.
- Do not auto-approve.
- Do not convert blocked decisions to `approval_required`.
- Do not convert clarification to a older executable fallback.
- Distinguish non-executed decisions from executed but unverified actions.
- Rebuild `pending_approval`, `pending_clarification`, `last_blocked_action`, `last_guard_decision`, and `action_timeline` from journal events.
- Treat `APPROVAL_RESOLVED(status=approved)` as permission state only. It is not equivalent to `ACTION_SUCCESS`.
- Treat `APPROVAL_RESOLVED(status=denied|expired|cancelled)` as terminal non-executed for that approval request.

Replay must not invent evidence. If an action never started, replay must not create `execution_evidence`.

## 6. GuardDecision Mapping

| GuardDecision state | Runtime projection | Journal events | Executor call? |
| --- | --- | --- | --- |
| `ready` | May continue to execution phase. `last_guard_decision` records ready status. | `COMMAND_CLASSIFIED` | Later phase may call executor. |
| `approval_required` | Create `pending_approval`; command waits. | `COMMAND_CLASSIFIED`, `APPROVAL_REQUESTED`, `COMMAND_WAITING_FOR_APPROVAL` | No |
| `clarification_required` | Create `pending_clarification`; command waits. | `COMMAND_CLASSIFIED`, `CLARIFICATION_REQUESTED`, `COMMAND_WAITING_FOR_CLARIFICATION` | No |
| `blocked` | Create `last_blocked_action`; command terminal non-executed. | `COMMAND_CLASSIFIED`, `ACTION_BLOCKED_BY_POLICY`, `COMMAND_BLOCKED` | No |

Mapping details:

- `GuardDecision.approval_request` becomes the snapshot `pending_approval`.
- `GuardDecision.clarification_request` becomes the snapshot `pending_clarification`.
- `GuardDecision.blocked_action` becomes the snapshot `last_blocked_action`.
- `GuardDecision.reason`, `policy_rule`, `risk_level`, `evidence_required`, and `rollback_required` become `last_guard_decision`.
- `safe_alternatives` should be projected to both blocked/clarification UI surfaces and timeline metadata.

## 7. Generic Click Projection Policy

Generic click remains quarantined.

Projection rules:

- Generic `click` without a resolved target becomes `clarification_required` or `blocked`.
- Generic `click` with selector or coordinates is still not `ready` by default.
- Generic `click` must not create `ACTION_STARTED`.
- Generic `click` must not create `execution_evidence`.
- Generic `click` must appear as a non-executable guard decision.
- Approval for a generic click, if temporarily represented for older compatibility, must not imply semantic target resolution.
- Coordinate-only click must require explicit user coordinates and window evidence in a future policy before any dispatch is possible.
- Coordinate-in-window evidence is geometry verification, not semantic verification.
- Future click work must introduce explicit `browser_click` and `desktop_click` capability contracts.
- `browser_click` and `desktop_click` remain future explicit capabilities until target resolution and evidence contracts exist.

## 8. UI Guidance

This section is design guidance only. No frontend implementation is part of this sprint.

UI should show:

- pending approval card
- pending clarification card
- blocked action card
- exact proposed action
- normalized params
- risk level
- policy rule
- user-facing reason
- expiration state
- rollback note when available
- safe alternatives when available

UI must show clearly:

- `approval_required`: not executed
- `clarification_required`: not executed
- `blocked`: not executed
- approval does not mean verified
- denied/expired approval is terminal non-executed
- no fake evidence is available for non-executed decisions

Voice, if added later, is only a UI/input surface. It is not authority.

## 9. Tests Required Before Implementation

Future implementation should add focused tests before wiring the guard into execution:

- `approval_required` creates snapshot `pending_approval`.
- `approval_required` emits journal/protocol projection events without executor call.
- `clarification_required` creates snapshot `pending_clarification`.
- `clarification_required` emits journal/protocol projection events without executor call.
- `blocked` creates terminal non-executed command.
- `blocked` emits `ACTION_BLOCKED_BY_POLICY` and `COMMAND_BLOCKED` without executor call.
- Generic `click` produces non-executable projection.
- Generic `click` does not produce `ACTION_STARTED`.
- Generic `click` does not produce `execution_evidence`.
- Denied approval is terminal non-executed.
- Expired approval is terminal non-executed.
- Cancelled approval is terminal non-executed.
- Approved approval proceeds only to a later execution phase and does not count as success.
- Replay reconstructs approval request, clarification request, and blocked decision.
- Replay does not auto-approve.
- Replay does not convert blocked to approval_required.
- Replay does not convert clarification into older executable fallback.
- `action_timeline` never shows fake verified success for non-executable decisions.
- `sequence_num` is monotonic.
- `causation_id` is preserved.
- `last_guard_decision` matches the journaled guard decision.

## 10. Future Implementation Slices

Recommended narrow implementation order:

1. Projection-only event constants and payload contract tests.
2. Runtime snapshot projection tests for `pending_approval`, `pending_clarification`, and `last_blocked_action`.
3. Journal append tests proving non-executable decisions do not call executor.
4. Action timeline projection tests for non-executed entries.
5. Replay tests for approval, clarification, and blocked decisions.
6. Orchestrator guard-policy wiring behind tests.
7. Generic click guard gate that prevents older click from dispatching.
8. Approval resolve endpoint.
9. UI pending approval/clarification/blocked panels.
10. Future `browser_click` and `desktop_click` design/implementation only after target resolution contracts exist.

## 11. Out Of Scope

Explicitly out of scope for this sprint:

- runtime implementation
- orchestrator wiring
- executor changes
- parser behavior changes
- approval endpoint
- frontend implementation
- event emission implementation
- snapshot schema migration
- click implementation
- `browser_click` implementation
- `desktop_click` implementation
- target resolution
- LLM/model adapter
- voice
- Ultron bridge
- broad cleanup

## Decision

`implementation_ready: design_only`

The projection contract is ready to be converted into focused tests, but runtime wiring should wait until those tests exist. The next sprint should implement projection contract tests without executor dispatch and without adding approval resolution behavior.
