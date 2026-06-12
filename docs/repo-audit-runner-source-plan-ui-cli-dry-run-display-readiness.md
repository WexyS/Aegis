# Repo Audit Runner Source Plan UI/CLI Dry-Run Display Readiness
## Decision

Decision: `REPO_AUDIT_SOURCE_PLAN_DISPLAY_READINESS_WITH_TESTS`

This sprint adds a pure readiness contract for representing how a future UI panel,
CLI summary, Mission Control card, audit-query projection, report preview, or
operator-review queue may display Repo Audit dry-run source-plan metadata.

The contract is display readiness only. It does not render UI, emit CLI output,
generate reports, fetch sources, read files, create evidence, mark verifier
success, or grant execution permission.

## Scope

The helper validates caller-supplied display metadata for future dry-run source
plan presentation surfaces. It classifies display surface, display intent,
display status, truth label, risk label, source references, provenance,
operator-review requirements, and related readiness decisions.

The implementation is:

- `src/aegis/core/repo_audit_source_plan_display.py`
- `tests/test_core/test_repo_audit_source_plan_display.py`

## Why This Exists

Repo Audit dry-run source planning produces candidate metadata that future
interfaces will need to show to an operator. That display layer must not turn
candidate metadata into source truth, proof, repo-read permission, evidence,
verifier success, or runtime permission.

This contract gives Aegis a backend-owned, non-authoritative display-readiness
shape before real UI/CLI wiring exists.

## Why This Is Not UI, CLI, Reports, Or Repo Access

This sprint intentionally does not implement:

- React UI rendering
- CLI command output
- report preview generation
- generated artifacts
- GitHub API calls
- URL fetches
- browser fetches
- raw file fetches
- git clone
- local repo reads
- repo scans
- directory scans
- file list/stat/hash/read
- HTTP or external API calls
- MCP/tool/model/web calls
- memory or context retrieval
- context package creation
- cache/source/citation records
- evidence
- verifier success
- runtime/API/frontend integration

Every output invariant keeps those fields false.

## Display Surface Classes

- `ui_panel_future`
- `cli_summary_future`
- `mission_control_card_future`
- `audit_query_projection_future`
- `report_preview_future`
- `operator_review_queue_future`
- `unknown`

The `future` suffix means the surface is a future presentation target. It does
not mean the helper rendered anything.

## Display Intent Classes

- `summarize_dry_run_plan`
- `show_candidate_sources`
- `show_exclusions`
- `show_blockers`
- `show_operator_review_items`
- `show_future_gates`
- `show_privacy_boundaries`
- `show_trust_freshness_completeness`
- `show_provenance_refs`
- `show_non_authority_notice`
- `unknown`

Display intent is descriptive metadata only.

## Display Status Classes

- `display_ready_metadata_only`
- `requires_dry_run_source_plan`
- `requires_operator_review`
- `blocked_by_privacy`
- `blocked_by_unknown_scope`
- `blocked_by_missing_provenance`
- `future_gated`
- `unavailable`
- `unknown`

`display_ready_metadata_only` means a future display surface may describe the
metadata. It does not authorize UI rendering, CLI output, source access, repo
reads, or execution.

## Display Truth Labels

- `metadata_only`
- `candidate_only`
- `excluded_by_policy`
- `blocked`
- `future_gated`
- `operator_review_required`
- `bounded_projection`
- `stale_or_unverified`
- `low_trust`
- `unavailable`
- `unknown`

Truth labels preserve uncertainty. They must not be rewritten into verified
source truth, proof, availability, permission, cleanup, or completion claims.

## Display Risk Labels

- `info`
- `low`
- `medium`
- `high`
- `critical`
- `unknown`

High, critical, and unknown risk labels require operator review in the display
readiness projection.

## Candidate, Excluded, Blocked, Future-Gated, And Operator-Review Display Rules

Candidate metadata can be displayed only as candidate metadata. It cannot be
displayed as read, fetched, verified, safe, complete, or authoritative.

Excluded metadata can be displayed only as excluded by policy. It cannot be
displayed as deleted, cleaned, or remediated.

Blocked metadata can be displayed only as blocked. It cannot be displayed as
permitted.

Future-gated metadata can be displayed only as future-gated and requires
operator review. It cannot be displayed as available now.

Operator-review metadata remains review-required and cannot be collapsed into
success.

## Source Refs And Provenance Display Boundaries

The helper requires source refs or provenance plus dry-run source-plan reference
metadata. These are references only:

- source refs are not evidence
- provenance refs are not verifier success
- GitHub/source metadata is not proof
- bounded projections are not complete repo plans
- low-trust metadata remains low trust

## Non-Authority Wording Rules

Future UI/CLI display text should preserve these constraints:

- say `candidate`, not `verified`
- say `metadata only`, not `read`
- say `excluded by policy`, not `deleted`
- say `blocked`, not `permitted`
- say `future-gated`, not `available`
- say `source refs`, not `evidence`
- say `bounded projection`, not `complete audit`
- say `low trust` or `stale`, not `authoritative`

## Relationship To Repo Audit Dry-Run Source Plan

The dry-run source plan can supply display candidates, but it cannot authorize
display authority, repo reads, file access, source truth, evidence, verifier
success, reports, or execution.

Unsafe dry-run decisions that claim reads, scans, file list/stat/hash/read,
proof, dispatch, evidence, verifier success, or grants are rejected.

## Relationship To Repo Audit Source Intake

Source intake metadata can describe future source candidates. It remains
candidate metadata and cannot authorize GitHub access, local repo reads, context
creation, source records, reports, or display authority.

## Relationship To GitHub Source Connector

GitHub Source Connector readiness can provide source refs and provenance
candidates. It cannot authorize GitHub API calls, URL fetches, browser fetches,
raw file fetches, clone, raw content ingestion, or private repo access.

## Relationship To Web Research Gateway

Web Research Gateway readiness cannot authorize web queries, page fetches,
browser scraping, HTTP requests, source truth, or display proof.

## Relationship To Context Policy

Context Policy cannot be contradicted. Display metadata does not create context
packages, retrieve context, retrieve memory, send data externally, or permit
cloud routing.

## Relationship To Identity Scope And Memory Governance

Private, project-scoped, or repository-scoped display metadata requires Identity
Scope. Memory-derived display metadata requires Memory Governance.

Those related decisions are references only; they do not create display
authority or execution permission.

## Relationship To Local Model Context Profile

Local Model Context Profile metadata cannot authorize model synthesis, model
calls, context delivery, or display truth. Model output remains low-trust unless
future policy and verification explicitly say otherwise.

## Relationship To Audit Query Layer

Audit Query Layer metadata may later consume display projections, but display
readiness does not create query execution, query results, reports, or proof.

## Relationship To Developer Work Passport And Compliance Evidence

Developer Work Passport and Compliance Evidence may later consume source
candidates. Display metadata is not passport proof, compliance proof,
certification, audit evidence, or verifier success.

## Relationship To MCP And Tool Future Work

MCP/tool metadata can be shown only as low-trust/reference metadata. It cannot
authorize tool calls, MCP calls, source access, context creation, or execution.

## Why Display Is Not Evidence Or Verifier Success

Display readiness describes how metadata may be labeled. It does not observe
files, fetch sources, inspect repository contents, check source availability, or
run verifiers. Evidence and verifier success must come from separate
backend-owned runtime paths when those are explicitly implemented and approved.

## Tests Added

Focused tests cover:

- valid metadata-only display projection
- future UI/CLI/Mission Control/Audit Query/report preview/operator queue
  surfaces remaining projection-only
- required field validation
- source refs/provenance and dry-run plan ref requirements
- taxonomy rejection for unsupported values
- candidate/excluded/blocked/future-gated/operator-review/low-trust labels
- high/critical risk operator-review behavior
- Identity Scope and Memory Governance requirements
- display overclaim rejection
- authority/grant/evidence/verifier/proof rejection
- UI render, CLI output, report/artifact rejection
- GitHub/web/API/fetch/clone/read/list/stat/hash rejection
- model/tool/MCP/context/memory/cache/source/citation/data-transfer rejection
- unsafe related decision rejection
- input and related-decision immutability
- output invariants staying non-authoritative even when blocked

## Intentionally Not Done

- No UI was rendered.
- No CLI command was added.
- No report preview was generated.
- No GitHub or web access was performed.
- No repo read, file list, stat, hash, or scan was performed.
- No context package was created.
- No model/tool/MCP/API call was performed.
- No runtime/API/frontend integration was added.
- No evidence or verifier success was created.
- No approval, lease, capability, or execution permission was granted.

## Future Implementation Notes

Future UI/CLI work should consume this contract as backend-owned metadata. A
real display implementation should preserve the labels and non-authority
notices, avoid collapsing blocked/future-gated/low-trust states, and keep any
operator action behind explicit future policy and runtime gates.

Future source access, context packaging, model calls, and audit reports must be
implemented in separate sprints with their own evidence and verifier contracts.

## Remaining Risks

- Display copy can still become misleading if a future UI ignores these labels.
- Future report preview work must avoid generating artifacts from display
  metadata alone.
- Future Audit Query and Mission Control surfaces must preserve low-trust,
  stale, blocked, and future-gated labels exactly.
- This helper does not verify that a referenced source exists or is current.
