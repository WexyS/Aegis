# Skill / Plugin Architecture Design v1

## 1. Decision

- Decision: `SKILL_PLUGIN_ARCHITECTURE_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T13:37:02+03:00`
- Repository checkpoint before sprint: `a1bc774084f141d7c6df533309f0d2dec5dd5aca`
- Foundation tag: `foundation-v1-baseline`

This sprint defines the future Aegis skill, plugin, and vertical-pack
architecture as documentation only. It does not implement a plugin registry,
plugin loader, skill runner, pack runner, dynamic import path, external package
loading, MCP/tool wiring, model wiring, memory wiring, API endpoint, or runtime
execution path.

The architecture exists to keep manifests, registrations, installed packages,
enabled flags, model output, memory preferences, external API scopes, and
frontend state from becoming permission.

## 2. Plugin, Skill, and Vertical Pack Non-Authority Rules

Plugin, skill, and pack metadata is non-authoritative.

The following are not permission:

- plugin manifest
- skill manifest
- vertical pack registration
- installed plugin
- enabled plugin
- installed skill
- enabled skill
- pack metadata
- plugin registration
- skill registration
- external API scope
- SDK client state
- MCP/tool availability
- model output
- memory preference
- Context Compiler package
- frontend state
- approval by itself
- lease by itself

Plugin, skill, and pack output is not:

- evidence by itself
- verifier success
- policy truth
- approval
- capability grant
- lease creation or refresh authority
- runtime health authority
- training truth by default
- Aegis platform identity

Plugin, skill, and pack output cannot:

- override policy, approval, lease, verifier, evidence, journal, or runtime
  truth
- hide current blockers
- hide historical evidence debt
- hide unknown-era evidence issues
- hide replay diagnostics debt
- hide resource warnings
- mark missing evidence as verified
- turn failed or denied actions into success
- make `runtime_health` healthy
- lower risk tier
- create approval
- create, refresh, or expand leases
- execute tools directly
- write memory directly
- call models directly
- call external APIs directly
- redefine Aegis platform identity

Every future pack action must be reduced to a backend-owned read-only result,
proposal, approval-gated action plan, or denial.

## 3. Architecture Definitions

| Type | Purpose | Allowed content | Forbidden content | Authority level | Side-effect potential | Dependency boundary | Current status | Future allowed status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Core Aegis module | trusted runtime component shipped with Aegis | runtime authority, policy, verifier, evidence, journal, maintenance code | plugin-owned policy override, hidden execution | backend authority when explicitly implemented | varies by module | reviewed source, tests, repo contracts | existing only | normal code review and tests |
| Plugin | extension bundle that may contribute manifests, docs, schemas, and future actions | manifest, schemas, docs, eval requirements, proposal templates | direct runtime mutation, dynamic execution by default, credentials | none | denied unless later gated | must go through policy, lease, approval, gateway, evidence | design only | disabled by default, reviewed |
| Skill | narrow capability unit inside a plugin or pack | prompt templates, schemas, examples, evals, proposal logic design | runtime execution, hidden tool calls, policy definitions | none | read/proposal/action depending on policy | no direct tool/model/memory/API access | design only | read-only or proposal first |
| Skill Pack | grouped skills for a workflow area | multiple skill manifests and evals | broad wildcard capability, platform identity rewrite | none | depends on skills | namespace and capability scoped | design only | disabled by default |
| Vertical Pack | domain product layer such as translation or repo audit | domain schemas, glossary rules, evals, data policy | generic Aegis authority, unscoped writes | none | read/proposal/action-gated | tenant/project/domain scoped | design only | read-only or approval-gated |
| Adapter Pack | model or dataset adaptation bundle | adapter metadata, eval report, rollback plan | model authority, policy bypass, runtime truth | none | no runtime side effect by itself | model/training governance | design only | gated after evals |
| Integration Pack | external app/service integration metadata | API scope needs, auth needs, data policy | credential storage, direct external calls | none | high if write-capable | External API/SDK and MCP/tool gateway | design only | proposal-only first |
| Evaluation Pack | tests/evals/security checks for packs | eval cases, expected labels, negative tests | runtime authority, training truth by default | none | none | training governance | design only | encouraged before activation |
| Read-only Pack | pack limited to observation/summarization | source refs, summaries, findings | writes, dispatch, tool calls | none | none | provenance and staleness rules | design only | safest first activation candidate |
| Proposal-only Pack | pack that drafts plans or actions | proposals, uncertainty, required gates | direct execution | none | no direct side effect | backend validation required | design only | after schema/eval gates |
| Approval-gated Action Pack | pack that may eventually execute side-effecting actions | action plan, approval text, evidence expectations, rollback | bypassing approval/lease/evidence | none until executed by backend | side-effecting only through runtime | full policy/lease/approval/evidence gateway | design only | later explicit boundary only |

