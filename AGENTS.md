# Aegis Agent Instructions

Aegis is a local-first AI Mission Control Workspace for Windows-first operator
automation, runtime truth, and release-grade operational visibility.

Aegis is not Ultron. Do not import, copy, reuse, or adapt Ultron code into
Aegis unless an explicit sprint asks for an Ultron inspiration audit.

## Core Invariants

- Backend-owned state is the source of truth.
- Frontend state is presentation only, never authority.
- Model output is proposal-only, never truth, evidence, verifier success,
  approval, lease, capability, or execution permission.
- Memory retrieval is not authority.
- Context packages are not permission.
- Blueprint, manifest, report, plugin, review, lease, or approval metadata is
  not execution permission.
- Policy allow is not execution success.
- Report output is not evidence or verifier success.
- Verifier success may only come from backend verifier logic.
- No fake telemetry, fake UI state, fake verification, fake runtime health,
  fake logs, fake metrics, or optimistic success.
- No uncontrolled autonomous loop, silent memory persistence, approval bypass,
  capability bypass, lease bypass, or hidden model/provider/tool fallback.

## Active Priority

Current active priority: Hackathon Release Candidate preparation.

The declared Hackathon RC scope is intentionally narrow:

- Memory OS RC1-Core
- AutoPilot RC1-Core
- Deterministic Society Session RC1
- Premium Single-Page Mission Control UI
- Fail-safe release package

Detailed scope and acceptance criteria live in
`docs/HACKATHON_RC_SCOPE.md`. Long-term product direction lives in
`docs/AEGIS_VISION.md`.

Repo-local Codex development guidance for future skill work lives in
`docs/codex-skill-pack-for-aegis-v1.md`; it is not runtime skill execution
permission.

## Explicit RC Exceptions

The following are allowed only when requested by a scoped Hackathon RC sprint
with tests and safety gates:

- new Memory, AutoPilot, and Society backend modules
- new frontend panels or tabs for the declared RC scope
- new protocol, event, or API shapes required for the declared RC scope
- new memory states required for Memory OS RC1-Core
- deterministic society session artifacts

These exceptions do not loosen the core invariants.

## Still Forbidden Unless Explicitly Requested

- live autonomous multi-agent loop
- LLM-dependent society runtime
- real MCP write execution
- real shell or file mutation
- model auto-routing
- cloud fallback
- vector or graph memory as a Hackathon RC blocker
- full CodingAgent patch generation
- voice, screen, or multimodal production features
- WebGL or shader dependency
- production deployment claim
- plugin marketplace
- self-modifying code
- Ultron bridge
- unified launcher

## Working Rules

- Identify the active workspace/repository before editing.
- Confirm whether the task belongs to Aegis, Ultron, or another project.
- Inspect relevant files before editing.
- Keep implementation scope narrow.
- Avoid opportunistic refactors.
- Do not implement future roadmap phases unless explicitly requested.
- Stop and report ambiguity before editing when scope is unclear.
- Preserve existing contracts unless the sprint explicitly changes them.
- If a larger issue is found, report it as remaining risk instead of silently
  expanding scope.

## Validation

Use focused validation first, then broader validation when required by the
sprint. Common commands:

- `.\.venv\Scripts\python.exe -m pytest tests\test_intent -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_executor\test_executor.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `cd frontend && npm.cmd run build`
- `git diff --check`

## Sprint Report Format

After every task, report:

- decision
- commit hash
- pushed yes/no
- active repo/worktree path
- branch or detached HEAD status
- changed files
- line/diff stats
- exact behavior
- tests added/changed
- validation outputs
- whether runtime/backend/frontend behavior changed
- intentionally not done
- safety invariant check
- remaining risks
- recommended next sprint
