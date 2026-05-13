# AEGIS — UI Layer

This directory will contain the desktop UI application.

## Status: Phase 6 (Not Yet Started)

The UI framework choice (Electron / Tauri / other) is intentionally deferred.
The backend API is designed to be UI-agnostic.

## Planned Panels

- Command input (text + voice)
- System status indicator
- Action / decision panel
- Memory / trace / replay viewer
- Security status panel
- Model routing status
- Vision panel (placeholder for Phase 7)

## API Contract

The UI communicates with the backend exclusively via:

```
POST /command       → send user command
GET  /status        → system health
GET  /trace/latest  → latest trace events
GET  /memory/query  → search memory
GET  /tools/list    → available tools
GET  /models/status → model health
POST /feedback      → user feedback
POST /replay/run    → replay a trace
```
