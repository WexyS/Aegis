# MCP / Tool Gateway Readiness
## 1. Decision

- Decision: `MCP_TOOL_GATEWAY_READINESS_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T03:21:12+03:00`
- Repository checkpoint before sprint: `0bcf8f842bc8edc2af2207fed4a16c7dea491231`
- Foundation tag: `foundation-baseline`

This sprint defines the future MCP/tool gateway readiness contract as
documentation only. It does not implement an MCP Gateway, tool registry,
runtime endpoint, tool execution path, MCP server startup, credential access,
browser/file/message/API automation, plugin/skill execution, vertical-pack
execution, External API/SDK integration, model-tool wiring, memory-tool wiring,
or runtime behavior change.

The gateway contract exists to keep tool availability, discovery, manifests,
model suggestions, memory preferences, frontend state, and plugin registration
from becoming permission.

## 2. Gateway Non-Authority Rules

Tool gateway metadata is non-authoritative.

The following are not permission:

- tool discovery
- tool manifest
- tool schema
- MCP server reachability
- MCP advertised tool list
- plugin registration
- skill registration
- vertical-pack registration
- model tool-call output
- memory preference
- Context Compiler package
- frontend state
- approval by itself
- lease by itself

Tool output is not:

- evidence by itself
- verifier success
- training truth
- policy truth
- approval
- lease creation or refresh authority
- runtime health authority
- debt, replay, evidence, or resource warning authority

Tool output cannot override policy, create approval, create or refresh leases,
make `runtime_health` healthy, hide historical evidence debt, hide unknown-era
evidence issues, hide replay diagnostics debt, or hide resource warnings.

Unknown tools, unknown capabilities, unknown risk tiers, missing manifests,
missing policy rules, frontend-derived permissions, model-derived permissions,
memory-derived permissions, context-derived permissions, and plugin-derived
permissions are denied by default.

## 3. Tool and MCP Capability Taxonomy

These are future capability categories. They are documentation only and do not
register tools in runtime.

