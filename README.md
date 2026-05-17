# Aegis

**Aegis is a local-first, verification-backed desktop automation runtime for Windows.**

It is designed to operate as a reliable computer assistant: it receives a user command, evaluates risk, asks for approval when needed, executes through bounded tools, verifies observable side effects, records evidence, and keeps the frontend synchronized from backend truth surfaces.

Aegis is not trying to be an uncontrolled autonomous agent. The project is intentionally built around deterministic runtime state, auditability, replayability, and approval-aware operation.

## Current Position

Aegis is currently focused on the reliability foundation for a future local AI computer operator:

- deterministic runtime authority
- separate command lifecycle state
- approval and cancellation governance
- canonical tool registry and sandbox policy
- protocol-backed WebSocket events
- append-only runtime event journal
- replayable action timeline
- execution evidence and evidence audit
- process/window verification for desktop side effects
- backend-derived UI state with no frontend fake inference
- read-only maintenance diagnostics

The long-term product direction is a trustworthy local assistant that can inspect a system, explain what it finds, recommend safe actions, request approval for risky actions, and prove what it did.

## Core Principles

- **No fake systems**: UI panels must render backend snapshot, protocol event, event journal, registry, verifier, or maintenance data.
- **Smart brain, dumb hands**: tools perform bounded operations; runtime, policy, audit, and verification decide whether work is trusted.
- **Evidence before success**: action output is not treated as proof. Desktop actions require process/window evidence when applicable.
- **Approval-aware execution**: low-risk actions may run automatically, medium-risk actions require approval, and critical actions are blocked.
- **Replayable behavior**: journaled events can rebuild the action timeline and provide audit context.
- **Bounded autonomy**: Aegis may assist, inspect, recommend, and execute approved actions, but it should not mutate the system or itself without governance.
- **Reliability Budget**: new capabilities must improve or preserve determinism, replayability, evidence quality, approval safety, backend truth, and test confidence.
- **Operational Simplicity Budget**: new capabilities should avoid unnecessary protocol fields, event types, FSM states, failure modes, recovery paths, or projection complexity.
- **Human Understandability Constraint**: a single engineer should be able to mentally trace a feature's runtime flow, evidence path, and failure behavior in a short review.

## Architecture

```mermaid
graph TD
    User[User Command] --> API[FastAPI / Socket.IO Bridge]
    API --> Command[CommandRecord / CommandStatus]
    Command --> Guard[Risk and Approval Gate]
    Guard --> Executor[Deterministic Executor]
    Executor --> Tools[Bounded Tools]
    Tools --> Verifier[Evidence and Verifier Layer]
    Verifier --> Journal[Runtime Event Journal]
    Journal --> Snapshot[Runtime Snapshot and Replay]
    Snapshot --> UI[Next.js Runtime UI]
```

### Truth Surfaces

The frontend should not invent runtime state. These backend surfaces are the source of truth:

- `src/aegis/core/protocol.py`
- `src/aegis/api/ws_bridge.py`
- `src/aegis/core/event_journal.py`
- `src/aegis/core/action_timeline.py`
- `src/aegis/core/evidence_audit.py`
- `src/aegis/tools/registry.py`
- `frontend/src/lib/socket.ts`
- `frontend/src/store/useRuntimeStore.ts`

### Contract Versioning Policy

Version suffixes such as `/1` and `/2` identify schema, verifier, and diagnostic contracts. They are not roadmap phase labels.

- Additive fields can stay on the same contract version when old readers can ignore them safely.
- Breaking payload, verifier, or replay semantics require a new version.
- Old journal events and snapshots must remain readable by replay and UI projection code.
- The frontend must not infer success or synthesize data when it sees an unknown version; it should render unavailable or unknown state from backend truth.
- Do not keep parallel v1/v2 execution paths unless backward compatibility requires it and tests cover both paths.

## Implemented Runtime Capabilities

### Command Governance

- `CommandRecord` and `CommandStatus`
- approval manager
- cancellation token support
- low / medium / critical risk policy
- approval, rejection, cancellation, blocked, and status-change events

### Tool Contract and Sandbox v1

- canonical `ToolSpec` registry
- registry drift validation
- `/tools/registry` endpoint
- frontend tool registry panel hydrated from backend state
- file tools v1
- allowlisted shell v1
- standardized risk, approval, timeout, cancellation, and evidence metadata

### Verified Desktop Evidence

Desktop side-effect actions such as `open_app`, `focus_app`, and `close_app` use a process/window verifier layer.

