# Aegis Current Mission

Decision: `AEGIS_CANONICAL_MISSION_DEFINED`

Date: 2026-06-12

## Mission

Aegis is a local-first, free-first AI Mission Control system for Windows-first
operator automation, runtime truth, and bounded AI assistance.

Aegis should help a user inspect local state, understand risk, plan work, ask
for approval when needed, execute allowed actions through governed capability
tiers, verify observable outcomes, and keep an auditable record of what happened.

## Product Direction

Aegis should become:

- powerful, not passive
- safe, not paralyzed
- user-friendly, not operator-hostile
- explicit about what it did and did not do
- honest about blocked, degraded, unknown, historical, and future-gated states
- useful without paid or external services by default
- extensible to optional APIs, MCP connectors, tools, and local or cloud models
  only after policy, privacy, capability, approval, evidence, and verifier
  gates exist

## Local-First And Free-First

The default Aegis experience should run locally and avoid paid dependencies.

- Local deterministic logic is preferred where it is enough.
- Local model providers are optional.
- Cloud APIs and paid connectors are optional future integrations, not core
  requirements.
- External services must never become hidden fallback paths.
- Private local context must not be routed externally without explicit future
  policy and user approval.

## User Experience Principle

Aegis should expose a clear capability ladder:

1. Observe local state.
2. Explain what was observed.
3. Propose a plan.
4. Ask for approval when risk requires it.
5. Execute only allowed actions.
6. Verify observable effects.
7. Report limitations, failures, and evidence honestly.

The UI should feel like Mission Control for useful work, not a debug console for
internal contracts. Advanced diagnostics should remain available but should not
be the default user path.

## Memory Consent Principle

Memory must be useful without becoming surveillance.

- No silent long-term memory write by default.
- Memory candidates should enter an inbox or review queue.
- Low-risk project preferences can be batched.
- Private or sensitive memory requires explicit approval.
- Secret-like and credential-like content is blocked.
- Retrieved memory is context, not truth or permission.

## Model, API, And MCP Connector Principle

Models, APIs, and MCP connectors can improve Aegis, but none of them are
authority.

- Model output is proposal-only.
- Provider availability is not permission.
- Tool or MCP metadata is not execution permission.
- Paid/external connectors require explicit policy, credentials, privacy, and
  approval gates.
- No hidden cloud fallback is allowed.

## What Aegis Currently Is

Aegis currently includes:

- governed command runtime and verifier surfaces
- read-only maintenance diagnostics
- local Memory OS core with explicit lifecycle operations
- AutoPilot read-only repository structure audit
- deterministic Society Session proposals
- local Model Gateway for explicitly configured LM Studio/OpenAI-compatible
  endpoints
- static Skill Registry metadata catalog
- proposal-only Bounded Agent Runtime
- Next.js/Electron unified operator workspace with one composer, response
  drafts, secondary tools, and backend-owned route preview metadata

## What Aegis Is Not Yet

Aegis is not yet:

- a full autonomous agent runtime
- a general MCP runner
- a plugin marketplace
- a cloud model router
- a production security certification system
- a vector memory/RAG system
- a full repo-audit source ingestion platform
- a CodingAgent mutation platform
- a finished end-to-end operator product with durable conversation lifecycle
  and complete accessibility coverage

## Near-Term Product Direction

Near-term product work should prioritize:

- generated drift hygiene and canonical documentation
- operator conversation lifecycle and read-only explanation improvements
- Intent Router / Capability Broker
- real read-only capability execution
- Memory Inbox and consent UX
- keyboard accessibility and broader Electron rendered QA
- model-assisted explanation through Model Gateway
- agent-to-skill proposal flow before execution
- historical evidence/replay debt closure through explicit operator gates

## Acceptance Rule

A future sprint is not accepted if it only adds skeletons, metadata, docs, or
future-gated placeholders unless it is explicitly declared as an audit,
checkpoint, or readiness sprint.