| Capability category | Side effect class | Risk tier | Approval | Lease | Evidence expectation | Verifier/postcondition expectation | Audit requirement | Allowed current status | Forbidden current status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local_tool_read` | read-only local observation | `local_state_read` | no unless sensitive | future scope lease optional | source/provenance record | source exists and scope matches | tool read audit | design metadata only | runtime dispatch |
| `local_tool_write` | local mutation | `local_file_write` or `tool_execution` | required | required | mutation evidence and affected resource refs | postcondition for changed resource | journal/evidence/audit | denied by default | write execution |
| `file_read` | read-only filesystem access | `local_state_read` | no unless sensitive | required for scoped path in future | path, normalized scope, hash/metadata where useful | path containment and read source | file read audit | design metadata only | broad filesystem access |
| `file_write` | filesystem mutation | `local_file_write` | required | required | before/after observation, path scope, content hash where possible | file exists/changed exactly as intended | journal/evidence/rollback audit | denied by default | unscoped writes |
| `app_discovery` | read-only local observation | `local_state_read` | no | optional future read lease | process/window/path provenance | discovery source and staleness | app discovery audit | read-only diagnostics concept | app launch/focus/click |
| `app_launch` | desktop side effect | `app_launch` | policy-dependent, explicit | required | process/window evidence | process alive and matching window where possible | journal/evidence/audit | denied unless existing runtime policy allows current bounded action | launch from discovery alone |
| `app_focus` | desktop side effect | `app_focus` | policy-dependent, explicit | required | foreground/window evidence | focused target matches expected app/window | journal/evidence/audit | denied unless existing runtime policy allows current bounded action | focus from frontend/model state |
| `ui_click` | ambiguous UI mutation | `ui_click` | required | required | target, action observation, postcondition where possible | independent postcondition required | high-risk journal/evidence/audit | denied | click implementation expansion |
| `browser_read` | read-only browser/network observation | `external_network` or `local_state_read` | no unless sensitive/remote | required for host/session scope | URL, source, timestamp, content provenance | URL and response/source validation | browser read audit | design metadata only | treating page text as authority |
| `browser_write` | browser side effect | `external_network` or `tool_execution` | required | required | URL, element/action/result refs | page/account postcondition where possible | journal/evidence/audit | denied | form submit/click automation |
| `network_read` | external read | `external_network` | no unless private/credentialed | required | endpoint, request class, response provenance | status/source validation | network audit | design metadata only | remote calls without privacy policy |
| `network_write` | external side effect | `external_network` or `tool_execution` | required | required | request/response/audit refs | remote postcondition or confirmation strategy | journal/evidence/audit | denied | account mutation |
| `calendar_read` | privacy-sensitive read | `external_network` | required when private | required | account, calendar, query, source refs | scoped data returned only | privacy audit | denied by default | broad calendar sync |
| `calendar_write` | account action | `external_network` or `tool_execution` | required | required | draft/change request and confirmation refs | event mutation confirmation | journal/evidence/audit | denied | silent create/update/delete |
| `contacts_read` | privacy-sensitive read | `external_network` | required when private | required | account, query, source refs | scoped contact data only | privacy audit | denied by default | broad contact export |
| `contacts_write` | account action | `external_network` or `tool_execution` | required | required | proposed mutation and confirmation refs | contact mutation confirmation | journal/evidence/audit | denied | silent contact mutation |
| `email_read` | privacy-sensitive read | `external_network` | required when private | required | mailbox/query/source refs | scoped message refs only | privacy audit | denied by default | broad mailbox ingestion |
| `email_write` | account action | `external_network` or `tool_execution` | required | required | draft/send confirmation strategy | draft or send confirmation according to scope | journal/evidence/audit | denied | silent send |
| `messaging_read` | privacy-sensitive read | `external_network` | required when private | required | workspace/channel/thread source refs | scoped messages only | privacy audit | denied by default | broad message export |
| `messaging_write` | account action | `external_network` or `tool_execution` | required | required | draft/send confirmation strategy | delivered/draft confirmation | journal/evidence/audit | denied | silent post/send |
| `document_read` | read-only content access | `local_state_read` or `external_network` | no unless sensitive | required for scoped source | document id/path/source refs | content provenance and scope | document read audit | design metadata only | unscoped document ingestion |
| `document_write` | content mutation | `local_file_write` or `external_network` | required | required | before/after or provider confirmation refs | saved document postcondition | journal/evidence/rollback audit | denied | silent overwrite |
| `code_read` | repo/source read | `local_state_read` | no unless sensitive | optional scoped read lease | path/commit/source refs | repo containment and revision refs | repo read audit | allowed only through existing human/dev workflow, not gateway runtime | treating stale code as current truth |
| `code_write` | repo/source mutation | `local_file_write` | required through dev workflow | required for future runtime writes | diff, tests, source refs | file diff and validation result | git/test/audit | denied for gateway runtime | self-modifying runtime |
| `repo_audit_read` | read-only repo analysis | `local_state_read` | no | optional scoped read lease | commit/path/source refs | source traceability | repo audit | design/read-only only | automated mutation |
| `plugin_action` | extension action | `plugin_execution` | required for side effects | required | plugin action evidence | plugin-specific postcondition | plugin/journal/evidence audit | denied | manifest-as-permission |
| `vertical_pack_read` | pack-scoped read | `local_state_read` or `external_network` | no unless sensitive | required for namespace/tenant scope | pack/source/provenance refs | scoped read validation | pack audit | design/read-only only | cross-namespace leakage |
| `vertical_pack_write` | pack-scoped mutation | `tool_execution` or `plugin_execution` | required | required | pack action evidence and rollback plan | pack-specific postcondition | journal/evidence/pack audit | denied | pack self-authorization |
| `cleanup_archive` | preservation mutation | `cleanup_archive` | required plus operator boundary | required | backup, restore rehearsal, replay, hash-chain refs | archive integrity and restore proof | cleanup audit | readiness only | archive execution |
| `cleanup_compaction` | source-facing cleanup risk | `cleanup_compaction` | required plus operator boundary | required | backup, restore rehearsal, replay, hash-chain refs | compaction parity proof | cleanup audit | readiness only | compaction execution |
| `destructive_system_change` | destructive mutation | `destructive_system_change` | required plus explicit boundary | required | strong evidence and rollback/irreversibility analysis | independent postcondition mandatory | high-risk audit | denied | execution by default |

`allowed current status` never means gateway dispatch is allowed in this
sprint. It means only that the category may be described as future metadata or
reviewed against existing non-runtime policy documents.

## 4. Risk Tier Model

This readiness contract aligns with the existing post-foundation policy
extension. Current helper output remains non-dispatchable:

- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_policy_extension`

