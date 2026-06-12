# Aegis System Integrity Audit

Decision: `AEGIS_SYSTEM_INTEGRITY_AUDIT_AND_CHECKPOINT_COMPLETE`

Date: 2026-06-12

Scope: repository-wide audit, checkpoint review, cleanup planning, and mission
realignment only. This document does not execute cleanup, rename files, rewrite
history, hide debt, create evidence, or change runtime behavior.

## Checkpoint Status

Active repository: `C:\Users\nemes\Desktop\Aegis`

Expected latest runtime foundation commit:
`81a3290a0bb7b6174ee776141e7a835e2fc1b74e`

Observed checkpoint:

- HEAD matched `81a3290a0bb7b6174ee776141e7a835e2fc1b74e` before this audit
  documentation was created.
- `main` was pushed to `origin/main` for the bounded Agent Runtime checkpoint.
- Annotated tag `hackathon-agent-runtime-foundation` was not created because
  the worktree was dirty from generated frontend drift.
- The only pre-existing dirty file was `frontend/next-env.d.ts`.
- `frontend/next-env.d.ts` was not staged and remains outside this sprint.

Focused validation before audit documentation:

- Agent Runtime core/API tests: passed.
- Skill Registry core/API tests: passed.
- Model Gateway core/API tests: passed.
- Policy boundary tests: passed.
- Threat model regression tests: passed.

## Current Mission

Aegis should be treated as a local-first, free-first AI Mission Control system.

Aegis should become powerful without becoming unsafe:

- deterministic logic where deterministic logic is enough
- local model support where useful and explicitly configured
- optional external APIs, tools, agents, and MCP connectors where policy allows
- real work through capability tiers
- explicit labels for what was done, not done, blocked, degraded, proposal-only,
  read-only, or future-gated
- no fake success, evidence, verifier success, approval, authority, capability,
  memory authority, or tool execution

The current repository contains both real bounded product slices and many
readiness-only contracts. The cleanup direction should reduce ambiguity between
those two categories.

## Trust Boundaries

These boundaries remain correct and must not be loosened by cleanup:

- Model output is proposal-only, not truth.
- AutoPilot report output is not evidence.
- Memory retrieval is not authority.
- Skill manifests are not permission.
- Agent Runtime proposals are not execution.
- Frontend state is not backend truth.
- Maintenance scan debt must remain visible.
- Missing evidence must not be fabricated.
- Unknown-era issues must not be guessed away.
- Paid or external services must not become required core dependencies.

## What Is Real Today

The audit found these implemented surfaces:

| Surface | Current reality | Classification |
| --- | --- | --- |
| Core command runtime | Backend-owned command lifecycle, policy gating, event journal, evidence and verifier surfaces exist. | keep as-is, continue hardening |
| Maintenance diagnostics | Read-only maintenance scan reports runtime health, evidence audit, replay diagnostics, resources, registries, and findings. | keep as-is |
| Memory OS | SQLite-backed local memory store exists with propose/approve/reject/delete/search lifecycle and explicit API/store calls. | real bounded product slice |
| AutoPilot | Real read-only local repository structure audit exists and scans supplied local roots under exclusions and limits. | real bounded product slice |
| Society Session | Deterministic role-session output exists from supplied AutoPilot report and memory refs. | proposal-only product slice |
| Model Gateway | Local LM Studio/OpenAI-compatible gateway exists, fail-closed by default, and can probe/complete only when explicitly enabled/configured. | real bounded local provider slice |
| Skill Registry | Static backend-owned skill metadata catalog exists. It has no execution endpoint. | metadata-only |
| External Skill/MCP candidates | Candidate metadata exists and remains future-gated or blocked. | metadata-only |
| Bounded Agent Runtime | Static agent profiles and deterministic process-local sessions exist. Output is proposal-only and model assistance is future-gated. | proposal-only |
| Frontend | Next.js/Electron Mission Control shell renders backend API and socket state. | product surface, needs redesign |
| Launcher | Starts backend, frontend, Electron, and local model health check. | useful but needs process-scope hardening |

