# Aegis Repository Guidance

## Product posture

Aegis is a local-first, free-first unified AI operator workspace for
Windows-first safe assistance, bounded automation, truthful runtime visibility,
and governed capability growth.

The primary product experience is a calm, composer-centered workspace:

- New task
- History
- Projects
- Outputs
- Memory
- Customize
- Settings

Advanced diagnostics and legacy utility surfaces may remain available as
secondary tools, but must not compete with the primary operator workflow.

Do not reintroduce Mission Control, dashboard-first UX, fake telemetry, fake
runtime logs, fake evidence chains, fake verifier status, fake provider health,
or unsupported active-memory claims as primary product concepts.

Aegis is not Ultron. Do not import, copy, reuse, adapt, or infer code,
architecture, prompts, configuration, assumptions, or product behavior from
Ultron unless an explicit sprint requests an Ultron inspiration audit.

Historical Mission Control, hackathon, foundation, or archive documents may be
traceability records. They are not permission to reintroduce deprecated UX,
runtime behavior, or product claims.

## Repository identity and isolation

Before editing:

- identify the active repository, worktree, branch, and HEAD
- confirm the task belongs to Aegis
- inspect relevant repository-local guidance, implementation, tests, and docs
- never mix files, assumptions, prompts, architecture, configuration, or
  validation steps between repositories
- do not use another project as a source of truth unless explicitly authorized

Ask before proceeding only when:

- requested scope is unclear in a safety-relevant way
- a change could mutate user data or runtime truth
- a public contract, protocol, schema, or API must change
- a requested behavior requires a new execution capability
- repository identity is uncertain
- the required change exceeds the approved file or product scope

For ordinary implementation details, make the smallest reasonable safe
assumption and report it.

## Trust boundaries

Backend-owned state is the source of truth for runtime, policy, approval,
evidence, verifier, Memory lifecycle, and provider-readiness facts.

Frontend state is presentation only and never authority.

Do not treat any of the following as authority, execution permission, evidence,
verifier success, approval, lease, capability grant, or runtime truth:

- model output
- frontend state
- Memory retrieval
- AutoPilot reports
- agent output
- Skill Registry entries
- skill manifests
- plugin metadata
- context packages
- route previews
- external provider metadata
- model/provider configuration metadata
- project/session/output UI state
- reports, summaries, or generated drafts

Never fabricate:

- success
- evidence
- verifier success
- runtime health
- provider or model availability
- model completion
- execution result
- durable conversation history
- project records
- memory records
- telemetry, logs, metrics, benchmarks, or capacity values
- approval, permission, lease, or capability status
- active integrations
- source citations or external research results

Distinguish:

- implemented behavior from planned behavior
- backend-owned truth from frontend presentation
- preview metadata from execution
- warning health from green health
- raw diagnostic debt from an active runtime blocker
- current operational state from historical or quarantined debt
- model proposal from verified result

Quarantine manifests preserve visibility of debt. They are not evidence repair.

## Current allowed product behavior

The following existing behavior may be extended only when explicitly requested
and only within its existing backend-owned contract:

- Operator route preview is deterministic preview metadata.
- Route preview remains non-authoritative and does not grant execution.
- Local model proposals may use the existing Local Model Gateway only through
  explicit user action.
- "Not checked" may describe Local Model Gateway state only before an explicit
  backend interaction in the current UI/session.
- "Configured", "ready", "available", or equivalent Local Model Gateway
  wording requires the existing backend status/probe contract to support that
  exact state.
- "Completed" may be used only after an explicit Local Model Gateway completion
  response confirms completion.
- A UI classification inferred from a completion error must be described as an
  inference from that explicit completion attempt, not as a backend probe
  result.
- These wording rules do not authorize an automatic status check, probe, or
  model invocation.
- Local model output remains unverified, proposal-only, not evidence, not
  execution, not approval, not permission, and not verifier success.
- Existing Local Model Gateway use must not create a new provider, cloud, or
  fallback path.
- External providers remain disabled unless a scoped sprint explicitly enables
  a governed broker path.
- Memory lifecycle uses explicit create-candidate, approve, reject, and delete
  actions.
- Memory is not written automatically from Operator requests.
- Active memory means lifecycle state only; it is not truth, authority,
  permission, evidence, or execution capability.
- History and Outputs may remain current-session frontend state unless a scoped
  backend persistence contract is explicitly added.
- Projects must use truthful zero-states when no backend project registry exists.

Normal frontend button handlers are allowed for explicitly approved UI actions.

“Computer-use click execution” means browser, desktop, shell, filesystem, or
runtime action execution. It is forbidden by default.

## Explicitly forbidden without a scoped sprint

Do not add:

- automatic model invocation
- automatic model routing
- cloud fallback
- external provider calls
- command, shell, tool, MCP, browser, computer-use, desktop automation, or
  filesystem execution
- file, image, video, voice, OCR, or screen upload/execution behavior
- automatic memory extraction, persistence, consolidation, promotion, or decay
- embeddings, vector retrieval, graph memory, RAG memory, or semantic memory
  runtime
