# Aegis Architecture Realignment

Decision: `HACKATHON_FINAL_ROADMAP_ARCHITECTURE_REALIGNMENT_V2`

This document defines the architecture realignment after the validated
Hackathon RC baseline and the later Agent Runtime foundation. It is not an
implementation sprint. It does not add model calls, provider probes, APIs,
frontend UI, skill execution, agent execution, memory writes, or runtime
behavior.

For current product mission and capability tiers, see:

- `docs/aegis-current-mission.md`
- `docs/capability-model.md`

## Architecture Principle

Aegis should advance from a safe RC demo into a local-first AI Mission Control
workspace by adding capability in layers. Each layer must preserve backend
authority, explicit policy, provenance, and truthful degraded states.

Non-negotiable rules:

- model output is not truth, evidence, verifier success, approval, lease,
  capability, permission, policy, or runtime health
- agent output is not authority
- skill manifest is not permission
- skill availability is not execution permission
- memory retrieval is not authority
- context package is not permission
- AutoPilot report is not evidence
- Society proposal is not truth
- frontend state is not backend truth
- no hidden model/provider/tool fallback
- no silent memory persistence
- no uncontrolled autonomous loop
- no fake telemetry, fake progress, fake success, fake evidence, or fake
  verifier

## Current System Boundary

Current implemented surfaces:

- FastAPI app with health, command, Memory, AutoPilot, Society, vision,
  local-provider probe projection, and repo-audit dry-run projection routes.
- Socket.IO runtime bridge for runtime snapshots and connectivity.
- Memory OS RC1-Core SQLite store and REST API.
- AutoPilot RC1-Core read-only repo structure audit.
- Deterministic Society Session RC1.
- Mission Control RC frontend panel using backend APIs.
- Legacy `LLMProvider` code path exists but is fail-closed unless explicit
  model authorization flags are enabled.

Roadmap implication:

- Model Gateway RC1 should become the only accepted model-call boundary for new
  model-assisted features.
- Existing direct provider paths should remain guarded and should not be
  expanded opportunistically.
- Agent, Society, Memory, AutoPilot, and UI work should consume Model Gateway
  output only as proposal material.

## Model Gateway RC1

Purpose:

Create the first real bounded model gateway for local LM Studio
OpenAI-compatible use without turning model availability into permission.

Required concepts:

- provider id and provider class
- LM Studio local OpenAI-compatible endpoint metadata
- provider health check
- model availability status
- timeout and retry budget
- request envelope with task type, privacy class, source refs, model role, and
  context budget
- response envelope with output text, structured output where practical,
  schema validation result, safety validation result, provider provenance, and
  failure state
- provider unavailable degraded state
- no hidden fallback
- no tool execution
- no memory write
- no evidence or verifier claims
- UI provider status panel later

Allowed uses:

- explanation
- summary
- proposal drafting
- report polishing
- Society role commentary
- Memory candidate refinement
- AutoPilot report interpretation

Forbidden uses:

- approval
- permission
- verifier success
- evidence
- autonomous execution
- silent memory persistence
- hidden fallback
- direct tool/MCP/shell/file mutation

Acceptance shape:

- If LM Studio is available, the gateway can produce proposal output with
  provenance and non-authority labels.
- If LM Studio is unavailable, the gateway returns a structured unavailable
  result and the deterministic RC path remains usable.
- Every model response carries `authority=false` and
  `execution_permission=not_granted_by_model_gateway`.

## Skill Registry RC1

Purpose:

Define known skills as backend-owned metadata and validation targets before any
skill execution is allowed.

Required manifest concepts:

- skill id
- name
- description
- version
- input contract
- output contract
- risk class
- allowed scopes
- required capabilities
- read-only / write / external / model-required classification
- enabled/disabled state
- provenance
- required policy checks
- required approval or lease class for future side effects

Initial candidate skills:

- `repo_structure_audit`
- `memory_candidate_review`
- `society_review`
- `report_summarization`
- `context_package_review`
- `model_assisted_explanation`

Rules:

- Manifest is not permission.
- Enabled state is not execution permission.
- Skill availability is not tool permission.
- Model requirement is not model permission.
- Skill output is not evidence or verifier success.
- No skill executes without backend policy, capability, approval/lease where
  needed, evidence expectation, and verifier/postcondition strategy.

## Bounded Agent Runtime RC1

Purpose:

Provide proposal-only agent timelines that can coordinate safe skills and model
commentary without becoming autonomous operators.

Required concepts:

- agent profile
- role
- allowed skills
- optional model provider candidate through Model Gateway
- context budget and preflight
- proposal-only output
- timeline
- policy gate
- approval boundary
- deterministic fallback where possible
- no uncontrolled loop
- no direct tool execution
- no silent memory writes

Candidate agents:

- Context Agent
- Memory Agent
- AutoPilot Agent
- Policy Agent
- Verifier Agent
- Report Agent

Rules:

- Agents produce proposals, summaries, review notes, and next-step candidates.
- Agents do not call tools directly.
- Agents do not write memory directly.
- Agents do not approve actions.
- Agents do not grant leases or capabilities.
- Agents do not mark verifier success.
- Agent loops must be bounded by max steps, timeout, and explicit stop reasons.