The evidence model includes:

- process name
- PID list
- HWND
- window title
- foreground window evidence
- process-alive / process-not-alive checks
- matching window count
- check-level evidence with expected and observed values
- graceful close and kill fallback evidence

Ambiguous desktop windows are treated as failed or unverified instead of optimistic success.

### Evidence Audit and Completion Gate

Process/window actions are gated by backend evidence audit before completion is trusted.

The audit layer protects against:

- missing critical checks
- failed critical checks
- optimistic success without evidence
- UI-generated verification results
- snapshot / journal / live socket drift

### Maintenance Diagnostics

The current maintenance path is read-only. It reports runtime health from backend-owned sources:

- runtime snapshot health
- command lifecycle state
- WebSocket runtime context
- action timeline health
- system resource snapshot
- process resource snapshot
- development port listener snapshot
- app registry health
- tool registry health
- environment checks
- documentation checks

Maintenance scan recommendations are productized as structured backend findings.
Every finding carries a category, severity, source, reason, and concrete evidence.
The UI only renders these backend findings; it does not infer maintenance status or create optimistic recommendations.
The scan does not refresh app discovery or mutate files, config, database, Git, or runtime FSM state.
It may update the ephemeral last-scan cache used by backend snapshots.

Future maintenance actions should remain approval-gated and evidence-backed.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Pydantic v2, Socket.IO |
| Runtime | FSM authority, command lifecycle, event journal, evidence audit |
| Desktop | PyGetWindow, psutil, ctypes, PyAutoGUI |
| Browser automation | Playwright |
| Frontend | Next.js, React, TypeScript, Zustand, Tailwind CSS |
| Local model integrations | Ollama / local model endpoints where configured |

## Repository Layout

```text
src/aegis/                 Backend runtime, API, verifier, tools, orchestration
frontend/                  Next.js runtime UI
tests/                     Backend and source-contract tests
config/                    Runtime configuration
schemas/                   Schema and contract assets
ui/                        Historical UI notes
logs/                      Local runtime journals and logs (ignored)
data/                      Local runtime data (ignored)
scratch/                   Local temporary test/smoke artifacts (ignored)
```

## Quick Start

### Prerequisites

- Windows
- Python 3.11+
- Node.js 20+
- Git for Windows

### Backend Setup

```powershell
git clone https://github.com/WexyS/Aegis.git
cd Aegis
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

### Frontend Setup

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

### Run

From the repository root:

```powershell
.\launch_aegis.bat
```

The default backend port is `8400`. The default frontend port is `3000`.

## Validation

Run the backend test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Build the frontend:

```powershell
cd frontend
npm.cmd run build
```

For browser smoke testing, Aegis uses the Python Playwright dependency from the backend environment. A separate JavaScript Playwright stack is not required.

## Windows Troubleshooting

### PATH Checks

Use explicit Windows commands when a tool exists but PowerShell cannot find it:

```powershell
where.exe git
where.exe node
where.exe npm.cmd
.\.venv\Scripts\python.exe -m pytest -q
```

If Git is installed but `where.exe git` does not find it, add Git for Windows to your user PATH and open a new terminal:

```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\Program Files\Git\cmd",
  "User"
)
```

For the current terminal only:

```powershell
$env:Path += ";C:\Program Files\Git\cmd"
```

### Node Commands

Prefer `npm.cmd` on Windows:

```powershell
cd frontend
npm.cmd run build
```

## Roadmap

### Near Term

- Runtime debt audit
- Maintenance scan productization
- Safer read-only system inspection
- Approval-gated maintenance actions
- Reliable desktop workflow expansion

### Later

- voice interaction
- screen/vision assistance
- richer system profiling
- layered memory and briefing
- controlled self-improvement proposals
- packaging and installer flow

These later capabilities should be added only after the runtime, evidence, approval, and replay foundations remain stable.

## Non-Goals for the Current Stage

- uncontrolled agent loops
- fake telemetry
- frontend-inferred verification
- unsandboxed tool execution
- plugin marketplace
- voice-first control
- memory graph
- self-modifying code without approval, tests, and rollback

## Project Status

Latest stable checkpoint:

- verified desktop process/window evidence
- evidence audit and completion gate
- WebSocket runtime truth sync
- replay parity hardening
- real Windows desktop smoke for open/focus/close
- full backend tests passing
- frontend production build passing

The current product target is:

**Reliable AI Computer Operator**

The first commercializable direction is likely an evidence-backed local computer maintenance assistant.
