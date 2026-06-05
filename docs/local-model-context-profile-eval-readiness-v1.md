# Local Model Context Profile / Eval Readiness v1

## Decision

- Decision: `LOCAL_MODEL_CONTEXT_PROFILE_READINESS_WITH_TESTS`
- Contract version: `local-model-context-profile-eval-readiness/1`
- Implementation surface: `src/aegis/core/local_model_context_profile.py`
- Test surface: `tests/test_core/test_local_model_context_profile.py`
- Previous sprint: `WEB_RESEARCH_GATEWAY_READINESS_WITH_TESTS`

This sprint adds a pure readiness contract for local model role profiles,
context budgets, sampling profile metadata, evaluation readiness, known risks,
and modality gates. It does not call models, load models, probe providers,
validate API keys, inspect live model files, run benchmarks, generate
embeddings, rerank, perform inference, retrieve context/memory, read repo files,
call web/API/GitHub, create evidence, mark verifier success, implement
runtime/API/frontend behavior, or mutate runtime/journal/evidence/replay state.

## Scope

The contract validates caller-supplied local model profile metadata and
classifies:

- intended model role
- model family
- provider class
- context source allowance
- context budget
- sampling profile
- eval readiness
- known risks
- future-gated modality boundaries

The output is non-authoritative. A model profile cannot grant execution
permission, approval, leases, capabilities, provider health, benchmark proof,
model identity, evidence, verifier success, context access, web access, memory
access, or runtime dispatch.

## Why Local Model Context Profiles Exist

Aegis needs a model profile/eval layer before local models are selected based on
vague names, self-reports, or manual impressions. Local Model Inventory can list
metadata, Model Auto Mode can propose candidates, and Provider Health can
describe readiness. None of those prove role quality, context safety, benchmark
results, or execution permission.

## Why This Is Not Model Execution or Evaluation

This contract does not load, call, probe, benchmark, or inspect models. Eval
readiness is metadata only. User observations are useful metadata, not benchmark
proof. Model self-reports are not model identity.

## Current User Model Set and Role Hypotheses

These are current user-supplied hypotheses only:

- Qwen3.5 9B: fast general chat, lightweight summaries, Mission Control
  wording, and low-latency user-facing explanation. It should remain separate
  from Gemma 4 12B rather than being fully replaced.
- Gemma 4 12B: stronger general reasoning, Turkish technical explanation, and
  future-gated multimodal reasoning. User reports it works well locally. Known
  risk: self-identity drift, where it called itself "Google Gemini" in a
  self-comparison.
- Qwen2.5-Coder 14B: primary coding, repo-audit candidate notes, and code
  explanation.
- DeepSeek R1 Distill Qwen 14B: heavy reasoning, risk analysis, and
  architecture critique.
- GPT-OSS 20B: fallback general candidate only if future eval justifies it.
- bge-m3 and Qwen embedding-class models: embedding/context retrieval
  candidates, not chat models.
- Qwen3 Reranker 0.6B: reranking/context precision candidate, not a chat model.
- Qwen3-VL 8B, if still present: previous/future-gated vision candidate.
  Replacement by Gemma 4 12B is undecided and requires later validation.

## Model Role Classes

Supported roles:

- `fast_general_chat`
- `lightweight_summary`
- `mission_control_wording`
- `general_reasoning`
- `turkish_technical_explanation`
- `coding_assistant`
- `repo_audit_candidate_notes`
- `architecture_review`
- `risk_analysis`
- `translation_terminology`
- `embedding`
- `reranking`
- `future_multimodal_reasoning`
- `future_vision`
- `future_audio`
- `future_video_frame`
- `future_screen_observation`
- `fallback_general`
- `unknown`

Embedding and reranking roles are not chat roles. Future vision/audio/video and
screen-observation roles remain future-gated.

## Model Family Classes

Supported families:

- `qwen_general`
- `qwen_coder`
- `deepseek_reasoning`
- `gemma_multimodal_general`
- `gpt_oss_general`
- `bge_embedding`
- `qwen_embedding`
- `qwen_reranker`
- `qwen_vl_future`
- `unknown`

## Context Source Allowance Classes

Supported source allowance classes:

- `public_docs_allowed`
- `repo_code_candidate_local_only`
- `repo_metadata_allowed`
- `user_memory_blocked_by_default`
- `project_memory_requires_governance`
- `raw_journal_blocked`
- `raw_evidence_blocked`
- `evidence_refs_allowed`
- `web_source_candidates_allowed_after_gateway`
- `document_text_future_gated`
- `image_observation_future_gated`
- `audio_observation_future_gated`
- `video_frame_future_gated`
- `unknown_blocked`

Raw journal and raw evidence remain blocked. Private repo context remains a
local-only candidate and requires Identity Scope. Memory context requires Memory
Governance.

## Context Budget Classes

Supported budget classes:

- `tiny_context`
- `small_context`
- `medium_context`
- `large_context_candidate`
- `unknown_context`
- `blocked`

Context budget is metadata only. Large context candidates require Context
Policy and do not select a provider or retrieve context.

## Sampling Profile Classes

Supported sampling profiles:

- `strict_json`
- `safe_general`
- `architecture_review`
- `coding_low_temperature`
- `creative_ui_copy`
- `multimodal_future_gated`
- `unknown`

