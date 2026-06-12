# Repo Audit Dry-Run Maintenance Surface UI Readiness
## Decision

Decision: REPO_AUDIT_DRY_RUN_SURFACE_UI_READINESS_WITH_TESTS

This sprint adds a pure Repo Audit dry-run maintenance surface display readiness contract.

## Scope

Implemented:

- `src/aegis/core/repo_audit_dry_run_surface_display.py`
- `tests/test_core/test_repo_audit_dry_run_surface_display.py`

The helper validates caller-supplied display metadata for future Maintenance Scan, Mission Control, or CLI surfaces. It does not implement visible frontend UI, frontend types, endpoint polling, run/retry controls, repo reads, GitHub fetches, context packages, reports, evidence, verifier success, approval grants, capability grants, or lease grants.

## Why Dry-Run Surface UI Readiness Exists

The read-only endpoint `GET /maintenance/repo-audit/dry-run-projection` exposes dry-run projection states such as `no_projection_available`, `repo_audit_dry_run_not_observed`, candidate sources, exclusions, blockers, future gates, and operator-review candidates.

Future UI surfaces need a stable display contract so those states are not accidentally shown as repo read results, verified source truth, evidence, verifier success, compliance proof, passport proof, report generation, run authorization, cleanup/deletion, or frontend authority.

## Why This Is Not Frontend Implementation

This sprint adds no React components, no visible Maintenance Scan panel, no Mission Control card, no CLI output, no polling hook, no button, and no action control.

It is a backend-owned display-readiness helper only.

## Why This Is Not Repo Read Or GitHub Integration

The helper does not:

- read repositories
- scan directories
- list files
- stat files
- hash files
- read files
- call GitHub API
- fetch GitHub URLs
- perform browser fetches
- fetch raw files
- clone repositories
- perform HTTP requests
- call external APIs

It always returns source-access invariants as false.

## Why This Is Not Source Truth / Evidence / Verifier Success

Display metadata is not source truth. It is not evidence, verifier success, report output, compliance proof, passport proof, or repo audit proof.

The helper always returns:

- `source_truth_claimed=false`
- `repo_audit_proof_claimed=false`
- `compliance_proof_claimed=false`
- `passport_proof_claimed=false`
- `evidence_provided_by_display=false`
- `verifier_success=false`
- `report_generated=false`

## Display Source Classes

- `repo_audit_dry_run_projection_api`
- `repo_audit_dry_run_source_plan`
- `repo_audit_source_intake`
- `repo_audit_source_plan_display`
- `synthetic_fixture`
- `mission_control_future`
- `maintenance_scan_future`
- `cli_summary_future`
- `unknown`

`unknown` requires clarification and is blocked.

## Display State Classes

- `no_projection_available`
- `repo_audit_dry_run_not_observed`
- `repo_audit_dry_run_not_configured`
- `dry_run_plan_metadata_candidate`
- `source_intake_metadata_candidate`
- `source_plan_display_candidate`
- `candidate_sources_available`
- `exclusions_available`
- `blockers_available`
- `operator_review_required_candidate`
- `future_gated`
- `blocked_by_policy`
- `unknown`

`unknown` requires clarification and is blocked.

## UI Meaning Classes

Allowed:

- `neutral_no_data`
- `informational_candidate`
- `exclusion_metadata`
- `blocked_notice`
- `future_gated_notice`
- `operator_review_required`
- `warning_attention`
- `unknown`

`unknown` remains blocked until clarified.

## Forbidden UI Meanings

Forbidden:

- `repo_read_performed`
- `source_truth_verified`
- `source_available_verified`
- `evidence_available`
- `verifier_success`
- `report_generated`
- `compliance_proof`
- `passport_proof`
- `run_authorized`
- `execution_ready`
- `cleanup_performed`
- `deletion_performed`
- `frontend_authority`

These labels are rejected because UI display cannot become backend authority, source truth, proof, execution permission, cleanup state, or evidence.

## Recommended Wording

- `no_projection_available`: "No current repo-audit dry-run projection is available."
- `repo_audit_dry_run_not_observed`: "Repo-audit dry-run has not been observed."
- `candidate_sources_available`: "Candidate sources only; not source truth or repo read."
- `exclusions_available`: "Exclusion metadata only; no cleanup or deletion performed."
- `blockers_available`: "Blocked items remain blocked; not permission."
- `future_gated`: "Future-gated; not execution-ready."
- `operator_review_required_candidate`: "Operator review required; run is not authorized."
- metadata candidates: "Metadata candidate only; not evidence or verifier success."

