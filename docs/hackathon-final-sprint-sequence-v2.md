# Hackathon Final Sprint Sequence v2

Decision: `HACKATHON_FINAL_ROADMAP_ARCHITECTURE_REALIGNMENT_V2`

This sequence turns the validated Hackathon RC baseline into a realistic
Hackathon Final plan. It is planning only. Individual implementation sprints
must restate scope, tests, safety gates, and rollback criteria before code
changes.

## S7 - Roadmap + Architecture Realignment v2

Goal: realign the final roadmap after the validated RC baseline.

In scope:

- classify current RC baseline
- define final target tiers
- define Model Gateway, Skill Registry, Bounded Agent Runtime, Society v2,
  Memory OS v2, AutoPilot v2, premium UI, and localization boundaries
- define sprint sequence, risks, and baseline preservation policy

Out of scope:

- runtime behavior
- model calls
- backend APIs
- frontend UI
- Memory/AutoPilot/Society behavior changes

Acceptance criteria:

- roadmap, architecture, and sequence docs exist
- no code behavior changes
- current RC claims remain intact

Validation:

- `git diff --check`
- docs review
- `git status --short --branch`

Key risks:

- overplanning full Aegis instead of a realistic final path
- weakening safety language

## S8 - Safe Baseline Push/Tag + Drift Hygiene

Goal: preserve the working RC before risky expansion.

In scope:

- inspect clean worktree
- push current validated commits if operator approves
- create a baseline tag such as `hackathon-rc-validated`
- document generated file drift policy
- verify `frontend/next-env.d.ts` is not staged

Out of scope:

- feature implementation
- release claims beyond validated RC

Acceptance criteria:

- baseline commit/tag is recoverable
- drift policy is documented
- no generated artifacts staged

Validation:

- `git status --short --branch`
- `git log -1 --oneline`
- `git tag --list`
- optional focused RC smoke if tag changes are made

Key risks:

- pushing unreviewed local commits
- tagging a dirty or partially validated state

## S9 - Model Gateway RC1 for LM Studio

Goal: implement the first bounded local Model Gateway for LM Studio.

In scope:

- provider descriptor and local endpoint config
- explicit health/check endpoint or backend helper
- timeout and unavailable handling
- request/response envelope
- structured output validation where practical
- no hidden fallback
- model output labeled proposal-only
- tests for unavailable, timeout, malformed response, and non-authority fields

Out of scope:

- cloud provider routing
- tool calls
- memory writes
- verifier/evidence claims
- autonomous execution

Acceptance criteria:

- LM Studio available path can produce proposal output if operator environment
  has a provider running
- unavailable path returns structured degraded state
- deterministic RC path still works when model unavailable
- model response cannot grant permission, evidence, verifier success, approval,
  lease, or capability

Validation:

- `git diff --check`
- focused model gateway tests
- `pytest tests/test_core/test_foundation_config_dependency_hygiene.py -q`
- focused Memory/AutoPilot/Society tests
- optional live LM Studio smoke only if safe and explicitly scoped

Key risks:

- accidental direct use of legacy `LLMProvider`
- hidden fallback masking provider failure
- sensitive context sent without policy

## S10 - Skill Registry RC1

Goal: add a backend-owned skill manifest registry without execution.

In scope:

- skill manifest type
- registry metadata
- enabled/disabled state
- risk class and scope validation
- candidate initial skills:
  - `repo_structure_audit`
  - `memory_candidate_review`
  - `society_review`
  - `report_summarization`
  - `context_package_review`
  - `model_assisted_explanation`
- no-permission tests

Out of scope:

- dynamic imports
- skill execution
- MCP/tool calls
- external APIs
- frontend UI

Acceptance criteria:

- invalid manifest blocks
- enabled skill is not execution permission
- skill output cannot create evidence or verifier success

Validation:

- `git diff --check`
- focused skill registry tests
- policy boundary tests
- threat model regression tests

Key risks:

- manifest metadata treated as permission
- broad wildcard scope
- future skill execution implied too early

## S11 - Bounded Agent Runtime RC1

Goal: implement proposal-only agent profiles and timelines.

In scope:

- agent profile schema
- role, allowed skills, model candidate, context budget
- max step/time bounds
- policy preflight
- deterministic fallback
- proposal-only timeline output
- candidate agents: Context, Memory, AutoPilot, Policy, Verifier, Report

Out of scope:

- direct tool execution
- uncontrolled loops
- memory writes
- approval/lease creation
- verifier success

Acceptance criteria:

- agent run produces bounded proposal timeline
- stopped/blocked/degraded states are explicit
- no agent output is authority

Validation:

- `git diff --check`
- focused agent runtime tests
- policy boundary tests
- Memory/AutoPilot/Society focused tests

Key risks:

- loop runaway
- agent proposal mistaken for permission
- model dependency breaking deterministic fallback

## S12 - Model-Assisted Society v2

Goal: evolve Society from deterministic-only to deterministic plus optional
model-assisted role commentary.

In scope:

- preserve RC1 deterministic roles
- route model assistance through Model Gateway only
- add provenance labels: `deterministic`, `model_assisted`, `mixed`
- structured role commentary
- unavailable provider fallback to deterministic output

