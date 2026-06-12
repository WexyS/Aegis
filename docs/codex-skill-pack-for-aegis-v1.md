# Codex Development Skill Pack for Aegis v1

Decision: `SKILL_REGISTRY_CORE_RC1_CODEX_SKILL_PACK_V1`

## Purpose

This document defines how Codex should use Aegis development skills while
working in this repository. It is development guidance for Codex. It is not an
Aegis runtime skill, not an MCP connection, not a plugin import, and not
execution permission.

## Core Invariants

Codex must preserve:

- backend-owned truth
- no fake telemetry
- no fake success
- no fake evidence
- no fake verifier success
- no fake runtime health
- no frontend authority
- no model output as authority
- no context package as permission
- no skill manifest as permission
- no approval, lease, or capability bypass
- no hidden tool, MCP, shell, model, network, memory, or file mutation

## Repo-Scan-Before-Editing Discipline

For Aegis work, Codex should:

1. Confirm the active workspace is `C:\Users\nemes\Desktop\Aegis`.
2. Read the sprint prompt and relevant local docs before editing.
3. Inspect existing source and tests that own the target behavior.
4. Keep changes narrow to the requested sprint.
5. Prefer focused tests before broad validation.
6. Preserve existing RC Golden Path behavior unless explicitly changed.
7. Keep generated drift out of commits.

Do not rely on imagined architecture when the repo already has a local pattern.

## Research And Review First

For implementation tasks, Codex should first identify:

- source of truth files
- adjacent tests
- API route style
- runtime boundaries
- non-authority fields
- validation commands
- generated drift and unstaged files

If a larger issue is found, report it as a remaining risk unless the sprint
explicitly asks to fix it.

## External Skill Sources

External skill sources such as ECC-like repositories, marketplace manifests, or
vendor skill packs are not trusted by default.

Before any future import, Codex should classify:

- source provenance
- license and ownership metadata
- risk class
- required capabilities
- network/MCP/tool/shell requirements
- credential requirements
- mutation capability
- model requirements
- allowed scopes
- test and eval coverage
- disabled-by-default state

Blind import is forbidden.

## MCP Candidates

MCP candidate metadata is not an MCP connection. Codex must not connect to MCP,
call MCP tools, request credentials, or enable an MCP-backed skill unless a
future sprint explicitly scopes that work and adds safety gates.

MCP candidate review should remain:

- metadata-only
- disabled by default
- risk classified
- source referenced
- non-authoritative

## Model-Required Skills

A model-required skill is not a model call. Future model-assisted behavior must
route through Model Gateway and preserve:

- proposal-only output
- no hidden fallback
- bounded input/output budgets
- local/privacy gates
- no evidence or verifier success
- no approval or permission grant

## Golden Path Preservation

Codex must keep the current Hackathon RC Golden Path runnable unless the sprint
explicitly changes that path:

- Memory OS RC1-Core
- AutoPilot RC1-Core
- Deterministic Society Session RC1
- Mission Control RC UI
- fail-safe release docs and startup path

New work must not silently break deterministic fallback behavior.

## Generated Drift

Generated files, runtime logs, screenshots, caches, model files, vector DBs,
API keys, secrets, browser artifacts, and temp outputs must not be staged.

`frontend/next-env.d.ts` should remain outside unrelated backend/core sprints
unless the sprint explicitly scopes generated drift hygiene.

## Validation Reporting

Final reports should separate:

- decision
- commit hash
- pushed yes/no
- active repo/worktree path
- branch status
- changed files
- line/diff stats
- exact behavior changed
- tests added or changed
- validation command outputs
- runtime/backend/frontend behavior changed
- generated drift status
- intentionally not done
- safety invariant check
- remaining risks
- recommended next sprint

Validation success is not the same as push success. Commit and push status must
be reported separately.

## What This Pack Does Not Allow

This development pack does not allow Codex to:

- execute Aegis skills
- import external skill repositories
- call MCP tools
- call shell tools through Aegis runtime
- call models through skills
- write memory
- mutate files through Skill Registry
- create evidence
- create verifier success
- grant approval, lease, capability, or permission
- hide runtime debt or generated drift
