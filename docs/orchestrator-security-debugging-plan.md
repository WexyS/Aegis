# Orchestrator Security Debugging Plan

Decision: `AEGIS_ORCHESTRATOR_SECURITY_DEBUGGING_PLAN_DEFINED`

## Scope

This is a future audit plan for Aegis Orchestrator work. It does not perform
the audit, mutate runtime state, call tools, call models, fetch networks,
create evidence, create verifier success, or change runtime health.

Each area below states why it matters, likely files or modules to inspect,
recommended validation, and what must never be claimed without backend
evidence.

## Generated Drift

Why it matters: generated or typo-path drift can pollute commits and hide real
source changes.

Likely files/modules:

- `frontend/next-env.d.ts`
- typo paths such as `rontend/next-env.d.ts`
- `.next/`
- screenshots, zips, logs, cache outputs

Recommended validation:

- `git status --short --branch`
- explicit ignored/generated artifact scan before commit
- `git diff --cached --check`

Never claim without backend evidence:

- that generated drift is product source
- that generated drift is intentionally committed

## Bridge And Socket Connectivity

Why it matters: bridge/socket warnings can make the UI look degraded or
untrustworthy.

Likely files/modules:

- `src/aegis/api/ws_bridge.py`
- `frontend/src/lib/socket.ts`
- `frontend/src/store/useRuntimeStore.ts`
- read-only bridge modules and launcher scripts

Recommended validation:

- browser console smoke
- websocket reconnect tests
- read-only bridge API tests
- no suppression of warnings without root cause

Never claim without backend evidence:

- websocket health is green
- bridge warnings are harmless
- runtime snapshot is fully synchronized

## Model Gateway Boundary And Prompt Privacy

Why it matters: local model prompts can leak private context or be mistaken for
truth.

Likely files/modules:

- `src/aegis/core/model_gateway.py`
- `docs/model-gateway.md`
- future context policy and model profile modules

Recommended validation:

- local-only URL validation tests
- mocked provider transport tests
- prompt budget and purpose tests
- negative tests for secrets, raw journals, and raw evidence

Never claim without backend evidence:

- model output is true
- model output is evidence
- model output is verifier success
- prompts are safe for private context

## LM Studio And OpenAI-Compatible Endpoint Validation

Why it matters: localhost-like URLs can be spoofed and endpoint status can be
confused with permission.

Likely files/modules:

- `src/aegis/core/model_gateway.py`
- model gateway API routes
- config settings

Recommended validation:

- URL canonicalization tests
- spoofed localhost rejection tests
- mocked probe and completion tests
- no live provider dependency in unit tests

Never claim without backend evidence:

- LM Studio is running
- a model is loaded
- endpoint availability grants permission

## Mode Policy Bypass

Why it matters: a mode label can become an accidental execution switch.

Likely files/modules:

- `src/aegis/core/mode_policy.py`
- future orchestrator/router modules
- frontend mode controls

Recommended validation:

- tests proving every mode returns `mode_allows_execution_now=false`
- negative tests for approval, lease, evidence, verifier, and dispatch flags

Never claim without backend evidence:

- Power or YOLO Lab grants execution
- a mode label overrides policy

## Integration Registry Drift

Why it matters: registry records can become stale, overclaim installation, or
lose upstream traceability.

Likely files/modules:

- `src/aegis/core/integration_registry.py`
- `docs/integration-landscape.md`
- future notice/license docs

Recommended validation:

- unique IDs
- required upstream refs and URLs
- no fake installed statuses
- all risky resource requirements non-executable

Never claim without backend evidence:

- an integration is installed
- an integration is ready
- an integration can execute

## License And Attribution

Why it matters: copying, vendoring, or redistributing third-party work without
review can create legal and maintenance risk.

Likely files/modules:

- integration registry
- future vendor directories
- future notice files
- docs referencing upstream projects

Recommended validation:

- license review checklist
- notice preservation tests if vendoring ever happens
- dependency and source provenance audit

Never claim without backend evidence:

- license compatibility
- vendoring permission
- attribution completeness

## Secrets And API Keys

Why it matters: provider keys and tokens can leak through config, memory,
context, logs, or screenshots.

Likely files/modules:

- config loaders
- launcher scripts
- read-only bridge scripts
- Model Gateway config
- future connector settings

Recommended validation:

- secret-pattern scans before commit
- `.env` and token path staging checks
- tests that reject credential-like context

Never claim without backend evidence:

- secrets are absent everywhere
- a connector is authenticated safely

## External API Egress Controls

Why it matters: Aegis is local-first and external calls must be explicit.

Likely files/modules:

- future provider/router modules
- context policy
- model gateway
- integration registry

Recommended validation:

- network-disabled tests for readiness modules
- explicit egress policy tests
- no hidden fallback tests

