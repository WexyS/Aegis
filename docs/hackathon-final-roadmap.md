# Hackathon Final Roadmap

Decision: `HACKATHON_FINAL_ROADMAP_ARCHITECTURE_REALIGNMENT_V2`

This is a historical hackathon planning document. It realigns the Aegis roadmap
after the validated Hackathon RC baseline. It is planning and architecture
only. It does not implement runtime behavior, model calls, backend APIs,
frontend UI, launcher behavior, Memory, AutoPilot, Society, skills, agents, or
provider integration.

Related architecture and sprint details:

- `docs/aegis-architecture-realignment.md`
- `docs/hackathon-final-sprint-sequence.md`

## Current Baseline Classification

The current baseline is a safe Hackathon RC foundation, not the final Aegis
vision.

What is real:

- Memory OS RC1-Core: SQLite-backed local memory proposal, approval, rejection,
  soft deletion, listing, and keyword search.
- AutoPilot RC1-Core: explicit local path validation, real read-only directory
  walk, metadata-only report generation, generated/heavy directory exclusions,
  candidate memory proposals, and verifier-lite metadata.
- Deterministic Society Session RC1: six fixed role contracts, deterministic
  proposal output from AutoPilot report data, timeline, final summary, and
  process-local session storage.
- Mission Control RC UI: judge-facing Hackathon RC tab that uses backend APIs
  for Memory, AutoPilot, and Society flows.
- Launcher/Electron: `launch_aegis.bat` starts backend, frontend, and Electron
  and clears inherited `ELECTRON_RUN_AS_NODE` before spawning Electron.
- Release package/docs: RC scope, demo runbook, release package, validation
  manifest, claims matrix, and startup instructions exist.

What is demo-scoped:

- AutoPilot reports are process-local and disappear after backend restart.
- Society sessions are process-local and disappear after backend restart.
- verifier-lite is scope-bound metadata, not full verifier success.
- Society is deterministic role-template output, not a live model-assisted
  multi-agent runtime.
- AutoPilot is read-only repo structure audit, not a full mission planner.
- Memory OS is RC1 lifecycle/search, not Memory OS v2.
- The RC Golden Path is local and bounded; it is not model, MCP, tool, shell,
  cloud, or external network execution.

What is missing:

- Model Gateway RC1 for LM Studio and other local OpenAI-compatible providers.
- Real model request/response envelope, timeout, degraded state, and provider
  health integration for generation.
- Bounded Agent Runtime RC1.
- Runtime skill registry and manifest validation.
- Model-assisted Society v2.
- Memory OS v2 candidate intelligence, provenance graph, duplicate/conflict
  detection, and model-assisted summaries.
- AutoPilot v2 mission planning, richer read-only blueprints, report
  comparison, and model-assisted interpretation.
- Premium app shell overhaul with lower cognitive load.
- EN/TR localization foundation for user-facing control surfaces.

What must not be overclaimed:

- Model output is not truth, evidence, verifier success, approval, lease,
  capability, policy, permission, or runtime health.
- Agent output is not authority.
- Skill manifest or availability is not execution permission.
- Memory retrieval is not authority.
- AutoPilot report is not evidence.
- Society proposal is not truth.
- Frontend state is not backend truth.
- Provider availability is not permission.

## Hackathon Final Target

Target definition:

`Aegis Hackathon Final: a local-first AI Mission Control workspace with real
Memory, read-only AutoPilot, bounded model gateway, skill registry,
proposal-only agents, model-assisted Society, premium UI, and honest governance
boundaries.`

### Minimum Final Target

- Preserve the current RC Golden Path.
- Push and tag the validated baseline before risky expansion.
- Add Model Gateway RC1 with LM Studio local provider support behind explicit
  gates and fail-closed unavailable states.
- Add Skill Registry RC1 as manifest/metadata plus backend policy boundaries,
  without direct execution from manifest.
- Add Bounded Agent Runtime RC1 for proposal-only agent timelines using
  deterministic fallback and optional model commentary where explicitly gated.
- Add Society v2 model-assisted commentary through Model Gateway only.
- Keep Memory and AutoPilot behavior honest and non-authoritative.
- Add a basic EN/TR localization dictionary/toggle foundation for the
  user-facing Mission Control surface.

### Strong Target

- Model Gateway includes structured request/response envelopes, timeout and
  unavailable handling, schema validation for expected outputs, and UI provider
  status projection.
- Skill Registry includes validation tests for risk class, allowed scopes,
  required capabilities, enabled/disabled state, and no-permission invariants.
- Bounded Agent Runtime can produce an auditable proposal timeline with six
  default agents and no tool execution.
- Society v2 supports deterministic, model-assisted, and mixed provenance
  labels per role.
- Memory OS v2 includes duplicate/conflict candidate detection and explicit
  source/reference graph metadata.
- AutoPilot v2 includes multiple read-only blueprints and model-assisted
  interpretation that remains proposal-only.