No definition above creates runtime permission in this sprint.

## 4. Pack Categories

| Pack category | Read/proposal/write profile | Data sensitivity | Model dependency | Tool dependency | Memory dependency | External API dependency | Required evals | Forbidden first version behaviors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `translation_terminology_pack` | read/proposal first; write denied | medium/high for documents | optional translation model | optional document read | glossary namespace only | optional | terminology accuracy, hallucination, namespace leakage | silent document overwrite, platform identity rewrite |
| `glossa_pack` | read/proposal first | high for learner/project data | optional | optional | separate Glossa namespace | possible | domain quality, tenant isolation, memory leakage | cross-project memory, Aegis identity rewrite |
| `language_learning_pack` | read/proposal first | high for learner profile | optional tutor model | optional | learner namespace | optional | pedagogy quality, privacy, progress integrity | unreviewed learner memory writes |
| `repo_audit_pack` | read/proposal first | medium/high for source code | optional code model | repo read only first | project memory refs only | no by default | source traceability, false positive rate, security evals | code write, self-modifying runtime |
| `coding_report_pack` | read/proposal first | high for code/workspace | optional code model | repo read only first | project namespace | no by default | source refs, test-report accuracy | fake tests, direct file mutation |
| `document_analysis_pack` | read/proposal first | high | optional | document read only first | document namespace | optional | redaction, citation/source fidelity | document write/delete |
| `content_generation_pack` | proposal first | medium/high | likely | optional | domain namespace | optional | provenance, plagiarism, brand/domain quality | publishing or sending content |
| `business_automation_pack` | read/proposal first; write later gated | high for account/customer data | optional | external tools later | tenant namespace | likely | privacy, approval bypass, account-action evals | silent SaaS/account changes |
| `freelance_pack` | read/proposal first | high for client/project data | optional | external tools later | tenant/project namespace | likely | tenant isolation, proposal quality, policy bypass | cross-client leakage, direct sends |
| `browser_workflow_pack` | read first; write/click denied | high | optional | browser read only first | task namespace | possible | prompt injection, URL provenance, postcondition evals | click/form submit/browser write |
| `messaging_comms_pack` | read/proposal first; send denied | very high | optional | messaging/email tools later | tenant/account namespace | likely | draft/send boundary, privacy, approval bypass | silent send/post/update |
| `voice_pack` | proposal/media design only | very high | STT/TTS optional | none first | voice namespace | optional | consent, privacy, transcript accuracy | recording, live voice action |
| `vision_pack` | observation design only | very high | VLM optional | screenshot/camera tools later | media namespace | optional | observation-vs-verification, privacy | treating vision as verifier success |
| `model_provider_pack` | metadata/proposal only | high | direct relation | none first | provider namespace | possible | provider failure, privacy, resource gates | model call/router activation |
| `memory_context_pack` | proposal only | very high | optional summarizer | none first | scoped namespace | no by default | staleness, conflict, quarantine, leakage | direct memory write/retrieval |
| `eval_security_pack` | read/eval only | varies | optional critic | test fixtures only | eval namespace | no by default | prompt injection, policy/approval/evidence bypass | runtime mutation, fake pass |

All packs are disabled by default until manifest validation, policy review,
scope review, and eval requirements are satisfied.

## 5. Manifest Contract

Future manifest fields:

- `manifest_version`
- `pack_id`
- `pack_name`
- `pack_type`
- `pack_version`
- `owner`
- `source`
- `trust_level`
- `description`
- `capabilities`
- `capability_categories`
- `risk_tiers`
- `allowed_tools`
- `forbidden_tools`
- `required_tools`
- `model_requirements`
- `memory_namespaces`
- `context_sources`
- `external_api_scopes`
- `tenant_scope`
- `project_scope`
- `data_sensitivity`
- `privacy_requirements`
- `redaction_requirements`
- `approval_requirements`
- `lease_requirements`
- `evidence_expectations`
- `verifier_strategy`
- `rollback_strategy`
- `eval_requirements`
- `training_data_policy`
- `output_schemas`
- `failure_taxonomy`
- `audit_requirements`
- `compatible_aegis_versions`
- `minimum_policy_contract_version`
- `minimum_gateway_contract_version`
- `disabled_by_default=true`
- `authority=false`
- `execution_permission=not_granted_by_plugin_manifest`

