# Repo Audit Pack Read-Only Contract v1

## 1. Decision

- Decision: `REPO_AUDIT_PACK_READ_ONLY_CONTRACT_WITH_TESTS`
- Contract version: `repo-audit-pack-contract/1`
- Foundation tag: `foundation-v1-baseline`

This sprint adds the first concrete vertical pack contract: a pure read-only
Repo Audit Pack validator. It is built on the Vertical Pack Framework, but it
does not execute repo audits.

No repo scanning, file reads, git commands, test execution, subprocess calls,
model calls, tool calls, MCP calls, memory reads/writes, API endpoints,
frontend surfaces, pack registry, planner/executor wiring, persistence, or
runtime mutation is added.

## 2. Scope

Implementation files:

- `src/aegis/core/repo_audit_pack.py`
- `tests/test_core/test_repo_audit_pack.py`

The helper validates caller-supplied repo audit metadata only. It never reads
the referenced repo, file paths, commits, tests, dependencies, config files, or
docs.

## 3. Input Contract

The request contract accepts caller-supplied metadata such as:

- `repo_id`
- `repo_name`
- `repo_root_ref`
- `commit_ref`
- `branch_ref`
- `source_refs`
- `file_refs`
- `test_refs`
- `dependency_refs`
- `config_refs`
- `docs_refs`
- `audit_scope`
- `requested_checks`
- `excluded_paths`
- `tenant_scope`
- `project_scope`
- `namespace`
- `privacy_class`
- `data_sensitivity`
- `generated_at`

Every decision returns:

- `authority=false`
- `execution_permission=not_granted_by_repo_audit_pack`
- `runtime_dispatch_allowed=false`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_report=false`
- `verifier_success=false`
- `mutation_performed=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_source_refs=true`
- `requires_human_review=true`

## 4. Allowed Audit Scopes

Allowed read-only audit scopes:

- `architecture_summary`
- `dependency_review`
- `test_inventory`
- `risk_findings`
- `security_static_notes`
- `documentation_review`
- `maintainability_review`
- `migration_readiness`
- `release_readiness_notes`
- `evidence_gap_notes`
- `policy_gap_notes`
- `developer_work_passport_candidate`
- `compliance_evidence_candidate`

Scope rules:

- Audit scope is metadata only.
- Audit scope does not authorize repo reads.
- Audit scope does not authorize git commands.
- Audit scope does not authorize test execution.
- Audit scope does not authorize file writes.
- `developer_work_passport_candidate` is not certification.
- `compliance_evidence_candidate` is not legal or compliance certification.

## 5. Requested Checks

Allowed requested check families:

- `project_structure`
- `dependency_metadata`
- `test_metadata`
- `config_metadata`
- `documentation_metadata`
- `risk_annotation`
- `policy_alignment_notes`
- `evidence_alignment_notes`
- `security_review_notes`
- `migration_notes`
- `release_notes`
- `unknowns_and_limitations`

Requested checks are advisory metadata. They do not run anything and do not
authorize tool, git, test, model, file, browser, MCP, or API actions.

## 6. Finding Contract

`RepoAuditFinding` fields:

- `finding_id`
- `severity`
- `category`
- `title`
- `summary`
- `source_refs`
- `confidence`
- `uncertainty`
- `suggested_next_step`
- `blocked_by_missing_source`
- `evidence_refs`
- `policy_refs`
- `labels`

Allowed severities:

- `info`
- `low`
- `medium`
- `high`
- `critical`
- `unknown`

Finding rules:

- Severity is advisory.
- Critical severity does not mutate runtime.
- Findings do not create evidence.
- Findings do not create verifier success.
- Findings without source refs must be marked uncertain or blocked by missing
  source.
- Evidence refs and policy refs are references only.

## 7. Report Contract

`RepoAuditReportContract` fields:

- `report_id`
- `repo_id`
- `commit_ref`
- `scope`
- `findings`
- `limitations`
- `source_refs`
- `unknowns`
- `generated_by`
- invariant non-authority fields

Report rules:

- The report is not Developer Work Passport final output.
- The report is not compliance certification.
- The report is not legal certification.
- The report is not security certification.
- The report is not proof tests passed.
- The report is not proof code is safe.
- The report cannot hide uncertainty.
- The report is not evidence by itself.
- The report cannot verify itself.

## 8. Validation Behavior

`validate_repo_audit_request(...)` denies:

- missing request
- missing repo identity
- missing commit ref without explicit unknown marker
- missing namespace
- missing project scope
- missing audit scope
- missing requested checks
- unknown audit scope
- unknown requested check
- write or execution scopes
- git command requests
- test execution requests
- file mutation requests
- model review requests
- external API requests
- tool/MCP requests
- repo scanning or repo file read requests
- authority or runtime dispatch flags
- approval, capability, or lease grants
- evidence or verifier success claims
- test pass or code safety claims
- Developer Work Passport certification claims
- compliance, legal, or security certification claims
- source ref wildcards
- findings without source refs unless marked uncertain or blocked
- vertical pack decisions that are dispatchable, non-`repo_audit`, non
  read/proposal profile, not `review_ready`, or contain failures

The helper never returns `runtime_dispatch_allowed=true`.

## 9. Relationship to Vertical Pack Framework

Repo Audit Pack requires a compatible Vertical Pack decision when one is
supplied:

- category: `repo_audit`
- profile: `read_only` or `proposal_only`
- status: `review_ready`
- runtime dispatch: false
- no failure reasons

The Repo Audit Pack does not mutate the vertical pack decision and does not
treat it as permission.

## 10. Relationship to Developer Work Passport

Repo Audit output may become candidate input for a future Developer Work
Passport.

It is not:

- the passport itself
- certification of work quality
- proof of LLM usage
- proof tests passed unless backed by caller-supplied test refs
- permission to export or share externally

External sharing remains future API/policy/approval-gated work.

## 11. Relationship to Compliance Evidence Pack

Repo Audit output may produce compliance evidence candidate notes.

It is not:

- compliance certification
- legal certification
- security certification
- forensic-grade audit export
- court-admissible proof

It can preserve source, evidence, and policy refs for future human review.

## 12. Evidence and Verifier Relationship

Repo audit findings are not evidence by themselves.

Rules:

- report output cannot verify itself
- `test_refs` can cite existing test result metadata, but cannot assert those
  results are valid without source refs
- `evidence_refs` are references only
- verifier success remains backend-owned
- missing source must remain visible as uncertainty or blocked status

## 13. Model / LLM Relationship

No model call is implemented.

Future model-assisted audit must remain proposal-only until a later explicit
boundary sprint. Model output must be labeled synthetic/unverified until
validated. Model suggestions cannot create findings without source refs.
Model failure cannot be hidden.

## 14. Memory / Context Relationship

No memory read or write is implemented.

Future project memory may provide context only, not truth. Context packages may
provide bounded refs, not authority. Stale or quarantined memory cannot drive
findings as truth.

## 15. MCP / Tools / API Relationship

No tool calls are implemented.

Rules:

- no file/git/test/browser/API automation
- no external sharing
- future tool use must go through MCP/Tool Gateway gates
- future API exposure must go through External API/SDK gates
- tool availability is not permission
- API scope is not permission

## 16. Tests Added

Focused tests assert:

- valid minimal repo audit request is non-dispatchable
- architecture summary scope validates
- requested check families validate
- missing repo identity is denied
- missing commit ref requires explicit unknown marker
- missing namespace/project scope is denied
- unknown scope and check families are denied
- write scope, git command, test execution, file mutation, model review,
  external API, and tool requests are denied
- authority, runtime dispatch, and grant fields are rejected
- evidence/verifier success claims are rejected
- Developer Work Passport final certification is rejected
- compliance/legal/security certification claims are rejected
- findings without source refs are blocked or must be uncertain
- report contract remains non-authoritative
- dispatchable or wrong-category vertical pack decisions are rejected
- validation does not mutate caller input

## 17. Deferred Work

Deferred to future explicit sprints:

- actual repo audit execution
- repo scanning
- file reading
- git integration
- test execution
- model-assisted proposal generation
- report persistence
- frontend display
- pack registry
- MCP/tool gateway integration
- External API/SDK exposure
- Developer Work Passport contract
- Compliance Evidence Pack readiness
