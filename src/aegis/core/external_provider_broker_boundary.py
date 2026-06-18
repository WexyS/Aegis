from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from aegis.core.external_provider_readiness import (
    expected_provider_env_placeholders,
    list_external_provider_readiness,
)


EXTERNAL_PROVIDER_BROKER_CONTRACT = "aegis-external-provider-broker-boundary"
EXTERNAL_PROVIDER_BROKER_EXECUTION_PERMISSION = "not_granted_by_external_provider_broker_boundary"
MAX_PROMPT_PREVIEW_CHARS = 800
MAX_PROMPT_CHARS = 4000

ALLOWED_PREVIEW_PURPOSES = (
    "explanation",
    "proposal_draft",
    "coding_review",
    "reasoning_review",
    "summary",
)

REQUIRED_OPERATOR_ACKNOWLEDGEMENTS = (
    "provider_selected",
    "model_selected",
    "prompt_reviewed",
    "privacy_risk_reviewed",
    "cost_risk_reviewed",
    "no_secrets_confirmed",
    "proposal_only_understood",
)

_SECRET_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"sk-[A-Za-z0-9._-]{8,}"), "sk-[redacted]"),
    (
        re.compile(r"(Authorization\s*:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
        r"\1[redacted]",
    ),
    (
        re.compile(r"((?:api[_-]?key|apikey|token|password|private[_-]?key)\s*[=:]\s*)([^\s;,\n]+)", re.IGNORECASE),
        r"\1[redacted]",
    ),
)

_RISK_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("possible_api_key_marker", re.compile(r"sk-[A-Za-z0-9._-]{8,}", re.IGNORECASE)),
    ("api_key_marker", re.compile(r"\bapi[_-]?key\b|\bapikey\b", re.IGNORECASE)),
    ("token_marker", re.compile(r"\btoken\b|Authorization\s*:\s*Bearer", re.IGNORECASE)),
    ("password_marker", re.compile(r"\bpassword\b", re.IGNORECASE)),
    ("private_key_marker", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY|private[_-]?key", re.IGNORECASE)),
    ("traceback_marker", re.compile(r"\bTraceback \(most recent call last\):|\bstack trace\b", re.IGNORECASE)),
    ("runtime_events_marker", re.compile(r"runtime_events(?:\.jsonl)?", re.IGNORECASE)),
    ("env_file_marker", re.compile(r"(^|[\s\\/])\.env(\b|[\\/])|\.env\.", re.IGNORECASE)),
    ("evidence_or_journal_marker", re.compile(r"\b(raw_)?evidence\b|\bjournal\b", re.IGNORECASE)),
    ("repo_dump_marker", re.compile(r"(^|\n)\s*(diff --git|commit [0-9a-f]{7,}|```)", re.IGNORECASE)),
    ("dependency_or_cache_path_marker", re.compile(r"node_modules|\.git[\\/]|__pycache__|\.next[\\/]|dist[\\/]|build[\\/]", re.IGNORECASE)),
)