| Risk tier | Side effect class | Current gateway status | Required future controls |
| --- | --- | --- | --- |
| `read_only` | no direct mutation | review-only metadata | provenance, scope, staleness |
| `local_state_read` | local observation | review-only metadata | source refs and privacy scope |
| `local_file_write` | local filesystem mutation | denied | approval, scoped lease, evidence, rollback |
| `app_launch` | desktop process/window side effect | denied except existing explicit bounded runtime behavior | policy, approval where required, verifier evidence |
| `app_focus` | desktop foreground/window side effect | denied except existing explicit bounded runtime behavior | policy, approval where required, verifier evidence |
| `ui_click` | ambiguous UI mutation | denied | explicit target contract, approval, lease, postcondition |
| `external_network` | remote read/write boundary | denied | privacy, tenant, credential, network policy |
| `tool_execution` | arbitrary tool side effect | denied | manifest, policy, approval, lease, evidence, audit |
| `memory_write` | persistent memory mutation | denied | Memory Governance, approval where sensitive, audit |
| `model_routing` | provider/cost/privacy decision | denied | model provider/lifecycle/resource policy |
| `plugin_execution` | extension side effect | denied | plugin policy, approval, lease, evidence, rollback |
| `cleanup_archive` | preservation mutation | denied | operator boundary, backup, restore, replay, hash-chain |
| `cleanup_compaction` | source-facing cleanup risk | denied | operator boundary, backup, restore, replay, hash-chain |
| `destructive_system_change` | destructive mutation | denied | explicit boundary; deny by default |

Additional tool-specific risk notes:

- `external_write`: any write to a remote service needs privacy, tenant,
  account, credential, approval, lease, evidence, and rollback/undo policy.
- `account_action`: calendar, contacts, email, messaging, SaaS, and cloud
  account changes require exact-scope approval and confirmation strategy.
- `irreversible_action`: deletion, sends, payments, security changes, and
  destructive system changes are denied unless a later boundary sprint proves
  controls.
- `credentialed_action`: credentials are backend-owned and never exposed to
  model output, tool output, logs, or training data.
- `privacy_sensitive_read`: private messages, email, contacts, files,
  screenshots, tenant data, and proprietary documents require scope, redaction,
  and privacy policy.
- `tenant_crossing_action`: cross-project or cross-tenant access is denied
  without explicit policy and namespace proof.

## 5. Tool Manifest Contract

Future `ToolManifest` fields:

- `tool_id`
- `tool_name`
- `tool_version`
- `provider`
- `source`
- `transport`
- `local_or_remote`
- `capability_categories`
- `risk_tiers`
- `input_schema`
- `output_schema`
- `side_effects`
- `external_systems`
- `credential_requirements`
- `network_requirements`
- `privacy_class`
- `tenant_scope`
- `namespace_scope`
- `approval_required`
- `lease_required`
- `evidence_expectations`
- `verifier_strategy`
- `rollback_strategy`
- `audit_requirements`
- `rate_limits`
- `timeout_policy`
- `failure_taxonomy`
- `provenance_refs`
- `disabled_by_default=true`
- `authority=false`
- `execution_permission=not_granted_by_tool_manifest`

Rules:

- A manifest is a registration candidate, not permission.
- A valid schema is not permission.
- Side effects must be explicit and conservative.
- Missing side-effect declaration is an invalid manifest.
- Missing evidence, rollback, audit, privacy, tenant, or credential policy
  blocks side-effecting use.
- Manifest drift requires revalidation.
- Manifest version changes require policy review before future use.

## 6. MCP Server Contract

Future `MCPServerDescriptor` fields:

- `mcp_server_id`
- `server_name`
- `transport`
- `endpoint_ref`
- `local_or_remote`
- `tool_list_source`
- `trust_level`
- `authentication_mode`
- `namespace_scope`
- `tenant_scope`
- `allowed_capabilities`
- `denied_capabilities`
- `policy_profile`
- `health_state`
- `discovery_timestamp`
- `provenance_refs`
- `disabled_by_default=true`

Rules:

- MCP server reachable is not permission.
- MCP health is not tool permission.
- MCP advertised tools must be validated against Aegis manifest policy.
- Unknown tools are denied.
- Tool list drift requires revalidation.
- Remote MCP servers require privacy, network, credential, tenant, and cost
  policy before any future use.
- A disabled MCP descriptor cannot be used as a runtime registry.

## 7. Tool Registration Lifecycle

All states default to `dispatch_allowed=false` until a later explicit gateway
implementation sprint changes that with tests.

| State | Dispatch allowed? | Required policy check | Approval/lease/evidence requirements | Allowed transitions | Forbidden transitions |
| --- | --- | --- | --- | --- | --- |
| `discovered` | no | discovery source only | none | `registered_metadata_only`, `blocked_by_policy`, `failed_validation` | `active`, `queued`, `dispatched` |
| `registered_metadata_only` | no | manifest schema and provenance | none | `disabled`, `policy_review_required`, `failed_validation` | execution from metadata |
| `disabled` | no | disable reason | none | `policy_review_required`, `deprecated`, `revoked` | silent enable |
| `policy_review_required` | no | capability/risk/policy mapping | evidence expectation design | `approved_for_read_only`, `approval_required_for_write`, `blocked_by_policy`, `blocked_by_privacy` | runtime dispatch |
| `approved_for_read_only` | no in this sprint | read-only policy | provenance and scoped read lease where required | `lease_required`, `deprecated`, `revoked` | side-effecting use |
| `approval_required_for_write` | no | write policy | exact approval and evidence expectation | `lease_required`, `blocked_by_missing_evidence`, `revoked` | approval-as-execution |
| `lease_required` | no | lease policy | scope, expiry, revocation, audit | `active` in future only, `revoked`, `blocked_by_policy` | lease-as-execution |
| `active` | no in this document; future only | policy recheck at use time | approval, lease, evidence, audit still required | `deprecated`, `revoked`, `quarantined` | bypassing call lifecycle |
| `deprecated` | no | replacement policy | none | `revoked`, `registered_metadata_only` by review | automatic use |
| `revoked` | no | revocation reason | none | none except new review record | reuse |
| `quarantined` | no | quarantine reason | none | `blocked_by_policy`, `failed_validation`, review-only release | dispatch |
| `blocked_by_policy` | no | denied policy reason | none | `policy_review_required` after policy change | silent override |
| `blocked_by_privacy` | no | privacy denial | none | `policy_review_required` after privacy policy change | remote/private use |
| `blocked_by_missing_evidence` | no | evidence gap | evidence design required | `policy_review_required` | execution without verifier |
| `failed_validation` | no | validation failure | none | `registered_metadata_only` after corrected manifest | silent repair |

## 8. Tool Call Lifecycle

Future tool calls must move through explicit non-authority states:

1. `proposed`
2. `schema_validated`
3. `policy_checked`
4. `lease_checked`
5. `approval_pending`
6. `approved`
7. `queued`
8. `dispatched`
9. `result_received`
10. `postcondition_checked`
11. `evidence_recorded`
12. `completed`
13. `failed`
14. `denied`
15. `cancelled`
16. `quarantined`

Rules:

- Proposed tool call is not execution.
- Schema valid is not permission.
- Policy checked is not dispatch by itself.
- Lease checked is not dispatch by itself.
- Approved is not verifier success.
- Queued is not dispatched.
- Dispatched is not verified success.
- Result received is not evidence success.
- Tool output cannot verify itself without independent backend checks.
- Postcondition and evidence are required before verified success.
- Failed, denied, cancelled, and quarantined calls produce diagnostic or
  negative records, not success.

## 9. Evidence and Verifier Expectations

Tool evidence expectations vary by risk:

- Read-only tools require source, scope, timestamp, and provenance records.
- Privacy-sensitive reads require namespace, tenant, account, redaction, and
  query scope records.
