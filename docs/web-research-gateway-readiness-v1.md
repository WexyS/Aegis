# Web Research Gateway Readiness v1

## Decision

- Decision: `WEB_RESEARCH_GATEWAY_READINESS_WITH_TESTS`
- Contract version: `web-research-gateway-readiness/1`
- Implementation surface: `src/aegis/core/web_research_gateway.py`
- Test surface: `tests/test_core/test_web_research_gateway.py`
- Previous sprint: `SYSTEM_DRIFT_INTEGRITY_READINESS_WITH_TESTS`

This sprint adds a pure readiness contract for future web research and source
intelligence. It does not perform web searches, call search APIs, use browser
automation, fetch pages, make HTTP requests, call external APIs, send data
externally, retrieve memory/context, call models/tools/MCP, cache records,
write source/citation records, generate reports, create evidence, mark verifier
success, implement API endpoints, implement frontend UI, or mutate
runtime/journal/evidence/replay state.

## Scope

The contract validates caller-supplied web research planning metadata and
classifies:

- research subject and operation
- future provider class
- source type and source quality
- freshness requirements
- privacy and redaction requirements
- citation and provenance requirements
- cache/TTL policy
- contradiction handling
- result authority boundary

The output is non-authoritative. Web research planning cannot grant execution
permission, approval, leases, capabilities, evidence, verifier success, source
truth, synthesis truth, or runtime dispatch.

## Why Web Research Gateway Exists

Aegis should eventually support high-quality source intelligence, not cheap
snippet search. Future web research should plan queries, avoid leaking private
data, prefer official sources, score source quality, check freshness, compare
sources, detect contradictions, preserve citations, and clearly report
uncertainty.

This sprint defines the safety boundary before any real search, fetch, API,
browser, cache, or synthesis implementation exists.

## Why This Is Not Web Search Implementation

The contract never searches the web. It only validates metadata supplied by the
caller. Provider classes such as `browser_search_future` and
`general_search_api_future` are future-gated candidates, not active providers.

## Research Subject Categories

Supported subjects:

- `general_web_research`
- `official_docs_research`
- `api_reference_research`
- `release_notes_research`
- `security_advisory_research`
- `package_dependency_research`
- `legal_regulatory_research`
- `product_pricing_research`
- `news_current_events_research`
- `academic_paper_research`
- `github_public_repo_research_future`
- `github_issue_pr_research_future`
- `vendor_status_page_research`
- `troubleshooting_research`
- `source_verification_research`
- `contradiction_check_research`
- `citation_lookup_research`
- `unknown`

GitHub source research remains future-gated until a later connector/readiness
sprint.

## Research Operations

Supported operations:

- `classify_research_request`
- `propose_query_plan`
- `propose_source_selection`
- `propose_source_quality_check`
- `propose_freshness_check`
- `propose_contradiction_check`
- `propose_citation_plan`
- `propose_cache_policy`
- `propose_privacy_redaction`
- `propose_context_package_future`
- `propose_browser_fetch_future`
- `propose_search_api_future`
- `unknown`

Future fetch/search/context-package operations remain future-gated.

## Source Provider Classes

Supported provider classes:

- `no_provider`
- `browser_search_future`
- `official_search_api_future`
- `general_search_api_future`
- `domain_limited_fetch_future`
- `github_api_future`
- `package_registry_api_future`
- `academic_index_future`
- `vendor_status_api_future`
- `local_cache_future`
- `unknown`

Provider class metadata is not provider selection and does not authorize network
behavior.

## Source Type Classes

Supported source types:

- `official_primary_source`
- `vendor_documentation`
- `standards_body`
- `government_regulator`
- `academic_source`
- `security_advisory`
- `package_registry`
- `github_repository`
- `github_issue_or_pr`
- `vendor_status_page`
- `reputable_news_source`
- `community_forum`
- `blog_or_opinion`
- `social_media`
- `search_snippet`
- `scraped_page_extract_future`
- `unknown`

Scraped page extracts are future-gated. Search snippets are low trust and never
evidence.

## Source Quality Classes

Supported quality classes:

- `high_authority`
- `medium_authority`
- `low_authority`
- `community_low_trust`
- `snippet_only_low_trust`
- `unverifiable`
- `conflicting`
- `unknown`

High-authority source metadata remains candidate-only. It is not truth,
evidence, or verifier success.

## Freshness Classes

Supported freshness classes:

- `current_required`
- `recent_required`
- `stable_reference`
- `historical_allowed`
- `stale`
- `unknown`

Current-sensitive subjects such as security advisories, current news, pricing,
and vendor status require freshness metadata. Stale and unknown freshness remain
review states.

## Privacy Classes

Supported privacy classes:

- `public_query`
- `internal_context`
- `private_user_context`
- `private_repo_context`
- `personal_private`
- `sensitive`
- `secret_like`
- `credential_like`
- `regulated_or_compliance_sensitive`
- `unknown`

Secrets and credentials are blocked. Private user/repo context cannot be routed
to web providers. Unknown privacy blocks external query planning.

## Cache Policy Classes

Supported cache policy classes:

- `no_cache`
- `session_cache_only`
- `short_ttl_cache`
- `source_ref_cache_only`
- `durable_cache_future`
- `prohibited_cache`
- `unknown`

Cache policy metadata does not write cache. Durable cache remains future-gated.
Source-ref cache stores no raw page content in this sprint.

## Result Authority Classes

Supported result authority classes:

- `source_candidate_only`
- `citation_candidate_only`
- `contradiction_candidate_only`
- `freshness_candidate_only`
- `synthesis_candidate_only`
- `unavailable`
- `unknown`

Every result authority class is candidate-only. No class provides source truth,
synthesis truth, evidence, verifier success, or policy authority.

## Query Privacy and Redaction Rules

- `secret_like` and `credential_like` are blocked.
- `private_user_context` and `private_repo_context` block web provider
  candidates.
- `personal_private`, `sensitive`, regulated, and unknown privacy require
  redaction and review.
- Memory-derived context requires Memory Governance.
- Project/user scoped metadata requires Identity Scope.
- Sensitive metadata requires Context Policy.
- Private query leakage is always denied.

## Source Quality and Scoring Rules

- Official primary sources can be high-authority candidates, not truth.
- Search snippets must remain low trust.
- Community forums must remain lower trust.
- Conflicting source metadata requires contradiction handling.
- Unverifiable sources require human review.

## Freshness and Contradiction Rules

Freshness metadata is preserved as a requirement. Current-sensitive research
cannot proceed with unknown freshness. Contradiction metadata remains a
candidate requiring review and does not resolve conflicts automatically.

## Citation and Provenance Rules

Claimed source metadata requires source refs or provenance. Citation candidates
are not verifier success. Citation records are not created in this sprint.

## Cache and TTL Rules

`no_cache`, `session_cache_only`, and `source_ref_cache_only` are planning
labels only. `prohibited_cache` blocks cache provider proposals. Durable cache
is future-gated and public-query-only.

## Relationship to Context Policy

Context Policy cannot be contradicted. Web research metadata cannot route
private context externally or create context packages. Any future context
package requires a separate context policy and provider-routing boundary.

## Relationship to Identity Scope and Memory Governance

Private/project/user scoped metadata requires Identity Scope. Memory-derived
research context requires Memory Governance. Neither grants web execution.

## Relationship to Policy-as-Code Extension

Policy-as-code remains the backend policy boundary. Web research metadata cannot
override policy, grant permissions, or enable unsupported future phases.

## Relationship to Model Auto Mode and Local Model Inventory

Model Auto Mode and Local Model Inventory are readiness metadata only. They do
not authorize web queries, model synthesis, model calls, or routing.

## Relationship to Audit Query, Action Attribution, and System Drift

Audit Query, Action Attribution, and System Drift outputs are projections or
candidates. They are not verified truth and cannot authorize web search,
fetching, GitHub API calls, or synthesis.

## Relationship to Repo Audit and GitHub Source Future Work

Repo Audit readiness does not authorize GitHub API calls, repo fetches, or page
extraction. GitHub source connector work remains a future explicit sprint.

## Why Web Results Are Not Evidence or Truth

Web result, search snippet, citation, page extract, source metadata, and model
synthesis are not evidence, verifier success, policy truth, runtime truth, or
execution permission. Future web research must keep source facts, citations,
freshness, contradiction state, and model synthesis separate.

## Tests Added

`tests/test_core/test_web_research_gateway.py` covers:

- valid official docs, security advisory, source verification, and contradiction
  planning metadata
- missing required fields and unsupported taxonomy values
- private, sensitive, secret, credential, unknown, memory-derived, and scoped
  privacy boundaries
- source quality and freshness boundaries
- citation, cache, TTL, and contradiction handling
- denial of web/search/browser/API/fetch/scrape/model/tool/MCP behavior
- denial of cache/source/citation/report/artifact creation
- denial of external data transfer, private leakage, source truth, synthesis
  truth, evidence, verifier success, and grants
- unsafe related decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No web searches
- No browser automation
- No page fetches or HTTP requests
- No external API or GitHub API calls
- No scraping or page extraction
- No model/tool/MCP calls
- No memory or context retrieval
- No caching or source/citation records
- No reports or artifacts
- No runtime/API/frontend integration
- No evidence or verifier success
- No approval, lease, capability, or dispatch grant
- No runtime/journal/evidence/replay mutation

## Future Implementation Notes

A future implementation sprint must define:

- allowed query inputs after redaction
- provider allowlist and policy gates
- source quality scoring
- freshness checks
- contradiction handling
- citation storage boundaries
- cache TTL and invalidation rules
- no-private-data-exfiltration checks
- evidence expectations for fetch attempts
- verifier expectations for any claimed postcondition
- separation between source facts and synthesis

## Remaining Risks

- The contract validates supplied metadata only; it does not prove source
  freshness, availability, or quality.
- Future provider integration could leak private data if query redaction and
  policy checks are not enforced at runtime.
- Future synthesis can still overstate confidence unless source facts,
  uncertainty, and citations remain separate from model output.