def build_external_provider_broker_boundary(
    *,
    provider_readiness: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    readiness = _readiness_records(provider_readiness)
    return {
        "contract": EXTERNAL_PROVIDER_BROKER_CONTRACT,
        "status": "designed_disabled",
        "execution_permission": EXTERNAL_PROVIDER_BROKER_EXECUTION_PERMISSION,
        "provider_setup_guidance": build_provider_setup_guidance(provider_readiness=readiness),
        "allowed_preview_purposes": ALLOWED_PREVIEW_PURPOSES,
        "required_operator_acknowledgements": REQUIRED_OPERATOR_ACKNOWLEDGEMENTS,
        "max_prompt_chars": MAX_PROMPT_CHARS,
        "max_prompt_preview_chars": MAX_PROMPT_PREVIEW_CHARS,
        "cloud_calls_enabled_now": False,
        "external_provider_calls_performed": False,
        "automatic_fallback_allowed": False,
        "local_failure_triggers_cloud": False,
        "provider_key_presence_is_authorization": False,
        "manual_operator_opt_in_required": True,
        "provider_selection_required": True,
        "exact_model_selection_required": True,
        "operator_managed_env_only": True,
        "ui_key_input_allowed": False,
        "ui_env_write_allowed": False,
        "prompt_preview_required": True,
        "prompt_redaction_preview_required": True,
        "cost_warning_required": True,
        "privacy_warning_required": True,
        "redaction_review_required": True,
        "secrets_allowed_in_prompt": False,
        "raw_logs_allowed_in_prompt": False,
        "raw_journals_allowed_in_prompt": False,
        "raw_evidence_allowed_in_prompt": False,
        "repo_dump_allowed_in_prompt": False,
        "proposal_only_output_required": True,
        "output_authority": False,
        "output_is_evidence": False,
        "output_is_verifier_success": False,
        "memory_write_allowed": False,
        "tool_execution_allowed": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "approval_grant": False,
        "approval_granted": False,
        "permission_granted": False,
        "capability_grant": False,
        "capability_lease_granted": False,
        "lease_grant": False,
        "evidence_created": False,
        "evidence": False,
        "verifier_success": False,
        "mutation_performed": False,
        "frontend_authority": False,
        "cloud_call_performed": False,
        "external_api_called": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "provider_authenticated": False,
        "provider_key_value_exposed": False,
        "prompt_payload_sent": False,
        "data_sent_external": False,
        "transcript_persisted": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "mcp_call_performed": False,
        "plugin_execution_performed": False,
        "agent_execution_performed": False,
        "workflow_execution_performed": False,
        "computer_control_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "requires_backend_validation": True,
        "requires_policy_check": True,
        "limitations": (
            "broker_boundary_is_preview_only",
            "no_external_provider_calls_are_enabled",
            "api_key_presence_is_boolean_metadata_only",
            "prompt_preview_is_not_cloud_permission",
            "model_output_would_remain_proposal_only",
        ),
    }


def build_provider_setup_guidance(
    provider_id: str | None = None,
    *,
    provider_readiness: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    readiness_by_id = {
        str(record.get("provider_id") or ""): dict(record)
        for record in _readiness_records(provider_readiness)
    }
    placeholders = expected_provider_env_placeholders()
    if provider_id:
        placeholders = [
            item for item in placeholders
            if item["provider_id"] == provider_id
        ]

    guidance: list[dict[str, Any]] = []
    for item in placeholders:
        readiness = readiness_by_id.get(item["provider_id"], {})
        guidance.append(
            {
                "provider_id": item["provider_id"],
                "label": readiness.get("label") or item["provider_id"],
                "status": readiness.get("status") or "missing_key_disabled",
                "api_key_env_var": item["api_key_env_var"],
                "model_env_var": item["model_env_var"],
                "api_key_placeholder": item["api_key_placeholder"],
                "model_placeholder": item["model_placeholder"],
                "api_key_present": bool(readiness.get("api_key_present")),
                "api_key_value_exposed": False,
                "operator_managed_env_only": True,
                "ui_key_input_allowed": False,
                "ui_env_write_allowed": False,
                "cloud_call_enabled": False,
                "automatic_fallback_allowed": False,
                "future_requirements": tuple(readiness.get("future_requirements") or ()),
            }
        )
    return guidance


def build_external_provider_prompt_preview(
    request: Mapping[str, Any],
    *,
    provider_readiness: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    readiness = _readiness_records(provider_readiness)
    provider_by_id = {
        str(record.get("provider_id") or ""): dict(record)
        for record in readiness
    }

    provider_id = str(request.get("provider_id") or "").strip().lower()
    provider = provider_by_id.get(provider_id)
    prompt = request.get("prompt")
    prompt_text = prompt if isinstance(prompt, str) else ""
    purpose = str(request.get("purpose") or "explanation").strip()
    model_id = request.get("model_id")
    model_id_text = str(model_id).strip() if model_id is not None else None
    acknowledgements = _as_string_tuple(request.get("operator_acknowledgements"))
    received_acknowledgements = frozenset(acknowledgements)
    missing_acknowledgements = tuple(
        item for item in REQUIRED_OPERATOR_ACKNOWLEDGEMENTS
        if item not in received_acknowledgements
    )
    risk_markers = detect_prompt_risk_markers(prompt_text)
    blocked_reasons = ["external_provider_broker_not_enabled", "external_provider_calls_disabled"]

    if not provider_id or provider is None:
        blocked_reasons.append("unsupported_or_missing_provider")
    if purpose not in ALLOWED_PREVIEW_PURPOSES:
        blocked_reasons.append("unsupported_preview_purpose")
    if not prompt_text.strip():
        blocked_reasons.append("prompt_required")
    if len(prompt_text) > MAX_PROMPT_CHARS:
        blocked_reasons.append("prompt_too_large")
    if missing_acknowledgements:
        blocked_reasons.append("required_operator_acknowledgements_missing")
    if risk_markers:
        blocked_reasons.append("prompt_contains_sensitive_or_raw_diagnostic_markers")

    return {
        "contract": EXTERNAL_PROVIDER_BROKER_CONTRACT,
        "status": _preview_status(blocked_reasons),
        "provider_id": provider_id or None,
        "provider_label": provider.get("label") if provider else None,
        "provider_status": provider.get("status") if provider else "unknown",
        "model_id": model_id_text,
        "purpose": purpose,
        "prompt_chars": len(prompt_text),
        "prompt_preview": _preview_prompt(prompt_text),
        "prompt_preview_truncated": len(_redact_prompt(prompt_text)) > MAX_PROMPT_PREVIEW_CHARS,
        "heuristic_prompt_risk_markers": risk_markers,
        "operator_acknowledgements_required": REQUIRED_OPERATOR_ACKNOWLEDGEMENTS,
        "operator_acknowledgements_received": acknowledgements,
        "missing_acknowledgements": missing_acknowledgements,
        "blocked_reasons": tuple(dict.fromkeys(blocked_reasons)),
        "future_requirements": (
            "explicit_external_provider_broker_enablement",
            "operator_provider_and_model_selection",
            "cost_warning_acknowledgement",
            "privacy_warning_acknowledgement",
            "secret_redaction_policy",
            "proposal_only_non_authority_output_envelope",
        ),
        "would_call_provider": False,
        "prompt_preview_only": True,
        "cloud_calls_enabled_now": False,
        "external_provider_calls_performed": False,
        "provider_key_presence_is_authorization": False,
        "manual_operator_opt_in_required": True,
        "provider_selection_required": True,
        "exact_model_selection_required": True,
        "automatic_fallback_allowed": False,
        "local_failure_triggers_cloud": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": EXTERNAL_PROVIDER_BROKER_EXECUTION_PERMISSION,
        "approval_grant": False,
        "approval_granted": False,
        "permission_granted": False,
        "capability_grant": False,
        "capability_lease_granted": False,
        "lease_grant": False,
        "evidence_created": False,
        "evidence": False,
        "verifier_success": False,
        "mutation_performed": False,
        "frontend_authority": False,
        "cloud_call_performed": False,
        "external_api_called": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "provider_authenticated": False,
        "provider_key_value_exposed": False,
        "prompt_payload_sent": False,
        "data_sent_external": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "mcp_call_performed": False,
        "plugin_execution_performed": False,
        "agent_execution_performed": False,
        "workflow_execution_performed": False,
        "computer_control_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "transcript_persisted": False,
        "output_authority": False,
        "output_is_evidence": False,
        "output_is_verifier_success": False,
        "requires_backend_validation": True,
        "requires_policy_check": True,
    }


def detect_prompt_risk_markers(prompt: str) -> tuple[str, ...]:
    markers = [marker for marker, pattern in _RISK_MARKERS if pattern.search(prompt)]
    if _looks_like_large_repo_or_log_dump(prompt):
        markers.append("large_or_line_dense_payload_marker")
    return tuple(dict.fromkeys(markers))


def _readiness_records(
    provider_readiness: Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if provider_readiness is None:
        return [dict(record) for record in list_external_provider_readiness()]
    return [dict(record) for record in provider_readiness]


def _preview_status(blocked_reasons: list[str]) -> str:
    if "unsupported_or_missing_provider" in blocked_reasons:
        return "blocked_by_unknown_provider"
    if "prompt_required" in blocked_reasons:
        return "blocked_by_empty_prompt"
    if "prompt_too_large" in blocked_reasons:
        return "blocked_by_prompt_too_large"
    if "unsupported_preview_purpose" in blocked_reasons:
        return "blocked_by_unsupported_purpose"
    if "prompt_contains_sensitive_or_raw_diagnostic_markers" in blocked_reasons:
        return "blocked_by_prompt_safety_preview"
    if "required_operator_acknowledgements_missing" in blocked_reasons:
        return "blocked_by_missing_operator_acknowledgement"
    return "blocked_until_external_provider_broker_enabled"


def _preview_prompt(prompt: str) -> str:
    redacted = _redact_prompt(prompt).strip()
    if len(redacted) <= MAX_PROMPT_PREVIEW_CHARS:
        return redacted
    return redacted[:MAX_PROMPT_PREVIEW_CHARS].rstrip() + "\n[preview truncated]"


def _redact_prompt(prompt: str) -> str:
    redacted = prompt
    for pattern, replacement in _SECRET_REDACTIONS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _looks_like_large_repo_or_log_dump(prompt: str) -> bool:
    lines = [line for line in prompt.splitlines() if line.strip()]
    if len(lines) < 60:
        return False
    path_like = sum(1 for line in lines if "/" in line or "\\" in line or line.lstrip().startswith(("+", "-", "@@")))
    return path_like >= 20


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return ()
