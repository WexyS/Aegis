# Post-Foundation Architecture Roadmap
## 1. Decision

- Decision: `ROADMAP_DOCUMENTED_ONLY`
- Recorded at: `2026-05-31T22:07:19+03:00`
- Current repository checkpoint: `474f6d6ea6899f5a4de86be6472129a282849aa7`
- Foundation tag: `foundation-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This roadmap is design-only. It does not implement Context Compiler
integration, Memory OS, MCP Gateway, Model Router, plugin execution, capability
leases, cleanup execution, new tools, new agents, or runtime behavior changes.

## 2. Current Foundation State

Aegis has a Foundation baseline baseline accepted as
`READY_FOR_BASELINE_WITH_KNOWN_HISTORICAL_DEBT`. The baseline deliberately keeps
historical evidence debt, unknown-era evidence issues, replay diagnostics debt,
and resource warnings visible.

Current known operator state:

- Branch: `main`
- Latest known head: `474f6d6ea6899f5a4de86be6472129a282849aa7`
- Runtime health: `fail`
- Closure readiness: `needs_operator_attention`
- Current blocker count: `0`
- Current evidence failure count: `0`
- Current missing evidence count: `0`
- Pending decision hygiene: `ok`
- Pending count: `0`
- Restored pending count: `0`
- Historical evidence debt count: `18`
- Historical missing evidence count: `16`
- Unknown-era evidence issue count: `10`
- Replay diagnostics status: `fail`
- Replay boundary classification: `historical_mixed_sequence_eras_or_reset_boundaries`
- Replay cleanup execution blocked: `true`
- System resources: `warning`, with disk pressure around `92.1%`

Runtime health remains `fail` by design while visible historical, unknown-era,
replay, or resource debt remains. Post-foundation platform expansion has not
started. Existing Context Compiler code is a pure, non-executing skeleton; the
next Context Compiler work should be `Context Compiler Read-Only Integration
Readiness`, not another design skeleton.

## 3. Non-Negotiable Invariants

Every post-foundation module must preserve these boundaries:

- No backend truth bypass.
- No frontend-only authority.
- No policy bypass.
- No approval bypass.
- No fake evidence, fake verification, fake health, fake logs, or fake metrics.
- No verifier weakening.
- No journal mutation without an explicit boundary sprint.
- No cleanup execution without backup, restore, replay, hash-chain, and operator gates.
- No memory, retrieval, context, plugin, or model output may grant execution permission.
- No tool execution without capability policy, approval rules, and evidence expectations.
- No model, router, or provider choice without traceable provenance and failure state.
- No plugin or skill action without a manifest, risk tier, permission scope, rollback plan, and audit plan.
- Negative evidence remains failed or unverified evidence, never success.
- Missing evidence remains missing, never verified.
- Unknown-era evidence remains unknown unless trusted metadata proves otherwise.
- Read-only scan is not cleanup.
- Approval hygiene is not approval grant.
- Path presence is not launch proof.
- Title-only observation is not deterministic verification.
- Compiler output is context, not command truth.

## 4. Architecture Layers

### A. Runtime Truth Layer

Purpose: preserve backend-owned truth before any planning or expansion module can
influence execution.

Primary surfaces:

- RuntimeAuthority
- event journal
- command lifecycle
- evidence audit
- replay diagnostics
- maintenance scan
- verifier outputs

Rules:

- This layer is the source of truth for runtime state.
- New modules may read this layer through explicit contracts.
- New modules may not fabricate, suppress, or reinterpret truth from this layer.

### B. Policy and Capability Layer

Purpose: decide what is allowed before any tool, planner, model, or skill can
act.

Primary surfaces:

- policy-as-code
- risk-tier classification
- approval gates
- capability leases
- tool permissions
- execution scope

Rules:

- Approval is a lifecycle transition, not execution permission by itself.
- Capability grants must be scoped, temporary, revocable, and auditable.
- Side-effecting tools require explicit policy and evidence expectations.

### C. Context and Memory Layer

Purpose: produce bounded, provenance-aware context without granting authority.

Primary surfaces:

- Context Compiler
- Memory Governance / Memory OS
- provenance records
- quarantine and decay rules
- conflict resolution
- context budget
- audit trail

Rules:

- Context is not authority.
- Retrieval is not permission.
- Memory is not approval.
- Summary is not evidence.
- Raw runtime journal inclusion must remain opt-in and bounded.

### D. Tool and Gateway Layer

Purpose: provide explicit, policy-gated adapters for local tools and future MCP
connections.

Primary surfaces:

- MCP gateway
- local tool adapters
- app registry
- tool registry
- skill registry
- provider/tool adapters

Rules:

- Tool availability does not imply execution permission.
- App registry path presence is not launch proof.
- Tool calls require manifest metadata, risk tier, capability scope, and evidence expectations.

### E. Model and Planning Layer

Purpose: support planning and model selection while preserving runtime authority.

Primary surfaces:

- model router
- local-first provider support
- provider capability metadata
- critic / red-team critic
- planner
- task state machine

Rules:

- Model output is advisory until parsed, policy-checked, approval-gated, executed, verified, and journaled.
- Provider routing must preserve provenance and failure state.
- Planner steps must be reviewable before side effects.

### F. Skill / Plugin / Vertical Pack Layer

Purpose: make Aegis modular without turning modules into execution bypasses.

Primary surfaces:

- skill contracts
- plugin manifests
- vertical packs
- eval harnesses
- rollback and audit requirements

Rules:

- Skills and plugins start read-only or approval-gated.
- Every action family needs threat-model tests.
- Vertical packs must reuse generic contracts instead of hard-coding one narrow product direction.

### G. Operator UX Layer

Purpose: make backend truth understandable without becoming authority.

Primary surfaces:

- cockpit clarity
- maintenance/readiness views
- approval review
- evidence explorer
- audit views

Rules:

- The frontend renders backend truth.
- It may group or explain, but must not create frontend-only success or hide backend debt.
- Missing data must render as unavailable or unknown, not zero or success.

## 5. Recommended Implementation Sequence

### Phase 1: Post-Foundation Architecture Contracts

Preconditions:

- Foundation baseline remains present.
- Current blocker count remains separate from historical debt.
- Runtime health semantics remain unchanged.

Allowed changes:

- Docs and contract notes.
- Tests that assert boundary invariants.

Forbidden changes:

- Execution behavior, schema expansion, cleanup execution, plugin execution, or model routing.

Test requirements:

- Threat-model regression tests.
- Maintenance tests if contract wording references maintenance outputs.

Rollback plan:

- Revert docs/tests only.

Operator approval:

- Required before moving from contracts into any integration work.

Completion criteria:

- Boundaries and next module gates are documented and validated.

### Phase 2: Context Compiler Read-Only Integration Readiness
Preconditions:

- Existing Context Compiler skeleton remains pure and non-executing.
- Compiler output is explicitly non-authoritative.

Allowed changes:

- Inspect and document integration points for runtime snapshot, command lifecycle,
  policy boundary, evidence audit, maintenance scan, and frontend reference data.
- Add read-only tests for source references and permission-denial semantics.

Forbidden changes:

- Planner execution, command permission, memory mutation, policy bypass, or raw journal ingestion by default.

Test requirements:

- Context package tests proving `capability_grant=false` and
  `execution_permission=not_granted_by_context`.
- Negative assertions that frontend projection is never authority.

Rollback plan:

- Remove readiness docs/tests; runtime remains unaffected.

Operator approval:

- Required before any runtime API exposes compiled context.

Completion criteria:

- A read-only integration plan exists with no execution path.

### Phase 3: Policy-as-Code Extension
Preconditions:

- Current approval/policy/verifier tests pass.
- Existing policy boundary semantics are preserved.

Allowed changes:

- Formal capability/risk tier matrix.
- Policy contract docs and threat-model-as-tests.

Forbidden changes:

- Broad permanent permissions.
- Automatic approval grants.
- Policy exceptions hidden in frontend or plugins.

Test requirements:

- Policy boundary regression tests.
- Side-effecting tool dispatch contract tests.

Rollback plan:

- Revert policy docs/tests; existing runtime policy remains in force.

Operator approval:

- Required for every new capability family.

Completion criteria:

- Future capabilities have explicit policy gates before implementation.

### Phase 4: Capability Lease Design
Preconditions:

- Policy-as-code extension defines capability categories.
- Approval lifecycle remains backend-owned.

Allowed changes:

- Design temporary scoped permissions, expiry, provenance, revocation, and audit.

Forbidden changes:

- Permanent broad grants.
- Lease implied by memory, context, retrieval, frontend state, or model output.

Test requirements:

- Lease design tests only if read-only helper code is added.

Rollback plan:

- Revert lease design docs/helpers.

Operator approval:

- Required before any lease can authorize runtime dispatch.

Completion criteria:

- Lease contract is documented without execution wiring.

### Phase 5: MCP/Tool Gateway Readiness
Preconditions:

- Tool registry and policy contracts define risk and evidence expectations.
- Capability lease design exists.

Allowed changes:

- Read-only adapter contract design.
- Tool manifest validation plan.

Forbidden changes:

- Arbitrary untrusted tool execution.
- Gateway calls that bypass policy, approval, evidence, or journal.

Test requirements:

- Contract tests for manifest parsing, risk tiers, denied-by-default behavior, and provenance.

Rollback plan:

- Disable gateway registration; no runtime execution should depend on it.

Operator approval:

- Required before any gateway tool can execute.

Completion criteria:

- Gateway readiness plan proves deny-by-default behavior.

### Phase 6: Memory Governance / Memory OS Design
Preconditions:

- Context Compiler readiness confirms context is non-authoritative.
- Policy layer states memory cannot authorize execution.

Allowed changes:

- Provenance, quarantine, decay, conflict resolution, and audit design.

Forbidden changes:

- Memory graph execution authority.
- Memory overriding policy, approval, verifier, or evidence truth.

Test requirements:

- Design-level tests only if a read-only projection helper is added.

Rollback plan:

- Remove memory governance docs/helpers.

Operator approval:

- Required before memory writes or retrieval affects runtime prompts.

Completion criteria:

- Memory governance rules are defined before Memory OS implementation.

### Phase 7: Model Router Readiness
Preconditions:

- Policy/capability metadata exists for model families.
- Local-first provider goals are documented.

Allowed changes:

- Provider capability metadata design.
- Routing provenance and failure-state design.

Forbidden changes:

- Provider routing that bypasses policy.
- Model output treated as command truth.

Test requirements:

- Read-only routing metadata tests if helper code is added.
- Failure-state tests proving unavailable providers do not become success.

Rollback plan:

- Disable router registration; default provider path remains unchanged.

Operator approval:

- Required before router affects planning or execution.

Completion criteria:

- Routing cannot hide provenance, capability limits, or failure state.

### Phase 8: Skill/Plugin Architecture Design
Preconditions:

- Tool gateway, policy, and capability lease designs exist.
- Threat-model test pattern exists for new capability families.

Allowed changes:

- Plugin manifest, skill contract, risk-tiered action, evidence requirement, eval,
  and rollback design.

Forbidden changes:

- Plugin marketplace execution.
- Skill action without manifest, scope, policy, evidence, and audit.

Test requirements:

- Manifest validation tests.
- Denied-by-default execution tests.

Rollback plan:

- Remove plugin registrations; no runtime dependency on plugin execution.

Operator approval:

- Required per plugin and per side-effecting action family.

Completion criteria:

- Skill/plugin contracts are generic, provenance-aware, and policy-gated.

### Phase 9: Vertical Pack Prototypes, Read-Only First

Preconditions:

- Skill/plugin contracts are approved.
- Policy and evidence expectations are defined per pack.

Allowed changes:

- Read-only prototypes for:
  - Academic Translation Pack
  - Terminology Engine
  - Repo Audit Pack
  - Citation/Reference Checker
  - Document Risk Analysis Pack
  - Small Business Automation Pack
  - Content Production Pack

Forbidden changes:

- Write actions without explicit approval, evidence expectations, rollback, and pack evals.
- Narrow product-specific shortcuts that bypass generic contracts.

Test requirements:

- Pack-specific eval harnesses.
- Provenance and no-execution tests for read-only mode.

Rollback plan:

- Disable pack registration and preserve audit records.

Operator approval:

- Required before any pack can perform write, external, or system mutation.

Completion criteria:

- Each pack proves read-only utility before any approval-gated write path exists.

## 6. Immediate Next Prompt Recommendation

Recommended next prompt:

`Context Compiler Read-Only Integration Readiness`

Reason: the Context Compiler skeleton already exists and is explicitly
non-executing. The next safe step is to design and validate how it can read
runtime truth surfaces without becoming command authority, policy authority, or
memory authority.

Alternative:

`Policy-as-code Extension`

Use this alternative if the operator wants capability/risk policy contracts
formalized before any Context Compiler integration surface is exposed.

## 7. Explicit Paused Items

These remain paused after this roadmap:

- journal cleanup execution
- archive execution
- compaction execution
- Context Compiler runtime integration
- Memory OS implementation
- MCP execution gateway implementation
- Model Router implementation
- capability lease execution
- plugin execution
- skill execution
- vertical pack write actions
- autonomous task execution expansion
- app launch/focus/click expansion
- frontend authority expansion

## 8. Risk Register

| Risk | Current handling |
| --- | --- |
| Historical evidence debt remains visible | Keep classified as known debt; do not mark verified. |
| Unknown-era evidence remains unresolved | Keep unknown until trusted metadata proves era. |
| Replay diagnostics fail on mixed sequence/reset boundaries | Cleanup execution remains blocked. |
| Disk pressure around 92% | Treat as resource warning, not journal cleanup permission. |
| Bounded maintenance projections can drift | Use inventory documentation and avoid treating count drift as cleanup. |
| Frontend density can confuse operators | Continue clarity work without frontend-only truth. |
| Capability expansion can bypass truth boundaries | Require policy, approval, evidence, and journal gates before execution. |
| Memory/context can be misused as authority | Keep memory/context non-authoritative by contract and tests. |
| Plugin systems can become execution bypasses | Require manifest, risk tier, permission scope, audit, and rollback. |
| Model routing can hide provenance | Require routing metadata, provider capability, and failure-state reporting. |
| Tool gateway can become arbitrary execution | Deny by default and require capability leases plus evidence expectations. |
| Vertical packs can narrow Aegis prematurely | Build packs on generic contracts, read-only first. |

## 9. README Alignment Note

`README.md` is directionally aligned with the foundation principles, but it is
materially behind the latest post-foundation state. Recommended future README
updates:

- Link to `docs/foundation-baseline.md`.
- Link to this roadmap.
- Clarify that runtime health may remain `fail` after baseline because
  historical, unknown-era, replay, and resource debt remain visible.
- Replace the older near-term roadmap wording with the post-foundation sequence.
- Correct future Context Compiler wording to `Context Compiler Read-Only
  Integration Readiness`, because the skeleton already exists.

README was not changed in this sprint to keep the roadmap task docs-only and
narrow.

## 10. Validation Plan

Required validation for this documentation-only sprint:

- `git status --short --branch`
- `git rev-parse HEAD`
- `git log -1 --oneline`
- `git tag --list foundation-baseline`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest tests/test_runtime/test_threat_model_regression.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_core/test_maintenance.py -q`

No frontend build or full pytest is required unless code or frontend files are
changed.

## 11. Non-Goals

- No runtime, backend, frontend, policy, approval, verifier, evidence, replay,
  command lifecycle, or journal semantic changes.
- No cleanup, archive, compaction, rewrite, truncation, deletion, repair, or
  resequencing.
- No Context Compiler integration.
- No Memory OS, MCP Gateway, Model Router, plugin architecture, skill execution,
  vertical pack execution, or provider routing implementation.
- No generated artifacts, runtime logs, screenshots, or temp files.
