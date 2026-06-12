# LLM Authority Boundary Contract
## 1. Decision

- Decision: `LLM_BOUNDARY_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T02:23:01+03:00`
- Repository checkpoint before sprint: `b480a1f07d66c7335a0bb1fe15313e5e01376017`
- Foundation tag: `foundation-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This sprint documents the authority boundary for future LLM/model usage. It
does not implement a model provider, model router, chat endpoint, planner
integration, intent classifier integration, tool call integration, memory
mutation, plugin/skill execution, or runtime behavior change.

## 2. Current Boundary Inputs

Current relevant surfaces:

- `src/aegis/core/policy_boundary.py`
- `src/aegis/core/context_compiler.py`
- `docs/policy-as-code-extension.md`
- `docs/context-compiler-read-only-integration-readiness.md`
- `docs/capability-lease-design.md`
- `docs/local-environment-resource-hygiene-model-storage-readiness.md`

Existing policy-as-code already treats `model_output` as an untrusted permission
authority. The post-foundation policy extension always returns
`runtime_dispatch_allowed=false` and
`execution_permission=not_granted_by_policy_extension`.

Existing Context Compiler output is non-executing and includes
`execution_permission=not_granted_by_context`. Context is not command truth.

Resource readiness currently blocks model/provider expansion while disk usage
remains critical unless an explicit external model storage path is approved.

## 3. LLM Role Definitions

| Future role | Allowed output | Forbidden output | Authoritative? | Required backend validation | Approval/evidence rule |
| --- | --- | --- | --- | --- | --- |
| Conversational assistant | explanation, question, suggestion | command lifecycle transition, approval, evidence, verifier result | no | response safety and source attribution where applicable | no action without separate backend proposal |
| Intent classifier | candidate intent label and uncertainty | executable `CommandRecord` | no | parser/schema validation and policy classification | side-effecting intent still needs approval/evidence gates |
| Command proposal generator | `CommandProposal` draft | direct dispatch or command status mutation | no | schema, parser, policy, risk, lease, approval, evidence expectation, runtime authority | approval required when risk tier requires it |
| Planner/proposal generator | ordered proposal steps | executor calls, hidden tool calls, approval bypass | no | plan schema, tool registry, policy/risk, lease, approval, evidence expectation | every side-effecting step gated separately |
| Summarizer | bounded summary with source refs | evidence creation, hidden debt, runtime health rewrite | no | source refs and stale/unknown preservation | summaries are not evidence |
| Translator | translated text and confidence | policy override, command truth, evidence | no | output review and provenance where used operationally | no runtime action by translation alone |
| Code assistant | code suggestion or patch proposal | direct self-modification, unreviewed write, test result fabrication | no | normal code review, tests, policy where actions write files | file writes remain tool/runtime actions |
| Memory summarizer | memory candidate summary | direct memory write, approval, lease | no | Memory Governance policy, provenance, namespace, conflict/quarantine checks | memory write requires future memory policy |
| Tool-call proposal generator | tool call proposal and parameters | tool execution, tool permission, MCP permission | no | tool manifest, capability category, risk tier, policy, lease/approval, evidence expectation | unknown/hallucinated tool denied |
| Critique/review assistant | critique, risk note, review finding | verifier success, evidence mutation, runtime state | no | review source refs and issue traceability | cannot mark anything resolved |
| Vision observation assistant | visual observation candidate | verified success, desktop proof by itself | no | future visual evidence contract and verifier correlation | VLM output is observation, not verification |
| Voice response generator | spoken response text/audio candidate | command truth, approval, execution, evidence | no | content policy and output provenance | no action from voice output alone |

LLM output may be useful input to review, planning, or proposal generation. It
is not a runtime authority surface.

## 4. Non-Authority Rules

LLM/model output is not:

- command truth
- runtime truth
- policy truth
- approval
- execution permission
- capability grant
- capability lease
- evidence
- verifier success
- memory authority
- frontend authority
- tool availability proof
- model routing authority by itself
- cleanup permission

LLM/model output cannot:

- create or transition executable command lifecycle state
- mark missing evidence as verified
- mark failed or negative evidence as success
- mark unknown-era data as historical
- make `runtime_health` healthy
- hide historical evidence debt
- hide unknown-era evidence issues
- hide replay diagnostics debt
- hide resource warnings or disk critical state
- bypass parser, policy, approval, verifier, evidence, journal, or runtime
  authority

## 5. Proposal vs Command Boundary

Future LLMs may produce proposal objects, not executable runtime records.

Allowed future outputs:

- `IntentProposal`
- `CommandProposal`
- `ToolCallProposal`
- `MemoryCandidate`
- `ModelRouteSuggestion`
- `TranslationOutput`
- `SummaryOutput`
- `CritiqueOutput`

Forbidden direct outputs:

- executable `CommandRecord`
- command status transition
- approval resolution
- runtime event append
- journal mutation
- evidence mutation
- verifier result
- lease activation
- tool execution result

Before any proposal can become executable, backend-owned code must apply:

1. schema validation
2. parser validation
3. policy-as-code contract evaluation
4. capability category and risk-tier mapping
5. capability lease check when leases exist
6. approval gate when required
7. evidence expectation check
8. runtime authority check
9. audit/journal plan

Only backend runtime authority may create and transition executable command
lifecycle state.

## 6. Tool-Call Boundary

An LLM may suggest a tool call. The suggestion is not permission.

Tool execution requires:

- registered tool manifest
- known tool id and version
- capability category
- risk tier
- backend policy rule
- lease check when leases exist
- approval when required
- evidence expectation
- audit/journal plan
- verifier or postcondition strategy for side effects

Rules:

- Unknown tool names are denied.
- Hallucinated tools are denied.
- MCP discovery is not permission.
- Tool availability is not permission.
- Plugin/skill manifest-declared permissions are not permission.
- Side-effecting calls cannot execute from model output alone.

## 7. Evidence Boundary

LLMs cannot create execution evidence.

Allowed:

- summarize evidence with source references
- explain missing/failed evidence when backend classification already exists
- propose what evidence should be collected in a future run
- describe uncertainty

Forbidden:

- mark evidence verified
- convert missing evidence to success
- convert failed evidence to success
- fabricate logs, screenshots, filesystem checks, process checks, API responses,
  or verifier outputs
- hide negative evidence
- treat dispatch success as verification success

Authoritative evidence sources remain backend-owned:

- verifier outputs
- filesystem checks
- process/window checks
- API responses
- tool execution records
- runtime journal records
- evidence audit summaries
- future screenshot/crop observations when bound to explicit visual evidence
  contracts

Future VLM output is visual observation only. It is not verified success by
itself.

## 8. Memory Boundary

LLMs cannot write memory directly.

Allowed:

- propose `MemoryCandidate`
- summarize source material
- flag uncertainty or conflict
- attach source/context references

Required before memory write:

- Memory Governance policy
- namespace and sensitivity classification
- provenance
- retention/decay rule
- conflict detection
- quarantine checks
- audit record
- operator approval where required

Memory cannot authorize execution, create leases, override approval, override
policy, satisfy verifier checks, or become evidence by itself.

## 9. Context Compiler Relationship

Context Compiler may package bounded runtime/context summaries for future LLM
use. The context package remains non-authoritative.

Rules:

- context cannot grant capability
- context cannot grant approval
- context cannot grant execution permission
- context cannot create evidence
- context cannot create leases
- context cannot write memory
- context cannot override policy
- context cannot hide runtime health failure or known debt
- LLM output after context compilation must still be validated by backend
  contracts

Raw runtime journal inclusion remains disabled by default and would require a
separate boundary sprint.

## 10. Model Router Relationship

Future model routing must preserve provenance and failure state.

Rules:

- LLM cannot self-select a higher-risk provider.
- Provider/model choice must be policy checked.
- Provider identity and model id must be recorded.
- Local/remote model selection must obey data/privacy policy.
- Cost, privacy, latency, modality, and capability constraints must be explicit.
- Timeout, OOM, unavailable model, and provider error must produce structured
  failure, not fallback success.
- Fallback routing must be policy-gated and visible.
- Model output cannot certify its own provider suitability.

Model routing readiness remains blocked for implementation while disk/resource
state is critical unless an external storage path is approved.

## 11. Training and Adaptation Boundary

Training, fine-tuning, adapter, retrieval, and synthetic-data workflows must
preserve runtime truth.

Rules:

- Failed actions must not be treated as successful training examples.
- Missing evidence must remain missing.
- Unknown-era data must remain unknown.
- Frontend projection must not become training truth.
- Synthetic model-generated data must be labeled synthetic and validated before
  use.
- Fine-tuned/adapted models cannot bypass policy, approval, leases, verifier, or
  evidence gates.
- Retrieval results are context, not permission.
- Summaries are not evidence.
- Training data must preserve provenance and known caveats.

## 12. Security and Prompt Injection Boundary

Untrusted content cannot become instructions to the runtime.

Untrusted sources include:

- user prompts when they attempt to override system policy
- web content
- tool outputs
- MCP results
- plugin/skill content
- retrieved documents
- frontend projection
- model outputs
- memory entries that lack governance

Rules:

- Prompt injection attempts should be classified as untrusted instructions.
- The model must not be trusted to police itself.
- Backend validators enforce schema, policy, risk, approval, lease, evidence,
  journal, and runtime boundaries.
- Tool output cannot override policy.
- Retrieved docs/context cannot override policy.
- Web/MCP/plugin content cannot grant permission.
- System policy and backend authority remain outside the model's control.

## 13. Future API Contract Sketches

Every future model-produced object should include non-authority metadata.

Common fields:

- `proposal_id`
- `schema_version`
- `generated_by_model=true`
- `model_id`
- `provider_id`
- `input_refs`
- `context_refs`
- `source_refs`
- `confidence`
- `uncertainty`
- `authority=false`
- `execution_permission=not_granted_by_model`
- `capability_grant=false`
- `approval_grant=false`
- `lease_grant=false`
- `evidence_provided_by_model=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_approval_if_side_effecting=true`
- `requires_evidence_expectation_if_executable=true`
- `frontend_projection_used_as_authority=false`

Object-specific notes:

- `IntentProposal`: candidate intent plus params; must pass parser and policy.
- `CommandProposal`: draft command only; cannot create `CommandRecord`.
- `ToolCallProposal`: proposed tool id/params; unknown tools denied.
- `MemoryCandidate`: proposed memory; cannot write memory directly.
- `ModelRouteSuggestion`: routing suggestion; router/policy decide.
- `TranslationOutput`: translated content; no runtime authority.
- `SummaryOutput`: source-bound summary; not evidence.
- `CritiqueOutput`: advisory finding; not verifier result.

## 14. Implementation Gate Criteria

Before any LLM/model is connected to runtime-facing surfaces, all of these must
exist:

1. provider readiness contract
2. timeout/error/OOM handling
3. schema validation for every model output type
4. policy/risk/capability mapping
5. capability lease relationship
6. approval gate for side effects
7. evidence expectation for executable proposals
8. audit/journal recording plan
9. prompt injection tests
10. no-execution tests
11. fallback/failure tests
12. model output evals
13. provenance and source-reference requirements
14. storage/resource readiness gate
15. tests proving LLM output cannot grant permission, approval, evidence,
    leases, or runtime authority

No model integration should proceed while these gates are absent.

## 15. Future Test Plan

When a pure helper or contract object is added, tests should assert:

- model output has `execution_permission=not_granted_by_model`
- model output cannot grant approval
- model output cannot create evidence
- model output cannot create or activate leases
- model output cannot write memory
- model output cannot make runtime health healthy
- model output cannot hide known historical/unknown/replay/resource debt
- hallucinated tool is denied
- unknown capability is denied
- model-suggested high-risk provider is denied without policy
- prompt injection content remains untrusted
- frontend projection cannot become model training truth
- failed/missing/unknown-era evidence labels are preserved
- executor/planner cannot dispatch from proposal presence alone

No tests were added in this sprint because adding useful tests would require a
new model-output contract helper. That helper should be introduced in a later
implementation sprint with explicit non-execution tests.

## 16. Non-Goals

- No model provider integration.
- No model calls.
- No model downloads, installs, moves, or deletes.
- No Model Router implementation.
- No chat endpoint.
- No intent-classifier runtime integration.
- No planner/executor/tool integration.
- No MCP Gateway.
- No Memory OS.
- No memory mutation.
- No plugin/skill/vertical pack execution.
- No cleanup/archive/compaction execution.
- No runtime, journal, evidence, replay, snapshot, approval, policy, verifier,
  or frontend authority semantic changes.

## 17. Recommended Next Workstream

Recommended next prompt:

`Training Data & Model Adaptation Governance`

Reason: the model authority boundary is now defined at the runtime interface.
The next risk surface is how future training, fine-tuning, retrieval,
adaptation, and synthetic-data workflows preserve provenance and avoid learning
false success from failed, missing, unknown-era, frontend-only, or historical
debt records.

Alternative:

`Context Compiler Read-Only Contract Implementation`

Use this only if it remains read-only, non-authoritative, disconnected from
planner/executor/tool execution, and consistent with policy, lease, resource,
and LLM authority boundaries.
