from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CONTRACT_NAME = "aegis-read-only-capability-broker-preview"

CLASSIFICATION_OBSERVE_ONLY = "observe_only"
CLASSIFICATION_EXPLAIN_ONLY = "explain_only"
CLASSIFICATION_PROPOSAL_ONLY = "proposal_only"
CLASSIFICATION_APPROVAL_REQUIRED = "approval_required"
CLASSIFICATION_EXECUTION_UNAVAILABLE = "execution_unavailable"
CLASSIFICATION_PROVIDER_UNAVAILABLE = "provider_unavailable"
CLASSIFICATION_UNSUPPORTED = "unsupported_or_ambiguous"

NO_ACTION_FLAGS: dict[str, bool] = {
    "action_performed": False,
    "model_call_performed": False,
    "provider_call_performed": False,
    "command_executed": False,
    "tool_executed": False,
    "browser_action_performed": False,
    "filesystem_mutation_performed": False,
    "memory_written": False,
    "approval_granted": False,
    "evidence_created": False,
    "verifier_run": False,
    "execution_authorized": False,
}

_OBSERVATION_TERMS = (
    "status",
    "durum",
    "health",
    "runtime",
    "diagnostic",
    "maintenance",
    "blocker",
)
_EXPLANATION_TERMS = ("explain", "acikla", "what is", "nedir", "why", "neden")
_EXECUTION_ACTION_TERMS = (
    "run",
    "execute",
    "calistir",
    "launch",
    "open",
    "delete",
    "remove",
    "create",
    "write",
)
_EXECUTION_TARGET_TERMS = (
    "command",
    "komut",
    "shell",
    "terminal",
    "browser",
    "tarayici",
    "file",
    "folder",
    "filesystem",
    "url",
    "website",
)


def build_capability_assessment(
    request: str,
    route_preview: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify route-preview metadata without invoking or authorizing capability use."""
    normalized = _normalize(request)
    route_id = str(route_preview.get("route_id", ""))
    primary_intent = str(route_preview.get("primary_intent", ""))
    external_candidate_disabled = route_preview.get("external_cloud_candidate_disabled") is True

    classification, rationale, boundary = _classify(
        normalized=normalized,
        route_id=route_id,
        primary_intent=primary_intent,
        external_candidate_disabled=external_candidate_disabled,
    )
    return {
        "contract": CONTRACT_NAME,
        "classification": classification,
        "rationale": rationale,
        "boundary": boundary,
        "source": "backend_route_preview",
        "read_only": True,
        "preview_only": True,
        "deterministic": True,
        "non_authoritative": True,
        "non_executing": True,
        "non_approving": True,
        "non_verifying": True,
        **NO_ACTION_FLAGS,
    }


def _classify(
    *,
    normalized: str,
    route_id: str,
    primary_intent: str,
    external_candidate_disabled: bool,
) -> tuple[str, str, str]:
    if not normalized:
        return (
            CLASSIFICATION_UNSUPPORTED,
            "No bounded request was available for capability classification.",
            "Clarify the request before any capability path is considered.",
        )
    if external_candidate_disabled:
        return (
            CLASSIFICATION_PROVIDER_UNAVAILABLE,
            "The request references an external provider path that is disabled.",
            "No provider was selected or called, and no fallback is allowed.",
        )
    if route_id in {"command_approval_preview", "research_plan", "vision_review_plan", "vision_to_code_prompt"}:
        return (
            CLASSIFICATION_EXECUTION_UNAVAILABLE,
            "The request depends on an execution, browser, file, upload, or external research capability.",
            "That capability is unavailable in the current read-only preview boundary.",
        )
    if _contains_any(normalized, _EXECUTION_ACTION_TERMS) and _contains_any(
        normalized, _EXECUTION_TARGET_TERMS
    ):
        return (
            CLASSIFICATION_EXECUTION_UNAVAILABLE,
            "The request asks for a command, browser, or filesystem action.",
            "No action was performed or authorized by this assessment.",
        )
    if route_id == "approval_review" or primary_intent == "approval_review":
        return (
            CLASSIFICATION_APPROVAL_REQUIRED,
            "The request concerns a capability path that would require explicit approval.",
            "This preview does not create, request, or grant approval.",
        )
    if route_id in {"safe_plan_builder", "code_prompt_builder", "memory_policy_preview"}:
        return (
            CLASSIFICATION_PROPOSAL_ONLY,
            "Aegis can prepare non-authoritative proposal metadata for this request.",
            "Any proposal remains unverified and does not execute or grant permission.",
        )
    if route_id == "model_hub_review":
        return (
            CLASSIFICATION_EXPLAIN_ONLY,
            "Aegis can explain declared model and provider boundaries without checking availability.",
            "No model or provider was selected, probed, or called.",
        )
    if route_id == "status_explainer" and _contains_any(normalized, _OBSERVATION_TERMS):
        return (
            CLASSIFICATION_OBSERVE_ONLY,
            "Aegis can summarize backend-owned state already supplied to the read-only path.",
            "Observation does not authorize action or establish production readiness.",
        )
    if route_id == "status_explainer" and _contains_any(normalized, _EXPLANATION_TERMS):
        return (
            CLASSIFICATION_EXPLAIN_ONLY,
            "Aegis can explain the requested boundary using deterministic preview metadata.",
            "The explanation is non-authoritative and performs no action.",
        )
    return (
        CLASSIFICATION_UNSUPPORTED,
        "The request does not map clearly to a supported read-only capability.",
        "Clarification is required; no capability was invoked or authorized.",
    )


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("ı", "i").split())
