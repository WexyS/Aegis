# Local Provider Health Check Readiness v1

## Decision

- Decision: `LOCAL_PROVIDER_HEALTH_READINESS_WITH_TESTS`
- Contract version: `local-provider-health-check-readiness/1`
- Implementation surface: `src/aegis/core/local_provider_health.py`
- Test surface: `tests/test_core/test_local_provider_health.py`
- Previous sprint: `MODEL_AUTO_MODE_PROVIDER_SELECTION_WITH_TESTS`

This sprint adds a pure local provider health readiness contract. It does not
probe endpoints, inspect provider processes, authenticate providers, validate
API keys, read secrets, request model lists, load models, call models, perform
minimal generation, generate embeddings, rerank, run multimodal probes, retrieve
context or memory, send data externally, call APIs/MCP/tools, wire runtime/API/
frontend behavior, or create evidence/verifier success.

## Scope

The helper validates caller-supplied metadata only. It can classify provider
class, provider health metadata, endpoint host class, config trust level, health
check phase, model health metadata, model role/modality compatibility, resource
blockers, and future gates.

The output is not:

- provider health proof
- endpoint reachability proof
- process observation proof
- model availability proof
- model quality proof
- model load proof
- model output proof
- Auto Mode execution permission
- evidence or verifier success
- approval, lease, or capability grant

Every decision preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_local_provider_health`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_provider_health=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `endpoint_probed=false`
- `provider_process_inspected=false`
- `provider_authenticated=false`
- `api_key_validated=false`
- `secret_read=false`
- `model_list_requested=false`
- `model_loaded=false`
- `model_call_performed=false`
- `minimal_generation_performed=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `multimodal_probe_performed=false`
- `context_retrieval_performed=false`
- `memory_retrieval_performed=false`
- `data_sent_external=false`
- `provider_selected_for_execution=false`
- `model_selected_for_execution=false`
- `health_verified=false`
- `health_check_executed=false`

## Why Provider Health Readiness Exists

Local model support needs a health layer, but provider health is a dangerous
boundary if metadata is confused with execution. Aegis must distinguish:

- configured metadata from reachable endpoint proof
- listed model metadata from loaded model proof
- model role metadata from task permission
- Auto Mode candidate selection from provider execution
- endpoint availability from privacy or policy approval
- provider readiness from evidence/verifier truth

This contract defines the metadata shape and blockers before any future health
probe runner exists.

## Provider Classes

Supported provider classes:

- `lm_studio_local`
- `ollama_local_optional`
- `vllm_local`
- `openai_compatible_local`
- `llama_cpp_local_future`
- `mlx_local_future`
- `mock_test_provider`
- `offline_disabled_provider`
- `unknown`

`llama_cpp_local_future` and `mlx_local_future` are future-gated. The
`offline_disabled_provider` class can validate without endpoint or model
entries, but it still grants no permission.

## Provider Health Statuses

Supported metadata statuses:

- `not_checked`
- `metadata_only`
- `configured_metadata_only`
- `offline_disabled`
- `not_configured`
- `endpoint_unknown`
- `endpoint_unverified`
- `endpoint_reachable_unverified_future`
- `endpoint_unreachable_metadata_only`
- `provider_process_unknown`
- `provider_process_not_observed`
- `provider_process_observed_metadata_only`
- `resource_blocked`
- `disk_pressure_blocked`
- `disabled_by_policy`
- `future_gated`
- `unknown`

`endpoint_reachable_unverified_future` is still not proof. It cannot set
`endpoint_probed=true` or `health_verified=true`.

## Model Health Statuses

Supported model metadata statuses:

- `model_metadata_only`
- `model_listed_unverified_future`
- `model_not_listed_metadata_only`
- `model_load_not_attempted`
- `model_loaded_unverified_future`
- `model_unavailable_metadata_only`
- `model_role_mismatch`
- `model_modality_future_gated`
- `model_resource_unknown`
- `model_resource_blocked`
- `unknown`

`model_listed_unverified_future` is future-gated and requires later evidence.
`model_loaded_unverified_future` is out of scope for this sprint because it
would imply a future probe/load boundary.

## Health Check Phases

Supported phases:

- `classify_metadata_only`
- `validate_config_shape`
- `propose_endpoint_probe_future`
- `propose_model_list_future`
- `propose_model_load_future`
- `propose_minimal_generation_future`
- `propose_embedding_probe_future`
- `propose_reranker_probe_future`
- `propose_multimodal_probe_future`
- `unknown`

All `propose_*_future` phases remain future-gated. They describe a later probe
design, not a probe execution.

## Endpoint Host Classes

Supported host classes:

- `localhost`
- `loopback`
- `lan`
- `remote`
- `cloud`
- `unknown`

Only `localhost` and `loopback` are acceptable as local metadata candidates in
this readiness contract. `lan`, `remote`, and `cloud` are blocked and require a
future explicit boundary. `unknown` requires human review.

## Config Trust Rules

Config source metadata is classified as metadata only:

