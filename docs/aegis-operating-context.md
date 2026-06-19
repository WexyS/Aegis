# Aegis Operating Context

This file is the canonical operating context for future ChatGPT / Custom GPT
inspection of the Aegis repository. It is a project-memory document, not runtime
authority, not evidence, and not verifier success.

## Mission

Aegis is a local-first, free-first AI Mission Control workspace for Windows-first
operator automation, runtime truth, and release-grade operational visibility.

Aegis should become powerful without becoming reckless:

- observe local state through bounded read-only surfaces
- explain what is known, unknown, blocked, or stale
- propose actions without treating proposals as execution
- require explicit policy, approval, capability, and verifier gates for risky
  work
- preserve historical debt instead of hiding it

## Roles

The user/operator owns direction, approvals, and final acceptance.

Codex is the implementation agent. Codex edits files, runs tests, commits, and
pushes when a sprint authorizes that work and validation passes.

Custom GPT / Aegis Architect is a read-only reviewer and prompt planner. It may
inspect files through the read-only bridge, compare Codex reports against repo
state, and draft precise future Codex prompts. It does not control Codex and
does not execute commands.

The read-only ChatGPT bridge, local launcher scripts, and local ngrok launcher
scripts are implemented as operator-started helper surfaces. They do not add
write, execute, shell, MCP, runtime dispatch, evidence, verifier, approval,
lease, or mutation authority.

## Latest Accepted State

Latest accepted verification decision: `AEGIS_SYSTEM_VERIFICATION_COMPLETE`

Latest accepted commit: `3c223e5f00aec1cc8616284db22bd063693e04ba`

Accepted verification result:

- pushed to `origin/main`: yes
- full pytest: `4221 passed, 4 deselected`
- runtime health: `warning`
- active failure components: none
- current blockers: 0
- active evidence failures: 0
- active missing evidence: 0
- pending decisions: 0
- restored pending decisions: 0
- restored executable unresolved: 0
- restored operator-cancelled count: 14
- evidence raw/projection: raw `fail`, projection `warning`
- replay raw/projection: raw `fail`, projection `warning`
- runtime snapshot projection: `warning`
- quarantined unknown-era debt: present, manifest-backed
- archived historical debt: `not_needed`
- manifest ref: `live-full-export-items`

This is not a green production-security claim. It means no current operational
blocker prevents the next controlled product slice.

## Capability Model Summary

Aegis currently separates capability tiers:

- Observe: read backend-owned state or local metadata without mutation.
- Explain: summarize observed state without claiming truth beyond sources.
- Propose: create plans, memory proposals, or agent proposals.
- Approve: operator-owned decision gate.
- Execute: future gated capability, not granted by proposal metadata.
- Verify: backend verifier-owned completion truth.

Metadata, proposals, context packages, model outputs, Memory records, Skill
Registry entries, and Agent Runtime sessions do not grant execution permission.

## Trust Boundaries

- Backend-owned state is the source of truth.
- Frontend state is presentation only.
- Model output is proposal-only.
- Memory retrieval is not authority.
- AutoPilot output is not evidence.
- Skill manifest metadata is not permission.
- Agent output is not execution.
- Context packages are not permission.
- Verifier success may only come from backend verifier logic.
- No fake telemetry, fake health, fake evidence, or optimistic success.
- Missing evidence and unknown-era debt must remain visible.

## Runtime Health Interpretation

Runtime health is currently `warning`, not `ok`.

Aegis uses a two-layer health model:

- Raw diagnostics preserve the observed status of evidence, replay, and runtime
  snapshot checks.
- Active projections classify whether the raw debt is a current operational
  blocker.

Raw evidence and replay diagnostics still report `fail`. Active projections are
`warning` because the remaining debt is manifest-backed historical/quarantined
attention, not a current blocker.

## Evidence And Replay Quarantine

Unknown-era evidence and replay debt remains inspectable through the quarantine
manifest. Missing historical evidence was not reconstructed or fabricated.

The intended closure model remains:

- archived legacy manifest
- explicit retired legacy baseline
- clean current operational baseline
- archived debt remains inspectable
- active runtime does not fail because safely closed legacy debt is quarantined

## Restored Approval Lifecycle

Latest verified state:

- pending decisions: 0
- restored unresolved decisions: 0
- restored executable unresolved: 0
- restored operator-cancelled records remain inspectable: 14

No approval was auto-granted, auto-denied, or hidden.

## Test Runtime Journal Isolation

Default pytest runs use isolated temporary runtime/log directories.
`RuntimeEventJournal.append()` refuses live `logs/runtime_events.jsonl` writes
during pytest unless explicitly opted in. The last accepted full pytest run did
not mutate the live runtime journal fingerprint.

## Current Module Map

Maintenance Scan: implemented read-only diagnostics with raw-vs-active health
projection.

Event Journal: append-only canonical runtime journal with hash-chain diagnostics
and pytest live-journal guard.

Evidence Audit: implemented read-only classification over action lifecycle and
evidence state. It does not fabricate evidence.

Replay Diagnostics: implemented diagnostics that preserve historical mixed-era
and reset-boundary debt.

Pending Decision Hygiene: implemented read-only lifecycle projection. It does
not resolve decisions.

Approval Lifecycle: implemented explicit pending/approved/rejected/cancelled
state. Approval metadata is not execution.

