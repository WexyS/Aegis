# Local Model Inventory / Role Mapping Readiness
## Decision

- Decision: `LOCAL_MODEL_INVENTORY_ROLE_MAPPING_WITH_TESTS`
- Contract version: `local-model-inventory-role-mapping-readiness/1`
- Scope: pure readiness helper, focused synthetic tests, and documentation
- Runtime dispatch: not allowed
- Execution permission: `not_granted_by_local_model_inventory`

This sprint defines a pure local model inventory and role-mapping contract for
future Aegis model/provider support. It does not load, call, probe, download,
install, move, delete, scan, inspect, route, or execute any model. It does not
wire model metadata into planner, executor, runtime, API, frontend, MCP, tools,
memory, approval, leases, evidence, or verifier truth.

## Scope

The helper accepts caller-supplied metadata only and returns a frozen
non-authoritative decision. It can describe provider class, provider status,
model role, model modality, task suitability, privacy/context policy, resource
metadata, Auto Mode eligibility metadata, limitations, and unknowns.

The inventory is not:

- model execution
- provider health proof
- endpoint reachability proof
- file existence proof
- model quality proof
- router decision
- execution permission
- approval, lease, or capability grant
- evidence or verifier success
- compliance, security, or audit proof

## Why Local Model Inventory Exists

Aegis will eventually support passive/no-model mode, local model mode, cloud API
model mode, and Auto Mode. Before any provider is called, Aegis needs a stable
metadata contract so chat models, coding models, reasoning models, embeddings,
rerankers, vision models, speech models, and disabled/offline providers are not
mixed together.

The contract preserves these boundaries:

- model availability is not permission
- model selection metadata is not authority
- model output is proposal-only
- embedding and reranker output is retrieval metadata only
- vision and audio roles require future explicit privacy gates
- local/private context routing must be explicit and policy checked
- Auto Mode eligibility metadata is not execution

## Provider Classes And Statuses

Provider classes:

- `lm_studio_local`
- `ollama_local`
- `vllm_local`
- `openai_compatible_local`
- `mock_test_provider`
- `offline_disabled_provider`
- `unknown_local_provider`

Provider statuses:

- `available_metadata_only`
- `configured_metadata_only`
- `not_configured`
- `unavailable`
- `endpoint_unverified`
- `endpoint_available_unverified`
- `resource_blocked`
- `disk_pressure_blocked`
- `disabled_by_policy`
- `unknown`

Provider status is metadata only. `endpoint_available_unverified` does not mean
safe to call. No endpoint probing or model loading is performed by this sprint.

## Model Roles And Modalities

Model roles:

- `chat_general`
- `coding`
- `reasoning`
- `summarization`
- `translation_terminology`
- `embedding`
- `reranker`
- `vision`
- `audio_stt`
- `audio_tts`
- `multimodal`
- `safety_classifier`
- `small_utility`
- `unknown`

Model modalities:

- `text_in_text_out`
- `text_embedding`
- `text_rerank`
- `image_text`
- `audio_text`
- `text_audio`
- `multimodal`
- `unknown`

Rules:

- Embedding models cannot be mapped to chat generation.
- Rerankers cannot be mapped to chat generation.
- Vision and multimodal models are future-gated and inactive by default.
- Audio STT/TTS models are future-gated and inactive by default.
- Unknown role or modality requires human review or blocks.
- Safety classifier output cannot become policy truth by itself.

## Task Role Mapping

Supported task roles:

- `mission_control_wording`
- `tool_simulation_explanation`
- `repo_audit_candidate_notes`
- `code_explanation`
- `architecture_review`
- `risk_analysis`
- `documentation_summary`
- `translation_terminology`
- `context_retrieval`
- `context_reranking`
- `visual_analysis_future_gated`
- `voice_interaction_future_gated`
- `unknown`

Coding and reasoning models can be proposal candidates for code explanation,
repo-audit candidate notes, risk analysis, and architecture review. Embedding
models are limited to `context_retrieval`. Rerankers are limited to
`context_reranking`. Vision and voice tasks remain future-gated.

## Auto Mode Eligibility Metadata

The helper can return:

- `passive_preferred`
- `local_preferred`
- `local_only`
- `cloud_allowed_later`
- `blocked_by_privacy`
- `blocked_by_resource`
- `blocked_by_unknown_metadata`
- `blocked_by_policy`
- `future_gated`

Auto Mode eligibility is not execution. `local_preferred` does not call the
model. `local_only` means external/cloud use should not be inferred for that
task. `cloud_allowed_later` is reserved for future policy work and is not cloud
permission.

## Context Policy Fields

Context policy metadata includes:

- `max_context_tokens`
- `recommended_context_budget`
- `can_receive_private_repo_context`
- `can_receive_user_memory_context`
- `can_receive_runtime_logs`
- `can_receive_evidence_refs`
- `can_receive_raw_evidence`
- `can_receive_secret_like_content`
- `can_receive_raw_journal`
- `can_receive_compliance_context`
- `can_receive_web_context`
- `requires_redaction`
- `requires_source_refs`
- `output_requires_validation`

The helper rejects raw secret-like context, raw journal context, and raw
evidence context. Evidence references may be allowed as metadata, but raw
evidence remains denied in this readiness contract.

## Privacy And Data Sensitivity

Non-passive model entries require `privacy_class`, `data_sensitivity_allowed`,
and context policy metadata. Private repo context maps to local-only by default
when the provider class is local. Cloud region and terms claims are out of scope
unless marked `unknown`, `out_of_scope`, `not_applicable`, or `local_only`.

