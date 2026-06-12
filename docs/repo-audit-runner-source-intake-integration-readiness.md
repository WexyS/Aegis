# Repo Audit Runner Source Intake Integration Readiness
## Decision

REPO_AUDIT_SOURCE_INTAKE_READINESS_WITH_TESTS

This sprint adds a pure readiness contract for future Repo Audit Runner source
intake. It does not implement GitHub access, URL fetching, browser automation,
repository cloning, local file reads, repository scans, context package
creation, model calls, source records, citation records, reports, evidence,
verifier success, or runtime integration.

## Scope

The contract validates caller-supplied source-intake metadata and related
readiness decisions. Its purpose is to describe how future GitHub Source
Connector candidates, Web Research Gateway planning, Context Policy, Identity
Scope, Local Model Context Profile, and Repo Audit read-plan metadata may be
referenced before any actual runner exists.

Source intake remains metadata only:

- Source intake is not repo scan.
- Source intake is not GitHub access.
- Source intake is not file read.
- Source intake is not context retrieval.
- Source intake is not source truth.
- Source intake is not repo audit proof.
- Source intake is not evidence.
- Source intake is not verifier success.

## Why This Is Not Repo Read or GitHub Integration

The helper only classifies metadata supplied by the caller. It does not call the
GitHub API, fetch URLs, open browser sessions, clone repositories, read local
files, traverse directories, inspect repository contents, create context
packages, call models, cache source data, or generate reports.

Any future source runner must be introduced by a separate boundary sprint with
backend policy, identity scope, source evidence, verifier checks, audit records,
operator review, and explicit no-secret/no-raw-sensitive safeguards.

## Source Intake Classes

- `github_source_candidate`
- `local_repo_metadata_candidate`
- `local_clone_reference_future`
- `web_source_candidate`
- `package_registry_candidate`
- `documentation_source_candidate`
- `release_notes_source_candidate`
- `security_advisory_source_candidate`
- `user_supplied_source_metadata`
- `repo_audit_read_plan_candidate`
- `unknown`

These classes describe candidate source origins only. They do not authorize any
source access.

## Source Intake Operations

- `classify_source_intake`
- `propose_repo_audit_source_handoff`
- `propose_read_plan_link`
- `propose_scope_filter`
- `propose_exclusion_policy`
- `propose_privacy_boundary`
- `propose_context_budget_link`
- `propose_source_ref_mapping`
- `propose_provenance_mapping`
- `propose_future_fetch_gate`
- `propose_future_local_read_gate`
- `unknown`

Operations are planning operations. Future fetch or local-read gate operations
remain future-gated and non-executing.

## Repo Source Scope Classes

- `repository_metadata_only`
- `readme_candidate`
- `docs_candidate`
- `dependency_manifest_candidate`
- `source_file_candidate`
- `test_file_candidate`
- `config_file_candidate`
- `selected_path_candidate`
- `issue_pr_metadata_candidate`
- `release_metadata_candidate`
- `advisory_metadata_candidate`
- `no_raw_content`
- `unknown`

Readme, docs, dependency manifests, source files, tests, config, and selected
paths are future read-plan candidates only. They do not prove file existence and
do not authorize reads.

## Privacy Classes

- `public_metadata`
- `public_source_candidate`
- `private_repo_metadata`
- `private_repo_content`
- `internal_repo_future`
- `secret_like`
- `credential_like`
- `sensitive`
- `unknown`

Secrets and credentials are always blocked. Unknown privacy blocks source
access. Private repository metadata requires Identity Scope when scoped. Private
repository content remains blocked until a later explicit boundary exists.

## Readiness Status Classes

- `intake_ready_metadata_only`
- `requires_identity_scope`
- `requires_context_policy`
- `requires_repo_audit_readiness`
- `requires_github_source_connector`
- `requires_web_research_gateway`
- `requires_capability_lease_future`
- `requires_operator_review`
- `blocked_by_privacy`
- `blocked_by_unknown_scope`
- `blocked_by_secret_scope`
- `future_gated`
- `unknown`

Readiness status is descriptive only. It does not grant access, approval,
capability, lease, execution permission, evidence, or verifier success.

## Source Trust Classes

- `source_ref_candidate`
- `connector_metadata_candidate`
- `repo_audit_read_plan_candidate`
- `web_gateway_candidate`
- `local_metadata_candidate`
- `user_supplied_low_trust`
- `frontend_supplied_low_trust`
- `model_output_low_trust`
- `mcp_output_low_trust`
- `tool_output_low_trust`
- `unknown`

Frontend, model, MCP, tool, and user-supplied source metadata remain low trust.
They can be reviewed but cannot become authority or truth.

## Freshness Classes

- `commit_pinned`
- `tag_or_release_pinned`
- `branch_floating`
- `local_snapshot_metadata`
- `current_required`
- `stale`
- `unknown`

