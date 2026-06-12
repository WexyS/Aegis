# Repo Audit Pack Read-Only Source Inventory Design
## 1. Decision

- Decision: `REPO_AUDIT_SOURCE_INVENTORY_DESIGN_WITH_TESTS`
- Contract version: `repo-audit-source-inventory-design/1`
- Foundation tag: `foundation-baseline`

This sprint defines a pure source inventory design contract for a future
read-only Repo Audit Pack.

It does not implement actual source inventory. It does not scan repos, read
files, stat files, traverse the filesystem, run git, run tests, spawn
subprocesses, call models, call tools, call APIs, call MCP, access memory,
generate reports, export artifacts, create evidence, mark verifier success, or
wire runtime/API/frontend/planner/executor behavior.

## 2. Source Files

Implementation files:

- `src/aegis/core/repo_audit_source_inventory.py`
- `tests/test_core/test_repo_audit_source_inventory.py`

The helper validates caller-supplied path metadata only. Candidate paths are
synthetic metadata. They are not proof that files exist, were read, were
counted, were statted, or are safe to inventory.

## 3. Input Contract

`validate_repo_audit_source_inventory_design(...)` accepts metadata such as:

- inventory identity: `inventory_id`, `repo_id`, `repo_name`, `repo_root_ref`
- refs: `commit_ref`, `branch_ref`, `source_refs`
- scope: `tenant_scope`, `project_scope`, `namespace`
- design intent: `source_inventory_scope`
- path metadata: `candidate_paths`
- path policy: `allowed_prefixes`, `allow_repo_root_files`,
  `forbidden_paths`, `forbidden_extensions`
- exclusion policy: generated artifacts, secrets, hidden paths, symlinks,
  external paths, traversal, logs, model/vector files, browser output,
  dependency/build/cache paths
- budget: `max_file_count`, `max_file_size_bytes`, `max_total_bytes`,
  `budget_policy`
- optional future read plan metadata
- privacy: `privacy_class`, `data_sensitivity`
- limitations and unknowns

Every decision preserves:

- `authority=false`
- `execution_permission=not_granted_by_repo_audit_source_inventory_design`
- `runtime_dispatch_allowed=false`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `actual_source_inventory_performed=false`
- `repo_scan_performed=false`
- `file_read_performed=false`
- `filesystem_traversal_performed=false`
- `file_stat_performed=false`
- `git_command_performed=false`
- `test_execution_performed=false`
- `subprocess_performed=false`
- `model_call_performed=false`
- `tool_call_performed=false`
- `api_call_performed=false`
- `mcp_call_performed=false`
- `memory_access_performed=false`
- `report_generated=false`
- `export_performed=false`
- `evidence_provided_by_inventory=false`
- `verifier_success=false`

## 4. Allowed Scopes

Allowed source inventory design scopes:

- `source_inventory_design`
- `path_policy_validation`
- `exclusion_policy_validation`
- `source_budget_validation`
- `metadata_only_inventory_candidate`
- `generated_artifact_exclusion_design`
- `secret_exclusion_design`
- `symlink_policy_design`
- `hidden_file_policy_design`
- `future_read_plan_candidate`

Scopes are metadata intent only. They do not authorize repo scans, file reads,
stat calls, git commands, test execution, subprocesses, model calls, tool calls,
MCP calls, API calls, memory access, evidence, verifier success, report export,
or signing.

Forbidden scopes include:

- `actual_source_inventory`
- `repo_filesystem_walk`
- `file_content_read`
- `file_stat_execution`
- `git_ls_files`
- `git_status`
- `test_execution`
- `dependency_install`
- `model_assisted_inventory`
- `external_api_inventory`
- `report_export`
- `signed_inventory`
- `evidence_creation`
- `verifier_success_claim`
- `proof_repo_state`
- `proof_file_exists`
- `proof_tests_passed`
- `proof_code_safe`
- `proof_secure`
- `proof_compliant`

## 5. Path Policy

Allowed path examples:

- `README.md`
- `pyproject.toml`
- `package.json`
- `src/aegis/core/example.py`
- `tests/test_core/example_test.py`
- `docs/source-inventory-design.md`

Allowed examples are still candidate metadata only. The contract does not prove
that those paths exist or contain source.

Denied by default:

- absolute Windows, POSIX, UNC, home-relative, or external paths
- path traversal and control-character paths
- `.env`, keys, pem files, tokens, credentials, passwords, private keys, and
  secret-like names
- `logs/`, `runtime/`, `journal/`, `journals/`, `evidence/`, and `replay/`
- `.git/`, `.venv/`, `venv/`, `node_modules/`, `.next/`, `dist/`, `build/`,
  `coverage/`, cache folders, scratch folders, and temp folders
- `data/` unless a future policy explicitly scopes it
- `models/`, `vector_db/`, `vectors/`, `datasets/`, `artifacts/`, model files,
  vector files, and local database artifacts
- `screenshots/`, `browser-output/`, `playwright-report/`, `test-results/`,
  and image/video artifacts
- hidden paths unless explicitly future-gated
- symlink candidates unless explicitly future-gated

Future-gated hidden or symlink metadata remains metadata only. It is not a
read, stat, traversal, target-resolution, or evidence grant.

## 6. Budget Policy

The contract requires:

- `budget_policy`
- `max_file_count`
- `max_file_size_bytes`
- `max_total_bytes`

Current review limits:

- file count: `5000`
- file size: `2000000` bytes
- total bytes: `50000000` bytes

Budgets above those limits return `requires_human_review`. The helper does not
count actual files or actual bytes.

## 7. Generated, Binary, Secret, Privacy, Hidden, And Symlink Rules

Generated artifacts, binary-like candidates, dependency folders, build outputs,
screenshots, browser outputs, model/vector files, datasets, logs, journals,
evidence folders, and data folders are excluded from this design by default.

High-risk scopes such as generated-artifact exclusion, secret exclusion, and
future read planning require `privacy_class` and `data_sensitivity`.

The helper records limitations as `source_inventory_limitation` findings only.
Those findings are not evidence and cannot mark verifier success.

## 8. Git And Test Boundary

The contract may preserve caller-supplied commit refs, branch refs, and test
path candidates. It does not run git, run tests, read test output, or prove the
current worktree state. Test path candidates are not proof tests passed.

## 9. Relationship Boundaries

Repo Audit Pack:
This source inventory design may become input to a future Repo Audit Pack
runner. It does not expand the existing Repo Audit Pack contract into a runner.

Implementation Readiness:
Implementation readiness can reference source inventory design metadata. It
cannot convert design readiness into execution readiness, evidence, verifier
success, or permission.

Developer Work Passport:
Source inventory metadata may become candidate context only. It is not a
passport and not proof of developer behavior, tests passed, or code safety.

Compliance Evidence Pack:
Source inventory metadata may become compliance candidate context only. It is
not legal, security, or compliance certification and is not court-admissible
evidence.

Mission Control and Tool Simulation:
Preview or simulation decisions cannot grant source inventory dispatch,
approval, lease, capability, execution permission, evidence, or verifier
success.

Tool, Evidence, Verifier, Context, Memory, and Plugin Review:
The design does not call tools, create evidence, satisfy verifier gates, compile
context, read or write memory, or publish plugin review authority. Related
decisions with dispatch, permission, evidence, verifier success, success, or
failure reasons block the design decision.

## 10. Validation Behavior

The validator rejects:

- missing request, inventory identity, repo identity, tenant scope, namespace,
  source inventory scope, or candidate/future-plan metadata
- unknown or forbidden source inventory scopes
- missing budget policy, file count, file size, or total byte budget
- budgets above review limits
- high-risk scopes without privacy and data sensitivity metadata
- forbidden policy values
- absolute, external, UNC, drive-root, home-relative, traversal, empty, or
  control-character paths
- secret, runtime/log, generated/cache, data, model/vector/dataset,
  screenshot/browser-output, hidden, and symlink paths
- authority, runtime dispatch, approval, capability, lease, frontend authority
- repo scan, file read, traversal, stat, git, test execution, subprocess, model,
  tool, API, MCP, memory, report generation, export, and signing requests
- repo-state, file-exists, tests-passed, code-safe, security, and compliance
  proof claims
- evidence, verifier, verified-success, and success claims
- unsafe related decisions

The helper never returns `runtime_dispatch_allowed=true`.

## 11. Tests Added

Focused tests assert:

- valid source inventory design is non-authoritative and non-dispatchable
- allowed path candidates do not claim existence, reads, stats, evidence, or
  verifier success
- request input and decision output are immutable/non-mutating
- missing identity, namespace, scope, candidate metadata, or budget metadata is
  denied
- future read plans remain unable to read now
- unknown and forbidden scopes are blocked
- execution, export, authority, evidence, verifier, success, and proof claims
  are rejected
- absolute, external, traversal, control-character, secret, runtime/log,
  generated/cache, data, model/vector/dataset, screenshot/browser-output,
  hidden, and symlink paths are denied
- hidden and symlink candidates can only become metadata candidates with
  explicit future gates
- excessive budgets require human review and count no actual files or bytes
- high-risk scopes require privacy and data sensitivity metadata
- unsafe related decisions are rejected
- findings remain limitations, not evidence or verifier truth

## 12. Intentionally Not Done

Not implemented:

- actual source inventory
- repo scanning
- file content reads
- file stat calls
- filesystem traversal
- git commands
- test execution
- subprocess execution
- model, tool, API, MCP, or memory calls
- report generation or export
- evidence creation
- verifier success
- runtime/API/frontend/planner/executor wiring
- new runtime states or protocol expansion

## 13. Remaining Risks

- Future inventory implementation still needs a separate approval, policy,
  evidence, verifier, and runtime boundary.
- Path policy remains syntactic metadata classification. It does not know
  whether a caller-supplied path exists or whether a future filesystem target
  is safe.
- Future source reads must revalidate hidden paths, symlink targets, generated
  artifacts, secrets, data folders, logs, journals, model/vector files, and
  browser outputs against live filesystem evidence.

## 14. Recommended Next Sprint

Recommended next prompt:

> Implement a read-only Repo Audit source inventory planning helper that accepts
> a validated `SourceInventoryDecision` and produces a future read plan only.
> Keep it pure, no file reads, no stat, no filesystem traversal, no git, no
> tests, no subprocesses, no tools, no evidence, no verifier success, no
> runtime/API/frontend wiring, and add negative tests proving those behaviors
> are absent.
