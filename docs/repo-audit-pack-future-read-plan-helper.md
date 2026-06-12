# Repo Audit Pack Future Read Plan Helper
## 1. Decision

- Decision: `REPO_AUDIT_FUTURE_READ_PLAN_WITH_TESTS`
- Contract version: `repo-audit-future-read-plan/1`
- Foundation tag: `foundation-baseline`

This sprint adds a pure future read-plan helper for Repo Audit Pack.

The read plan is not a read. It does not scan the repository, read files, stat
files, traverse directories, run git, execute tests, spawn subprocesses, call
models, call tools, call APIs, call MCP, access memory, generate reports,
export artifacts, create evidence, mark verifier success, grant approval,
grant leases, grant capabilities, or dispatch runtime work.

## 2. Scope

Implementation files:

- `src/aegis/core/repo_audit_read_plan.py`
- `tests/test_core/test_repo_audit_read_plan.py`

The helper accepts caller-supplied metadata and, optionally, a validated source
inventory design decision. It produces a backend-owned plan describing what a
future explicitly gated read-only runner may attempt and what it must not
attempt.

## 3. Why Future Read Plan Exists

Repo Audit now has:

- a read-only pack contract
- an implementation-readiness contract
- a source-inventory design contract

The next pure layer is a future read plan. It translates synthetic candidate
path metadata into planned, denied, or future-gated targets without treating
the plan as permission, proof, evidence, verifier success, or audit output.

## 4. Relationship To Source Inventory Design

The helper may consume `SourceInventoryDecision` output.

Rules:

- source inventory must remain non-authoritative
- source inventory must not report live reads, scans, stat calls, traversal,
  git, tests, tools, models, APIs, MCP, memory, reports, exports, evidence, or
  verifier success
- source inventory failures block read planning except human-review-only budget
  excess
- paths supplied by source inventory are reclassified syntactically by the read
  plan before becoming plan targets
- source inventory metadata does not prove a file exists

## 5. Relationship To Implementation Readiness

Implementation readiness remains a boundary contract. It does not authorize a
future read plan, and a future read plan does not bypass implementation
readiness.

Unsafe implementation-readiness decisions block read planning when they carry
dispatch, permission, evidence, verifier success, success, or failure reasons.

## 6. Read Plan Statuses

Supported statuses:

- `plan_ready`
- `plan_ready_requires_human_review`
- `blocked_by_source_inventory`
- `blocked_by_missing_scope`
- `blocked_by_missing_budget`
- `blocked_by_budget_excess`
- `blocked_by_secret_policy`
- `blocked_by_generated_artifact_policy`
- `blocked_by_runtime_journal_policy`
- `blocked_by_hidden_path_policy`
- `blocked_by_symlink_policy`
- `blocked_by_path_policy`
- `blocked_by_privacy_policy`
- `blocked_by_missing_evidence_expectation`
- `blocked_by_missing_verifier_expectation`
- `blocked_by_unsafe_related_decision`
- `clarification_required`

`plan_ready` means the metadata plan is well-formed. It does not mean a read is
allowed now, does not dispatch a runner, and still requires future runtime,
policy, evidence, verifier, and human-review gates before any real read.

## 7. Read Target Categories

Planned target categories:

- `planned_metadata_only_candidate`
- `future_read_candidate`

Denied target categories:

- `denied_secret_path`
- `denied_generated_artifact`
- `denied_runtime_journal`
- `denied_log_path`
- `denied_dependency_path`
- `denied_build_cache`
- `denied_model_artifact`
- `denied_vector_db`
- `denied_hidden_path`
- `denied_symlink`
- `denied_external_path`
- `denied_traversal_path`
- `denied_unknown`

Future-gated target categories:

- `future_gated_hidden_path`
- `future_gated_symlink`
- `future_gated_large_file`
- `future_gated_sensitive_path`

Every target preserves the original path, safe normalized relative path when
available, category, reason, privacy label, expected future evidence, expected
future verifier checks, source policy refs, limitations, and unknowns.

## 8. Path Behavior

Path handling is syntactic over caller-supplied strings only.

Denied by default:

- absolute paths
- external URL or object-store paths
- UNC/network paths
- drive-root paths
- home-relative paths
- traversal paths
- null/control-character paths
- `.env`, key, token, credential, password, private-key, and secret-like paths
- runtime, evidence, replay, journal, archive, and log paths
- `.git`, `.venv`, `node_modules`, dependency paths
- `.next`, `dist`, `build`, cache, coverage, scratch, temp paths
- model, vector DB, dataset, and artifact paths
- browser output, screenshots, images, and video artifacts
- hidden paths unless future-gated
- symlink candidates unless future-gated

The helper never proves file existence, file content, current repo state, or
path safety against the live filesystem.

## 9. Budget Behavior

Budget metadata is required:

- `max_file_count`
- `max_file_size_bytes`
- `max_total_bytes`
- `budget_policy`

Review limits:

- file count: `5000`
- file size: `2000000` bytes
- total bytes: `50000000` bytes

