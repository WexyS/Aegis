# Repo Audit Pack Read-Only Inventory Runner Readiness v1

## 1. Decision

- Decision: `REPO_AUDIT_INVENTORY_RUNNER_READINESS_WITH_TESTS`
- Contract version: `repo-audit-inventory-runner-readiness/1`
- Foundation tag: `foundation-v1-baseline`

This sprint adds a pure readiness contract for a future Repo Audit Pack
read-only inventory runner.

The readiness decision is not a runner. It does not scan the repository, read
files, stat files, traverse directories, run git, execute tests, spawn
subprocesses, call models, call tools, call APIs, call MCP, access memory,
generate reports, export artifacts, create evidence, mark verifier success,
grant approval, grant leases, grant capabilities, or dispatch runtime work.

## 2. Scope

Implementation files:

- `src/aegis/core/repo_audit_inventory_runner_readiness.py`
- `tests/test_core/test_repo_audit_inventory_runner_readiness.py`

The helper validates caller-supplied metadata and an optional future read-plan
decision. It produces a backend-owned readiness envelope describing what a
future explicitly gated runner would have to preserve before any actual read.

## 3. Why Inventory Runner Readiness Exists

Repo Audit now has:

- a read-only pack contract
- implementation readiness
- source inventory design
- future read-plan helper

The next pure layer is inventory runner readiness. It answers whether the
future runner contract is sufficiently constrained before any real runner is
implemented.

Readiness only describes constraints. It is not source inventory execution,
not file existence proof, not content proof, not evidence, not verifier
success, not audit output, and not permission.

## 4. Relationship To Future Read Plan

The readiness helper may consume `RepoAuditReadPlanDecision`.

Rules:

- read plan must be `plan_ready` or `plan_ready_requires_human_review`
- read plan must remain non-authoritative
- read plan must not report live reads, scans, stat calls, traversal, git,
  tests, tools, models, APIs, MCP, memory, reports, exports, evidence, or
  verifier success
- denied read-plan targets remain denied
- future-gated read-plan targets remain gated and require human review
- planned targets become future read-attempt envelopes only
- envelopes do not prove a file exists and do not read content

## 5. Relationship To Source Inventory Design

Source inventory design remains metadata-only. It may inform the read plan,
which may then inform runner readiness. Source inventory design does not
authorize a runner and cannot prove live source state.

Unsafe source inventory decisions block runner readiness when passed as a
related decision.

## 6. Relationship To Implementation Readiness

Implementation readiness remains a boundary contract. Runner readiness does
not bypass it.

A future real runner still requires separate implementation readiness, policy,
approval or lease gates where applicable, evidence expectations, verifier
postconditions, and operator review.

## 7. Runner Readiness Statuses

Supported statuses:

- `readiness_ready`
- `readiness_ready_requires_human_review`
- `blocked_by_missing_read_plan`
- `blocked_by_unsafe_read_plan`
- `blocked_by_missing_scope`
- `blocked_by_missing_budget`
- `blocked_by_missing_privacy_class`
- `blocked_by_missing_evidence_expectation`
- `blocked_by_missing_verifier_expectation`
- `blocked_by_secret_policy`
- `blocked_by_generated_artifact_policy`
- `blocked_by_runtime_journal_policy`
- `blocked_by_log_policy`
- `blocked_by_model_artifact_policy`
- `blocked_by_vector_db_policy`
- `blocked_by_dependency_policy`
- `blocked_by_build_artifact_policy`
- `blocked_by_hidden_path_policy`
- `blocked_by_symlink_policy`
- `blocked_by_content_logging_policy`
- `blocked_by_redaction_policy`
- `blocked_by_unsafe_related_decision`
- `clarification_required`

`readiness_ready` means the future runner contract is well-formed. It does
not mean reading is allowed now and does not dispatch a runner.

## 8. Future Read Attempt Envelope

For planned read-plan targets, readiness creates synthetic future read-attempt
envelopes with:

- target path metadata
- normalized relative path metadata
- expected evidence types
- expected verifier checks
- privacy and data-sensitivity labels
- policy references
- negative-evidence failure classification for future runner failures

Each envelope keeps:

- `read_performed=false`
- `content_observed=false`
- `evidence_created=false`
- `verifier_success=false`
- `content_logging_allowed=false`
- `redaction_required=true`

The envelope is not a read result.

## 9. Path Behavior

Path classification is inherited from the read plan. Runner readiness does not
normalize against the live filesystem, check existence, stat files, resolve
symlinks, or inspect content.

Denied categories remain denied:

- secret paths
- generated artifacts
- runtime journal, evidence, replay, archive, and log paths
- dependency paths
- build/cache paths
- model artifacts
- vector DB paths
- hidden paths when denied
- symlinks when denied
- external, absolute, UNC, home-relative, traversal, or unknown paths

