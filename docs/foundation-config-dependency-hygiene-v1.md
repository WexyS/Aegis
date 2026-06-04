# Foundation Config / Dependency Hygiene Hardening v1

## Decision

FOUNDATION_CONFIG_DEPENDENCY_HYGIENE_WITH_TESTS

## Scope

This sprint hardens legacy configuration and dependency surfaces so they do not
imply model, vector, memory, provider, or context-retrieval readiness before the
required governance contracts exist.

This is not a model, memory, vector, or provider integration sprint.

## Config Surfaces Inspected

- `config/settings.yaml`
- `config/models.yaml`
- `src/aegis/core/config.py`
- `src/aegis/models/llm.py`
- `src/aegis/core/local_model_inventory.py`
- `src/aegis/api/ws_bridge.py`

## Dependency Surfaces Inspected

- `pyproject.toml`
- source imports under `src/aegis`
- tests touching local model inventory, policy boundaries, router/parser, and
  threat-model regression

## Dependency Status

| Dependency | Before | After | Runtime import found | Status |
|---|---|---|---|---|
| `ollama` | production dependency | optional `model` dependency | no | future-gated install-time availability only |
| `qdrant-client` | production dependency | optional `vector` dependency | no | future-gated vector availability only |
| `httpx` | production dependency | unchanged | yes, `LLMProvider` | HTTP client remains required by existing code |

Installed dependency is not capability enablement. Optional dependency presence
does not grant policy, approval, lease, provider health, evidence, verifier
success, or runtime dispatch.

## Memory Flag Status

Memory settings are now explicitly reserved and non-authoritative by default:

- `governance_status=not_implemented`
- `semantic_auto_index=false`
- `procedural_enabled=false`
- `memory_write_authorized=false`
- `memory_retrieval_authorized=false`
- `vector_store_enabled=false`
- `rag_enabled=false`

Memory config does not implement Memory OS, memory writes, memory retrieval,
semantic indexing, vector storage, RAG, evidence, verifier success, or policy
override.

## Model / Provider Config Status

Default model settings are now safe metadata defaults:

- `backend=offline_disabled`
- `base_url=""`
- model names are `not_configured`
- `provider_status=not_configured`
- `provider_health_verified=false`
- `model_calls_authorized=false`
- `embedding_generation_authorized=false`
- `auto_mode_enabled=false`

Configured provider URLs and model names are metadata only. They are not
endpoint health, model availability, provider authentication, Auto Mode,
execution permission, evidence, verifier success, approval, lease, or
capability grants.

## Runtime Guard

`LLMProvider.generate(...)` now denies by default unless
`settings.models.model_calls_authorized` is true.

`LLMProvider.embed(...)` now denies by default unless
`settings.models.embedding_generation_authorized` is true.

This is a fail-closed guard. It does not implement provider health checks,
provider calls, embeddings, reranking, context retrieval, model routing, or Auto
Mode.

## Model Registry Metadata

`config/models.yaml` is labeled as future-gated registry metadata. It is not
loaded as runtime provider selection, and it is not live resource verification.
Future Model Auto Mode / Provider Health Check work must validate any registry
entry before use.

## Relationship To Memory Governance

Memory Governance remains required before any memory write, memory retrieval,
semantic indexing, vector DB, RAG, user-memory context, or raw runtime/evidence
context behavior can be enabled.

Config fields cannot create memory authority.

## Relationship To Model Auto Mode

Model Auto Mode remains unimplemented. Future work must introduce a backend
decision object that evaluates provider class, provider health, privacy,
resource status, context policy, cost/latency, approval/lease requirements, and
evidence expectations before any model call.

Config fields cannot create Auto Mode authority.

## Relationship To Local Provider Health Check

Provider health remains unverified. A configured endpoint is not a successful
probe. Provider availability must be established by a future read-only health
check contract before it can be surfaced as availability.

## Relationship To Context Retrieval / Provider Context Budget

Context retrieval and provider context budgets remain future work. Embedding
model names and vector dependencies do not authorize embedding generation,
reranking, vector writes, vector reads, or raw evidence/journal context.

## Tests Added

`tests/test_core/test_foundation_config_dependency_hygiene.py` verifies:

- memory defaults are reserved and non-authoritative
- model defaults do not authorize provider calls
- `LLMProvider.generate` does not touch HTTP without config authorization
- `LLMProvider.embed` does not touch HTTP without embedding authorization
- `ollama` and `qdrant-client` are optional dependencies
- runtime code does not directly import `ollama` or `qdrant_client`
- `config/models.yaml` is metadata only
- Local Model Inventory remains metadata only

## Intentionally Not Done

- No model calls.
- No endpoint probes.
- No provider authentication.
- No API key validation.
- No dependency installation or removal from the environment.
- No Memory OS implementation.
- No vector DB implementation.
- No embedding generation or reranking.
- No Model Auto Mode.
- No provider health check.
- No context retrieval.
- No runtime/API/frontend behavior expansion.
- No evidence/verifier semantics change.
- No runtime journal/evidence/replay mutation.

## Remaining Risks

Environment variables or a local `.env` can still provide legacy model names or
provider URLs. The default guard prevents calls, but future model work must
replace this with an explicit Model Auto Mode / Provider Selection contract.

`src/aegis/models/llm.py` remains a legacy provider client. It is now fail-closed
by default, but it should be reconciled or wrapped before any future provider
execution sprint.

Identity and tenant scoping remain the next prerequisite before persistent
memory, cloud model routing, or broader provider context decisions.
