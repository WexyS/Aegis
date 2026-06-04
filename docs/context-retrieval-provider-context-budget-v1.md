# Context Retrieval Policy / Provider Context Budget v1

## Decision

- Decision: `CONTEXT_POLICY_PROVIDER_BUDGET_WITH_TESTS`
- Contract version: `context-retrieval-provider-context-budget/1`
- Implementation surface: `src/aegis/core/context_policy.py`
- Test surface: `tests/test_core/test_context_policy.py`
- Previous sprint: `POLICY_AS_CODE_EXTENSION_WITH_TESTS`

This sprint adds a pure context policy and provider budget contract. It does
not implement actual context retrieval, context package creation, memory
retrieval, repo file reads, web queries, document parsing, vector indexing,
embedding generation, reranking, model calls, provider selection, API/MCP/tool
calls, runtime wiring, API endpoints, or frontend behavior.

## Scope

The contract validates caller-supplied context metadata and classifies whether
the metadata is:

- metadata-ready
- proposal-ready
- future-gated
- blocked

The output is non-authoritative. Context policy cannot grant permission,
approval, lease, capability, evidence, verifier success, provider selection, or
runtime dispatch.

## Why Context Policy Exists

Context is high risk because it can contain private repo code, runtime logs,
journal projections, raw journal entries, evidence references, raw evidence,
memory-derived material, compliance context, developer passport context,
frontend-supplied context, MCP/tool output, web-derived material, documents,
images, videos, secrets, tokens, credentials, and unknown-sensitivity data.

Aegis needs a backend-owned policy contract before any real retrieval,
embedding, reranking, RAG, memory retrieval, web research, repo reads, document
parsing, or model provider routing can start.

## Context Source Categories

Supported source categories:

- `public_docs`
- `private_repo_code`
- `repository_metadata`
- `project_config`
- `runtime_logs`
- `raw_journal`
- `journal_projection`
- `evidence_refs`
- `raw_evidence`
- `maintenance_findings`
- `policy_decision_refs`
- `memory_refs`
- `user_memory`
- `project_memory`
- `repo_memory`
- `compliance_context`
- `developer_passport_context`
- `plugin_review_context`
- `vertical_pack_context`
- `web_search_result_future`
- `web_page_extract_future`
- `document_text_future`
- `pdf_extract_future`
- `image_observation_future`
- `video_observation_future`
- `mcp_output`
- `tool_output`
- `frontend_supplied_context`
- `external_agent_output_future`
- `secrets_or_tokens`
- `unknown`

## Provider Target Classes

Supported provider targets:

- `passive_backend_only`
- `local_model_candidate`
- `local_embedding_candidate`
- `local_reranker_candidate`
- `cloud_model_candidate_later`
- `web_query_candidate_later`
- `memory_index_candidate_later`
- `vector_index_candidate_later`
- `no_provider_allowed`
- `future_gated`
- `unknown`

Provider target metadata is not provider selection. The decision always keeps
`provider_selected=false`, `cloud_routing_allowed=false`, and
`local_model_routing_allowed=false`.

## Context Operations

Supported operations:

- `classify_context`
- `propose_context_package`
- `propose_context_budget`
- `propose_redaction`
- `propose_provider_target`
- `propose_retrieval_future`
- `propose_embedding_future`
- `propose_reranking_future`
- `propose_memory_retrieval_future`
- `propose_web_research_future`
- `propose_document_parse_future`
- `propose_repo_read_future`
- `unknown`

Future operations stay future-gated. They do not retrieve context, read files,
query web, parse documents, touch vector stores, generate embeddings, rerank, or
call models.

## Privacy Classes

Supported privacy classes:

- `public`
- `internal`
- `private`
- `private_repo`
- `personal_private`
- `sensitive`
- `secret_like`
- `credential_like`
- `regulated_or_compliance_sensitive`
- `unknown`

## Sensitivity Rules

- `secrets_or_tokens` is blocked.
- `secret_like` is blocked.
- `credential_like` is blocked.
- `raw_journal` is blocked by default.
- `raw_evidence` is blocked unless constrained to refs-only metadata.
- `evidence_refs` are allowed only as refs-only metadata, never evidence.
- `private_repo_code` cannot target `cloud_model_candidate_later`.
- `private_repo_code` may be proposed for `passive_backend_only` or
  `local_model_candidate`, but that is not routing permission.
- `user_memory`, `project_memory`, `repo_memory`, and `memory_refs` require
  Memory Governance and Identity Scope.
- Unknown sensitivity blocks provider routing and requires review.
- Frontend, MCP, tool, web, model, and external-agent outputs are lower trust
  and cannot be truth or authority.
- Document, PDF, image, video, web extraction, and external-agent output remain
  future-gated until explicit policy exists.

## Provider Budget Concepts

The `ProviderContextBudget` metadata captures:

- `max_context_tokens`
- `recommended_context_tokens`
- `reserved_system_tokens`
- `reserved_instruction_tokens`
- `reserved_response_tokens`
- `max_source_count`
- `max_chunk_count`
- `max_chunk_tokens`
- `max_memory_items`
- `max_evidence_refs`
- `allow_raw_content`
- `allow_summaries`
- `allow_source_refs_only`
- `requires_redaction`
- `requires_citation`
- `requires_freshness_check`
- `requires_provenance`
- `requires_human_review`

Budget metadata is not permission. It does not authorize retrieval, model
calls, cloud routing, memory access, vector indexing, or provider selection. It
only constrains a future context package candidate.

## Redaction, Citation, and Provenance

Private, private repo, personal private, sensitive, regulated, and unknown
context require redaction. The budget preserves citation, freshness, and
provenance requirements. Durable/reference context requires source refs or
provenance. Missing source refs/provenance blocks the decision.

## Relationships

### Identity Scope

Identity Scope is required for private, project, user, repo, runtime, memory,
compliance, developer passport, plugin, and vertical pack context. Blocked or
unknown identity scope blocks context policy.

### Memory Governance

Memory-derived context requires Memory Governance and Identity Scope. Memory
Governance metadata does not retrieve memory and does not authorize memory
context delivery.

### Policy-as-Code Extension

Policy Extension decisions may be referenced. Blocked, unsupported, or unsafe
policy extension decisions block context policy. Context policy does not
contradict backend policy.

### Local Model Inventory and Model Auto Mode

Local Model Inventory metadata alone does not authorize context delivery.
Absent Model Auto Mode means no provider selection. Context policy keeps
provider selection and routing flags false.

### Repo Audit Runner

Repo audit readiness metadata does not authorize repo file reads. Repo read
operations remain future-gated and no file read is performed.

### Web Research Gateway

Web search and page extraction context remains future-gated. This sprint does
not query the web, call APIs, or create web evidence.

### Document, PDF, and Multimodal Future Work

Document, PDF, image, and video context remains future-gated. This sprint does
not parse documents or perform visual/audio analysis.

### MCP, Tool, Frontend, and External Agent Output

MCP, tool, frontend, web, model, and external-agent output is lower trust. It
cannot be authority, truth, permission, evidence, verifier success, or runtime
state.

### Evidence and Verifier

Context policy does not create evidence and cannot mark verifier success.
Evidence refs are source references only. Raw evidence remains blocked unless a
future explicit policy proves a refs-only boundary.

## Invariants

Every `ContextPolicyDecision` preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_context_policy`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_context_policy=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `context_retrieval_performed=false`
- `context_package_created=false`
- `memory_retrieval_performed=false`
- `repo_file_read_performed=false`
- `web_query_performed=false`
- `document_parse_performed=false`
- `vector_index_touched=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `model_call_performed=false`
- `cloud_sync_performed=false`
- `data_sent_external=false`
- `provider_selected=false`
- `cloud_routing_allowed=false`
- `local_model_routing_allowed=false`
- `memory_context_allowed=false`
- `raw_journal_allowed=false`
- `raw_evidence_allowed=false`
- `secret_context_allowed=false`

## Tests Added

Focused tests cover:

- public docs metadata classification
- private repo identity scope requirement
- memory context Memory Governance and Identity Scope requirement
- missing required fields
- missing source refs/provenance
- secret, credential, raw journal, and raw evidence boundaries
- evidence refs as refs-only metadata
- private repo context cloud denial
- passive/local private repo proposals without routing permission
- lower-trust frontend/MCP/tool/web/model/external-agent output
- budget non-authority and budget excess blocking
- redaction/citation/provenance preservation
- unsafe related decision rejection
- Local Model Inventory metadata not authorizing delivery
- absent Model Auto Mode not selecting providers
- repo audit metadata not authorizing repo file reads
- compliance/passport metadata not becoming proof
- authority, permission, routing, retrieval, vector, model, web, document,
  cloud, API, MCP, and tool behavior claim rejection
- input and related decision immutability

## Intentionally Not Done

- No context retrieval.
- No context package creation.
- No repo file read.
- No memory retrieval.
- No web query.
- No document/PDF parse.
- No image/video observation.
- No vector DB touch.
- No embedding generation.
- No reranking.
- No model call.
- No provider selection.
- No data sent external.
- No runtime/API/frontend integration.
- No evidence/verifier success.
- No approval, lease, or capability grant.

## Future Implementation Notes

Future work must add separate explicit gates before any real context behavior:

- Context Retrieval Runner Readiness
- Provider Context Package Contract
- Model Auto Mode / Provider Selection Contract
- Web Research Gateway Policy
- Document/PDF/Multimodal Policy
- Memory Retrieval Policy
- Repo Audit Runner Policy
- Capability Lease Design

Every future runner must produce backend-owned evidence, verifier
postconditions, policy checks, identity/memory scope checks, redaction checks,
and failure states.

## Remaining Risks

- Context routing can leak private data if future provider selection bypasses
  this contract.
- Raw journal/evidence handling needs a later explicit boundary sprint.
- Memory-derived context needs strict governance before retrieval.
- Web/document/multimodal context needs source trust and citation policy.
- Budget constraints are synthetic metadata and do not prove token counts until
  a future runner validates them.
