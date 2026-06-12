# GitHub Source Connector Readiness
## Decision

GITHUB_SOURCE_CONNECTOR_READINESS_WITH_TESTS

This sprint adds a pure readiness contract for future GitHub source intake. It
does not implement GitHub integration, network access, repository cloning, URL
fetching, browser fetching, local repository reads, caching, source record
creation, citation record creation, model synthesis, runtime routing, evidence,
or verifier success.

## Scope

The contract validates caller-supplied GitHub source planning metadata so future
Aegis work can reason about repositories, files, branches, commits, releases,
issues, pull requests, security advisories, and packages without confusing a
source reference with authority.

The helper is intentionally read-only and non-authoritative:

- GitHub source metadata is not source truth.
- A GitHub URL is not evidence.
- A GitHub source ref is not verifier success.
- Public repository metadata is not raw-content permission.
- Private repository metadata is not private repository access permission.
- Repo Audit, Developer Work Passport, and Compliance Evidence may consume
  candidates later, but a candidate is not proof.

## Why This Is Not GitHub Integration

The readiness contract only classifies metadata supplied by the caller. It does
not call the GitHub API, fetch URLs, open a browser, clone a repository, inspect
files, read a local clone, scan directories, write caches, or create records.

Future implementation must add explicit backend policy gates, identity scope,
context policy, source evidence, verifier checks, audit records, and operator
approval where required before any real GitHub access occurs.

## GitHub Object Classes

- `github_repository`
- `github_file`
- `github_directory`
- `github_branch`
- `github_commit`
- `github_tag`
- `github_release`
- `github_issue`
- `github_pull_request`
- `github_discussion`
- `github_actions_workflow`
- `github_security_advisory`
- `github_package`
- `github_gist_future`
- `unknown`

Issues, pull requests, and discussions are treated as lower-trust,
user-generated metadata unless later source-quality checks prove otherwise.

## Repository Visibility Classes

- `public_repository`
- `private_repository`
- `internal_repository_future`
- `fork_public`
- `fork_private`
- `archived_repository`
- `deleted_or_unavailable`
- `unknown_visibility`

Private, internal, and private fork metadata require Identity Scope for any
private or repository-scoped planning. Private API/fetch/clone candidates remain
blocked in this readiness sprint.

Archived repositories preserve stale or archived status. Deleted or unavailable
repositories are unavailable and cannot become source candidates.

## Source Intent Classes

- `repo_overview`
- `readme_review`
- `architecture_review`
- `dependency_review`
- `security_static_notes`
- `issue_triage`
- `pull_request_review`
- `release_notes_review`
- `changelog_review`
- `documentation_review`
- `license_review`
- `repo_audit_candidate_source`
- `developer_work_passport_candidate_source`
- `compliance_evidence_candidate_source`
- `source_citation_lookup`
- `unknown`

These intents describe future review purposes only. They do not authorize
source access, model context delivery, repo audit execution, or compliance
claims.

## Access Method Classes

- `no_access`
- `url_classification_only`
- `github_api_future`
- `browser_fetch_future`
- `raw_file_fetch_future`
- `git_clone_future`
- `local_clone_future`
- `mcp_github_future`
- `unknown`

Only `url_classification_only` and `no_access` are non-future access classes.
Future access classes are readiness metadata only and do not perform access.
Private repository API/fetch/clone/MCP candidates remain blocked until a later
explicit policy and identity boundary exists.

## Privacy Classes

- `public_metadata`
- `public_source_candidate`
- `private_repo_metadata`
- `private_repo_content`
- `secret_like`
- `credential_like`
- `personal_private`
- `sensitive`
- `unknown`

Secrets and credentials are always blocked. Unknown privacy blocks external or
future access planning. Private repository content requires a later explicit
boundary and cannot be fetched, cloned, cached, or sent to a model here.

## Source Trust Classes

- `source_ref_candidate`
- `public_metadata_candidate`
- `official_github_metadata_candidate`
- `repository_content_candidate`
- `issue_or_pr_discussion_low_trust`
- `user_generated_low_trust`
- `archived_or_stale`
- `unavailable`
- `unknown`

Official GitHub metadata may be a stronger candidate source, but it is still not
evidence or verifier success. Issue and PR discussions remain low-trust
user-generated material.

## Freshness Classes

- `commit_pinned`
- `branch_floating`
- `release_pinned`
- `tag_pinned`
- `current_required`
- `recent_required`
- `historical_allowed`
- `stale`
- `unknown`

Commit, tag, and release pinning produce stronger metadata candidates, not proof.
Floating branches are not pinned and require review when source stability matters.
Security advisory candidates require current, recent, or pinned freshness
metadata.

## Cache Policy Classes

- `no_cache`
- `source_ref_only`
- `session_metadata_only`
- `short_ttl_metadata`
- `durable_cache_future`
- `raw_content_cache_prohibited`
- `unknown`

Cache policy does not authorize caching. Raw content caching is prohibited by
default. Durable cache candidates require public metadata and later explicit
implementation gates.

## Allowed Future Source Scopes

