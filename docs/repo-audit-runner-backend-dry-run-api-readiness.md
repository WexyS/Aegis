# Repo Audit Runner Backend Dry-Run API Readiness
## Decision

Decision: REPO_AUDIT_DRY_RUN_API_READINESS_WITH_TESTS

This sprint adds a narrow backend-owned read-only API surface for Repo Audit dry-run projection metadata.

## Scope

Implemented:

- `GET /maintenance/repo-audit/dry-run-projection`
- `src/aegis/api/repo_audit_dry_run_projection.py`
- `tests/test_api/test_repo_audit_dry_run_projection_api.py`

The endpoint exposes dry-run planning projection metadata to future Maintenance Scan, Mission Control, CLI, or API consumers without performing source access or creating runtime truth.

## Endpoint Added

`GET /maintenance/repo-audit/dry-run-projection`

The endpoint is read-only. There is no POST, execute, run, retry, scan, fetch, clone, or report action endpoint.

## Why This Is Read-Only Projection Only

Repo Audit dry-run API projection is metadata about a future dry-run source plan. It is not execution, source truth, evidence, verifier success, report generation, compliance proof, passport proof, approval, capability, lease, or permission.

The response includes:

- `read_only=true`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_repo_audit_dry_run_api_surface`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided=false`
- `verifier_success=false`

## Why This Is Not Repo Read

The endpoint does not:

- read repositories
- scan directories
- list files
- stat files
- hash files
- read files
- prove file existence
- prove file content
- authorize repo reads

Response invariants include:

- `repo_read_performed=false`
- `repo_scan_performed=false`
- `directory_scan_performed=false`
- `file_list_performed=false`
- `file_stat_performed=false`
- `file_hash_performed=false`
- `file_read_performed=false`
- `repo_read_authorized=false`

## Why This Is Not GitHub Integration

The endpoint does not:

- call GitHub API
- fetch GitHub URLs
- perform browser fetches
- fetch raw files
- clone repositories
- perform HTTP requests
- call external APIs
- send data externally

Response invariants include:

- `github_api_called=false`
- `github_url_fetched=false`
- `browser_fetch_performed=false`
- `raw_file_fetch_performed=false`
- `git_clone_performed=false`
- `http_request_performed=false`
- `external_api_called=false`
- `data_sent_external=false`
- `github_fetch_authorized=false`

## Why This Is Not Context Package Creation

The endpoint does not retrieve memory or context, create context packages, touch vector stores, or prepare model inputs.

Response invariants include:

- `memory_retrieval_performed=false`
- `context_retrieval_performed=false`
- `context_package_created=false`
- `model_call_performed=false`
- `mcp_call_performed=false`
- `tool_call_performed=false`
- `web_query_performed=false`

## No-Current-Projection Semantics

If there is no durable/current Repo Audit dry-run projection source in backend state, the endpoint returns:

- `projection_result_class=no_projection_available`
- `api_surface_status_class=no_current_dry_run_result`
- `projection_available=false`
- `current_projection_available=false`
- `source_current=false`
- `dry_run_status=repo_audit_dry_run_not_observed`

This is neutral no-data. It is not repo failure, GitHub failure, source unavailable proof, runtime failure, evidence failure, verifier failure, or repo audit proof.

Prior design examples are not replayed as current runtime state.

## Dry-Run Metadata Candidate Semantics

Synthetic test fixtures and future backend-supplied dry-run metadata can project:

- `dry_run_plan_metadata_candidate`
- `source_intake_metadata_candidate`
- `source_plan_display_candidate`
- `candidate_sources_available`
- `exclusions_available`
- `blockers_available`

These are metadata/candidate labels only. They are not repo reads, source truth, evidence, verifier success, reports, compliance proof, passport proof, or execution permission.

## Source Candidate Semantics

Source candidates are references only. A candidate source can be included as metadata, excluded by policy, future-gated, or marked for operator review. None of those states reads source content or authorizes a future read.

## Exclusion Semantics

