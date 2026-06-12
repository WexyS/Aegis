# Model Lifecycle / VRAM Budget Design
## 1. Decision

- Decision: `MODEL_LIFECYCLE_BUDGET_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T03:18:00+03:00`
- Repository checkpoint before sprint: `5890db8c4d5f5315ee4142ac89dc66c3619f3b95`
- Foundation tag: `foundation-baseline`

This sprint defines the future model lifecycle and resource budget contract. It
does not load, unload, call, probe, download, install, move, delete, route, or
execute any model. It does not implement a `ModelManager`, model router,
provider health probe, generation endpoint, chat surface, intent classifier,
embedding/reranking path, STT/TTS/VLM behavior, memory mutation, dataset export,
adapter, or runtime behavior change.

## 2. Lifecycle State Model

Core rule: no model lifecycle state grants execution permission, approval,
evidence, verifier success, lease, capability, policy authority, or runtime
authority.

| State | Can generate? | Grants permission? | Routable? | Required metadata/checks | Allowed transitions | Forbidden transitions | Audit/failure expectation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `unregistered` | no | no | no | none | `registered_metadata_only`, `disabled` | direct load/generation | record unknown model request if referenced |
| `registered_metadata_only` | no | no | no | provider/model metadata, provenance | `cold`, `unavailable`, `disabled`, `blocked_by_disk_pressure`, `blocked_by_policy`, `blocked_by_privacy` | generation without provider/resource checks | metadata source and staleness |
| `unavailable` | no | no | no | provider health failure | `cold`, `disabled`, `quarantined` | route as usable | structured provider failure |
| `disabled` | no | no | no | operator/policy disable reason | `registered_metadata_only` by explicit review | silent enable | disable audit |
| `cold` | no | no | policy/resource candidate only | provider reachable, model present, budget estimate | `loading`, `disabled`, `unavailable`, `blocked_by_*` | generation before load | readiness assessment |
| `warm` | maybe metadata/cache only; no generation by state alone | no | candidate only | provider warm signal and budget | `loading`, `loaded`, `idle`, `unloading` | treating warm as success | warm-state observation |
| `loading` | no | no | no | load plan, VRAM/RAM/disk gate | `loaded`, `failed_load`, `blocked_by_vram_pressure`, `blocked_by_policy` | active generation during load | load start/end/failure |
| `loaded` | generation candidate only | no | yes only after policy/privacy/resource gates | observed load state, resource observation | `active_generation`, `idle`, `unloading`, `failed_generation` | task success, verifier success | load observation |
| `active_generation` | yes, if request gates pass | no | already selected | request refs, timeout, privacy, context refs | `idle`, `failed_generation`, `unloading` after cancel | hidden parallel generation | usage and timeout audit |
| `idle` | candidate only | no | yes if budget still valid | idle age, TTL, observed memory | `active_generation`, `unloading`, `unloaded` | hiding active work as idle | idle timestamp |
| `unloading` | no | no | no | unload plan and active-work check | `unloaded`, `model_unload_failed`, `quarantined` | assume success without observation | unload evidence/failure |
| `unloaded` | no | no | no | observed release state | `cold`, `loading`, `disabled` | generation while unloaded | unload observation |
| `failed_load` | no | no | no | failure state | `cold`, `disabled`, `quarantined` after review | retry loop without policy | structured failure |
| `failed_generation` | no for failed request | no | model may need review | failure state and request refs | `idle`, `unloading`, `quarantined` | fallback as success | structured failure |
| `blocked_by_disk_pressure` | no | no | no | disk gate result | `registered_metadata_only` after storage review | download/install/load expansion | resource blocker |
| `blocked_by_vram_pressure` | no | no | no | VRAM estimate/observation | `cold`, `registered_metadata_only` after budget review | load anyway | resource blocker |
| `blocked_by_policy` | no | no | no | policy decision | `registered_metadata_only` after policy change | bypass policy | policy blocker |
| `blocked_by_privacy` | no | no | no | privacy decision | `registered_metadata_only` after privacy approval | remote fallback | privacy blocker |
| `quarantined` | no | no | no | operator or system quarantine reason | `disabled`, `registered_metadata_only` after review | automatic route/load | quarantine audit |
| `deprecated` | no by default | no | no | replacement/deprecation reason | `disabled`, `registered_metadata_only` by review | silent production use | deprecation audit |