Manifest rules:

- Manifest is not permission.
- Manifest cannot create capabilities.
- Manifest cannot reduce risk tier.
- Manifest cannot create approval.
- Manifest cannot create or refresh leases.
- Manifest cannot satisfy evidence.
- Manifest cannot mark verifier success.
- Missing required fields deny activation.
- Unknown capability is denied.
- Unknown risk tier is denied.
- Unknown tool is denied.
- Unknown model/provider is denied.
- Unknown memory namespace is denied.
- Unknown external API scope is denied.
- Broad wildcard scope is denied by default.
- Manifest drift requires review.
- Version change requires revalidation.
- Incompatible pack versions are disabled.
- Revoked manifests cannot be used.

## 6. Lifecycle Model

| State | Dispatch allowed? | Required policy check | Approval/lease/evidence requirements | Allowed transitions | Forbidden transitions |
| --- | --- | --- | --- | --- | --- |
| `discovered` | no | discovery provenance only | none | `registered_metadata_only`, `failed_validation`, `blocked_by_policy` | `active_*`, dispatch |
| `registered_metadata_only` | no | manifest schema and provenance | none | `disabled`, `policy_review_required`, `failed_validation` | execution from registration |
| `disabled` | no | disable reason | none | `policy_review_required`, `deprecated`, `revoked` | silent enable |
| `policy_review_required` | no | capability/risk/policy mapping | evidence expectations designed | `eval_required`, `approved_for_read_only`, `blocked_by_policy`, `blocked_by_privacy` | dispatch |
| `eval_required` | no | eval policy | eval requirements present | `approved_for_read_only`, `approved_for_proposal_only`, `failed_validation` | activation without evals |
| `approved_for_read_only` | no in this sprint | read-only policy | provenance and optional scoped lease | `active_read_only`, `deprecated`, `revoked` | write/proposal-as-execution |
| `approved_for_proposal_only` | no | proposal policy | schema, uncertainty, audit | `active_proposal_only`, `approval_required_for_actions` | execution from proposal |
| `approval_required_for_actions` | no | side-effecting policy | exact approval and evidence expectation | `lease_required`, `blocked_by_missing_evidence`, `revoked` | approval-as-execution |
| `lease_required` | no | lease policy | scope, expiry, revocation, audit | `active_action_gated` in future only, `revoked`, `blocked_by_policy` | lease-as-execution |
| `active_read_only` | no direct dispatch | policy recheck at use time | source/provenance audit | `deprecated`, `revoked`, `quarantined` | writes, tool calls |
| `active_proposal_only` | no direct dispatch | policy recheck at proposal time | proposal schema/audit | `approval_required_for_actions`, `deprecated`, `revoked` | dispatch |
| `active_action_gated` | future only, never by metadata alone | policy recheck at use time | approval, lease, evidence, verifier/postcondition, audit | `deprecated`, `revoked`, `quarantined` | bypassing runtime |
| `deprecated` | no new actions | replacement/deprecation review | none | `revoked`, metadata review only | silent new use |
| `revoked` | no | revocation reason | none | none except new review record | reuse |
| `quarantined` | no | quarantine reason | none | `blocked_by_policy`, `failed_validation`, review-only release | dispatch |
| `blocked_by_policy` | no | denied policy reason | none | `policy_review_required` after policy change | silent override |
| `blocked_by_privacy` | no | privacy denial | none | `policy_review_required` after privacy review | private data access |
| `blocked_by_missing_evidence` | no | evidence gap | evidence design required | `policy_review_required` | execution without verifier |
| `failed_validation` | no | validation failure | none | `registered_metadata_only` after corrected manifest | silent repair |

Lifecycle state alone never grants dispatch. Even a future active state must
pass policy, lease, approval, evidence, verifier/postcondition, and audit gates
at use time.

## 7. Capability and Risk Mapping

