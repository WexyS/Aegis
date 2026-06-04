# Memory Governance / Memory OS Contract v1

## Decision

MEMORY_GOVERNANCE_CONTRACT_WITH_TESTS

## Scope

This sprint defines a pure Memory Governance / Memory OS contract for future
Aegis memory work. It does not implement memory storage, retrieval, vector DB
usage, embeddings, reranking, RAG, model calls, database persistence, frontend
UI, or runtime behavior.

## Why Memory Governance Exists

Memory is a high-risk foundation surface. Future memory can affect planning,
context packaging, provider routing, repo audit productization, compliance
records, and operator UX. Before any memory exists, Aegis needs a contract that
defines scope, provenance, sensitivity, retention, trust, review, quarantine,
staleness, and non-authority boundaries.

Memory is not truth, permission, evidence, verifier success, approval, lease, or
capability.

## Memory Categories

The contract models these categories:

- `user_preference`
- `project_preference`
- `repo_memory`
- `task_session_memory`
- `operator_decision_history`
- `approval_denial_history`
- `policy_decision_summary`
- `model_provider_preference`
- `ui_ux_preference`
- `vertical_pack_memory`
- `plugin_review_memory`
- `entity_memory`
- `organization_team_memory_future`
- `tool_provider_reliability`
- `failure_negative_evidence_summary`
- `source_citation_memory`
- `web_research_memory`
- `document_memory`
- `conversation_summary`
- `personal_private_memory`
- `temporary_scratch`
- `quarantine_memory`
- `stale_deprecated_memory`
- `unknown`

## Memory Statuses

Supported statuses:

- `proposed`
- `active`
- `tentative`
- `inferred`
- `user_confirmed`
- `stale`
- `superseded`
- `quarantined`
- `deleted`
- `expired`
- `conflict`
- `sensitive_requires_review`
- `private_local_only`
- `rejected`
- `unknown`

Stale, quarantined, superseded, deleted, expired, conflict, rejected, and
unknown memory cannot be treated as active current memory.

## Memory Scopes

Supported scopes:

- `session_only`
- `project_scoped`
- `repository_scoped`
- `user_profile_scoped`
- `workspace_scoped`
- `tenant_scoped_future`
- `machine_local_only`
- `disabled`
- `unknown`

Rules:

- `session_only` requires `session_ref`
- `project_scoped` requires `project_ref`
- `repository_scoped` requires `project_ref` and `repository_ref`
- `user_profile_scoped` requires explicit `user_ref` and `profile_ref`
- durable memory proposals require source refs or provenance
- unknown identity blocks persistent memory
- cross-project memory mixing is denied by default
- Aegis and Ultron memory scopes cannot merge

## Memory Operations

Operations are proposals only:

- `propose_write`
- `propose_retrieve`
- `propose_update`
- `propose_delete`
- `propose_forget`
- `propose_export`
- `propose_quarantine`
- `propose_supersede`
- `propose_expire`
- `propose_rebuild_index_future`
- `unknown`

Proposal does not mean execution. `propose_write` does not write memory.
`propose_retrieve` does not retrieve memory. Delete, forget, export, and index
rebuild proposals do not mutate state.

## Sensitivity Classes

Supported sensitivity classes:

- `public`
- `internal`
- `private`
- `sensitive`
- `secret_like`
- `credential_like`
- `health_or_personal_sensitive`
- `unknown`

Rules:

- `secret_like` and `credential_like` persistence is blocked by default
- `unknown` sensitivity blocks persistence
- `health_or_personal_sensitive` requires human review
- `personal_private_memory` requires explicit user confirmation
- model-inferred personal memory cannot become active without confirmation

## Retention Policies

Supported retention policies:

- `no_persistence`
- `session_ttl`
- `project_ttl`
- `user_confirmed_until_deleted`
- `explicit_expiry`
- `quarantined_until_review`
- `disabled`
- `unknown`

Retention metadata does not write, delete, expire, or export memory by itself.

## Relationship To Identity / Tenant Scope

Memory Governance consumes Identity Scope decisions when supplied. Identity
scope can validate project/session/repository boundaries, but it cannot grant
memory write or retrieval permission.

