# External API / SDK Readiness
## 1. Decision

- Decision: `EXTERNAL_API_SDK_READINESS_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T13:18:33+03:00`
- Repository checkpoint before sprint: `499eb0aed1425948bb6c28bb3445268c360b4d73`
- Foundation tag: `foundation-baseline`

This sprint defines the future External API and SDK readiness boundary as
documentation only. It does not implement an external API, SDK package, runtime
endpoint, authentication store, API key, token, webhook, external service call,
tenant enforcement layer, hosted deployment, or remote execution path.

The readiness contract exists to prevent external callers, SDK clients, API
keys, webhooks, integrations, hosted deployments, and third-party applications
from becoming runtime authority.

## 2. External API and SDK Non-Authority Rules

External API and SDK metadata is non-authoritative.

The following are not permission:

- an API key
- an OAuth token
- an SDK client
- a webhook event
- an integration registration
- a tenant id
- a project id
- an external request
- an API route existing in source code
- an OpenAPI schema
- a client library method
- a successful HTTP request
- an accepted queue item
- a Context Compiler package
- a memory item
- a model output
- a plugin or skill manifest
- frontend state
- approval by itself
- lease by itself

External API and SDK output is not:

- runtime truth
- command truth
- evidence
- verifier success
- approval
- capability grant
- lease creation or refresh authority
- model routing authority
- memory authority
- training truth
- cleanup permission
- runtime health authority

Every future external request must be reduced to a backend-owned proposal,
review, read-only query, or denied result. Runtime dispatch remains forbidden
unless a later explicit implementation sprint adds policy, approval, lease,
evidence, journal, verifier, tenant, and audit gates with tests.

## 3. Integration Classes

| Integration class | Purpose | Default status | Side effect risk | Required future controls | Forbidden current behavior |
| --- | --- | --- | --- | --- | --- |
| `public_read_only_status_api` | expose public project or health metadata | design only | low if scoped | redaction, stable contract, no runtime secrets | endpoint creation |
| `operator_local_api` | local operator control surface | design only | medium to high | local auth, policy, approval, lease, evidence, audit | command execution |
| `sdk_read_only_client` | typed client for read-only summaries | design only | low if scoped | schema versioning, source refs, staleness labels | SDK package creation |
| `sdk_operator_client` | future operator workflows | denied | high | exact scopes, policy, approval, leases, audit | dispatch or mutation |
| `external_project_integration` | external app or project access | denied | medium to high | tenant/project isolation, auth scopes, privacy policy | cross-project access |
| `webhook_ingress` | receive external event notifications | denied | high | signature verification, replay protection, quarantine | event-to-command wiring |
| `webhook_egress` | notify external systems | denied | high | approval, privacy, tenant, rate limit, audit | outbound calls |
| `hosted_control_plane_api` | multi-user hosted Aegis surface | denied | high | tenant isolation, auth, quotas, logging, policy | hosted behavior |
| `third_party_plugin_api` | plugin-facing integration surface | denied | high | manifest validation, policy, lease, sandbox | plugin execution |
| `vertical_pack_api` | pack-specific workflows | denied | medium to high | namespace, evals, approval, evidence | pack write actions |

All integration classes remain future design categories. None are registered,
started, exposed, called, or connected in this sprint.

## 4. API Key and Authentication Model

Future API keys and authentication tokens must be scoped, revocable, auditable,
and backend-owned.

Required future key metadata:

- `key_id`
- `key_version`
- `subject`
- `tenant_id`
- `project_id`
- `scope`
- `capability_categories`
- `risk_tiers`
- `created_at`
- `expires_at`
- `revoked_at`
- `issuer`
- `approved_by`
- `approval_event_id`
- `policy_rule_id`
- `lease_ref`
- `provenance_refs`
- `audit_refs`
- `rate_limit_profile`
- `privacy_profile`
- `disabled_by_default=true`
- `authority=false`
- `execution_permission=not_granted_by_api_key`

Rules:

- API key present is not permission.
- Authenticated request is not approval.
- Token validity is not capability grant.
- OAuth consent is not Aegis policy approval.
- API key scope cannot exceed backend policy scope.
- API key scope cannot create or expand a lease.
- API keys must expire or be revocable.
- Secrets must never be committed, logged, exposed to model output, written to
  memory, copied into training data, or rendered in frontend projections.
- Missing, expired, revoked, overbroad, unknown, or tenant-mismatched keys deny
  the request.

No API key, token, credential file, auth database, or secret store is created in
this sprint.

## 5. Scope Model

Future API/SDK scopes must be explicit, narrow, and machine-checkable.

Scope dimensions:

- tenant scope
- project scope
- user/operator scope
- session scope
- command scope
- capability category scope
- risk tier scope
- read/write mode
- app identity scope
- tool id scope
- memory namespace scope
- model/provider scope
- plugin/skill/vertical pack scope
- cleanup boundary scope
- network/external service scope
- rate limit and quota scope

Rules:

- Broad wildcard scopes are denied by default.
- Scope expansion requires new policy review and, where side-effecting, new
  approval and lease.
- Cross-tenant or cross-project access is denied by default.
- Read-only scope cannot be upgraded to write scope.
- SDK default scope must be read-only or no-op.
- Scope mismatch denies the request.
- Scope absence denies the request.
- Scope cannot satisfy evidence, verifier, approval, policy, or runtime truth.

## 6. Tenant and Project Isolation

External API/SDK access must treat tenant and project identity as first-class
security boundaries.

Required future isolation properties:

- every external request has an explicit tenant/project context or is denied
- tenant/project ids are backend-validated, not client-trusted
- resources are namespace-scoped
- memory retrieval is namespace-scoped
- tool permissions are namespace-scoped
- model/provider requests include privacy and tenant metadata
- training/export candidates preserve namespace labels
- logs and audit records include tenant/project references without leaking
  secrets
- cross-tenant reads and writes are denied unless a later explicit boundary
  sprint approves an administrative path

External project examples such as Glossa, customer workflows, freelance tasks,
and vertical packs must use separate namespaces. They cannot redefine Aegis
platform identity and cannot share memory, tools, providers, datasets, or
runtime authority without explicit policy.

## 7. Public vs Internal API Surfaces

Future API surfaces should be separated before implementation.

| Surface | Audience | Allowed future data | Forbidden data/behavior | Initial posture |
| --- | --- | --- | --- | --- |
| Public repository metadata | unauthenticated readers | project description, docs links, version tags | runtime state, local paths, secrets | static docs only |
| Public health/status | unauthenticated or low-trust clients | limited liveness in hosted mode only | local runtime health details, debt details, commands | not implemented |
| Local operator API | trusted local operator | runtime summaries, approvals, maintenance summaries | bypassing policy, fake health, execution from context | existing local backend only |
| Internal runtime API | backend components | command lifecycle, policy, evidence, verifier, journal | external direct access | internal only |
| SDK read-only API | authenticated client | summaries with source refs and staleness | raw journal by default, secrets, cross-tenant data | future read-only |
| SDK mutation API | authenticated operator client | proposals only until approved | direct dispatch, silent writes, cleanup execution | denied |
| Webhook ingress | external systems | signed event proposals | direct command execution, memory write, tool call | denied |
| Admin API | operator/admin | revocation, audit, policy review | broad permanent grants, hidden mutation | not implemented |

Public surfaces must never expose local runtime secrets, raw journals, private
memory, tenant data, approval grants, API keys, model prompts, screenshots, or
tool outputs by default.

## 8. Candidate Endpoint Design

These endpoint names are candidate contracts only. They are not implemented.

Read-only candidates:

- `GET /api/v1/status`
- `GET /api/v1/foundation/readiness`
- `GET /api/v1/maintenance/summary`
- `GET /api/v1/evidence/summary`
- `GET /api/v1/replay/summary`
- `GET /api/v1/policy/capabilities`
- `GET /api/v1/tools/catalog`
- `GET /api/v1/models/catalog`
- `GET /api/v1/context/packages/{id}`
- `GET /api/v1/audit/events`