## What Is Not Real Yet

These must not be marketed as completed execution:

- autonomous multi-agent runtime
- agent skill execution
- MCP connector execution
- plugin execution
- shell/file mutation through Agent Runtime
- model-driven planner authority
- cloud provider auto-routing
- context retrieval/RAG/vector execution
- memory graph intelligence
- repo audit source reading beyond AutoPilot read-only structure audit
- GitHub source fetching or cloning
- web research execution
- full capability broker
- user-friendly capability tier UI
- durable AutoPilot/Society session persistence
- production-grade frontend

## Major Area Classification

| Area | Classification | Finding | Cleanup action |
| --- | --- | --- | --- |
| `README.md` | update wording/docs only | Current text still centers Foundation v1 and Hackathon RC and under-represents Memory OS, AutoPilot, Model Gateway, Skill Registry, and Agent Runtime. | Rewrite as current product README with real/proposal/future sections. |
| `AGENTS.md` | update wording/docs only | Active priority still says Hackathon Release Candidate preparation. | Replace active priority with current mission and cleanup/productization guidance. |
| `src/aegis/main.py` | refactor later | API description says deterministic autonomous runtime platform and route comments keep RC naming. | Later wording cleanup only; avoid protocol or route contract churn. |
| Core runtime/evidence/policy modules | keep as-is | Safety contracts remain central and useful. | Do not refactor during docs cleanup. |
| Memory OS modules | keep as-is, productize UX later | Store/API is real and local, but consent UX needs Memory Inbox and batch review. | Implement memory consent UX sprint after docs cleanup. |
| AutoPilot modules | keep as-is, extend later | Read-only scanner is real and useful. Reports are not evidence and not durable. | Add capability broker/read-only product slice later. |
| Society modules | update wording/docs only | Deterministic session is useful but proposal-only. Naming remains RC/hackathon-specific. | Rename public docs/UI later; keep internal constants until migration plan. |
| Model Gateway modules | keep as-is, harden later | Local provider path is real but fail-closed by default. | Document as optional local model gateway, not cloud/model authority. |
| Skill Registry modules | keep as-is | Static metadata catalog is safe. | Add execution only through future capability broker. |
| Agent Runtime modules | keep as-is | Proposal-only runtime is preserved. It does not call models or tools. | Productize only after capability model is defined. |
| API routes | keep as-is | API exposes real and proposal-only surfaces. | Later route docs should label authority boundaries. |
| Frontend shell | requires follow-up product sprint | Current UI is dark, dense, RC-labeled, and operator-hostile for normal users. | Premium Mission Control redesign with backend truth preserved. |
| `frontend/next-env.d.ts` | generated drift | Tracked Next-generated file changes between `.next/types` and `.next/dev/types`. | Dedicated generated drift hygiene sprint. |
| `launch_aegis.bat` | refactor later | Contains a project-scoped process cleanup followed by global `taskkill /IM electron.exe`. | Narrow launcher process cleanup in a dedicated sprint. |
| `logs/` and `data/` | unsafe to change now | Local runtime artifacts are ignored but large; journal is hundreds of MB. | No deletion now. Use historical debt closure plan. |
| Tests | keep as-is | Broad validation exists and protects many safety boundaries. | Update only when cleanup changes public docs/contracts. |
| Readiness docs | rename to canonical name | Many public filenames use `v1`, `v2`, `RC1`, `readiness`, or `future`. | Rename with compatibility pointers in cleanup sprint. |
| Hackathon docs | obsolete/legacy | Useful historical record but not current mission. | Mark as legacy or move under a legacy/hackathon section. |

## Current Runtime Health Interpretation

Latest read-only maintenance scan during this audit:

- scan version: `maintenance-scan/1`
- read-only: true
- runtime health summary status: `fail`
- finding count: 7
- finding severity counts: 1 fail, 4 warning, 2 info
- current blocker count: 0
- current evidence failure count: 0
- current missing evidence count: 0
- pending decision blocker count: 0
- unknown-era evidence issue count: 25
- unknown-era missing evidence count: 19
- replay diagnostics status: fail
- replay boundary classification:
  `historical_mixed_sequence_eras_or_reset_boundaries`
- maintenance scan observed mutations: none

Interpretation:

- Current operational blockers were not found by the scan.
- Runtime health still fails because evidence audit, runtime snapshot alignment,
  and replay diagnostics remain attention surfaces.
- Unknown-era and replay debt must remain visible until closed through an
  explicit operator-gated process.

## Product And Architecture Gaps

The project has become too readiness-heavy. The safety work is valuable, but
future work should stop adding endless skeleton-only contracts unless the sprint
is explicitly an audit/checkpoint/readiness sprint.

High-value product gaps:

- no capability broker that turns user intent into safe real capability tiers
- no friendly Ask Aegis product slice
- no unified labels for real/read-only/proposal-only/future-gated actions
- no durable user-facing history for AutoPilot/Society outputs
- no Memory Inbox / consent review queue
- no polished Mission Control experience
- no agent-to-skill execution path under approval and capability gates
- no clean separation between legacy hackathon docs and current product docs
- no completed historical evidence/replay debt closure baseline

## UI/Product Weakness Summary

The current UI is functional but not good enough for the product mission:

- The sidebar still exposes `Hackathon RC` as a primary tab.
- The brand subtitle says `Runtime Core`, which reads like an internal debug
  tool instead of user-facing Mission Control.
- The Mission Control RC panel contains machine-specific default paths such as
  `C:\Users\nemes\Desktop\Aegis`.
- Several visible concepts are internal, stale, or overly technical for normal
  users.
- The interface leans dark/debug/cockpit-heavy and can feel cluttered instead
  of calm, premium, and useful.
- The UI does not yet guide users through capability levels: observe, explain,
  propose, ask approval, execute, verify.

The frontend must still preserve backend truth, debt labels, blocked states,
unknowns, verifier failures, and policy denials.

## README And Docs Realignment Plan

The README should become the canonical current entrypoint. It should state:

- what Aegis is now
- what it currently can do
- what it cannot yet do
- local-first and free-first principle
- optional external or paid connectors are not core
- core trust boundaries
- current modules and authority boundaries
- run instructions
- validation instructions
- roadmap toward real product slices

Docs should be reorganized into these canonical public areas:

- current mission: `docs/aegis-current-mission.md`
- architecture: `docs/aegis-architecture-realignment.md`
- capability model: `docs/capability-model.md`
- memory consent: `docs/memory-consent-policy.md`
- model gateway: `docs/model-gateway.md`
- skill registry: `docs/skill-registry.md`
- bounded agent runtime: `docs/bounded-agent-runtime.md`
- system integrity audit: `docs/system-integrity-audit.md`
- evidence/replay closure: `docs/historical-evidence-replay-debt-closure.md`

Hackathon docs should remain available as historical records, but they should
not be the current public product narrative.

## Naming Inventory And Rename Plan

Rule for future public docs: do not create new public-facing docs, feature
names, sprint labels, or filenames with suffixes such as `v1`, `v2`, `RC1`,
`RC2`, or `next`.

Historical commit tags, internal schema versions, event protocol versions,
runtime constants, database filenames, and tests may keep version labels until a
compatibility migration is explicitly scoped.

The following scan found the main old naming and readiness surfaces. No files
were renamed in this sprint.

