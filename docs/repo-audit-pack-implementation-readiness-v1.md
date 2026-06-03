# Repo Audit Pack Implementation Readiness v1

## 1. Decision

- Decision: `REPO_AUDIT_IMPLEMENTATION_READINESS_WITH_TESTS`
- Contract version: `repo-audit-implementation-readiness/1`
- Foundation tag: `foundation-v1-baseline`

This sprint defines the implementation-readiness boundary for a future
read-only Repo Audit runner.

It does not implement that runner. It does not scan repos, read product files,
run git, execute tests as product behavior, install dependencies, spawn
subprocesses, call tools, call MCP, call APIs, call models, access memory,
generate reports, export artifacts, sign reports, expose endpoints, add
frontend UI, wire planner/orchestrator/executor/runtime, create approval or
lease state, create capability grants, create evidence, or mark verifier
success.

## 2. Source Files

Implementation files:

- `src/aegis/core/repo_audit_implementation_readiness.py`
- `tests/test_core/test_repo_audit_implementation_readiness.py`

The helper validates caller-supplied implementation-readiness metadata only. It
does not read the referenced files, paths, test refs, dependency refs, commit
refs, or docs.

## 3. Input Contract

`validate_repo_audit_implementation_readiness(...)` accepts metadata such as:

- repo identity: `readiness_id`, `repo_id`, `repo_name`, `repo_root_ref`
- git refs: `commit_ref`, `branch_ref`
- scope: `tenant_scope`, `project_scope`, `namespace`
- source refs: `source_refs`
- audit intent: `allowed_source_scopes`, `requested_audit_scopes`
- file policy: `file_access_policy`, `allowed_path_prefixes`,
  `candidate_file_refs`, `excluded_path_patterns`
- generated/secret safety: `generated_artifact_policy`,
  `secret_privacy_policy`, `hidden_path_policy`, `symlink_policy`
- git/test metadata modes: `git_metadata_mode`, `test_metadata_mode`,
  `test_refs`
- output shape: `output_categories`, `output_candidates`,
  `report_contract`, `limitations`, `unknowns`
- privacy: `privacy_class`, `data_sensitivity`

Every decision preserves:

- `authority=false`
- `execution_permission=not_granted_by_repo_audit_implementation_readiness`
- `runtime_dispatch_allowed=false`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_readiness=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `requires_human_review=true`

## 4. Allowed Readiness Scopes

Allowed scopes:

- `source_inventory_readiness`
- `architecture_review_readiness`
- `test_reference_readiness`
- `dependency_metadata_readiness`
- `security_smell_readiness`
- `documentation_alignment_readiness`
- `policy_alignment_readiness`
- `evidence_reference_readiness`
- `developer_passport_candidate_readiness`
- `compliance_candidate_readiness`
- `generated_artifact_exclusion_readiness`
- `secret_exclusion_readiness`
- `repo_health_candidate_readiness`

Scopes are metadata intent only. They do not authorize file reads, repo scans,
git commands, test execution, dependency installation, model-assisted audit,
tool/MCP/API calls, report export, signing, or certification.

## 5. File And Source Policy

The readiness contract requires:

- caller-supplied source refs
- caller-supplied file/test/dependency refs only
- generated-artifact exclusion policy
- secret/privacy exclusion policy
- hidden/system path policy
- symlink-target policy
- exclusion patterns for logs, Git metadata, dependency folders, build outputs,
  env/key/pem files, secrets, and tokens

Denied by default:

- absolute or external paths
- path traversal
- hidden/system paths
- symlink refs
- runtime events, journals, logs, model files, vector DBs, build artifacts,
  dependency folders, and Git metadata
- env files, keys, tokens, credentials, and secret-like paths

High-risk audit scopes such as `security_smell_readiness` require
`privacy_class` and `data_sensitivity`.

## 6. Git And Test Metadata

Allowed git/test modes:

- `none`
- `caller_supplied_refs_only`
- future read-only metadata modes
- `blocked`

The contract can preserve commit refs, branch refs, and test refs, but it does
not run git or tests. Test refs are not proof tests passed. Git refs are not
proof of current repository state.

## 7. Output Contract

Allowed output categories:

- `architecture_note_candidate`
- `test_reference_candidate`
- `dependency_note_candidate`
- `security_smell_candidate`
- `documentation_alignment_candidate`
- `policy_alignment_candidate`
- `evidence_reference_candidate`
- `limitation_note`
- `unknown_note`
- `remediation_candidate`
- `developer_passport_candidate_ref`
- `compliance_candidate_ref`

