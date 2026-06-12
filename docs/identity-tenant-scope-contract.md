# Identity / Tenant Scope Contract
## Decision

IDENTITY_TENANT_SCOPE_CONTRACT_WITH_TESTS

## Scope

This sprint defines a pure identity, tenant, project, workspace, repository,
session, and machine scope contract for future Aegis durable objects.

It does not implement accounts, authentication, login, cloud identity, memory,
model routing, provider calls, persistence, database migrations, external agent
tracking, frontend UI, or runtime behavior.

## Why Identity Scope Exists

Aegis is currently local-first and can operate as a single-user local runtime,
but future memory, persistent context, cloud/local provider routing, repo audit
product records, compliance evidence, developer work passport records, and
external agent oversight need explicit scope boundaries.

Identity scope prevents future durable state from assuming one global operator
forever. It also prevents Aegis project data from leaking into Ultron or any
other project scope.

Identity scope is metadata and validation context, not authority.

## Non-Authority Rules

Identity metadata does not:

- grant permission
- approve actions
- create leases
- create capabilities
- create evidence
- create verifier success
- authorize model calls
- authorize cloud routing
- authorize memory writes or retrieval
- authorize vector indexing
- authorize external agent tracking
- override policy
- prove who physically used the machine

The output contract always keeps:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_identity_scope`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_identity_scope=false`
- `verifier_success=false`
- `memory_write_allowed=false`
- `memory_retrieval_allowed=false`
- `cloud_routing_allowed=false`
- `model_call_allowed=false`
- `context_persistence_allowed=false`
- `vector_index_allowed=false`
- `external_agent_tracking_allowed=false`
- `surveillance_allowed=false`
- `productivity_scoring_allowed=false`

## Single-User Local Assumption And Limits

The safe default is local-only, session-only metadata. A local Windows account
is not treated as verified human identity. One local machine account may later
represent multiple people, profiles, operators, or external agents.

The contract must not infer real identity from OS usernames, local account
names, machine names, home directory names, or environment variables.

## Subject Kinds

Supported subject kinds:

- `local_single_user`
- `local_multi_profile_future`
- `project`
- `workspace`
- `repository`
- `organization_future`
- `external_agent_future`
- `unknown`

`unknown` requires human review and cannot enable persistence or cloud routing.

## Persistence Scopes

Supported persistence scopes:

- `session_only`
- `project_scoped`
- `workspace_scoped`
- `user_profile_scoped`
- `tenant_scoped_future`
- `machine_local_only`
- `disabled`
- `unknown`

Rules:

- default is `session_only`
- `session_only` requires `session_ref`
- `project_scoped` requires `project_ref`
- project and repository scoped objects require `project_ref`
- repository scoped objects require `repository_ref`
- scope metadata alone never allows memory writes or context persistence

## Data Boundaries

Supported data boundaries:

- `local_only`
- `project_local_only`
- `private_repo_local_only`
- `cloud_disallowed`
- `cloud_allowed_later`
- `external_agent_observation_future`
- `unknown`

Rules:

- `local_only`, `project_local_only`, `private_repo_local_only`,
  `cloud_disallowed`, and `unknown` block cloud routing
- `cloud_allowed_later` is future-gated metadata, not cloud permission
- external agent observation remains future-gated metadata only

## Project / Workspace / Tenant Separation

Tenant, workspace, user, and profile refs may be absent in the current local
foundation, but missing values are preserved as explicit unknowns. They are not
converted into success or inferred from the machine.

Cross-project mixing is denied by default. Scope expansion requires a future
explicit policy and identity boundary sprint.

## Aegis vs Ultron Separation

Aegis and Ultron are distinct project scopes. They must not share memory,
context, repo audit records, compliance records, developer passport records, or
provider routing scope unless a future explicit cross-project boundary proves
that safe.

This contract rejects requests that merge Aegis and Ultron project refs.

## Relationship To Memory Governance

Identity scope is a prerequisite for memory governance, but it does not grant
memory writes or memory retrieval. If memory governance is absent, no persistent
memory is allowed.

Future Memory OS work must require project/user/profile/tenant scope where
appropriate and must preserve unknowns instead of inferring identity.

## Relationship To Context Retrieval / Provider Context Budget

Context retrieval and provider context budgets must consume identity scope as a
boundary, not as permission. Project-local and private-repo boundaries block
cloud routing by default. Raw journals, raw evidence, secrets, and private repo
context require future explicit gates.

## Relationship To Model Auto Mode / Cloud Routing

Model Auto Mode cannot override identity scope. Cloud/local provider selection
must re-check identity scope, data boundary, privacy class, provider health,
policy, approval/lease requirements, and evidence expectations before any model
call.

## Relationship To Repo Audit Pack

Repo audit productization must carry `project_ref` and `repository_ref` for
repo-scoped objects. Repo audit metadata cannot bypass identity scope or merge
projects.

## Relationship To Developer Work Passport / Compliance Evidence

Developer passport and compliance evidence records may later reference identity
scope, but they cannot prove human identity, compliance, certification, or work
quality by themselves.

## Relationship To External Agent Oversight

External agent observation is future-gated. This sprint does not implement
tracking, surveillance, productivity scoring, telemetry, or external agent
state.

## Relationship To Policy / Approval / Lease

Policy, approval, and leases remain separate gates. Identity scope cannot grant
approval, leases, capabilities, or execution permission. Future side-effecting
actions must still pass backend policy and evidence/verifier expectations.

## Relationship To Evidence / Verifier

Identity scope is not evidence and cannot mark verifier success. Future evidence
must come from backend-owned runtime or read-only runner paths, not identity
metadata.

## Tests Added

`tests/test_core/test_identity_scope.py` covers:

- valid local session scope is non-authoritative
- project/repository scoped requirements
- missing required fields
- unknown identity and human review
- cloud-blocking data boundaries
- missing project ref for memory/context requests
- cross-project and Aegis/Ultron merge rejection
- user profile scope is not memory permission
- authority/grant/evidence/verifier/model/memory/vector claims are rejected
- frontend/model/cloud/memory/tool/API/MCP behavior claims are rejected
- surveillance/productivity/external agent tracking claims are rejected
- local account and OS username cannot verify human identity
- safe related decisions cannot override identity scope
- unsafe related decisions are rejected
- input and related decisions are not mutated
- outputs never grant runtime, memory, cloud, model, context, or vector authority

## Intentionally Not Done

- No real user accounts.
- No authentication or login.
- No OAuth or cloud identity.
- No database schema or persistence.
- No memory implementation.
- No model routing or provider calls.
- No vector index.
- No context retrieval.
- No external agent tracking.
- No surveillance or productivity scoring.
- No frontend UI.
- No runtime/journal/evidence/replay mutation.

## Future Implementation Notes

Future durable records should include identity scope refs before writing memory,
context, repo audit product records, compliance records, provider routing
decisions, or external agent observation records.

Future work should define how local profiles are created and reviewed without
silently treating the OS username as human identity.

## Remaining Risks

The current runtime still mostly operates with command/session ids rather than a
full durable identity model. This contract is not wired into runtime, memory, or
provider routing. It is a prerequisite for those future boundary sprints, not an
implementation of them.