| Current path/name | Proposed canonical path/name | References to update | Risk | Safe to rename now | Should remain legacy | Compatibility pointer needed |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` Foundation/Hackathon wording | keep path, rewrite current mission | README tests, docs links | medium | no | no | no |
| `AGENTS.md` Hackathon active priority | keep path, rewrite current priority | agent instructions | medium | no | no | no |
| `src/aegis/main.py` RC route comments | internal canonical comments later | API docs, tests if comments asserted | low | no | no | no |
| `frontend/src/features/sidebar/components/Sidebar.tsx` `Hackathon RC` | `Mission Control` / `Release Console` label | UI tests, screenshots | medium | no | no | no |
| `frontend/src/features/mission-control-rc` | canonical Mission Control feature path | imports, routes, tests | medium | no | no | yes |
| `docs/action-attribution-change-intelligence-contract-v1.md` | `docs/action-attribution-change-intelligence.md` | docs backlinks | low | no | yes | yes |
| `docs/aegis-architecture-realignment-v2.md` | `docs/aegis-architecture-realignment.md` | README, AGENTS, docs backlinks | medium | no | no | yes |
| `docs/audit-query-layer-readiness-v1.md` | `docs/audit-query-layer.md` | docs backlinks | low | no | yes | yes |
| `docs/autopilot-rc1-core.md` | `docs/autopilot.md` | README, hackathon docs | medium | no | no | yes |
| `docs/backend-timeout-event-projection-contract-v1.md` | `docs/backend-timeout-event-projection.md` | docs backlinks | low | no | yes | yes |
| `docs/bounded-agent-runtime-rc1.md` | `docs/bounded-agent-runtime.md` | README, docs, API docs | medium | no | no | yes |
| `docs/capability-lease-design-v1.md` | `docs/capability-model.md` | README, docs backlinks | medium | no | no | yes |
| `docs/codex-skill-pack-for-aegis-v1.md` | `docs/codex-skill-pack-for-aegis.md` | AGENTS, README, docs | medium | no | no | yes |
| `docs/compliance-evidence-pack-readiness-v1.md` | `docs/compliance-evidence-pack.md` | docs backlinks | low | no | yes | yes |
| `docs/context-compiler-read-only-contract-implementation-v1.md` | `docs/context-compiler.md` | README, docs backlinks | medium | no | yes | yes |
| `docs/context-compiler-read-only-integration-readiness-v1.md` | `docs/context-compiler.md` or legacy pointer | README, docs backlinks | medium | no | yes | yes |
| `docs/context-retrieval-provider-context-budget-v1.md` | `docs/context-policy.md` | docs backlinks | low | no | yes | yes |
| `docs/developer-work-passport-contract-v1.md` | `docs/developer-work-passport.md` | docs backlinks | low | no | yes | yes |
| `docs/external-api-sdk-readiness-v1.md` | `docs/external-api-sdk-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/first-local-provider-health-probe-design-v1.md` | `docs/local-provider-health-probe-design.md` | docs backlinks | low | no | yes | yes |
| `docs/foundation-3track-rc-readiness-inventory-v1.md` | legacy/hackathon inventory | README, docs backlinks | medium | no | yes | yes |
| `docs/foundation-baseline-v1.md` | legacy foundation baseline | README, sitemap, docs backlinks | high | no | yes | yes |
| `docs/foundation-config-dependency-hygiene-v1.md` | `docs/config-dependency-hygiene.md` | docs backlinks | low | no | yes | yes |
| `docs/frontend-design-system-playwright-visual-pipeline-readiness-v1.md` | `docs/frontend-visual-validation.md` | docs backlinks | low | no | yes | yes |
| `docs/github-discoverability-seo-v1.md` | `docs/github-discoverability-seo.md` | README, sitemap | medium | no | no | yes |
| `docs/github-source-connector-readiness-v1.md` | `docs/github-source-connector.md` | docs backlinks | low | no | yes | yes |
| `docs/HACKATHON_RC_SCOPE.md` | legacy hackathon scope | AGENTS, docs backlinks | high | no | yes | yes |
| `docs/hackathon-final-roadmap-v2.md` | `docs/hackathon-final-roadmap.md` | docs backlinks | medium | no | yes | yes |
| `docs/hackathon-final-sprint-sequence-v2.md` | `docs/hackathon-final-sprint-sequence.md` | docs backlinks | medium | no | yes | yes |
| `docs/hackathon-rc-claims-matrix.md` | legacy hackathon claims matrix | README, hackathon docs | medium | no | yes | yes |
| `docs/hackathon-rc-demo-runbook.md` | legacy hackathon demo runbook | README | medium | no | yes | yes |
| `docs/hackathon-rc-demo-script.md` | legacy hackathon demo script | README | medium | no | yes | yes |
| `docs/hackathon-rc-release-package-v1.md` | legacy hackathon release package | README, docs backlinks | high | no | yes | yes |
| `docs/hackathon-rc-validation-manifest.md` | legacy hackathon validation manifest | README | medium | no | yes | yes |
| `docs/historical-evidence-replay-debt-cleanup-design-v1.md` | `docs/historical-evidence-replay-debt-closure.md` | README, docs backlinks | high | no | yes | yes |
| `docs/historical-evidence-replay-debt-inventory-v1.md` | `docs/historical-evidence-replay-debt-inventory.md` | README, docs backlinks | medium | no | yes | yes |
| `docs/identity-tenant-scope-contract-v1.md` | `docs/identity-scope.md` | docs backlinks | low | no | yes | yes |
| `docs/legacy-router-model-call-boundary-guard-v1.md` | `docs/legacy-router-model-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/llm-authority-boundary-contract-v1.md` | `docs/model-authority-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/local-environment-resource-hygiene-model-storage-readiness-v1.md` | `docs/local-resource-hygiene.md` | docs backlinks | low | no | yes | yes |
| `docs/local-model-context-profile-eval-readiness-v1.md` | `docs/local-model-context-profile.md` | docs backlinks | low | no | yes | yes |
| `docs/local-model-inventory-role-mapping-readiness-v1.md` | `docs/local-model-inventory.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-check-readiness-v1.md` | `docs/local-provider-health.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-probe-api-runtime-wiring-readiness-v1.md` | `docs/local-provider-health-probe-api-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-probe-implementation-boundary-v1.md` | `docs/local-provider-probe-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-probe-live-localhost-design-gate-v1.md` | `docs/local-provider-probe-localhost-gate.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-probe-mock-transport-runner-v1.md` | `docs/local-provider-probe-mock-runner.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-health-probe-real-localhost-runner-v1.md` | `docs/local-provider-probe-localhost-runner.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-probe-maintenance-projection-api-readiness-v1.md` | `docs/local-provider-probe-maintenance-projection.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-probe-maintenance-projection-api-surface-v1.md` | `docs/local-provider-probe-maintenance-api.md` | docs backlinks | low | no | yes | yes |
| `docs/local-provider-probe-result-projection-maintenance-surface-readiness-v1.md` | `docs/local-provider-probe-result-projection.md` | docs backlinks | low | no | yes | yes |
| `docs/mcp-tool-gateway-readiness-v1.md` | `docs/mcp-tool-gateway.md` | docs backlinks | medium | no | yes | yes |
| `docs/memory-governance-memory-os-contract-v1.md` | `docs/memory-governance.md` | docs backlinks | medium | no | yes | yes |
| `docs/memory-governance-memory-os-design-v1.md` | `docs/memory-os-design.md` | docs backlinks | medium | no | yes | yes |
| `docs/memory-os-rc1-core.md` | `docs/memory-os.md` | README, docs backlinks | medium | no | no | yes |
| `docs/mission-control-dry-run-ux-contract-v1.md` | `docs/mission-control-dry-run-ux.md` | docs backlinks | low | no | yes | yes |
| `docs/mission-control-rc-ui.md` | `docs/mission-control-ui.md` | frontend/docs backlinks | medium | no | no | yes |
| `docs/model-auto-mode-provider-selection-contract-v1.md` | `docs/model-auto-mode.md` | docs backlinks | low | no | yes | yes |
| `docs/model-gateway-rc1-lm-studio.md` | `docs/model-gateway.md` | README, docs backlinks | medium | no | no | yes |
| `docs/model-lifecycle-vram-budget-design-v1.md` | `docs/model-lifecycle-resource-budget.md` | docs backlinks | low | no | yes | yes |
| `docs/model-provider-local-llm-readiness-v1.md` | `docs/model-provider-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/multiagent-society-session-rc1.md` | `docs/society-session.md` | README, docs backlinks | medium | no | no | yes |
| `docs/operator-browser-interstitial-classification-v1.md` | `docs/operator-browser-interstitials.md` | docs backlinks | low | no | yes | yes |
| `docs/operator-reliability-intent-browser-hardening-v1.md` | `docs/operator-browser-reliability.md` | docs backlinks | low | no | yes | yes |
| `docs/passive-observe-only-product-mode-readiness-v1.md` | `docs/passive-observe-mode.md` | docs backlinks | low | no | yes | yes |
| `docs/plugin-lifecycle-type-contract-v1.md` | `docs/plugin-lifecycle.md` | docs backlinks | low | no | yes | yes |
| `docs/plugin-manifest-drift-signature-readiness-v1.md` | `docs/plugin-manifest-drift-signature.md` | docs backlinks | low | no | yes | yes |
| `docs/plugin-manifest-type-contract-v1.md` | `docs/plugin-manifest-contract.md` | docs backlinks | low | no | yes | yes |
| `docs/plugin-persistence-review-store-readiness-v1.md` | `docs/plugin-review-store.md` | docs backlinks | low | no | yes | yes |
| `docs/policy-as-code-extension-v1.md` | `docs/policy-as-code.md` | README, sitemap, docs backlinks | medium | no | no | yes |
| `docs/policy-tool-simulation-dry-run-v1.md` | `docs/policy-tool-simulation.md` | docs backlinks | low | no | yes | yes |
| `docs/post-foundation-architecture-roadmap-v1.md` | `docs/aegis-architecture-roadmap.md` | README, sitemap, docs backlinks | medium | no | yes | yes |
| `docs/provider-interstitial-registry-v1.md` | `docs/provider-interstitial-registry.md` | docs backlinks | low | no | yes | yes |
| `docs/provider-probe-maintenance-surface-ui-readiness-v1.md` | `docs/provider-probe-maintenance-ui.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-dry-run-maintenance-surface-ui-readiness-v1.md` | `docs/repo-audit-maintenance-ui.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-pack-future-read-plan-helper-v1.md` | `docs/repo-audit-read-plan.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-pack-implementation-readiness-v1.md` | `docs/repo-audit-pack.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-pack-read-only-contract-v1.md` | `docs/repo-audit-read-only-contract.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-pack-read-only-inventory-runner-readiness-v1.md` | `docs/repo-audit-inventory-runner.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-pack-read-only-source-inventory-design-v1.md` | `docs/repo-audit-source-inventory.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-runner-backend-dry-run-api-readiness-v1.md` | `docs/repo-audit-dry-run-api.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-runner-dry-run-source-plan-projection-v1.md` | `docs/repo-audit-source-plan.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-runner-source-intake-integration-readiness-v1.md` | `docs/repo-audit-source-intake.md` | docs backlinks | low | no | yes | yes |
| `docs/repo-audit-runner-source-plan-ui-cli-dry-run-display-readiness-v1.md` | `docs/repo-audit-source-plan-display.md` | docs backlinks | low | no | yes | yes |
| `docs/runtime-state-timeout-safe-fallback-contract-v1.md` | `docs/runtime-timeout-fallback.md` | docs backlinks | low | no | yes | yes |
| `docs/runtime-surface-boundary-closure-v1.md` | `docs/runtime-surface-boundary.md` | docs backlinks | low | no | yes | yes |
| `docs/skill-plugin-architecture-design-v1.md` | `docs/skill-plugin-architecture.md` | docs backlinks | low | no | yes | yes |
| `docs/skill-registry-rc1.md` | `docs/skill-registry.md` | README, docs backlinks | medium | no | no | yes |
| `docs/SPRINT_SEQUENCE_HACKATHON_RC.md` | legacy hackathon sprint sequence | docs backlinks | medium | no | yes | yes |
| `docs/system-drift-integrity-monitoring-readiness-v1.md` | `docs/system-drift-integrity-monitoring.md` | docs backlinks | low | no | yes | yes |
| `docs/training-data-model-adaptation-governance-v1.md` | `docs/training-data-model-adaptation-governance.md` | docs backlinks | low | no | yes | yes |
| `docs/vertical-pack-framework-v1.md` | `docs/vertical-pack-framework.md` | docs backlinks | low | no | yes | yes |
| `docs/web-research-gateway-readiness-v1.md` | `docs/web-research-gateway.md` | docs backlinks | low | no | yes | yes |
| `docs/audit/*-readiness.md` | legacy audit readiness records or canonical audit notes | audit index/backlinks | low | no | yes | yes |
| `docs/design/*readiness*.md` | design notes without readiness/version labels | design backlinks | low | no | yes | yes |
| `docs/sitemap.xml` old version URLs | canonical GitHub Pages URLs | GitHub Pages build/SEO | medium | no | no | no |

Cleanup rule: rename high-visibility public docs first, keep legacy pointer
stubs, update README/sitemap/backlinks, run link checks, then rename lower-risk
readiness archives in batches.

## Historical Evidence/Replay Debt Closure Plan Summary

The closure model is documented in
`docs/historical-evidence-replay-debt-closure.md`.

Summary:

- Do not reconstruct missing historical evidence by guessing.
- Do not suppress unknown-era issues.
- Create an archived legacy manifest for old evidence/replay debt.
- Preserve a retired legacy baseline that remains inspectable.
- Create a clean current operational baseline only after backup, restore,
  replay, hash-chain, and operator gates pass.
- Maintenance scan should report archived legacy debt separately from active
  current blockers.

## Memory Consent Policy Summary

The consent model is documented in `docs/memory-consent-policy.md`.

Summary:

- No silent long-term memory write by default.
- Use a Memory Inbox / candidate queue.
- Batch review project preferences and low-risk candidates at meaningful
  boundaries.
- Require explicit approval for private, sensitive, or secret-adjacent content.
- Allow session/ephemeral memory only when disclosed and non-persistent.
- Retrieval is context, not authority.

## Cleanup Implementation Sequence

Recommended next cleanup order:

1. Canonical mission and README rewrite.
2. AGENTS active priority realignment.
3. High-visibility doc rename with compatibility pointers.
4. Generated drift hygiene for `frontend/next-env.d.ts`.
5. Historical evidence/replay debt closure preparation.
6. Launcher process-scope hardening.
7. Premium Mission Control UI information architecture.
8. Capability model and broker design for real work tiers.
9. Aegis Ask product slice.

## Future Work Acceptance Rule

A future sprint is not accepted if it only adds skeletons, metadata, docs, or
future-gated placeholders unless the sprint is explicitly declared as an
audit/checkpoint/readiness sprint.

Normal product sprints should deliver at least one of:

- real read-only capability execution
- real local-only model/proposal utility
- approved safe action with evidence and verifier checks
- clear user-facing workflow improvement
- measurable reliability or maintainability improvement

## Safe To Proceed

It is safe to proceed to an implementation cleanup prompt if that prompt stays
within the planned cleanup order and keeps the following constraints:

- no history rewrite
- no generated drift staging unless explicitly scoped
- no hidden runtime debt
- no fabricated evidence
- no cleanup/archive/compaction execution without the debt closure gates
- no broad runtime refactor during documentation cleanup
- no frontend authority
- no model/tool/MCP execution expansion without a capability and approval model