Memory: implemented local SQLite core with propose/approve/reject/delete/search
surfaces. Memory retrieval is not authority.

AutoPilot: implemented read-only local repository structure audit. Reports are
analysis output, not evidence.

Society: implemented deterministic proposal sessions. It is not autonomous
execution.

Model Gateway: implemented optional local LM Studio/OpenAI-compatible boundary.
Model output is proposal-only.

Aegis Model Hub: implemented local LM Studio status, explicit probe, and
proposal-only local text surface. Status is configuration-only until the
operator explicitly probes or sends a proposal request.
Operator setup and explicit local smoke guidance lives in
`docs/model-hub-operator-setup.md`; the helper script is diagnostics-only and
does not edit `.env`, start providers, create evidence, or add cloud fallback.
Model Hub also projects static local model profiles/resource guardrails and
external provider readiness metadata. External provider key presence is boolean
metadata only; cloud calls and automatic fallback remain disabled. The current
External Provider Broker Boundary adds only provider setup guidance and a
dry-run prompt preview envelope. It does not call external providers, expose
key values, send prompt payloads, or grant cloud routing.

Skill Registry: implemented static metadata catalog and proposal surfaces. It
does not execute skills.

Agent Runtime: implemented bounded proposal-only sessions. Agents do not call
tools, MCP, shell, model completions, or memory writes in the current runtime.

Aegis Ask: implemented read-only explanation and safe next-step planning over
backend-owned status and metadata. It is not command execution, tool execution,
plugin execution, model authority, memory write, evidence, verifier success, or
approval/capability/lease grant. The deterministic router distinguishes Skill
Registry, Tool Registry, and Plugin Registry questions without model calls.

Frontend / Operator Workspace: implemented unified product shell centered on a
single New Task composer and `OperatorResponseDraft`. Primary navigation is
History, Projects, Outputs, Memory, and Skills; Settings and Advanced remain
secondary controls. Existing Ask, Work, capability, model, memory, artifact,
and diagnostic surfaces remain reachable through those destinations and the
workspace drawer instead of competing as dashboard panels. It remains
presentation only. English/Turkish UI preferences, Electron-owned window
controls, backend/fallback route-source labels, runtime truth, and raw debt
visibility are preserved.

Launcher: implemented baseline launcher surfaces. Launcher cleanup remains
future work.

## Current Limitations

- Runtime health is warning-level, not green.
- Raw evidence and replay diagnostics still fail.
- UI/product experience has a unified operator workspace with responsive
  desktop/mobile rendering, localized controls, and Electron window controls,
  but conversation persistence, keyboard accessibility, and broader Electron
  state QA remain useful follow-up work.
- Aegis Ask is implemented as a narrow read-only explanation slice, not an
  execution surface.
- Full autonomous operation is not implemented.
- Real tool/MCP execution is not implemented.
- Skill Registry is metadata, not execution.
- Agent Runtime is proposal-only.
- Memory consent UX is planned, not fully productized.
- Optional local model calls are bounded; cloud fallback is not required core
  behavior.

## Memory Consent Model

Long-term memory must not be written silently by default. The intended UX is a
Memory Inbox / candidate queue:

- session/ephemeral context may be automatic when disclosed
- persistent memory requires explicit lifecycle state
- sensitive, secret-like, or private content requires explicit approval
- user can approve, reject, forget, or delete
- retrieval remains context, not authority

## Local Model Posture

Local LM Studio/OpenAI-compatible providers are optional. Aegis prefers local
and free-first operation, but provider availability is not execution permission.
Model Gateway output remains proposal-only and cannot create evidence, verifier
success, approval, lease, capability, or runtime truth.
Live LM Studio success is operator-environment specific; disabled,
misconfigured, unavailable, and timeout states are valid fail-closed outcomes
that must remain visible.
External provider readiness does not call OpenRouter, DeepSeek, OpenAI,
Anthropic, Gemini, or any other cloud provider. Future cloud use requires an
External Provider Broker with explicit opt-in, prompt preview, cost and privacy
warnings, and proposal-only output. The current broker boundary is preview-only
and remains blocked.

## Implemented Versus Planned

Implemented:

- maintenance diagnostics
- journal isolation for tests
- evidence/replay projection and quarantine visibility
- Memory core lifecycle/search
- AutoPilot read-only scanner
- deterministic Society proposal surface
- local Model Gateway boundary
- Aegis Model Hub local status/probe/proposal surface
- static Skill Registry
- bounded Agent Runtime proposal sessions
- read-only ChatGPT bridge and local launcher helpers
- Aegis Ask read-only explanation slice
- unified operator workspace, copy-ready preview artifacts, secondary context
  drawer, Settings language selector, Electron window controls, and capability
  map

Planned:

- capability broker
- approval-gated safe execution slices
- model-assisted interpretation through strict boundaries

## Overclaim Guardrails

Do not claim:

- full autonomy
- production security certification
- raw evidence/replay debt is fixed
- model output is truth
- AutoPilot report is evidence
- Memory is authority
- Skill Registry or Agent Runtime can execute work
- paid or external services are required core dependencies

## Next Direction

Continue productization after the unified operator workspace by improving
conversation lifecycle, keyboard accessibility, source-specific read-only
summaries, capability broker design, Memory Inbox workflow, and controlled
read-only capability execution without weakening runtime truth or
approval/evidence/verifier boundaries.