Persistent memory remains blocked when identity scope is missing, blocked, or
unknown.

## Relationship To Local Model Inventory / Model Auto Mode

Model metadata and future Auto Mode decisions cannot authorize memory. Model
output is lower-trust source material and cannot become memory truth,
permission, evidence, verifier success, or policy override.

## Relationship To Context Retrieval / Provider Context Budget

Memory governance is a prerequisite for context retrieval and provider context
budgets. Memory cannot silently become model context, raw evidence context, raw
journal context, cloud context, or vector content.

## Relationship To Vector Memory / Knowledge Graph

Vector indexing, embeddings, reranking, knowledge graph construction, and RAG
remain future-gated. `propose_rebuild_index_future` is metadata only and never
touches a vector DB.

## Relationship To Repo Audit Pack

Repo audit memory requires project and repository scope. Repo audit findings,
candidate notes, and source metadata cannot become memory truth without future
governance, provenance, review, and policy gates.

## Relationship To Developer Work Passport / Compliance Evidence

Developer passport and compliance evidence records may later reference governed
memory, but memory cannot prove work quality, compliance, certification, audit
success, or verifier success.

## Relationship To External Agent Oversight

External agent memory and observation are future-gated. This contract does not
implement external agent tracking, surveillance, productivity scoring, telemetry,
or long-term behavioral profiling.

## Relationship To Policy / Approval / Lease

Memory cannot approve actions, create leases, grant capabilities, or override
policy. Future side-effecting actions must pass backend policy and evidence
expectations independently.

## Relationship To Evidence / Verifier

Runtime evidence refs may be cited as source refs, but memory is still not
evidence. Memory cannot mark verifier success.

## Source Trust Rules

Model, web, MCP, tool, and frontend outputs are lower-trust source material.
They require review and cannot be treated as truth by themselves.

Confidence, freshness, provenance, and limitations are preserved as metadata,
not proof.

## Required Invariants

The contract output always keeps:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_memory_governance`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_memory_governance=false`
- `verifier_success=false`
- `mutation_performed=false`
- `memory_write_performed=false`
- `memory_retrieval_performed=false`
- `memory_delete_performed=false`
- `memory_export_performed=false`
- `vector_index_touched=false`
- `embedding_generated=false`
- `reranking_performed=false`
- `model_call_performed=false`
- `cloud_sync_performed=false`
- `data_sent_external=false`
- `surveillance_allowed=false`
- `productivity_scoring_allowed=false`
- `memory_write_allowed=false`
- `memory_retrieval_allowed=false`
- `memory_delete_allowed=false`
- `memory_export_allowed=false`

## Tests Added

`tests/test_core/test_memory_governance.py` covers:

- valid session-only proposal is non-authoritative and proposed-only
- project and repository scope requirements
- missing required fields
- provenance/source refs for durable memory
- identity scope relationships
- unknown identity and cross-project blocking
- Aegis vs Ultron memory separation
- sensitivity and personal memory rules
- operation proposals do not execute
- vector/index rebuild remains future-gated
- non-current statuses cannot be treated as active current memory
- source trust for model/web/MCP/tool/frontend inputs
- evidence refs are source refs, not evidence
- unsafe related decisions are rejected
- input and related decisions are not mutated
- outputs never grant runtime or memory permissions

## Intentionally Not Done

- No memory storage.
- No memory retrieval.
- No memory delete/export.
- No vector DB or qdrant integration.
- No embeddings or reranking.
- No RAG.
- No model calls.
- No database persistence.
- No Memory UI.
- No cloud sync.
- No external data transfer.
- No surveillance or productivity scoring.
- No runtime/API/frontend behavior change.
- No runtime/journal/evidence/replay mutation.

## Future Implementation Notes

Future Memory OS implementation should start with storage-disabled dry-run
contracts, then explicit backend policy gates, then scoped storage only after
identity/project/user/profile boundaries are enforced.

Any future write/retrieve/delete/export path must create backend-owned audit
records and must preserve provenance, sensitivity, retention, stale/conflict
state, revocation, and review status.

## Remaining Risks

This contract is not wired into runtime, context packaging, model provider
routing, repo audit, or frontend UX. It is a foundation prerequisite, not a
Memory OS implementation.
