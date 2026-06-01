# Vertical Pack Framework v1

## 1. Decision

- Decision: `VERTICAL_PACK_FRAMEWORK_WITH_TESTS`
- Contract version: `vertical-pack-framework/1`
- Foundation tag: `foundation-v1-baseline`

This sprint adds a pure Vertical Pack Framework descriptor contract and
validator. It does not add vertical pack execution, plugin loading, dynamic
imports, registry behavior, runtime endpoints, persistence, frontend surfaces,
planner/executor wiring, tool/MCP/API/model wiring, memory mutation, Context
Compiler wiring, or runtime state mutation.

The framework exists to make future vertical packs reviewable while preserving
the Aegis rule that metadata is not permission.

## 2. Source Files

- `src/aegis/core/vertical_pack.py`
- `tests/test_core/test_vertical_pack.py`

The validator is pure over caller-supplied descriptor mappings and existing
manifest/integrity/lifecycle decisions. It does not inspect global runtime
state, read the event journal, mutate evidence, write memory, call tools, call
models, import plugin packages, or execute pack behavior.

## 3. Pack Categories

Canonical vertical pack categories:

- `repo_audit`
- `developer_work_passport`
- `skopos_terminology`
- `glossa`
- `compliance_evidence`
- `language_learning`
- `document_analysis`
- `coding_report`
- `security_eval`
- `business_automation`
- `freelance_workflow`
- `browser_workflow`
- `messaging_comms`
- `voice`
- `vision`
- `model_provider`
- `memory_context`
- `custom`

Unknown categories are denied. `custom` is allowed only when an explicit custom
category namespace is supplied. A vertical pack category never grants runtime
dispatch, approval, capability, lease, evidence, or verifier truth.

## 4. Operating Profiles

Supported operating profiles:

- `read_only`
- `proposal_only`
- `approval_gated_action`
- `evidence_reporting`
- `eval_only`
- `training_candidate_source`
- `external_integration_candidate`

Unknown profiles are denied. `approval_gated_action` is still
non-dispatchable. It only means the descriptor carries metadata needed for a
future policy/approval/lease/evidence review.

## 5. Descriptor Contract

Required descriptor fields:

- `pack_id`
- `pack_category`
- `operating_profile`
- `namespace`

Review fields:

- `tenant_scope`
- `project_scope`
- `required_capabilities`
- `required_tools`
- `tool_scopes`
- `required_model_roles`
- `model_provider_scopes`
- `required_memory_namespaces`
- `required_external_api_scopes`
- `required_eval_families`
- `evidence_expectations`
- `verifier_expectations`
- `policy_requirements`
- `approval_requirements`
- `lease_requirements`
- `data_sensitivity`
- `privacy_class`
- pack-specific provenance, privacy, and trust-positioning metadata

Every framework decision returns:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_vertical_pack_framework`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_pack_output=false`
- `verifier_success=false`
- `pack_output_is_evidence=false`
- `pack_output_is_verifier_truth=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_manifest_validation=true`
- `requires_integrity_check=true`
- `requires_lifecycle_check=true`

## 6. Validation Behavior

The validator denies:

- missing descriptor
- missing required fields
- unknown category
- `custom` without explicit namespace
- unknown operating profile
- missing namespace
- tenant/project-sensitive packs without tenant or project scope
- memory-using packs without memory namespace
- tool-using packs without tool scope
- model-using packs without model role and provider scope
- external-integration packs without external API scope
- known categories without eval family metadata
- evidence-reporting packs without evidence or verifier expectations
- action-gated packs without policy, approval, lease, evidence, and verifier
  requirements
- manifest validation failure
- integrity drift, review-required, or quarantine state
- lifecycle failure, revoked, quarantined, deprecated, failed, or blocked state
- authority or runtime dispatch flags
- approval, capability, or lease grants
- pack output as evidence or verifier success
- Aegis platform identity override attempts

`review_ready` means the descriptor is complete enough for future review. It is
not runtime permission.

## 7. Pack-Specific Minimums

### Repo Audit

- Allowed profiles: `read_only`, `proposal_only`.
- Requires repo/code read capability metadata.
- Requires source, commit, and path provenance.
- Denies code write tools, git mutation tools, and external API scope by
  default.

### Developer Work Passport

- Requires `evidence_reporting`.
- Requires audit/provenance expectations.
- Hidden monitoring and surveillance mode are denied.
- External sharing requires explicit approval metadata.
- Output is a transparency report, not legal certification.

### Skopos Terminology

- Allowed profiles: `proposal_only`, `evidence_reporting`.
- Requires source language, target language, domain refs, and reviewer refs.
- Cannot redefine Aegis as a translation-only product.

### Glossa

