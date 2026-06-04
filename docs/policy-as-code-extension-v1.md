# Policy-as-Code Extension v1

## 0. 2026-06-05 Foundation Hardening Update

- Decision: `POLICY_AS_CODE_EXTENSION_WITH_TESTS`
- Repository checkpoint before sprint: `bb9df1d4066acbb95c258994834dcf40a15d62b4`
- Previous completed sprint: `MEMORY_GOVERNANCE_CONTRACT_WITH_TESTS`
- Foundation tag: `foundation-v1-baseline`

This update adds a second pure policy extension surface:

- `PolicyExtensionDecision`
- `evaluate_policy_extension_request(...)`
- `POLICY_SUBJECT_KINDS`
- `POLICY_ACTION_KINDS`
- `POLICY_OUTCOMES`

The helper classifies future memory, context, model, vector, web research,
repo-audit, external agent, plugin, vertical pack, capability lease, playbook,
rollback, frontend, and MCP policy metadata. It does not call tools, retrieve
context, write memory, call models, read repo files, create leases, replay
playbooks, execute rollbacks, dispatch runtime commands, create evidence, mark
verifier success, or change frontend authority.

Every decision from this extension preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_policy_extension`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_policy=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- all future feature allow flags false
- `requires_backend_validation=true`

The existing runtime guard remains the only place where current runtime policy
can allow existing dispatchable actions after normal guard classification. The
new post-foundation helper is intentionally non-dispatchable.

## 1. Decision

- Decision: `POLICY_EXTENSION_WITH_DENY_DEFAULT_TESTS`
- Recorded at: `2026-05-31T22:50:49+03:00`
- Repository checkpoint before sprint: `bfbb5c40baa812a6eb614613dd3b71470ae4cada`
- Foundation tag: `foundation-v1-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This sprint extends the post-foundation policy-as-code boundary as a
non-executing contract. It does not grant new runtime permissions, connect
future modules to execution, or change existing approval, verifier, evidence,
journal, replay, command lifecycle, runtime health, or frontend authority
semantics.

## 2. Policy Extension Scope

Authoritative implementation surface:

- `src/aegis/core/policy_boundary.py`

Current runtime boundary remains:

- `evaluate_policy_boundary()`
- `approval_resolution_can_resume()`
- `side_effects_missing_dispatch_contract()`

Added design-time contract surface:

- `POST_FOUNDATION_POLICY_VERSION=post-foundation-policy-extension/1`
- `POST_FOUNDATION_RISK_TIERS`
- `POST_FOUNDATION_CAPABILITY_CATEGORIES`
- `evaluate_capability_policy_contract()`
- `PolicyExtensionDecision`
- `POLICY_SUBJECT_KINDS`
- `POLICY_ACTION_KINDS`
- `POLICY_OUTCOMES`
- `evaluate_policy_extension_request()`

The new helper is pure and not wired to dispatcher, executor, planner, Context
Compiler runtime integration, Memory OS, MCP, Model Router, plugins, skills, or
vertical packs. It always returns `runtime_dispatch_allowed=false` and
`execution_permission=not_granted_by_policy_extension`.

`evaluate_capability_policy_contract()` remains the design-time capability and
risk-tier contract evaluator. `evaluate_policy_extension_request()` is the
future subject/action classifier for the next post-foundation modules. Neither
helper changes `POLICY_DISPATCHABLE_TOOL_NAMES`.

## 2A. Subject, Action, and Outcome Taxonomy

Policy subject kinds:

- `runtime_command`
- `tool_action`
- `memory_operation`
- `context_operation`
- `model_operation`
- `vector_operation`
- `web_research_operation`
- `repo_audit_operation`
- `external_agent_operation`
- `plugin_operation`
- `vertical_pack_operation`
- `capability_lease_operation`
- `playbook_operation`
- `rollback_operation`
- `frontend_request`
- `mcp_output`
- `unknown`

Policy action kinds:

- `read_only_observation`
- `metadata_validation`
- `proposal_only`
- `simulate`
- `dry_run_preview`
- `memory_write`
- `memory_retrieve`
- `memory_delete`
- `memory_export`
- `context_retrieve`
- `context_package`
- `vector_index`
- `embedding_generate`
- `rerank`
- `model_call`
- `cloud_model_call`
- `web_query`
- `repo_file_read`
- `repo_inventory_run`
- `external_agent_observe`
- `external_agent_track`
- `plugin_load`
- `plugin_execute`
- `lease_create`
- `lease_use`
- `playbook_record`
- `playbook_replay`
- `rollback_snapshot`
- `rollback_execute`
- `frontend_authority_claim`
- `mcp_authority_claim`
- `unknown`