- Premium app shell reduces debug noise through progressive disclosure while
  preserving all truth and limitation labels.

### Stretch Target

- Integrated model/agent/skill Golden Path smoke using a local LM Studio
  provider when available.
- Provider unavailable path shown cleanly when LM Studio is not running.
- Bilingual judge/operator copy for core surface labels.
- Model-assisted report polishing and Society commentary with structured output
  validation.
- Read-only skill registry can drive proposal generation without execution.

### Explicit Non-Goals

- Full final Aegis.
- Autonomous execution.
- Tool, MCP, shell, browser-write, external API, or cloud execution.
- Silent memory persistence.
- Cloud fallback.
- Vector/graph memory as a blocker.
- Full CodingAgent patch generation.
- Production deployment claim.
- Model output as authority, proof, evidence, verifier success, or permission.

## Remaining Hackathon vs Post-Hackathon

Remaining hackathon period should focus on the smallest compelling bridge from
the RC baseline to the real product direction:

- baseline push/tag and drift hygiene
- LM Studio Model Gateway RC1
- Skill Registry RC1 metadata and validation
- Bounded Agent Runtime RC1 proposal timeline
- Society v2 model-assisted commentary
- premium app shell and EN/TR foundation
- integrated local smoke and final package

Post-hackathon should own deeper and riskier expansion:

- durable AutoPilot reports and Society sessions
- full Memory OS lifecycle beyond RC1 and v2 candidate intelligence
- vector/embedding/reranking memory
- real MCP/tool execution
- CodingAgent mutation path
- cloud model routing
- production packaging
- external source and web execution
- voice, screen, OCR, multimodal production features

## Dependency Order

1. Preserve and tag the RC baseline.
2. Confirm generated drift and launch hygiene are clean.
3. Implement Model Gateway RC1 before model-assisted agents or Society.
4. Implement Skill Registry RC1 before skill-driven agents.
5. Implement Bounded Agent Runtime RC1 before model-assisted Society v2.
6. Add Society v2 after Model Gateway and Agent Runtime boundaries exist.
7. Expand Memory OS and AutoPilot after model/agent/skill boundaries are clear.
8. Polish premium UI/localization only after backend claims are stable.
9. Run integrated Golden Path smoke.
10. Freeze final submission package.

## Baseline Preservation Policy

- Push and tag the current RC before risky development.
- Do not lose the working Golden Path.
- Every future feature sprint must preserve existing RC tests or explicitly
  update the Golden Path acceptance criteria.
- No feature sprint is accepted if it breaks the baseline without a documented,
  validated replacement.
- Generated artifacts remain uncommitted.
- `frontend/next-env.d.ts` drift must be restored unless a scoped sprint
  intentionally changes it.
- Runtime logs, screenshots, SQLite smoke databases, reports, sessions, model
  files, vector databases, API keys, and secrets must not be staged.
- If Model Gateway, agents, skills, or Society v2 fail, the deterministic RC
  path must still be runnable.

## Risk Matrix

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Breaking current RC baseline | Judge demo becomes unreliable | Push/tag baseline first; rerun focused Memory/AutoPilot/Society tests after each feature sprint |
| Overclaiming model/agent autonomy | Trust boundary violation | Keep model/agent outputs labeled proposal-only; update claims matrix with each feature |
| Model Gateway instability | Demo stalls or fails | Provider unavailable state is first-class; no hidden fallback; deterministic fallback remains |
| LM Studio unavailable | Model path cannot be shown | Treat as degraded but successful governance behavior; show provider status honestly |
| UI complexity/clutter | Judges miss the value | Progressive disclosure, first-run path, simpler copy, debug panels behind advanced mode |
| Hidden state drift | False confidence | Keep backend-owned state visible; preserve stale/unknown/degraded labels |
| Generated file drift | Dirty commits and noisy release | Restore generated files after dev/build; inspect staged files before commit |
| Memory contamination | Demo data pollutes local store | Use disposable demo namespaces or temp DBs for smoke where possible |
| Process-local report/session limitation | Lost state after restart | Keep fallback instructions visible; consider durable storage post-hackathon |
| Scope creep | Final rehearsal time collapses | Time-box sprints; stop at candidate/proposal boundary when implementation risk grows |
| Insufficient final rehearsal time | Unvalidated final package | Reserve S16/S17 for integrated smoke and submission freeze |

## Acceptance Criteria For This Roadmap

- Current RC baseline is classified honestly.
- Hackathon Final target is realistic and narrower than full Aegis.
- Model Gateway, Skill Registry, Bounded Agent Runtime, Society v2, Memory OS
  v2, AutoPilot v2, premium UI, and localization boundaries are defined.
- Sprint sequence includes scope, out-of-scope, acceptance, validation, and
  risks.
- Safety invariants remain explicit.
- No runtime/backend/frontend behavior changes are introduced by this sprint.
