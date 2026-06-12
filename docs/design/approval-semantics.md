# Approval Semantics Design
**Goal:** Define how Aegis represents `approval_required`, `clarification_required`, `blocked`, and proposed actions before risky mutation, maintenance action, desktop click, browser click, or model-planned action is enabled.

**Status:** Design-only. No production code, endpoint, frontend, executor, orchestrator, parser, click, target-resolution, model-adapter, or schema migration is implemented by this document.

## Core Decision

Model, user, parser, and planner surfaces may propose intent. Aegis guard/runtime is the authority that decides whether the proposal is:

- `ready`
- `clarification_required`
- `approval_required`
- `blocked`

Approval is permission to attempt a specific action under a specific scope. Approval is not proof, not verification, and not success. Every approved action must still run through executor, verifier, evidence gate, journal, snapshot, and replay.

## Definitions

| State | Meaning | Executable? | Terminal? |
| --- | --- | --- | --- |
| `ready` | The intent/action is sufficiently specified, allowed by policy, and may be dispatched. | Yes | No |
| `clarification_required` | Aegis cannot safely resolve intent, target, parameters, or context. | No | Pending until answered or expired |
| `approval_required` | Aegis has a concrete proposed action, but policy requires explicit user approval before dispatch. | No, until approved | Pending until approved, denied, expired, or cancelled |
| `blocked` | Policy forbids the proposed action in the current state. | No | Yes, unless a future policy explicitly allows appeal/escalation |
| `unverified` | The action ran, but evidence did not prove the declared success condition. | Already ran | Yes |
| `failed` | The action did not complete, hard-failed, or verifier/evidence gate converted execution into failure. | Already attempted or failed before completion | Yes |
| `cancelled` | User/runtime cancelled the pending or running operation. | No further dispatch | Yes |

Clarifications:

- `approval_required` is not `failed`.
- `approval_required` is not `unverified`.
- `approval_required` is not executable until resolved as approved.
- `clarification_required` is not executable.
- `blocked` is not approvable unless a future explicit policy allows appeal.
- `unverified` means dispatch may have happened, but the evidence contract did not prove success.
- `failed` means dispatch failed, the tool hard-failed, or a required verifier/evidence gate failed.

## ApprovalRequest Schema Proposal

```yaml
ApprovalRequest:
  approval_id: string
  command_id: string
  trace_id: string
  span_id: string | null
  action_id: string | null
  source_intent:
    intent: string
    raw_input: string
    source: rule | deterministic | model | user | maintenance | system
    confidence: number | null
    metadata: object
  proposed_action:
    tool: string
    description: string
    action_kind: mutation | navigation | desktop_side_effect | browser_side_effect | maintenance | command | other
  normalized_params: object
  risk_level: none | low | medium | high | critical
  reason: string
  evidence_refs:
    - ref_id: string
      type: parser_plan | guard_report | target_resolution | maintenance_report | prior_evidence | runtime_snapshot
      summary: string
  expected_effect: string
  possible_side_effects:
    - string
  rollback_note: string
  expiration_policy:
    mode: never | ttl | command_lifetime | session_lifetime
    ttl_seconds: integer | null
    expire_on_context_change: boolean
  created_at: string
  expires_at: string | null
  status: pending | approved | denied | expired | cancelled
  required_confirmation_mode: ui | voice | typed_phrase | both
  approval_scope: single_action | command_step | full_plan
  replay_policy:
    replayable_decision: boolean
    replay_requires_same_context: boolean
    context_fingerprint: string | null
```

Rules:

- `approval_id` is unique and journal-addressable.
- `normalized_params` must contain the exact params being approved.
- Approval must not approve a vague natural-language phrase.
- Approval cannot silently widen from `single_action` to `full_plan`.
- If `expire_on_context_change` is true, changed target/window/file/runtime context invalidates pending approval.
- An approved action still needs execution evidence.

## ClarificationRequest Schema Proposal

```yaml
ClarificationRequest:
  clarification_id: string
  command_id: string
  trace_id: string
  original_user_text: string
  ambiguity_type: intent | target | app | file_path | browser_context | desktop_context | risk | parameter | unknown
  question: string
  options:
    - option_id: string
      label: string
      normalized_intent: object | null
      risk_level: none | low | medium | high | critical
      safe: boolean
  recommended_default:
    option_id: string | null
    reason: string
  blocked_until_answer: boolean
  created_at: string
  expires_at: string | null
```

Rules:

- A clarification response may produce a new normalized plan.
- Clarification must not mutate the system.
- Unresolved clarification must never fall through to older executable behavior.
- `recommended_default` is allowed only when it is non-mutating or clearly safer than alternatives.
- If the user answer changes risk or target, the new plan must re-enter guard/risk classification.

## BlockedAction Schema Proposal

```yaml
BlockedAction:
  blocked_id: string
  command_id: string
  trace_id: string
  source_intent:
    intent: string
    raw_input: string
    source: rule | deterministic | model | user | maintenance | system
    metadata: object
  reason: string
  policy_rule: string
  risk_level: none | low | medium | high | critical
  evidence_refs:
    - ref_id: string
      type: guard_report | parser_plan | runtime_snapshot | tool_registry | evidence_gate
      summary: string
  user_message: string
  retry_allowed: boolean
  safe_alternatives:
    - label: string
      command_hint: string | null
      reason: string
```