Sampling profile metadata is not inference and does not run a model.

## Eval Readiness Classes

Supported eval readiness classes:

- `not_evaluated`
- `user_observed_metadata_only`
- `eval_plan_candidate`
- `benchmark_future_gated`
- `health_required`
- `provider_probe_required`
- `context_policy_required`
- `multimodal_privacy_required`
- `failed_eval_metadata_only`
- `unknown`

Eval readiness is not benchmark proof. Benchmark and multimodal evaluation
remain future-gated until a later scoped sprint.

## Risk Classes

Supported risks:

- `self_identity_drift`
- `self_report_untrusted`
- `hallucination_risk`
- `json_format_risk`
- `context_overrun_risk`
- `role_mismatch_risk`
- `modality_future_gated`
- `resource_unknown`
- `provider_health_unknown`
- `privacy_boundary_required`
- `unknown`

Self-identity drift and self-report uncertainty are preserved as risks, not
converted into identity or benchmark truth.

## Context and Privacy Rules

- Raw journal and raw evidence are blocked.
- User memory is blocked by default.
- Project memory requires Memory Governance.
- Private repo context is local-only candidate metadata and requires Identity
  Scope.
- Large context candidates require Context Policy.
- Web source candidates require Web Research Gateway in future work and do not
  authorize web synthesis.

## Sampling and Profile Metadata Rules

Sampling profiles are descriptive only. They do not set runtime generation
parameters, call a model, or authorize provider selection.

## Eval Readiness and Benchmark Proof Boundaries

User observation is metadata only. Benchmark proof requires a later eval
contract with explicit source, evidence, verifier, and reproducibility
boundaries. This sprint never sets `benchmark_claim_verified=true`.

## Relationship to Local Model Inventory

Local Model Inventory metadata may inform role/profile candidates. It cannot
prove availability, health, quality, or execution permission.

## Relationship to Model Auto Mode

Model Auto Mode can propose candidate selection metadata. It cannot authorize
model calls, profile records, context routing, or execution.

## Relationship to Local Provider Health and Probe Design

Provider Health and Probe Design are references only. Provider health readiness
does not become verified provider health. Probe design does not probe endpoints.

## Relationship to Context Policy

Context Policy is required for large/private/sensitive context candidates. The
profile contract cannot authorize context retrieval.

## Relationship to Web Research Gateway

Web Research Gateway is planning metadata only. It cannot authorize model
synthesis, web queries, or source truth.

## Relationship to Memory Governance and Identity Scope

Memory-derived model context requires Memory Governance. Private repo and
project/user scoped context requires Identity Scope.

## Why Model Self-Report Is Not Model Identity

Models can report incorrect names, families, ownership, training data, or
capabilities. Gemma 4 12B has user-observed self-identity drift and must keep
that risk visible.

## Why User Observation Is Not Benchmark Proof

User observations can guide profile hypotheses, but they are not reproducible
benchmarks, evidence, verifier success, or provider health.

## Why Model Profile Is Not Provider Health or Execution Permission

Profile metadata describes intended roles and risks. It cannot prove provider
availability, model loading, endpoint reachability, context safety, or runtime
permission.

## Tests Added

`tests/test_core/test_local_model_context_profile.py` covers:

- Qwen3.5 9B fast general profile retained as candidate
- Gemma 4 12B general and future multimodal profiles
- Qwen2.5-Coder, DeepSeek, embedding, and reranker profiles
- required metadata and source/provenance checks
- self-report, benchmark, and provider-health truth boundaries
- embedding/reranker/chat role mismatch boundaries
- multimodal future privacy boundaries
- raw journal/evidence and memory/context boundaries
- sampling and context budget metadata-only behavior
- denial of model calls, loading, probes, inference, embeddings, reranking,
  multimodal inference, benchmarks, eval records, profile records, repo reads,
  web/context/memory retrieval, data transfer, evidence, verifier success, and
  grants
- unsafe related decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No model calls, loads, probes, or inference
- No LM Studio/Ollama/OpenAI-compatible endpoint probing
- No API key validation or secret reads
- No live model file inspection
- No benchmark or eval execution
- No embedding generation or reranking
- No multimodal analysis
- No context, memory, web, or repo retrieval
- No profile records
- No runtime/API/frontend integration
- No evidence or verifier success
- No approval, lease, capability, or dispatch grant
- No runtime/journal/evidence/replay mutation

## Future Implementation Notes

A future eval sprint should define:

- explicit prompt sets and expected outputs
- local provider health prerequisites
- model identity source boundaries
- benchmark reproducibility metadata
- privacy-safe context fixtures
- no-secret/no-raw-journal/no-raw-evidence gates
- modality-specific privacy gates
- evidence and verifier expectations for eval attempts
- separation between eval result, profile metadata, and runtime authority

## Remaining Risks

- The contract validates supplied metadata only; it does not prove model quality,
  availability, provider health, context length, latency, or resource fit.
- Future eval work can overclaim results unless benchmark provenance, evidence,
  and verifier boundaries are explicit.
- Multimodal model routing remains risky until image/audio/video/screen privacy
  boundaries are separately implemented.
