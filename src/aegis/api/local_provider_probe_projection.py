"""Read-only local provider probe projection API surface."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from fastapi import APIRouter

from aegis.core.local_provider_probe_maintenance_projection import (
    LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_EXECUTION_PERMISSION,
    validate_local_provider_probe_maintenance_projection_request,
)


LOCAL_PROVIDER_PROBE_API_SURFACE_VERSION = (
    "local-provider-probe-maintenance-projection-api-surface/1"
)
LOCAL_PROVIDER_PROBE_API_SURFACE_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_api_surface"
)

NO_CURRENT_PROJECTION_RESULT_CLASS = "no_projection_available"
NO_CURRENT_PROJECTION_STATUS_CLASS = "no_current_probe_result"

PROBE_RESULT_TO_API_RESULT_CLASS = {
    "unreachable_negative_candidate": "provider_probe_unreachable_candidate",
    "timeout_negative_candidate": "provider_probe_timeout_candidate",
    "connection_refused_negative_candidate": "provider_probe_connection_refused_candidate",
    "invalid_response_negative_candidate": "provider_probe_invalid_response_candidate",
    "unauthorized_negative_candidate": "provider_probe_unauthorized_candidate",
    "unsupported_endpoint_negative_candidate": "provider_probe_unsupported_endpoint_candidate",
    "metadata_success_candidate": "provider_probe_metadata_candidate",
    "health_metadata_success_candidate": "provider_probe_metadata_candidate",
    "model_list_success_candidate": "provider_probe_model_list_candidate",
    "empty_model_list_candidate": "provider_probe_empty_model_list_candidate",
    "not_observed": "provider_probe_not_observed",
    "not_executed": "provider_probe_not_configured",
    "unknown": "unknown",
}

NEGATIVE_API_RESULT_CLASSES = {
    "provider_probe_unreachable_candidate",
    "provider_probe_timeout_candidate",
    "provider_probe_connection_refused_candidate",
    "provider_probe_invalid_response_candidate",
    "provider_probe_unauthorized_candidate",
    "provider_probe_unsupported_endpoint_candidate",
}

METADATA_API_RESULT_CLASSES = {
    "provider_probe_metadata_candidate",
    "provider_probe_model_list_candidate",
    "provider_probe_empty_model_list_candidate",
}

RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS = {
    "provider_probe_unreachable_candidate",
    "provider_probe_timeout_candidate",
    "provider_probe_connection_refused_candidate",
    "provider_probe_invalid_response_candidate",
}

RETRY_REQUIRES_OPERATOR_APPROVAL_PROBE_RESULTS = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
}

router = APIRouter(prefix="/maintenance/local-provider/probe-projection", tags=["maintenance"])


@router.get("")
async def local_provider_probe_projection_status() -> dict[str, Any]:
    """Return the current read-only provider probe projection, if one exists."""

    return build_local_provider_probe_projection_api_response()


def build_local_provider_probe_projection_api_response(
    *,
    projection_metadata: Mapping[str, Any] | None = None,
    maintenance_projection_decision: Any | None = None,
) -> dict[str, Any]:
    """Build a non-authoritative projection response without probing providers."""

    if projection_metadata is None and maintenance_projection_decision is None:
        return _no_current_projection_response()

    if maintenance_projection_decision is None:
        maintenance_projection_decision = validate_local_provider_probe_maintenance_projection_request(
            _maintenance_projection_request(dict(projection_metadata or {}))
        )
    decision = _to_mapping(maintenance_projection_decision)
    result_class = _api_result_class(str(decision.get("probe_result_class") or "unknown"))
    api_status = _api_surface_status(result_class, decision)
    response = _base_response(
        projection_result_class=result_class,
        api_surface_status_class=api_status,
        projection_available=True,
        current_projection_available=False,
        source_current=False,
    )
    response.update(
        {
            "maintenance_projection_status": decision.get("projection_status"),
            "probe_result_class": decision.get("probe_result_class"),
            "display_contract_class": decision.get("display_contract_class"),
            "display_status_candidate": decision.get("display_status_candidate"),
            "api_projection_semantics": decision.get("api_projection_semantics"),
            "truthfulness_classification": decision.get("truthfulness_classification"),
            "retry_semantics": decision.get("retry_semantics"),
            "requires_operator_approval_for_retry": result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS,
            "failure_reasons": tuple(decision.get("failure_reasons") or ()),
            "source_refs": tuple(decision.get("projection_input", {}).get("source_refs", ()) if isinstance(decision.get("projection_input"), Mapping) else ()),
            "provenance": tuple(decision.get("projection_input", {}).get("provenance", ()) if isinstance(decision.get("projection_input"), Mapping) else ()),
            "limitations": tuple(decision.get("projection_input", {}).get("limitations", ()) if isinstance(decision.get("projection_input"), Mapping) else ()),
            "unknowns": tuple(decision.get("projection_input", {}).get("unknowns", ()) if isinstance(decision.get("projection_input"), Mapping) else ()),
            "blocked": bool(decision.get("failure_reasons")),
        }
    )
    return response


def _no_current_projection_response() -> dict[str, Any]:
    response = _base_response(
        projection_result_class=NO_CURRENT_PROJECTION_RESULT_CLASS,
        api_surface_status_class=NO_CURRENT_PROJECTION_STATUS_CLASS,
        projection_available=False,
        current_projection_available=False,
        source_current=False,
    )
    response.update(
        {
            "maintenance_projection_status": "not_observed",
            "probe_result_class": "not_observed",
            "display_contract_class": "non_authoritative_status_card",
            "display_status_candidate": "no_current_projection",
            "api_projection_semantics": "no_current_projection_available_not_provider_health_or_runtime_failure",
            "truthfulness_classification": "not_runtime_health_not_provider_health_not_model_availability_not_evidence_not_verifier_success",
            "retry_semantics": "no_retry_authorized_by_api_surface",
            "requires_operator_approval_for_retry": False,
            "failure_reasons": (),
            "source_refs": (),
            "provenance": (
                {
                    "ref_id": "local-provider-probe-projection:current-source-unavailable",
                    "ref_type": "absence_projection",
                },
            ),
            "limitations": (
                "No durable/current local provider probe projection source is available.",
                "Previous manual smoke results are not replayed as current runtime state.",
            ),
            "unknowns": ("Current provider endpoint reachability is not observed.",),
            "blocked": False,
        }
    )
    return response


def _base_response(
    *,
    projection_result_class: str,
    api_surface_status_class: str,
    projection_available: bool,
    current_projection_available: bool,
    source_current: bool,
) -> dict[str, Any]:
    return {
        "api_surface_version": LOCAL_PROVIDER_PROBE_API_SURFACE_VERSION,
        "read_only": True,
        "projection_result_class": projection_result_class,
        "api_surface_status_class": api_surface_status_class,
        "projection_available": projection_available,
        "current_projection_available": current_projection_available,
        "source_current": source_current,
        "mutation_performed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_API_SURFACE_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_provided": False,
        "verifier_success": False,
        "frontend_authority": False,
        "api_authority": False,
        "api_route_added": False,
        "runtime_command_added": False,
        "scheduler_added": False,
        "provider_health_verified": False,
        "model_availability_verified": False,
        "model_identity_verified": False,
        "benchmark_claim_verified": False,
        "retry_authorized": False,
        "auto_mode_selection_performed": False,
        "live_probe_performed": False,
        "real_endpoint_probed": False,
        "socket_opened": False,
        "http_request_performed": False,
        "model_loaded": False,
        "model_call_performed": False,
        "generation_performed": False,
        "embedding_generated": False,
        "reranking_performed": False,
        "multimodal_inference_performed": False,
        "prompt_payload_sent": False,
        "context_payload_sent": False,
        "memory_payload_sent": False,
        "repo_payload_sent": False,
        "raw_journal_payload_sent": False,
        "raw_evidence_payload_sent": False,
        "api_key_validated": False,
        "secret_read": False,
        "authorization_header_sent": False,
        "response_body_logged": False,
        "secret_logged": False,
        "cloud_provider_called": False,
        "lan_or_remote_endpoint_called": False,
        "runtime_health_mutated": False,
        "maintenance_health_mutated": False,
        "runtime_state_mutated": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "replay_mutated": False,
        "data_sent_external": False,
    }


def _maintenance_projection_request(metadata: Mapping[str, Any]) -> dict[str, Any]:
    probe_result_class = str(metadata.get("probe_result_class") or "not_observed")
    return {
        "request_id": str(metadata.get("request_id") or "local-provider-probe-api-surface:fixture"),
        "projection_api_source_class": str(metadata.get("projection_api_source_class") or "caller_supplied_metadata"),
        "api_exposure_readiness_class": str(
            metadata.get("api_exposure_readiness_class")
            or _readiness_for_probe_result(probe_result_class)
        ),
        "maintenance_category_class": str(
            metadata.get("maintenance_category_class")
            or _category_for_probe_result(probe_result_class)
        ),
        "consumer_surface_class": str(metadata.get("consumer_surface_class") or "api_response_future"),
        "display_contract_class": str(
            metadata.get("display_contract_class")
            or _display_for_probe_result(probe_result_class)
        ),
        "namespace": str(metadata.get("namespace") or "local_provider_probe_api_surface"),
        "source_refs": metadata.get("source_refs") or [{"ref_id": "synthetic:provider-probe-projection", "ref_type": "test_fixture"}],
        "provenance": metadata.get("provenance") or [{"ref_id": "caller-supplied-projection-metadata", "ref_type": "synthetic_fixture"}],
        "local_provider_probe_projection_ref": metadata.get("local_provider_probe_projection_ref")
        or {
            "ref_id": str(metadata.get("projection_ref_id") or "local-provider-probe-projection:fixture"),
            "probe_result_class": probe_result_class,
            "projection_status": str(metadata.get("projection_status") or "fixture_projection"),
        },
        "probe_result_class": probe_result_class,
        "projection_status": str(metadata.get("projection_status") or "fixture_projection"),
        "display_severity_class": str(metadata.get("display_severity_class") or "info"),
        "limitations": tuple(metadata.get("limitations") or ("caller-supplied fixture only",)),
        "unknowns": tuple(metadata.get("unknowns") or ()),
        **_forward_safety_flags(metadata),
    }


def _forward_safety_flags(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: metadata[key]
        for key in (
            "generation_performed",
            "embedding_generated",
            "reranking_performed",
            "multimodal_inference_performed",
            "prompt_payload_sent",
            "context_payload_sent",
            "memory_payload_sent",
            "repo_payload_sent",
            "raw_journal_payload_sent",
            "raw_evidence_payload_sent",
            "api_key_validated",
            "secret_read",
            "authorization_header_sent",
            "response_body_logged",
            "secret_logged",
            "cloud_provider_called",
            "lan_or_remote_endpoint_called",
            "data_sent_external",
            "runtime_dispatch_allowed",
            "mutation_performed",
            "frontend_authority",
            "api_authority",
            "provider_health_verified",
            "model_availability_verified",
            "retry_authorized",
            "auto_mode_selection_performed",
            "live_probe_performed",
            "real_endpoint_probed",
            "socket_opened",
            "http_request_performed",
        )
        if key in metadata
    }


def _readiness_for_probe_result(probe_result_class: str) -> str:
    if probe_result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_PROBE_RESULTS:
        return "requires_operator_review_for_retry"
    return "api_projection_metadata_only"


def _category_for_probe_result(probe_result_class: str) -> str:
    if probe_result_class == "model_list_success_candidate":
        return "local_model_list_metadata"
    if probe_result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_PROBE_RESULTS:
        return "local_provider_retry_guidance"
    if probe_result_class in {
        "unauthorized_negative_candidate",
        "unsupported_endpoint_negative_candidate",
        "cancelled_negative_candidate",
    }:
        return "local_provider_negative_candidate"
    if probe_result_class == "not_observed":
        return "local_provider_unknown"
    return "provider_probe_status"


def _display_for_probe_result(probe_result_class: str) -> str:
    if probe_result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_PROBE_RESULTS:
        return "retry_requires_operator_approval_notice"
    if probe_result_class in NEGATIVE_API_RESULT_CLASSES or probe_result_class.endswith("_negative_candidate"):
        return "negative_candidate_notice"
    if probe_result_class == "model_list_success_candidate":
        return "not_model_availability_proof_notice"
    if probe_result_class in {"metadata_success_candidate", "health_metadata_success_candidate"}:
        return "not_provider_health_proof_notice"
    if probe_result_class == "empty_model_list_candidate":
        return "not_runtime_failure_notice"
    return "non_authoritative_status_card"


def _api_result_class(probe_result_class: str) -> str:
    return PROBE_RESULT_TO_API_RESULT_CLASS.get(probe_result_class, "unknown")


def _api_surface_status(result_class: str, decision: Mapping[str, Any]) -> str:
    if decision.get("failure_reasons"):
        return "blocked_by_policy"
    if result_class in NEGATIVE_API_RESULT_CLASSES:
        return "negative_candidate_available"
    if result_class in METADATA_API_RESULT_CLASSES:
        return "metadata_candidate_available"
    if result_class in {"provider_probe_not_observed", "provider_probe_not_configured"}:
        return "not_configured"
    return "read_only_projection_available"


def _to_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}
