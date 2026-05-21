# Deterministic Decomposition Default-On Readiness Review

**Date:** 2026-05-21

**Goal:** Decide whether feature-flagged deterministic decomposition is ready for a later controlled default-on sprint.

**Scope:** Audit/report only. No production behavior change, no default flip, no legacy parser cleanup, no executor/orchestrator/frontend changes, no click implementation, no target resolution, no LLM planner, and no Ultron bridge.

---

## Decision

**ready_for_default_on:** yes, for a controlled default-on sprint only.

This is not approval to remove `_parse_compound_app_search()` and not approval to expand capabilities. The safe next change is to flip only `ENABLE_DETERMINISTIC_DECOMPOSITION` default behavior while keeping the legacy parser as fallback for unrelated text and still returning non-executable deterministic `unknown` results for explicit non-ready plans.

---

## Evidence Reviewed

- `src/aegis/intent/decomposition.py`
- `src/aegis/intent/parser.py`
- `src/aegis/core/config.py`
- `tests/test_intent/test_decomposition.py`
- `tests/test_intent/test_decomposition_adapter.py`
- `tests/test_intent/test_parser.py`
- `tests/test_intent/test_parser_deterministic_decomposition_smoke.py`
- `docs/audit/legacy-compound-parser-parity.md`

---

## Parser Parity

Deterministic decomposition now covers these ready compound shapes:

| Shape | Examples | Deterministic output |
| --- | --- | --- |
| Turkish open + type | `notepad açıp merhaba yaz`, `not defterini aç ve merhaba yaz` | `open_app` then `type` |
| English open + type | `open notepad and type hello` | `open_app` then `type` |
| Turkish open + search | `brave açıp python nedir ara`, `chrome aç ve python nedir ara`, `brave aç sonra yapay zeka ara` | `open_app` then `search_web` |
| English open + search | `open brave and search python`, `open chrome then search python tutorial` | `open_app` then `search_web` |

Intentionally not preserved from legacy:

- Unknown app compound commands becoming executable `open_app(unknownapp)`.
- Open + click-like compounds partially executing an `open_app` step while click target resolution is unavailable.
- Query leakage such as `ve python nedir`.
- Missing `_require_focus` on type steps.
- Missing `browser` context on English search compounds.

Legacy fallback still matters for:

- unrelated text where `decompose_command()` returns `None`, such as `merhaba`;
- existing single-intent commands and broader rule-based parser coverage;
- legacy compound app-search phrases not yet modeled by deterministic decomposition, such as `araması yap`, `bul`, `find`, `googlela`, `launch`, and `start` forms.

Behavior differs from `_parse_compound_app_search()` by design. The deterministic path is narrower and stricter: it either emits a validated normalized plan or returns a non-executable clarification/block result. The legacy compound parser is broader but can preserve unsafe or low-quality parses.

---

## Safety Review

Confirmed:

- Unknown app does not execute under flag ON. It returns one non-executable `unknown` with `plan_status="clarification_required"`.
- Unresolved click does not execute under flag ON.
- Unresolved click does not partially execute `open_app`; `brave aç ve ilk sonuca tıkla` returns one non-executable `unknown`.
- Generic `click that button` does not produce `click`, `browser_click`, or `desktop_click`.
- Non-ready deterministic plans do not fall through to the legacy parser because `IntentParser.parse()` returns the deterministic non-ready result when `decompose_command()` returns a plan.
- Destructive/system-sensitive behavior is not expanded by deterministic decomposition. The normalized plan allowlist does not include file deletion, shell execution, raw click, `browser_click`, or `desktop_click`. Existing legacy risk handling remains separate and unchanged.

Not confirmed in this sprint:

- Runtime/executor enforcement for every destructive/system-sensitive command. That is outside parser default-on scope and remains covered by the runtime/evidence/approval workstreams.

---

## Metadata Review

Ready deterministic plans preserve:

- `decomposition="deterministic"`
- `plan_status`
- `step_index`
- `step_count`
- `source_span`
- `plan_kind`
- `plan_risk`
- empty `ambiguities` and `guard_notes` when ready

Action-specific context is also preserved:

- `type` includes `_require_focus`.
- `search_web` includes `browser`.

Non-ready deterministic plans preserve:

- `decomposition="deterministic"`
- `plan_status` as `clarification_required` or `blocked`
- `ambiguities` or `guard_notes` explaining why no executable intent was emitted

