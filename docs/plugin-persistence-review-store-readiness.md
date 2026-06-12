# Plugin Persistence / Review Store Readiness
Decision: `PLUGIN_REVIEW_STORE_READINESS_WITH_TESTS`

## Scope

This sprint defines a pure Plugin Review Store readiness contract for Aegis. It
validates caller-supplied review records for plugins, skills, vertical packs, and
pack descriptors without creating real persistence or granting execution
permission.

The implementation adds:

- `src/aegis/core/plugin_review_store.py`
- `tests/test_core/test_plugin_review_store.py`

No plugin execution, dynamic import, plugin package generation, marketplace
publishing, endpoint, frontend wiring, real database, file store, runtime state,
journal mutation, evidence mutation, replay mutation, approval, lease,
capability grant, external API call, MCP call, model call, memory access, or
tool execution is added.

## Why Review Store Readiness Exists

Aegis has pure contracts for plugin manifests, manifest integrity, lifecycle
transitions, vertical packs, repo audit metadata, developer work passports,
compliance evidence readiness, Mission Control previews, and policy/tool
simulation. The missing layer is a common place to represent review decisions
without making review status look like permission.

The review-store readiness contract prevents fragmented review metadata:

- manifest refs can be tied to checksum and signature refs;
- lifecycle decisions can be related to review records;
- vertical pack decisions can be referenced without becoming authority;
- reviewer notes, limitations, unknowns, followups, and provenance are kept;
- high-risk capabilities require explicit security, privacy, and policy review
  flags;
- future catalog or marketplace work cannot treat reviewed metadata as
  publication or execution permission.

## Review Record Contract

`PluginReviewRecordInput` accepts metadata such as:

- `review_record_id`, `plugin_id`, `plugin_name`, `plugin_version`;
- `manifest_ref`, `manifest_checksum_ref`, `signature_ref`;
- `lifecycle_decision_ref`, `vertical_pack_decision_ref`;
- `policy_refs`, `evidence_refs`;
- `reviewer_ref`, `review_timestamp`;
- `review_status`, `review_scope`, `review_version`;
- `source_refs`, `limitations`, `unknowns`, `required_followups`;
- `required_operator_review`, `required_security_review`,
  `required_privacy_review`, `required_policy_review`;
- `allowed_operations`, `forbidden_operations`;
- `declared_capabilities`, `declared_risk_tiers`, `requested_permissions`;
- `data_sensitivity`, `tenant_scope`, `project_scope`, `namespace`;
- `provenance_refs`, `expiry_or_revalidation_at`,
  `supersedes_review_record_id`;
- non-authority fields that must remain false.

`PluginReviewRecord` always preserves these invariant fields:

- `authority=false`;
- `runtime_dispatch_allowed=false`;
- `execution_permission=not_granted_by_plugin_review_store`;
- `approval_grant=false`;
- `capability_grant=false`;
- `lease_grant=false`;
- `evidence_provided_by_review=false`;
- `verifier_success=false`;
- `mutation_performed=false`;
- `frontend_authority=false`;
- `plugin_execution_allowed=false`;
- `dynamic_import_allowed=false`;
- `marketplace_publication_allowed=false`;
- `requires_backend_validation=true`;
- `requires_policy_check=true`;
- `requires_operator_approval_for_execution=true`.

The included `PluginReviewStoreContract` records that this sprint adds no real
persistence, database, file store, runtime integration, plugin loading, or
marketplace publication behavior.

## Review Statuses

Allowed review statuses:

- `draft`;
- `submitted_for_review`;
- `review_ready`;
- `approved_for_catalog_review`;
- `approved_metadata_only`;
- `rejected`;
- `blocked`;
- `quarantined`;
- `deprecated`;
- `superseded`;
- `expired`;
- `requires_security_review`;
- `requires_privacy_review`;
- `requires_policy_review`;
- `unknown`.

Rules:

- `review_ready` is not execution permission.
- `approved_metadata_only` is not execution permission.
- `approved_for_catalog_review` is not marketplace publication.
- `rejected`, `blocked`, and `quarantined` remain blocked.
- `expired`, `superseded`, and `deprecated` require revalidation metadata.
- `unknown` requires operator/security attention.

## Review Scopes

Allowed review scopes:

- `manifest_metadata_only`;
- `integrity_metadata_only`;
- `lifecycle_metadata_only`;
- `vertical_pack_metadata_only`;
- `catalog_review_candidate`;
- `security_review_candidate`;
- `privacy_review_candidate`;
- `policy_review_candidate`;
- `read_only_pack_candidate`;
- `external_integration_candidate`;
- `execution_candidate_future_only`.

Rules:

- scope is metadata and review intent only;
- `execution_candidate_future_only` is not execution permission;
- `external_integration_candidate` is not API permission;
- `catalog_review_candidate` is not marketplace publication.

## Validation Behavior

The validator:

- requires `review_record_id` or `plugin_id` plus `plugin_version`;
- requires `manifest_ref` or `source_refs` for non-draft records;
- requires allowed review status and scope;
- requires tenant, namespace, and project scope for non-draft records;
- requires limitations and unknowns to be preserved;
- requires revalidation metadata for expired, superseded, and deprecated
  records;
- requires security, privacy, and policy review flags for high-risk capability,
  risk, or permission records;
