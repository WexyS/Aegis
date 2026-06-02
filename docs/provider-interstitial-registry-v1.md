# Provider Interstitial Registry v1

## Decision

PROVIDER_INTERSTITIAL_REGISTRY_WITH_TESTS

This sprint moves provider interstitial classification into a small pure helper
registry. The registry preserves the existing Google `/sorry` bot-challenge
classification while making future provider-specific rules explicit,
host-checked, and testable.

## Scope

The registry is verifier evidence only. It classifies known provider
interstitial URLs so browser evidence can explain why search or URL verification
was blocked. It does not bypass provider pages, solve challenges, click through
flows, or navigate to another provider.

## Why The Registry Exists

The previous implementation correctly classified Google `/sorry`, but the rule
lived inline in the executor. A small registry keeps the executor focused on
evidence construction and gives future provider additions a narrow checklist:
provider identity, exact host constraints, path constraints, reason, message,
fallback flags, and tests.

## Rule Requirements

Each provider rule must define:

- provider name;
- exact allowed hosts;
- exact path prefixes or exact paths;
- interstitial type;
- classification reason;
- operator message;
- operator suggestion;
- fallback allowed flag, default false;
- accepted URL tests;
- spoof URL tests;
- unrelated URL tests.

Rules must not use broad body-text or arbitrary substring matching. Host matching
must not accept provider-looking suffixes such as `www.google.com.evil.test`.

## Google Rule

The only active rule in this sprint is Google `/sorry`.

- Provider: `google`
- Allowed hosts: `google.com`, `www.google.com`
- Paths: `/sorry`, `/sorry/...`
- Type: `bot_challenge`
- Reason: `google_sorry_bot_challenge`
- Fallback allowed: false

Accepted examples:

- `https://www.google.com/sorry?...`
- `https://www.google.com/sorry/index?...`
- `https://google.com/sorry/index?...`

Rejected examples:

- `https://www.google.com/search?q=aegis+runtime`
- `https://www.google.com.evil.test/sorry/index?...`
- `https://unexpected.example/sorry/index`

## Spoof-Domain Rejection

The registry only marks spoof rejection for provider-host impersonation, such as
`www.google.com.evil.test`. Generic mismatches remain generic verifier failures
and are not mislabeled as provider interstitials.

## Fallback

Fallback remains disabled by default:

- `fallback_available=false`
- `fallback_enabled=false`
- `fallback_attempted=false`
- no automatic fallback navigation
- no original provider challenge rewritten as success

Any future fallback policy must be approved as a separate runtime policy sprint.

## Evidence And Verifier Relationship

Provider interstitial classification feeds browser evidence fields such as:

- `provider_interstitial_detected`
- `provider_interstitial_provider`
- `provider_interstitial_type`
- `provider_interstitial_reason`
- `provider_interstitial_host_matched`
- `provider_interstitial_spoof_rejected`
- `blocked_by_bot_challenge`
- `search_verification_blocked_by_provider`
- `verification_blocker`
- `operator_message`
- `operator_suggestion`
- fallback flags
- `verified_success=false`

The browser URL verifier remains the source of truth for verified success.
Provider interstitial classification can explain a failed verifier check, but it
cannot turn dispatch success or evidence presence into verified success.

## Tests Added

Tests cover:

- Google `/sorry` classification;
- Google `/sorry/...` classification;
- `google.com` and `www.google.com` allowlisted hosts;
- spoof host rejection;
- unrelated Google path rejection;
- generic mismatch not mislabeled as interstitial;
- fallback disabled and unattempted;
- provider interstitial evidence remains `verified_success=false`;
- browser URL verification remains strict;
- bot challenge evidence does not become timeout without a backend timeout.

## Intentionally Not Done

- CAPTCHA or challenge solving
- challenge bypass
- browser click, desktop click, or generic click
- provider fallback execution
- URL verifier weakening
- schema or protocol expansion
- frontend authority
- journal, replay, or historical evidence mutation
- model, API, MCP, memory, plugin, or external provider calls

## Future Provider Additions

Future provider rules should be added only when exact host and path constraints
are known and covered by tests. Speculative provider rules should remain out of
the registry until they can be represented without broad matching or bypass
behavior.

## Remaining Risks

Only Google `/sorry` is covered. Other providers may present consent, login,
rate-limit, or bot-challenge pages that still appear as ordinary unverified
browser outcomes until a host-checked rule is added.