## MultiAgent Society v2

Purpose:

Evolve deterministic Society RC1 into model-assisted Society v2 while keeping
deterministic role contracts as the safe fallback.

Target behavior:

- The six RC1 roles remain stable:
  - Context Planner
  - Policy Reviewer
  - Memory Curator
  - AutoPilot Planner
  - Verifier Reviewer
  - Report Writer
- Each role may add model-assisted commentary through Model Gateway only.
- Each role output carries provenance:
  - `deterministic`
  - `model_assisted`
  - `mixed`
- Deterministic output remains available when model provider is unavailable.
- All outputs remain proposal-only.

Possible future roles:

- Red Team Reviewer
- UX/Explainer
- Risk Analyst

Rules:

- Society never grants permission.
- Society never executes tools.
- Society never writes memory silently.
- Society never treats model commentary as truth.
- Society cannot convert verifier-lite into full verifier success.

## Memory OS v2

Purpose:

Expand Memory OS from RC1 lifecycle/search into governed candidate intelligence
without silent persistence or authority overreach.

Potential features:

- memory usage events
- source/reference graph
- duplicate detection
- conflict detection
- explicit source provenance
- model-assisted summarization through Model Gateway
- memory candidate scoring
- governance preview
- session/project/repository scope UX
- import/export later
- vector/embedding later, not first

Keep:

- explicit approval for active memory
- no silent persistence
- memory not authority
- memory not permission
- secret-like and credential-like content blocked
- stale/conflicting/quarantined memory cannot drive actions as truth

## AutoPilot v2

Purpose:

Expand AutoPilot from one read-only repo structure audit into a read-only
mission planner and source-intelligence surface.

Potential features:

- multiple read-only blueprints
- dependency surface inventory
- test surface inventory
- docs/readme quality review
- architecture summary
- model-assisted interpretation through Model Gateway
- safe follow-up plan
- report comparison
- scheduled read-only scan later
- approval-gated non-destructive action later
- CodingAgent later, not immediate

Keep:

- read-only first
- no mutation without explicit future policy and approval
- report not evidence
- scanner not verifier
- model-assisted interpretation remains proposal-only
- no shell, MCP, tool, cloud, or external network by default

## Premium App Shell And EN/TR Localization

Purpose:

Make the working Aegis surface easier to understand without hiding runtime
truth or limitations.

Product naming:

- Primary product language: Aegis Control / Mission Control.
- Judge default: English.
- Operator/user support: Turkish for user-facing control surfaces.

Required UX concepts:

- reduce internal/debug language in the default path
- simplify first-run UX
- keep advanced runtime/debug panels behind progressive disclosure
- premium app shell with clear status hierarchy
- ambient motion or visual polish that never creates fake state
- EN/TR dictionary and toggle foundation
- no fake healthy state for visual polish
- no hidden historical, stale, unknown, degraded, or future-gated state

Localization foundation:

- stable message keys for user-facing copy
- default English strings
- Turkish strings for core controls and limitations
- no translation of backend truth into optimistic wording
- unsupported strings fall back visibly rather than inventing text

## Cross-Layer Contracts

Model Gateway feeds:

- Society v2 commentary
- Memory candidate refinement
- AutoPilot report interpretation
- report summarization
- UI explanations

Skill Registry feeds:

- Bounded Agent Runtime allowed-skill lists
- AutoPilot v2 blueprint discovery
- proposal-only skill availability display

Bounded Agent Runtime feeds:

- Society v2 role timelines
- report drafting
- safe next-step proposals

Memory OS v2 feeds:

- user-approved context refs
- candidate provenance
- conflict/duplicate warnings

AutoPilot v2 feeds:

- Society v2 source facts
- Memory candidate proposals
- UI mission plan status

No layer may feed:

- direct execution permission
- verifier success
- evidence creation
- approval creation
- capability or lease grant
- frontend authority

## Rollback And Freeze Policy

- Keep the deterministic RC path as fallback.
- If Model Gateway fails, show unavailable/degraded and continue deterministic
  flow.
- If Skill Registry validation fails, disable the skill and preserve the RC
  path.
- If Agent Runtime fails, show proposal generation failed and keep manual flow.
- If Society v2 model assistance fails, fall back to deterministic RC1 role
  output.
- If Memory OS v2 governance fails, preserve RC1 proposal/approval lifecycle.
- If AutoPilot v2 fails, preserve RC1 `repo_structure_audit`.
- If premium UI creates ambiguity, revert to the clearer RC panel.

## Not Implemented By This Realignment

- No model calls.
- No LM Studio probes.
- No provider health calls.
- No skill registry runtime.
- No skill execution.
- No agent runtime.
- No Society v2 runtime.
- No Memory OS v2 runtime.
- No AutoPilot v2 runtime.
- No frontend UI changes.
- No backend API changes.
- No launcher changes.
- No evidence, verifier success, approval, lease, capability, or runtime
  mutation.