| Pack capability | Capability category | Risk tier | Current status | Future controls |
| --- | --- | --- | --- | --- |
| read-only analysis | `vertical_pack_read` or `local_tool_read` | `read_only` or `local_state_read` | design only | provenance, staleness, namespace |
| proposal generation | `vertical_pack_read` | `read_only` | design only | schema, uncertainty, backend validation |
| translation review | `vertical_pack_read` | `read_only` | design only | source/target/glossary refs, evals |
| terminology extraction | `vertical_pack_read` | `local_state_read` | design only | source refs, domain namespace |
| repo read | `local_tool_read` | `local_state_read` | design only | path/commit scope |
| code read | `local_tool_read` | `local_state_read` | design only | repo containment, commit refs |
| code write proposal | `vertical_pack_write` | `local_file_write` | denied | diff proposal, approval, lease, tests, evidence |
| memory candidate proposal | `memory_write` | `memory_write` | denied | Memory Governance, policy, approval where sensitive |
| context summary | `context_compilation` | `read_only` | design only | source refs, non-authority contract |
| model request proposal | `model_provider_selection` | `model_routing` | denied | model provider/lifecycle/privacy/resource gates |
| tool call proposal | `mcp_tool_call` | `tool_execution` | denied | gateway manifest, policy, approval, lease, evidence |
| browser read | `local_tool_read` or `mcp_tool_call` | `local_state_read` or `external_network` | design only | URL/source/provenance, injection handling |
| browser write | `mcp_tool_call` | `tool_execution` or `external_network` | denied | approval, lease, postcondition, evidence |
| external API read | `mcp_tool_call` | `external_network` | denied | tenant, auth, privacy, rate limits |
| external API write | `mcp_tool_call` | `external_network` or `tool_execution` | denied | exact approval, lease, evidence, rollback |
| document read | `local_tool_read` | `local_state_read` | design only | source refs, redaction |
| document write | `local_tool_write` | `local_file_write` | denied | before/after evidence, approval, rollback |
| messaging read | `mcp_tool_call` | `external_network` | denied | tenant/account scope, privacy |
| messaging write | `mcp_tool_call` | `external_network` or `tool_execution` | denied | draft/send strategy, exact approval |
| vertical pack write | `vertical_pack_write` | `local_file_write`, `tool_execution`, or `plugin_execution` | denied | policy, approval, lease, evidence, audit |
| cleanup archive | `cleanup_archive` | `cleanup_archive` | denied | explicit operator boundary, backup/restore/replay/hash |
| cleanup compaction | `cleanup_compaction` | `cleanup_compaction` | denied | explicit boundary sprint |

Rules:

- Read-only does not imply write.
- Proposal does not imply execution.
- Write requires policy, approval, lease, evidence, verifier/postcondition, and
  audit.
- Cleanup/archive/compaction remain special boundary classes.
- Destructive actions are denied by default.

## 8. Relationship to Policy, Lease, and Approval

Policy evaluates whether a pack capability may be considered. Policy does not:

- activate a plugin
- dispatch actions
- create approval
- create or refresh leases
- satisfy evidence
- mark verifier success

Lease rules:

- A lease may scope a future pack capability.
- Lease alone is not execution permission.
- Expired, revoked, missing, or scope-mismatched lease denies use.
- Pack cannot create, refresh, or expand leases.
- Pack output can be provenance only.

Approval rules:

- Approval may be required for side-effecting pack actions.
- Approval alone is not execution permission.
- Approval must reference exact pack, capability, action, tenant/project,
  namespace, tool/model/API scope, and risk where applicable.
- Pack cannot create approval.
- Bulk or hygiene approval cannot become a pack-wide grant.

Policy recheck is required at use time for every future pack capability.

## 9. Relationship to MCP and Tool Gateway

Packs may declare tool needs. Declared tools are not permission.

Rules:

- Tool availability is not permission.
- Tool manifest is not permission.
- MCP server reachability is not permission.
- Pack cannot call tools directly.
- Future tool use must go through MCP/Tool Gateway.
- Gateway policy, approval, lease, evidence, verifier/postcondition, sandbox,
  credential, tenant, and audit rules apply.
- Hallucinated tools are denied.
- Unknown tools are denied.
- Pack-specific tools are disabled by default.
- Tool output cannot verify itself.
- Tool output cannot become pack success without backend validation.

