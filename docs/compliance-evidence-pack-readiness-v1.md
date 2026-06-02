# Compliance Evidence Pack Readiness v1

## 1. Decision

- Decision: `COMPLIANCE_EVIDENCE_PACK_READINESS_WITH_TESTS`
- Contract version: `compliance-evidence-pack-readiness/1`
- Foundation tag: `foundation-v1-baseline`

This sprint adds a pure Compliance Evidence Pack readiness contract and tests.
It defines how future compliance-facing packages may preserve caller-supplied
source refs, policy refs, evidence refs, Repo Audit candidate refs, Developer
Work Passport candidate refs, control mappings, limitations, unknowns,
audit-readiness metadata, forensic-readiness metadata, and human-review
requirements.

It does not generate compliance reports, create forensic exports, sign outputs,
scan repos, read files, run git, run tests as product behavior, call models,
call tools, call APIs, write memory, expose endpoints, persist packages, or
connect to runtime/planner/executor/frontend/MCP/API/model/memory systems.

## 2. Product Positioning

Allowed positioning:

- audit-readiness metadata
- forensic-readiness metadata
- due-diligence support
- evidence-reference package candidate
- policy alignment notes
- control-mapping candidates
- compliance gap candidates
- human-review queue candidates
- limitations and unknowns reports

Forbidden positioning:

- legal certification
- compliance certification
- security certification
- court-admissible evidence claim
- official audit result
- proof of regulatory compliance
- proof that controls are effective
- proof that an organization is safe
- liability shield
- regulator-approved claim
- runtime evidence by itself
- verifier success by itself

## 3. Input Contract

Implementation files:

- `src/aegis/core/compliance_evidence_pack.py`
- `tests/test_core/test_compliance_evidence_pack.py`

The request contract accepts caller-supplied metadata such as:

- `package_id`
- `project_ref`
- `tenant_scope`
- `project_scope`
- `namespace`
- `audit_context_ref`
- `source_refs`
- `policy_refs`
- `evidence_refs`
- `repo_audit_refs`
- `developer_work_passport_refs`
- `control_refs`
- `framework_refs`
- `limitation_notes`
- `unknowns`
- `review_status`
- `evidence_scope`
- `data_sensitivity`
- `privacy_class`
- `generated_at`

Every decision returns:

- `authority=false`
- `execution_permission=not_granted_by_compliance_evidence_pack`
- `runtime_dispatch_allowed=false`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_package=false`
- `verifier_success=false`
- `mutation_performed=false`
- `requires_human_review=true`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_source_refs=true`
- `not_certification=true`
- `not_legal_advice=true`
- `not_court_admissible_claim=true`

## 4. Allowed Evidence Scopes

Allowed metadata/report-intent scopes:

- `policy_alignment_notes`
- `evidence_refs_summary`
- `repo_audit_candidate_notes`
- `developer_work_passport_candidate_notes`
- `control_mapping_candidate`
- `audit_readiness_notes`
- `forensic_readiness_notes`
- `limitations_and_unknowns`
- `risk_register_candidate`
- `remediation_plan_candidate`
- `compliance_gap_candidate`
- `human_review_queue_candidate`

Scope rules:

- scope is metadata/report intent only
- scope does not certify compliance
- scope does not create evidence
- scope does not verify controls
- scope does not authorize external sharing
- `forensic_readiness_notes` is allowed
- court-admissible evidence, legal certification, compliance certification,
  and security certification scopes are denied

## 5. Control and Framework References

Control refs preserve:

- `control_id`
- `framework_name`
- `framework_version`
- `mapping_status`
- `source_refs`
- `evidence_refs`
- `confidence`
- `uncertainty`
- `human_review_required`

Allowed mapping statuses:

- `candidate`
- `mapped_with_refs`
- `missing_refs`
- `uncertain`
- `not_applicable`
- `blocked`

Rules:

- control mapping is not proof of control effectiveness
- `mapped_with_refs` is not certification
- missing refs must preserve uncertainty
- unknown frameworks must remain uncertain or blocked
- human review is required for compliance-facing claims

## 6. Evidence Candidate Contract

Candidate categories:

- `policy_reference`
- `evidence_reference`
- `repo_audit_reference`
- `developer_work_passport_reference`
- `control_mapping`
- `risk_note`
- `remediation_note`
- `limitation_note`
- `unknown_note`

Candidate rules:

- candidate is not evidence by itself
- candidate is not verifier success
- candidate without source, evidence, policy, repo-audit, or passport refs must
  be uncertain or blocked
- Repo Audit and Developer Work Passport refs are candidate inputs only
- candidate severity or risk labels do not mutate runtime

## 7. Package Contract

`ComplianceEvidencePackageContract` records:

- `package_id`
- `project_ref`
- `tenant_scope`
- `namespace`
- `evidence_scope`
- `candidates`
- `control_refs`
- `limitations`
- `unknowns`
- `source_refs`
- `policy_refs`
- `evidence_refs`
- `generated_by`
- invariant non-authority fields

Package rules:

- package is audit-readiness metadata only
- package is not legal/compliance/security certification
- package is not a court-admissible evidence claim
- package is not proof of regulatory compliance
- package cannot hide uncertainty
- package cannot create evidence
- package cannot verify itself
- package cannot be exported or shared externally without future API, policy,
  approval, lease, privacy, and audit gates