- File writes require before/after filesystem observation, path containment,
  content/hash or metadata postcondition where practical, and rollback plan.
- App launch requires process/window verifier evidence.
- App focus requires foreground/window verifier evidence.
- UI click requires target, action observation, and a postcondition wherever
  possible.
- Browser write requires URL, element, action, result, and postcondition
  evidence.
- Network/account writes require request class, response/confirmation, tenant,
  credential boundary, and rollback/undo plan where possible.
- Messaging/email writes require draft/send confirmation strategy and exact
  operator approval for the action/scope.
- Document writes require before/after or provider confirmation evidence.
- Code writes require diff, source refs, tests/validation, and no self-modifying
  runtime shortcut.
- Plugin and vertical-pack actions require pack-specific evidence, evals,
  approval rules, rollback plan, and audit refs.
- Cleanup archive/compaction require backup path, restore rehearsal, replay,
  hash-chain validation, operator boundary approval, and `mutation_performed`
  visibility.
- Destructive actions are denied by default.

Tool output cannot be its own verifier without independent backend checks.

## 10. Approval and Lease Relationship

Approval and leases are separate controls.

Rules:

- Approval may be required for side-effecting actions.
- A lease may scope a future tool capability.
- Approval alone is not execution permission.
- Lease alone is not execution permission.
- Approval plus lease still requires policy recheck.
- Policy check remains required at use time.
- Expired lease denies use.
- Revoked lease denies use.
- Scope-mismatch lease denies use.
- Missing audit or evidence expectation denies use.
- Approval must reference the exact action, tool, capability, tenant, namespace,
  and scope where required.
- Hygiene or bulk approval cannot become a bulk grant.
- Approval is not verified success.

## 11. Policy-as-Code Relationship

Policy decides whether a future tool can be proposed or considered. It does not
automatically dispatch.

Required policy behavior:

- Unknown capability denied.
- Unknown risk tier denied.
- Missing policy rule denied.
- Missing manifest denied.
- Invalid manifest denied.
- Frontend-derived permission denied.
- Model-derived permission denied.
- Memory-derived permission denied.
- Context-derived permission denied.
- Plugin/skill/vertical-pack-derived permission denied.
- Cleanup boundary denied unless an explicit operator boundary exists.

Existing post-foundation policy helper semantics remain unchanged:

- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_policy_extension`

## 12. LLM and Model Relationship

LLMs may suggest `ToolCallProposal` objects only.

Rules:

- Model tool-call output remains non-authoritative.
- Tool-call capable model does not grant tool permission.
- Model provider readiness is not tool gateway readiness.
- Hallucinated tools are denied.
- Unknown tools are denied.
- Model cannot select a higher-risk tool path.
- Model output requires schema validation and policy checks.
- Model output cannot satisfy approval, lease, evidence, postcondition, or
  verifier success.
- Model output cannot hide tool, provider, resource, privacy, timeout, or
  policy failures.

## 13. Memory Relationship

Memory may inform tool proposals only as context.

Rules:

- Memory cannot authorize tool calls.
- Remembered user preference cannot bypass approval.
- Project memory cannot override tool policy.
- Skill/plugin memory cannot grant tool permission.
- Quarantined memory cannot drive tool selection as truth.
- Stale memory must be refreshed before operational use.
- Tool output cannot write memory automatically.
- Memory cannot create, activate, refresh, or expand leases.

## 14. Context Compiler Relationship

Context packages may include tool metadata only as references after future
contract work.

Rules:

- Context cannot authorize tool calls.
- Context cannot hide risk, debt, replay, evidence, or resource warnings.
- Context package output must preserve `authority=false`.
- `context_package_id` and `source_refs` should travel with future tool proposal
  provenance.
- Raw journal remains excluded by default.
- Tool metadata in context remains non-authoritative and requires backend
  validation and policy recheck.

## 15. Model Lifecycle and Resource Relationship

Tool calls may require models, but model readiness is not tool permission.

Rules:

- Model/router failure must not be hidden by tool fallback.
- Tool output may increase context size and resource pressure.
- Resource-blocked states must block unsafe tool/model combinations.
- Critical disk, VRAM, RAM, timeout, unavailable provider, and privacy-blocked
  states remain structured failures.
- Remote provider plus remote tool combinations require explicit privacy, cost,
  credential, and tenant policy.
- Fallback cannot erase original model or tool failure.

## 16. Training Governance Relationship

Tool traces are not training data by default.

Rules:

- Successful tool traces require evidence refs before becoming dataset
  candidates.
- Failed tool calls are negative/error candidates only.
- Denied tool calls are refusal/policy candidates only.
- Cancelled tool calls are not success.
- Hallucinated tools are negative tool-safety examples.
- Frontend/tool output is not training truth.
- Tool datasets require redaction, provenance, namespace, eval, and review
  gates.
- Secrets, credentials, private messages, screenshots, and tenant data must not
  enter training without explicit governance and redaction.

## 17. Memory, External API, SDK, and Tenant Relationship

External projects require tenant/project scoped tool permissions.

Rules:

- API keys must have tool scopes.
- Credentials are backend-owned and never model-owned.
- No cross-project tool access without policy.
- External integration tools are disabled by default.
- External API/SDK access requires a separate readiness sprint.
- Glossa, language-learning, customer, freelance, and other external projects
  require separate tool namespaces.
- Tenant data must not leak through tool output, model context, memory,
  training data, logs, or frontend projection.

## 18. Plugin, Skill, and Vertical Pack Relationship

Plugin and pack metadata is proposal metadata only.

Rules:

- Plugin manifest is not permission.
- Skill registration is not permission.
- Vertical pack can propose tool families only.
- Each pack requires allowed tools, forbidden tools, risk tiers, evidence
  expectations, evals, approval rules, rollback plan, privacy policy, and audit
  strategy.
- Pack tools are disabled by default until policy and lease gates exist.
- Plugin/skill/pack action output is untrusted until validated.
- Translation and Glossa pack tools must not define Aegis platform identity.
- Vertical pack write actions require the same generic gateway, policy, lease,
  approval, evidence, and audit rules as core tools.

## 19. Sandbox and Credential Boundary

Sandbox and credential rules:

- Credentials are never exposed to model output.
- Credentials are never exposed to tool output unless explicitly redacted and
  policy-approved for display.
- Credentials are never logged in training data.
- Tool credential access must be backend-owned.
- Use least privilege per tool.
- Use scoped API keys.
- No broad filesystem access by default.
- No shell execution by default.
- No browser/file/message/API automation by default.
- No destructive system actions by default.
- Remote network tools require explicit network, privacy, credential, and
  tenant policy.
- Tool sandboxes must define allowed paths, hosts, methods, credentials,
  timeouts, rate limits, output size limits, and audit refs.

## 20. Failure Taxonomy

Future `ToolFailure` states:

- `unknown_tool`
- `disabled_tool`
- `missing_manifest`
- `invalid_manifest`
- `schema_validation_failed`
- `policy_denied`
- `approval_required`
- `approval_denied`
- `lease_required`
- `lease_invalid`
- `lease_expired`
- `credential_missing`
- `credential_invalid`
- `timeout`
- `rate_limited`
- `network_unreachable`
- `privacy_policy_blocked`
- `tenant_scope_violation`
- `sandbox_violation`
- `side_effect_unverified`
- `postcondition_failed`
- `evidence_missing`
- `tool_error`
- `rollback_failed`
- `unknown_error`

Failures are diagnostic or negative records. They are not success, evidence
success, verifier success, training truth, or runtime health success.

## 21. Future API and Contract Sketch

Documentation-only contract names:

- `ToolManifest`
- `MCPServerDescriptor`
- `ToolRegistrationDecision`
- `ToolCallProposal`
- `ToolCallPlan`
- `ToolCallPolicyDecision`
- `ToolCallLeaseCheck`
- `ToolCallApprovalRequest`
- `ToolExecutionRecord`
- `ToolResult`
- `ToolPostconditionCheck`
- `ToolEvidenceExpectation`
- `ToolFailure`
- `ToolAuditRecord`

Common non-authority fields:

- `authority=false`
- `execution_permission=not_granted_by_tool_gateway`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_tool_output=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_approval_if_side_effecting=true`
- `tool_id`
- `capability_category`
- `risk_tier`
- `namespace_scope`
- `tenant_scope`
- `provenance_refs`
- `audit_refs`
- `failure_state`