Proposal-only candidates:

- `POST /api/v1/commands/propose`
- `POST /api/v1/tools/propose-call`
- `POST /api/v1/memory/propose-write`
- `POST /api/v1/models/propose-generation`
- `POST /api/v1/cleanup/propose-archive`

Administrative candidates:

- `POST /api/v1/auth/keys/propose`
- `POST /api/v1/auth/keys/revoke`
- `GET /api/v1/audit/access`
- `GET /api/v1/tenants/{tenant_id}/projects`

Forbidden first implementation shortcuts:

- direct command dispatch from API request
- direct tool execution from SDK call
- direct memory write from SDK call
- direct model call from SDK call
- direct cleanup/archive/compaction execution
- webhook-to-command execution
- raw journal streaming by default
- endpoint that marks evidence verified
- endpoint that changes runtime health
- endpoint that grants approval or capability from client state

## 9. SDK Principles

Future SDKs should be thin clients over backend-owned contracts.

SDK rules:

- SDK is not runtime authority.
- SDK is not a policy engine.
- SDK is not an approval manager.
- SDK is not an evidence/verifier layer.
- SDK cannot create capabilities or leases.
- SDK cannot infer success from HTTP success.
- SDK cannot hide backend failures or warnings.
- SDK should expose typed failure states.
- SDK should preserve source refs and staleness metadata.
- SDK should default to read-only methods.
- SDK mutation methods should submit proposals only unless later gates allow
  policy/approval/lease/evidence-backed execution.
- SDK logs must redact secrets, tokens, tenant data, and private runtime data.

No SDK package, package metadata, package build, npm/PyPI publishing, or client
library is created in this sprint.

## 10. Request and Response Contract

Future API requests should include:

- `request_id`
- `idempotency_key`
- `tenant_id`
- `project_id`
- `subject`
- `scope`
- `capability_category`
- `risk_tier`
- `intent`
- `input_refs`
- `context_package_refs`
- `lease_refs`
- `approval_refs`
- `policy_rule_refs`
- `client_version`
- `sdk_version`
- `generated_at`

Future responses should include:

- `schema_version`
- `request_id`
- `decision_status`
- `result_status`
- `authority=false`
- `execution_permission`
- `capability_grant=false`
- `approval_grant=false`
- `lease_grant=false`
- `requires_policy_check=true`
- `requires_approval_if_side_effecting=true`
- `requires_evidence_if_executable=true`
- `source_refs`
- `audit_refs`
- `staleness`
- `failure_state`
- `mutation_performed`

Rules:

- HTTP 2xx means request accepted or read succeeded, not verified execution.
- `accepted` is not `approved`.
- `queued` is not `dispatched`.
- `dispatched` is not verified success.
- `completed` is not verified success without evidence/verifier support.
- `denied`, `failed`, `cancelled`, `expired`, `revoked`, and `quarantined`
  remain non-success.

## 11. Error and Failure Taxonomy

Future API/SDK failures should be structured and non-optimistic:

- `unauthenticated`
- `auth_expired`
- `auth_revoked`
- `invalid_token`
- `unknown_api_key`
- `scope_missing`
- `scope_violation`
- `tenant_missing`
- `tenant_scope_violation`
- `project_scope_violation`
- `policy_denied`
- `approval_required`
- `approval_denied`
- `lease_required`
- `lease_invalid`
- `lease_expired`
- `lease_revoked`
- `capability_unknown`
- `risk_tier_unknown`
- `endpoint_disabled`
- `sdk_version_unsupported`
- `schema_validation_failed`
- `idempotency_conflict`
- `rate_limited`
- `quota_exceeded`
- `abuse_detected`
- `privacy_policy_blocked`
- `credential_missing`
- `external_service_unavailable`
- `timeout`
- `resource_pressure_blocked`
- `evidence_missing`
- `verifier_failed`
- `runtime_health_failed`
- `replay_boundary_blocked`
- `unknown_error`