Policy outcomes:

- `allowed_metadata_only`
- `allowed_proposal_only`
- `requires_approval`
- `requires_capability_lease`
- `requires_human_review`
- `requires_identity_scope`
- `requires_memory_governance`
- `requires_context_policy`
- `requires_provider_policy`
- `requires_evidence_plan`
- `requires_verifier_plan`
- `blocked_by_policy`
- `blocked_by_privacy`
- `blocked_by_unknown_scope`
- `blocked_by_missing_governance`
- `blocked_by_sensitive_data`
- `blocked_by_frontend_authority`
- `blocked_by_mcp_authority`
- `blocked_by_unimplemented_feature`
- `unsupported`
- `unknown`

`allowed_metadata_only` and `allowed_proposal_only` mean only that policy
metadata is not blocked by this pure classifier. They do not grant approval,
capability, lease, execution permission, evidence, verifier success, runtime
truth, frontend authority, or memory/model/context/tool behavior.

## 2B. Future Feature Rules

- Memory operations require Memory Governance and remain proposal-only.
- Model operations require future Model Auto Mode and provider health policy;
  local model inventory metadata alone is not model-call permission.
- Cloud model calls require future provider, region, terms, and secret policy.
- Context retrieval requires future Context Retrieval Policy; context package
  metadata is still not permission.
- Vector indexing, embedding generation, and reranking require future vector,
  embedding, context, and memory governance policy.
- Web research requires future Web Research Gateway policy and query privacy
  gates.
- Repo file reads require future Repo Audit Runner, source inventory, read-plan,
  evidence, and verifier gates.
- External agent tracking requires future external agent oversight and identity
  scope.
- Plugin execution is blocked unless a future plugin execution policy exists.
- Vertical pack metadata does not create runtime behavior.
- Lease creation/use is blocked unless future Capability Lease policy exists.
- Playbook replay is blocked unless future playbook and lease policy exists.
- Rollback snapshot/execution requires a future rollback contract.
- Frontend authority claims are blocked.
- MCP authority claims are blocked.
- Unknown subject/action is unsupported and requires human review.

## 3. Risk Tier Model

| Risk tier | Side-effect level | Default status | Required approval | Evidence expectation | Replay/journal expectation | Context influence | Memory influence | Frontend influence | Model influence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `read_only` | none | review-only possible | no | no execution evidence | provenance only | context may inform, not authorize | no permission | no authority | no authority |
| `local_state_read` | local observation | review-only possible | no | source/provenance expected | read-only audit trail | context may inform, not authorize | no permission | no authority | no authority |
| `local_file_write` | local mutation | deny unless approved and evidenced | yes | required | journal/evidence required in future execution sprint | cannot reduce risk | cannot approve | cannot authorize | cannot approve |
| `app_launch` | desktop side effect | deny unless approved where required and evidenced | policy-dependent; future gate must be explicit | process/window evidence required | journal/evidence required | cannot prove launch | cannot approve | cannot authorize | cannot approve |
| `app_focus` | desktop side effect | deny unless approved where required and evidenced | policy-dependent; future gate must be explicit | foreground/window evidence required | journal/evidence required | cannot prove focus | cannot approve | cannot authorize | cannot approve |
| `ui_click` | UI mutation/high ambiguity | deny | yes | target, verifier, and postcondition required | journal/evidence required | cannot target or authorize | cannot approve | cannot authorize | cannot approve |
| `external_network` | external side effect | deny | yes | request/response/audit expectation required | journal/evidence required | cannot authorize | cannot approve | cannot authorize | cannot approve |
| `tool_execution` | arbitrary tool side effect | deny | yes | tool-specific evidence required | journal/evidence required | cannot authorize | cannot approve | cannot authorize | cannot approve |
| `memory_write` | persistent context mutation | deny | yes | provenance/audit required | memory audit required | cannot self-authorize | cannot self-authorize | cannot authorize | cannot approve |
| `model_routing` | provider decision | deny until router readiness | yes if changes capability/cost/privacy boundary | routing metadata required | routing audit required | cannot authorize | cannot approve | cannot authorize | cannot approve |
| `plugin_execution` | extension side effect | deny | yes | plugin action evidence required | journal/evidence required | cannot authorize | cannot approve | cannot authorize | cannot approve |
| `cleanup_archive` | preservation action | deny until boundary sprint | yes plus operator boundary | backup/restore/replay/hash evidence required | original hash and audit required | no authority | no authority | no authority | no authority |
| `cleanup_compaction` | source-facing cleanup risk | deny until explicit boundary sprint | yes plus operator boundary | backup/restore/replay/hash evidence required | original hash and audit required | no authority | no authority | no authority | no authority |
| `destructive_system_change` | destructive mutation | deny | yes plus explicit boundary | strong verifier/evidence required | journal/evidence required | no authority | no authority | no authority | no authority |