No MCP server, gateway, tool call, shell, browser, file, message, document, or
external API automation is started in this sprint.

## 10. Relationship to External API and SDK

External clients may request pack read or proposal surfaces only in a future
API/SDK sprint.

Rules:

- External API scope is not pack permission.
- SDK method existence is not pack permission.
- API key is not pack permission.
- Tenant/project namespace applies to pack data.
- Pack output cannot cross tenant/project boundaries.
- Glossa, language-learning, customer, and freelance packs require separate
  namespaces.
- External pack actions need API, policy, lease, approval, evidence, and audit
  gates.
- SDK cannot hide pack errors.
- SDK cannot infer pack success from HTTP success.
- Webhook events cannot trigger pack execution.

No API endpoint, SDK package, key, token, webhook, or external service call is
implemented here.

## 11. Relationship to Memory Governance

Packs may request memory namespaces in future. Memory remains non-authoritative.

Rules:

- Pack memory is namespace-specific.
- Pack cannot write memory directly.
- Pack can propose `MemoryCandidate` only.
- Pack memory cannot grant tool permission.
- Pack memory cannot override policy.
- Pack memory cannot create approval or leases.
- Stale, conflicting, or quarantined memory cannot drive pack action as truth.
- Vertical pack memory cannot redefine Aegis platform identity.
- External/customer/Glossa/freelance memory requires tenant/project isolation.

No memory store, vector DB, embedding path, retrieval path, or write path is
created in this sprint.

## 12. Relationship to Context Compiler

Packs may request Context Compiler package input in future. Context remains
non-authoritative.

Rules:

- Context cannot authorize pack actions.
- Context cannot reduce risk tier.
- Context cannot satisfy approval, lease, evidence, or verifier checks.
- Context refs must travel with pack output provenance.
- Raw journal remains excluded by default.
- Known debt markers must remain visible.
- Unknown-era markers must remain preserved.
- Context cannot hide replay diagnostics or resource warnings.
- Pack cannot use context to bypass policy or memory governance.

## 13. Relationship to LLM, Model Provider, and Model Lifecycle

Packs may declare model requirements. Model availability is not pack permission.

Rules:

- Model output remains non-authoritative.
- Pack cannot force model selection.
- Pack cannot call a model directly.
- Provider, lifecycle, resource, VRAM, privacy, cost, and timeout gates apply.
- Model failure must not be hidden by pack fallback.
- Fallback must preserve provider/model provenance and original failure state.
- Pack outputs generated by models are `synthetic_unverified` unless validated.
- Model output cannot create evidence, verifier success, approval, leases,
  runtime truth, or pack activation.
- Critical disk/resource pressure can block model-dependent packs.

No model call, provider probe, router, generation, embedding, STT, TTS, VLM, or
adapter behavior is implemented here.

## 14. Relationship to Training Governance

Pack traces are not training data by default.

Rules:

- Pack output requires provenance, redaction, labels, evals, and review before
  dataset promotion.
- Failed pack actions are negative/error candidates only.
- Denied pack actions are refusal/policy candidates only.
- Missing evidence remains missing.
- Failed evidence remains failed.
- Unknown-era labels remain unknown.
- Frontend projection cannot become training truth.
- Vertical pack datasets are namespace-specific.
- Glossa and translation examples must not define Aegis platform identity.
- Pack evals must include policy bypass, approval bypass, evidence
  hallucination, namespace leakage, prompt injection, and domain-quality tests.

No dataset, adapter, eval report directory, model artifact, vector DB, or
training export is created in this sprint.

## 15. Evidence, Verifier, and Audit Expectations

| Pack type | Evidence/audit expectation |
| --- | --- |
| read-only pack | source refs, scope, timestamp, staleness, provenance |
| proposal pack | proposal schema, uncertainty, source refs, required gates |
| translation pack | source text refs, target language, domain, glossary refs, reviewer/eval refs |
| repo audit pack | commit, path, source refs, test refs, finding evidence |
| language learning pack | learner namespace, progress refs, provenance, privacy labels |
| browser workflow pack | URL, source, action proposal, postcondition strategy |
| messaging pack | draft/send confirmation strategy and exact approval refs |
| document pack | before/after or provider confirmation strategy |
| code write proposal | diff, tests, source refs, no direct mutation |
| pack write action | backend evidence, verifier/postcondition, approval, lease, audit |