Never claim without backend evidence:

- cloud routing is allowed
- external API use happened safely

## Tool, Agent, Workflow, And Computer Gates

Why it matters: these are the surfaces most likely to create real-world side
effects.

Likely files/modules:

- `src/aegis/core/agent_runtime.py`
- `src/aegis/core/skill_registry.py`
- future flow engine modules
- executor and policy modules

Recommended validation:

- negative tests for shell/tool/MCP/process execution
- approval and lease boundary tests
- kill switch tests before computer control

Never claim without backend evidence:

- a tool ran safely
- an agent executed work
- a workflow completed
- computer control succeeded

## Filesystem Scope Enforcement

Why it matters: code assistants, workflow tools, and computer control can read
or write sensitive files.

Likely files/modules:

- executor
- policy boundary modules
- future code workforce modules
- repo audit source-intake modules

Recommended validation:

- path traversal tests
- workspace boundary tests
- no broad write tests

Never claim without backend evidence:

- arbitrary paths are safe
- filesystem writes are approved

## YOLO Lab Misuse Risk

Why it matters: high-autonomy mode can become a bypass if implemented casually.

Likely files/modules:

- `src/aegis/core/mode_policy.py`
- future orchestrator
- future UI controls

Recommended validation:

- kill switch tests
- timebox tests
- activity ledger tests
- explicit operator opt-in tests

Never claim without backend evidence:

- YOLO Lab is enabled
- YOLO Lab can bypass approvals

## Memory Silent-Write And Poisoning

Why it matters: memory can preserve wrong, sensitive, or malicious context.

Likely files/modules:

- `src/aegis/memory/store.py`
- memory governance modules
- memory consent UI

Recommended validation:

- no silent persistent write tests
- sensitivity and secret-blocking tests
- memory retrieval non-authority tests

Never claim without backend evidence:

- memory is truth
- memory write was consented
- retrieved memory grants permission

## Prompt Injection Through Integrations

Why it matters: external docs, tools, workflows, and model outputs can carry
instructions that conflict with Aegis policy.

Likely files/modules:

- future source connectors
- context policy
- model gateway callers
- integration registry

Recommended validation:

- hostile source text tests
- instruction hierarchy tests
- model output non-authority checks

Never claim without backend evidence:

- external text is trusted
- model output can override policy

## Upstream Dependency Compromise

Why it matters: external tools and packages can change independently of Aegis.

Likely files/modules:

- dependency manifests
- future adapter modules
- future vendored source

Recommended validation:

- pinned dependency review
- release provenance review
- no auto-update execution

Never claim without backend evidence:

- upstream packages are safe
- latest upstream is compatible

## Provenance And Audit Logs

Why it matters: future execution must be replayable and attributable.

Likely files/modules:

- event journal
- action timeline
- evidence audit
- future orchestrator execution modules

Recommended validation:

- event sequence tests
- hash-chain diagnostics
- provenance reference tests

Never claim without backend evidence:

- an action happened
- an action was caused by a specific integration

## Evidence And Verifier Boundary

Why it matters: proposal output and status metadata must not become proof.

Likely files/modules:

- verifier modules
- evidence audit modules
- runtime event journal
- Model Gateway and Agent Runtime envelopes

Recommended validation:

- negative tests for fake evidence fields
- verifier success provenance tests
- replay tests

Never claim without backend evidence:

- verifier success
- evidence creation
- policy success from model output

## Frontend Authority

Why it matters: the Mission Control UI must present backend truth, not invent
state.

Likely files/modules:

- `frontend/src/store/useRuntimeStore.ts`
- Mission, Advanced, Capabilities, and Settings surfaces
- socket client code

Recommended validation:

- rendered QA
- no fake status copy
- localization checks for warning/unknown states

Never claim without backend evidence:

- runtime health is green
- pending approvals are resolved
- an integration is ready or installed

## Test Isolation And Live Journal Mutation

Why it matters: tests must not mutate the operator runtime journal.

Likely files/modules:

- runtime journal
- pytest guards
- maintenance scan tests

Recommended validation:

- isolated temporary runtime dirs
- live journal append guard tests
- fingerprint comparison when needed

Never claim without backend evidence:

- tests are isolated if live journal writes occurred

## Raw Diagnostics Versus Active Blockers

Why it matters: Aegis can have raw historical debt while current blockers are
clear. Both facts must remain visible.

Likely files/modules:

- maintenance scan
- evidence audit
- replay diagnostics
- Advanced diagnostics UI

Recommended validation:

- raw and projection status tests
- historical/quarantined debt visibility tests
- no greenwashing UI checks

Never claim without backend evidence:

- raw fail is fixed
- historical debt is gone
- active blockers are zero when scan data is unavailable