## 4. Capability Categories

| Capability | Default allow/deny | Authority source | Policy gate | Approval gate | Evidence requirement | Audit requirement | Forbidden shortcuts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `context_compilation` | review-only when policy-registered | backend policy | read-only context policy | no approval for read-only | provenance only | source refs and omitted sections | context cannot grant permission |
| `memory_read` | deny until Memory Governance | backend policy | memory read policy | no approval unless sensitive scope | provenance/staleness | memory read audit | retrieval cannot authorize |
| `memory_write` | deny | backend policy plus future approval | memory write policy | required | provenance/conflict/rollback | memory mutation audit | context/model cannot create memory writes |
| `local_tool_read` | deny until registered | backend policy | tool registry policy | no approval for read-only tools unless sensitive | read provenance | tool audit | tool availability is not permission |
| `local_tool_write` | deny | backend policy plus approval | tool write policy | required | tool-specific evidence | journal/evidence | missing evidence expectation blocks |
| `app_discovery` | review-only when policy-registered | backend policy | read-only discovery policy | no approval | observation provenance | app discovery audit | path/title is not launch proof |
| `app_launch` | deny until explicit action policy | backend policy plus approval when required | app action policy | policy-dependent, explicit | process/window evidence | journal/evidence | path presence cannot authorize launch |
| `desktop_verification` | review-only when policy-registered | backend policy | verifier policy | no approval for read-only verifier | verifier checks | verifier audit | title-only is not deterministic verification |
| `mcp_tool_call` | deny | backend policy plus future lease | MCP gateway policy | required for side effects | tool-call evidence | gateway audit | MCP discovery is not permission |
| `model_provider_selection` | deny until router readiness | backend policy | router policy | required when provider changes capability/cost/privacy boundary | routing provenance | router audit | model output cannot choose authority |
| `plugin_action` | deny | backend policy plus manifest validation | plugin policy | required for side effects | plugin action evidence | plugin audit | manifest is not permission |
| `vertical_pack_read` | review-only when policy-registered | backend policy | pack read policy | no approval unless sensitive scope | provenance | pack audit | pack cannot bypass generic contracts |
| `vertical_pack_write` | deny | backend policy plus approval | pack write policy | required | pack action evidence | journal/evidence/rollback | vertical pack cannot self-authorize |
| `cleanup_inventory` | review-only when policy-registered | backend policy | cleanup inventory policy | no approval for read-only | inventory provenance | maintenance audit | inventory is not cleanup |
| `cleanup_archive` | deny | backend policy plus operator boundary | cleanup archive policy | required | backup/restore/replay/hash evidence | cleanup audit | archive cannot delete source journal |
| `cleanup_compaction` | deny | backend policy plus operator boundary | cleanup compaction policy | required | backup/restore/replay/hash evidence | cleanup audit | compaction cannot rewrite source without boundary sprint |

## 5. Deny-by-Default Rules

The policy extension denies when any of these are true:

- Unknown capability.
- Unknown risk tier.
- Risk tier is not allowed for the capability category.
- Missing policy rule.
- Missing approval for side-effecting risk.
- Missing evidence expectation for executable action.
- Missing operator boundary for archive, compaction, or destructive system
  change.
- Frontend-only authority source.
- Context-derived permission.
- Memory-derived permission.
- Model-derived permission.
- Retrieval-derived permission.
- Plugin or skill manifest-derived permission without backend policy
  registration.
- Tool/MCP discovery without backend policy registration.

Even when the metadata is ready for read-only review, the extension does not
grant runtime dispatch permission. It reports `review_ready` only for
non-executing read-only/local-state-read policy contracts.

## 6. Context Compiler Relationship

Policy rules:

- Context Compiler output cannot grant capability.
- Context Compiler output cannot reduce risk tier.
- Context Compiler output cannot satisfy approval.
- Context Compiler output cannot satisfy evidence.
- Context Compiler output can only provide bounded context for review or
  planning.
- Any future runtime usage must re-check policy after context compilation.
- Context package fields such as `capability_grant` or `execution_permission`
  from an input source must be ignored as authority.

## 7. Capability Lease Relationship

Capability leases are future scoped grants, not implemented in this sprint.

Required future lease rules:

- temporary
- revocable
- provenance-backed
- tied to a policy rule
- tied to a risk tier
- tied to an approval record when side-effecting
- tied to an audit record
- bounded by capability scope and expiry
- never broad or permanent

Forbidden lease sources:

- Context Compiler output
- memory
- retrieval
- model output
- frontend projection
- plugin or skill manifest

## 8. Tool and MCP Relationship

Policy rules:

- Tool availability is not permission.
- MCP tool discovery is not permission.
- Tool call requires backend policy registration, risk tier, approval rules,
  evidence expectation, and audit plan.
- Arbitrary untrusted tool execution is denied.
- Tool manifests must be validated before use.
- Tool/MCP calls must not bypass approval, policy, verifier, evidence, journal,
  or runtime authority.

## 9. Plugin, Skill, and Vertical Pack Relationship

Policy rules:

- Plugin manifest is not permission.
- Skill registration is not permission.
- Every plugin action family requires risk tier, capability scope, evidence
  expectation, tests, rollback, and audit plan.
- Plugin and skill actions cannot bypass approval, policy, verifier, evidence,
  journal, or runtime authority.
- Vertical packs must start read-only or approval-gated.
- Vertical pack write actions require explicit policy, approval, evidence,
  rollback, and eval coverage.

## 10. Cleanup, Archive, and Compaction Relationship

Policy rules:

- Cleanup inventory is read-only.
- Archive execution requires operator approval plus backup, restore, replay,
  hash-chain, and audit gates.
- Compaction requires explicit boundary approval.
- Journal rewrite, truncation, deletion, resequencing, or repair remains
  forbidden without a later boundary sprint.
- Unknown-era evidence must not be reclassified as historical unless trusted
  metadata proves it.
- Runtime health must not be greenwashed by cleanup policy.

## 11. Tests Added

The focused policy tests assert:

- Unknown policy subject/action is unsupported and non-dispatchable.
- Metadata-only policy classification is not execution.
- Proposal-only policy classification is not approval, lease, capability,
  evidence, verifier success, or frontend authority.
- Policy success/evidence/verifier/model-output proof claims are rejected.
- Inputs and related decisions are not mutated.
- Memory write and retrieve require Memory Governance.
- Valid Memory Governance still leaves memory operations proposal-only.
- Secret-like memory operations are blocked.
- Unknown identity blocks persistent memory policy.
- Model calls remain blocked pending future Auto Mode and provider health
  policy.
- Cloud model calls remain blocked pending region, terms, and secret policy.
- Local model inventory metadata alone is not model-call permission.
- Legacy router hints do not allow model calls.
- Context package metadata is not permission.
- Context retrieval, vector indexing, embedding generation, and reranking are
  blocked pending future policy gates.
- Web query and repo file read actions are blocked pending future gateway and
  runner gates.
- External agent tracking, MCP authority claims, and frontend authority claims
  are blocked.
- Plugin review and vertical pack metadata do not allow execution.
- Lease create/use, playbook replay, rollback snapshot, and rollback execution
  are blocked pending future contracts.
- Unsafe related decisions with dispatch, evidence, or verifier claims are
  rejected.
- Future subject/action names are not added to existing dispatchable tool names.
- Unknown capability is denied.
- Context-, memory-, model-, plugin-, and frontend-derived permission is denied.
- Side-effecting risk tiers require approval and evidence expectation.
- Approval plus evidence metadata still does not grant execution permission.
- Cleanup archive and compaction require an explicit operator boundary.
- Read-only context compilation can be `review_ready` but still not dispatchable.

These tests validate the design-time helper only. They do not add executor,
dispatcher, endpoint, frontend, Context Compiler runtime, Memory OS, MCP, Model
Router, plugin, skill, vertical pack, archive, or compaction integration.

## 12. Non-Goals

- No new execution capability.
- No new runtime permission.
- No change to current approval, policy, verifier, evidence, replay, journal,
  command lifecycle, runtime authority, or runtime health semantics.
- No Context Compiler execution integration.
- No Memory OS, MCP Gateway, Model Router, plugin/skill execution, or vertical
  pack execution.
- No cleanup, archive, or compaction execution.
- No frontend authority changes.

## 13. Recommended Next Workstream

Recommended next prompt:

`Capability Lease Design v1`

Reason: the policy extension now defines risk tiers, capability categories, and
deny-by-default rules. The next safe design step is a scoped, revocable,
auditable lease model that still grants no runtime execution until a later
explicit implementation sprint.

Alternative:

`Context Compiler Read-Only Contract Implementation v1`

Use this only if implementation remains read-only, non-authoritative, and
disconnected from planner execution, tool execution, memory mutation, and
command permission.
