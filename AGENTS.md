# Aegis Agent Instructions

Aegis is a local Windows-first Codex-style AI computer operator runtime.

Aegis is not Ultron.
Do not import, copy, reuse, or adapt Ultron code into Aegis.
Ultron may only be referenced in explicit audit/design tasks.

Core principles:
- Reliability before capability
- No fake telemetry
- No fake UI state
- No fake verification
- No optimistic success
- Dispatch success is not verification success
- Evidence exists does not mean verified
- Frontend is not the source of truth
- Backend snapshot, event journal, protocol events, and execution evidence are the source of truth

Architecture rules:
- Tools are dumb hands
- Decisions pass through parser/decomposition, guard, executor, verifier, evidence gate, and journal
- Ambiguous commands become clarification_required
- Risky/destructive commands require approval or are blocked
- Unverified actions must not be shown as verified success

Current priorities:
1. Runtime truth
2. Evidence integrity
3. Parser/decomposition correctness
4. Verification semantics
5. Approval/clarification/blocked semantics
6. Replay/journal/snapshot consistency
7. Read-only diagnostics
8. Controlled capability expansion

Forbidden unless explicitly requested:
- click implementation
- browser_click / desktop_click implementation
- vision/OCR/accessibility
- voice
- memory graph
- autonomous loop
- plugin marketplace
- self-modifying code
- Ultron bridge
- unified launcher
- LLM planner integration
- frontend redesign
- new runtime states
- schema/protocol expansion

Validation:
Use focused tests first, then full validation when required.

Common commands:
- .\.venv\Scripts\python.exe -m pytest tests\test_intent -q
- .\.venv\Scripts\python.exe -m pytest tests\test_executor\test_executor.py -q
- .\.venv\Scripts\python.exe -m pytest -q
- cd frontend && npm.cmd run build
- git diff --check

Report after every sprint:
- changed files
- exact behavior
- tests added/changed
- validation outputs
- intentionally not done
- remaining risks
- recommended next sprint