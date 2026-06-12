# Runtime Surface Boundary Closure
Decision: `RUNTIME_SURFACE_BOUNDARY_CLOSED`

## Findings Verified

- Vision was registered through the backend vision router and the stream route could capture desktop screenshots.
- Frontend runtime state defaulted `visionFeedEnabled` to `true` and rendered live-feed image elements.
- Chaos Shield sent raw `/force_idle` and `/reset_memory` strings over the socket command channel.
- `ws_bridge.py` handled those raw strings before normal command lifecycle handling.
- Generic `click` remained present in policy dispatch names, tool registry/specs, config, executor browser handling, and the older `ClickTool`.

## Changes Made

- Added a backend `features.vision_feed` flag that defaults to `false`.
- Kept the vision router visible, but made `/vision/stream` return a disabled `403` response before any frame capture unless the backend flag is explicitly enabled.
- Added `/vision/status` to report disabled/enabled state without capturing frames.
- Changed frontend vision defaults and UI wording so the feed is future-gated and cannot be enabled by frontend state.
- Converted raw websocket control strings into blocked command lifecycle records with `not_executed=true` and `mutation_performed=false`.
- Removed generic `click` from dispatchable policy names, tool registry/specs, tool config, and executor browser dispatch handling.
- Left `ClickTool` only as a quarantined older stub that returns an error and performs no browser click.

## Vision Boundary

Vision/live desktop feed is disabled by default. A client cannot silently receive frames while the backend flag is false. The frontend no longer renders a live image source or offers a start-feed control.

## Raw Control Boundary

Raw `/force_idle` and `/reset_memory` text no longer forces runtime state or performs memory reset behavior. They are recorded as blocked, non-executed lifecycle records and are not queued for orchestration.

## Generic Click Boundary

Generic `click` is no longer registered as a runtime tool or policy-dispatchable tool. Existing guard and non-executable projection contracts still represent click requests as quarantined clarification/approval/block decisions, but executor dispatch cannot find a generic click tool.

## Frontend Authority Boundary

Frontend state remains projection-only. Vision and raw controls are disabled/quarantined in the UI, and the frontend does not gain any permission or state-transition authority.

## Tests Added

- Vision stream/status disabled-by-default tests.
- Raw websocket control quarantine test.
- Frontend source contract tests for vision and raw controls.
- Policy and registry tests proving generic click is not dispatchable.
- Executor regression proving generic click coordinates do not acquire a browser page or dispatch.

## Intentionally Not Done

- No vision/OCR/accessibility capability was added.
- No click target resolution, `browser_click`, or `desktop_click` implementation was added.
- No new runtime states or schema/protocol expansion was added.
- No journal/evidence/replay cleanup, archive, or compaction execution was added.
- No product/vertical-pack/commercial work was started.

## Remaining Risks

- Compatibility parser surfaces can still produce `click` intents for guard/non-executable handling; this is acceptable only because runtime dispatch is now quarantined.
- Future explicit vision enablement still needs privacy, consent, redaction, evidence, and operator-boundary design before it should be used.
- Timeout/safe fallback behavior remains a separate runtime reliability sprint.

## Future Work

Recommended next sprint: `Runtime State Timeout / Safe Fallback Contract`.
