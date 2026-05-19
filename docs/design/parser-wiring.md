# Parser Wiring Design v1

**Goal:** Define how `decompose_command(text)` should enter the existing parser and orchestrator pipeline without changing runtime behavior in this sprint.

**Decision:** Wire deterministic decomposition behind a feature flag, before the legacy rule parser, but only for high-confidence compound plans that pass normalized-plan validation and adapter validation.

This document is design-only. It does not change parser, executor, orchestrator, frontend, LLM routing, click routing, target resolution, tools, runtime states, replay, or timeline behavior.

---

## Current Boundaries

Existing decomposition layer:

- `NormalizedPlan`
- `PrimitiveStep`
- `validate_normalized_plan()`
- `decompose_open_type()`
- `decompose_open_search()`
- `decompose_command()`

Existing live runtime parser output:

- `IntentParser.parse(text) -> list[IntentResult]`
- `Planner.plan(list[IntentResult]) -> list[IntentResult]`
- Orchestrator executes the planned `IntentResult` list.

The decomposition layer must not execute anything. It only produces a normalized plan that can be adapted into existing parser output.

---

## Recommended Integration Point

Run `decompose_command(text)` near the start of `IntentParser.parse()`, after byte-artifact cleanup and before:

1. `normalize_text()`
2. legacy `_parse_compound_app_search()`
3. connector splitting
4. `parse_single()`
5. AI fallback
6. final safety overrides

Guard it with a setting:

```text
ENABLE_DETERMINISTIC_DECOMPOSITION=false
```

Initial rollout should default to disabled. When enabled, it should only intercept commands when `decompose_command(text)` returns a non-`None` plan.

### Why Before The Existing Parser

Deterministic decomposition exists to prevent malformed compound commands from being split or guessed incorrectly by the older parser path. Running it first lets a high-confidence compound pattern preserve:

- action order
- app/query separation
- `_require_focus`
- browser context
- ambiguity status

### Why Behind A Feature Flag

The current parser already supports many single-intent commands and has legacy compound handling. A flag allows staged rollout without breaking:

- `notepad ac`
- `not defterini ac`
- `hesap makinesi ac`
- existing URL commands
- existing file commands
- existing web search commands
- existing tests that depend on legacy parser behavior

### Legacy Compound Parser

`IntentParser._parse_compound_app_search()` should remain until deterministic decomposition has equivalent parser-level tests. After parity is proven, it can be removed in a separate cleanup sprint.

---

## Conversion Contract

Add a small adapter in the implementation sprint, for example:

```python
normalized_plan_to_intents(plan: NormalizedPlan, *, raw_text: str) -> list[IntentResult]
```

The adapter should be the only bridge from `NormalizedPlan` to live parser output.

### PrimitiveStep To IntentResult

For each `PrimitiveStep`:

| PrimitiveStep field | IntentResult field |
| --- | --- |
| `intent` | `intent` |
| `params` | `params` |
| `risk` | `risk` as `RiskLevel` |
| `source_span` | `metadata["source_span"]` |
| plan source text | `raw_input` |
| rule provenance | `source=IntentSource.RULE` |
| adapter confidence | `confidence=1.0` for validated deterministic plans |

### Metadata

Each adapted `IntentResult.metadata` should include:

```python
{
    "decomposition": "deterministic",
    "plan_kind": plan.plan_kind,
    "plan_status": plan.status,
    "plan_risk": plan.risk,
    "step_index": index,
    "step_count": len(plan.steps),
    "source_span": step.source_span,
    "guard_notes": plan.guard_notes,
    "ambiguities": plan.ambiguities,
}
```

If a future `plan_id` is added, it should be copied into every step metadata. Do not add a new protocol field for this during the wiring sprint.

### Risk Mapping

Map string risks to existing `RiskLevel`:

| Normalized risk | Runtime risk |
| --- | --- |
| `none` | `RiskLevel.NONE` |
| `low` | `RiskLevel.LOW` |
| `medium` | `RiskLevel.MEDIUM` |
| `high` | `RiskLevel.HIGH` |
| `critical` | `RiskLevel.CRITICAL` |

If risk mapping fails, return a non-executable parser result or fall back according to the status handling matrix below. Never silently downgrade risk.

### Planner Compatibility

The adapter should produce a plain `list[IntentResult]`, not a new chain intent.

Reason:

- `Planner.plan()` already accepts `list[IntentResult]`.
- Existing command lifecycle tests use `list[IntentResult]`.
- Executor already operates on individual `IntentResult` items.
- A chain intent would create a new runtime contract and new failure modes.

---

## Status Handling Matrix

| NormalizedPlan result | Parser behavior | Execution behavior |
| --- | --- | --- |
| `None` | Fall back to existing parser path | Existing behavior unchanged |
| `ready` and valid | Adapt to `list[IntentResult]` | Existing guard/planner/executor pipeline handles it |
| `clarification_required` | Return non-executable clarification result or fallback only if feature flag policy says so | Must not execute |
| `approval_required` | Return non-executable approval placeholder or route to existing approval proposal layer when available | Must not execute directly |
| `blocked` | Return non-executable blocked/unknown result with guard metadata | Must not execute |
| validation fails | Return blocked result with validation errors in metadata | Must not execute |

### Clarification Result

Until a first-class clarification intent exists, use the safest existing non-executable representation:

```python
IntentResult(
    intent="unknown",
    confidence=0.0,
    params={},
    risk=RiskLevel.NONE,
    source=IntentSource.RULE,
    raw_input=text,
    metadata={
        "decomposition": "deterministic",
        "plan_status": "clarification_required",
        "ambiguities": plan.ambiguities,
        "guard_notes": plan.guard_notes,
    },
)
```

Do not encode clarification as `general_chat` if it could be mistaken for a successful answer path.

### Approval Required

Do not route directly to execution. Until action proposals are the parser-level contract, use a non-executable result with:

- `intent="unknown"`
- `risk=RiskLevel.CRITICAL` if the proposed action is destructive
- metadata containing `plan_status="approval_required"`

The implementation sprint should verify how the existing approval manager expects pending proposals before routing here.

### Blocked

Blocked means the deterministic guard rejected the plan. It must not fall through to legacy parser if falling through could execute a known-dangerous command.

Safe fallback rule:

- `None` can fall back.
- `ready` can adapt.
- `clarification_required`, `approval_required`, and `blocked` should not fall back by default, because they are explicit decomposition decisions.

---

## Backward Compatibility

Feature flag off:

- `IntentParser.parse()` behavior is unchanged.
- Existing tests should pass without any expected-output changes.

Feature flag on:

- Only commands that match `decompose_command(text)` are intercepted.
- Single-intent commands still use the existing parser.
- Unknown text still uses the existing parser and AI fallback policy.

Commands that must remain compatible:

- `notepad ac`
- `not defterini ac`
- `hesap makinesi ac`
- `google ac`
- `ac https://example.com`
- `write smoke-live to scratch/aegis_write_smoke.txt`
- `read README.md`
- `git status`

Compound commands expected to improve behind the flag:

- `notepad acip merhaba yaz`
- `not defterini ac ve merhaba yaz`
- `brave acip python nedir ara`
- `open brave and search python`

---

## Test Plan Before Implementation

### Feature Flag Off

- `ENABLE_DETERMINISTIC_DECOMPOSITION=false`
- `notepad ac sonra merhaba yaz` keeps current parser behavior.
- `brave acip python nedir ara` keeps current parser behavior.
- Existing parser test suite passes unchanged.

### Feature Flag On: Ready Plans

- `notepad acip merhaba yaz` returns two `IntentResult` objects in order:
  1. `open_app`
  2. `type`
- Type step preserves:
  - `params["text"]`
  - `params["_require_focus"]`
  - metadata source span
- `brave acip python nedir ara` returns two `IntentResult` objects in order:
  1. `open_app`
  2. `search_web`
- Search step preserves:
  - `params["query"]`
  - `params["browser"]`
  - metadata source span
- Returned intents have `source=IntentSource.RULE`.
- Returned risks match primitive risks or a safe recomputation.

### Feature Flag On: Fallback

- Unrelated text returns the existing parser result.
- Existing single open-app commands still work.
- Existing open-url commands still work.
- Existing file commands still work.

### Feature Flag On: Non-Executable Status

- Unknown app in open+type returns a non-executable result.
- Unknown app in open+search returns a non-executable result.
- Clarification does not reach planner/executor as an executable app/search/type action.
- Blocked plans do not fall back to legacy parsing.
- Approval-required plans do not execute directly.

### Guard And Metadata

- Unknown app does not become search query accidentally.
- `_require_focus` is not dropped.
- Browser context is not dropped.
- Plan order is preserved.
- Metadata includes `decomposition`, `plan_status`, `step_index`, and `source_span`.
- Invalid normalized plan becomes blocked, not executable ready.

---

## Rollout Strategy

1. Add feature flag with default off.
2. Add adapter tests without changing default parser behavior.
3. Implement adapter function.
4. Wire `decompose_command(text)` behind the flag before legacy parser logic.
5. Run parser tests with flag off.
6. Run new parser tests with flag on.
7. Run full backend tests.
8. Keep `_parse_compound_app_search()` for one release window.
9. Remove legacy compound parser only after deterministic decomposition parity is proven.

---

## Failure Modes And Mitigations

| Failure mode | Mitigation |
| --- | --- |
| Duplicate parsing | Deterministic branch returns immediately only when feature flag is on and plan is explicit |
| Legacy parser also parses same command | Do not continue to legacy parser after a non-`None` deterministic plan |
| Plan order lost | Adapter iterates `plan.steps` in list order and writes `step_index` |
| `_require_focus` dropped | Adapter copies params exactly before planner enrichment |
| Browser context dropped | Adapter copies `browser` param exactly |
| Risk downgraded accidentally | Explicit risk mapping; invalid risk blocks |
| Clarification treated as executable | Non-ready statuses return non-executable result |
| Blocked plan falls through | Explicit blocked status must not fall back |
| Chain intent mismatch | Use `list[IntentResult]`, not a new chain intent |
| AI fallback bypasses guard | AI fallback only runs after `None`; explicit non-ready plans stop fallback |
| Legacy force override mutates adapted result | Apply deterministic branch before final override and return immediately |

---

## Out Of Scope

Do not implement in this sprint:

- actual parser wiring
- adapter code
- feature flag code
- executor changes
- orchestrator changes
- frontend changes
- approval UI
- LLM planner
- click routing
- target resolution
- new runtime states
- protocol schema changes
- replay or timeline changes
