# Capability Lease Design v1

## Decision

- Decision: `CAPABILITY_LEASE_CONTRACT_WITH_TESTS`
- Contract version: `capability-lease-design/1`
- Implementation surface: `src/aegis/core/capability_lease.py`
- Test surface: `tests/test_core/test_capability_lease.py`
- Previous sprint: `LOCAL_PROVIDER_HEALTH_READINESS_WITH_TESTS`

This sprint adds a pure capability lease candidate contract. It does not create
lease storage, issue leases, activate leases, use leases, implement approval UI,
run runtime execution, probe providers, call models, read repo files, retrieve
memory, retrieve context, query web, execute plugins/playbooks/rollback, call
tools/MCP/APIs, or mutate runtime, journal, evidence, or replay state.

## Scope

The contract validates caller-supplied lease candidate metadata only. It can
classify lease subject, risk tier, scope, bounded duration, bounded action
count, revocability, source/provenance refs, required related decisions,
blockers, lifecycle state, and future gates.

Every `CapabilityLeaseDecision` preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_capability_lease`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `lease_active=false`
- `lease_created=false`
- `lease_used=false`
- `evidence_provided_by_lease=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `model_call_allowed=false`
- `provider_probe_allowed=false`
- `repo_file_read_allowed=false`
- `memory_write_allowed=false`
- `memory_retrieval_allowed=false`
- `context_retrieval_allowed=false`
- `web_query_allowed=false`
- `plugin_execution_allowed=false`
- `playbook_execution_allowed=false`
- `rollback_execution_allowed=false`
- `external_agent_tracking_allowed=false`
- `data_sent_external=false`

## Why Capability Leases Exist

Aegis will eventually need a way to reduce approval fatigue for repeated,
low-risk, narrowly scoped actions. Lease candidates can describe what a future
operator-approved lease might cover before actual lease issuance exists.

Capability leases are relevant for future:

- local provider health probes
- repo audit runner reads
- context retrieval
- memory operations
- model calls
- embeddings and reranking
- web research
- document parsing
- external agent observation
- plugin and vertical pack operations
- playbook replay
- rollback snapshots
- low-risk file writes
- tool actions

The current contract is readiness only. A lease candidate is not an active
lease, not approval, not execution permission, not evidence, and not verifier
success.

## Approval Fatigue Problem

Approval fatigue is a real product risk. Repeated prompts can make operators
approve mechanically. A future lease model can help by making repeated low-risk
actions scoped, bounded, revocable, and auditable.

This sprint does not solve approval fatigue operationally. It only defines the
metadata constraints future lease issuance must satisfy.

## Lease Subject Categories

Supported lease subjects:

- `local_provider_health_probe_future`
- `repo_audit_read_future`
- `repo_inventory_run_future`
- `context_retrieval_future`
- `memory_operation_future`
- `model_call_future`
- `embedding_generation_future`
- `reranking_future`
- `web_research_query_future`
- `document_parse_future`
- `external_agent_observation_future`
- `plugin_operation_future`
- `vertical_pack_operation_future`
- `playbook_record_future`
- `playbook_replay_future`
- `rollback_snapshot_future`
- `low_risk_file_write_future`
- `tool_action_future`
- `unknown`

`unknown` is blocked.

## Risk Tiers

Supported risk tiers:

- `metadata_only`
- `read_only`
- `low_risk_local`
- `medium_risk_local`
- `high_risk`
- `destructive`
- `external_network`
- `cloud_data_transfer`
- `sensitive_data`
- `unknown`

Rules:

- `metadata_only` can remain `proposed`.
- `read_only`, `low_risk_local`, and `medium_risk_local` require operator
  review before any future use.
- `sensitive_data` requires operator review and policy.
- `external_network` and `cloud_data_transfer` require future explicit policy.
- `high_risk` activation is blocked in this contract.
- `destructive` and `unknown` are blocked.

## Lease Scopes

Supported scopes:

- `session_scoped`
- `project_scoped`
- `repository_scoped`
- `path_scoped`
- `tool_scoped`
- `provider_scoped`
- `model_scoped`
- `context_scoped`
- `memory_scoped`
- `web_domain_scoped_future`
- `external_agent_scoped_future`
- `disabled`
- `unknown`

Rules:

- `session_scoped` requires `session_ref`.
- `project_scoped` requires `project_ref`.
- `repository_scoped` requires `project_ref` and `repository_ref`.
- `path_scoped` requires `project_ref`, `repository_ref`, and bounded
  relative `path_prefixes`.
- `tool_scoped` requires explicit `allowed_tools`.
- provider/model/context/memory subjects require matching explicit scope
  metadata.
- `disabled` and `unknown` are blocked.

## Lease Lifecycle States

The contract models these lifecycle states:

- `proposed`
- `requires_policy`
- `requires_identity_scope`
- `requires_context_policy`
- `requires_memory_governance`
- `requires_provider_health`
- `requires_human_approval`
- `ready_for_operator_review`
- `active_future_only`
- `denied`
- `expired`
- `revoked`
- `superseded`
- `blocked`
- `unknown`

This sprint never returns an active usable lease. `active_future_only`, if used
later, must remain metadata-only and non-dispatchable until a separate boundary
sprint proves active lease storage/use safe.

## Lease Constraints

Lease candidates may include:

- `lease_id`
- `lease_subject`
- `lease_scope`
- `risk_tier`
- `namespace`
- `project_ref`
- `repository_ref`
- `session_ref`
- `path_prefixes`
- `allowed_tools`
- `allowed_provider_classes`
- `allowed_model_roles`
- `allowed_context_categories`
- `allowed_memory_categories`
- `allowed_domains_future`
- `max_actions`
- `max_duration_seconds`
- `expires_at_metadata`
- `requires_evidence_plan`
- `requires_verifier_plan`
- `requires_negative_evidence_on_failure`
- `requires_redaction`
- `requires_secret_safe_logging`
- `requires_operator_review`
- `revocable`
- `source_refs`
- `provenance`
- `limitations`
- `unknowns`

Rules:

- `max_duration_seconds` must be positive and bounded.
- `max_actions` must be positive and bounded.
- lease candidates must be revocable.
- source refs or provenance are required.
- lease metadata cannot contain secret/credential scopes.
- lease metadata cannot authorize surveillance or productivity scoring.

## Hard Blocked Scopes

The validator blocks:

- unknown or disabled scope
- wildcard/all tool/model/provider/context/memory/domain scopes
- broad filesystem scope
- absolute paths
- external paths
- home/root/global paths
- path traversal
- secret, credential, token, API key, or `.env` path/scope markers
- surveillance/productivity scoring scopes
- destructive risk
- unknown risk
- high-risk activation
- unbounded duration
- unbounded action count
- non-revocable leases

## Relationship To Policy-as-Code Extension

Policy-as-code metadata is required. A blocked policy extension blocks lease
readiness. Policy metadata cannot create a lease, activate a lease, use a
lease, or override other governance boundaries.

## Relationship To Identity Scope

Identity Scope is required for session, project, repository, and path-scoped
lease candidates. Identity metadata cannot authorize runtime dispatch or active
lease use.

## Relationship To Memory Governance

Memory Governance is required for `memory_operation_future`. A lease candidate
cannot write memory, retrieve memory, refresh memory, or use memory as
authority.

## Relationship To Context Policy

Context Policy is required for `context_retrieval_future`. A lease candidate
cannot retrieve context, create a context package, route context to a provider,
or treat context as permission.

## Relationship To Model Auto Mode

Model Auto Mode is required for model-call, embedding, and reranking lease
candidates. Auto Mode candidate metadata cannot authorize model execution, and
a lease candidate cannot make a model call safe by itself.

## Relationship To Local Provider Health

Local Provider Health readiness is required for local provider health probe
and model-call lease candidates. Provider health readiness remains metadata
only. A lease candidate cannot probe an endpoint or prove provider health.

## Relationship To Repo Audit Runner

Repo Audit/read-plan metadata is required for repo read or inventory run lease
candidates. Lease readiness cannot read files, run inventory, create findings,
or produce evidence.

## Relationship To Web Research Gateway

Web research lease candidates are future-gated. They require a future web
research gateway policy before any query can run. This contract never allows
web queries or external data transfer.

## Relationship To External Agent Oversight

External agent observation is future-gated. Lease candidates cannot track
external agents, score productivity, or authorize surveillance.

## Relationship To Plugin / Vertical Pack

Plugin and vertical pack metadata cannot grant leases. Plugin operation lease
candidates remain future-gated and cannot load, execute, or trust plugin output
as authority.

## Relationship To Playbook / Rollback

Playbook replay and rollback snapshot subjects are future-gated. Lease
candidates cannot replay workflows, create rollback snapshots, execute
rollback, mutate runtime state, or bypass approval/policy.

## Why Lease Candidate Is Not Active Lease

A candidate only describes a possible future lease. It does not create storage,
does not issue an approval-derived grant, does not mark itself active, and does
not authorize a runtime path. Future active lease work must separately prove:

- storage integrity
- expiry enforcement
- revocation enforcement
- audit records
- evidence expectations
- verifier expectations
- policy re-check at use time
- failure/negative evidence behavior

## Why Lease Is Not Evidence Or Verifier Success

Evidence must come from backend-owned runtime events and evidence capture.
Verifier success must come from verifier checks. A lease candidate can require
future evidence/verifier plans, but it cannot create evidence, verify an action,
or hide missing/failed evidence.

## Why Lease Cannot Override Policy

Policy remains the controlling boundary. A future lease must be derived from
policy and approval metadata and must be re-checked at use time. Context,
memory, model output, plugin manifests, frontend projections, tool simulation,
Mission Control wording, compliance/passport metadata, and repo-audit metadata
cannot grant a lease or activate one.

## Intentionally Not Done

This sprint intentionally did not:

- implement lease storage
- issue leases
- activate leases
- use leases
- implement approval UI
- add runtime/API/frontend behavior
- probe providers
- call models
- read repo files
- retrieve memory or context
- query web
- execute plugins, playbooks, rollback, tools, MCP, or APIs
- mutate runtime, journal, evidence, or replay
- create evidence or verifier success

## Future Implementation Notes

A future lease implementation would need:

- immutable lease records
- expiry enforcement
- revocation enforcement
- use counters
- scope matching
- policy re-checks at use time
- audit/journal events
- negative evidence on failed lease use
- backup/restore/replay/hash-chain gates for cleanup-like subjects
- explicit operator approval binding
- tests that prove approval alone and lease alone are not execution permission

## Remaining Risks

- Lease concepts can be misread as permission if UI wording is careless.
- Broad scopes and long durations remain dangerous.
- Future low-risk action shortcuts can create approval fatigue if not audited.
- Provider/model/repo/web/memory subjects each need separate execution-boundary
  sprints before lease use can be considered.
- Active lease storage and revocation are intentionally unresolved.