- Requires tenant, project, translation, and user scope.
- Requires namespace/memory isolation.
- Cannot redefine Aegis platform identity.

### Compliance Evidence

- Requires `evidence_reporting`.
- Requires forensic-readiness positioning.
- Requires policy/evidence/audit refs.
- Cannot claim legal certification or court admissibility by default.

### Language Learning

- Requires learner namespace isolation.
- Cross-learner leakage is denied.

### Document Analysis

- Requires document provenance.
- Requires privacy classification.
- Customer or tenant data must stay tenant/project scoped.

### Coding Report

- Requires repo, path, and test provenance.
- Code mutation tools are denied by default.

### Security Eval

- Requires `eval_only`.
- Exploit execution is denied.
- Security findings remain eval data, not execution permission.

## 8. Relationship to Manifest, Integrity, and Lifecycle

Vertical pack validation requires caller-supplied decisions from:

- `validate_plugin_manifest()`
- `evaluate_manifest_drift()`
- `evaluate_plugin_lifecycle_transition()`

Rules:

- Valid manifest metadata is required, but manifest metadata is not permission.
- Checksum match is required for review, but checksum match is not permission.
- `signature_verified` is trust metadata, not permission.
- Integrity drift, review-required, quarantine, version drift, or checksum
  mismatch blocks review.
- Active lifecycle states may be required later, but active lifecycle is not
  dispatch.
- `active_action_gated` remains non-dispatchable.
- Revoked, quarantined, deprecated, failed, or blocked lifecycle states block
  vertical pack validation.
- The vertical pack validator does not mutate supplied decisions.

## 9. Relationship to Policy, Lease, Approval, and Evidence

Rules:

- Pack category does not grant capability.
- Pack profile does not grant approval.
- Pack descriptor does not create a capability lease.
- Approval metadata alone is not execution permission.
- Lease metadata alone is not execution permission.
- Policy metadata alone is not execution permission.
- Evidence expectations are requirements, not evidence.
- Verifier expectations are requirements, not verifier success.
- Pack output cannot become evidence or verifier truth.

Any future executable pack behavior must pass backend policy, approval, lease,
evidence, verifier, audit, journal, and runtime authority gates in a later
explicit sprint.

## 10. Relationship to Model, Memory, Context, Tool, and API Surfaces

Rules:

- Model role or provider requirements are not permission.
- Memory namespace requirements are not permission.
- Context Compiler output is not permission.
- Tool availability is not permission.
- External API scope metadata is not permission.
- Frontend projection is not authority.
- Plugin/skill/pack metadata is not authority.

The framework records requirements for future review only. It does not wire to
model providers, memory, tools, MCP, SDKs, Context Compiler, or frontend.

## 11. Commercial and Product Positioning Metadata

Vertical packs may describe future product-facing domains such as repo audit,
developer work passport, terminology, translation, compliance evidence,
language learning, document analysis, coding reports, security eval, business
automation, and freelance workflows.

Product positioning metadata must remain scoped:

- no pack may redefine Aegis platform identity
- no pack may claim runtime authority
- no compliance pack may claim legal certification by default
- no developer passport may become hidden monitoring
- no training-candidate pack may imply model training execution
- no external-integration pack may imply API permission

The framework supports commercial packaging language without creating fake
pack results, fake evidence, fake verification, fake health, fake logs, or fake
metrics.

## 12. Tests Added

Focused tests assert:

- valid repo-audit read-only descriptor is non-dispatchable
- valid developer work passport evidence-reporting descriptor is
  non-dispatchable
- valid Skopos terminology proposal descriptor is non-dispatchable
- valid compliance evidence descriptor uses forensic-readiness positioning
- unknown category is denied unless `custom` has explicit namespace
- unknown operating profile is denied
- missing namespace is denied
- tenant-sensitive pack without tenant scope is denied
- memory/tool/model/external API scope requirements are enforced
- evidence-reporting and action-gated requirements are enforced
- manifest failure blocks vertical pack review
- integrity quarantine/drift blocks vertical pack review
- lifecycle revoked/quarantined/deprecated/failed blocks review
- signature verified does not grant dispatch
- active action-gated lifecycle does not grant dispatch
- authority, runtime dispatch, and grant fields are rejected
- Aegis platform identity override is rejected
- pack output cannot create evidence or verifier success
- legal certification claims are rejected for compliance evidence
- descriptor and supplied decisions are not mutated

## 13. Explicitly Not Implemented

This sprint does not implement:

- vertical pack execution
- pack registry
- plugin loading
- dynamic imports
- package installation
- frontend pack UI
- runtime endpoint
- persistence
- Context Compiler integration
- memory mutation
- MCP/tool/API/model wiring
- planner/executor integration
- generated pack artifacts
- training dataset generation
- cleanup/archive/compaction execution
