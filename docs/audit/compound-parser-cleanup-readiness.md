# Compatibility Compound Parser Cleanup Readiness

**Date:** 2026-05-21

**Goal:** Decide whether `_parse_compound_app_search()` can be safely deprecated or removed now that deterministic decomposition is default-on.

**Scope:** Readiness/audit plus focused parser tests only. No compatibility parser removal, no executor/orchestrator/frontend changes, no click implementation, no target resolution, no LLM planner, and no broad cleanup.

---

## Decision

**cleanup_safe_now:** no

**Recommended state:** deprecate conceptually, but keep the compatibility compound parser in code for now.

Default-on deterministic decomposition covers the high-risk audited compound cases, but `_parse_compound_app_search()` still preserves useful behavior for broader search tails that deterministic decomposition intentionally does not support yet. Removing it now would regress those phrases into single `search_web` intents with polluted query text or otherwise lower-quality fallback behavior.

---

## Older References Found

Runtime references:

- `src/aegis/intent/parser.py`: `IntentParser.parse()` calls `_parse_compound_app_search()` after deterministic decomposition returns `None`.
- `src/aegis/intent/parser.py`: `_parse_compound_app_search()` emits metadata `decomposition="compound_app_search"` with `segment="open_app"` or `segment="search_web"`.

Test/doc references:

- `tests/test_intent/test_parser.py`: older flag-off behavior and an older compound browser search expectation.
- `tests/test_intent/test_parser_deterministic_decomposition_smoke.py`: default-on, env override, fallback, and compatibility-tail protection tests.
- `docs/audit/compound-parser-parity.md`
- `docs/audit/deterministic-decomposition-default-on-readiness.md`
- `docs/design/parser-wiring.md`

No executor, orchestrator, or frontend references were found.

---

## Behavior Classification

| Input | Current default-on behavior | Classification | Removal impact |
| --- | --- | --- | --- |
| `google aç ve python ara` | `open_url(google)` + `search_web(query=python)` via normal older split rules | safely falls back to compatibility parser | Not dependent on `_parse_compound_app_search()` |
| `youtube aç ve müzik ara` | `open_url(youtube)` + `search_web(query=müzik)` via normal older split rules | safely falls back to compatibility parser | Not dependent on `_parse_compound_app_search()` |
| `brave açıp python nedir ara` | deterministic `open_app(brave)` + `search_web(query=python nedir, browser=brave)` | covered by deterministic decomposition | Safe for compound parser removal |
| `chrome aç ve python nedir ara` | deterministic `open_app(chrome)` + `search_web(query=python nedir, browser=chrome)` | covered by deterministic decomposition | Safe for compound parser removal |
| `open brave and search python` | deterministic `open_app(brave)` + `search_web(query=python, browser=brave)` | covered by deterministic decomposition | Safe for compound parser removal |
| `notepad açıp merhaba yaz` | deterministic `open_app(notepad)` + `type(text=merhaba, _require_focus=notepad)` | covered by deterministic decomposition | Safe for compound parser removal |
| `not defterini aç ve merhaba yaz` | deterministic `open_app(notepad)` + `type(text=merhaba, _require_focus=notepad)` | covered by deterministic decomposition | Safe for compound parser removal |
| `unknownapp aç ve python ara` | deterministic non-executable `unknown`, `clarification_required` | unsafe older behavior not preserved | Must not fall back to older executable behavior |
| `brave aç ve ilk sonuca tıkla` | deterministic non-executable `unknown`, `clarification_required` | unsafe partial execution blocked | Must not fall back to partial `open_app` |
| `click that button` | deterministic non-executable `unknown`, `clarification_required` | unresolved click blocked | No dependency on compound parser |

---

## Broader Older Tail Review