Out of scope:

- live autonomous agents
- tool execution
- silent memory writes
- permission or verifier grants

Acceptance criteria:

- deterministic Society path still passes
- model-assisted fields are proposal-only
- provider unavailable path is honest and non-blocking

Validation:

- `git diff --check`
- Society tests
- Model Gateway tests
- API tests for Society if API shape changes
- frontend build if UI changes are scoped

Key risks:

- model commentary overtrusted as truth
- role output loses provenance
- degraded state hidden for demo polish

## S13 - Memory OS v2 Candidate Intelligence

Goal: extend Memory OS with candidate intelligence while preserving explicit
approval.

In scope:

- duplicate candidate detection
- conflict candidate detection
- source/reference graph metadata
- usage events or usage refs
- model-assisted summarization through Model Gateway if S9 is stable
- governance preview

Out of scope:

- silent persistence
- vector/embedding memory as first step
- automatic activation
- memory as permission

Acceptance criteria:

- candidates remain proposed until explicit approval
- duplicate/conflict labels do not delete or overwrite data
- summaries carry provenance and non-authority labels

Validation:

- `git diff --check`
- memory manager tests
- memory API tests
- memory governance tests
- model gateway tests if summaries use model assistance

Key risks:

- memory contamination
- stale memory overtrusted
- model summaries treated as memory truth

## S14 - AutoPilot v2 Read-Only Mission Planner

Goal: expand AutoPilot into a read-only mission planner.

In scope:

- multiple read-only blueprints
- dependency surface inventory
- test surface inventory
- docs/readme quality review
- architecture summary
- model-assisted interpretation through Model Gateway where gated
- safe follow-up plan
- report comparison

Out of scope:

- file mutation
- shell execution
- CodingAgent patches
- verifier/evidence claims
- scheduled scans unless separately scoped

Acceptance criteria:

- RC1 `repo_structure_audit` still works
- new blueprints are read-only
- reports preserve limitations and unknowns
- model-assisted interpretation is proposal-only

Validation:

- `git diff --check`
- AutoPilot core/API tests
- repo-audit/source-intelligence tests if touched
- threat model regression tests

Key risks:

- scanner becomes de facto verifier
- model interpretation overclaims source truth
- broad file reads without policy

## S15 - Premium App Shell Overhaul + EN/TR Localization

Goal: make the UI more judge/operator friendly without hiding truth.

In scope:

- simplified first-run surface
- progressive disclosure for debug/runtime panels
- premium app shell layout
- EN/TR dictionary and toggle foundation
- default English for judges
- Turkish user-facing labels for the control surface
- no fake health or progress

Out of scope:

- backend authority in frontend
- static mock data as live state
- hiding failures, unknowns, stale state, or limitations

Acceptance criteria:

- Golden Path remains visible and usable
- limitation labels remain visible
- no frontend-created authority
- EN/TR copy falls back safely

Validation:

- `git diff --check`
- frontend lint
- frontend build
- browser/Electron smoke
- focused API tests if UI API usage changes

Key risks:

- visual polish hiding truth
- localization making safety copy ambiguous
- UI clutter remains too high

## S16 - Integrated Model/Agent/Skill Golden Path Smoke

Goal: validate the final integrated path without overclaiming autonomy.

In scope:

- startup through normal launcher
- backend/frontend/Electron readiness
- WebSocket connection
- Memory, AutoPilot, Society flow
- Model Gateway available and unavailable cases where practical
- skill registry projection
- bounded agent proposal timeline
- no hidden fallback

Out of scope:

- production certification
- full autonomous execution
- cloud fallback

Acceptance criteria:

- deterministic path still reaches Golden Path completion
- model/agent/skill enhancements are visibly proposal-only
- provider unavailable path is honest
- no generated artifacts committed

Validation:

- `git diff --check`
- frontend lint/build
- focused API/core tests
- browser/Electron smoke
- optional live LM Studio smoke if safe and operator-approved

Key risks:

- insufficient rehearsal time
- environment-dependent provider behavior
- demo data persistence confusion

## S17 - Final Submission Package v2

Goal: freeze the final judge package.

In scope:

- final README/demo updates
- claims matrix update
- validation manifest update
- final runbook update
- screenshots only if intentionally temporary or explicitly archived
- final risk/limitation statement

Out of scope:

- new product features
- risky refactors
- new provider behavior

Acceptance criteria:

- claims match validated behavior
- startup instructions work
- fallback path is documented
- final validation results are recorded

Validation:

- `git diff --check`
- frontend lint/build
- focused API/core tests
- final smoke checklist
- `git status --short --branch`

Key risks:

- adding last-minute features
- overclaiming final package
- generated artifacts staged

## Sequence Acceptance Rule

No sprint after S7 should be considered complete if it:

- breaks the RC Golden Path without a validated replacement
- hides provider/model/tool failures
- treats model, agent, skill, memory, AutoPilot, Society, or frontend output as
  authority
- stages generated artifacts, API keys, secrets, screenshots, runtime logs,
  SQLite smoke databases, model files, datasets, or vector stores
- skips validation without explanation