Pinned metadata is stronger than floating branch metadata, but it is still not
proof. Floating branch metadata preserves drift risk and requires review when
source stability matters.

## Exclusion Classes

- `secrets_excluded`
- `credentials_excluded`
- `env_files_excluded`
- `private_keys_excluded`
- `generated_artifacts_excluded`
- `build_outputs_excluded`
- `dependency_vendor_dirs_excluded`
- `model_files_excluded`
- `vector_db_files_excluded`
- `runtime_journals_excluded`
- `raw_evidence_files_excluded`
- `unknown_sensitive_excluded`
- `unknown`

Future read candidates require explicit exclusion metadata. Missing exclusion
coverage blocks the candidate rather than permitting a read.

## Source Refs and Provenance Rules

Every request must include source refs or provenance. These references are
planning pointers only. They do not prove source existence, source content,
freshness, safety, authenticity, compliance, or audit quality.

## Public and Private Repo Handoff Rules

Public source metadata can be a candidate. Public does not allow raw content
ingestion. Private repository metadata requires identity scope when scoped.
Private repository content is blocked until a later policy, identity, evidence,
and verifier boundary is approved.

## Future Read-Plan Handoff Boundaries

Repo Audit read-plan metadata can inform future read-plan candidates, but cannot
authorize a read now. Read-plan candidates are classified as candidate-only, and
they require explicit exclusion policy metadata.

## Context Package Boundaries

Source intake cannot create a context package. Context Policy may be referenced
but cannot authorize context delivery by itself. Future context packages must
re-check privacy, source refs, redaction, budget, model/provider eligibility, and
policy gates.

## Blocked Source Scopes

Generated artifacts, build outputs, vendor dependency directories, model files,
vector database files, runtime journals, raw evidence files, env files, private
keys, credentials, secrets, and unknown sensitive material remain excluded.

## Relationship to GitHub Source Connector

GitHub Source Connector readiness can supply source candidates. It cannot
authorize GitHub API calls, URL fetches, raw file fetches, repository cloning,
MCP GitHub calls, private repository access, or raw content ingestion.

## Relationship to Web Research Gateway

Web Research Gateway readiness can supply web source planning. It cannot
authorize search, fetch, API, scraping, cache writes, or citation records.

## Relationship to Context Policy

Context Policy must not be contradicted. It does not authorize source intake,
context package creation, model routing, cloud routing, or source retrieval.

## Relationship to Identity Scope and Memory Governance

Identity Scope is required for private, project, or repository-scoped source
metadata. Memory Governance is required for memory-derived source metadata.
Neither contract grants source access here.

## Relationship to Local Model Context Profile

Local Model Context Profile cannot authorize model synthesis, context delivery,
or source-to-model injection. Model output remains proposal-only and lower trust.

## Relationship to Repo Audit Pack and Read Plan

Repo Audit Pack and read-plan metadata may be referenced as candidates. They do
not authorize repo reads, repository scans, local clone access, source inventory,
findings, reports, or proof.

## Relationship to Developer Work Passport and Compliance Evidence

Developer Work Passport and Compliance Evidence may consume approved candidates
later. Source intake is not proof of work quality, security, compliance,
certification, passport validity, or official audit status.

## Relationship to MCP and Tool Future Work

MCP/tool metadata cannot authorize source access. Future MCP/tool use requires
policy registration, capability scope, approval rules, evidence expectations,
verifier expectations, and audit records.

## Why Source Intake Is Not Proof

A source candidate is a planning object. It is not evidence, verifier success,
source truth, repo audit proof, compliance proof, passport proof, permission, or
approval.

## Tests Added

Focused tests cover:

- public GitHub repository source candidate metadata
- public README, dependency manifest, release, and security advisory candidates
- required fields, source refs/provenance, and exclusion policy enforcement
- private, secret, credential, unknown, and internal future privacy handling
- required exclusion coverage for future read candidates
- branch floating and pinned freshness semantics
- low-trust user/frontend/model/MCP/tool metadata
- denial of GitHub/API/fetch/clone/local read/repo scan/file read/directory scan
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
- No HTTP or external API calls.
- No MCP/tool/model/web calls.
- No memory/context retrieval.
- No context package creation.
- No cache, source record, citation record, report, or artifact creation.
- No runtime/API/frontend integration.
- No journal/evidence/replay mutation.
- No evidence or verifier success.

## Future Implementation Notes

A later dry-run projection sprint should define how this readiness metadata is
projected into non-executing source-plan previews. A later implementation
boundary sprint must separately define backend-owned source access, policy
checks, identity handling, evidence capture, verifier postconditions, redaction,
source hashing where appropriate, and audit logging.

## Remaining Risks

- Public sources can still contain secrets or sensitive data.
- Branch references can drift.
- Source refs can become stale or unavailable.
- User-generated source metadata can be misleading.
- Private repositories require a dedicated identity/privacy/access boundary.
- Repo Audit runner implementation still needs separate evidence and verifier
  contracts before any real read is safe.
