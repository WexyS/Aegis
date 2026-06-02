# src/aegis/executor/deterministic_executor.py

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from urllib.parse import parse_qs, quote_plus, urlparse

from aegis.core.context import ExecutionContext
from aegis.core.schemas import IntentResult, ActionResult, ExecutionEvidence, ReliabilityMetrics
from aegis.core.constants import ActionStatus
from aegis.core.commands import CancellationToken
from aegis.logger.event_logger import get_event_logger, EventType
from aegis.core.state_manager import get_state_manager
from aegis.core.transition_model import get_transition_model
from aegis.tools.registry import TOOLS, get_tool_spec
from aegis.tools.file_tools import _resolve_read_path, _resolve_write_path
from aegis.executor.utils import verify_path
from aegis.executor.desktop_verifier import (
    DesktopVerificationResult,
    now_ms,
    verification_to_execution_evidence,
    verify_desktop_action,
)

logger = logging.getLogger(__name__)


def _normalized_url(value: str) -> str:
    return value.rstrip("/")


def _valid_browser_url(value: str) -> Any | None:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return parsed


SAFE_HOST_EQUIVALENTS = {
    frozenset({"google.com", "www.google.com"}),
    frozenset({"github.com", "www.github.com"}),
}

SAFE_DYNAMIC_QUERY_PARAMS = {
    ("google.com", "/"): {"zx"},
    ("www.google.com", "/"): {"zx"},
}


def _equivalent_browser_hosts(requested_host: str, observed_host: str) -> bool:
    requested = requested_host.lower().strip(".")
    observed = observed_host.lower().strip(".")
    if requested == observed:
        return True
    return frozenset({requested, observed}) in SAFE_HOST_EQUIVALENTS


def _same_or_safe_upgraded_scheme(requested_scheme: str, observed_scheme: str) -> bool:
    requested = requested_scheme.lower()
    observed = observed_scheme.lower()
    return requested == observed or requested == "http" and observed == "https"


def _normalized_browser_path(path: str) -> str:
    normalized = path or "/"
    return "/" if normalized == "" else normalized.rstrip("/") or "/"


def _browser_query_matches_or_safe_dynamic(requested: Any, observed: Any) -> bool:
    if requested.query == observed.query:
        return True
    if requested.query:
        return False
    observed_query = parse_qs(observed.query, keep_blank_values=True)
    if not observed_query:
        return True
    observed_host = (observed.hostname or "").lower().strip(".")
    observed_path = _normalized_browser_path(observed.path)
    allowed_params = SAFE_DYNAMIC_QUERY_PARAMS.get((observed_host, observed_path))
    if not allowed_params:
        return False
    return set(observed_query).issubset(allowed_params) and all(
        len(values) == 1 and bool(values[0])
        for values in observed_query.values()
    )


def _browser_url_mismatch_reason(requested_url: str, observed_url: str) -> str | None:
    requested = _valid_browser_url(requested_url)
    observed = _valid_browser_url(observed_url)
    if not requested:
        return "requested_url_invalid"
    if not observed:
        return "observed_url_invalid"
    if not _same_or_safe_upgraded_scheme(requested.scheme, observed.scheme):
        return "scheme_mismatch"
    if not _equivalent_browser_hosts(requested.hostname or "", observed.hostname or ""):
        return "host_mismatch"
    if _normalized_browser_path(requested.path) != _normalized_browser_path(observed.path):
        return "path_mismatch"
    if not _browser_query_matches_or_safe_dynamic(requested, observed):
        return "query_mismatch"
    return None


def _same_browser_url(requested_url: str, observed_url: str) -> bool:
    return _browser_url_mismatch_reason(requested_url, observed_url) is None