- `repository_metadata_only`
- `readme_candidate`
- `docs_candidate`
- `package_metadata_candidate`
- `dependency_manifest_candidate`
- `selected_file_candidate`
- `issue_metadata_candidate`
- `pr_metadata_candidate`
- `release_metadata_candidate`
- `no_raw_content`
- `unknown`

Allowed scopes are candidate scopes only. They do not prove files exist and do
not authorize reads.

## Blocked Source Scopes

- `secrets`
- `credentials`
- `env_files`
- `private_keys`
- `generated_artifacts`
- `build_outputs`
- `node_modules`
- `vendor_dependencies`
- `model_files`
- `vector_db_files`
- `runtime_journals`
- `raw_evidence_files`
- `unknown_sensitive`

Blocked scopes cannot be laundered into allowed candidate scopes. Runtime
journals, raw evidence files, model files, vector databases, dependency trees,
and build outputs remain blocked by default.

## Public vs Private Repository Rules

Public URL classification may produce source-ref metadata, but public does not
mean safe to ingest raw content. Private repository metadata requires Identity
Scope when private or repository-scoped. Private repository content cannot become
API, browser, raw fetch, clone, MCP, context, or model input in this readiness
sprint.

## Branch and Pinning Rules

Pinned commit, tag, and release metadata is stronger than a floating branch but
still not source truth, proof, evidence, or verifier success. Floating branches
preserve the fact that the target may change.

## Source Refs and Provenance

Every request must include source refs or provenance for claimed GitHub source
metadata. These references are pointers for future review only. They do not
prove availability, freshness, authenticity, content, or safety.

## GitHub Metadata vs Raw Content

GitHub metadata and URL classification can help future planning. Raw file
content, repository trees, local clone content, and generated artifacts remain
outside this contract. Raw content ingestion is explicitly false in the output.

## Relationship to Web Research Gateway

Web Research Gateway readiness cannot authorize GitHub API calls, browser
fetches, raw fetches, clone operations, or MCP GitHub access. It can be
referenced as planning context only.

## Relationship to Context Policy

Context Policy cannot be contradicted. It does not authorize GitHub source
delivery by itself. Any future GitHub source context package must re-check
privacy, redaction, provenance, source refs, and provider eligibility.

## Relationship to Identity Scope and Memory Governance

Identity Scope is required for private or repository-scoped GitHub metadata.
Memory Governance is required if GitHub context is memory-derived. Neither
contract grants GitHub access here.

## Relationship to Local Model Context Profile

Local Model Context Profile cannot authorize model synthesis, model calls, or
source-to-model context delivery. Model output remains proposal-only and cannot
turn GitHub metadata into truth.

## Relationship to Repo Audit Pack

Repo Audit Pack may consume GitHub source candidates later, but this readiness
contract does not authorize repo reads, scans, source inventory, findings,
reports, or proof.

## Relationship to Developer Work Passport and Compliance Evidence

Developer Work Passport and Compliance Evidence may later cite approved source
candidates. A candidate source is not proof of work quality, compliance,
security posture, certification, or official audit status.

## Relationship to MCP and Tool Future Work

MCP/tool metadata cannot authorize GitHub access. Future MCP GitHub usage must
register policy, capability scope, approval, provenance, evidence expectations,
and verifier expectations before any call.

## Why GitHub Source Ref Is Not Evidence

A source ref is a reference. It is not evidence, verifier success, repo audit
proof, source truth, freshness proof, content proof, or permission. Future real
reads require backend evidence and verifier checks.

## Tests Added

Focused tests cover:

- public repository, README, issue, release, and security advisory candidates
- required field and provenance enforcement
- private repository and private content blocking
- secret, credential, env, private key, generated, runtime, raw evidence, model,
  vector, dependency, and build scope blocking
- branch floating and pinned freshness semantics
- low-trust issue/PR handling
- GitHub API/fetch/browser/raw/clone/local read/repo scan/file read denial
- MCP/tool/model/web/HTTP/API/memory/context denial
- cache/source/citation/report/artifact/data-transfer denial
- source truth, repo audit proof, evidence, verifier, grant, and authority denial
- unsafe related-decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No GitHub API calls.
- No URL fetches.
- No browser automation.
- No raw file fetches.
- No repository cloning.
- No local repository reads.
- No repository scans.
- No HTTP or external API calls.
- No MCP/tool/model/web calls.
- No memory or context retrieval.
- No cache, source record, citation record, report, or artifact creation.
- No runtime/API/frontend integration.
- No journal/evidence/replay mutation.
- No evidence or verifier success.

## Future Implementation Notes

A later implementation readiness sprint should define a backend-owned GitHub
source runner boundary. That boundary must include policy registration, identity
scope, access method gates, private repository controls, cache restrictions,
source evidence, verifier checks, audit records, rate-limit handling, and
explicit no-raw-secret behavior.

## Remaining Risks

- GitHub source URLs can be stale, spoofed, deleted, moved, or rate-limited.
- Branch references can drift.
- Public repository content may still contain secrets or sensitive material.
- Issues and PRs are user-generated and may be misleading.
- Private repository access requires a later dedicated privacy and identity
  boundary.
- Raw content ingestion requires later source evidence, redaction, and verifier
  contracts.