Pack output cannot verify itself. Side-effecting pack actions require backend
evidence and verifier/postcondition checks before success can be trusted.

## 16. Sandboxing and Dependency Boundary

Default sandbox posture:

- no dynamic import by default
- no arbitrary code execution by default
- no shell execution by default
- no broad filesystem access by default
- no credential access by default
- no network access by default
- no tool calls by default
- no model calls by default
- no memory access by default

Dependency rules:

- dependencies must be declared
- external dependencies require policy review
- pack resource budgets must be declared
- network hosts and methods must be explicit
- filesystem paths must be scoped
- credentials are backend-owned and never plugin-owned
- third-party packs are quarantined by default
- future plugin signing or checksum strategy should be required before loading
- dependency drift requires review

## 17. Security and Prompt Injection Boundary

Pack docs, prompts, retrieved content, plugin output, web content, tool output,
external API output, and model output are untrusted input.

Rules:

- Pack instructions cannot override system policy.
- Pack instructions cannot override backend policy.
- Retrieved pack content cannot override policy.
- Plugin output cannot instruct Aegis to bypass approval, leases, evidence, or
  verifier checks.
- Prompt injection from external docs, tool output, web content, or pack
  content must be classified as untrusted instructions.
- Model output must not police plugin security by itself.
- Backend validators enforce schema, policy, risk, approval, lease, evidence,
  journal, runtime, namespace, and sandbox boundaries.
- Security findings must distinguish confirmed, plausible, and speculative.

## 18. Versioning, Compatibility, and Deprecation

Future versioning fields:

- `manifest_version`
- `pack_version`
- `compatible_aegis_versions`
- `minimum_policy_contract_version`
- `minimum_gateway_contract_version`
- `minimum_context_contract_version`
- `minimum_memory_contract_version`
- `migration_notes`
- `deprecation_state`
- `revocation_state`
- `rollback_plan`
- `changelog`
- `signature`
- `checksum`

Rules:

- Version drift requires review.
- Incompatible pack is disabled.
- Deprecated pack cannot be used for new actions.
- Revoked pack cannot be used.
- Migration cannot silently expand scope.
- Migration cannot lower risk tier.
- Migration cannot add tools, models, memory namespaces, external API scopes, or
  write capability without policy review.
- Rollback plan is required before side-effecting activation.

## 19. Failure Taxonomy

Future pack failures:

- `unknown_pack`
- `disabled_pack`
- `missing_manifest`
- `invalid_manifest`
- `manifest_drift`
- `incompatible_version`
- `unknown_capability`
- `unknown_tool`
- `missing_policy`
- `policy_denied`
- `approval_required`
- `approval_denied`
- `lease_required`
- `lease_invalid`
- `missing_evidence_expectation`
- `missing_eval`
- `namespace_violation`
- `tenant_scope_violation`
- `privacy_policy_blocked`
- `dependency_missing`
- `model_requirement_unmet`
- `tool_requirement_unmet`
- `memory_namespace_missing`
- `schema_validation_failed`
- `unsafe_output`
- `prompt_injection_detected`
- `sandbox_violation`
- `pack_error`
- `unknown_error`

Failures are diagnostic or negative records. They are not success, evidence
success, verifier success, policy truth, training truth, or runtime health
success.

## 20. Future API and Contract Sketch

Documentation-only contract names:

- `PluginManifest`
- `SkillManifest`
- `VerticalPackManifest`
- `PackRegistrationDecision`
- `PackCapabilityDeclaration`
- `PackActivationRequest`
- `PackActivationDecision`
- `PackRunProposal`
- `PackRunPlan`
- `PackPolicyDecision`
- `PackLeaseCheck`
- `PackApprovalRequest`
- `PackOutput`
- `PackEvidenceExpectation`
- `PackFailure`
- `PackAuditRecord`
- `PackEvalRequirement`

Common non-authority fields:

- `authority=false`
- `execution_permission=not_granted_by_plugin_architecture`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_pack_output=false`
- `verifier_success=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_approval_if_side_effecting=true`
- `pack_id`
- `pack_version`
- `capability_category`
- `risk_tier`
- `namespace_scope`
- `tenant_scope`
- `provenance_refs`
- `audit_refs`
- `failure_state`

These contracts must remain non-executing until a later explicit implementation
sprint adds pure type contracts and tests proving they cannot dispatch.

## 21. Gate Criteria Before Plugin or Skill Implementation

Required gates:

1. Skill/Plugin Architecture document complete.
2. Manifest schema accepted.
3. Lifecycle model accepted.
4. Policy capability mapping accepted.
5. Lease relationship accepted.
6. Approval relationship accepted.
7. Evidence expectations accepted.
8. MCP/Tool Gateway relationship accepted.
9. External API/SDK relationship accepted.
10. Memory namespace model accepted.
11. Context Compiler relationship accepted.
12. Model Provider/Lifecycle relationship accepted.
13. Training Governance relationship accepted.
14. Sandbox/dependency policy accepted.
15. Versioning/deprecation policy accepted.
16. No-authority tests designed.
17. Manifest validation tests designed.
18. Policy-deny tests designed.
19. Namespace leakage tests designed.
20. Prompt injection tests designed.
21. Failed/denied action tests designed.
22. Eval requirement tests designed.
23. Secret/credential redaction tests designed.
24. Resource budget tests designed for model/tool-heavy packs.
25. No generated artifacts, runtime logs, screenshots, temp files, `.next`
    output, model files, dataset files, adapter files, vector DB files,
    tool-output files, plugin packages, API keys, secrets, tokens, or local
    environment files staged.

No plugin, skill, or vertical-pack implementation should begin while these
gates are absent.

## 22. Future Test Plan

No tests are added in this documentation-only sprint because no manifest type,
registry, loader, dynamic import path, plugin runner, skill runner, pack runner,
endpoint, tool wiring, model wiring, memory wiring, or external integration is
introduced.

When pure contracts are added, tests should assert:

- plugin manifest grants no permission
- skill registration grants no permission
- vertical pack metadata grants no permission
- enabled flag grants no execution permission
- unknown pack is denied
- unknown capability is denied
- unknown tool is denied
- missing manifest is denied
- manifest drift is denied
- incompatible version is denied
- context-derived permission is denied
- memory-derived permission is denied
- model-derived permission is denied
- API/SDK-derived permission is denied
- tool availability grants no pack permission
- approval alone is not execution permission
- lease alone is not execution permission
- pack output cannot create evidence or verifier success
- failed and denied pack actions are not success
- namespace leakage is denied
- prompt injection content remains untrusted
- no plugin code is imported or executed
- no MCP server is started
- no tool, model, memory, API, or runtime state is touched

## 23. Non-Goals

- No plugin registry.
- No plugin loading.
- No skill execution.
- No vertical pack execution.
- No dynamic imports.
- No plugin code execution.
- No MCP server startup.
- No tool calls.
- No browser, file, message, document, or external API automation.
- No API/SDK endpoint.
- No model call, provider probe, model router, or generation path.
- No memory write, retrieval, vector store, or embedding path.
- No connection to execution, planning, tools, models, memory, or API.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  runtime health, backend, frontend, or API semantic change.
- No cleanup, archive, or compaction execution.
- No generated artifacts, runtime logs, screenshots, temp files, `.next`
  output, model files, dataset files, adapter files, vector DB files,
  tool-output files, plugin packages, API keys, secrets, tokens, fake plugin
  results, fake benchmark claims, fake success, fake evidence, fake
  verification, fake telemetry, fake health, or fake metrics.

## 24. Remaining Risks

- No concrete manifest schema exists yet.
- No manifest validator exists yet.
- No plugin/skill/pack lifecycle helper exists yet.
- No no-authority tests exist for pack-specific contracts yet.
- No namespace leakage tests exist for packs yet.
- No prompt-injection tests exist for pack docs or outputs yet.
- No sandbox, signing, checksum, dependency, or package quarantine
  implementation exists yet.
- Current runtime health still reflects known historical, unknown-era, replay,
  and resource debt.

## 25. Recommended Next Workstream

Recommended next prompt:

`Plugin Manifest Type Contract v1`

Reason: this design defines the architecture and gates, but there is still no
enforceable manifest shape. The next safe implementation step is a pure,
non-runtime manifest type/validator with negative tests proving manifests,
enabled flags, installed state, model output, memory, API scopes, and tool
availability grant no permission.

Alternative:

`Vertical Pack Framework v1`

Use this only if it remains framework-design or read-only metadata work and
does not add runtime loading, dynamic imports, tool/model/memory/API wiring, or
pack execution.
