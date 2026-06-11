# Aegis Vision

## Decision

Decision: `AEGIS_VISION_DOCUMENTED_ONLY`

This document describes the long-term Aegis direction. It is not the Hackathon
implementation checklist. Hackathon RC scope is defined in
`docs/HACKATHON_RC_SCOPE.md`.

## Final Identity

Aegis is a local-first AI Mission Control Workspace: a trustworthy operating
surface for computer-operator workflows, source intelligence, memory,
policy-gated automation, and evidence-backed execution.

The long-term product should feel premium, responsive, and operator-friendly
without hiding runtime truth, unknowns, verifier failures, policy denials, or
historical debt.

## Local-First Mission Control Workspace

Aegis should default to local control where practical:

- backend-owned runtime truth
- local-first provider support
- explicit cloud and external routing gates
- clear provenance for actions, context, memory, models, and tools
- readable Mission Control surfaces for technical and non-technical operators

## Full Memory OS

The long-term Memory OS should support governed memory lifecycle management:

- proposal, approval, activation, quarantine, supersession, expiry, and deletion
- identity, namespace, tenant, project, and repository scope
- source refs and provenance
- sensitivity and retention policies
- conflict handling
- retrieval and context packaging with policy gates

Memory remains non-authoritative. It cannot grant permission, evidence,
verifier success, approval, lease, or capability.

## AutoPilot System

The long-term AutoPilot system should provide bounded audit, planning, and
operator assistance:

- read-only diagnostics
- source inventory and repo audit flows
- risk and readiness summaries
- recommended actions with policy boundaries
- approval-aware execution only after explicit future gates

AutoPilot output is not execution success, evidence, or verifier success.

## MultiAgent Society System

The long-term Society system may coordinate deterministic and model-assisted
roles for review, planning, critique, and explanation.

Future versions may include:

- deterministic session artifacts
- role-based review flows
- model-assisted critique
- policy-gated tool interaction
- traceable provenance and replay

Society output remains proposal-only until parsed, policy-checked,
approval-gated, executed, verified, and journaled by backend systems.

## MCP And Tool Gateway

Aegis may eventually support MCP and tool gateways with:

- manifest-based tool identity
- risk tiers and capability scopes
- approval and lease boundaries
- evidence expectations
- rollback and audit requirements
- strict separation between tool availability and tool permission

Tool metadata must never become execution permission by itself.

## Model And Provider System

Aegis should support passive/no-model, local model, and cloud model modes.

LM Studio and other local providers are priority candidates for local-first
operation. Cloud providers remain explicitly gated future options.

Provider routing should consider:

- privacy
- task type
- provider status
- local resources
- cost and latency
- region and terms status
- fallback policy

Model output is proposal-only.

## CodingAgent And Repo Control Plane

The long-term repo control plane may support:

- source intelligence
- repo audit
- change attribution
- patch planning
- review preparation
- controlled code modification

Full CodingAgent patch generation and mutation are future-gated and require
separate approval, evidence, verifier, and rollback boundaries.

## Source Intelligence

Aegis should safely understand source candidates from:

- local repositories
- GitHub source refs
- documentation
- release notes
- issues and pull requests
- web research outputs
- package metadata

Source refs are not proof. Public URLs are not automatically safe. Private data
must remain policy-gated.

## Document Workspace

Future document workflows may include:

- document/PDF extraction
- source citation management
- compliance and release packages
- developer work passports
- technical summaries

Document-derived context remains non-authoritative unless validated through
backend evidence and verifier contracts.

## Personal Productivity Packs

Aegis may grow into local productivity packs for:

- project memory
- daily planning
- release preparation
- engineering reviews
- source intelligence
- operational checklists

These packs must reuse policy, identity, memory, context, and evidence
contracts rather than bypass them.

## Premium Product Layer

The premium product layer should make trustworthy state easy to understand:

- polished single-page Mission Control
- clear status hierarchy
- responsive panels
- ambient but truthful motion
- no fake success
- no hidden debt
- no static mock data presented as live state

Frontend remains presentation only.

## Voice, Screen, And Multimodal Future

Voice, screen, OCR, accessibility execution, and multimodal workflows are future
directions. They require explicit privacy, policy, verifier, and evidence
boundaries before production use.

## Post-Hackathon Roadmap

After Hackathon RC, Aegis can expand through scoped, validated sprints:

- harden Memory OS beyond RC1-Core
- expand AutoPilot audit capabilities
- introduce controlled Society model assistance
- implement source intelligence execution gates
- add local provider integration after health and privacy gates
- add tool/MCP execution only after lease and evidence contracts are wired
- polish Mission Control without weakening backend truth

The vision is intentionally larger than the RC. The RC must only claim what it
actually implements and validates.