def _google_search_query(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if not _equivalent_browser_hosts("www.google.com", host) or parsed.path != "/search":
        return ""
    return str(parse_qs(parsed.query).get("q", [""])[0]).strip()


BROWSER_PROVIDER_INTERSTITIAL_CLASSIFICATION_VERSION = "browser-provider-interstitial/1"


def _provider_interstitial_absent() -> dict[str, Any]:
    return {
        "classification_version": BROWSER_PROVIDER_INTERSTITIAL_CLASSIFICATION_VERSION,
        "provider_interstitial_detected": False,
        "provider_interstitial_type": None,
        "provider_interstitial_reason": None,
        "blocked_by_bot_challenge": False,
        "search_verification_blocked_by_provider": False,
        "verification_blocker": None,
        "operator_message": None,
        "operator_suggestion": None,
        "fallback_available": False,
        "fallback_enabled": False,
        "fallback_attempted": False,
        "fallback_requires_operator_decision": True,
    }


def _browser_provider_interstitial(
    *,
    requested_provider: str,
    requested_url: str,
    observed_url: str,
) -> dict[str, Any]:
    requested = _valid_browser_url(requested_url)
    observed = _valid_browser_url(observed_url)
    if not requested or not observed:
        return _provider_interstitial_absent()

    requested_host = requested.hostname or ""
    observed_host = observed.hostname or ""
    provider = requested_provider.lower().strip()
    expected_google = provider == "google" or _equivalent_browser_hosts("www.google.com", requested_host)
    observed_google = _equivalent_browser_hosts("www.google.com", observed_host)
    observed_path = _normalized_browser_path(observed.path).lower()
    google_sorry_path = observed_path == "/sorry" or observed_path.startswith("/sorry/")

    if expected_google and observed_google and google_sorry_path:
        return {
            "classification_version": BROWSER_PROVIDER_INTERSTITIAL_CLASSIFICATION_VERSION,
            "provider_interstitial_detected": True,
            "provider_interstitial_type": "bot_challenge",
            "provider_interstitial_reason": "google_sorry_bot_challenge",
            "blocked_by_bot_challenge": True,
            "search_verification_blocked_by_provider": True,
            "verification_blocker": "search_verification_blocked_by_provider",
            "operator_message": (
                "Browser/search verification was blocked by a Google provider interstitial/bot challenge; "
                "Aegis did not bypass it or mark the search as verified."
            ),
            "operator_suggestion": (
                "retry_later_or_use_another_configured_provider_or_open_manually"
            ),
            "fallback_available": False,
            "fallback_enabled": False,
            "fallback_attempted": False,
            "fallback_requires_operator_decision": True,
        }

    return _provider_interstitial_absent()


def _is_browser_lifecycle_failure(value: str) -> bool:
    lowered = value.lower()
    markers = (
        "target page, context or browser has been closed",
        "page has been closed",
        "context has been closed",
        "browser has been closed",
        "target closed",
    )
    return any(marker in lowered for marker in markers)


def _read_only_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent not in {"read_file", "read_page", "search_web", "list_directory", "search_files", "grep_in_files", "file_info"}:
        return None
    encoded = output_text.encode("utf-8")
    evidence: Dict[str, Any] = {
        "tool": intent,
        "bytes": len(encoded),
        "byte_count": len(encoded),
        "chars": len(output_text),
        "char_count": len(output_text),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "truncated": intent == "read_page" and output_text.endswith("..."),
    }
    if intent in {"read_file", "list_directory", "search_files", "grep_in_files", "file_info"}:
        evidence["path"] = str(params.get("path", ""))
    if intent == "read_file":
        resolved = _resolve_read_path(str(params.get("path", "")))
        file_exists = resolved.exists()
        is_file = resolved.is_file() if file_exists else False
        disk_sha256 = None
        read_error = None
        if is_file:
            try:
                disk_sha256 = _sha256_text(resolved.read_text(encoding="utf-8"))
            except Exception as exc:
                read_error = str(exc)
        content_hash_captured = disk_sha256 is not None
        count_captured = evidence["byte_count"] is not None or evidence["char_count"] is not None
        dispatch_ok = True
        content_hash_matches_disk = bool(disk_sha256 and disk_sha256 == evidence["sha256"])
        checks = [
            _evidence_check(
                "read_file_exists",
                file_exists,
                True,
                file_exists,
                "read_file is verified only when the resolved source file still exists.",
            ),
            _evidence_check(
                "read_path_is_file",
                is_file,
                True,
                is_file,
                "read_file is verified only when the resolved source path is a file.",
            ),
            _evidence_check(
                "read_dispatch_ok",
                dispatch_ok,
                True,
                dispatch_ok,
                "read_file is verified only when dispatch completed without raising.",
            ),
            _evidence_check(
                "read_content_hash_captured",
                content_hash_captured,
                True,
                content_hash_captured,
                "read_file is verified only when a disk content hash is captured.",
            ),
            _evidence_check(
                "read_count_captured",
                count_captured,
                "byte_count or char_count",
                {
                    "byte_count": evidence["byte_count"],
                    "char_count": evidence["char_count"],
                },
                "read_file is verified only when byte or character count evidence is captured.",
            ),
            _evidence_check(
                "read_content_hash_matches_disk",
                content_hash_matches_disk,
                evidence["sha256"],
                disk_sha256,
                "read_file output hash must match the resolved file content hash.",
            ),
        ]
        critical_passed = bool(
            file_exists
            and is_file
            and dispatch_ok
            and content_hash_captured
            and count_captured
            and content_hash_matches_disk
        )
        failed_checks = [str(check["check_name"]) for check in checks if check["passed"] is False]
        evidence.update({
            "resolved_path": str(resolved),
            "file_exists": file_exists,
            "is_file": is_file,
            "disk_sha256": disk_sha256,
            "content_hash_captured": content_hash_captured,
            "count_captured": count_captured,
            "dispatch_ok": dispatch_ok,
            "content_hash_matches_disk": content_hash_matches_disk,
            "read_error": read_error,
            "read_verification_state": "verified" if critical_passed else "unverified",
            "read_verification_reason": "read file evidence matched disk" if critical_passed else f"read file verification failed: {', '.join(failed_checks)}",
            "verification_checks": checks,
        })
    if intent in {"search_files", "grep_in_files"}:
        evidence["query"] = str(params.get("query") or params.get("pattern") or "")
    if intent == "search_web":
        query = str(params.get("query", "")).strip()
        evidence["query"] = query
        evidence["search_url"] = f"https://www.google.com/search?q={quote_plus(query)}"
    return evidence


async def _capture_click_context(intent: str, params: Dict[str, Any], page: Any | None) -> Dict[str, Any] | None:
    if intent != "click" or page is None:
        return None

    selector = params.get("selector")
    x = params.get("x")
    y = params.get("y")
    context: Dict[str, Any] = {
        "url": str(getattr(page, "url", "")),
        "selector": str(selector) if selector else None,
        "target": None,
    }
    if x is not None and y is not None:
        context["coordinates"] = {"x": int(x), "y": int(y)}

    try:
        if selector:
            context["target"] = await page.evaluate(
                """
                (selector) => {
                  const el = document.querySelector(selector);
                  if (!el) return null;
                  const rect = el.getBoundingClientRect();
                  return {
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                  };
                }
                """,
                selector,
            )
        elif x is not None and y is not None:
            context["target"] = await page.evaluate(
                """
                ({x, y}) => {
                  const el = document.elementFromPoint(x, y);
                  if (!el) return null;
                  const rect = el.getBoundingClientRect();
                  return {
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                  };
                }
                """,
                {"x": int(x), "y": int(y)},
            )
    except Exception as exc:
        context["capture_error"] = str(exc)

    return context


def _browser_evidence(
    intent: str,
    params: Dict[str, Any],
    output_text: str,
    *,
    observed_url: str | None = None,
    click_before: Dict[str, Any] | None = None,
    click_after: Dict[str, Any] | None = None,
    recovery_attempts: list[dict[str, Any]] | None = None,
) -> Dict[str, Any] | None:
    if intent not in {"open_url", "search_web", "scroll"}:
        if intent != "click":
            return None
    evidence: Dict[str, Any] = {"tool": intent}
    recovery_attempt_list = list(recovery_attempts or [])
    recovery_fields = {
        "browser_recovery_attempted": bool(recovery_attempt_list),
        "browser_recovery_attempt_count": len(recovery_attempt_list),
        "browser_recovery_attempts": recovery_attempt_list,
    }
    if intent == "open_url":
        requested_url = str(params.get("url", ""))
        observed = str(observed_url or "")
        requested_url_valid = _valid_browser_url(requested_url) is not None
        browser_context_observable = bool(observed)
        final_url_captured = bool(observed)
        mismatch_reason = _browser_url_mismatch_reason(requested_url, observed)
        url_matches = mismatch_reason is None
        dispatch_ok = True
        interstitial = _browser_provider_interstitial(
            requested_provider=str(params.get("search_provider") or ""),
            requested_url=requested_url,
            observed_url=observed,
        )
        challenge = bool(interstitial["blocked_by_bot_challenge"])
        checks = [
            _evidence_check(
                "browser_requested_url_valid",
                requested_url_valid,
                "absolute http(s) URL",
                requested_url,
                "open_url is verified only when the requested URL is a valid browser URL.",
            ),
            _evidence_check(
                "browser_observed_url_present",
                browser_context_observable,
                "browser URL after navigation",
                observed,
                "Browser navigation is verified only when the controlled page reports an observed URL.",
            ),
            _evidence_check(
                "browser_final_url_captured",
                final_url_captured,
                True,
                final_url_captured,
                "open_url is verified only when the final browser URL is captured.",
            ),
            _evidence_check(
                "browser_url_matches_request",
                url_matches,
                requested_url,
                observed,
                "open_url is verified only when the observed URL matches the requested URL.",
            ),
            _evidence_check(
                "browser_dispatch_ok",
                dispatch_ok,
                True,
                dispatch_ok,
                "open_url is verified only when browser dispatch completed without raising.",
            ),
            _evidence_check(
                "browser_no_bot_challenge",
                not challenge,
                False,
                {
                    "bot_challenge_detected": challenge,
                    "provider_interstitial_reason": interstitial["provider_interstitial_reason"],
                },
                "Provider bot-challenge/interstitial pages require operator review instead of automatic success.",
            ),
            _evidence_check(
                "browser_no_provider_interstitial",
                not interstitial["provider_interstitial_detected"],
                False,
                interstitial["provider_interstitial_detected"],
                "Provider interstitial pages block browser URL verification until a future explicit policy supports continuation.",
            ),
        ]
        verified = bool(
            requested_url_valid
            and browser_context_observable
            and final_url_captured
            and url_matches
            and dispatch_ok
            and not challenge
        )
        state = "approval_required" if challenge else "verified" if verified else "unverified"
        failed_checks = [str(check["check_name"]) for check in checks if check["passed"] is False]
        verification_reason = (
            "browser URL matched request"
            if state == "verified"
            else (
                f"browser verification blocked by provider interstitial: {interstitial['provider_interstitial_reason']}"
                if interstitial["provider_interstitial_detected"]
                else f"browser URL verification failed: {', '.join(failed_checks)}"
            )
        )
        evidence.update({
            "url": requested_url,
            "requested_url": requested_url,
            "requested_url_valid": requested_url_valid,
            "observed_url": observed,
            "final_url": observed,
            "preferred_browser": params.get("preferred_browser"),
            "browser_runtime": params.get("browser_runtime") or "controlled_browser",
            "controlled_browser": bool(params.get("controlled_browser", True)),
            "browser_preference_is_verification": False,
            **recovery_fields,
            "browser_context_observable": browser_context_observable,
            "final_url_captured": final_url_captured,
            "url_matches_request": url_matches,
            "url_mismatch_reason": mismatch_reason,
            "dispatch_ok": dispatch_ok,
            "bot_challenge_detected": challenge,
            "verified_success": verified,
            **interstitial,
            "browser_verification_state": state,
            "browser_verification_reason": verification_reason,
            "verification_checks": checks,
        })
    if intent == "search_web":
        query = str(params.get("query", "")).strip()
        requested_url = f"https://www.google.com/search?q={quote_plus(query)}"
        observed = str(observed_url or "")
        observed_parsed = _valid_browser_url(observed)
        provider_domain = ((observed_parsed.hostname or "").lower() if observed_parsed else "")
        provider = "google" if _equivalent_browser_hosts("www.google.com", provider_domain) else ""
        browser_context_observable = bool(observed)
        final_url_captured = bool(observed)
        query_present = bool(query)
        observed_query = _google_search_query(observed)
        query_matches = bool(observed_query and observed_query == query)
        provider_matches = provider == "google"
        dispatch_ok = True
        requested_provider = str(params.get("search_provider") or "google")
        interstitial = _browser_provider_interstitial(
            requested_provider=requested_provider,
            requested_url=requested_url,
            observed_url=observed,
        )
        challenge = bool(interstitial["blocked_by_bot_challenge"])
        checks = [
            _evidence_check(
                "search_query_present",
                query_present,
                "non-empty search query",
                query,
                "search_web is verified only when the requested query is non-empty.",
            ),
            _evidence_check(
                "browser_observed_url_present",
                browser_context_observable,
                "browser URL after search navigation",
                observed,
                "search_web is verified only when the controlled page reports an observed URL.",
            ),
            _evidence_check(
                "browser_final_url_captured",
                final_url_captured,
                True,
                final_url_captured,
                "search_web is verified only when the final browser URL is captured.",
            ),
            _evidence_check(
                "search_provider_matches_expected",
                provider_matches,
                "google",
                provider or provider_domain,
                "search_web is verified only when the observed URL belongs to the deterministic search provider.",
            ),
            _evidence_check(
                "search_query_matches_observed_url",
                query_matches,
                query,
                observed_query,
                "search_web is verified only when the observed search URL carries the requested query.",
            ),
            _evidence_check(
                "browser_dispatch_ok",
                dispatch_ok,
                True,
                dispatch_ok,
                "search_web is verified only when browser dispatch completed without raising.",
            ),
            _evidence_check(
                "browser_no_bot_challenge",
                not challenge,
                False,
                {
                    "bot_challenge_detected": challenge,
                    "provider_interstitial_reason": interstitial["provider_interstitial_reason"],
                },
                "Provider bot-challenge/interstitial pages require operator review instead of automatic success.",
            ),
            _evidence_check(
                "browser_no_provider_interstitial",
                not interstitial["provider_interstitial_detected"],
                False,
                interstitial["provider_interstitial_detected"],
                "Provider interstitial pages block search verification until a future explicit policy supports continuation.",
            ),
        ]
        verified = bool(
            query_present
            and browser_context_observable
            and final_url_captured
            and provider_matches
            and query_matches
            and dispatch_ok
            and not challenge
        )
        state = "approval_required" if challenge else "verified" if verified else "unverified"
        failed_checks = [str(check["check_name"]) for check in checks if check["passed"] is False]
        verification_reason = (
            "search query matched observed URL"
            if state == "verified"
            else (
                f"search verification blocked by provider interstitial: {interstitial['provider_interstitial_reason']}"
                if interstitial["provider_interstitial_detected"]
                else f"search URL verification failed: {', '.join(failed_checks)}"
            )
        )
        evidence.update({
            "query": query,
            "requested_url": requested_url,
            "requested_search_url": requested_url,
            "observed_url": observed,
            "final_url": observed,
            "provider": provider,
            "provider_domain": provider_domain,
            "search_provider": requested_provider,
            "preferred_browser": params.get("preferred_browser"),
            "browser_runtime": params.get("browser_runtime") or "controlled_browser",
            "controlled_browser": bool(params.get("controlled_browser", True)),
            "browser_preference_is_verification": False,
            **recovery_fields,
            "browser_context_observable": browser_context_observable,
            "final_url_captured": final_url_captured,
            "observed_query": observed_query,
            "query_present": query_present,
            "provider_matches_expected": provider_matches,
            "query_matches_observed_url": query_matches,
            "dispatch_ok": dispatch_ok,
            "bot_challenge_detected": challenge,
            "verified_success": verified,
            **interstitial,
            "browser_verification_state": state,
            "browser_verification_reason": verification_reason,
            "verification_checks": checks,
        })
    if intent == "scroll":
        evidence["direction"] = str(params.get("direction", "down"))
        evidence["amount"] = int(params.get("amount", 500) or 500)
    if intent == "click":
        selector = params.get("selector")
        x = params.get("x")
        y = params.get("y")
        if selector:
            evidence["selector"] = str(selector)
        if x is not None and y is not None:
            evidence["coordinates"] = {"x": int(x), "y": int(y)}
        evidence["before"] = click_before
        evidence["after"] = click_after
    evidence["output_sha256"] = hashlib.sha256(output_text.encode("utf-8")).hexdigest()
    return evidence


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _capture_write_before(intent: str, params: Dict[str, Any]) -> Dict[str, Any] | None:
    if intent not in {"write_file", "create_file", "edit_file"}:
        return None
    raw_path = params.get("path")
    if not raw_path:
        return None

    path = Path(_resolve_write_path(str(raw_path)))
    existed = path.exists()
    content = path.read_text(encoding="utf-8") if existed else ""
    return {
        "path": str(path),
        "existed_before": existed,
        "content": content,
        "bytes": len(content.encode("utf-8")),
        "sha256": _sha256_text(content) if existed else None,
    }


def _write_evidence(
    intent: str,
    params: Dict[str, Any],
    before: Dict[str, Any] | None,
    output_text: str,
) -> Dict[str, Any] | None:
    if intent not in {"write_file", "create_file", "edit_file"} or before is None:
        return None

    path = Path(before["path"])
    intended_path = Path(_resolve_write_path(str(params.get("path", ""))))
    existed_after = path.exists()
    after_content = path.read_text(encoding="utf-8") if existed_after else ""
    after_sha256 = _sha256_text(after_content) if existed_after else None
    expected_after_sha256 = None
    write_confirmed = False
    path_unchanged = str(path) == str(intended_path)
    before_state_known = (
        (bool(before["existed_before"]) and before["sha256"] is not None)
        or before["existed_before"] is False
    )
    dispatch_ok = True
    verification_checks: list[dict[str, Any]] = []
    verification_state = "verified"
    verification_reason = "write evidence captured"

    if intent == "write_file":
        expected_content = str(params.get("content", ""))
        expected_after_sha256 = _sha256_text(expected_content)
        after_hash_captured = after_sha256 is not None
        write_confirmed = bool(existed_after and after_sha256 == expected_after_sha256)
        verification_checks = [
            _evidence_check(
                "write_path_unchanged",
                path_unchanged,
                str(intended_path),
                str(path),
                "write_file is verified only when the resolved path remains unchanged.",
            ),
            _evidence_check(
                "write_before_state_known",
                before_state_known,
                "existing file hash or existed_before=false",
                {
                    "existed_before": bool(before["existed_before"]),
                    "before_sha256_captured": before["sha256"] is not None,
                },
                "write_file is verified only when the pre-write state is known.",
            ),
            _evidence_check(
                "write_file_exists_after",
                existed_after,
                True,
                existed_after,
                "write_file is verified only when the target file exists after dispatch.",
            ),
            _evidence_check(
                "write_after_hash_captured",
                after_hash_captured,
                True,
                after_hash_captured,
                "write_file is verified only when the post-write content hash is captured.",
            ),
            _evidence_check(
                "write_content_hash_matches_expected",
                write_confirmed,
                expected_after_sha256,
                after_sha256,
                "write_file is verified only when the after-content hash matches the requested content.",
            ),
            _evidence_check(
                "write_dispatch_ok",
                dispatch_ok,
                True,
                dispatch_ok,
                "write_file is verified only when dispatch completed without raising.",
            ),
        ]
        verification_state = (
            "verified"
            if path_unchanged
            and before_state_known
            and existed_after
            and after_hash_captured
            and write_confirmed
            and dispatch_ok
            else "unverified"
        )
        failed_checks = [str(check["check_name"]) for check in verification_checks if check["passed"] is False]
        verification_reason = "write file evidence matched requested content" if verification_state == "verified" else f"write file verification failed: {', '.join(failed_checks)}"

    return {
        "tool": intent,
        "path": str(path),
        "intended_path": str(intended_path),
        "dry_run": bool(params.get("dry_run", False)),
        "existed_before": bool(before["existed_before"]),
        "existed_after": existed_after,
        "before_state_known": before_state_known,
        "before_bytes": int(before["bytes"]),
        "after_bytes": len(after_content.encode("utf-8")),
        "before_sha256": before["sha256"],
        "after_sha256": after_sha256,
        "expected_after_sha256": expected_after_sha256,
        "path_unchanged": path_unchanged,
        "dispatch_ok": dispatch_ok,
        "write_confirmed": write_confirmed,
        "write_verification_state": verification_state,
        "write_verification_reason": verification_reason,
        "verification_checks": verification_checks,
        "output_sha256": _sha256_text(output_text),
    }


def _target_snapshot(state: Any) -> Dict[str, Any]:
    return {
        "active_app": getattr(state, "active_app", None),
        "pid": getattr(state, "pid", None),
        "hwnd": getattr(state, "hwnd", None),
        "focus_stable": bool(getattr(state, "focus_stable", False)),
        "is_responsive": bool(getattr(state, "is_responsive", False)),
    }


def _type_evidence(
    intent: str,
    params: Dict[str, Any],
    before_state: Any,
    after_state: Any,
    output_text: str,
) -> Dict[str, Any] | None:
    if intent != "type":
        return None
    text = str(params.get("text", ""))
    expected_focus = params.get("_require_focus")
    before = _target_snapshot(before_state)
    after = _target_snapshot(after_state)
    before_hwnd = before.get("hwnd")
    after_hwnd = after.get("hwnd")
    focus_verified_before = bool(before_hwnd and before.get("focus_stable"))
    focus_verified_after = bool(after_hwnd and after.get("focus_stable"))
    focus_did_not_change_unexpectedly = bool(before_hwnd and after_hwnd and before_hwnd == after_hwnd)
    dispatch_ok = True
    checks = [
        _evidence_check(
            "before_hwnd_present",
            bool(before_hwnd),
            "active HWND before typing",
            before_hwnd,
            "TypeTool must observe a focused HWND before sending keyboard input.",
        ),
        _evidence_check(
            "after_hwnd_present",
            bool(after_hwnd),
            "active HWND after typing",
            after_hwnd,
            "TypeTool must observe a focused HWND after sending keyboard input.",
        ),
        _evidence_check(
            "focus_did_not_change_unexpectedly",
            focus_did_not_change_unexpectedly,
            before_hwnd,
            after_hwnd,
            "TypeTool must not silently type into a different HWND than the one observed before execution.",
        ),
        _evidence_check(
            "focus_verified_before",
            focus_verified_before,
            True,
            before.get("focus_stable"),
            "TypeTool requires stable focus before sending keyboard input.",
        ),
        _evidence_check(
            "focus_verified_after",
            focus_verified_after,
            True,
            after.get("focus_stable"),
            "Post-type focus stability is recorded as confidence evidence.",
        ),
        _evidence_check(
            "dispatch_ok",
            dispatch_ok,
            True,
            dispatch_ok,
            "TypeTool dispatch must complete without raising before focus evidence can be verified.",
        ),
    ]
    critical_passed = bool(before_hwnd and after_hwnd and before_hwnd == after_hwnd and focus_verified_before and dispatch_ok)
    if critical_passed:
        verification_reason = "critical focus evidence passed"
    elif before_hwnd and after_hwnd and before_hwnd != after_hwnd:
        verification_reason = "focus changed unexpectedly during type action"
    else:
        failed_checks = [str(check["check_name"]) for check in checks[:4] if check["passed"] is False]
        verification_reason = f"type focus verification failed: {', '.join(failed_checks)}"
    return {
        "tool": intent,
        "text_chars": len(text),
        "text_bytes": len(text.encode("utf-8")),
        "text_sha256": _sha256_text(text),
        "expected_focus": expected_focus,
        "expected_focus_process_name": params.get("_require_focus_process_name"),
        "expected_focus_keywords": list(params.get("_require_focus_keywords") or []),
        "target_before": before,
        "target_after": after,
        "focus_verified_before": focus_verified_before,
        "focus_verified_after": focus_verified_after,
        "focus_did_not_change_unexpectedly": focus_did_not_change_unexpectedly,
        "dispatch_ok": dispatch_ok,
        "type_verification_state": "verified" if critical_passed else "unverified",
        "type_verification_reason": verification_reason,
        "verification_checks": checks,
        "output_sha256": _sha256_text(output_text),
    }


def _git_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent != "git_action":
        return None
    git_cmd = str(params.get("git_cmd", "")).lower().strip()
    return {
        "tool": intent,
        "git_cmd": git_cmd,
        "read_only": git_cmd == "status",
        "output_bytes": len(output_text.encode("utf-8")),
        "output_sha256": _sha256_text(output_text),
    }


def _shell_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent != "run_command":
        return None
    return {
        "tool": intent,
        "command": str(params.get("command", "")),
        "read_only": True,
        "output_bytes": len(output_text.encode("utf-8")),
        "output_sha256": _sha256_text(output_text),
    }


DESKTOP_EVIDENCE_TOOLS = {"open_app", "focus_app", "close_app"}
PROOF_EVIDENCE_KEYS = ("read_only_evidence", "browser_evidence", "write_evidence", "type_evidence", "git_evidence", "shell_evidence")
FILE_EVIDENCE_TOOLS = {"read_file", "write_file", "create_file", "edit_file", "delete_file", "move_file"}
BROWSER_EVIDENCE_TOOLS = {"open_url", "search_web", "scroll", "read_page"}


def _close_evidence_updates(close_attempts: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not close_attempts:
        return {}
    extra_checks: list[dict[str, Any]] = []
    fallback_chain = [
        {
            "method": "kill_after_graceful_timeout",
            "process_name": attempt.get("process_name"),
            "pids": list(attempt.get("kill_sent_pids") or []),
            "reason": "graceful terminate timeout",
        }
        for attempt in close_attempts
        if attempt.get("kill_sent_pids")
    ]
    for attempt in close_attempts:
        initial = set(int(pid) for pid in attempt.get("initial_pids") or [])
        graceful = set(int(pid) for pid in attempt.get("graceful_terminated_pids") or [])
        killed = set(int(pid) for pid in attempt.get("killed_pids") or [])
        remaining = set(int(pid) for pid in attempt.get("remaining_pids") or [])
        accounted = initial <= (graceful | killed | remaining)
        extra_checks.append(_evidence_check(
            "close_initial_pids_accounted_for",
            accounted if initial else True,
            sorted(initial),
            {
                "graceful_terminated_pids": sorted(graceful),
                "killed_pids": sorted(killed),
                "remaining_pids": sorted(remaining),
            },
            "Every initially matched PID should be observed as gracefully terminated, killed, or still remaining.",
        ))
        extra_checks.append(_evidence_check(
            "close_no_remaining_after_fallback",
            not remaining,
            [],
            sorted(remaining),
            "Close fallback is complete only when no target PID remains after terminate/kill.",
        ))
    return {
        "attempts": list(close_attempts),
        "fallback_chain": fallback_chain,
        "recovery_triggered": bool(fallback_chain),
        "verification_checks": extra_checks,
    }


def _evidence_check(name: str, passed: bool | None, expected: Any, observed: Any, reason: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "name": name,
        "passed": passed,
        "expected": expected,
        "observed": observed,
        "actual": observed,
        "reason": reason,
        "detail": reason,
    }


def _negative_evidence_target(intent: str, params: Dict[str, Any]) -> str:
    if intent == "type":
        return "focused_input"
    for key in ("path", "app", "window", "url", "query", "selector", "command", "git_cmd"):
        value = params.get(key)
        if value:
            return str(value)
    if params.get("x") is not None and params.get("y") is not None:
        return "coordinates"
    return intent


def _negative_evidence_target_type(intent: str) -> str:
    if intent in FILE_EVIDENCE_TOOLS:
        return "file"
    if intent == "type":
        return "focused_input"
    if intent in DESKTOP_EVIDENCE_TOOLS:
        return "application"
    if intent in BROWSER_EVIDENCE_TOOLS:
        return "browser"
    if intent == "git_action":
        return "git"
    if intent == "run_command":
        return "shell"
    return "tool"


def _file_failure_observation(before: Dict[str, Any] | None) -> dict[str, Any]:
    if not before:
        return {}

    path = Path(before["path"])
    observed: dict[str, Any] = {
        "path": str(path),
        "existed_before": bool(before.get("existed_before")),
        "before_sha256": before.get("sha256"),
        "before_bytes": before.get("bytes"),
    }
    try:
        existed_after = path.exists()
        after_content = path.read_text(encoding="utf-8") if existed_after else ""
        after_sha256 = _sha256_text(after_content) if existed_after else None
        mutation_performed = bool(
            bool(before.get("existed_before")) != existed_after
            or before.get("sha256") != after_sha256
        )
        observed.update({
            "existed_after": existed_after,
            "after_sha256": after_sha256,
            "after_bytes": len(after_content.encode("utf-8")) if existed_after else 0,
            "mutation_performed": mutation_performed,
        })
    except Exception as exc:
        observed.update({
            "existed_after": None,
            "after_sha256": None,
            "after_bytes": None,
            "mutation_performed": None,
            "mutation_observation_error": str(exc),
        })
    return observed


def _negative_execution_evidence(
    intent: str,
    params: Dict[str, Any],
    started_at_ms: int,
    *,
    failure_kind: str,
    reason: str,
    dispatch_attempted: bool,
    dispatch_succeeded: bool,
    tool_response_returned: bool = False,
    before_write: Dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    recovery_attempts: list[dict[str, Any]] | None = None,
) -> ExecutionEvidence:
    recovery_attempt_list = list(recovery_attempts or [])
    observed: dict[str, Any] = {
        "failure_kind": failure_kind,
        "error": reason,
        "error_sha256": _sha256_text(reason),
        "dispatch_attempted": dispatch_attempted,
        "dispatch_succeeded": dispatch_succeeded,
        "tool_response_returned": tool_response_returned,
        "recovery_attempted": bool(recovery_attempt_list),
        "recovery_attempt_count": len(recovery_attempt_list),
        "recovery_attempts": recovery_attempt_list,
        "verified_success": False,
    }
    expected: dict[str, Any] = {
        "dispatch_succeeded": True,
        "verified_success": True,
    }
    file_observation = _file_failure_observation(before_write)
    if file_observation:
        observed["file"] = file_observation
        expected["mutation_performed"] = False

    mutation_performed = file_observation.get("mutation_performed") if file_observation else None
    checks = [
        _evidence_check(
            "negative_evidence_recorded",
            True,
            "explicit failed/unverified execution evidence",
            failure_kind,
            "Failed execution paths must emit evidence instead of appearing as missing evidence.",
        ),
        _evidence_check(
            "dispatch_attempted",
            True,
            dispatch_attempted,
            dispatch_attempted,
            "Evidence records whether the tool dispatch boundary was reached.",
        ),
        _evidence_check(
            "dispatch_succeeded",
            dispatch_succeeded,
            True,
            dispatch_succeeded,
            "Negative evidence is failed because dispatch or verification did not complete successfully.",
        ),
        _evidence_check(
            "verified_success",
            False,
            True,
            False,
            "Negative evidence must not be interpreted as verified success.",
        ),
    ]
    if file_observation:
        checks.append(_evidence_check(
            "no_unexpected_file_mutation_on_failure",
            (mutation_performed is False) if mutation_performed is not None else None,
            False,
            mutation_performed,
            "Failed file actions should record whether a mutation was observed.",
        ))

    return ExecutionEvidence(
        action=intent,
        target=_negative_evidence_target(intent, params),
        target_type=_negative_evidence_target_type(intent),
        method="negative_result",
        verifier="executor-negative-evidence/1",
        verification_state="failed",
        verification_reason=f"{failure_kind}: {reason}",
        started_at_ms=started_at_ms,
        completed_at_ms=now_ms(),
        expected=expected,
        observed=observed,
        verification_checks=checks,
        warnings=list(warnings or []),
    )


def _with_dispatch_warning(
    evidence: ExecutionEvidence,
    warning: str,
    *,
    method: str,
) -> ExecutionEvidence:
    observed = dict(evidence.observed)
    observed.update({
        "dispatch_warning": warning,
        "dispatch_warning_sha256": _sha256_text(warning),
        "dispatch_warning_did_not_determine_verification": True,
    })
    return evidence.model_copy(update={
        "method": method,
        "observed": observed,
        "warnings": [
            *evidence.warnings,
            f"Dispatch warning preserved separately from verifier result: {warning}",
        ],
    })


def _focus_evidence_updates(focus_attempts: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not focus_attempts:
        return {}
    latest = focus_attempts[-1]
    selected = latest.get("selected_window") if isinstance(latest.get("selected_window"), dict) else {}
    foreground = latest.get("foreground_after") if isinstance(latest.get("foreground_after"), dict) else {}
    selected_hwnd = selected.get("hwnd")
    foreground_hwnd = foreground.get("hwnd")
    checks = [
        _evidence_check(
            "focus_attempt_recorded",
            True,
            "focus tool attempt evidence",
            latest.get("outcome"),
            "Focus tool should record the candidate selection and activation attempt.",
        ),
        _evidence_check(
            "focus_single_tool_candidate",
            latest.get("candidate_count") == 1,
            1,
            latest.get("candidate_count"),
            "Focus tool should choose exactly one visible candidate window.",
        ),
        _evidence_check(
            "focus_activate_called",
            latest.get("activate_called") is True,
            True,
            latest.get("activate_called"),
            "Focus tool should call activate on the selected window.",
        ),
        _evidence_check(
            "focus_selected_hwnd_matches_foreground",
            selected_hwnd == foreground_hwnd if selected_hwnd is not None and foreground_hwnd is not None else None,
            selected_hwnd,
            foreground_hwnd,
            "Foreground HWND after focus should match the selected window HWND.",
        ),
    ]
    return {
        "attempts": list(focus_attempts),
        "verification_checks": checks,
    }


def _desktop_evidence_from_verification(
    intent: str,
    params: Dict[str, Any],
    started_at_ms: int,
    verification: "VerificationEvidence",
    close_attempts: list[dict[str, Any]] | None = None,
    focus_attempts: list[dict[str, Any]] | None = None,
) -> ExecutionEvidence | None:
    if intent not in DESKTOP_EVIDENCE_TOOLS:
        return None
    evidence_updates = _close_evidence_updates(close_attempts) if intent == "close_app" else _focus_evidence_updates(focus_attempts) if intent == "focus_app" else {}
    extra_checks = list(evidence_updates.pop("verification_checks", []))
    if verification.execution_evidence is not None:
        checks = list(verification.execution_evidence.verification_checks)
        checks.extend(extra_checks)
        return verification.execution_evidence.model_copy(update={
            "started_at_ms": started_at_ms,
            "verification_checks": checks,
            **evidence_updates,
        })
    app = str(params.get("app") or params.get("window") or "")
    if not app:
        return None
    desktop_verification = verify_desktop_action(
        action=intent,
        app=app,
        process_name=params.get("_process_name"),
        window_keywords=params.get("_keywords"),
    )
    return verification_to_execution_evidence(
        verification=desktop_verification,
        app=app,
        started_at_ms=started_at_ms,
        attempts=evidence_updates.get("attempts"),
        fallback_chain=evidence_updates.get("fallback_chain"),
        recovery_triggered=bool(evidence_updates.get("recovery_triggered", False)),
    )


def _desktop_failure_evidence(
    intent: str,
    params: Dict[str, Any],
    started_at_ms: int,
    output_text: str,
    close_attempts: list[dict[str, Any]] | None = None,
    focus_attempts: list[dict[str, Any]] | None = None,
) -> ExecutionEvidence | None:
    if intent not in DESKTOP_EVIDENCE_TOOLS:
        return None
    app = str(params.get("app") or params.get("window") or "")
    if not app:
        return None
    verification = verify_desktop_action(
        action=intent,
        app=app,
        process_name=params.get("_process_name"),
        window_keywords=params.get("_keywords"),
    )
    if verification.verification_state != "failed":
        verification = DesktopVerificationResult(
            action=verification.action,
            method=verification.method,
            observation=verification.observation,
            verification_state="failed",
            reason=output_text,
            checks=verification.checks,
        )
    evidence_updates = _close_evidence_updates(close_attempts) if intent == "close_app" else _focus_evidence_updates(focus_attempts) if intent == "focus_app" else {}
    extra_checks = list(evidence_updates.pop("verification_checks", []))
    verification = DesktopVerificationResult(
        action=verification.action,
        method=verification.method,
        observation=verification.observation,
        verification_state=verification.verification_state,
        reason=verification.reason,
        checks=[*verification.checks, *extra_checks],
    )
    return verification_to_execution_evidence(
        verification=verification,
        app=app,
        started_at_ms=started_at_ms,
        attempts=evidence_updates.get("attempts"),
        fallback_chain=evidence_updates.get("fallback_chain"),
        recovery_triggered=bool(evidence_updates.get("recovery_triggered", False)),
        warnings=[output_text],
    )


def _generic_execution_evidence_from_proof(
    intent: str,
    params: Dict[str, Any],
    proof: Dict[str, Any],
    started_at_ms: int,
) -> ExecutionEvidence | None:
    if intent in {"open_url", "search_web"} and "browser_evidence" in proof:
        proof_key = "browser_evidence"
    else:
        proof_key = next((key for key in PROOF_EVIDENCE_KEYS if key in proof), None)
    if not proof_key:
        return None

    target_type = "unknown"
    method = proof_key.replace("_evidence", "")
    target: str | None = intent
    verification_state = "verified"
    verification_reason: str | None = None
    verifier: str | None = None
    expected: dict[str, Any] = {}
    observed: dict[str, Any] = {}
    verification_checks: list[dict[str, Any]] = []

    if proof_key == "read_only_evidence":
        target_type = "read_only"
        data = proof[proof_key]
        if isinstance(data, dict):
            target = str(data.get("path") or data.get("query") or data.get("search_url") or intent)
            if data.get("tool") == "read_file":
                verifier = "file-read-gate/1"
                verification_state = str(data.get("read_verification_state") or "unverified")
                verification_reason = str(data.get("read_verification_reason") or "missing read_file verification state")
                expected = {
                    "resolved_path": data.get("resolved_path"),
                    "content_sha256": data.get("sha256"),
                    "file_exists": True,
                    "is_file": True,
                    "dispatch_ok": True,
                    "content_hash_captured": True,
                    "count_captured": True,
                }
                observed = {
                    "resolved_path": data.get("resolved_path"),
                    "file_exists": data.get("file_exists"),
                    "is_file": data.get("is_file"),
                    "disk_sha256": data.get("disk_sha256"),
                    "output_sha256": data.get("output_sha256") or data.get("sha256"),
                    "byte_count": data.get("byte_count"),
                    "char_count": data.get("char_count"),
                    "dispatch_ok": data.get("dispatch_ok"),
                    "content_hash_captured": data.get("content_hash_captured"),
                    "count_captured": data.get("count_captured"),
                    "content_hash_matches_disk": data.get("content_hash_matches_disk"),
                    "read_error": data.get("read_error"),
                }
                verification_checks = list(data.get("verification_checks") or [])
    elif proof_key == "browser_evidence":
        target_type = "browser"
        browser = proof[proof_key]
        if isinstance(browser, dict):
            target = str(browser.get("url") or browser.get("selector") or browser.get("coordinates") or intent)
            if browser.get("tool") in {"open_url", "search_web"}:
                verifier = "browser-url-gate/1"
                verification_state = str(browser.get("browser_verification_state") or "unverified")
                verification_reason = str(browser.get("browser_verification_reason") or "missing browser URL verification state")
                target = str(browser.get("requested_url") or target)
                expected = {
                    "requested_url": browser.get("requested_url"),
                    "requested_search_url": browser.get("requested_search_url"),
                    "query": browser.get("query"),
                    "bot_challenge_detected": False,
                    "provider_interstitial_detected": False,
                    "fallback_enabled": False,
                    "verified_success": True,
                }
                observed = {
                    "observed_url": browser.get("observed_url"),
                    "final_url": browser.get("final_url"),
                    "browser_context_observable": browser.get("browser_context_observable"),
                    "final_url_captured": browser.get("final_url_captured"),
                    "dispatch_ok": browser.get("dispatch_ok"),
                    "provider": browser.get("provider"),
                    "provider_domain": browser.get("provider_domain"),
                    "search_provider": browser.get("search_provider"),
                    "preferred_browser": browser.get("preferred_browser"),
                    "browser_runtime": browser.get("browser_runtime"),
                    "controlled_browser": browser.get("controlled_browser"),
                    "browser_preference_is_verification": browser.get("browser_preference_is_verification"),
                    "browser_recovery_attempted": browser.get("browser_recovery_attempted"),
                    "browser_recovery_attempt_count": browser.get("browser_recovery_attempt_count"),
                    "browser_recovery_attempts": browser.get("browser_recovery_attempts"),
                    "observed_query": browser.get("observed_query"),
                    "url_matches_request": browser.get("url_matches_request"),
                    "url_mismatch_reason": browser.get("url_mismatch_reason"),
                    "query_matches_observed_url": browser.get("query_matches_observed_url"),
                    "provider_matches_expected": browser.get("provider_matches_expected"),
                    "bot_challenge_detected": browser.get("bot_challenge_detected"),
                    "provider_interstitial_detected": browser.get("provider_interstitial_detected"),
                    "provider_interstitial_type": browser.get("provider_interstitial_type"),
                    "provider_interstitial_reason": browser.get("provider_interstitial_reason"),
                    "blocked_by_bot_challenge": browser.get("blocked_by_bot_challenge"),
                    "search_verification_blocked_by_provider": browser.get("search_verification_blocked_by_provider"),
                    "verification_blocker": browser.get("verification_blocker"),
                    "operator_message": browser.get("operator_message"),
                    "operator_suggestion": browser.get("operator_suggestion"),
                    "fallback_available": browser.get("fallback_available"),
                    "fallback_enabled": browser.get("fallback_enabled"),
                    "fallback_attempted": browser.get("fallback_attempted"),
                    "fallback_requires_operator_decision": browser.get("fallback_requires_operator_decision"),
                    "verified_success": browser.get("verified_success"),
                    "classification_version": browser.get("classification_version"),
                }
                verification_checks = list(browser.get("verification_checks") or [])
    elif proof_key == "write_evidence":
        target_type = "file"
        write_data = proof[proof_key]
        target = str(params.get("path") or write_data.get("path") or "file")
        if isinstance(write_data, dict) and write_data.get("tool") == "write_file":
            verifier = "file-write-gate/1"
            verification_state = str(write_data.get("write_verification_state") or "unverified")
            verification_reason = str(write_data.get("write_verification_reason") or "missing write_file verification state")
            expected = {
                "path": write_data.get("intended_path") or write_data.get("path"),
                "after_sha256": write_data.get("expected_after_sha256"),
                "path_unchanged": True,
                "before_state_known": True,
                "existed_after": True,
                "after_hash_captured": True,
                "dispatch_ok": True,
                "write_confirmed": True,
            }
            observed = {
                "path": write_data.get("path"),
                "after_sha256": write_data.get("after_sha256"),
                "path_unchanged": write_data.get("path_unchanged"),
                "before_state_known": write_data.get("before_state_known"),
                "existed_after": write_data.get("existed_after"),
                "after_hash_captured": write_data.get("after_sha256") is not None,
                "dispatch_ok": write_data.get("dispatch_ok"),
                "write_confirmed": write_data.get("write_confirmed"),
            }
            verification_checks = list(write_data.get("verification_checks") or [])
    elif proof_key == "type_evidence":
        target_type = "focused_input"
        target = "focused_input"
        type_data = proof[proof_key]
        if isinstance(type_data, dict):
            verification_state = str(type_data.get("type_verification_state") or "unverified")
            verification_reason = str(type_data.get("type_verification_reason") or "missing TypeTool verification state")
            expected = {
                "focus": type_data.get("expected_focus"),
                "process_name": type_data.get("expected_focus_process_name"),
                "keywords": type_data.get("expected_focus_keywords"),
                "before_hwnd_equals_after_hwnd": True,
                "focus_verified_before": True,
            }
            observed = {
                "target_before": type_data.get("target_before"),
                "target_after": type_data.get("target_after"),
                "focus_verified_before": type_data.get("focus_verified_before"),
                "focus_verified_after": type_data.get("focus_verified_after"),
                "focus_did_not_change_unexpectedly": type_data.get("focus_did_not_change_unexpectedly"),
                "dispatch_ok": type_data.get("dispatch_ok"),
            }
            verification_checks = list(type_data.get("verification_checks") or [])
        else:
            verification_state = "unverified"
            verification_reason = "missing TypeTool evidence payload"
    elif proof_key == "git_evidence":
        target_type = "git"
        target = str(params.get("git_cmd") or proof[proof_key].get("git_cmd") or "git")
    elif proof_key == "shell_evidence":
        target_type = "shell"
        target = str(params.get("command") or proof[proof_key].get("command") or "shell")

    return ExecutionEvidence(
        action=intent,
        target=target,
        target_type=target_type,
        method=method,
        verifier="type-tool-focus-gate/1" if proof_key == "type_evidence" else verifier,
        verification_state=verification_state,
        verification_reason=verification_reason,
        started_at_ms=started_at_ms,
        completed_at_ms=now_ms(),
        expected=expected,
        observed=observed,
        verification_checks=verification_checks,
        warnings=[],
    )

@dataclass
class VerificationEvidence:
    """Detailed evidence for Tier 4.5 Formal Verification."""
    verified: bool
    status: str # 'SUCCESS', 'AMBIGUOUS', 'FAILED'
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    details: str
    execution_evidence: ExecutionEvidence | None = None

class Verifier:
    """
    AEGIS Tier 4.5 Formal Verifier.
    Enforces strict determinism. 
    Ambiguity (multiple window matches) is treated as a Failure.
    """
    @staticmethod
    async def verify(intent: str, params: Dict[str, Any], ctx: ExecutionContext) -> VerificationEvidence:
        expected = {"intent": intent, "process_name": params.get("_process_name")}
        actual = {"pid": None, "hwnd": None, "is_responsive": False}

        if intent in DESKTOP_EVIDENCE_TOOLS:
            app = str(params.get("app") or "")
            # Give newly launched windows a short stabilization window, but keep the
            # process/window verifier as the single source of the desktop verdict.
            max_attempts = 50 if intent == "open_app" else 1
            last_result = None
            for _ in range(max_attempts):
                result = verify_desktop_action(
                    action=intent,
                    app=app,
                    process_name=params.get("_process_name"),
                    window_keywords=params.get("_keywords"),
                )
                last_result = result
                if result.verification_state in {"verified", "failed"}:
                    break
                if intent != "open_app":
                    break
                await asyncio.sleep(0.1)

            assert last_result is not None
            evidence = verification_to_execution_evidence(
                verification=last_result,
                app=app,
                started_at_ms=now_ms(),
            )
            observed = evidence.observed
            actual.update({
                "pid": observed.get("primary_pid") or observed.get("active_pid") or (evidence.pids[0] if evidence.pids else None),
                "hwnd": observed.get("primary_hwnd") or observed.get("active_hwnd"),
                "is_responsive": bool(evidence.window) or intent == "close_app" and evidence.process_alive is False,
            })
            if last_result.verification_state == "verified":
                return VerificationEvidence(True, "SUCCESS", expected, actual, last_result.reason, evidence)
            if last_result.ambiguous:
                return VerificationEvidence(False, "AMBIGUOUS", expected, actual, last_result.reason, evidence)
            return VerificationEvidence(False, "FAILED", expected, actual, last_result.reason, evidence)

        return VerificationEvidence(True, "SUCCESS", expected, actual, "Generic success.")

class DeterministicExecutor:
    """
    AEGIS Tier 4.5 Formal Executor.
    Uses Formal Specs and Ambiguity-Aware Verification.
    """
    def __init__(self):
        self.max_retries = 1
        self.base_delay = 1.0
        self.tool_timeout = 30.0
        self.transition_model = get_transition_model()
        
        # Browser management — lazy init
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    async def _get_page(self):
        """Lazy initialization of Playwright browser and page with Supervisor tracking."""
        if self._page and hasattr(self._page, "is_closed"):
            try:
                if self._page.is_closed():
                    await self._reset_browser_session()
            except Exception:
                await self._reset_browser_session()
        if self._page:
            return self._page
        from playwright.async_api import async_playwright
        from aegis.executor.browser_supervisor import get_browser_supervisor
        
        supervisor = get_browser_supervisor()
        supervisor.start()

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self._context = await self._browser.new_context()
        supervisor.register_context(self._context)
        
        self._page = await self._context.new_page()
        supervisor.register_page(self._page)
        
        return self._page

    async def _reset_browser_session(self) -> None:
        for handle in (self._page, self._context, self._browser):
            if not handle:
                continue
            try:
                if hasattr(handle, "is_closed") and handle.is_closed():
                    continue
                close = getattr(handle, "close", None)
                if close:
                    result = close()
                    if hasattr(result, "__await__"):
                        await result
            except Exception:
                logger.debug("[BROWSER] Ignored browser reset close failure", exc_info=True)
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            logger.debug("[BROWSER] Ignored Playwright stop failure during reset", exc_info=True)
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    async def close(self):
        """Cleanup browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token: CancellationToken | None = None,
    ) -> ActionResult:
        event_logger = get_event_logger()
        state_manager = get_state_manager()
        step_start = time.perf_counter()
        
        intent = intent_result.intent
        params = intent_result.params
        desktop_started_at_ms = now_ms()

        if cancellation_token and cancellation_token.cancelled:
            evidence = _negative_execution_evidence(
                intent,
                params,
                desktop_started_at_ms,
                failure_kind="cancelled_before_dispatch",
                reason=cancellation_token.cancelled_reason or "Command cancelled before tool execution",
                dispatch_attempted=False,
                dispatch_succeeded=False,
            )
            return ActionResult(
                action=intent,
                params=params,
                status=ActionStatus.CANCELLED,
                success=False,
                output=cancellation_token.cancelled_reason or "Command cancelled before tool execution",
                proof={"execution_evidence": evidence.model_dump()},
                execution_evidence=evidence,
            )
        
        # 0. PRE-EXECUTION SNAPSHOT
        focus_start = time.perf_counter()
        await state_manager.sync_with_os(ctx.trace_id, ctx.span_id)
        before_state = state_manager.get_state()
        focus_acquire_time = (time.perf_counter() - focus_start) * 1000
        
        # 1. PRE-EXECUTION: Validate Formal Preconditions
        pre_errors = self.transition_model.validate_preconditions(intent, before_state)
        if pre_errors:
            reason = f"Formal Precondition Failure: {', '.join(pre_errors)}"
            evidence = _negative_execution_evidence(
                intent,
                params,
                desktop_started_at_ms,
                failure_kind="precondition_failed",
                reason=reason,
                dispatch_attempted=False,
                dispatch_succeeded=False,
            )
            return ActionResult(
                action=intent, params=params, 
                status=ActionStatus.FAILED, success=False,
                output=reason,
                recovery_hint="Executor stopped before tool dispatch because formal preconditions failed.",
                proof={"execution_evidence": evidence.model_dump()},
                execution_evidence=evidence,
                metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter() - step_start)*1000)
            )

        # 2. Predict Transition
        expected_transition = self.transition_model.predict_next_state(before_state, intent, params)
        browser_recovery_attempts: list[dict[str, Any]] = []
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0: await asyncio.sleep(self.base_delay * (2 ** (attempt - 1)))
            write_before: Dict[str, Any] | None = None

            try:
                tool = TOOLS.get(intent)
                tool_spec = get_tool_spec(intent)
                if tool is None:
                    evidence = _negative_execution_evidence(
                        intent,
                        params,
                        desktop_started_at_ms,
                        failure_kind="unknown_tool",
                        reason=f"Unknown tool '{intent}'",
                        dispatch_attempted=False,
                        dispatch_succeeded=False,
                    )
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.FAILED,
                        success=False,
                        output=f"Unknown tool '{intent}'",
                        recovery_hint="Planner produced an intent with no registered deterministic tool.",
                        proof={"execution_evidence": evidence.model_dump()},
                        execution_evidence=evidence,
                        metrics=ReliabilityMetrics(
                            execution_time_ms=(time.perf_counter() - step_start) * 1000,
                            retries=attempt,
                        ),
                    )

                call_params = dict(params)
                call_params["trace_id"] = str(ctx.trace_id)
                call_params["span_id"] = str(ctx.span_id)
                if tool_spec and tool_spec.cancellation_supported:
                    call_params["cancellation_token"] = cancellation_token
                if tool_spec and intent == "run_command" and "timeout_seconds" not in call_params:
                    call_params["timeout_seconds"] = tool_spec.timeout_seconds
                page = None
                if intent in ["open_url", "search_web", "scroll", "read_page"]:
                    page = await self._get_page()
                    call_params["page"] = page
                close_attempts: list[dict[str, Any]] = []
                if intent == "close_app":
                    call_params["_close_evidence"] = close_attempts
                focus_attempts: list[dict[str, Any]] = []
                if intent == "focus_app":
                    call_params["_focus_evidence"] = focus_attempts

                write_before = _capture_write_before(intent, params)
                click_before = await _capture_click_context(intent, params, page)
                
                tool_task = asyncio.create_task(tool.run(**call_params))
                timeout_seconds = float(tool_spec.timeout_seconds if tool_spec else self.tool_timeout)
                deadline = time.perf_counter() + timeout_seconds
                while not tool_task.done():
                    if cancellation_token and cancellation_token.cancelled:
                        tool_task.cancel()
                        evidence = _negative_execution_evidence(
                            intent,
                            params,
                            desktop_started_at_ms,
                            failure_kind="cancelled_during_dispatch",
                            reason=cancellation_token.cancelled_reason or "Command cancelled during tool execution",
                            dispatch_attempted=True,
                            dispatch_succeeded=False,
                            before_write=write_before,
                        )
                        return ActionResult(
                            action=intent,
                            params=params,
                            status=ActionStatus.CANCELLED,
                            success=False,
                            output=cancellation_token.cancelled_reason or "Command cancelled during tool execution",
                            proof={"execution_evidence": evidence.model_dump()},
                            execution_evidence=evidence,
                            metrics=ReliabilityMetrics(
                                execution_time_ms=(time.perf_counter() - step_start) * 1000,
                                retries=attempt,
                            ),
                        )
                    if time.perf_counter() >= deadline:
                        tool_task.cancel()
                        raise asyncio.TimeoutError(f"Tool '{intent}' timed out after {timeout_seconds}s")
                    await asyncio.sleep(0.05)
                output = await tool_task
                output_text = str(output)
                click_after = await _capture_click_context(intent, params, page)
                if output_text.lower().startswith(("error", "failed", "read error", "write error")):
                    if (
                        intent in {"open_url", "search_web"}
                        and _is_browser_lifecycle_failure(output_text)
                        and attempt < self.max_retries
                        and not browser_recovery_attempts
                    ):
                        browser_recovery_attempts.append({
                            "attempt": len(browser_recovery_attempts) + 1,
                            "failure": output_text,
                            "recovery_reason": "closed_browser_lifecycle",
                        })
                        await self._reset_browser_session()
                        continue
                    if intent == "open_app":
                        verifier_result = await Verifier.verify(intent, params, ctx)
                        verified_existing_evidence = _desktop_evidence_from_verification(
                            intent,
                            params,
                            desktop_started_at_ms,
                            verifier_result,
                            close_attempts=close_attempts,
                            focus_attempts=focus_attempts,
                        )
                        if verifier_result.verified and verified_existing_evidence is not None:
                            verified_existing_evidence = _with_dispatch_warning(
                                verified_existing_evidence,
                                output_text,
                                method="verified_existing_after_launch_error",
                            )
                            return ActionResult(
                                action=intent,
                                params=params,
                                status=ActionStatus.EXECUTED,
                                success=True,
                                output=(
                                    "Tool reported a launch error, but the desktop verifier "
                                    f"observed the target window/process: {verifier_result.details}"
                                ),
                                recovery_hint=output_text,
                                proof={
                                    "execution_evidence": verified_existing_evidence.model_dump(),
                                    "tool_output_warning": output_text,
                                },
                                execution_evidence=verified_existing_evidence,
                                focus_verified=True,
                                metrics=ReliabilityMetrics(
                                    execution_time_ms=(time.perf_counter() - step_start) * 1000,
                                    retries=attempt,
                                    determinism_score=0.85,
                                    recovery_triggered=True,
                                ),
                            )
                    failure_evidence = _desktop_failure_evidence(
                        intent,
                        params,
                        desktop_started_at_ms,
                        output_text,
                        close_attempts=close_attempts,
                        focus_attempts=focus_attempts,
                    )
                    if intent == "read_file":
                        read_evidence = _read_only_evidence(intent, params, output_text)
                        if read_evidence and read_evidence.get("file_exists") is True:
                            failure_proof = {"read_only_evidence": read_evidence}
                            execution_evidence = _generic_execution_evidence_from_proof(
                                intent,
                                params,
                                failure_proof,
                                desktop_started_at_ms,
                            )
                            if execution_evidence:
                                failure_proof["execution_evidence"] = execution_evidence.model_dump()
                            return ActionResult(
                                action=intent,
                                params=params,
                                status=ActionStatus.EXECUTED,
                                success=False,
                                output=output_text,
                                recovery_hint=(
                                    execution_evidence.verification_reason
                                    if execution_evidence
                                    else "read_file did not produce execution evidence."
                                ),
                                proof=failure_proof,
                                execution_evidence=execution_evidence,
                                metrics=ReliabilityMetrics(
                                    execution_time_ms=(time.perf_counter() - step_start) * 1000,
                                    retries=attempt,
                                ),
                            )
                    if failure_evidence is None:
                        failure_evidence = _negative_execution_evidence(
                            intent,
                            params,
                            desktop_started_at_ms,
                            failure_kind="tool_returned_error",
                            reason=output_text,
                            dispatch_attempted=True,
                            dispatch_succeeded=False,
                            tool_response_returned=True,
                            before_write=write_before,
                            warnings=[output_text],
                            recovery_attempts=browser_recovery_attempts,
                        )
                    failure_proof = {"execution_evidence": failure_evidence.model_dump()}
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.FAILED,
                        success=False,
                        output=output_text,
                        recovery_hint="Tool returned an explicit failure before verification.",
                        proof=failure_proof,
                        execution_evidence=failure_evidence,
                        metrics=ReliabilityMetrics(
                            execution_time_ms=(time.perf_counter() - step_start) * 1000,
                            retries=attempt,
                        ),
                    )
                
                # 3. POST-EXECUTION: Formal Verification & Sync
                await state_manager.sync_with_os(ctx.trace_id, ctx.span_id)
                evidence = await Verifier.verify(intent, params, ctx)
                execution_evidence = _desktop_evidence_from_verification(
                    intent,
                    params,
                    desktop_started_at_ms,
                    evidence,
                    close_attempts=close_attempts,
                    focus_attempts=focus_attempts,
                )
                
                state_manager.update(
                    ctx.trace_id, ctx.span_id,
                    pid=evidence.actual["pid"], hwnd=evidence.actual["hwnd"],
                    active_app=params.get("app") if intent == "open_app" else before_state.active_app,
                    last_action=intent, last_status=evidence.status
                )
                
                after_state = state_manager.get_state()
                
                # 4. Reliability Metrics & Determinism Score
                post_errors = self.transition_model.validate_postconditions(intent, after_state)
                deviations = self.transition_model.calculate_deviation(expected_transition, after_state)
                
                # Formula: S = (1 - (Dev*0.2 + Err*0.3)) * Stability_Factor
                score = 1.0 - (len(deviations) * 0.2 + len(post_errors) * 0.3)
                if evidence.status == "AMBIGUOUS": score *= 0.5
                if not after_state.focus_stable: score *= 0.8
                
                metrics = ReliabilityMetrics(
                    execution_time_ms=(time.perf_counter() - step_start) * 1000,
                    focus_acquire_ms=focus_acquire_time,
                    retries=attempt,
                    determinism_score=max(0.0, score)
                )

                proof = {
                    "expected": expected_transition, "actual": asdict(after_state),
                    "deviations": deviations, "postcondition_errors": post_errors,
                    "status": evidence.status,
                    "snapshot_diff": {"before": asdict(before_state), "after": asdict(after_state)}
                }
                read_evidence = _read_only_evidence(intent, params, output_text)
                if read_evidence:
                    proof["read_only_evidence"] = read_evidence
                browser_evidence = _browser_evidence(
                    intent,
                    params,
                    output_text,
                    observed_url=str(getattr(page, "url", "")) if page is not None else None,
                    click_before=click_before,
                    click_after=click_after,
                    recovery_attempts=browser_recovery_attempts,
                )
                if browser_evidence:
                    proof["browser_evidence"] = browser_evidence
                write_evidence = _write_evidence(intent, params, write_before, output_text)
                if write_evidence:
                    proof["write_evidence"] = write_evidence
                type_evidence = _type_evidence(intent, params, before_state, after_state, output_text)
                if type_evidence:
                    proof["type_evidence"] = type_evidence
                git_evidence = _git_evidence(intent, params, output_text)
                if git_evidence:
                    proof["git_evidence"] = git_evidence
                shell_evidence = _shell_evidence(intent, params, output_text)
                if shell_evidence:
                    proof["shell_evidence"] = shell_evidence
                if execution_evidence:
                    proof["execution_evidence"] = execution_evidence.model_dump()
                elif generic_evidence := _generic_execution_evidence_from_proof(intent, params, proof, desktop_started_at_ms):
                    execution_evidence = generic_evidence
                    proof["execution_evidence"] = execution_evidence.model_dump()

                if evidence.status == "AMBIGUOUS":
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.FAILED, success=False,
                        confidence=0.5, output=evidence.details, metrics=metrics, proof=proof,
                        execution_evidence=execution_evidence,
                    )

                if intent == "type" and (not execution_evidence or execution_evidence.verification_state != "verified"):
                    reason = (
                        execution_evidence.verification_reason
                        if execution_evidence
                        else "TypeTool did not produce execution evidence."
                    )
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.EXECUTED,
                        success=False,
                        confidence=min(metrics.determinism_score, 0.5),
                        output=output,
                        recovery_hint=reason,
                        focus_verified=False,
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )

                if intent in {"read_file", "write_file"} and (
                    not execution_evidence or execution_evidence.verification_state != "verified"
                ):
                    reason = (
                        execution_evidence.verification_reason
                        if execution_evidence
                        else f"{intent} did not produce execution evidence."
                    )
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.EXECUTED,
                        success=False,
                        confidence=min(metrics.determinism_score, 0.5),
                        output=output,
                        recovery_hint=reason,
                        focus_verified=False,
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )

                if intent in {"open_url", "search_web"} and (
                    not execution_evidence or execution_evidence.verification_state != "verified"
                ):
                    reason = (
                        execution_evidence.verification_reason
                        if execution_evidence
                        else f"{intent} did not produce browser execution evidence."
                    )
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.EXECUTED,
                        success=False,
                        confidence=min(metrics.determinism_score, 0.5),
                        output=output,
                        recovery_hint=reason,
                        focus_verified=False,
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )

                if evidence.verified and not post_errors:
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.EXECUTED, success=True,
                        confidence=metrics.determinism_score, output=output, 
                        focus_verified=after_state.focus_stable or bool(execution_evidence and execution_evidence.verification_state == "verified"),
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )
                if intent in DESKTOP_EVIDENCE_TOOLS and execution_evidence and attempt == self.max_retries:
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.FAILED,
                        success=False,
                        confidence=metrics.determinism_score,
                        output=evidence.details or output_text,
                        recovery_hint="Desktop verifier did not produce verified evidence.",
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )

            except Exception as e:
                if (
                    intent in {"open_url", "search_web"}
                    and _is_browser_lifecycle_failure(str(e))
                    and attempt < self.max_retries
                    and not browser_recovery_attempts
                ):
                    browser_recovery_attempts.append({
                        "attempt": len(browser_recovery_attempts) + 1,
                        "failure": str(e),
                        "recovery_reason": "closed_browser_lifecycle",
                    })
                    await self._reset_browser_session()
                    continue
                if attempt == self.max_retries:
                    evidence = _negative_execution_evidence(
                        intent,
                        params,
                        desktop_started_at_ms,
                        failure_kind="dispatch_exception",
                        reason=str(e),
                        dispatch_attempted=True,
                        dispatch_succeeded=False,
                        before_write=write_before,
                        warnings=[str(e)],
                        recovery_attempts=browser_recovery_attempts,
                    )
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.FAILED, success=False,
                        output=str(e),
                        recovery_hint="Tool dispatch raised before producing verified evidence.",
                        proof={"execution_evidence": evidence.model_dump()},
                        execution_evidence=evidence,
                        metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter()-step_start)*1000)
                    )

        evidence = _negative_execution_evidence(
            intent,
            params,
            desktop_started_at_ms,
            failure_kind="max_retries_exceeded",
            reason="Max retries exceeded or formal failure.",
            dispatch_attempted=True,
            dispatch_succeeded=False,
            recovery_attempts=browser_recovery_attempts,
        )
        return ActionResult(
            action=intent, params=params, status=ActionStatus.FAILED, success=False,
            output="Max retries exceeded or formal failure.",
            proof={"execution_evidence": evidence.model_dump()},
            execution_evidence=evidence,
            metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter()-step_start)*1000)
        )

_instance = None
def get_deterministic_executor() -> DeterministicExecutor:
    global _instance
    if _instance is None:
        _instance = DeterministicExecutor()
    return _instance
