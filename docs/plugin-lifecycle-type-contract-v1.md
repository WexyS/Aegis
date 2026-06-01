# Plugin Lifecycle Type Contract v1

## 1. Decision

- Decision: `PLUGIN_LIFECYCLE_TYPE_CONTRACT_WITH_TESTS`
- Foundation tag: `foundation-v1-baseline`
- Lifecycle contract version: `plugin-lifecycle-contract/1`

This sprint adds a pure Plugin / Skill / Vertical Pack lifecycle type contract
and transition validator. It is the lifecycle counterpart to the existing
manifest validator and manifest integrity helpers.

No plugin registry, plugin loading, dynamic import, plugin execution, skill
execution, vertical-pack execution, endpoint, persistence, tool/MCP/API/model
wiring, memory wiring, Context Compiler wiring, planner wiring, executor
wiring, frontend behavior, or runtime mutation is added.

## 2. Scope

Implementation files:

- `src/aegis/core/plugin_lifecycle.py`
- `tests/test_core/test_plugin_lifecycle.py`

Relationship files:

- `src/aegis/core/plugin_manifest.py`
- `src/aegis/core/plugin_manifest_integrity.py`

The lifecycle helper is pure over caller-supplied state and decision objects.
It does not read files, scan plugin directories, persist lifecycle records,
inspect runtime state, import packages, or execute code.

## 3. Lifecycle States

Supported states:

- `discovered`
- `registered_metadata_only`
- `disabled`
- `policy_review_required`
- `eval_required`
- `approved_for_read_only`
- `approved_for_proposal_only`
- `approval_required_for_actions`
- `lease_required`
- `active_read_only`
- `active_proposal_only`
- `active_action_gated`
- `deprecated`
- `revoked`
- `quarantined`
- `blocked_by_policy`
- `blocked_by_privacy`
- `blocked_by_missing_evidence`
- `failed_validation`

Lifecycle state is not permission. Even an `active_*` lifecycle state is not
runtime dispatch permission.

## 4. Transition Helper

Implemented helper:

- `evaluate_plugin_lifecycle_transition(...)`

The helper returns `PluginLifecycleDecision` with:

- `transition_allowed`
- `activation_allowed`
- `failure_reasons`
- `required_gates`
- `audit_notes`
- invariant non-authority fields

Every decision returns:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_plugin_lifecycle`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_lifecycle=false`
- `verifier_success=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_manifest_validation=true`
- `requires_integrity_check=true`

`activation_allowed=true` means the lifecycle transition is internally allowed
for a future pack framework. It does not mean command, tool, plugin, skill, or
runtime dispatch is allowed.

## 5. Deny-by-Default Transitions

The helper denies:

- unknown current state
- unknown requested state
- missing manifest validation
- failed manifest validation
- missing integrity check
- integrity quarantine
- checksum mismatch
- manifest drift requiring review
- version drift requiring review
- invalid, expired, revoked, untrusted, or unsupported signature when
  activation depends on trust
- revoked to active states
- quarantined to active states
- failed validation to active states
- deprecated to new action-gated activation
- disabled directly to active states
- policy-review-required directly to active states
- eval-required activation without eval evidence
- unsupported transitions

Installed and enabled flags are recorded as metadata-only audit notes. They do
not override lifecycle denial.

## 6. Allowed Metadata and Activation Transitions

Safe non-runtime transitions include:

- `discovered -> registered_metadata_only`
- `registered_metadata_only -> policy_review_required`
- `registered_metadata_only -> eval_required`
- `registered_metadata_only -> disabled`
- `disabled -> policy_review_required`
- `policy_review_required -> approved_for_read_only`
- `eval_required -> approved_for_proposal_only`
- `approved_for_read_only -> active_read_only`
- `approved_for_proposal_only -> active_proposal_only`

These transitions still require manifest validation and integrity checks.
Approved or active lifecycle state is not runtime authority.

## 7. Action-Gated Rules

`active_action_gated` is not runtime dispatch permission.

To transition to `active_action_gated`, the helper requires:

- valid manifest validation decision
- acceptable integrity decision
- unchanged reviewed manifest
- signature verified for trusted action-gated activation
- policy check requirement
- approval present
- lease present
- evidence expectation present
- verifier strategy present
- audit requirements present
- eval present
- rollback present for mutating risk tiers
- namespace and tenant scope for vertical-pack action capabilities

Even if every gate is present:

- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_plugin_lifecycle`
- approval, lease, evidence, verifier, and lifecycle metadata remain
  non-authoritative for runtime dispatch

Actual action execution remains a future runtime boundary and is not introduced
here.

## 8. Manifest Validator Relationship

The lifecycle helper consumes caller-supplied manifest validation decisions.

Rules:

- missing validation blocks lifecycle transitions
- failed validation blocks activation
- manifest validation output cannot grant dispatch
- manifest validation output cannot create approval, capability, lease,
  evidence, or verifier success

The lifecycle helper does not modify `validate_plugin_manifest()`.

## 9. Manifest Integrity Relationship

The lifecycle helper consumes caller-supplied integrity decisions.

Rules:

- missing integrity check blocks lifecycle transitions
- checksum mismatch blocks activation
- quarantine blocks activation
- drift requiring review blocks active and approved states
- version drift blocks active and approved states
- unchanged checksum is required for active/approved lifecycle transitions
- checksum match does not grant activation by itself
- integrity output cannot grant dispatch

The lifecycle helper does not modify manifest checksum or drift helpers.

## 10. Signature and Checksum Relationship

Rules:

- checksum match is not permission
- signature verified is not dispatch permission
- unsigned may remain metadata-only
- signature-present-unverified cannot become trusted action-gated activation
- invalid, revoked, expired, untrusted, or unsupported signatures block trusted
  activation
- signature state cannot override policy, approval, lease, evidence, verifier,
  audit, or lifecycle gates

## 11. Installed and Enabled Flag Rules

Rules:

- `installed=true` is inventory metadata only
- `enabled=true` is preference/config metadata only
- installed/enabled cannot bypass manifest validation
- installed/enabled cannot bypass integrity checks
- installed/enabled cannot bypass quarantine
- installed/enabled cannot revive revoked packs
- installed/enabled cannot make deprecated packs action-gated
- installed/enabled cannot create runtime dispatch permission

## 12. Deprecation, Revocation, and Quarantine

Rules:

- `deprecated` cannot become new action-gated activation
- `revoked` cannot activate
- `quarantined` cannot activate
- `failed_validation` cannot activate
- blocked policy/privacy/evidence states cannot activate until resolved and
  re-reviewed
- quarantine and revocation reasons must be preserved by future persistence
  work

No lifecycle persistence is implemented in this sprint.

## 13. Tests Added

Focused tests assert:

- `discovered -> registered_metadata_only` is allowed but non-dispatchable
- read-only approval requires valid manifest and acceptable integrity
- `active_read_only` remains non-dispatchable
- `active_proposal_only` remains non-dispatchable
- `active_action_gated` remains non-dispatchable
- action-gated lifecycle requires approval, lease, evidence, verifier, audit,
  eval, and rollback metadata
- unknown states are denied
- failed manifest validation blocks activation
- checksum mismatch blocks activation
- drift requiring review blocks active states
- signature verified does not grant dispatch
- unverified signature blocks trusted action-gated activation
- revoked cannot become active
- quarantined cannot become active
- deprecated cannot become action-gated
- enabled and installed flags do not bypass denial
- approval alone does not grant dispatch
- lease alone does not grant dispatch
- valid manifest plus unchanged checksum plus verified signature still does not
  grant runtime dispatch
- vertical-pack action-gated activation requires namespace and tenant scope
- lifecycle helper does not mutate caller inputs

## 14. Deferred Work

- plugin lifecycle persistence
- review store
- quarantine store
- revocation/deprecation audit store
- lifecycle UI
- vertical-pack framework
- namespace enforcement
- plugin registry design
- plugin signing/trust store
- runtime pack action lifecycle

## 15. Safety Constraints Preserved

- No plugin registry.
- No plugin loading.
- No plugin directory scan.
- No lifecycle record persistence.
- No dynamic imports.
- No plugin code execution.
- No skill execution.
- No vertical-pack execution.
- No tool/MCP/API/model/memory/context/runtime wiring.
- No endpoint.
- No frontend behavior change.
- No runtime dispatch.
- No journal, evidence, replay, snapshot, memory, runtime, approval, policy,
  verifier, backend, frontend, API, or runtime-health semantic change.
- No cleanup/archive/compaction execution.
- No generated artifacts, plugin packages, tool outputs, model files, datasets,
  adapters, vector DB files, API keys, secrets, tokens, screenshots, runtime
  logs, or temp files.

## 16. Recommended Next Workstream

Recommended next prompt:

`Vertical Pack Framework v1`

Reason: manifest shape, manifest integrity, and lifecycle type contracts now
exist as pure, non-runtime boundaries. A vertical-pack framework can be
introduced as metadata-only if it remains disconnected from loading, dispatch,
tools, MCP, API, models, memory, Context Compiler authority, frontend authority,
and runtime execution.

Alternative:

`Plugin Persistence / Review Store Readiness v1`

Use this if persistence, review-store schema, quarantine records, or revocation
audit need design before vertical-pack framework work.
