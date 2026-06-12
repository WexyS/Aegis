# Generic Click Path Quarantine Audit

**Date:** 2026-05-21

**Sprint:** Generic Click Path Quarantine Audit

**Scope:** Audit/report plus focused parser safety tests. No click implementation, no `browser_click`, no `desktop_click`, no target resolution, no executor/orchestrator/frontend behavior change, no parser expansion, no compatibility parser removal.

## Decision

`cleanup_safe_now: no`

Generic `click` must be kept temporarily as a quarantined compatibility/browser stub, then deprecated and removed or replaced only after explicit `browser_click` and `desktop_click` contracts exist.

Current deterministic decomposition correctly blocks unresolved click examples before dispatch, but compatibility parser/rules and executor/tool paths still allow executable generic `click` for bare, count, coordinate, selector, or AI-produced click intents. That means generic click can currently reach executor when a compatibility parser path or test/fake planner emits it and approval is granted.

## Reference Inventory

| Location | Reference | Classification | Notes |
| --- | --- | --- | --- |
| `src/aegis/intent/decomposition.py` | `ALLOWED_EXECUTABLE_INTENTS` excludes `click`; `BLOCKED_FUTURE_INTENTS` includes `browser_click`/`desktop_click`; validation rejects raw `click` | Safe deterministic guard | Correct current foundation rule: normalized plans cannot execute raw generic click or future split click before target resolution. |
| `src/aegis/intent/decomposition.py` | unresolved click token check returns clarification plan | Safe deterministic block | Blocks `click that button` and open+first-result examples without partial `open_app`. |
| `tests/test_intent/test_decomposition.py` | raw click/future click validation tests | Test-only reference | Protects normalized plan guard. |
| `tests/test_intent/test_parser_deterministic_decomposition_smoke.py` | unresolved click parser tests | Test-only reference | Existing plus new tests protect required ambiguous examples. |
| `src/aegis/intent/rules.py` | `IntentRule(intent="click")` for coordinates, count, and bare `tıkla/click` | Unsafe ambiguity / compatibility parser path | Emits executable generic `click` outside deterministic decomposition. Should be quarantined, then replaced by split routing. |
| `src/aegis/intent/parser.py` | click coordinate/count parameter extraction | Compatibility parser support | Supports old generic `click` contract. Not safe as final architecture. |
| `src/aegis/intent/ai_parser.py` | accepts `click` if x/y or selector exists; assigns medium risk | Unsafe ambiguity | LLM/AI path can propose generic click. Future guard should reject generic click or normalize after target resolution. |
| `src/aegis/tools/web_tools.py` | `ClickTool` uses Playwright `page.click` or `page.mouse.click` | Browser-specific old code | This is really a browser click implementation under generic name. Keep only as older stub until `browser_click` exists. |
| `src/aegis/tools/registry.py` | `TOOLS["click"] = ClickTool()` and `TOOL_SPECS["click"]` | Registered older executable | Generic click is still registered, medium risk, side-effecting, browser evidence policy. |
| `config/tools.yaml` | `click` tool config | Config-only older reference | Requires approval, browser evidence policy. Should later become `browser_click`/`desktop_click` specs. |
| `config/guard_rules.yaml` | `click` in approval gates | Guard config | Approval helps, but approval is not target resolution and does not make generic click safe. |
| `src/aegis/guard/action_guard.py` | click count limit | Safe but insufficient older guard | Limits repeated clicks only. Does not resolve browser/desktop ambiguity. |
| `src/aegis/orchestrator/orchestrator.py` | `click` in `VERIFIED_TOOLS`, `SIDE_EFFECTING_TOOLS`, proof policy | Unsafe executable compatibility path | Allows approved generic click through lifecycle when parser/planner emits it. Should be removed after split. |
| `src/aegis/executor/deterministic_executor.py` | `_capture_click_context`, browser evidence for generic `click`, page acquisition for click | Browser-specific old executor path | Existing evidence is browser-oriented and should be renamed/replaced by `browser_click`; not extended as generic click. |
| `src/aegis/executor/executor.py` | older executor page setup includes `click` | Deprecated older path | Generic browser click can run if older executor is used. |
| `src/aegis/core/constants.py` | `IntentType.CLICK = "click"` | Older enum/reference | Keep until cleanup can safely remove compatibility references. |
| `tests/test_executor/test_executor.py` | coordinate click success includes browser evidence | Test-only older compatibility | Proves current executor can execute generic click. This is useful audit evidence but should be retired after split. |
| `tests/test_guard/test_action_guard.py` | click count guard tests | Test-only older guard | Can remain while older click is registered. |
| `tests/test_runtime/test_command_lifecycle.py` | approved click command resumes/executed, proof-backed click verified/unverified tests | Test-only lifecycle compatibility | Demonstrates generic click can reach orchestrator/executor after approval. |
| `tests/test_api/test_command.py` | `click 50 times` API test | Test-only guard/API compatibility | Should later assert generic click is blocked/clarification unless split routing exists. |
| `tests/test_runtime/test_action_timeline.py` | action-active tool `click` | Test-only projection fixture | Safe fixture, but can later be renamed to explicit split click. |
| `docs/design/click-capability-split.md` | split architecture | Docs-only target architecture | Correct future direction: `browser_click`, `desktop_click`, target resolution first. |
| `docs/design/deterministic-command-decomposition.md` | click guardrails | Docs-only target architecture | Aligns with current deterministic guard expectations. |
| Frontend | no direct generic `click` runtime implementation found | No active reference found | No frontend change needed. |