| Tail / shape | Example | Current behavior | Cleanup risk |
| --- | --- | --- | --- |
| `ara` | `brave açıp python nedir ara` | deterministic ready plan | Low |
| `araması yap` | `brave açıp python nedir araması yap` | `_parse_compound_app_search()` -> `open_app(brave)` + `search_web(query=python nedir, browser=brave)` | High: without compound parser it becomes only `search_web(query=brave açıp python nedir)` |
| `bul` | `brave açıp python bul` | `_parse_compound_app_search()` -> `open_app(brave)` + `search_web(query=python, browser=brave)` | High: without compound parser it becomes only `search_web(query=brave açıp python)` |
| `googlela` | `brave açıp python googlela` | `_parse_compound_app_search()` -> `open_app(brave)` + `search_web(query=python, browser=brave)` | High: without compound parser it becomes only `search_web(query=brave açıp python)` |
| English `search` | `open brave and search python` | deterministic ready plan | Low |
| English `find` | `open brave and find python` | normal split rules -> `open_app(brave)` + `search_web(query=python)` | Medium: works without compound parser but does not preserve browser context |
| known site names | `google aç ve python ara`, `youtube aç ve müzik ara` | normal split rules -> `open_url(site)` + `search_web(query=...)` | Low for compound cleanup, but still relies on older split parser |

These tails should not be implemented in this sprint. They are blockers for removal only.

---

## Deterministic Coverage Confirmed

Default-on deterministic decomposition covers:

- Turkish open + search for supported `ara` forms.
- English open + search for supported `search` forms.
- Turkish/English open + type.
- Unknown app clarification for deterministic compound app commands.
- Unresolved click blocking.
- Browser context preservation for deterministic `search_web`.
- `_require_focus` preservation for deterministic `type`.
- Clean query extraction for audited `ara` cases.

---

## Unsafe Older Behaviors Not To Preserve

These should remain blocked or improved by deterministic decomposition:

- `open_app(unknownapp)`.
- Partial `open_app` for unresolved click commands.
- Connector leaking into query, such as `ve python nedir`.
- Dropping the `type` step from open + type commands.
- Dropping `_require_focus` from type steps.
- Dropping `browser` context from deterministic open + search commands.

---

## Tests Added In This Sprint

Focused parser tests were added to `tests/test_intent/test_parser_deterministic_decomposition_smoke.py`:

- `youtube aç ve müzik ara` now protects known-site fallback alongside `google aç ve python ara`.
- `brave açıp python nedir araması yap`, `brave açıp python bul`, and `brave açıp python googlela` now explicitly assert `compound_app_search` metadata and browser-preserving output.

These tests intentionally make older cleanup fail until equivalent deterministic support exists or the behavior is explicitly retired.

---

## Blockers

- Compatibility-only compound search tails still exist: `araması yap`, `bul`, `googlela`.
- English `find` works through normal split rules, but still lacks deterministic browser context.
- App alias/encoding cleanup remains separate and should not be mixed into parser removal.
- Runtime/replay E2E readiness remains separate.
- Removing `_parse_compound_app_search()` would reduce behavior quality even though the high-risk unsafe cases are now deterministic-safe.

---

## Tests Needed Before Removal

Before any removal sprint:

- Add deterministic coverage for `araması yap`, `bul`, and `googlela`, or explicitly decide to drop those forms.
- Add deterministic or intentionally-fallback coverage for English `find` with a browser context decision.
- Keep the existing unknown app and unresolved click non-executable tests green.
- Keep known-site fallback tests green.
- Run the full validation suite after temporarily removing or bypassing `_parse_compound_app_search()`.

---

## Recommended Next Sprint

Recommended next sprint: **App Registry Alias Encoding Fix**.

Reason: cleanup is not safe now, and alias/encoding correctness affects whether deterministic decomposition can safely own broader app/search patterns later.

After that, a narrow **Older Tail Deterministic Coverage** sprint can decide whether to support or retire `araması yap`, `bul`, `googlela`, and English `find` before any removal attempt.

---

## Validation

Validation for this sprint was run after the report and focused tests were added:

- `.\.venv\Scripts\python.exe -m pytest tests\test_intent -q` -> `106 passed in 0.75s`
- `.\.venv\Scripts\python.exe -m pytest -q` -> `340 passed, 4 deselected in 26.83s`
- `cd frontend && npm.cmd run build` -> Next.js production build completed successfully
- `git diff --check` -> exit 0; LF-to-CRLF warnings only for existing touched files