These contracts must remain non-executing until a later explicit implementation
sprint adds tests proving they cannot dispatch.

## 22. Gate Criteria Before MCP or Tool Implementation

Required gates before implementation:

1. Gateway readiness document complete.
2. Policy capability mapping accepted.
3. Lease relationship accepted.
4. Approval relationship accepted.
5. Evidence expectations accepted.
6. Tool manifest schema accepted.
7. MCP server descriptor accepted.
8. Credential and sandbox policy accepted.
9. Tenant/project namespace model accepted.
10. No-authority tests designed.
11. Schema validation tests designed.
12. Policy-deny tests designed.
13. Hallucinated tool tests designed.
14. Side-effect evidence tests designed.
15. Failure taxonomy tests designed.
16. Rollback strategy documented.
17. Privacy/redaction policy accepted for external and credentialed tools.
18. Resource/cost policy accepted for remote tool/model combinations.
19. No generated, tool-output, model, dataset, adapter, vector DB, screenshot,
    temp, runtime log, or local environment artifacts staged.

No MCP/tool implementation should begin while these gates are absent.

## 23. Future Test Plan

No tests are added in this documentation-only sprint because no type helper,
runtime surface, endpoint, registry, gateway, tool call, MCP descriptor loader,
credential path, or automation path is introduced.

When pure contracts are added, tests should assert:

- tool discovery grants no permission
- tool manifest grants no permission
- MCP reachable grants no permission
- model tool-call output grants no permission
- memory/context/plugin/frontend output grants no tool permission
- unknown tool is denied
- hallucinated tool is denied
- unknown capability is denied
- unknown risk tier is denied
- missing manifest is denied
- invalid schema is denied
- approval alone is not execution permission
- lease alone is not execution permission
- result received is not verifier success
- failed, denied, cancelled, and quarantined calls are not success
- side-effecting actions require evidence expectations
- tool output cannot verify itself
- cleanup/archive/compaction remain blocked without operator boundary
- no MCP server is started
- no tool is called
- no credential is accessed
- no runtime state, journal, evidence, replay, snapshot, memory, backend,
  frontend, or policy semantics are mutated

## 24. Non-Goals

- No MCP Gateway implementation.
- No executable tool registry.
- No tool execution.
- No MCP server startup.
- No MCP server probing.
- No browser automation.
- No file automation.
- No message, email, calendar, contact, document, or external API automation.
- No shell execution.
- No credential access.
- No plugin, skill, or vertical-pack execution.
- No External API/SDK implementation.
- No model output connected to tool execution.
- No memory or context connected to tool execution.
- No frontend authority change.
- No runtime endpoint.
- No approval, policy, verifier, evidence, journal, replay, snapshot,
  runtime-health, backend, or frontend semantic change.
- No cleanup/archive/compaction execution.
- No generated artifacts, tool outputs, model files, datasets, adapters,
  vector DB files, screenshots, runtime logs, temp files, fake success, fake
  evidence, fake verification, fake telemetry, fake health, or fake metrics.

## 25. Remaining Risks

- No concrete gateway schema or validator exists yet.
- No no-authority tests exist for gateway-specific contracts yet.
- No manifest drift detection exists yet.
- No MCP server descriptor validation exists yet.
- No sandbox or credential implementation exists yet.
- No tenant/project namespace enforcement exists yet.
- No external API/SDK readiness contract exists yet.
- Current runtime health still reflects known historical, unknown-era, replay,
  and resource debt.

## 26. Recommended Next Workstream

Recommended next prompt:

`External API / SDK Readiness`

Reason: the gateway readiness contract now defines deny-by-default tool and MCP
boundaries. The next safe design surface is external API/SDK access,
credential scope, tenant/project isolation, and remote integration policy
without calling external services or wiring runtime execution.

Alternative:

`Skill / Plugin Architecture Design`

Use this if external integration is intentionally deferred and the work remains
design-only, disabled by default, and disconnected from runtime dispatch.
