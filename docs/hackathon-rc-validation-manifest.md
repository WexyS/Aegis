# Hackathon RC Validation Manifest

Decision: `HACKATHON_RC_VALIDATION_MANIFEST_V1`

This manifest records the validation boundary for the Hackathon RC release
package. It is not evidence, not verifier success, and not production
certification. Runtime-generated SQLite databases, reports, sessions,
screenshots, and logs must not be committed.

## Validation Scope

S6 validates the release package and rechecks the local RC path without adding
new product behavior.

Validated surfaces:

- release documentation
- README judge quickstart
- frontend lint/build
- AutoPilot API and core tests
- Memory API and manager tests
- Society API and core tests
- Context Policy tests
- Memory Governance tests
- backend/frontend HTTP smoke
- WebSocket smoke where practical
- Golden Path smoke where practical
- `launch_aegis.bat` smoke when safe and practical

## Commands

```powershell
git diff --check
cd frontend
npm.cmd run lint
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m pytest tests\test_api\test_autopilot_api.py tests\test_api\test_memory_api.py tests\test_api\test_society_api.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_autopilot.py tests\test_memory\test_manager.py tests\test_core\test_society.py tests\test_core\test_context_policy.py tests\test_core\test_memory_governance.py -q
```

Smoke checks:

- backend health HTTP check
- frontend HTTP check
- WebSocket connection check
- Hackathon RC tab browser check
- Golden Path browser smoke when runtime cost is acceptable
- `launch_aegis.bat` smoke when it can be safely started and cleaned up

## S5 Golden Path Summary

S5 validated the complete judged path:

- backend health HTTP 200
- frontend HTTP 200
- WebSocket connected
- Hackathon RC tab loaded
- AutoPilot read-only audit completed through UI
- AutoPilot report rendered
- Memory candidate proposal visible
- Memory propose, approve, reject, and search/list completed
- deterministic Society Session ran from AutoPilot report
- all six Society role cards rendered
- timeline and final summary rendered
- limitation labels visible
- Golden Path reached `5/5 completed`
- UI path used without API fallback
- console errors/warnings: 0
- page errors: 0
- failed requests: 0
- bad HTTP responses: 0
- no runtime artifacts committed

## S6 Final Validation Results

| Check | Result | Notes |
| --- | --- | --- |
| `git diff --check` | Passed | Whitespace check passed; Git reported expected README LF/CRLF warning only. |
| frontend lint | Passed | `cd frontend && npm.cmd run lint` |
| frontend build | Passed | `cd frontend && npm.cmd run build` |
| API tests | Passed | AutoPilot, Memory, Society: `10 passed` |
| core tests | Passed | AutoPilot, Memory manager, Society, Context Policy, Memory Governance: `160 passed` |
| backend health HTTP smoke | Passed | Isolated S6 smoke returned HTTP 200. |
| frontend HTTP smoke | Passed | Isolated S6 smoke returned HTTP 200. |
| WebSocket smoke | Passed | Browser smoke observed runtime WebSocket connection. |
| Golden Path smoke | Passed | S6 Playwright fallback smoke completed UI-only Golden Path with no API fallback. |
| `launch_aegis.bat` smoke | Partial | Batch launched backend/frontend and ports `8400`/`3000` listened; Electron visual window was not verified from headless automation. The launcher generated `frontend/next-env.d.ts` dev-mode drift, which was restored and not staged. |

## Launch Script Status

`launch_aegis.bat` is the documented preferred operator start. It starts the
backend, frontend dev server, and Electron workflow and keeps an orchestrator
terminal alive. Because it starts long-running UI processes, validation must
include a cleanup step when run from automation.

S6 status: partial. Automated smoke confirmed backend and frontend HTTP
readiness from the launcher path. Electron visual readiness was not verified.
The launch path can produce tracked `frontend/next-env.d.ts` dev-mode drift
because Next dev rewrites the route type import. That generated drift was
restored and must not be committed as release-package output.

## S6 Smoke Details

Browser validation used standalone Playwright because the in-app Browser
runtime reported `Browser is not available: iab`.

S6 isolated Golden Path smoke used:

- temporary sample project outside the repo
- temporary Memory SQLite database outside the repo
- real backend API responses
- real frontend UI interactions
- no API fallback
- no committed screenshots, logs, reports, sessions, or SQLite files

Observed S6 smoke result:

- backend health: HTTP 200
- frontend: HTTP 200
- WebSocket: connected
- AutoPilot read-only audit: completed through UI
- AutoPilot report: rendered
- Memory candidate proposal: visible
- Memory propose/approve/reject/search: completed through UI
- deterministic Society Session: completed from selected AutoPilot report
- all six Society roles: rendered
- timeline and final summary: rendered
- Golden Path: `5/5 completed`
- console errors/warnings: 0
- page errors: 0
- failed requests: 0
- bad HTTP responses: 0

Temporary screenshot paths from S6 local smoke:

- `C:\Users\nemes\AppData\Local\Temp\aegis-s6-smoke-3f6h1obz\artifacts\hackathon-rc-initial.png`
- `C:\Users\nemes\AppData\Local\Temp\aegis-s6-smoke-3f6h1obz\artifacts\hackathon-rc-final.png`

## Claim Hygiene

Validated wording must preserve these statements:

- AutoPilot report is not evidence.
- verifier-lite is not full verifier success.
- Society is deterministic and bounded, not live autonomous multi-agent.
- Memory retrieval is not authority or permission.
- AutoPilot does not mutate files in the RC Golden Path.
- No model, MCP, tool, shell, cloud, or external network execution is part of
  the RC Golden Path.
- Process-local AutoPilot reports and Society sessions are visible limitations.