Exclusion metadata can represent blocked or excluded scopes such as secrets, credentials, generated artifacts, build outputs, dependency/vendor directories, model/vector artifacts, runtime journals, and raw evidence files.

Exclusion metadata is not cleanup, deletion, archive execution, or source mutation.

## Blocker Semantics

Blocked projections remain blocked and do not become source access. Secret-like, credential-like, private repo content, raw-content requests, unsafe related decisions, and execution/proof claims remain blocked.

## Future-Gated Semantics

Future-gated projections remain future-gated. They do not authorize local clone, GitHub fetch, repo read, context package creation, model synthesis, or report generation.

## Operator Review Semantics

Operator-review candidates can require human review. This does not authorize a run, retry, fetch, clone, repo read, report, evidence creation, verifier success, approval, capability, or lease.

## Relationship To Repo Audit Dry-Run Source Plan

The API builder validates supplied dry-run metadata through `validate_repo_audit_dry_run_source_plan_request(...)`. That core helper remains the source of projection semantics for candidate sources, exclusions, privacy, trust, freshness, and completeness.

## Relationship To Repo Audit Source Intake

Source Intake can provide candidate source metadata later, but cannot authorize source access through this API. Source intake metadata remains reference-only and non-authoritative.

## Relationship To Source Plan Display Readiness

Source Plan Display Readiness can be referenced as a display candidate. Display readiness is not frontend authority, report generation, evidence, verifier success, or source truth.

## Relationship To GitHub Source Connector

GitHub Source Connector readiness can provide GitHub source candidate metadata later. It cannot authorize GitHub API calls, URL fetches, raw file fetches, clones, or raw content ingestion through this API.

## Relationship To Web Research Gateway

Web Research Gateway readiness can provide web source planning metadata later. It cannot authorize web search, HTTP fetch, scraping, browser automation, or external data transfer through this API.

## Relationship To Context Policy / Identity / Memory Governance

Context Policy cannot be contradicted by this API. Identity Scope remains required for private/project/repository-scoped source metadata. Memory Governance remains required for memory-derived source metadata. This endpoint does not retrieve memory, context, or source content.

## Relationship To Developer Work Passport / Compliance Evidence

Developer Work Passport and Compliance Evidence may consume future source candidates, but this API does not create proof, compliance evidence, passport evidence, audit proof, certification, or report output.

## Relationship To Future Mission Control UI

Future Mission Control or Maintenance Scan UI can consume this endpoint as display metadata. UI consumers must preserve no-current-projection, metadata-only, candidate-only, blocked, future-gated, and operator-review labels.

Frontend consumers must not become authority.

## API And Frontend Authority Boundary

The response includes:

- `frontend_authority=false`
- `api_authority=false`
- `runtime_dispatch_allowed=false`
- `source_truth_claimed=false`
- `repo_audit_proof_claimed=false`

API and frontend consumers cannot turn projection metadata into source truth or execution permission.

## Intentionally Not Done

This sprint did not:

- read repositories
- scan directories
- list/stat/hash/read files
- call GitHub API
- fetch GitHub URLs
- perform browser or raw file fetches
- clone repositories
- perform HTTP requests
- call external APIs
- retrieve memory or context
- create context packages
- call models
- call tools or MCP
- perform web queries
- create cache/source/citation records
- generate reports or artifacts
- add frontend UI
- add POST/action/run/retry endpoints
- add scheduler/background jobs
- mutate runtime, journal, evidence, or replay state
- create evidence or verifier success
- grant approval, capability, or lease

## Future Implementation Notes

A future durable backend-owned projection source can be wired only after a separate sprint defines source storage, freshness, provenance, and current-vs-stale boundaries. Any actual repo read, GitHub fetch, clone, context package creation, model call, report generation, or evidence creation requires separate gates and tests.

## Remaining Risks

- Future consumers could misread no-current-projection as repo failure if labels are hidden.
- Future durable projection state must distinguish current, stale, historical, fixture, and unavailable metadata.
- Future UI or CLI work must avoid adding run/retry controls without explicit gates.
