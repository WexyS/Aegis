# Repo Audit Runner Dry-Run Source Plan Projection
## Decision

REPO_AUDIT_DRY_RUN_SOURCE_PLAN_WITH_TESTS

This sprint adds a pure dry-run source plan projection contract. It does not
implement GitHub access, URL fetching, browser automation, repository cloning,
local file reads, directory scans, file listing, file stat, file hashing,
context package creation, model calls, source records, citation records,
reports, artifacts, evidence, verifier success, or runtime integration.

## Scope

The contract validates caller-supplied dry-run source plan metadata and related
readiness decisions. It projects what future source candidates would be included
as metadata, excluded, future-gated, or require operator review without touching
any source.

Dry-run projection remains metadata only:

- Dry-run source plan projection is not repo read.
- Dry-run source plan projection is not GitHub access.
- Dry-run source plan projection is not file listing.
- Dry-run source plan projection is not context package creation.
- Dry-run source plan projection is not source truth.
- Dry-run source plan projection is not evidence.
- Dry-run source plan projection is not verifier success.
- Dry-run source plan projection cannot authorize future execution by itself.

## Why This Is Not Repo Read, GitHub Integration, or Context Package Creation

The helper only classifies metadata supplied by the caller. It does not call the
GitHub API, fetch URLs, open browser sessions, clone repositories, read local
files, list files, stat files, hash files, inspect repository contents, create
context packages, call models, cache source data, or generate reports.

Any future source runner requires a separate implementation boundary with
backend policy, identity scope, evidence capture, verifier postconditions,
operator review, no-secret handling, and audit logging.

## Dry-Run Plan Classes

- `github_repo_source_plan`
- `github_file_source_plan`
- `github_issue_pr_source_plan`
- `local_repo_metadata_plan`
- `local_clone_future_plan`
- `web_source_plan`
- `package_dependency_plan`
- `documentation_plan`
- `release_notes_plan`
- `security_advisory_plan`
- `mixed_source_plan`
- `unknown`

Plan classes describe source-plan shape only. They do not authorize access.

## Plan Operations

- `classify_dry_run_plan`
- `project_candidate_sources`
- `project_allowed_scopes`
- `project_blocked_scopes`
- `project_exclusion_policy`
- `project_privacy_boundaries`
- `project_freshness_requirements`
- `project_provenance_requirements`
- `project_context_budget_requirements`
- `project_operator_review_requirements`
- `project_future_execution_gates`
- `unknown`

Operations are dry-run projections. Future execution gates remain non-executing.

## Plan Status Classes

- `dry_run_ready`
- `metadata_only_projection`
- `requires_identity_scope`
- `requires_context_policy`
- `requires_source_intake`
- `requires_github_source_connector`
- `requires_web_gateway`
- `requires_repo_audit_readiness`
- `requires_operator_review`
- `blocked_by_privacy`
- `blocked_by_exclusion_policy`
- `blocked_by_unknown_scope`
- `blocked_by_secret_or_credential`
- `future_gated`
- `unknown`

Status is descriptive. It does not grant approval, capability, lease, execution
permission, evidence, or verifier success.

## Candidate Source Dispositions

- `include_candidate_metadata_only`
- `exclude_by_policy`
- `exclude_generated`
- `exclude_build_output`
- `exclude_vendor_dependency`
- `exclude_secret_like`
- `exclude_credential_like`
- `exclude_runtime_journal`
- `exclude_raw_evidence`
- `exclude_model_or_vector_artifact`
- `require_operator_review`
- `future_gated`
- `unknown`

Included candidates are metadata-only. Excluded candidates preserve exclusion
reason. Future-gated candidates do not execute. Operator-review candidates do not
become approvals.

## Projection Completeness Classes

- `complete_for_supplied_metadata`
- `bounded_metadata_only`
- `partial`
- `stale`
- `unavailable`
- `unknown`

Completeness is scoped to supplied metadata. Bounded metadata cannot claim a
complete repository source plan.

## Trust Classes

- `backend_supplied_metadata`
- `source_intake_candidate`
- `github_connector_candidate`
- `web_gateway_candidate`
- `repo_audit_read_plan_candidate`
- `user_supplied_low_trust`
- `frontend_supplied_low_trust`
- `model_output_low_trust`
- `mcp_output_low_trust`
- `tool_output_low_trust`
- `unknown`

User, frontend, model, MCP, and tool metadata remain low trust. Low-trust source
metadata requires review and never becomes authority.

## Source Refs and Provenance Rules

Every dry-run plan requires source refs or provenance. These references are
planning pointers only. They do not prove source existence, content, freshness,
safety, authenticity, compliance, or audit quality.

## Public and Private Repo Dry-Run Rules

Public source candidates can be projected as metadata. Public does not allow raw
content ingestion. Private repository metadata requires Identity Scope when
scoped. Private repository content is blocked until a later policy, identity,
evidence, and verifier boundary exists.

## Future Read-Plan Handoff Boundaries

