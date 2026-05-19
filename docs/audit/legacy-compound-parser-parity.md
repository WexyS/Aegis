# Legacy Compound Parser Parity Audit

**Date:** 2026-05-19

**Goal:** Compare legacy compound parsing with feature-flagged deterministic decomposition before removing, bypassing, or default-enabling any parser path.

**Scope:** Audit/report only. No legacy parser cleanup, no executor/orchestrator/frontend changes, no click implementation, no target resolution, and no LLM planner work.

---

## Method

Each case was evaluated through `IntentParser.parse()` with:

- legacy behavior: `ENABLE_DETERMINISTIC_DECOMPOSITION=false`
- deterministic behavior: `ENABLE_DETERMINISTIC_DECOMPOSITION=true`

The comparison focuses on parser output shape, params, safety behavior, and decomposition metadata. Executor behavior is out of scope.

---

## Parity Matrix

| Input | Legacy result | Deterministic result | Same / Different | Expected future behavior | Risk if legacy removed |
| --- | --- | --- | --- | --- | --- |
| `brave açıp python nedir ara` | `open_app(brave)` + `search_web(query=python nedir, browser=brave)` via `compound_app_search` | `open_app(brave)` + `search_web(query=python nedir, browser=brave)` with deterministic metadata | Same behavior, different metadata | Deterministic path should replace legacy for this case | Low |
| `chrome aç ve python nedir ara` | `open_app(chrome)` + `search_web(query=ve python nedir, browser=chrome)` | `open_app(chrome)` + `search_web(query=python nedir, browser=chrome)` | Different | Deterministic path is safer and cleaner; legacy preserves connector in query | Low; removal fixes a legacy query bug |
| `notepad açıp merhaba yaz` | `open_app(notepad)` only | `open_app(notepad)` + `type(text=merhaba, _require_focus=notepad)` | Different | Deterministic path is correct; legacy drops the type step | Low; removal improves behavior |
| `not defterini aç ve merhaba yaz` | `open_app(notepad)` + `type(text=merhaba)` | `open_app(notepad)` + `type(text=merhaba, _require_focus=notepad)` | Different | Deterministic path should be preferred because focus dependency is explicit | Low |
| `open brave and search python` | `open_app(brave)` + `search_web(query=python)` without browser context | `open_app(brave)` + `search_web(query=python, browser=brave)` | Different | Deterministic path should be preferred because browser context is explicit | Low |
| `open notepad and type hello` | `open_app(notepad)` + `type(text=hello)` | `open_app(notepad)` + `type(text=hello, _require_focus=notepad)` | Different | Deterministic path should be preferred because focus dependency is explicit | Low |
| `unknownapp aç ve python ara` | `open_app(unknownapp)` + `search_web(query=python)` | non-executable `unknown` with `clarification_required` | Intentionally different | Deterministic behavior is safer; do not preserve unknown-app execution | Medium if legacy remains enabled for this pattern |
| `brave aç ve ilk sonuca tıkla` | `open_app(brave)` + `unknown` | non-executable `unknown` with `clarification_required` | Intentionally different | Deterministic behavior is safer; no blind click or partial open should execute | Medium if legacy remains enabled for click-like compounds |
| `click that button` | `unknown` | non-executable `unknown` with `clarification_required` | Different metadata only | Deterministic clarification metadata is preferred; no executable click | Low |
| `merhaba` | `general_chat` | `general_chat` | Same | Keep legacy fallback when decomposition returns `None` | None |

---

## Legacy Coverage Already Matched

The deterministic path already covers the core safe legacy app-search cases:

- browser app + search query in Turkish
- browser app + search query in English
- app name separated from query
- browser context carried into `search_web`

For `brave açıp python nedir ara`, deterministic output is behaviorally equivalent to legacy and adds structured metadata.

---

## Legacy Behaviors Not Covered Exactly

These differences are intentional and should not block future deprecation:

- Legacy may omit `_require_focus` for type steps.
- Legacy may omit `browser` for English search compounds.
- Legacy may parse incomplete open+type commands as only `open_app`.
- Legacy may include connector text such as `ve` in a search query.
- Legacy may execute `open_app(unknownapp)` instead of asking for clarification.

The deterministic path is stricter because evidence gates can only verify the action they are given. A wrong or partial parse can still lead to a "verified" wrong action later.

---

## Unsafe Legacy Behaviors Not To Preserve

Do not preserve these during cleanup:

- `unknownapp aç ve python ara` becoming executable `open_app(unknownapp)`.
- `brave aç ve ilk sonuca tıkla` partially executing `open_app(brave)` when click target resolution is unavailable.
- `chrome aç ve python nedir ara` leaking `ve` into the query.
- `notepad açıp merhaba yaz` dropping the `type` step.

These are exactly the kinds of parser mistakes deterministic decomposition is meant to prevent.

---

## Behaviors Needing Tests Before Cleanup

Before removing `_parse_compound_app_search()`, keep or add parser-level tests for:

- `brave açıp python nedir ara`
- `chrome aç ve python nedir ara`
- `open brave and search python`
- `notepad açıp merhaba yaz`
- `not defterini aç ve merhaba yaz`
- `unknownapp aç ve python ara`
- `brave aç ve ilk sonuca tıkla`

Most of these are already protected by deterministic decomposition smoke tests. A cleanup sprint should add any missing parity tests before deleting legacy code.

---

## Recommendation

**Keep legacy parser for now. Deprecate later. Cleanup later.**

Do not remove `_parse_compound_app_search()` in the current state. The deterministic path is safer for the audited cases, but it is still feature-flagged and not yet default-on. The next safe progression is:

1. Add a small cleanup-readiness test set for any missing parity cases.
2. Run a feature-flag-on parser smoke across common user phrases.
3. Consider default-on only after a short stabilization window.
4. Remove `_parse_compound_app_search()` only after deterministic decomposition is default-on and parity tests stay green.

No cleanup should happen before that.