Future-gated hidden, symlink, large-file, and sensitive targets remain
human-review gated and are not converted into read attempts.

## 10. Budget Behavior

Budget metadata is required:

- `max_file_count`
- `max_file_size_bytes`
- `max_total_bytes`
- `budget_policy`

Budget values are metadata only. The helper does not count files or bytes.
Budget excess can require human review. It does not prove repository size.

## 11. Content Logging And Redaction

Runner readiness requires:

- content logging policy
- redaction policy
- raw content logging disabled by default
- secrets never logged
- sensitive redaction required
- binary, generated, runtime journal, model, and vector content not logged

These are future runner preconditions, not proof that a runner enforced them.

## 12. Evidence Expectation

Future real reads require evidence expectations such as:

- `file_read_attempt_evidence_expected`
- `path_normalization_evidence_expected`
- `exclusion_policy_evidence_expected`
- `file_hash_evidence_expected_future`
- `no_content_logged_without_policy`

Evidence expectation is not evidence. Runner readiness cannot create evidence.

## 13. Verifier Expectation

Future real reads require verifier expectations such as:

- `path_within_repo_root_verifier`
- `forbidden_path_exclusion_verifier`
- `budget_enforcement_verifier`
- `secret_exclusion_verifier`
- `content_read_boundary_verifier`

Verifier expectation is not verifier success. Runner readiness cannot verify
itself.

## 14. Relationship To Repo Audit Pack

Runner readiness can feed a future Repo Audit inventory runner as contract
metadata only.

It is not:

- a Repo Audit finding
- source inventory
- an audit report
- audit proof
- a read result
- a permission grant
- a runtime dispatch signal

## 15. Relationship To Mission Control / Tool Simulation

Runner readiness may support future Mission Control or Tool Simulation
previews. Those previews remain non-authoritative. A future runner still needs
backend policy, approval or lease gates where applicable, evidence, verifier
postconditions, and runtime control.

## 16. Relationship To Developer Work Passport / Compliance Evidence

Runner readiness can provide candidate references only in a future phase. It
is not proof of work quality, legal compliance, safety, security, or audit
completion.

## 17. Relationship To Evidence / Verifier

Runner readiness creates no evidence and no verifier success. Missing future
read evidence remains missing until a future backend-owned runner emits real
evidence.

## 18. Relationship To Context / Memory

Context and memory cannot provide path authority. Memory cannot assert file
safety, refresh runner readiness, or authorize reads. This helper performs no
memory access.

## 19. Relationship To Policy / Approval / Lease

Runner readiness cannot grant policy approval, operator approval, capability,
lease, or execution permission. A future actual read may require policy,
approval, and lease checks depending on scope.

Scope expansion requires a future explicit gate.

## 20. Tests Added

`tests/test_core/test_repo_audit_inventory_runner_readiness.py` covers:

- valid non-authoritative readiness
- read-plan target preservation
- future read-attempt envelopes without reads
- no file existence or content proof
- missing identity, scope, budget, privacy, evidence, and verifier blockers
- required exclusion, content logging, and redaction policies
- denied target preservation
- future-gated hidden and symlink target preservation
- budget review behavior without counting files or bytes
- unsafe read-plan and related decisions rejected
- authority, evidence, verifier, proof, report, export, tool, model, API, MCP,
  memory, and execution claims rejected
- input and supplied-decision immutability

## 21. Intentionally Not Done

- no actual repo scanning
- no live file reads
- no filesystem traversal
- no stat calls
- no git commands
- no subprocesses
- no test execution as product behavior
- no model/tool/API/MCP/memory behavior
- no endpoint
- no frontend UI
- no runtime/planner/executor integration
- no journal/evidence/replay/runtime mutation
- no reports, exports, audit files, passport files, compliance files, or
  signatures
- no evidence or verifier success
- no approvals, leases, capabilities, or execution permission

## 22. Future Real Read-Only Runner Notes

A future runner sprint should remain separate and must require:

- explicit implementation-readiness gate
- policy check
- operator approval or lease when required
- backend-owned read-only execution path
- read-attempt evidence
- negative evidence on failure
- path-within-repo verifier
- forbidden-path exclusion verifier
- budget enforcement verifier
- secret exclusion verifier
- content logging and redaction verifier
- post-run audit showing no forbidden paths were read

## 23. Remaining Risks

- This contract only validates metadata shape and related-decision safety.
- It cannot prove a future implementation will enforce the same rules.
- Future runner implementation must not use this readiness decision as
  execution permission.
- Future read attempts must still be journaled and evidenced by backend-owned
  runtime code in a later explicitly approved sprint.