- rejects wildcard requested permissions and wildcard allowed operations;
- rejects hidden permissions;
- rejects execution permission claims;
- rejects plugin execution, dynamic import, marketplace publication, runtime
  dispatch, approval, capability, lease, evidence, verifier, mutation, and
  frontend authority claims;
- rejects external API, MCP, model, memory, and tool-execution requests;
- rejects certification, official audit, proof, and court-admissible claims;
- validates related manifest, integrity, lifecycle, vertical-pack, and policy
  decision objects for permission/evidence/verifier leakage;
- never returns `runtime_dispatch_allowed=true`.

## Manifest Relationship

Manifest metadata can be referenced through `manifest_ref` and related manifest
validation decisions. Manifest validity is not execution permission. Manifest
presence is not plugin installation or execution. If a manifest-related decision
claims runtime dispatch or permission, review-store validation rejects it.

## Integrity And Signature Relationship

Checksum and signature refs are metadata only. Signature presence or verified
metadata does not create trust by itself and does not grant permission. Manifest
drift, review-required states, quarantine-required states, or non-unchanged
integrity decisions require revalidation.

This sprint does not perform real cryptographic signature verification.

## Lifecycle Relationship

Lifecycle decisions can be referenced. Lifecycle state is not runtime dispatch
permission. Approved lifecycle metadata does not authorize execution.
Quarantined, deprecated, revoked, or failed lifecycle states block review
readiness or require revalidation. Lifecycle decisions claiming dispatch or
permission are rejected.

## Vertical Pack Relationship

Vertical pack validation decisions can be referenced. `review_ready` is metadata
only. Pack category and operating profile do not grant execution.
`approval_gated_action` still requires future policy, approval, lease, evidence,
verifier, and runtime dispatch gates.

Vertical pack decisions claiming dispatch, evidence, or verifier success are
rejected.

## Policy / Approval / Lease Relationship

Review records may reference policy decisions, but they cannot create policy
decisions. They cannot create approval, activate a lease, grant capability, or
authorize execution. Future execution still requires policy, approval or lease
where needed, evidence, verifier checks, and runtime dispatch gates.

## Evidence / Verifier Relationship

Review records are not evidence. `evidence_refs` are references only. Review
metadata cannot create verifier success. Plugin output or tool output cannot
verify itself.

## Frontend Relationship

A future frontend may display plugin review status, but frontend state cannot
create review authority, turn `review_ready` into execution, publish a plugin,
or grant approval, lease, capability, evidence, verifier success, or runtime
dispatch.

Frontend authority claims are rejected.

## Marketplace / Commercial Relationship

The review-store contract can support future catalog or marketplace readiness
metadata. `catalog_review_candidate` and `approved_for_catalog_review` are not
public listing, publication, distribution, signing, or packaging approval.

`marketplace_publication_allowed` remains false in this sprint.

## External API / MCP / Model / Memory Boundary

The review-store helper makes no external calls. It does not call APIs, start
MCP servers, call tools, call models, read memory, write memory, load plugin
code, or import plugin modules.

## Tests Added

Focused tests cover:

- valid metadata-only review record non-authority;
- `review_ready` and `approved_metadata_only` not granting execution;
- catalog review not allowing marketplace publication;
- `execution_candidate_future_only` not allowing execution;
- rejected, blocked, and quarantined status blocking;
- expired, superseded, and deprecated revalidation metadata;
- unknown status operator attention;
- missing identity, refs, and scope validation;
- high-risk security/privacy/policy review flags;
- wildcard and hidden permission denial;
- plugin execution, dynamic import, marketplace publication, runtime dispatch,
  approval, capability, lease, evidence, verifier, and frontend authority
  rejection;
- related manifest, integrity, lifecycle, vertical-pack, and policy decision
  leakage rejection;
- certification and official-audit wording rejection;
- input and supplied decision immutability;
- review output never setting `runtime_dispatch_allowed=true`.

## Intentionally Not Done

- no real persistence, database, or file store;
- no runtime integration;
- no frontend UI;
- no endpoints;
- no plugin loading, dynamic import, or execution;
- no plugin package creation;
- no marketplace publication or distribution;
- no real cryptographic signature verification;
- no approval, lease, or capability lifecycle changes;
- no evidence or verifier semantics changes;
- no planner, executor, runtime, tool, API, MCP, model, or memory integration;
- no generated artifacts, logs, screenshots, images, plugin packages, API keys,
  secrets, or tokens.

## Future Real Persistence Notes

Future persistence work must keep the review-store record append-only or
versioned, preserve reviewer and source provenance, preserve limitations and
unknowns, revalidate on manifest drift, and keep execution permission behind
separate policy, approval/lease, evidence, verifier, and runtime dispatch gates.

Any real database or file-store implementation must define:

- record identity and versioning;
- supersession and expiry behavior;
- immutable review provenance;
- revalidation workflow for drifted manifests;
- secret and token exclusion;
- audit-safe export boundaries;
- frontend display boundaries;
- no direct path from review status to execution.

## Remaining Risks

The current helper validates caller-supplied metadata and related pure decision
objects. Future work must define how review records are assembled, stored,
expired, superseded, and displayed without allowing plugin manifests, lifecycle
states, signature metadata, frontend state, or marketplace metadata to become
execution authority.
