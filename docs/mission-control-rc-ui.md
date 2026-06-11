# Mission Control RC UI

Decision: MISSION_CONTROL_RC_UI_WITH_REAL_BACKEND_APIS

Mission Control RC UI adds a judge-facing Hackathon RC tab for the three RC
backend tracks:

- Memory OS RC1-Core
- AutoPilot RC1-Core
- Deterministic Society Session RC1

The UI uses real backend APIs. It does not use static mock data as the main
path and does not fabricate success states.

## UI Structure

The existing Aegis shell receives a new sidebar tab:

- `Hackathon RC`

The tab contains:

- Golden Path status strip
- AutoPilot read-only audit panel
- AutoPilot report renderer
- Memory OS action panel
- Deterministic Society Session panel
- degraded-state and limitation labels

## Premium Visual Layer

S4.1 adds a scoped premium visual layer for the Hackathon RC surface only. The
layer is CSS-based and does not add backend behavior, fake progress, fake
telemetry, evidence claims, or verifier claims.

The visual layer includes:

- dark Mission Control workspace treatment
- non-blocking ambient radial/conic light field
- masked grid depth layer
- glass/depth panels and candidate cards
- stronger first-screen hierarchy
- guided Golden Path progression
- premium in-flight API loading banners
- clearer empty and limitation states
- refined Society role and timeline presentation

The ambient and loading animations are disabled for users who prefer reduced
motion. The UI remains usable with the visual layer static because all effects
are decorative and `pointer-events: none` where they sit above the workspace.

## Golden Path

The visible flow is:

1. Run AutoPilot read-only repo audit.
2. Inspect the report and candidate memories.
3. Explicitly propose and approve/reject/delete Memory entries.
4. Run deterministic Society Session from the selected AutoPilot report.
5. View Society role proposals, timeline, and final summary.

The Golden Path state is driven by backend responses and local UI selection
state. It is not fake telemetry.

The S4.1 Golden Path polish keeps that rule: a step only appears completed when
the corresponding backend response or explicit user action is present in UI
state. Visual progress does not imply hidden backend work.

## Backend Endpoints Used

AutoPilot:

- `POST /autopilot/run`
- `GET /autopilot/reports/{report_id}`
- `GET /autopilot/reports`

Memory:

- `POST /memory/propose`
- `POST /memory/{memory_id}/approve`
- `POST /memory/{memory_id}/reject`
- `DELETE /memory/{memory_id}`
- `GET /memory`
- `GET /memory/search`

Society:

- `POST /society/run`
- `GET /society/sessions/{session_id}`
- `GET /society/sessions`

## Labels and Limits

The UI labels:

- AutoPilot as read-only audit.
- AutoPilot report as report, not evidence.
- verifier-lite as verifier-lite, not full verification.
- Memory candidates as candidate-only.
- active Memory as non-authoritative.
- Society as deterministic and bounded.
- Society proposals as proposals, not truth.

Current limitations are shown in the UI:

- AutoPilot reports are process-local/in-memory only.
- Society sessions are process-local/in-memory only.
- No WebSocket events for these tracks yet.
- No LLM/model/MCP/tool/shell/network execution.
- Memory is local SQLite.
- Society is deterministic, not autonomous.
- AutoPilot is read-only.

## Not Implemented

- No backend feature changes.
- No WebSocket integration for RC tracks.
- No durable AutoPilot report or Society session persistence.
- No model, MCP, tool, shell, network, or cloud calls.
- No frontend-created authority.
- No evidence or verifier success claims.

## Safety Rules

The UI must not:

- fabricate backend success
- hide backend errors
- treat reports as evidence
- treat verifier-lite as full verification
- treat Society as live autonomous multi-agent behavior
- silently persist memory
- treat memory retrieval as authority
- imply hidden provider/model/tool fallback

## Manual Visual Smoke Checklist

If automated browser visual capture is unavailable:

1. Start the backend normally.
2. Start the frontend normally.
3. Open the Aegis UI and select `Hackathon RC`.
4. Confirm the first screen reads as a premium Mission Control workspace.
5. Confirm the ambient visual layer never blocks clicks, focus, or scrolling.
6. Run an AutoPilot audit and confirm the loading banner is in-flight only.
7. Propose and approve/reject a Memory candidate only through explicit buttons.
8. Run a deterministic Society Session from a selected AutoPilot report.
9. Confirm Golden Path steps advance only after real backend responses or
   explicit user actions.
10. Confirm report, Memory, Society, limitation, empty, and error states remain
    truthful and do not claim evidence, verifier success, or autonomy.

## Current Limitations

- Visual smoke is still manual if no Browser/IAB or Playwright runner is
  available in the environment.
- AutoPilot reports and Society sessions remain process-local backend state.
- This sprint does not add durable persistence, WebSocket integration, or new
  backend routes for the RC tracks.
