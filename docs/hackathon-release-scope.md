# Hackathon Release Candidate Scope

## Decision

Decision: `HACKATHON_RELEASE_SCOPE_DOCUMENTED_ONLY`

This document defines the declared Aegis Hackathon Release Candidate scope. It
is not a runtime implementation checklist, not a claim that the scope is already
implemented, and not evidence that foundation work is closed.

## Product Positioning

Aegis Hackathon release is a local-first AI Mission Control Workspace that shows a
narrow, honest, end-to-end operator experience:

- real backend-owned state rendered in a premium single-page UI
- governed memory proposal and approval flow
- read-only AutoPilot audit output
- deterministic Society Session artifact generation from available backend data
- fail-safe release packaging with truthful limitations

The RC should demonstrate trustworthy control-plane behavior, not broad
autonomous execution.

## 100 Percent Declared Scope Quality Rule

Every feature claimed as part of Hackathon release must work completely inside its
declared scope. Narrow scope is acceptable. Half-working claims are forbidden.

Do not claim foundation closure, full Memory OS, live MultiAgent Society,
autonomous execution, or AI-powered analysis unless the exact claimed behavior
is implemented, gated, and validated.

## In Scope

- Foundation-honest state, preferably foundation-closed only if validated later
- Memory OS Core
- AutoPilot Core
- Deterministic Society Session
- Premium Single-Page Mission Control UI
- Fail-safe release package

## Out Of Scope

- live autonomous multi-agent loop
- LLM-dependent society runtime
- real MCP write execution
- real shell or file mutation
- model auto-routing
- cloud fallback
- full CodingAgent patch generation
- production deployment claim
- vector or graph memory as a release blocker
- voice, screen, or multimodal production features
- WebGL or shader dependency

## Future-Gated

- Full Memory OS beyond Core
- Live MultiAgent Society
- CodingAgent patch generation and repo mutation
- MCP write tools
- cloud provider fallback
- vector memory, graph memory, and RAG
- voice, screen, multimodal, and ambient operating modes
- production deployment and enterprise packaging

## Memory OS Core Scope

Memory OS Core is a governed memory proposal loop, not full autonomous
memory.

Required scope:

- propose memory item from a bounded backend path
- validate identity, namespace, sensitivity, and provenance
- require approval before activation
- reject or block at least one invalid proposal
- render memory state from backend data
- avoid silent persistence

Acceptance criteria:

- at least one propose -> approve cycle works end to end
- at least one invalid proposal is blocked by governance
- UI shows backend memory data, not static mock data
- memory retrieval remains non-authoritative
- memory output cannot grant permission, evidence, verifier success, approval,
  lease, or capability

## AutoPilot Core Scope

AutoPilot Core is a read-only audit and report producer, not autonomous
execution.

Required scope:

- run a bounded scan or equivalent backend-owned read-only audit path
- produce a parseable report
- preserve source, limitations, and unknowns
- show results in Mission Control
- avoid shell/file mutation unless a later sprint explicitly scopes it

Acceptance criteria:

- AutoPilot scan produces a report
- report is parseable JSON or otherwise explicitly machine-readable
- report is not treated as evidence or verifier success
- report does not hide blockers, unknowns, or future-gated items

## Deterministic Society Session Scope

Deterministic Society Session is a deterministic session artifact, not a
live LLM multi-agent runtime.

Required scope:

- consume real Memory/AutoPilot/backend data when available
- produce deterministic role/session/timeline artifacts
- preserve provenance and limitations
- mark missing inputs as unavailable or future-gated

Acceptance criteria:

- session output is reproducible from supplied backend data
- no LLM-dependent society runtime is required
- no agent loop executes tools or mutates state
- if live data consumption is not ready, output is downgraded to static preview
  with that limitation visible

## Premium Single-Page Mission Control UI Scope

The RC UI should feel like a polished Mission Control workspace while preserving
truthful backend state.

Required scope:

- single-page mission dashboard
- panels for runtime health, memory, AutoPilot, Society, and release readiness
- real backend data for claimed working panels
- clear unavailable, blocked, stale, and future-gated states
- no frontend-only authority

Acceptance criteria:

- frontend loads
- UI renders real backend data for working panels
- non-working panels are removed, blocked, or clearly future-gated
- no static mock data is presented as live state
- no fake success, fake health, fake evidence, or fake verification is shown

## Fail-Safe Release Package Scope

The release package should make the demo truthful and recoverable.

Required scope:

- startup instructions
- demo script
- validation checklist
- known limitations
- fail-safe fallback path
- release claim rules

Acceptance criteria:

- backend starts
- frontend loads
- health endpoint works
- demo path can be repeated
- known non-RC features are future-gated, not hidden

## Tier-0 Must-Work Criteria

- backend starts
- frontend loads
- health endpoint works
- at least one Memory propose -> approve cycle works
- AutoPilot scan produces a report
- Memory governance blocks at least one invalid proposal
- UI shows real backend data, not static mock data

## Claim Rules

- Do not claim "Full Memory OS"; say "Memory OS Core".
- Do not claim "Live MultiAgent Society"; say "Deterministic Society Session".
- Do not claim "Autonomous execution"; say "read-only audit".
- Do not claim "AI-powered analysis" unless a model is actually involved and
  gated.
- Do not claim foundation is closed unless validation proves it.
- Do not claim implementation for Memory, AutoPilot, or Society before the
  relevant sprint completes.

## Gate Decisions

- After S0: if repo audit does not produce real directory scan output, add
  source inventory implementation to S2.
- After S2: if AutoPilot cannot produce parseable JSON report, simplify Society
  to static preview.
- After S3: if Society cannot consume live Memory/AutoPilot data, convert to
  static timeline.
- After S4: if all panels cannot render real backend data, keep only working
  panels and mark others future-gated.

## Relationship To Vision

`docs/AEGIS_VISION.md` defines long-term direction. This file defines the
Hackathon release claim boundary.