- `backend_config`, `operator_supplied`, `test_fixture`, and
  `synthetic_fixture` are metadata-only sources.
- `frontend`, `frontend_projection`, and `user_supplied_untrusted` are lower
  trust metadata sources.

Lower trust config can be recorded for review, but it cannot authorize health,
provider calls, endpoint probes, model calls, or frontend authority.

## Model Role And Modality Rules

Model roles follow the local model inventory taxonomy:

- coding/reasoning/chat/summarization roles require `text_in_text_out`
- embedding requires `text_embedding`
- reranker requires `text_rerank`
- vision/audio/multimodal roles are future-gated

Embedding and reranker metadata cannot be mapped to chat generation tasks.
Vision/audio/multimodal metadata, including Gemma 4 12B-like or Qwen3-VL-like
fixtures, requires a future privacy and multimodal boundary.

## Relationship To Model Auto Mode

Model Auto Mode can name a provider/model candidate, but that candidate does
not authorize health checks. Provider health readiness does not accept Auto Mode
as execution permission. Future runtime use must re-check policy, privacy,
identity, evidence expectations, and verifier expectations after any health
metadata is classified.

## Relationship To Local Model Inventory

Local model inventory metadata can be supplied as a related decision, but it is
not proof that a model exists, is loaded, is healthy, or is safe to call. This
readiness contract keeps model metadata separate from endpoint probing and model
execution.

## Relationship To Context Policy

Context policy can block provider health readiness when the context boundary is
unsafe. Context policy metadata alone cannot deliver context to a provider, and
provider health readiness cannot select or call a provider for context.

## Relationship To Policy Extension

Policy-as-code remains the controlling boundary. A blocked policy extension
decision blocks provider health readiness. A policy extension cannot create a
probe, lease, approval, evidence record, verifier success, or model call.

## Relationship To Identity And Memory Governance

Identity scope and Memory Governance may be supplied as related decisions for
future readiness checks. They cannot authorize provider health execution. Memory
metadata cannot prove provider health, create leases, or refresh provider
availability.

## Current Example Model Role Notes

These are cautious metadata examples only:

- Qwen2.5-Coder 14B: coding, repo audit candidate notes, code explanation;
  proposal-only.
- DeepSeek-R1-Distill-Qwen-14B: reasoning, risk analysis, architecture review;
  proposal-only.
- Qwen3.5-9B: general explanations, Mission Control wording, summaries;
  proposal-only.
- GPT-OSS-20B: general fallback; quality/resource/health unknown until future
  testing.
- Gemma 4 12B: future-gated multimodal metadata if supplied; not active now.
- Qwen3-VL-8B: future-gated vision/multimodal metadata; not active now.
- text-embedding-baai-bge-m3-567M: embedding/context retrieval metadata; not
  chat.
- Qwen3-Reranker-0.6B: reranking/context precision metadata; not chat.

No live LM Studio, Ollama, vLLM, model folders, model files, or endpoints were
inspected by this sprint.

## Tests Added

Focused tests cover:

- valid LM Studio metadata as non-authoritative
- offline disabled provider metadata
- future-gated provider classes and probe phases
- missing identity/provider/model metadata blockers
- localhost/loopback versus LAN/remote/cloud endpoint rules
- unknown endpoint human review
- endpoint reachable unverified not becoming health proof
- process observed metadata not becoming process inspection
- API key/secret metadata blocked
- resource and disk pressure blockers
- lower trust frontend config remaining metadata only
- coding/reasoning/embedding/reranker/multimodal model role handling
- listed-unverified model metadata not becoming loaded or verified
- behavior flags rejected
- authority/grant/evidence/verifier/proof claims rejected
- unsafe related decisions rejected
- Auto Mode and local inventory metadata not authorizing probes
- input and related decisions not mutated

## Intentionally Not Done

This sprint intentionally did not:

- probe provider endpoints
- inspect provider processes
- authenticate providers
- validate or read API keys/secrets
- request model lists
- load models
- call models
- perform minimal generation
- generate embeddings
- rerank
- run multimodal probes
- inspect live model files or directories
- implement provider health runner
- implement provider health endpoint/API/frontend
- wire into planner, executor, runtime, MCP, tools, memory, or Auto Mode
- create evidence/verifier success

## Future Provider Health Probe Notes

A future probe sprint would need an explicit boundary and tests for:

- local-only endpoint allowlist
- timeout and retry limits
- negative evidence on failed probes
- no API key disclosure
- no secret logging
- model list proof versus model load proof
- minimal generation proof boundaries
- embedding/reranker probe boundaries
- multimodal privacy gates
- journal/evidence/verifier expectations
- rollback and operator approval rules

## Remaining Risks

- Local provider metadata can become stale quickly.
- Disk/resource pressure remains a real operational constraint.
- Endpoint and process status must not be trusted until a later evidence-backed
  probe runner exists.
- Multimodal and voice models need separate privacy boundaries.
- Auto Mode must continue to treat provider health readiness as metadata, not
  execution authority.