Rules:

- A blocked action is terminal for that proposed action.
- `retry_allowed=true` means the user may issue a different safer request, not that the same blocked action is approvable.
- `safe_alternatives` must not smuggle in the blocked mutation.

## Risk Classification

| Risk | Meaning | Examples |
| --- | --- | --- |
| `none` | No meaningful system side effect. | read-only status query, explain current state, summarize already loaded runtime state |
| `low` | Read-only or bounded observable side effect. | open app, search web, read file, focus window |
| `medium` | Bounded mutation or focused side effect with expected evidence. | type into focused app, write file inside allowed workspace, run safe test command, close own dev server |
| `high` | Broad mutation, hard-to-verify UI action, or sensitive local environment change. | delete files, kill arbitrary process, edit config, install package, change system settings, desktop click on unknown UI |
| `critical` | Credential, financial, destructive, elevated, or security-sensitive action. | credential handling, payment/financial action, destructive system command, registry mutation, security settings modification, mass deletion, unknown elevated action |

Risk is contextual. A low-risk tool can become high-risk if parameters, target, or runtime context are unsafe.

## Approval Policy Matrix

| Action category | Default decision | Approval required? | Evidence required? | Rollback required? |
| --- | --- | --- | --- | --- |
| `read_file` | `ready` if path is allowed | No | Yes, file-read evidence/hash when available | No |
| `write_file` | `approval_required` for mutation | Yes | Yes, before/after file evidence and content/hash check | Rollback note required; actual rollback optional unless implemented |
| `open_app` | `ready` or `approval_required` by risk/context | Sometimes | Yes, process/window evidence for verified success | No |
| `focus_app` | `ready` for known target | No by default | Yes, foreground/window evidence | No |
| `close_app` | `approval_required` for side effect | Yes unless policy marks own dev process safe | Yes, process termination evidence | Rollback note required if state loss possible |
| `type` | `approval_required` | Yes | Yes, focus stability/type evidence | Rollback note required if typed text may mutate state |
| `run_command` | `ready`, `approval_required`, or `blocked` by allowlist/risk | Depends on command | Yes, shell result evidence | Required for mutating command proposals; critical commands blocked |
| `git_action` | `ready` for status/read-only, blocked or approval for mutation | Depends on subcommand | Yes, git evidence | Required for mutating commands |
| maintenance recommendation | `ready` read-only proposal | No | Yes, diagnostic source refs | No |
| maintenance action | `approval_required` | Yes | Yes, action result evidence and maintenance rescan | Rollback note required |
| `browser_click` | Future: `ready` only after target resolution and low-risk browser evidence | Sometimes | Yes, browser target/context evidence | Required for risky page actions |
| `desktop_click` | Future: `approval_required` or `blocked` by default | Yes | Yes, foreground HWND/PID/window geometry evidence | Required |
| generic `click` | `clarification_required` or `blocked` | Not executable as generic action | Not applicable until split | Not applicable |
| model-proposed action | Guarded proposal only | Depends on resolved action and risk | Yes if executed | Depends on category |
| unknown tool | `blocked` | No | Tool registry/guard evidence | No |

Important click rules:

- Generic click must not be executable by default.
- Generic click should become `clarification_required` or `blocked` until `browser_click`/`desktop_click` split exists.
- `desktop_click` requires stronger policy than `browser_click`.
- Unresolved targets must never be approved as blind clicks.
- Explicit user coordinates may be considered only when policy allows them and window/coordinate evidence is available.

## Lifecycle

```text
User command
-> parser/decomposition
-> guard/risk classification
-> ready OR clarification_required OR approval_required OR blocked
-> if approved, executor runs
-> evidence verifier runs
-> journal records result
-> snapshot/action_timeline update
-> replay reconstructs same decision
```

For `approval_required`:

- Pending approval blocks execution.
- The approval request is journaled.
- Approval resolution is journaled.
- Denied approval is terminal and non-executed.
- Expired approval is terminal and non-executed.
- Cancelled approval is terminal and non-executed.
- Approved action still must produce evidence.
- Approval does not imply verified success.
- Replay must reconstruct both the pending decision and the resolution.

For `clarification_required`:

- Pending clarification blocks execution.
- The clarification request is journaled.
- The answer may create a new normalized plan.
- The new plan must re-enter guard/risk classification.
- Missing or expired answer must not fall back to older executable behavior.

For `blocked`:

- The blocked decision is journaled.
- No executor dispatch occurs.
- UI/action_timeline may show the policy block as non-executed.
- Replay must not turn a blocked action into approval-required or ready.

## Event and Journal Design Proposal

These event names are proposed only; not implemented in this sprint.