## 8. Validation Behavior

`validate_compliance_evidence_request(...)` denies:

- missing request
- missing package/project identity
- missing tenant/project/namespace scope
- missing evidence scope
- missing source refs
- unknown evidence scope
- write, execute, git, test, file, model, tool, repo-scan, and API requests
- external sharing, export, and report signing requests
- legal certification claims
- compliance certification claims
- security certification claims
- court-admissible evidence claims
- official audit result claims
- proof-of-compliance claims
- proof-control-effective claims
- proof-organization-safe claims
- liability shield and regulator-approved claims
- authority, runtime dispatch, approval, capability, and lease grant fields
- evidence, verifier, verified-success, and success claims
- source-ref wildcards
- candidates without refs unless marked uncertain or blocked
- mapped controls without refs
- candidate or missing-ref controls without uncertainty
- unknown frameworks unless uncertain or blocked
- dispatchable or evidence/verifier-claiming Repo Audit decisions
- dispatchable or evidence/verifier-claiming Developer Work Passport decisions
- non-`compliance_evidence` or non-`evidence_reporting` Vertical Pack decisions

The helper never returns `runtime_dispatch_allowed=true`.

## 9. Relationship to Repo Audit Pack

Repo Audit output may be candidate input only.

Rules:

- Repo Audit decision remains non-authoritative.
- Repo Audit findings are not evidence by themselves.
- Repo Audit critical severity does not certify compliance.
- Source-less repo audit uncertainty must be preserved.
- Repo Audit cannot promote a compliance candidate to certified evidence.

## 10. Relationship to Developer Work Passport

Developer Work Passport output may be candidate input only.

Rules:

- Passport remains transparency metadata.
- Passport is not certification.
- Passport cannot prove work quality, safety, or compliance.
- Passport uncertainty and anti-surveillance constraints must be preserved.
- Passport cannot create certified compliance evidence.

## 11. Evidence and Verifier Relationship

Compliance Evidence Pack is not evidence by itself.

Rules:

- `evidence_refs` are references only
- verifier success remains backend-owned
- package output cannot verify itself
- current, historical, unknown-era, replay, and resource debt must remain
  visible
- unknown-era issues cannot be recategorized as historical or compliant
- missing evidence cannot become verified

## 12. Policy, Lease, and Approval Relationship

Policy refs are references only.

Rules:

- policy alignment notes are not policy decisions
- approval may be required for future export/share, but approval is not
  certification
- a lease may scope future package export/access, but a lease is not
  certification
- Compliance Evidence Pack cannot create approval or lease
- Compliance Evidence Pack cannot satisfy policy, approval, lease, evidence,
  or verifier gates

## 13. Model / LLM Relationship

No model call is implemented.

Rules:

- future model-assisted compliance wording remains proposal-only
- model output is synthetic/unverified until validated
- model-generated compliance summaries cannot certify
- model failure cannot be hidden

## 14. Memory and Context Relationship

No memory read or write is implemented.

Rules:

- future project memory can provide context only, not truth
- Context Compiler packages can provide bounded refs, not authority
- stale or quarantined memory cannot become compliance truth
- compliance package cannot write long-term memory by itself

## 15. MCP, Tools, and API Relationship

No MCP, tool, file, git, test, browser, API, or external sharing behavior is
implemented.

Rules:

- future tool use must go through MCP/Tool Gateway gates
- future external sharing/export must go through External API/SDK gates
- SDK/client delivery cannot hide uncertainty or convert denied states to
  success
- tool availability is not permission
- API scope is not permission

## 16. Commercial/Product Wording Boundary

Allowed terms:

- audit-readiness
- forensic-readiness
- due-diligence support
- evidence-reference package
- compliance candidate notes
- human-review queue

Forbidden terms:

- legal certification
- compliance certification
- security certification
- court-admissible evidence
- official audit result
- guaranteed compliance
- organization is safe
- controls are effective
- liability shield
- regulator-approved

## 17. Tests Added

Focused tests assert:

- valid minimal compliance evidence request is non-dispatchable
- valid `forensic_readiness_notes` scope validates without certification
- valid control mapping candidate preserves uncertainty
- missing package/project identity is denied
- missing tenant/project/namespace scope is denied
- unknown evidence scope is denied
- source-less candidate claims are blocked or uncertain
- legal, compliance, security, and court-admissible claims are denied
- proof and official audit claims are denied
- external sharing/export/signing requests are denied
- write/execute/git/test/file/model/tool/API requests are denied
- authority, runtime dispatch, and grant fields are rejected
- evidence/verifier/success claims are rejected
- Repo Audit decisions with dispatch/evidence/verifier success are rejected
- Developer Work Passport decisions with dispatch/evidence/verifier success
  are rejected
- non-compliance Vertical Pack decisions are rejected
- package contract remains non-authoritative
- validation does not mutate input or supplied decisions

## 18. Deferred Work

Deferred to future explicit sprints:

- actual compliance report generation
- forensic exports
- signing
- repo scanning
- file reads
- git integration
- test execution as product behavior
- model-assisted compliance drafting
- MCP/tool/API integration
- External API/SDK delivery
- memory/context integration
- frontend display
- package persistence/export
- legal/compliance/security certification
- court-admissibility claims