Repo Audit read-plan candidates can inform dry-run projection, but they cannot
authorize repo reads. Candidate source dispositions are preserved as metadata,
exclusion, future-gated, or operator-review categories.

## Exclusion Policy Rules

Dry-run projection requires exclusion metadata for secrets, credentials, env
files, private keys, generated artifacts, build outputs, vendor dependencies,
model files, vector database files, runtime journals, and raw evidence files.
Missing required exclusions block the projection.

## Context Budget Requirements

The dry-run plan may reference future context budget requirements, but it does
not create a context package, retrieve context, route to a model, or send data
externally.

## Operator Review Requirements

Operator review is required for private, unknown, low-trust, future-gated,
floating branch, or explicitly review-marked candidates. Review requirement is
not approval.

## Blocked Source Scopes

Generated artifacts, build outputs, vendor dependency directories, model files,
vector database files, runtime journals, raw evidence files, env files, private
keys, credentials, secrets, and unknown sensitive material remain excluded.

## Relationship to Repo Audit Source Intake

Repo Audit Source Intake can supply candidates. It cannot authorize reads, API
calls, context packages, model calls, source truth, evidence, verifier success,
or proof.

## Relationship to GitHub Source Connector

GitHub Source Connector readiness can supply GitHub candidates. It cannot
authorize GitHub API calls, URL fetches, raw file fetches, repository cloning,
MCP GitHub access, private repository access, or raw content ingestion.

## Relationship to Web Research Gateway

Web Research Gateway readiness can supply web source planning. It cannot
authorize search, fetch, API, scrape, cache writes, or citation records.

## Relationship to Context Policy

Context Policy must not be contradicted. It does not authorize context package
creation, provider routing, cloud routing, source retrieval, or model delivery.

## Relationship to Identity Scope and Memory Governance

Identity Scope is required for private, project, or repository-scoped source
metadata. Memory Governance is required for memory-derived source metadata.
Neither grants source access here.

## Relationship to Local Model Context Profile

Local Model Context Profile cannot authorize model synthesis, source-to-model
context delivery, or dry-run projection truth. Model output remains proposal-only
and lower trust.

## Relationship to Repo Audit Pack and Read Plan

Repo Audit Pack and read-plan metadata may be referenced as dry-run candidates.
They do not authorize repo reads, scans, file lists, stats, hashes, findings, or
reports.

## Relationship to Developer Work Passport and Compliance Evidence

Developer Work Passport and Compliance Evidence may consume approved candidates
later. Dry-run source plans are not proof of work quality, security, compliance,
certification, passport validity, or official audit status.

## Relationship to MCP and Tool Future Work

MCP/tool metadata cannot authorize source access. Future MCP/tool usage requires
policy registration, capability scope, approval rules, evidence expectations,
verifier expectations, and audit records.

## Why Dry-Run Source Plan Is Not Proof

A dry-run source plan is a planning projection. It is not evidence, verifier
success, source truth, repo audit proof, compliance proof, passport proof,
permission, approval, or a lease.

## Tests Added

Focused tests cover:

- GitHub public repository, README, dependency manifest, selected file, and
  security advisory dry-run candidates
- required fields, source refs/provenance, candidate metadata, and exclusion
  policy enforcement
- private, secret, credential, unknown, and internal future privacy handling
- excluded generated, build, vendor, model/vector, runtime journal, and raw
  evidence candidates
- branch floating and pinned freshness semantics
- bounded metadata and stale source completeness handling
- low-trust user/frontend/model/MCP/tool metadata
- denial of GitHub/API/fetch/clone/local read/repo scan/directory scan/file
  list/stat/hash/read behavior
- denial of HTTP/external API/MCP/tool/model/web calls
- denial of memory/context retrieval and context package creation
- denial of cache/source/citation/report/artifact creation and external transfer
- denial of source truth, repo audit proof, compliance proof, passport proof,
  evidence, verifier success, authority, and grants
- unsafe related-decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No GitHub API calls.
- No URL fetches.
- No browser automation.
- No raw file fetches.
- No repository cloning.
- No local repository reads.
- No repository scans or directory scans.
- No file listing, stat, hash, or read.
- No HTTP or external API calls.
- No MCP/tool/model/web calls.
- No memory/context retrieval.
- No context package creation.
- No cache, source record, citation record, report, or artifact creation.
- No runtime/API/frontend integration.
- No journal/evidence/replay mutation.
- No evidence or verifier success.

## Future Implementation Notes

A later UI/CLI dry-run display readiness sprint can decide how to present this
metadata without creating frontend authority. A later implementation boundary
must define backend-owned source access, policy checks, identity handling,
evidence capture, verifier postconditions, redaction, hashing where appropriate,
and audit logging.

## Remaining Risks

- Public sources can still contain secrets or sensitive data.
- Branch references can drift.
- Source refs can become stale or unavailable.
- User-generated and model-generated metadata can be misleading.
- Private repositories require a dedicated identity/privacy/access boundary.
- Real Repo Audit runner implementation still needs separate evidence and
  verifier contracts before any source read is safe.