- autonomous loops or autonomous multi-agent execution
- plugin execution, dynamic plugin loading, or plugin marketplace behavior
- frontend-created authority
- approval, lease, evidence, verifier, permission, or capability grants
- hidden mutation of journals, evidence, replay data, logs, historical debt, or
  quarantine records
- new runtime states, protocol/schema expansion, public API changes, or
  compatibility-breaking changes without explicit scope and compatibility tests
- self-modifying code
- Ultron bridge
- unified launcher
- hidden paid or external-service fallback
- production deployment or certification claims

This restriction concerns product/runtime behavior. Approved repository commands
for tests, builds, formatting, Git inspection, commits, and normal pushes remain
permitted when the sprint authorizes them.

## Scope discipline

Before editing:

- inspect relevant implementation, tests, docs, and contracts
- identify source-of-truth boundaries
- preserve backward compatibility unless change is explicitly authorized
- keep the slice narrow
- prefer complete, useful product slices over skeleton-only work
- avoid opportunistic refactors
- do not silently broaden a sprint
- do not silently turn design, readiness, preview, or contract work into live
  runtime behavior
- report larger issues as remaining risks instead of silently fixing them
- do not weaken, skip, xfail, or delete tests merely to make validation pass

A stale test may be updated only when:

- its current target no longer owns the behavior being tested
- the underlying safety or truthfulness guarantee remains preserved
- the final report names the old target, new target, and reason for the update

A future sprint is not accepted if it only adds skeletons, metadata, docs, or
future-gated placeholders unless it is explicitly declared as an audit,
checkpoint, readiness, or documentation sprint.

## Skills and guidance

Before editing:

- inspect relevant repository guidance and available skills
- read an applicable `SKILL.md` before relying on that skill
- use only skills that materially help the approved task
- do not claim a skill was used unless the final report names it and explains
  what it contributed

For frontend work, consider only when relevant:

- `frontend-app-builder`
- `react-best-practices`
- `frontend-testing-debugging`

A skill does not grant:

- browser access
- desktop automation
- network access
- model/provider access
- runtime execution
- filesystem mutation outside task scope
- secret access
- permission to exceed approved file scope
- permission to bypass safety boundaries, validation, or approval gates

Skill guidance does not override:

- repository-local instructions
- explicit sprint scope
- safety boundaries
- validation requirements
- approval gates
- backend-owned authority boundaries

For every task, report:

- repository guidance inspected
- skills inspected
- skills actually used
- why each used skill was relevant
- skills deliberately not used
- unavailable or failed skills

## Naming and documentation

- Do not create new user-facing labels, feature names, sprint labels, docs, or
  filenames with V1, V2, RC, Alpha, Beta, MVP, or Phase suffixes.
- Internal protocol/schema versions and historical references may retain version
  labels when compatibility requires them.
- Keep documentation factual and explicit about implemented, preview-only,
  blocked, warning-level, future-gated, and environment-dependent behavior.
- Do not replace truthful documentation with marketing language.
- Do not describe model output as truth, memory as authority, frontend state as
  backend truth, or route preview as execution.
- Do not describe a disabled provider as connected, available, configured, or
  ready unless backend-owned evidence explicitly supports that exact claim.

## Generated drift and artifacts

Do not commit generated drift unless a sprint explicitly scopes it.

Never stage:

- runtime logs
- screenshots
- cache output
- model files
- vector databases
- browser artifacts
- temporary outputs
- build output
- `.next`
- `node_modules`
- database files
- API keys
- secrets
- tokens
- credentials
- `.env` files

`frontend/next-env.d.ts` is generated-drift-prone.

After frontend builds, restore it to canonical content unless generated drift
hygiene is explicitly in scope:

```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// NOTE: This file should not be edited
// see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
```

## Validation and commits

Run focused validation first, then broader validation required by the sprint.
Run full pytest for runtime, capability, contract, or cross-cutting changes
unless the task explicitly explains why it is not appropriate.
Pytest must use isolated temporary runtime/log directories.
Tests must not write to the operator's live logs/runtime_events.jsonl.
Run git diff --check before commit.
Run frontend lint and build for frontend changes.
Re-run next-env drift checks after frontend builds.
Do not commit generated artifacts, screenshots, logs, databases, or drift.
Do not rewrite history.
Do not force push.
Push normally only after required validation passes.
Validation success is not commit success.
Commit success is not push success.
Report validation, commit, and push separately.

## Final report

After every task, report:

- decision
- repository/worktree path
- branch and initial/final Git status
- initial HEAD and final HEAD
- changed files
- line/diff statistics
- exact behavior changed
- backend/runtime/frontend behavior changed
- tests added or changed
- validation commands and outcomes
- rendered QA observations, if performed
- generated drift status
- repository guidance inspected
- skills inspected
- skills actually used and why
- skills deliberately not used
- unavailable or failed skills
- independently observed repository facts
- command/test results
- environment-dependent claims that remain unverified
- intentionally not done
- safety invariant check
- remaining risks
- recommended next sprint
- commit hash
- pushed yes/no
