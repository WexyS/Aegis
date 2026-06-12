# Hackathon RC Release Package v1

Decision: `HACKATHON_RC_RELEASE_PACKAGE_FREEZE_V1`

This package freezes the Aegis Hackathon Release Candidate into a judge-ready,
fail-safe local demo package. It is documentation and validation packaging. It
does not add product features, runtime behavior, model calls, MCP/tool calls,
shell execution, network execution, evidence, verifier success, or autonomy.

## RC Name

Aegis Hackathon RC: local-first Mission Control for governed memory,
read-only AutoPilot audit, deterministic Society reasoning, and backend-owned
truth surfaces.

Core message:

> Memory remembers, AutoPilot audits, Society reasons, Aegis governs.

## Commit Boundary

- Latest validated implementation commit before this release package:
  `fbf2775b12ce5e39d6102bd3a699af857b9cd1ba`
- Previous sprint decision:
  `S5_RC_GOLDEN_PATH_SMOKE_PASSED_WITH_RUNBOOK`
- This release package is a docs and validation freeze layered on top of that
  validated Golden Path. The exact S6 package commit is recorded in the final
  operator report for the sprint.

## Included RC Tracks

- Memory OS RC1-Core
- AutoPilot RC1-Core
- Deterministic Society Session RC1
- Premium Mission Control RC UI
- Fail-safe release package

## What The Golden Path Demonstrates

The judged path demonstrates a narrow, truthful, backend-driven workflow:

1. AutoPilot runs a read-only audit against a safe local project path.
2. Mission Control renders the AutoPilot report from backend response data.
3. Memory candidate proposals are shown as candidates only.
4. The operator explicitly proposes and approves or rejects Memory items.
5. Memory search/list returns backend Memory state.
6. A deterministic Society Session runs from the selected AutoPilot report.
7. Six Society role proposal cards, timeline, and final summary render.
8. Limitation labels remain visible.
9. Golden Path reaches `5/5 completed`.

The path is not a model demo, not a tool execution demo, not a shell automation
demo, not a network browsing demo, and not live autonomous multi-agent runtime.

## Backend And Frontend Start

Preferred operator start:

```powershell
.\launch_aegis.bat
```

Manual start used for isolated validation:

```powershell
.\.venv\Scripts\python.exe -m aegis.main
cd frontend
npm.cmd run build
npm.cmd run start -- -H 127.0.0.1
```

Expected local endpoints:

- Backend health: `http://127.0.0.1:8400/health`
- Frontend: `http://127.0.0.1:3000`
- Mission Control tab: `Hackathon RC`

## UI Demo Flow

Use a disposable local sample project, then:

1. Open `http://127.0.0.1:3000`.
2. Click `Hackathon RC`.
3. Enter the sample project path in `Local root path`.
4. Click `Run audit`.
5. Confirm the AutoPilot report and verifier-lite label render.
6. Propose a Memory candidate.
7. Approve one proposed Memory item.
8. Propose and reject one manual Memory item.
9. Search Memory, then clear the search before final Golden Path review.
10. Click `Run from report`.
11. Confirm all six Society roles render.
12. Confirm `Timeline`, final summary, limitation labels, and `5/5 completed`.

The exact UI checklist and API fallback commands are in
`docs/hackathon-rc-demo-runbook.md`.

## Expected Success Indicators

- Backend health returns HTTP 200.
- Frontend returns HTTP 200.
- WebSocket connects to the backend runtime channel.
- `Hackathon RC Mission Control` renders.
- AutoPilot completion notice appears from a backend response.
- Memory propose/approve/reject/search notices appear from backend responses.
- Society completion notice appears from a backend response.
- Golden Path reaches `5/5 completed`.
- Browser console has no unexpected Golden Path errors or warnings.
- No failed browser requests or bad HTTP responses occur on the success path.

## Known Limitations

- AutoPilot reports are process-local/in-memory and disappear after backend
  restart.
- Society sessions are process-local/in-memory and disappear after backend
  restart.
- Memory is SQLite-backed local storage.
- RC-specific AutoPilot, Memory, and Society events are not streamed as separate
  WebSocket track events.
- verifier-lite is not full verifier success.
- Society is deterministic role-template session output, not live autonomous
  multi-agent execution.
- AutoPilot is read-only for the demo path and must not be described as file
  mutation.
- No LLM/model, MCP, tool, shell, cloud, or external network execution is part
  of the RC Golden Path.

If the backend restarts, rerun AutoPilot and Society because process-local
reports and sessions are cleared.

## What Not To Claim

Do not claim:

- full Memory OS
- live MultiAgent Society
- autonomous execution
- model-powered analysis
- MCP/tool/shell execution
- cloud fallback
- production deployment
- report-as-evidence
- verifier-lite as full verifier success
- Memory retrieval as authority
- frontend-created runtime truth

Safe wording:

- "Memory OS RC1-Core governs explicit local memory proposals."
- "AutoPilot RC1-Core performs a read-only local audit."
- "Deterministic Society Session renders bounded role proposals."
- "Aegis keeps the demo honest with visible limitations and backend-owned
  state."

## Final Validation Commands

Run before judging or release handoff:

```powershell
git diff --check
cd frontend
npm.cmd run lint
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m pytest tests\test_api\test_autopilot_api.py tests\test_api\test_memory_api.py tests\test_api\test_society_api.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_autopilot.py tests\test_memory\test_manager.py tests\test_core\test_society.py tests\test_core\test_context_policy.py tests\test_core\test_memory_governance.py -q
```

Then perform:

- backend health HTTP smoke
- frontend HTTP smoke
- WebSocket smoke
- Golden Path browser smoke where practical
- `launch_aegis.bat` smoke when safe and practical

## Final Smoke Summary

S5 established the full Golden Path with UI-only browser smoke:

- backend health HTTP 200
- frontend HTTP 200
- WebSocket connected
- AutoPilot, Memory, and Society path completed
- all six Society roles rendered
- timeline and final summary rendered
- `5/5 completed`
- console errors/warnings: 0
- page errors: 0
- failed requests: 0
- bad HTTP responses: 0
- no runtime artifacts committed

S6 validation results are recorded in
`docs/hackathon-rc-validation-manifest.md` and in the final sprint report.

## Fallback Instructions

If reports or sessions disappear after restart:

1. Reopen `Hackathon RC`.
2. Rerun AutoPilot against the safe sample project.
3. Recreate or approve Memory items as needed.
4. Rerun Society from the new selected report.

If UI automation is unavailable, use the API fallback commands in
`docs/hackathon-rc-demo-runbook.md`, then return to the UI to show rendered
state.
