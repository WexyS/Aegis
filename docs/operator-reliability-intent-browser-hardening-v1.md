# Operator Reliability Intent Browser Hardening v1

## Decision

OPERATOR_RELIABILITY_INTENT_BROWSER_HARDENING_WITH_TESTS

This sprint hardened intent routing, app target safety, browser URL verification,
browser lifecycle failure handling, and failed-dispatch evidence. It did not add
new execution capabilities, click controls, cleanup execution, or frontend truth.

## Root Cause Summary

- Browser-search phrases such as `brave aç python nedir diye arat` could be
  partially interpreted as app launch or lose the search query.
- Google could be ambiguous between a site/search provider and a browser
  application.
- Known site phrases such as `githuba gir` did not consistently become
  `open_url`.
- Unknown app phrases could reach `open_app` without a strict final guard.
- Browser URL verification allowed broad host suffix matching for Google search
  evidence.
- Closed browser/page/context failures were not represented as a bounded
  recovery attempt with preserved failure details.

## Fixed Routing Contract

Search-oriented browser commands now route to `search_web` with
`metadata.route_kind=browser_search`.

Required examples:

| Input | Intent | Key fields |
| --- | --- | --- |
| `brave aç python nedir diye arat` | `search_web` | `query=python nedir`, `preferred_browser=brave`, `search_provider=google` |
| `google açıp github yaz` | `search_web` | `query=github`, `search_provider=google` |
| `githuba gir` | `open_url` | `url=https://github.com`, `site=github` |
| `python nedir diye arat` | `search_web` | `query=python nedir`; no app target |

Google is treated as a site/search provider unless the user explicitly asks for
Chrome or default-browser detection reports Chrome. Browser preference is
metadata only. The runtime still uses the controlled browser and labels that as
`browser_runtime=controlled_browser`.

## App Target Safety

- Arbitrary free text does not become a safe executable target.
- Unknown app aliases carry `_app_known=false` and are blocked by `ActionGuard`.
- Search phrases are not promoted to local app targets.
- Mixed destructive commands such as `notepad aç sonra dosya sil` are blocked
  before partial open-app execution.
- No broad shell execution path was added.

## Browser Verification Contract

- Exact URL and trailing-slash canonicalization pass.
- Safe `http` to `https` upgrade passes.
- Safe `www` and non-`www` equivalence is allowlisted for Google and GitHub.
- Spoof hosts such as `google.com.evil.test` and `github.com.evil.test` fail.
- Dispatch completion is not URL verification.
- Unrelated redirects remain unverified.

## Browser Lifecycle Contract

Closed page/context/browser failures trigger at most one bounded recovery
attempt. Recovery success still goes through normal browser URL verification.
Recovery failure emits negative execution evidence with original failure details
preserved. No infinite retry loop is allowed.

## Evidence Contract

- Failed browser dispatch records `executor-negative-evidence/1`.
- Unverified URL/search outcomes remain unverified.
- Verified browser success requires browser URL/search verifier checks.
- Negative evidence is failed evidence, not verified success.
- No fake process, window, browser, URL, health, or historical cleanup evidence
  is introduced.

## Validation Scope

Focused tests cover:

- Turkish app launch commands.
- Turkish browser/search commands.
- English app/browser/search equivalents.
- Mocked default browser as Brave.
- Google as search provider/site, not browser app.
- URL canonicalization and spoof rejection.
- Closed browser context recovery and negative evidence.
- Arbitrary text and unknown app targets not becoming executable.
- Command lifecycle preservation of browser negative evidence.

## Deferred

Live OS smoke was not made part of this document because opening Notepad and
browsers is intentionally side-effecting. If an operator chooses to run live
smoke later, the result should record normalized intent, dispatched action,
evidence status, verifier status, final URL/app/window evidence, and failure
reason.