Display wording that claims repo read, source truth, source availability verification, evidence, verifier success, report generation, compliance proof, passport proof, run authorization, execution readiness, cleanup, or deletion is rejected.

## Color And Severity Guidance

- `no_projection_available`, `repo_audit_dry_run_not_observed`, `repo_audit_dry_run_not_configured`: neutral/info, not red/fail
- candidate source metadata: info/neutral, not green verified
- exclusions: neutral/info, not cleanup success
- blockers: warning/blocked/attention, not permission
- future-gated: neutral/future, not execution-ready
- operator-review: attention/warning, not action-ready
- unknown: neutral/unknown and review-required

Display severity is not backend truth.

## No Projection Available Semantics

`no_projection_available` means no current durable dry-run projection is available. It is not repo audit failure, source unavailable proof, repo read failure, evidence failure, verifier failure, or run blocker.

The expected UI meaning is `neutral_no_data`.

## Not Observed Semantics

`repo_audit_dry_run_not_observed` means a dry-run projection has not been observed. It does not prove that source is unavailable, unsafe, verified, or readable.

The expected UI meaning is `neutral_no_data`.

## Candidate Source Semantics

Candidate source display is informational only. Candidate sources are not source truth, repo reads, verified availability, evidence, verifier success, compliance proof, passport proof, or report output.

## Exclusion Metadata Semantics

Exclusion display is metadata only. Exclusions are not cleanup, deletion, archive execution, or source mutation.

## Blocked / Future-Gated / Operator-Review Semantics

Blocked items remain blocked and do not become permission.

Future-gated items remain future-gated and do not become execution-ready.

Operator-review candidates require review but do not authorize run, retry, fetch, clone, repo read, report generation, evidence creation, verifier success, approval, capability, or lease.

## Relationship To Dry-Run API Surface

The Dry-Run API Surface can be referenced as source metadata. This helper maps API projection states into UI-safe labels but cannot make API/frontend output authoritative.

## Relationship To Source Intake

Repo Audit Source Intake can be referenced as candidate metadata. It cannot authorize source access or become source truth through this display helper.

## Relationship To Dry-Run Source Plan

Dry-Run Source Plan provides projection semantics for candidates, exclusions, blockers, future gates, and operator-review items. This display helper preserves those labels without executing or approving anything.

## Relationship To Source Plan Display Readiness

Source Plan Display Readiness remains a related display contract. It can be referenced, but it cannot create report output, frontend authority, evidence, verifier success, or proof.

## Relationship To GitHub Source Connector / Web Research Gateway

GitHub and web readiness contracts may provide future source metadata. This helper cannot authorize GitHub API calls, URL fetches, browser fetches, raw file fetches, web queries, or external data transfer.

## Relationship To Context Policy / Identity / Memory Governance

Context Policy, Identity Scope, and Memory Governance remain separate boundaries. This helper does not retrieve memory, create context packages, or send data externally.

## Relationship To Developer Work Passport / Compliance Evidence

Developer Work Passport and Compliance Evidence may consume source candidates later, but this helper cannot turn display metadata into proof, certification, compliance evidence, passport evidence, or audit output.

## Relationship To Future Mission Control UI

Future Mission Control and Maintenance Scan UI can consume this helper as a display contract. They must preserve no-data, informational, exclusion, blocked, future-gated, and operator-review meanings without adding run/retry/action controls.

## Intentionally Not Done

This sprint did not:

- implement visible frontend UI
- add frontend type files
- add polling
- add run/retry/action buttons
- add or change API endpoints
- read repositories
- scan/list/stat/hash/read files
- call GitHub API
- fetch URLs
- clone repositories
- perform HTTP requests
- call external APIs
- retrieve memory or context
- create context packages
- call models, tools, or MCP
- generate reports or artifacts
- mutate runtime, journal, evidence, or replay
- create evidence or verifier success
- grant approval, capability, or lease

## Future Implementation Notes

A future UI implementation can use this contract to map endpoint responses into display copy, icons, and severity. It should keep no-data states neutral, candidate states informational, exclusions separate from cleanup/deletion, blockers separate from permission, future gates separate from execution readiness, and operator review separate from run authorization.

Any actual repo read, GitHub fetch, clone, context package, model call, report generation, evidence creation, or run/retry control requires a separate gated implementation sprint.

## Remaining Risks

- Future UI could bypass this helper and misuse colors or labels.
- Future durable dry-run projection state must preserve current, stale, historical, unavailable, and fixture distinctions.
- Future run/retry UI needs a separate explicit authorization gate.
