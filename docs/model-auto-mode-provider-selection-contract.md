# Model Auto Mode / Provider Selection Contract
## Decision

- Decision: `MODEL_AUTO_MODE_PROVIDER_SELECTION_WITH_TESTS`
- Contract version: `model-auto-mode-provider-selection-contract/1`
- Implementation surface: `src/aegis/core/model_auto_mode.py`
- Test surface: `tests/test_core/test_model_auto_mode.py`
- Previous sprint: `CONTEXT_POLICY_PROVIDER_BUDGET_WITH_TESTS`

This sprint adds a pure Auto Mode provider/mode candidate contract. It does
not call models, load models, probe endpoints, validate API keys, read secrets,
authenticate providers, select a real provider for execution, send data
externally, retrieve context, retrieve memory, read repo files, query web,
generate embeddings, rerank, run inference, touch vector stores, wire runtime,
expose APIs, or change frontend behavior.

## Scope

Auto Mode classifies caller-supplied metadata and related pure decisions into a
non-authoritative `selection_mode`. It may name a provider or model candidate,
but candidate metadata is not provider selection and never execution
permission.

Every `ModelAutoModeDecision` preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_model_auto_mode`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_auto_mode=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `model_call_performed=false`
- `model_loaded=false`
- `endpoint_probed=false`
- `provider_authenticated=false`
- `cloud_api_called=false`
- `api_key_validated=false`
- `secret_read=false`
- `context_retrieval_performed=false`
- `memory_retrieval_performed=false`
- `repo_file_read_performed=false`
- `web_query_performed=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `inference_performed=false`
- `vector_index_touched=false`
- `provider_selected=false`
- `data_sent_external=false`
- `auto_mode_execution_allowed=false`
- `cloud_routing_allowed=false`
- `local_model_routing_allowed=false`
- `output_is_authority=false`

## Why Auto Mode Exists

Aegis will eventually support passive/no-model mode, local model mode, cloud
provider mode, and hybrid fallback modes. Auto Mode must choose the safest
useful candidate from task metadata, privacy, identity scope, memory
governance, context policy, policy-as-code, local model inventory, provider
status, cloud status, secret status, and resource status.

This contract prevents Auto Mode from becoming an unsafe router. It is a
classifier, not execution.

## Task Types

Supported task types:

- `maintenance_scan`
- `evidence_audit`
- `policy_validation`
- `repo_audit_readiness`
- `repo_audit_candidate_notes`
- `code_explanation`
- `architecture_review`
- `risk_analysis`
- `mission_control_wording`
- `tool_simulation_explanation`
- `documentation_summary`
- `translation_terminology`
- `context_retrieval`
- `context_reranking`
- `web_research_future`
- `document_analysis_future`
- `visual_analysis_future_gated`
- `audio_analysis_future_gated`
- `multimodal_analysis_future_gated`
- `voice_interaction_future_gated`
- `external_agent_oversight_future`
- `unknown`

Deterministic backend validation tasks default to `passive_no_model`:

- `maintenance_scan`
- `evidence_audit`
- `policy_validation`
- `repo_audit_readiness`

## User Preference Modes

Supported preferences:

- `auto`
- `passive_only`
- `local_only`
- `cloud_allowed`
- `local_first_cloud_fallback`
- `ask_each_time`
- `disabled`
- `unknown`

Preference is not permission. `cloud_allowed` cannot override privacy,
context, policy, identity, secret, region, terms, or provider status blockers.
`local_only` blocks cloud. `passive_only` blocks model candidates. `disabled`
blocks provider/model selection.

## Selection Modes

Supported selection modes:

- `passive_no_model`
- `local_model_candidate`
- `local_embedding_candidate`
- `local_reranker_candidate`
- `cloud_model_candidate_later`
- `hybrid_local_first_candidate`
- `hybrid_cloud_first_candidate_later`
- `ask_operator`
- `blocked_by_privacy`
- `blocked_by_policy`
- `blocked_by_context_policy`
- `blocked_by_memory_governance`
- `blocked_by_identity_scope`
- `blocked_by_provider_status`
- `blocked_by_region_or_terms`
- `blocked_by_secret_boundary`
- `blocked_by_resource`
- `blocked_by_unknown_metadata`
- `future_gated`
- `unsupported`

Candidate modes are metadata only. They do not select providers for execution,
call models, authorize context delivery, or permit external transfer.

## Provider Classes

Supported provider classes:

- `passive_backend`
- `lm_studio_local`
- `ollama_local_optional`
- `vllm_local`
- `openai_compatible_local`
- `cloud_provider_future`
- `mock_test_provider`
- `offline_disabled_provider`
- `unknown`

## Provider Status Model

Supported provider statuses:

- `offline_disabled`
- `metadata_only`
- `configured_metadata_only`
- `not_configured`
- `unavailable`
- `endpoint_unverified`
- `endpoint_available_unverified`
- `resource_blocked`
- `disk_pressure_blocked`
- `disabled_by_policy`
- `future_gated`
- `unknown`

`endpoint_available_unverified` does not prove provider health. Provider health
requires a later explicit health-check readiness sprint.

## Cloud Provider Status Model

Supported cloud statuses:

- `not_configured`
- `api_key_missing`
- `api_key_present_unverified`
- `region_blocked`
- `unsupported_region`
- `terms_unverified`
- `quota_unknown`
- `disabled_by_policy`
- `future_gated`
- `unknown`

`api_key_present_unverified` is not cloud permission. Region and terms blockers
block cloud candidate use.

## Secret Boundary

Supported secret statuses:

- `no_secret_required`
- `secret_missing`
- `secret_present_unverified`
- `secret_invalid_metadata_only`
- `secret_storage_unknown`
- `secret_disallowed`
- `unknown`

This sprint does not read secrets, validate API keys, authenticate providers,
or call cloud APIs.

## Resource Status Model

Supported resource statuses:

- `disk_ok`
- `disk_warning`
- `disk_blocked`
- `ram_ok`
- `ram_unknown`
- `vram_ok`
- `vram_unknown`
- `gpu_required_unknown`
- `resource_unknown`
- `resource_blocked`

Resource-blocked statuses block model candidates. Warnings and unknowns remain
metadata and do not prove model usability.

## Relationships

### Identity Scope

Private, private repo, personal, sensitive, and regulated context requires
Identity Scope. Blocked identity scope blocks Auto Mode.

### Memory Governance

Retrieval and reranking tasks require Memory Governance. Memory Governance
metadata does not retrieve memory and cannot authorize model routing.

### Context Policy / Provider Budget

Context-bearing tasks require Context Policy. Context budget metadata does not
authorize provider selection, retrieval, model calls, or cloud routing.

### Policy-as-Code Extension

Blocked or unsupported policy extension decisions block Auto Mode. Policy
proposal metadata is not execution permission.

### Local Model Inventory

Local Model Inventory metadata may provide local candidate role mappings, but
it does not authorize model calls or provider selection. Embedding models can
only be embedding candidates. Rerankers can only be reranker candidates.

### Future Provider Health Check

Provider status metadata does not prove health. A future health-check contract
must handle endpoint probing and provider availability, if explicitly allowed.

### Web Research Gateway

Web research remains future-gated until a Web Research Gateway policy exists.
Auto Mode does not query web or create web evidence.

### Document, PDF, and Multimodal Future Work

Document, PDF, visual, audio, multimodal, and voice tasks remain future-gated
until explicit privacy and modality boundaries exist.

## Current Model Role Map

These are cautious metadata examples only:

- Qwen2.5 Coder 14B: coding, repo-audit candidate notes, code explanation;
  proposal-only local candidate.
- DeepSeek R1 Distill Qwen 14B: reasoning, risk analysis, architecture review;
  proposal-only local candidate.
- Qwen3.5 9B: fast general explanation, Mission Control wording, summaries;
  proposal-only local candidate.
- GPT-OSS 20B: general fallback; quality/resource suitability unknown until
  later testing.
- text-embedding-baai-bge-m3-567M: embedding/context retrieval; not chat.
- Qwen3 embedding-class 0.6B: embedding/retrieval support; not chat.
- Qwen3 Reranker 0.6B: reranking/context precision; not chat.
- Gemma 4 12B: future-gated multimodal reasoning candidate; not active by
  default and requires Vision/Audio/Multimodal Privacy Boundary.
- Qwen3-VL 8B: previous/future-gated vision candidate if still present; not
  active by default.

No model is assumed installed, loadable, fast, healthy, safe, or available.

## Non-Authority Rules

- Auto Mode is not model execution.
- Auto Mode is not provider selection for execution.
- Auto Mode is not model-call authorization.
- Auto Mode is not context retrieval authorization.
- Auto Mode is not cloud permission.
- Auto Mode is not evidence.
- Auto Mode is not verifier success.
- Auto Mode is not approval.
- Auto Mode is not a lease.
- Auto Mode is not a capability grant.
- Auto Mode cannot override policy, context, memory, identity, or privacy
  boundaries.
- Model output remains proposal-only and never authority.

## Tests Added

Focused tests cover:

- passive/no-model deterministic backend tasks
- disabled and passive-only preferences
- Qwen2.5-Coder-like, DeepSeek-like, and Qwen3.5-like local candidates
- provider health absence preserving candidate-only status
- embedding and reranker candidate separation
- embedding/reranker rejection as chat candidates
- cloud preference blocked by private repo context
- local-only cloud blocking
- unknown sensitivity ask-operator path
- raw journal and secret/credential blockers
- raw evidence refs-only non-authority
- API key, region, and terms blockers
- future-gated visual/audio/multimodal/web/document/external-agent tasks
- Gemma 4 12B and Qwen3-VL future-gated multimodal handling
- unsafe related decision rejection
- missing context policy and missing local inventory blockers
- policy extension blockers
- memory/context budget non-authority
- model/provider/context/memory/web/vector behavior flag rejection
- authority, grant, evidence, verifier, frontend, and MCP claim rejection
- input and related decision immutability

## Intentionally Not Done

- No model calls.
- No model loading.
- No endpoint probing.
- No cloud API calls.
- No API key validation.
- No secret reads.
- No provider authentication.
- No provider selection for execution.
- No external data transfer.
- No context retrieval.
- No memory retrieval.
- No repo file reads.
- No web queries.
- No embeddings.
- No reranking.
- No inference.
- No vector DB access.
- No runtime/API/frontend wiring.

## Future Implementation Notes

Recommended next work:

- `Local Provider Health Check Readiness`

Alternative:

- `Capability Lease Design`

Provider health must remain separate from Auto Mode. Health checks, endpoint
probing, API key validation, and model calls require explicit future boundary
sprints with policy, evidence, verifier, identity, privacy, and operator gates.

## Remaining Risks

- Provider health is unknown until a later safe health-check contract exists.
- Resource suitability remains metadata-only.
- Cloud provider region, terms, secret storage, and quota remain unresolved.
- Multimodal/privacy boundaries are not implemented.
- Auto Mode candidate naming could be overtrusted by future UI if not labeled
  clearly as non-authoritative.