Failures are diagnostic outputs. They do not become success, evidence success,
training truth, or runtime health success.

## 12. Rate Limit, Quota, and Abuse Boundary

Future external API/SDK access requires defensive limits before exposure:

- per-key rate limits
- per-tenant quotas
- per-project quotas
- per-endpoint limits
- request body size limits
- response size limits
- context package size limits
- raw journal export disabled by default
- webhook replay protection
- idempotency keys for proposals
- suspicious request quarantine
- credential abuse detection
- local resource pressure gates
- backoff and retry policy

Rate limit success or quota availability is not permission. Rate limit failure
must remain visible and must not fall back to a higher-privilege path.

## 13. Privacy and Data Handling

Sensitive data classes:

- API keys
- tokens
- session cookies
- local filesystem paths
- command inputs
- runtime journals
- evidence records
- screenshots
- email/messages/calendar/contact data
- memory items
- model prompts and outputs
- tool outputs
- tenant/customer/project data
- proprietary code or documents

Rules:

- Secrets must not be committed, staged, logged, written to memory, exported to
  training, sent to models, or displayed by SDK debug output.
- External API responses must be scoped and redacted.
- Raw journal and raw evidence export require a later explicit boundary sprint.
- Tenant/project data must not cross namespace boundaries.
- Remote providers and external services require explicit privacy policy.
- SDK telemetry is disabled unless later explicitly governed.
- Access logs must avoid secret values and redact sensitive request bodies.
- Data retention must be defined before hosted or multi-tenant deployment.

## 14. Audit and Provenance Model

Every future external request should create or reference audit metadata.

Audit fields:

- `audit_id`
- `request_id`
- `idempotency_key`
- `tenant_id`
- `project_id`
- `subject`
- `api_key_ref`
- `sdk_version`
- `endpoint`
- `capability_category`
- `risk_tier`
- `policy_decision_ref`
- `approval_ref`
- `lease_ref`
- `evidence_expectation_ref`
- `context_package_ref`
- `memory_refs`
- `tool_refs`
- `model_refs`
- `source_refs`
- `decision_status`
- `failure_state`
- `mutation_performed`
- `created_at`

Audit must distinguish:

- request accepted
- proposal created
- approval pending
- approval granted
- policy denied
- lease denied
- dispatched
- verifier failed
- evidence missing
- verified success

Audit entries are not evidence by themselves. They are provenance and
traceability records.

## 15. Policy, Lease, and Approval Relationship

External API/SDK access must preserve the existing policy-as-code and lease
design rules.

Rules:

- API key scope is not policy approval.
- Policy may decide whether a request is reviewable.
- Policy does not automatically create a lease.
- Lease does not override policy.
- Approval does not override policy.
- Approval alone is not execution permission.
- Lease alone is not execution permission.
- API authentication alone is not execution permission.
- Runtime must re-check policy at use time in any future executable path.
- Side-effecting requests require exact-scope approval.
- Executable requests require evidence expectations.
- Cleanup/archive/compaction requires explicit operator boundary approval plus
  backup, restore, replay, hash-chain, and audit gates.

Existing policy helper semantics remain unchanged:

- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_policy_extension`

## 16. Context Compiler Relationship

Context Compiler output cannot:

- create API keys
- authorize API requests
- expand API scope
- satisfy approval
- create or activate leases
- grant execution permission
- mark evidence verified
- hide runtime health failures
- hide known debt
- write memory
- trigger tool/model/planner execution

Compiled context may be referenced by future API requests as provenance only.
The context package non-authority fields must travel with any request using it.
Raw journal remains excluded by default.

## 17. Memory Governance Relationship

Memory cannot:

- authorize API access
- create API keys
- refresh tokens
- expand scopes
- satisfy approval
- create or activate leases
- write itself from external API requests
- cross tenant/project boundaries
- become training data from API logs automatically

Future external memory access requires namespace-scoped policy, privacy review,
redaction, provenance, and audit. External API memory writes must remain denied
until Memory Governance has an implementation boundary with tests.

## 18. MCP and Tool Gateway Relationship

External API/SDK access cannot bypass tool gateway controls.

Rules:

- API route existing is not tool permission.
- SDK method existing is not tool permission.
- MCP server reachable is not permission.
- Tool manifest is not permission.
- Tool discovery is not permission.
- External request can propose a tool call only after gateway contracts exist.
- Tool calls require manifest validation, policy, approval when required, lease,
  evidence expectation, sandbox, credentials, tenant scope, and audit.
- Tool output cannot verify itself and cannot satisfy API success by itself.

No tool, MCP server, credential, browser, file, message, calendar, contact,
document, or external account automation is called in this sprint.

## 19. Model Provider and Lifecycle Relationship

External API/SDK access cannot bypass model provider readiness.

Rules:

- API request cannot force a model call.
- SDK client cannot select a provider as authority.
- Model availability is not permission.
- Model output is not API truth.
- Model output cannot create approval, lease, evidence, or verifier success.
- Remote model use requires privacy, redaction, cost, credential, tenant, and
  provider policy.
- Resource pressure can block model requests.
- Fallback must preserve original provider failures.

No local or remote model endpoint is probed or called in this sprint.

## 20. Training Governance Relationship

External API and SDK traces are not training data by default.

Rules:

- API logs are not automatic dataset sources.
- SDK examples are not runtime truth.
- Failed API requests are failure examples only.
- Denied requests are denial/policy examples only.
- Unknown-era, missing evidence, failed evidence, and frontend-derived states
  must preserve labels.
- API payloads require redaction and tenant/project review before any dataset
  candidate status.
- Secrets, tokens, private messages, screenshots, tenant data, and proprietary
  content are forbidden training material unless a later governance boundary
  explicitly permits redacted use.

No dataset, adapter, vector store, embedding, export, or training artifact is
created in this sprint.

## 21. Skill, Plugin, and Vertical Pack Relationship

External API/SDK access cannot become a plugin or vertical pack bypass.

Rules:

- Plugin manifest is not API permission.
- Skill registration is not API permission.
- Vertical pack registration is not API permission.
- Pack APIs must start read-only or proposal-only.
- Pack write actions require policy, approval, lease, evidence, audit, rollback,
  and eval coverage.
- External project APIs must remain tenant/project scoped.
- Translation, terminology, repo audit, citation, document risk, content, or
  business packs cannot define Aegis platform authority.

No plugin, skill, vertical pack, or pack-specific API behavior is implemented in
this sprint.

## 22. Deployment Modes

Future deployment modes should be treated separately.

| Mode | Intended boundary | Required gates before implementation | Current status |
| --- | --- | --- | --- |
| `local_single_operator` | local Windows operator only | local auth, loopback binding, no external exposure | existing foundation, no new API |
| `local_lan_operator` | trusted LAN operator access | TLS/auth, network policy, tenant/project checks, rate limits | denied |
| `hosted_single_tenant` | one tenant/project hosted Aegis | auth, secrets, audit, privacy, quotas, backups | denied |
| `hosted_multi_tenant` | multiple tenants/projects | strict isolation, tenant tests, admin policy, abuse controls | denied |
| `sdk_offline_read_only` | local read-only client | schema stability, source refs, no secrets | design only |
| `sdk_cloud_connected` | remote integrations | auth, tenant, privacy, quotas, external service policy | denied |

No deployment mode is added, enabled, hosted, or exposed in this sprint.

## 23. Gate Criteria Before API or SDK Implementation

Required gates:

1. External API/SDK readiness document accepted.
2. API surface classification accepted.
3. Public vs internal API boundary accepted.
4. Auth/key/token model accepted.
5. Tenant/project isolation model accepted.
6. Scope model accepted.
7. Rate limit/quota/abuse model accepted.
8. Privacy/redaction policy accepted.
9. Audit/provenance model accepted.
10. Error/failure taxonomy accepted.
11. Policy/capability mapping accepted.
12. Lease relationship accepted.
13. Approval relationship accepted.
14. Evidence/verifier expectations accepted.
15. Context Compiler non-authority contract enforced.
16. Memory Governance boundaries accepted.
17. MCP/tool gateway boundaries accepted.
18. Model provider/privacy/resource boundaries accepted.
19. Training governance boundaries accepted.
20. SDK no-authority tests designed.
21. Endpoint no-dispatch tests designed.
22. Auth/scope/tenant denial tests designed.
23. Secret redaction tests designed.
24. Webhook replay/quarantine tests designed before webhooks.
25. No generated artifacts, API keys, secrets, tokens, logs, screenshots,
    datasets, adapters, vector DBs, model files, or temp files staged.

No External API or SDK implementation should begin while these gates are absent.

## 24. Future Test Plan

No tests are added in this documentation-only sprint because no endpoint, SDK,
auth model, API key, token store, webhook, request handler, tenant checker,
client package, helper, type contract, or runtime surface is introduced.

When pure contracts or endpoints are added, tests should assert:

- API key grants no execution permission
- authenticated request grants no approval
- SDK method grants no permission
- unknown scope is denied
- wildcard scope is denied
- tenant mismatch is denied
- project mismatch is denied
- expired/revoked token is denied
- context-derived permission is denied
- memory-derived permission is denied
- model-derived permission is denied
- plugin/skill-derived permission is denied
- public endpoint cannot expose runtime secrets or raw journals
- read-only endpoint does not mutate runtime state
- proposal endpoint does not dispatch
- webhook input is quarantined and cannot execute
- HTTP success is not verifier success
- API output cannot mark evidence verified
- side-effecting request requires policy, approval, lease, evidence, and audit
- cleanup/archive/compaction remains blocked without explicit boundary gates
- no external service is called by contract tests
- no token, API key, or secret file is created by tests

## 25. Non-Goals

- No External API implementation.
- No SDK implementation.
- No endpoint.
- No auth/key/token store.
- No webhook.
- No external service call.
- No hosted/cloud behavior.
- No tenant enforcement implementation.
- No API docs generator or OpenAPI surface change.
- No package, package metadata, publishing, or workflow change.
- No command execution from external input.
- No planner execution from external input.
- No tool, MCP, memory, model, plugin, skill, or vertical pack integration.
- No cleanup/archive/compaction execution.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  runtime health, backend, frontend, or API semantic change.
- No generated artifacts, API keys, secrets, tokens, datasets, adapters, vector
  DB files, model files, screenshots, runtime logs, temp files, fake success,
  fake evidence, fake verification, fake telemetry, fake health, or fake
  metrics.

## 26. Remaining Risks

- No concrete API schema or route contract exists yet.
- No auth/key/token validation implementation exists.
- No tenant/project namespace enforcement exists.
- No SDK package boundary exists.
- No no-dispatch tests exist for future API endpoints yet.
- No webhook quarantine implementation exists.
- No secret redaction test suite exists for API logs yet.
- Current runtime health still reflects known historical, unknown-era, replay,
  and resource debt.

## 27. Recommended Next Workstream

Recommended next prompt:

`Skill / Plugin Architecture Design`

Reason: API/SDK, MCP/tool gateway, memory, model, policy, lease, Context
Compiler, and training boundaries now have readiness/design contracts. The next
safe architecture surface is plugin and skill design, with manifests treated as
non-authoritative metadata and every pack starting read-only or approval-gated.

Alternative:

`API/SDK Contract Skeleton`

Use this only if it remains pure, non-executing, disabled by default, and
limited to type/schema contracts plus tests proving API keys, SDK clients,
webhooks, context, memory, model output, and plugin metadata grant no runtime
permission.