---

## Feature Flag Review

Current state:

- `FeatureFlags.deterministic_decomposition` defaults to `False`.
- `EnvOverrides.enable_deterministic_decomposition` defaults to `False`.
- `ENABLE_DETERMINISTIC_DECOMPOSITION` overrides the setting through `load_settings(force_reload=True)`.
- Parser tests toggle the environment flag both ON and OFF.

Default-off behavior remains unchanged in the readiness tests for:

- `notepad aç`
- `not defterini aç`
- `hesap makinesi aç`

Flag-on behavior is tested for:

- safe ready compound decomposition;
- unknown app clarification;
- unresolved click clarification;
- unrelated text falling back to existing parser behavior.

Default-on would not bypass legacy fallback for unrelated text because `decompose_command()` returns `None` for unsupported/unrelated input and the parser continues through the existing legacy path. Non-ready deterministic decisions are different: they intentionally return immediately and do not fall through.

---

## Regression Risk

Possible regressions if made default-on:

- Some broad legacy app-search forms may still rely on `_parse_compound_app_search()` because deterministic decomposition is intentionally narrower.
- App alias encoding/normalization issues could cause valid phrases to become `clarification_required` instead of executable plans.
- Users relying on legacy partial execution may see safer non-executable clarification results instead.
- If a phrase matches a deterministic non-ready pattern too aggressively, it can block legacy fallback. Current audited cases are intentional, but broader language coverage should stay conservative.

Commands that should still use legacy parser or fallback:

- single-intent app open/focus/close commands;
- URL/site open commands;
- file commands;
- git commands;
- shell/run commands;
- general chat/unrelated text;
- legacy search phrases not yet represented by deterministic decomposition.

Test coverage gaps:

- More Turkish suffix and alias variants before legacy cleanup.
- More legacy `_parse_compound_app_search()` tails: `araması yap`, `arama yap`, `bul`, `find`, `googlela`.
- Explicit flag-ON smoke for destructive/system-sensitive parser inputs to prove the default-on gate does not make them more executable than today.
- App alias encoding fix and tests remain a separate sprint.

Turkish/English coverage is enough for controlled default-on of the audited high-risk compound patterns, but not enough for legacy parser removal.

---

## Current Blocker Review

- `_parse_compound_app_search()` still exists and should stay through default-on.
- `AGENTS.md` is untracked. Treat it as a separate docs/instruction sprint decision, not part of this parser readiness sprint.
- The app registry alias encoding issue remains a separate sprint.
- Runtime/replay E2E readiness remains a separate sprint.
- No click, target resolution, LLM planner, frontend, executor, or orchestrator work should be bundled into default-on.

---

## Required Tests Before Default-On

No new blocking parser tests were discovered for the audited default-on scope. The existing readiness tests cover the current mandatory cases.

Recommended extra tests before or during controlled default-on:

- flag-ON destructive/system-sensitive parser smoke showing behavior remains unchanged or non-executable;
- flag-ON coverage for additional legacy app-search tails if those are considered part of default-on acceptance;
- explicit config default assertion that deterministic decomposition remains false until the controlled default-on sprint changes it.

---

## Cleanup Safety

**Can default-on be done while keeping `_parse_compound_app_search()`?** Yes. That is the recommended path.

**Is cleanup safe now?** No. Legacy cleanup must wait until default-on has landed, remained green, and broader legacy fallback coverage has been reviewed.

---

## Recommendation

Recommended next sprint: **A) Controlled Default-On**.

Constraints for that sprint:

- flip only the deterministic decomposition default;
- keep `_parse_compound_app_search()`;
- keep non-ready deterministic no-fallback behavior;
- keep unrelated text legacy fallback behavior;
- add the smallest necessary config/default assertion tests;
- run the same validation suite.

Cleanup should remain a later sprint.

---

## Validation

Validation for this review was run after this audit file was added:

- `.\.venv\Scripts\python.exe -m pytest tests\test_intent -q` -> `102 passed in 0.54s`
- `.\.venv\Scripts\python.exe -m pytest -q` -> `336 passed, 4 deselected in 25.58s`
- `cd frontend && npm.cmd run build` -> Next.js production build completed successfully
- `git diff --check` -> exit 0; warning only: `tests/test_intent/test_parser_deterministic_decomposition_smoke.py` LF will be replaced by CRLF when Git touches it