| Event | Required fields | Trace/causation links | Replay meaning |
| --- | --- | --- | --- |
| `APPROVAL_REQUESTED` | `approval_request`, `command_id`, `risk_level`, `reason`, `status=pending` | Trace points to command; causation points to guard or proposal event | Recreate pending approval state. |
| `APPROVAL_RESOLVED` | `approval_id`, `status=approved|denied|cancelled`, `resolved_by`, `resolved_at`, `resolution_reason` | Causation points to `APPROVAL_REQUESTED` | Mark approval as resolved; only approved may continue to execution. |
| `APPROVAL_EXPIRED` | `approval_id`, `expired_at`, `expiration_policy` | Causation points to `APPROVAL_REQUESTED` | Terminal non-executed result. |
| `CLARIFICATION_REQUESTED` | `clarification_request`, `command_id`, `ambiguity_type`, `question` | Trace points to command; causation points to parser/decomposition/guard event | Recreate pending clarification state. |
| `CLARIFICATION_RESOLVED` | `clarification_id`, `answer`, `selected_option_id`, `new_plan_ref` | Causation points to `CLARIFICATION_REQUESTED` | Resume planning with a new normalized plan. |
| `ACTION_BLOCKED_BY_POLICY` | `blocked_action`, `policy_rule`, `risk_level` | Causation points to guard event | Terminal non-executed blocked action. |
| `ACTION_APPROVAL_REQUIRED` | `approval_id`, `action_id`, `proposed_action`, `risk_level` | Causation points to guard event | Action cannot dispatch until approval is resolved. |
| `ACTION_APPROVED_FOR_EXECUTION` | `approval_id`, `action_id`, `normalized_params`, `approval_scope` | Causation points to `APPROVAL_RESOLVED` | Executor may dispatch exactly the approved action. |
| `ACTION_DENIED_BY_USER` | `approval_id`, `action_id`, `reason` | Causation points to `APPROVAL_RESOLVED` | Terminal non-executed action. |

Event rules:

- Every proposed event must include `trace_id`.
- Step/action events should include `span_id` and `action_id` when available.
- Resolution events must include causation links to the request event.
- Snapshot projection must be derived from journaled events, not frontend-local state.
- Replay must not invent approval, clarification, or evidence that was not journaled.

## UI and Voice Behavior Guidance

UI behavior:

- Show a pending approval card for `approval_required`.
- Show exact proposed action and normalized params.
- Show risk level and reason.
- Show evidence refs and runtime context used for the decision.
- Show possible side effects.
- Show rollback note.
- Show approval scope: single action, command step, or full plan.
- Provide approve/deny controls only for approvable requests.
- Show blocked actions without approve controls.
- Show clarification questions separately from approvals.

Voice behavior:

- Voice may ask for approval.
- Voice is UI, not authority.
- Voice approval is allowed only for low/medium risk if policy allows it.
- High risk requires UI or typed phrase.
- Critical risk is blocked by default.
- Voice responses must be journaled like any other approval/clarification resolution.
- Voice must read back the exact action being approved for any side-effecting action.

## Generic Click Quarantine Policy

Based on the generic click quarantine audit:

- Generic `click` is deprecated/quarantined.
- Generic `click` must not be extended.
- Older generic `click` may remain only for compatibility until split migration.
- New click work must use `browser_click` or `desktop_click`.
- If target is unresolved, return `clarification_required`.
- If target is high risk, return `approval_required` or `blocked`.
- If action is coordinate-only, require explicit user coordinates and window/context evidence.
- Coordinate inside a window is geometry verification, not semantic verification.
- Approval cannot convert an unresolved generic click into a blind coordinate click.
- `browser_click` and `desktop_click` must have separate evidence contracts.

Migration rule:

```text
generic click phrase
-> target resolution
-> browser_click OR desktop_click OR clarification_required OR approval_required OR blocked
```

No future implementation should add more behavior to the generic `click` tool path.

## Future Implementation Slices

1. Approval/clarification/blocked protocol types.
2. Guard risk classifier tests.
3. Non-executable approval/clarification runtime snapshot projection.
4. UI pending approval panel.
5. Approval resolve endpoint.
6. Generic click block/clarification gate.
7. Maintenance action proposal approval.
8. `browser_click` approval/evidence.
9. `desktop_click` approval/evidence.

Recommended constraints for these slices:

- Each slice should include focused tests before behavior changes.
- Runtime FSM should not gain new states unless separately approved.
- Command lifecycle and action timeline can represent approval/clarification as command/action projections without making the frontend authoritative.
- Compatibility generic click should be blocked or clarified before any split click implementation is enabled.

## Out of Scope

- No production code.
- No backend endpoint implementation.
- No frontend implementation.
- No executor changes.
- No orchestrator changes.
- No parser expansion.
- No click implementation.
- No `browser_click` implementation.
- No `desktop_click` implementation.
- No target resolution implementation.
- No model adapter.
- No LLM planner.
- No maintenance mutation.
- No voice implementation.
- No runtime state addition.
- No schema migration.

## Remaining Design Risks

- Existing production code still has older generic `click` compatibility paths.
- Existing command lifecycle has approval concepts, but not the first-class request schemas proposed here.
- Existing event names differ from the proposal; a future protocol slice must decide migration versus additive compatibility.
- Voice approval needs stricter anti-spoofing and confirmation rules before implementation.
- Target resolution is a prerequisite for safe click expansion.
