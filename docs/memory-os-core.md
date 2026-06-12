# Memory OS Core

Decision: MEMORY_OS_CORE_BACKEND_API

Memory OS Core is the first real local Memory OS backend for the Aegis
Hackathon release track. It is intentionally small: explicit API/store requests can
propose, approve, reject, soft-delete, list, and keyword-search local memories
backed by SQLite.

This is not the final Full Memory OS.

## Scope

Implemented:

- Local SQLite storage through `aegis.memory.store.MemoryStore`.
- Minimal memory item schema: id, type, content, content summary, scope, status,
  sensitivity, source refs, project/repository/session refs, timestamps, and
  metadata JSON.
- Lifecycle states: `proposed`, `active`, `rejected`, `deleted`.
- Operations: propose, approve, reject, delete, list, search.
- Scopes: `session`, `project`, `repository`.
- Sensitivities: `public`, `internal`, `private`, `sensitive`, `secret_like`.
- FastAPI routes under `/memory`.
- Memory Governance integration for proposals.
- Identity Scope integration for project and repository scoped proposals.

Not implemented:

- Frontend UI.
- AutoPilot or Society integration.
- Silent memory writes from chat/task outputs.
- Vector memory, graph memory, embeddings, reranking, duplicate detection, or
  conflict graph.
- Model, MCP, tool, cloud, web, or external API calls.
- Import/export, sync, capability leases, or evidence generation.
- Runtime journal, evidence, replay, approval, policy, or verifier mutation.

## Storage

Default database:

`data/memory_os_rc1.sqlite3`

The database is created lazily when the store is used. Tests inject a temporary
database path and do not use the default file.

Deleted memories are soft-deleted by setting status to `deleted` and recording
`deleted_at`.

## API

Endpoints:

- `POST /memory/propose`
- `POST /memory/{memory_id}/approve`
- `POST /memory/{memory_id}/reject`
- `DELETE /memory/{memory_id}`
- `GET /memory`
- `GET /memory/search`

Responses include backend-owned operation state:

- `memory_id`
- `status`
- `operation`
- `validation_result`
- `governance_result`
- `warnings`
- `limitations`
- non-authority invariants

Failures are explicit. Validation failures return HTTP 400, missing memories
return HTTP 404, and invalid lifecycle transitions return HTTP 409.

## Governance

`propose` validates Core rules first, then calls the existing Memory
Governance contract. Project and repository scoped proposals also build a local
Identity Scope decision from caller-supplied refs so persistent scope checks
remain explicit.

Blocked examples:

- empty content
- invalid scope
- missing `session_ref` for session memory
- missing `project_ref` for project memory
- missing `repository_ref` for repository memory
- `secret_like`, `secret-like`, `credential_like`, or unknown sensitivity

Lifecycle transitions are store-level operations. Their response marks
governance as `not_applicable_lifecycle_transition`; they do not claim approval,
lease, capability, evidence, verifier success, or execution permission.

## Non-Authority Rules

Memory candidates are not active memory.

Retrieved memory is not truth.

Memory output is not evidence.

Memory retrieval is not authority.

Memory-derived context is not execution permission.

Context packages remain separate from permission, execution, evidence, and
verifier semantics.

Search results are candidate material only and include:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_memory_os_rc1`
- `evidence_provided_by_memory=false`
- `verifier_success=false`
- `memory_output_is_authority=false`
- `retrieved_memory_is_truth=false`
- `context_permission_granted=false`

## Search Behavior

Search is simple SQLite keyword matching over content, summary, and type. It
returns active memories by default.

Sensitive memories are excluded from search by default unless explicitly
requested with `include_sensitive=true` or a compatible sensitivity filter.
Unknown sensitivity is not accepted for new memories in Core.

Search supports:

- `keyword`
- `scope`
- `project_ref`
- `repository_ref`
- `session_ref`
- `sensitivity`
- `status`
- `limit`

No embeddings, vector index, model scoring, or reranking are used.

## Events

S1 does not add WebSocket or protocol memory events. Adding memory events would
touch broader runtime/protocol surfaces. S4 UI work can use REST polling or a
separate scoped event-integration sprint.

## Tests

Added focused tests for:

- valid proposal creation
- approve/reject/delete lifecycle
- invalid transition blocking
- secret-like validation blocking
- missing scope reference blocking
- project/repository scope validation
- keyword search
- scope filters
- deleted exclusion
- API happy path
- API validation failure
- API invalid transition conflict

## Future-Gated Full Memory OS Work

Future phases may add duplicate detection, conflict resolution, graph memory,
vector memory, retrieval scoring, memory compaction, UI panels, explicit memory
events, import/export, or model-assisted summarization. Each requires a separate
scoped sprint and must preserve Aegis authority, policy, evidence, verifier, and
runtime truth boundaries.
