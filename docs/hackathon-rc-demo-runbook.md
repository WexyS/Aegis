# Hackathon RC Demo Runbook

Decision: `HACKATHON_RC_GOLDEN_PATH_SMOKE_RUNBOOK`

This runbook describes the verified judge-facing Hackathon RC Golden Path. It is
an operator checklist and fallback guide. It is not evidence, not verifier
success, not a production deployment claim, and not authorization for model,
MCP, shell, network, or autonomous execution.

## Scope

The demo covers the declared RC path only:

1. AutoPilot read-only audit.
2. AutoPilot report rendered in Mission Control.
3. Memory candidate proposal visible.
4. Explicit Memory proposal.
5. Memory approve, reject, and search/list.
6. Deterministic Society Session from the selected AutoPilot report.
7. Society role cards, timeline, final summary, and limitation labels.

Do not claim live autonomous agents, full Memory OS, full verifier success,
model-based analysis, MCP execution, shell execution, network execution, or
durable report/session persistence during this demo.

## Start Checklist

Preferred normal start:

```powershell
.\launch_aegis.bat
```

The launcher clears inherited `ELECTRON_RUN_AS_NODE` before spawning Electron.
If Electron does not appear from an automation shell, first confirm the current
launcher includes that guard before changing runtime or frontend code.

Manual fallback start:

```powershell
.\.venv\Scripts\python.exe -m aegis.main
cd frontend
npm.cmd run build
npm.cmd run start -- -H 127.0.0.1
```

Expected readiness checks:

- `GET http://127.0.0.1:8400/health` returns HTTP 200.
- `GET http://127.0.0.1:3000` returns HTTP 200.
- Browser console has no new critical errors.
- WebSocket connects to the backend runtime channel.

## Safe Sample Project

Use a disposable local sample project for the demo. A minimal sample can contain:

```text
sample-project/
  README.md
  pyproject.toml
  docs/index.md
  src/demo/__init__.py
  tests/test_demo.py
```

Keep the sample outside committed source unless the sprint explicitly asks for a
fixture. Do not commit smoke SQLite databases, screenshots, logs, or generated
runtime artifacts.

## UI Golden Path

1. Open `http://127.0.0.1:3000`.
2. Click the `Hackathon RC` sidebar tab.
3. Confirm `Hackathon RC Mission Control` is visible.
4. Enter the safe sample project path in `Local root path`.
5. Click `Run audit`.
6. Confirm the AutoPilot notice appears:
   `AutoPilot read-only audit completed from backend response.`
7. Confirm the AutoPilot report renders:
   - status
   - included files
   - dirs
   - `verifier-lite`
   - key files, docs/tests, frontend/backend indicators
   - risk markers and limitations
8. Confirm Memory candidate proposals are visible.
9. Click a candidate `Propose`.
10. Confirm the Memory notice appears:
    `Memory proposal created. It is not active until explicitly approved.`
11. Click `Approve` on a proposed memory.
12. Confirm:
    `Memory approve completed from backend response.`
13. Enter a manual memory proposal.
14. Click the Memory OS `Propose` action.
15. Click enabled `Reject` on the new proposed memory.
16. Confirm:
    `Memory reject completed from backend response.`
17. Use `Search/List` to verify memory search. Clear the search afterward before
    checking final Golden Path completion, because the UI list reflects the
    current search filter.
18. Click `Run from report`.
19. Confirm:
    `Deterministic Society Session completed from backend response.`
20. Confirm all six role cards render:
    - Context Planner
    - Policy Reviewer
    - Memory Curator
    - AutoPilot Planner
    - Verifier Reviewer
    - Report Writer
21. Confirm `Timeline` and the final Society summary render.
22. Confirm the Golden Path strip reaches `5/5 completed`.

## Expected Labels

The UI should keep these limitation and boundary labels visible:

- `backend APIs only`
- `no fake evidence`
- `proposal-only society`
- `explicit memory actions`
- AutoPilot report is not evidence and not full verifier success.
- verifier-lite is not full verification.
- Memory is not authority and does not grant permission.
- Society is deterministic and bounded, not live autonomous multi-agent.
- AutoPilot reports and Society sessions are process-local/in-memory only.

## API Fallbacks

Use API fallback only when UI automation cannot perform an action. Prefer UI for
the judged demo.

Run AutoPilot:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8400/autopilot/run `
  -ContentType application/json `
  -Body (@{
    task_id = "repo_structure_audit"
    root_path = "C:\Path\To\sample-project"
  } | ConvertTo-Json)
```

Propose Memory:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8400/memory/propose `
  -ContentType application/json `
  -Body (@{
    type = "repo_memory"
    content = "Demo memory candidate"
    summary = "Explicit demo proposal"
    scope = "repository"
    sensitivity = "internal"
    project_ref = "hackathon-rc"
    repository_ref = "sample-project"
    source_refs = @(@{ ref_id = "demo"; ref_type = "operator_demo" })
  } | ConvertTo-Json -Depth 5)
```

Approve or reject Memory:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8400/memory/<memory_id>/approve
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8400/memory/<memory_id>/reject `
  -ContentType application/json `
  -Body (@{ reason = "Rejected during demo validation" } | ConvertTo-Json)
```

Search Memory:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8400/memory/search?keyword=demo&include_sensitive=true"
```

Run Society:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8400/society/run `
  -ContentType application/json `
  -Body (@{
    autopilot_report_id = "<report_id>"
    memory_ids = @("<active_memory_id>")
    society_name = "hackathon_rc_review_society"
  } | ConvertTo-Json -Depth 5)
```

Fetch Society session:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8400/society/sessions/<session_id>
```

## Fail-Safe Rules

- If AutoPilot fails, show the backend error and do not claim report success.
- If a Memory action fails, show the backend error and do not mark memory active.
- If Society fails, show the backend error and do not claim session completion.
- If WebSocket disconnects, report it as runtime connectivity degradation.
- If screenshots or smoke logs are created, keep them as temporary artifacts
  unless a sprint explicitly asks to archive them.

## Validated Smoke

The S5 smoke validated the Golden Path with:

- real backend API responses
- real frontend UI interactions
- safe temporary sample project
- temporary Memory SQLite database outside the repo
- no API fallbacks
- no console errors or warnings
- no page errors
- no failed browser requests
- no bad HTTP responses
- WebSocket connected
- screenshots captured as temporary artifacts only

## Not Done

- No frontend feature work.
- No backend feature expansion.
- No WebSocket support for RC-specific tracks.
- No durable AutoPilot report persistence.
- No durable Society session persistence.
- No model, MCP, tool, shell, cloud, or external network execution.
- No evidence or verifier success was created.
- No runtime journal, evidence, or replay state was mutated.

## Remaining Risks

- AutoPilot reports and Society sessions are process-local and disappear after
  backend restart.
- Memory persistence is local SQLite and remains non-authoritative.
- The Golden Path strip reflects currently loaded UI state. If Memory search is
  filtered, clear the filter before using the strip as the final demo progress
  indicator.
- verifier-lite is useful demo metadata only, not full backend verifier success.
