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
- AutoPilot output is not evidence.
- Agent output is not execution.
- Verifier success may only come from backend verifier logic.
- No fake telemetry, fake UI state, fake verification, fake runtime health,
  fake logs, fake metrics, or optimistic success.
- No uncontrolled autonomous loop, silent memory persistence, approval bypass,
  capability bypass, lease bypass, or hidden model/provider/tool fallback.

## Active Priority

Current active priority: canonical mission cleanup and productization toward
real, useful, safe product slices.

The current product target is local-first, free-first Mission Control:

- Memory OS with explicit consent
- AutoPilot read-only inspection
- deterministic and model-assisted proposals through safe boundaries
- optional local Model Gateway
- static Skill Registry metadata before skill execution
- proposal-only Agent Runtime before any execution runtime
- premium Mission Control UI that never hides backend truth
- future capability tiers for observe, explain, propose, approve, execute, and
  verify

Historical hackathon and foundation documents remain useful traceability records,
but they are not the current product narrative.

Repo-local Codex development guidance lives in
`docs/codex-skill-pack-for-aegis.md`; it is not runtime skill execution
permission.

## Working Standard

Work like a senior engineer, security-minded systems engineer, and product
engineer:

- identify the active workspace/repository before editing
- confirm whether the task belongs to Aegis, Ultron, or another project
- inspect relevant files before editing
- keep implementation scope narrow
- prefer working product slices over skeleton-only work
- avoid opportunistic refactors
- do not implement future roadmap phases unless explicitly requested
- stop and report ambiguity before editing when scope is unclear
- preserve existing contracts unless the sprint explicitly changes them
- if a larger issue is found, report it as a remaining risk instead of silently
  expanding scope

A future sprint is not accepted if it only adds skeletons, metadata, docs, or
future-gated placeholders unless it is explicitly declared as an audit,
checkpoint, or readiness sprint.

## Naming And Documentation

- Do not create new public-facing docs, feature names, sprint labels, or
  filenames with version-style suffixes or release-candidate numbering.
- Internal protocol versions, schema versions, tests, and historical decision
  references may keep version labels when needed for compatibility.
- Prefer canonical durable names such as `docs/model-gateway.md`,
  `docs/skill-registry.md`, `docs/bounded-agent-runtime.md`, and
  `docs/capability-model.md`.
- Keep README and docs truthful, current, and explicit about real,
  proposal-only, read-only, blocked, and future-gated behavior.
- Do not over-write docs with marketing fluff.

## Forbidden Unless Explicitly Scoped

- live autonomous multi-agent loop
- real MCP write execution
- real shell or file mutation through agents
- model auto-routing
- cloud fallback
- vector or graph memory runtime
- full CodingAgent patch generation
- voice, screen, OCR, or multimodal production features
- production deployment claim
- plugin marketplace
- self-modifying code
- Ultron bridge
- unified launcher
- historical archive/compaction execution
- hidden fallback to paid or external services

## Generated Drift And Artifacts

Do not commit generated drift unless a sprint explicitly scopes it.

Never stage:

- runtime logs
- screenshots
- cache output
- model files
- vector databases
- browser artifacts
- API keys
- secrets
- tokens
- temp outputs

`frontend/next-env.d.ts` is generated drift prone. Restore it before unrelated
commits unless the sprint explicitly scopes generated drift hygiene.

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
- generated drift status
- intentionally not done
- safety invariant check
- remaining risks
- recommended next sprint

Validation success is not push success. Commit and push status must be reported
separately.
