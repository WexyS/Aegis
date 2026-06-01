# Plugin Manifest Type Contract v1

## 1. Decision

- Decision: `PLUGIN_MANIFEST_TYPE_CONTRACT_WITH_NON_AUTHORITY_TESTS`
- Foundation tag: `foundation-v1-baseline`
- Contract version: `plugin-manifest-contract/1`

This sprint adds a pure Plugin / Skill / Vertical Pack manifest type contract
and validator. It does not add plugin loading, plugin registry behavior,
dynamic imports, skill execution, vertical-pack execution, tool/MCP/API/model
wiring, Context Compiler runtime wiring, memory wiring, frontend controls,
runtime endpoints, or command dispatch.

The validator exists to make pack metadata reviewable while preserving the
Aegis rule that metadata is not permission.

## 2. Source Files

- `src/aegis/core/plugin_manifest.py`
- `tests/test_core/test_plugin_manifest.py`

The validator is standalone and pure over caller-supplied manifest mappings. It
does not inspect global runtime state, read the event journal, mutate evidence,
write memory, call tools, call models, import plugin packages, or start any
execution path.

## 3. Non-Authority Contract

Every validation decision returns:

- `authority=false`
- `execution_permission=not_granted_by_plugin_manifest`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_pack_output=false`
- `verifier_success=false`
- `runtime_dispatch_allowed=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

These fields are invariant. A manifest can become `review_ready` for future
metadata review, but it still cannot dispatch.

## 4. Manifest Shape

Required manifest fields for review:

- `manifest_version`
- `pack_id`
- `pack_name`
- `pack_type`
- `pack_version`
- `capabilities`
- `capability_categories`
- `risk_tiers`
- `disabled_by_default=true`
- `authority=false`
- `execution_permission=not_granted_by_plugin_manifest`

Recognized pack types:

- `plugin`
- `skill`
- `skill_pack`
- `vertical_pack`
- `adapter_pack`
- `integration_pack`
- `evaluation_pack`
- `read_only_pack`
- `proposal_only_pack`
- `approval_gated_action_pack`

Missing required fields produce `failed_validation`.

## 5. Capability and Risk Rules

The validator reuses the post-foundation policy-as-code capability and risk
catalog from `src/aegis/core/policy_boundary.py`.

Rules:

- unknown capability category is denied
- unknown risk tier is denied
- risk tier must match the declared capability category
- unknown tools are denied unless explicitly marked `unresolved` or `blocked`
- unknown model providers are denied unless explicitly marked `unresolved` or
  `blocked`
- unknown memory namespaces are denied unless explicitly marked `unresolved` or
  `blocked`
- unknown external API scopes are denied unless explicitly marked `unresolved`
  or `blocked`
- wildcard scopes such as `*`, `all`, or `any` are denied

Unresolved or blocked future references are metadata only. They are not
permission and cannot dispatch.

## 6. Side-Effecting Pack Rules

Side-effecting risk tiers require:

- approval requirements
- lease requirements
- evidence expectations
- verifier strategy
- audit requirements
- eval requirements

Mutation-capable risk tiers also require rollback strategy.

Even when all side-effecting metadata is present, the validation result remains
non-dispatchable. The best possible result is future review readiness, not
runtime permission.

## 7. Vertical Pack Rules

Vertical packs and vertical-pack capabilities require:

- namespace scope
- tenant scope
- namespace-specific training data policy

Vertical packs cannot define or redefine Aegis platform identity. Glossa,
translation, learner, repo-audit, document, content, business, and other
vertical packs must remain scoped domain layers, not Aegis authority.

## 8. Explicit Denials

The validator rejects attempts to use these as permission:

- `enabled=true`
- `installed=true`
- `authority=true`
- `approval_grant=true`
- `capability_grant=true`
- `lease_grant=true`
- `runtime_dispatch_allowed=true`
- `evidence_provided_by_pack_output=true`
- `verifier_success=true`
- context-derived permission
- memory-derived permission
- model-derived permission
- API/SDK-derived permission
- tool-derived permission
- frontend-derived permission
- plugin-derived permission
- skill-derived permission

Approval alone, lease alone, policy metadata alone, and manifest metadata alone
are not execution permission.

## 9. Validation Statuses

Current activation statuses:

- `metadata_only`: valid metadata for non-runtime review, no dispatch
- `review_ready`: future review metadata is complete enough to inspect, no
  dispatch
- `blocked`: manifest is present but blocked by one or more contract failures
- `failed_validation`: manifest is missing or missing required fields

No activation status enables runtime dispatch in this sprint.

## 10. Tests Added

Focused tests assert:

- valid read-only manifest remains metadata-only and non-dispatchable
- missing manifest fails validation
- required fields are enforced
- enabled and installed states grant no permission
- authority, approval, capability, lease, and dispatch grants are rejected
- execution permission must remain `not_granted_by_plugin_manifest`
- unknown capability and risk tier are denied
- capability/risk mismatches are denied
- unknown tool, model, memory namespace, and API scope are denied
- unresolved future references stay metadata-only, not permission
- wildcard scope is denied
- side-effecting packs require approval, lease, evidence, verifier, audit, eval,
  and rollback metadata
- complete side-effecting metadata still cannot dispatch
- vertical packs require namespace, tenant, and namespace-specific training
  policy
- vertical packs cannot define Aegis platform identity
- pack output cannot create evidence or verifier success
- context, memory, model, API, tool, frontend, plugin, and skill permission
  sources are denied
- validation does not mutate manifest input

## 11. Non-Goals

- No plugin registry.
- No plugin loading.
- No dynamic imports.
- No plugin code execution.
- No skill execution.
- No vertical-pack execution.
- No tool/MCP gateway implementation.
- No External API/SDK implementation.
- No model call or model router integration.
- No memory write, retrieval, vector DB, or embedding path.
- No Context Compiler runtime integration.
- No runtime endpoint.
- No command dispatch.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  runtime health, backend, frontend, or API semantic change.
- No cleanup/archive/compaction execution.

## 12. Remaining Risks

- No plugin registry exists yet.
- No manifest persistence or drift detection exists yet.
- No signature/checksum validation exists yet.
- No sandbox or dependency quarantine exists yet.
- No namespace enforcement layer exists yet.
- No prompt-injection classifier exists for pack docs or outputs yet.
- No runtime pack action lifecycle exists yet.
- Current runtime health still reflects known historical, unknown-era, replay,
  and resource debt.

## 13. Recommended Next Workstream

Recommended next prompt:

`Vertical Pack Framework v1`

Reason: the manifest type contract now gives future packs a non-authoritative
schema and validator. The next safe step is a framework-level design or
metadata-only contract for vertical packs, still without loading, dispatch,
tool calls, model calls, memory mutation, API endpoints, or runtime execution.

Alternative:

`Plugin Manifest Drift / Signature Readiness v1`

Use this if package integrity, manifest drift, checksums, signing, and
quarantine should be designed before any vertical-pack framework work.