## Parser and Decomposition Safety Result

Required unresolved examples are currently non-executable:

| Input | Current result | Safety result |
| --- | --- | --- |
| `click that button` | `unknown` with deterministic `clarification_required` metadata | Safe: no `click`, no `browser_click`, no `desktop_click`. |
| `şuna tıkla` | `unknown` through compatibility fallback | Safe for execution: no generic click emitted. Metadata is not deterministic because no deterministic pattern matched. |
| `buna tıkla` | `unknown` through compatibility fallback | Safe for execution: no generic click emitted. |
| `brave aç ve ilk sonuca tıkla` | `unknown` with deterministic `clarification_required` metadata | Safe: no partial `open_app(brave)`, no generic click. |
| `chrome aç ve ilk sonuca tıkla` | `unknown` with deterministic `clarification_required` metadata | Safe: no partial `open_app(chrome)`, no generic click. |

The new focused parser test asserts all five examples never emit `open_app`, `click`, `browser_click`, or `desktop_click`.

## Can Generic Click Currently Reach Executor?

Yes.

The required unresolved examples do not produce executable click, but other older paths still can:

- `tıkla` parses to `click(count=1)`.
- `5 kere tıkla` parses to `click(count=5)`.
- `10 20 tıkla` parses to `click(x=10, y=20, count=1)`.
- AI parser can accept generic `click` with selector or x/y.
- `click` is registered in the tool registry and orchestrator executable/proof lists.
- The deterministic executor has a working browser-oriented generic `click` path.

This is the core quarantine finding: unresolved click is safe under deterministic decomposition, but compatibility generic click is not yet architecturally isolated from execution.

## Unsafe Older Behaviors Not To Preserve

- Generic `click` as the internal runtime capability.
- Bare natural language `click` dispatch.
- Count-only click dispatch without target identity.
- User-provided coordinates as default UX.
- Selector/coordinate execution under generic `click` instead of explicit `browser_click`.
- Treating approval as a replacement for target resolution.
- Treating browser evidence as valid desktop evidence.
- Treating dispatch success as semantic click success.

## Quarantine Recommendation

Keep temporarily, but quarantine and deprecate later.

Do not extend:

- `src/aegis/intent/rules.py` generic `click` patterns
- `src/aegis/tools/web_tools.py::ClickTool`
- `src/aegis/executor/deterministic_executor.py` generic click evidence path
- `src/aegis/orchestrator/orchestrator.py` generic click verified-tool compatibility
- AI parser generic `click` acceptance

Before any capability expansion, future work should:

1. Introduce explicit `browser_click` and `desktop_click` tool specs.
2. Add target resolution before click dispatch.
3. Make unresolved semantic targets return `clarification_required`, `approval_required`, or `blocked`.
4. Reject generic `click` from deterministic and AI plans unless a compatibility adapter maps it to a resolved split capability.
5. Treat coordinate click as a low-level fallback only, never the default natural-language path.

## Required Tests Before Browser Click Implementation

- Generic click language routes to `browser_click` only after browser context and target resolution.
- `click that button` remains clarification-required without target evidence.
- `click first search result` resolves only when a browser search results context is observable.
- Selector target must be unique, visible, and inside viewport.
- Coordinate mode must prove viewport bounds and element-at-point evidence.
- Browser challenge/CAPTCHA/permission state must not be verified success.
- Playwright dispatch success alone must not mark semantic success.

## Required Tests Before Desktop Click Implementation

- Desktop click requires foreground window identity evidence before dispatch.
- Coordinate must be inside the active window rect in a known coordinate space.
- PID/HWND/window title evidence must be attached to `ExecutionEvidence`.
- Raw semantic phrases like `şuna tıkla` do not become coordinates without target resolution.
- Coordinate-only requests are approval-gated and report geometry verification only.
- DPI/multi-monitor unknowns become unverified, clarification, approval, or blocked.
- Desktop click verified must not imply semantic button correctness.

## Blockers Before Click Capability Expansion

- Target resolution layer is not implemented.
- `browser_click` and `desktop_click` contracts do not exist in tool registry.
- Generic `click` remains registered and executable.
- AI parser can still propose generic `click`.
- Compatibility parser still emits generic `click` for bare/count/coordinate commands.
- Existing tests still encode generic click as executable compatibility.

## Recommendation

Recommended next sprint: Approval Semantics Design.

Click expansion should wait until approval/clarification/blocked semantics are explicitly settled for ambiguous UI actions. After that, run a dedicated Target Resolution Layer Design sprint, then introduce `browser_click` as the first split implementation. Do not implement `desktop_click` before the target-resolution and evidence contracts are stable.