Budget excess returns human-review status unless the caller policy says to
block above limits. Target-level file size metadata is descriptive only. The
helper does not count real files or real bytes.

## 10. Evidence Expectation

Future real reads require evidence expectations such as:

- `file_read_attempt_evidence_expected`
- `path_normalization_evidence_expected`
- `exclusion_policy_evidence_expected`
- `file_hash_evidence_expected_future`
- `no_content_logged_without_policy`

Evidence expectation is not evidence. The read plan cannot create evidence.
Future evidence must come from a backend-owned read-only runner in a later
explicit sprint.

## 11. Verifier Expectation

Future real reads may require verifier expectations such as:

- `path_within_repo_root_verifier`
- `forbidden_path_exclusion_verifier`
- `budget_enforcement_verifier`
- `secret_exclusion_verifier`
- `content_read_boundary_verifier`

Verifier expectation is not verifier success. The read plan cannot verify
itself.

## 12. Relationship To Repo Audit Pack

The plan may feed a future Repo Audit runner as candidate metadata only.

It is not:

- a Repo Audit finding
- audit proof
- source inventory evidence
- a report
- a permission grant
- a runtime dispatch signal

## 13. Relationship To Mission Control / Tool Simulation

The plan can support future Mission Control or Tool Simulation previews as
metadata. Those previews remain non-authoritative. A future runner still needs
separate policy, approval or lease gates where applicable, backend evidence,
verifier checks, and runtime dispatch.

## 14. Relationship To Developer Work Passport / Compliance Evidence

The plan may later provide candidate refs only.

It is not proof of:

- work quality
- safety
- compliance
- legal certification
- security certification
- audit completion
- tests passed
- file existence
- file content

## 15. Relationship To Evidence / Verifier

The helper always preserves:

- `evidence_provided_by_read_plan=false`
- `verifier_success=false`
- `source_existence_proven=false`
- `file_content_observed=false`

Missing evidence remains missing or uncertain. Future actual reads need
backend-owned evidence and verifier boundaries.

## 16. Relationship To Context / Memory

Context and memory cannot provide path authority. Memory cannot assert file
safety. The helper does not read or write memory.

Compiled context, summaries, or memory refs may later serve as provenance only,
not permission, approval, evidence, or verifier truth.

## 17. Relationship To Policy / Approval / Lease

The plan cannot grant:

- approval
- capability
- lease
- execution permission
- runtime dispatch

Future actual reads may require policy, approval, or lease depending on scope.
Scope expansion requires a future explicit gate.

## 18. Tests Added

Focused tests assert:

- valid minimal plans are non-authoritative and non-dispatchable
- README, source, test, and docs path candidates become metadata or future-read
  candidates without existence or read claims
- source inventory decisions can supply metadata candidates without reads
- missing identity, scope, source inventory/candidate metadata, budget, privacy,
  evidence expectation, or verifier expectation blocks planning
- absolute, UNC, drive-root, home-relative, external, traversal, and
  control-character paths are denied
- secret, runtime, evidence, replay, journal, archive, log, dependency, build,
  cache, model, vector, dataset, browser-output, screenshot, and generated
  paths are denied
- hidden and symlink paths are future-gated only when policy and gate refs allow
- budget excess requires human review or blocks by policy
- denied and future-gated targets preserve reasons and policy refs
- unsafe source inventory, implementation-readiness, Repo Audit, Mission
  Control, Tool Simulation, Passport, Compliance Evidence, and Plugin Review
  decisions are rejected
- authority, dispatch, approval, capability, lease, evidence, verifier, proof,
  report, export, signing, tool, model, API, MCP, memory, and behavior flags are
  rejected
- output invariants never claim reads, scans, stat, traversal, dispatch,
  evidence, verifier success, existence proof, or content observation
- validation does not mutate caller inputs or supplied decisions

## 19. Intentionally Not Done

Not implemented:

- actual repo scanning
- source inventory runner
- live file reads
- file stat calls
- filesystem traversal
- git commands
- test execution as product behavior
- subprocess calls
- model/tool/API/MCP/memory calls
- report/export/signing generation
- audit/passport/compliance output files
- endpoint or frontend UI
- planner/executor/runtime integration
- journal/evidence/replay/runtime mutation
- approval, lease, capability, or policy lifecycle changes
- cleanup/archive/compaction

## 20. Future Real Read-Only Runner Notes

A future runner must be a separate explicit sprint and must require:

- backend-owned path normalization
- proof that each target remains inside repo root
- secret/generated/runtime/journal/log/model/vector/build/cache exclusions
- symlink and hidden-path gates
- budget enforcement
- no content logging without policy
- evidence for every read attempt
- verifier checks after read attempts
- human review for gated paths and budget excess
- failure handling that emits negative evidence rather than fake success

## 21. Remaining Risks

- The plan is syntactic metadata classification. It cannot detect live
  filesystem changes.
- Caller-supplied path metadata can be stale or incomplete.
- Future live runner work must avoid treating this helper as permission.
- Future Repo Audit findings must distinguish plan refs from evidence-backed
  observations.