The helper does not infer cloud eligibility, endpoint availability, provider
health, speed, benchmark quality, context length, or VRAM fitness.

## Embedding And Reranker Boundary

Embedding models are retrieval support metadata only. They cannot become chat,
planner, code-generation, approval, policy, or evidence authority.

Rerankers are ranking support metadata only. They cannot produce chat text,
tool calls, execution decisions, policy truth, evidence, or verifier success.

No embeddings are generated and no reranking is performed by this sprint.

## Vision And Audio Future Gate

Vision, multimodal, audio STT, and audio TTS roles require future explicit
privacy and media-boundary work. They are inactive by default and can only be
represented as future-gated metadata.

No screenshots, images, audio, speech, OCR, accessibility, VLM calls, STT, or
TTS behavior is implemented.

## Relationship To Model Provider Readiness

`Model Provider / Local LLM Readiness` documents provider classes and output
authority boundaries. This sprint turns a narrow subset into a pure validation
contract over caller-supplied metadata. Provider readiness remains
non-dispatchable and metadata-only.

## Relationship To Mission Control And Tool Simulation

Future Mission Control or Tool Simulation surfaces may use role mappings for
preview wording, explanation, or candidate notes. Those surfaces remain
non-authoritative. A model role map cannot execute a tool, approve a command, or
mark simulated output as real.

## Relationship To Repo Audit Pack

Repo Audit Pack may later use coding/reasoning model metadata for candidate
notes or code explanation. Model output remains proposal-only and cannot become
repo audit proof, source inventory truth, read-plan truth, runner evidence, or
verifier success.

## Relationship To Context Compiler And Memory

Context Compiler packages are non-authoritative context. They cannot grant
model permission, select providers, satisfy approval, or satisfy evidence.

Memory cannot create model authority, refresh model metadata, approve model
use, or route private context. No memory read or write is performed.

## Relationship To Policy / Approval / Lease

Policy, approval, and future lease gates remain backend-owned. The helper
rejects capability, approval, lease, runtime dispatch, and execution permission
claims. A future model call must re-check policy after any context compilation
and before any provider request.

## Relationship To Evidence / Verifier

The helper cannot create evidence, verifier success, compliance proof, security
proof, model health proof, or benchmark proof. Model output cannot mark missing
or failed evidence as verified, and cannot make runtime health green.

## Current Example Model Role Map

These examples are synthetic role-map fixtures based on caller-supplied
metadata only. They are not live provider inventory and are not health checks.

| Model | Candidate role map | Boundary |
| --- | --- | --- |
| Qwen2.5-Coder 14B | coding / repo-audit candidate notes / code explanation | proposal-only |
| DeepSeek-R1-Distill-Qwen-14B | reasoning / risk analysis / architecture review | proposal-only |
| Qwen3.5-9B | fast general explanations / Mission Control wording / summaries | proposal-only |
| GPT-OSS-20B | general fallback | quality, latency, context length, and resource suitability unknown until tested later |
| Qwen3-VL-8B | future-gated vision/multimodal | not active now |
| text-embedding-baai-bge-m3-567M | embedding / context retrieval | not chat |
| Qwen3 0.6B embedding-class model | embedding / context retrieval or retrieval-support metadata | not chat |
| Qwen3-Reranker-0.6B | reranking / context precision | not chat |

## Tests Added

Added `tests/test_core/test_local_model_inventory.py` covering:

- valid LM Studio metadata is non-authoritative
- offline disabled provider with no models
- synthetic role maps for the current example local models
- embedding/reranker not mapped to chat
- vision/audio future-gated boundaries
- missing provider/model/context/privacy metadata blocks
- raw secret, raw journal, and raw evidence context rejected
- model call, endpoint probe, load, download, file read/move/delete, inference,
  embedding, reranking, API, MCP, tool, and memory behavior rejected
- authority, dispatch, grant, evidence, verifier, Auto Mode execution, proof,
  certification, and model-output-as-truth claims rejected
- unsafe related decisions rejected
- inputs and supplied decisions are not mutated

## Intentionally Not Done

- No model loading or calling
- No provider health checks
- No LM Studio/Ollama/vLLM/OpenAI-compatible endpoint probing
- No model directory scan or model file inspection
- No model download, install, move, or delete
- No embedding generation, reranking, or inference
- No router execution or Auto Mode implementation
- No API/runtime/frontend integration
- No MCP/tool/memory behavior
- No approval, lease, capability, evidence, or verifier success creation

## Future Local Provider Health Check Notes

A future health-check sprint should be read-only, explicit, bounded, and
separate from this inventory contract. It should report provider id, endpoint
reference, timeout behavior, failure state, privacy class, and staleness without
calling generation unless a later policy gate authorizes it.

## Future Auto Mode Router Notes

A future Auto Mode contract must keep routing metadata separate from execution.
It must re-check policy, privacy, resource, context, model role, provider class,
lease/approval gates, and evidence expectations before any model request.
Fallback must preserve original failure state and cannot convert unavailable,
OOM, timeout, policy-blocked, or privacy-blocked results into success.

## Remaining Risks

- Current model metadata is caller-supplied and may be stale.
- No provider endpoint, model health, speed, quality, context length, VRAM, or
  RAM facts are proven.
- Disk/resource pressure remains a blocker for careless model expansion.
- Future local provider integration must avoid leaking private repo context or
  secrets through provider logs.
- Auto Mode can become an authority bypass if routing, policy, privacy, and
  evidence gates are not kept backend-owned.
