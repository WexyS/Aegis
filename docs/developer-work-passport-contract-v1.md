# Developer Work Passport Contract v1

## 1. Decision

- Decision: `DEVELOPER_WORK_PASSPORT_CONTRACT_WITH_TESTS`
- Contract version: `developer-work-passport-contract/1`
- Foundation tag: `foundation-v1-baseline`

This sprint adds a pure Developer Work Passport metadata contract and
validator. It defines how a future developer-facing transparency report can
represent caller-supplied source refs, repo audit candidate refs, changed-file
refs, test refs, policy refs, LLM assistance disclosures, tool usage
disclosures, limitations, unknowns, and client-safe delivery metadata.

It does not generate passports from repo contents. It does not scan repos,
read files, run git, run tests, call models, call tools, call APIs, write
memory, compile context, expose endpoints, export files, persist reports, or
connect to runtime/planner/executor/frontend/MCP/API/model/memory systems.

## 2. Product Positioning

Developer Work Passport is positioned as:

- transparency metadata
- provenance-backed work summary
- client-safe delivery candidate
- developer-controlled disclosure candidate
- future audit package input

It is not:

- surveillance
- hidden monitoring
- employee monitoring
- legal certification
- compliance certification
- security certification
- proof of work quality
- proof code is safe
- proof tests passed without test refs
- proof of complete LLM usage history
- runtime evidence
- verifier success

## 3. Source Files

- `src/aegis/core/developer_work_passport.py`
- `tests/test_core/test_developer_work_passport.py`

The validator is pure over caller-supplied mappings and optional caller-supplied
Repo Audit / Vertical Pack decisions. It does not mutate input mappings or
supplied decisions.

## 4. Input Contract

The request contract accepts caller-supplied metadata such as:

- `passport_id`
- `developer_ref`
- `project_ref`
- `repo_ref`
- `commit_refs`
- `branch_ref`
- `source_refs`
- `changed_file_refs`
- `test_refs`
- `review_refs`
- `repo_audit_refs`
- `policy_refs`
- `evidence_refs`
- `llm_assistance_refs`
- `tool_usage_refs`
- `limitation_notes`
- `unknowns`
- `disclosure_scope`
- `disclosure_categories`
- `audience`
- `tenant_scope`
- `project_scope`
- `namespace`
- `privacy_class`
- `data_sensitivity`
- `generated_at`

Every decision returns:

- `authority=false`
- `execution_permission=not_granted_by_developer_work_passport`
- `runtime_dispatch_allowed=false`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_passport=false`
- `verifier_success=false`
- `mutation_performed=false`
- `requires_human_review=true`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_source_refs=true`
- `not_surveillance=true`
- `not_certification=true`

## 5. Allowed Passport Scopes

Allowed scopes:

- `work_summary`
- `repo_audit_summary`
- `change_summary`
- `test_summary_refs`
- `policy_alignment_summary`
- `evidence_refs_summary`
- `llm_assistance_disclosure`
- `tool_usage_disclosure`
- `limitations_and_unknowns`
- `client_delivery_summary`
- `compliance_candidate_notes`

Scope rules:

- scope is metadata/report intent only
- scope does not authorize repo reads
- scope does not authorize git commands
- scope does not authorize test execution
- scope does not authorize external sharing
- `compliance_candidate_notes` is not compliance certification
- `client_delivery_summary` is not legal certification

## 6. Disclosure Categories

Allowed disclosure categories:

- `changed_files`
- `commits`
- `tests_referenced`
- `reviews_referenced`
- `repo_audit_candidate`
- `llm_assistance`
- `tool_usage`
- `policy_alignment`
- `evidence_refs`
- `limitations`
- `unknowns`
- `human_review_required`

Disclosure rules:

- disclosure is not proof
- disclosure without source refs must be uncertain or blocked
- LLM assistance disclosure is not proof of complete LLM usage history
- test disclosure is not proof tests passed unless backed by test refs
- evidence refs are references only, not newly created evidence

## 7. Report Contract

`DeveloperWorkPassportReportContract` fields:

- `report_id`
- `passport_id`
- `developer_ref`
- `project_ref`
- `repo_ref`
- `commit_refs`
- `disclosures`
- `limitations`
- `unknowns`
- `source_refs`
- `repo_audit_refs`
- `generated_by`
- invariant non-authority fields

Report rules:

- passport report is transparency metadata only
- passport report is not proof of work quality
- passport report is not proof code is safe
- passport report is not proof tests passed unless backed by refs
- passport report is not legal/compliance/security certification
- passport report cannot hide uncertainty
- passport report cannot be generated from hidden monitoring by default
- passport report is not evidence by itself
- passport report cannot verify itself

## 8. Validation Behavior

`validate_developer_work_passport_request(...)` denies:

- missing request
- missing passport id without developer/project identity
- missing namespace
- missing project scope
- missing disclosure scope
- missing disclosure categories
- unknown passport scope
- unknown disclosure category
- disclosure without source refs unless marked uncertain or blocked
- missing source refs
- source ref wildcards
- external sharing requests
- hidden monitoring and surveillance flags
- background tracking, screen recording, keystroke logging, and activity
  surveillance
- productivity score and worker monitoring claims
- certification claims
- proof-of-quality claims
- proof-tests-passed claims without test refs
- proof-code-safe claims
- legal, compliance, or security certification claims
- write/execute scopes
- git command requests
- test execution requests
- file mutation requests
- model review requests
- tool/MCP requests
- external API requests
- authority or runtime dispatch flags
- approval, capability, or lease grants
- evidence or verifier success claims
- dispatchable or evidence/verifier-claiming repo audit decisions
- non-`developer_work_passport` vertical pack decisions

The helper never returns `runtime_dispatch_allowed=true`.

## 9. Relationship to Repo Audit Pack

Repo Audit report output may be candidate input for Developer Work Passport.

Rules:

- Repo Audit decision remains non-authoritative.
- Repo Audit findings are not evidence by themselves.
- Repo Audit critical severity does not mutate or certify anything.
- Developer Work Passport cannot promote source-less repo audit findings to
  fact.
- Repo Audit missing-source uncertainty must be preserved.

## 10. Relationship to Compliance Evidence Pack

Developer Work Passport may become candidate input for a future Compliance
Evidence Pack.

It is not:

- compliance evidence export by itself
- legal certification
- compliance certification
- security certification
- forensic-grade export
- court-admissible proof

It can preserve source refs, evidence refs, policy refs, limitations, and
unknowns for future review. Forensic-readiness wording is allowed only as
future candidate context, not certification.

## 11. Evidence and Verifier Relationship

Developer Work Passport is not evidence by itself.

Rules:

- passport output cannot verify itself
- evidence refs are references only
- verifier success remains backend-owned
- test refs can cite existing test metadata, but cannot assert validity without
  source refs
- missing or stale refs must produce uncertainty

## 12. Model / LLM Relationship

No model call is implemented.

Rules:

- future model-assisted passport work remains proposal-only until explicitly
  gated
- model output is synthetic/unverified until validated
- LLM assistance disclosure is not proof of complete model usage history
- model-generated wording must not certify work quality
- model failure cannot be hidden

## 13. Memory / Context Relationship

No memory read or write is implemented.

Rules:

- future project memory can provide context only, not truth
- Context Compiler packages can provide bounded refs, not authority
- stale or quarantined memory cannot become passport truth
- passport cannot write long-term memory by itself

## 14. MCP / Tools / API Relationship

No tool, MCP, or API calls are implemented.

Rules:

- no file/git/test/browser/API automation
- no external sharing
- future tool use must go through MCP/Tool Gateway gates
- future external sharing must go through External API/SDK gates
- SDK/client delivery cannot hide uncertainty or convert denied states to
  success
- tool availability is not permission
- API scope is not permission

## 15. Anti-Surveillance Boundary

Developer Work Passport is developer-controlled transparency metadata.

Forbidden by default:

- hidden monitoring
- background tracking
- keystroke logging
- screen recording
- activity surveillance
- external sharing without explicit future consent/approval/API gates
- employer-facing monitoring claim
- worker compliance score
- opaque productivity score

The contract is intended to support transparent delivery metadata, not worker
surveillance.

## 16. Tests Added

Focused tests assert:

- valid minimal passport request is non-dispatchable
- valid `work_summary` scope validates
- valid `repo_audit_summary` with repo audit decision validates
- missing developer/project identity is denied
- missing namespace/project scope is denied
- unknown passport scope is denied
- unknown disclosure category is denied
- disclosure without source refs is blocked or must be uncertain
- external sharing is denied
- hidden monitoring and surveillance are denied
- productivity score and worker monitoring claims are denied
- certification claims are denied
- proof-of-quality claims are denied
- proof-tests-passed without test refs is denied
- compliance/legal/security certification claims are denied
- write/execute/git/test/file/model/tool/API requests are denied
- authority, runtime dispatch, and grant fields are rejected
- evidence/verifier success claims are rejected
- dispatchable repo audit decision is rejected
- repo audit decision claiming evidence/verifier success is rejected
- non-Developer Work Passport vertical pack decision is rejected
- report contract remains non-authoritative
- validation does not mutate input or supplied decisions

## 17. Deferred Work

Deferred to future explicit sprints:

- actual passport generation from repo contents
- repo scanning
- file reads
- git integration
- test execution
- model-assisted passport drafting
- report persistence
- report export
- frontend display
- External API/SDK delivery
- MCP/tool gateway integration
- memory/context integration
- Compliance Evidence Pack readiness
