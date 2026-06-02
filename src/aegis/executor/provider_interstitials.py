from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


BROWSER_PROVIDER_INTERSTITIAL_CLASSIFICATION_VERSION = "browser-provider-interstitial/1"


@dataclass(frozen=True)
class ProviderInterstitialRule:
    provider: str
    allowed_hosts: tuple[str, ...]
    path_prefixes: tuple[str, ...]
    interstitial_type: str
    reason: str
    operator_message: str
    operator_suggestion: str
    fallback_allowed: bool = False


@dataclass(frozen=True)
class ProviderInterstitialClassification:
    detected: bool
    provider: str | None = None
    reason: str | None = None
    interstitial_type: str | None = None
    host_matched: bool = False
    spoof_rejected: bool = False
    operator_message: str | None = None
    suggestion: str | None = None
    fallback_allowed: bool = False
    fallback_attempted: bool = False
    verified_success: bool = False
    classification_version: str = BROWSER_PROVIDER_INTERSTITIAL_CLASSIFICATION_VERSION

    @property
    def blocked_by_bot_challenge(self) -> bool:
        return self.detected and self.interstitial_type == "bot_challenge"

    def to_evidence_fields(self) -> dict[str, object]:
        return {
            "classification_version": self.classification_version,
            "provider_interstitial_detected": self.detected,
            "provider_interstitial_provider": self.provider,
            "provider_interstitial_type": self.interstitial_type,
            "provider_interstitial_reason": self.reason,
            "provider_interstitial_host_matched": self.host_matched,
            "provider_interstitial_spoof_rejected": self.spoof_rejected,
            "blocked_by_bot_challenge": self.blocked_by_bot_challenge,
            "search_verification_blocked_by_provider": self.detected,
            "verification_blocker": "search_verification_blocked_by_provider" if self.detected else None,
            "operator_message": self.operator_message,
            "operator_suggestion": self.suggestion,
            "fallback_available": self.fallback_allowed,
            "fallback_enabled": False,
            "fallback_attempted": self.fallback_attempted,
            "fallback_requires_operator_decision": True,
        }


PROVIDER_INTERSTITIAL_RULES: tuple[ProviderInterstitialRule, ...] = (
    ProviderInterstitialRule(
        provider="google",
        allowed_hosts=("google.com", "www.google.com"),
        path_prefixes=("/sorry",),
        interstitial_type="bot_challenge",
        reason="google_sorry_bot_challenge",
        operator_message=(
            "Browser/search verification was blocked by a Google provider interstitial/bot challenge; "
            "Aegis did not bypass it or mark the search as verified."
        ),
        operator_suggestion="retry_later_or_use_another_configured_provider_or_open_manually",
        fallback_allowed=False,
    ),
)


def classify_provider_interstitial(
    observed_url: str,
    *,
    requested_provider: str | None = None,
    requested_url: str | None = None,
) -> ProviderInterstitialClassification:
    observed = _valid_browser_url(observed_url)
    if observed is None:
        return ProviderInterstitialClassification(detected=False)

    requested_host = ""
    if requested_url:
        requested = _valid_browser_url(requested_url)
        requested_host = _normalized_host(requested.hostname or "") if requested else ""

    provider = (requested_provider or "").lower().strip()
    observed_host = _normalized_host(observed.hostname or "")
    observed_path = _normalized_path(observed.path).lower()
    spoof_rejected = False

    for rule in PROVIDER_INTERSTITIAL_RULES:
        provider_expected = provider == rule.provider or requested_host in rule.allowed_hosts
        path_matched = any(_path_matches_prefix(observed_path, prefix) for prefix in rule.path_prefixes)
        host_matched = observed_host in rule.allowed_hosts
        spoof_rejected = spoof_rejected or bool(
            provider_expected
            and path_matched
            and not host_matched
            and _looks_like_spoof_host(observed_host, rule.allowed_hosts)
        )

        if provider_expected and host_matched and path_matched:
            return ProviderInterstitialClassification(
                detected=True,
                provider=rule.provider,
                reason=rule.reason,
                interstitial_type=rule.interstitial_type,
                host_matched=True,
                spoof_rejected=False,
                operator_message=rule.operator_message,
                suggestion=rule.operator_suggestion,
                fallback_allowed=rule.fallback_allowed,
                fallback_attempted=False,
                verified_success=False,
            )

    return ProviderInterstitialClassification(detected=False, spoof_rejected=spoof_rejected)


def _valid_browser_url(value: str):
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return parsed


def _normalized_host(value: str) -> str:
    return value.lower().strip(".")


def _normalized_path(value: str) -> str:
    normalized = value or "/"
    return "/" if normalized == "" else normalized.rstrip("/") or "/"


def _path_matches_prefix(path: str, prefix: str) -> bool:
    normalized_prefix = _normalized_path(prefix).lower()
    return path == normalized_prefix or path.startswith(f"{normalized_prefix}/")


def _looks_like_spoof_host(observed_host: str, allowed_hosts: tuple[str, ...]) -> bool:
    return any(observed_host.startswith(f"{allowed}.") for allowed in allowed_hosts)