Output candidates remain candidate metadata. They are not evidence, verifier
truth, certified findings, reports, exports, or security/compliance proof.
Source-less candidates must be marked uncertain or blocked by missing source.

## 8. Relationship Boundaries

Repo Audit Pack:
The existing Repo Audit Pack remains a metadata contract. This readiness helper
does not expand it into a runner.

Developer Work Passport:
Readiness output may become candidate input only. It is not a passport,
developer performance proof, proof tests passed, or proof code is safe.

Compliance Evidence Pack:
Readiness output may become compliance candidate context only. It is not legal,
security, or compliance certification, official audit result, or
court-admissible evidence.

Mission Control and Tool Simulation:
Readiness may reference preview/simulation decisions. Those decisions cannot
grant dispatch, approval, lease, capability, evidence, verifier success, or
execution permission to Repo Audit readiness.

Plugin Review Store:
Review records may reference readiness metadata. Review status cannot become
plugin execution, dynamic import, marketplace publication, or repo audit
execution permission.

Context Compiler and Memory:
Future context or memory may provide bounded refs only. Context and memory are
not truth, not authority, and not evidence. This sprint adds no memory read or
write behavior.

Policy, Approval, and Lease:
Policy refs are references only. Approval or lease metadata cannot grant
execution. Future execution still needs explicit runtime policy, approval or
lease where applicable, evidence, verifier checks, and runtime dispatch.

Evidence and Verifier:
Readiness metadata cannot create evidence, satisfy evidence gates, or mark
verifier success. Missing or uncertain source state must remain visible.

## 9. Validation Behavior

The validator rejects:

- missing request, repo identity, tenant scope, project scope, namespace,
  source refs, audit scope, or output categories
- unknown or forbidden audit scopes
- missing generated, secret/privacy, hidden-path, or symlink policy
- missing required exclusion patterns
- absolute paths, external paths, path traversal, hidden paths, symlinks,
  generated artifacts, runtime artifacts, logs, model/vector files, and secrets
- high-risk audit scopes without privacy and data sensitivity metadata
- source-less output candidates unless uncertain or blocked
- authority, runtime dispatch, approval, capability, lease, frontend authority
- repo scan, file read, git command, test execution, subprocess, tool, MCP,
  API, model, memory, report generation, export, and signing requests
- evidence, verifier, verified-success, and success claims
- proof-tests-passed, proof-code-safe, proof-secure, proof-compliant, legal,
  security, compliance, official-audit, court-admissible, surveillance, and
  productivity-score claims
- related decisions that carry dispatch, permission, evidence, verifier success,
  or failure reasons

The helper never returns `runtime_dispatch_allowed=true`.

## 10. Tests Added

Focused tests assert:

- valid minimal readiness is non-authoritative and non-dispatchable
- architecture readiness validates without scanning
- security-smell candidates preserve uncertainty
- missing identity and scope metadata are denied
- unknown and forbidden audit scopes are denied
- absolute, external, traversal, hidden, symlink, generated, runtime, model,
  vector, build, log, and secret paths are denied
- secret/generated exclusion policies are required
- high-risk scopes require privacy and data sensitivity
- proof claims and source-less candidates are blocked or uncertain
- authority, dispatch, approval, capability, lease, evidence, verifier, success,
  and frontend authority claims are rejected
- repo scan, file read, git, test, subprocess, tool, MCP, API, model, memory,
  report, and export requests are rejected
- related Repo Audit, Passport, Compliance Evidence, Mission Control, Tool
  Simulation, Plugin Review, Vertical Pack, Context Compiler, and Policy
  decisions cannot leak dispatch, evidence, verifier success, permissions, or
  failures into readiness
- validation does not mutate caller input or related decisions
- output never sets `runtime_dispatch_allowed=true`

## 11. Intentionally Not Done

- no actual repo audit runner
- no source inventory implementation
- no repo scanning
- no product file reads
- no git integration
- no test execution as product behavior
- no dependency installation
- no subprocess calls
- no model-assisted audit
- no tool, MCP, API, browser, or plugin calls
- no memory/context integration
- no report generation, export, signing, or persistence
- no frontend, endpoint, planner, orchestrator, executor, runtime, evidence, or
  verifier wiring
- no approval, lease, capability, or policy lifecycle changes
- no schema/protocol expansion

## 12. Remaining Risks

This helper validates caller-supplied metadata. Future runner work must define a
separate read-only source inventory design with explicit file-read scope,
secret exclusion enforcement, generated artifact exclusion, symlink handling,
path normalization, git/test metadata handling, runtime evidence boundaries,
human-review requirements, and validation that dispatch success is never
verification success.
