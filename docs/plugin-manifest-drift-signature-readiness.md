# Plugin Manifest Drift / Signature Readiness
## 1. Decision

- Decision: `PLUGIN_MANIFEST_DRIFT_SIGNATURE_WITH_TESTS`
- Foundation tag: `foundation-baseline`
- Integrity contract version: `plugin-manifest-integrity/1`

This sprint adds a pure manifest integrity/readiness helper for future plugin,
skill, and vertical-pack manifests. It does not add a plugin registry, plugin
loader, dynamic import path, skill runner, vertical-pack runner, runtime
endpoint, tool/MCP/API/model/memory wiring, frontend behavior, planner
integration, executor integration, or runtime mutation.

The implementation exists to make manifest drift, checksum mismatch, signature
readiness, and scope expansion visible before any future pack framework work.
It grants no permission.

## 2. Scope

Implementation files:

- `src/aegis/core/plugin_manifest_integrity.py`
- `tests/test_core/test_plugin_manifest_integrity.py`

Relationship file:

- `src/aegis/core/plugin_manifest.py`

The integrity helper is pure over caller-supplied manifest mappings. It does
not read files, scan directories, load manifests from disk, persist checksums,
import plugins, execute plugin code, or inspect runtime state.

## 3. Manifest Identity Model

Future identity fields should include:

- `manifest_id`
- `pack_id`
- `pack_version`
- `manifest_version`
- `source`
- `owner`
- `trust_level`
- `provenance_refs`
- `checksum_algorithm`
- `manifest_checksum`
- `signature_status`
- `signed_by`
- `reviewed_manifest_checksum`
- `reviewed_at`
- `review_status`

Rules:

- `pack_id` alone is not identity.
- `pack_version` alone is not identity.
- reviewed status must be bound to the reviewed manifest checksum.
- manifest content change invalidates prior review unless explicitly reviewed
  again.
- signature metadata is trust metadata, not execution permission.
- checksum match is not permission.

## 4. Checksum and Normalization Model

Implemented helpers:

- `normalize_manifest_for_checksum(manifest)`
- `calculate_manifest_checksum(manifest, algorithm="sha256")`

Normalization rules:

- deterministic JSON output
- stable key ordering
- no mutation of caller input
- `sha256` only in this readiness layer
- non-JSON-serializable values are rejected
- review/signature/checksum bookkeeping fields are excluded from content
  checksum to avoid self-referential hashes

Excluded checksum bookkeeping fields:

- `checksum_algorithm`
- `manifest_checksum`
- `review_status`
- `reviewed_at`
- `reviewed_manifest_checksum`
- `signature`
- `signature_status`
- `signed_by`

The helper does not include runtime or environment-specific fields unless a
caller explicitly provides them as manifest content.

## 5. Drift Decision Model

Implemented helper:

- `evaluate_manifest_drift(...)`

Decision states:

- `no_review_record`
- `unchanged`
- `changed_requires_review`
- `version_changed_requires_review`
- `checksum_mismatch_requires_quarantine`
- `invalid_manifest_requires_quarantine`
- `unsupported_algorithm`
- `blocked`

Every drift decision returns:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_manifest_integrity`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_pack_output=false`
- `verifier_success=false`

Changing a reviewed manifest cannot silently inherit previous review status.

## 6. Signature Readiness Model

Implemented signature status classification:

- `unsigned`
- `signature_missing`
- `signature_present_unverified`
- `signature_verified`
- `signature_invalid`
- `signer_untrusted`
- `signature_expired`
- `signature_revoked`
- `algorithm_unsupported`

Rules:

- unsigned is not trusted.
- signature present is not verified.
- signature verified is not permission.
- trusted signer is not execution permission.
- invalid, untrusted, expired, revoked, or unsupported signatures block and
  require quarantine.
- signature status cannot override policy, approval, lease, evidence, verifier,
  or runtime checks.

No cryptographic signing or signature verification implementation is added in
this sprint.

## 7. Quarantine Model

Quarantine reasons include:

- `checksum_mismatch`
- `manifest_drift`
- `version_drift`
- `signature_invalid`
- `signer_untrusted`
- `signature_expired`
- `signature_revoked`
- `algorithm_unsupported`
- `invalid_manifest`
- `scope_expansion`
- `capability_expansion`
- `risk_tier_expansion`
- `new_tool_reference`
- `new_model_reference`
- `new_memory_namespace`
- `new_external_api_scope`
- `tenant_scope_expansion`
- `disabled_by_default_changed_to_false`
- `authority_changed_to_true`
- `execution_permission_changed`
- `platform_identity_override_attempt`

A quarantined manifest:

- cannot activate
- cannot dispatch
- cannot inherit previous review
- cannot grant permission
- must preserve the reason
- requires operator or policy review
- must not be silently repaired

## 8. Scope and Capability Expansion Detection

Implemented helper:

- `compare_manifest_scope_expansion(reviewed_manifest, current_manifest)`

It detects:

- added capability categories
- added risk tiers
- added tool references
- added model provider references
- added memory namespaces
- added external API scopes
- tenant scope expansion
- project/scope expansion
- `disabled_by_default` changing to `false`
- `authority` changing to `true`
- `execution_permission` changing away from
  `not_granted_by_plugin_manifest`
- vertical-pack platform identity override attempts

Any expansion requires review and blocks activation. Scope expansion cannot use
the old reviewed checksum as a silent permission bridge.

## 9. Relationship to `validate_plugin_manifest()`

The integrity helper is separate from `validate_plugin_manifest()`.

Current relationship:

- `validate_plugin_manifest()` validates manifest shape and non-authority
  fields.
- `evaluate_manifest_drift()` evaluates checksum, reviewed-state drift,
  signature readiness, and expansion/quarantine state.
- neither helper reads files
- neither helper persists records
- neither helper grants dispatch
- neither helper loads plugin code

Future use should run validation and integrity checks before any pack is shown
as reviewable. Runtime execution still requires later policy, lease, approval,
evidence, verifier, journal, audit, and explicit implementation gates.

## 10. Tests Added

Focused tests assert:

- checksum is deterministic for equivalent manifest key order
- checksum helper does not mutate input
- checksum excludes review/signature bookkeeping fields
- non-JSON-serializable values are rejected
- no review record requires review but not quarantine by itself
- unchanged reviewed manifest remains non-dispatchable
- changed reviewed manifest requires quarantine review
- version change requires review
- checksum mismatch requires quarantine
- unsupported checksum algorithm is blocked
- unsigned manifest is not trusted
- unverified signature is not trusted
- verified signature still grants no permission
- invalid, expired, revoked, or untrusted signatures block activation
- added capability and risk tier require review
- added tool/model/memory/API scope require review
- tenant/project scope expansion requires review
- changed `disabled_by_default`, `authority`, or `execution_permission` is
  quarantined
- vertical pack identity override requires quarantine
- quarantined manifest cannot dispatch or grant authority
- invalid manifest requires quarantine
- `validate_plugin_manifest()` still handles the same manifest independently

## 11. Deferred Work

- manifest persistence
- reviewed manifest store
- signed manifest verification
- signer trust store
- checksum migration strategy
- manifest drift UI
- manifest quarantine UI
- namespace enforcement
- dependency quarantine
- package signing/checksum validation
- prompt-injection classifier for pack docs/output
- plugin lifecycle type contract
- vertical-pack framework

## 12. Safety Constraints Preserved

- No plugin registry.
- No plugin loading.
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

## 13. Recommended Next Workstream

Recommended next prompt:

`Vertical Pack Framework`

Reason: manifest shape and manifest integrity readiness now exist as pure,
non-runtime contracts. A vertical-pack framework can be designed or introduced
as metadata-only if it stays disconnected from loading, dispatch, tools, MCP,
API, models, memory, context, frontend authority, and runtime execution.

Alternative:

`Plugin Lifecycle Type Contract`

Use this if lifecycle state validation, quarantine transitions, revocation, and
review-state persistence need a separate pure helper before vertical-pack
framework work.