## 3. Model Role Taxonomy

| Role | Likely model type | Latency sensitivity | VRAM/RAM sensitivity | Disk footprint | Privacy sensitivity | Output authority | Side-effecting? | Required gates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_primary` | instruct/chat LLM | high | medium/high | medium/high | medium/high | proposal only | no | provider, privacy, schema, policy |
| `intent_classifier` | small classifier/LLM | high | low/medium | low/medium | high | candidate intent only | no | parser/policy evals |
| `command_proposal` | instruct/planner LLM | medium | medium/high | medium/high | high | proposal only | no | no-execution tests, policy gates |
| `reasoning_planner` | reasoning LLM | medium/low | high | high | high | plan proposal only | no | planner schema, policy, approval gates |
| `coding_assistant` | code LLM | medium | high | high | high | patch suggestion only | no by output | source/ref/test gates |
| `translation_terminology` | translation/domain model | medium | medium | medium | medium/high | translated text only | no | glossary/eval/privacy gates |
| `memory_summarizer` | summarizer LLM | low/medium | medium | medium | very high | memory candidate only | no | Memory Governance required |
| `context_summarizer` | summarizer LLM | medium | medium | medium | high | summary only | no | Context Compiler contract |
| `embedding` | embedding model | medium/high | low/medium | low/medium | high | vector only | no | privacy/namespace gates |
| `reranker` | reranker model | high | low/medium | low/medium | high | ranking score only | no | retrieval governance |
| `vision_observer` | VLM | medium | high | high | very high | observation only | no | media privacy and visual evidence contract |
| `speech_to_text` | STT | high | medium/high | medium/high | very high | transcript candidate only | no | audio privacy and review gates |
| `text_to_speech` | TTS | high | medium | medium/high | medium/high | audio output candidate only | no | voice artifact policy |
| `voice_response` | LLM/TTS chain | high | medium/high | medium/high | very high | response candidate only | no | voice and model gates |
| `critique_evaluator` | evaluator LLM | low/medium | medium | medium | high | critique only | no | source refs/eval gates |
| `vertical_pack_specialist` | domain model | varies | varies | varies | varies | pack proposal only | no | pack-specific evals and policy |

Generation is not a side effect by itself, but generation output can propose
side-effecting work. Those proposals must still pass backend parser, policy,
capability, lease, approval, verifier, evidence, and journal gates.

## 4. Resource Budget Model

Future resource descriptors should include:

- `estimated_disk_gb`
- `actual_disk_gb`
- `estimated_vram_gb`
- `observed_vram_gb`
- `estimated_ram_gb`
- `observed_ram_gb`
- `context_window`
- `max_concurrency`
- `load_time_budget_ms`
- `generation_timeout_ms`
- `idle_ttl_seconds`
- `unload_grace_seconds`
- `priority`
- `eviction_class`
- `cache_policy`
- `provider_type`
- `local_or_remote`
- `privacy_class`
- `cost_class`

No live GPU metrics are collected in this sprint. Future VRAM/RAM observations
must be read-only, explicit about source, and treated as stale when old.

## 5. Budget Gates

| Gate | Rule |
| --- | --- |
| Critical disk | disk usage `>= 90%` blocks model download/install and local model expansion unless external storage is explicitly approved |
| Warning disk | disk usage `>= 80%` requires operator review before model expansion |
| Storage path | local model expansion requires explicit external model storage path |
| Large model load | requires VRAM/RAM budget proof before load |
| Multiple large models | denied unless budget proves simultaneous load is safe |
| Reasoning/coding/vision | default on-demand, unload after idle TTL |
| Chat primary | may stay warm only when budget proves it is safe |
| Embedding/reranker | separate lower-memory class; still privacy gated |
| STT/TTS/VLM | separately gated because media artifacts and model size differ |
| Remote provider | requires privacy/cost policy, not local VRAM proof |

Current state remains blocked for local model expansion because disk usage is
about `92.3%`.

## 6. Load and Unload Policy

- Model load is not generation success.
- Model load is not task success.
- Model unload must be observable in future implementation.
- Assuming unload success is forbidden.
- Model object references must be released in future implementation.
- GPU cache clearing alone is not sufficient proof of unload.
- Failed unload must be recorded as `model_unload_failed`.
- Idle TTL must not hide active work.
- Eviction must preserve audit, resource, and failure state.
- A loaded model still cannot grant permission, approval, evidence, verifier
  success, lease, or runtime authority.

## 7. Concurrency Policy

Initial future defaults:

- Max concurrent large local models: `1` unless budget proof explicitly allows
  more.
- Max concurrent generation per local provider: `1` by default for large
  models; small embedding/reranker models may define separate limits later.
- Queue if an operator-interactive request can wait within timeout.
- Reject with structured failure if queue delay would exceed timeout or budget.

Priority classes:

- `operator_interactive`
- `verification_related`
- `background_summary`
- `batch_generation`
- `vertical_pack_batch`

Rules:

- Operator-interactive work should not be starved by background batches.
- Verification-related analysis may be high priority, but model output remains
  non-verifier evidence.
- Cancellation must preserve partial/failure state.
- Retry must be bounded and must not hide the original failure.
- No concurrency implementation is added in this sprint.

## 8. Fallback Policy

- Fallback cannot erase the original failure.
- Fallback cannot convert failure to success.
- Fallback must preserve provider/model provenance.
- Fallback to a remote provider requires privacy and cost policy.
- Fallback to a smaller model must preserve quality/eval warning.
- Fallback to no-model response must be structured and honest.
- No silent fallback for side-effecting proposals.
- Fallback cannot make provider unavailable, timeout, OOM, policy blocked, or
  privacy blocked appear healthy.

## 9. Failure Taxonomy

Model lifecycle failures:

- `insufficient_disk`
- `insufficient_vram`
- `insufficient_ram`
- `provider_unavailable`
- `model_missing`
- `model_disabled`
- `model_load_timeout`
- `model_generation_timeout`
- `model_oom`
- `model_unload_failed`
- `context_too_large`
- `invalid_output_schema`
- `unsafe_output`
- `privacy_policy_blocked`
- `cost_policy_blocked`
- `policy_blocked`
- `unknown_error`

Failures are diagnostic records, not success evidence. They may become future
negative/eval candidates only after training governance review.

## 10. Evidence and Verifier Relationship

- Model generation is not execution evidence.
- Model output is not verifier success.
- Model load success is not task success.
- VLM output is future visual observation only, not verified success by itself.
- Evidence expectations remain backend-owned.
- Model lifecycle records can be diagnostics, not action verification.
- No model lifecycle event may mark missing, failed, or unknown-era evidence as
  verified.

## 11. Context Compiler Relationship

- Context packages can increase prompt size and resource pressure.
- `context_package_id`, source refs, source versions, and staleness markers
  should travel with future model request provenance.
- `raw_journal_included=false` remains the default.
- `known_debt_visible` and `unknown_era_preserved` must not be hidden from
  future model prompts, summaries, or outputs.
- Context truncation must be explicit and auditable.
- Context Compiler output remains non-authoritative and cannot pick models,
  grant permission, satisfy approval, or satisfy evidence.

## 12. Training Governance Relationship

- Lifecycle failures can become negative/eval candidates only after governance.
- OOM, timeout, unavailable, blocked, and failed unload states are not
  successful examples.
- Model outputs are `synthetic_unverified` unless validated.
- Provider logs are not automatic training data.
- Adapter use requires dataset, eval, resource, provenance, redaction, and
  rollback gates.

## 13. Memory Governance Relationship

- Memory summarization models must not write memory directly.
- Memory retrieval may affect context size and model selection, but retrieval is
  not permission.
- Memory namespace/privacy may restrict remote providers.
- Memory-derived routing suggestions are non-authoritative.
- Stale, conflicting, or quarantined memory cannot influence model selection as
  truth.
- Memory Governance is required before any persistent memory write path.

## 14. MCP / Tool Gateway Relationship

- Model/tool co-scheduling must not bypass policy.
- Tool-call capable model does not grant tool permission.
- Model lifecycle readiness does not imply MCP readiness.
- Tool outputs may increase context and resource pressure.
- MCP output must not override provider/privacy policy.
- Tool availability, MCP discovery, and plugin manifests remain non-authority.

## 15. Future API / Contract Sketch

Documentation-only contract names:

- `ModelLifecycleDescriptor`
- `ModelResourceBudget`
- `ModelLifecycleState`
- `ModelLoadPlan`
- `ModelUnloadPlan`
- `ModelEvictionDecision`
- `ModelLifecycleFailure`
- `ModelUsageBudgetRecord`

Common fields:

- `authority=false`
- `execution_permission=not_granted_by_model_lifecycle`
- `grants_approval=false`
- `grants_evidence=false`
- `grants_verifier_success=false`
- `provider_id`
- `model_id`
- `role`
- `lifecycle_state`
- `resource_estimates`
- `resource_observations`
- `policy_constraints`
- `privacy_constraints`
- `failure_state`
- `provenance_refs`
- `audit_refs`

These contracts are design-only until a later explicit implementation sprint.

## 16. Gates Before Model Lifecycle Implementation

Required gates:

1. Disk/resource pressure resolved or external model storage approved.
2. Model provider readiness contract accepted.
3. LLM authority boundary accepted.
4. Training governance accepted.
5. Context Compiler read-only contract accepted.
6. Privacy and redaction policy ready.
7. Provider metadata contract implemented.
8. Read-only provider health checks implemented and tested.
9. No-execution model output tests added.
10. Failure taxonomy tests added.
11. Timeout, OOM, unload, and fallback tests designed.
12. Lifecycle audit format designed.
13. No generated, model, dataset, adapter, screenshot, temp, or local
    environment artifacts staged.

No model lifecycle implementation should begin while these gates are absent.

## 17. Test Plan for Future Implementation

No tests are added in this documentation-only sprint because no type helper,
endpoint, provider probe, model call, or lifecycle manager is introduced.

When pure contract helpers are added, tests should assert:

- model lifecycle state does not grant execution permission
- provider/model ready does not grant permission
- loaded state is not generation success
- generation success is not verifier success
- timeout/OOM/unavailable remain failures
- fallback preserves original failure
- disk pressure produces `blocked_by_disk_pressure`
- VRAM pressure produces `blocked_by_vram_pressure`
- unload success requires observation
- model output cannot create approval, capability, lease, evidence, or verifier
  success
- no endpoint is probed and no model is called by contract tests

## 18. Non-Goals

- No model load or unload.
- No local or remote model call.
- No LM Studio/Ollama/OpenAI-compatible endpoint probe.
- No model download, install, move, or deletion.
- No model router.
- No model generation, chat, intent classification, embeddings, reranking,
  STT, TTS, or VLM behavior.
- No model lifecycle concept connected to execution, planning, tools, MCP,
  memory, plugins, skills, or vertical packs.
- No memory, journal, evidence, replay, snapshot, runtime, approval, policy,
  verifier, runtime health, backend, frontend, or API semantic change.
- No datasets, adapters, training exports, generated logs, fake metrics, fake
  health, fake evidence, fake verification, or benchmark claims.

## 19. Remaining Risks

- Disk usage remains critical around `92.3%`.
- No live GPU/VRAM inventory has been collected.
- Local model storage already uses about `31.82 GB`.
- Future provider logs, prompts, and context packages need privacy/redaction
  governance before use.
- Memory Governance and MCP/Tool Gateway readiness remain separate blockers.

## 20. Recommended Next Workstream

Recommended next prompt:

`Memory Governance / Memory OS Design`

Reason: model lifecycle planning now has provider, authority, context, training,
and resource boundaries. The next highest-risk non-execution design surface is
memory governance: memory must not become approval, permission, evidence, or
runtime truth.

Alternative:

`MCP/Tool Gateway Readiness`

Use this only if Memory Governance is intentionally deferred and gateway work
remains read-only, non-executing, policy-gated, and disconnected from runtime
dispatch.
