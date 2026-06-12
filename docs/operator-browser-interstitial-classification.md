# Operator Browser Interstitial Classification
## Decision

OPERATOR_INTERSTITIAL_CLASSIFICATION_WITH_TESTS

This sprint classifies known browser provider interstitials, starting with the
Google `/sorry/` bot-challenge page, as verifier blockers. It does not treat the
interstitial as success, does not bypass the provider challenge, and does not add
fallback execution.

## Scope

The classification is a browser-verifier evidence improvement only.

- `search_web` and `open_url` preserve requested and observed URL evidence.
- Google `/sorry` and `/sorry/...` paths are recognized only when the requested
  provider or requested host is Google and the observed host is the allowlisted
  Google host.
- Spoof hosts such as `www.google.com.evil.test` are ordinary verifier failures,
  not provider interstitials.
- The classifier is URL-structured and does not rely on broad text substring
  matching.

## Evidence Fields

Browser evidence now preserves:

- `classification_version=browser-provider-interstitial/1`
- `requested_url` and `requested_search_url`
- `observed_url` and `final_url`
- `search_provider`, `provider`, and `provider_domain`
- `query` and `observed_query`
- `provider_interstitial_detected`
- `provider_interstitial_type`
- `provider_interstitial_reason`
- `bot_challenge_detected`
- `blocked_by_bot_challenge`
- `search_verification_blocked_by_provider`
- `verification_blocker`
- `operator_message`
- `operator_suggestion`
- `fallback_available`
- `fallback_enabled`
- `fallback_attempted`
- `fallback_requires_operator_decision`
- `verified_success`
- failed verifier checks

For Google `/sorry/`, the expected classification is:

- `provider_interstitial_detected=true`
- `provider_interstitial_type=bot_challenge`
- `provider_interstitial_reason=google_sorry_bot_challenge`
- `bot_challenge_detected=true`
- `blocked_by_bot_challenge=true`
- `search_verification_blocked_by_provider=true`
- `verification_blocker=search_verification_blocked_by_provider`
- `verified_success=false`
- `fallback_enabled=false`
- `fallback_attempted=false`

## Operator Reporting

The browser verifier reports:

- `browser_verification_state=approval_required`
- `browser_verification_reason=search verification blocked by provider interstitial: google_sorry_bot_challenge`

The operator-facing suggestion is to retry later, use another configured
provider, or open manually. This is informational only. It does not grant
approval, does not continue through the challenge, and does not trigger fallback.

## Safety Invariants

- Provider interstitial detection is not URL verification success.
- Dispatch success is not verification success.
- Evidence presence is not verified success.
- Bot challenge evidence is not a timeout unless a backend timeout condition is
  independently present.
- Frontend display is not a source of truth.
- Fallback remains disabled by default.
- No click, CAPTCHA solving, vision, OCR, or browser challenge bypass was added.
- No journal, replay, schema, or protocol expansion was added.

## Validation

Focused tests cover:

- verified Google search evidence remains clean and fallback-disabled;
- Google `/sorry/` is classified as a provider bot-challenge interstitial;
- the same `/sorry/` path on a spoof host is not classified;
- spoof search and open-url hosts remain unverified;
- bot-challenge evidence alone is not a timeout without a backend deadline.

Full validation should include the executor/browser verifier tests, intent tests,
runtime threat-model regression tests, API command tests, `git diff --check`, and
full pytest when practical.

## Deferred

Future provider classification can add explicit, host-checked provider cases.
That work should remain verifier evidence only unless a later sprint explicitly
approves fallback or continuation policy.
