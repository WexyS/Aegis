"""Read-only Repo Audit dry-run projection API surface."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from fastapi import APIRouter

from aegis.core.repo_audit_dry_run_source_plan import (
    validate_repo_audit_dry_run_source_plan_request,
)


REPO_AUDIT_DRY_RUN_API_SURFACE_VERSION = "repo-audit-dry-run-api-surface/1"
REPO_AUDIT_DRY_RUN_API_SURFACE_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_dry_run_api_surface"
)

NO_CURRENT_PROJECTION_RESULT_CLASS = "no_projection_available"
NO_CURRENT_DRY_RUN_STATUS_CLASS = "no_current_dry_run_result"

DRY_RUN_STATUS_TO_RESULT_CLASS = {
    "dry_run_ready": "dry_run_plan_metadata_candidate",
    "dry_run_requires_operator_review": "operator_review_required_candidate",
    "dry_run_future_gated": "future_gated",
    "blocked_by_missing_required_field": "blocked_by_policy",
    "blocked_by_unsafe_related_decision": "blocked_by_policy",
    "blocked_by_execution_claim": "blocked_by_policy",
    "blocked_by_authority_claim": "blocked_by_policy",
    "blocked_by_privacy_or_exclusion": "blocked_by_policy",
    "blocked_by_truth_claim": "blocked_by_policy",
    "blocked_by_policy": "blocked_by_policy",
}

METADATA_RESULT_CLASSES = {
    "dry_run_plan_metadata_candidate",
    "source_intake_metadata_candidate",
    "source_plan_display_candidate",
    "candidate_sources_available",
    "exclusions_available",
    "blockers_available",
}

BLOCKED_RESULT_CLASSES = {"blocked_by_policy"}
FUTURE_RESULT_CLASSES = {"future_gated"}
OPERATOR_REVIEW_RESULT_CLASSES = {"operator_review_required_candidate"}

router = APIRouter(prefix="/maintenance/repo-audit/dry-run-projection", tags=["maintenance"])


@router.get("")
async def repo_audit_dry_run_projection_status() -> dict[str, Any]:
    """Return the current read-only Repo Audit dry-run projection, if one exists."""

    return build_repo_audit_dry_run_projection_api_response()


def build_repo_audit_dry_run_projection_api_response(
    *,
    projection_metadata: Mapping[str, Any] | None = None,
    dry_run_source_plan_decision: Any | None = None,
    source_plan_display_decision: Any | None = None,
) -> dict[str, Any]:
    """Build a non-authoritative dry-run projection response without source access."""

    if (
        projection_metadata is None
        and dry_run_source_plan_decision is None
        and source_plan_display_decision is None
    ):
        return _no_current_projection_response()

    if dry_run_source_plan_decision is None:
        dry_run_source_plan_decision = validate_repo_audit_dry_run_source_plan_request(
            _dry_run_source_plan_request(dict(projection_metadata or {}))
        )

    decision = _to_mapping(dry_run_source_plan_decision)
    display_decision = _to_mapping(source_plan_display_decision)
    result_class = _projection_result_class(decision, display_decision)
    api_status = _api_surface_status(result_class)
    response = _base_response(
        projection_result_class=result_class,
        api_surface_status_class=api_status,
        projection_available=True,
        current_projection_available=False,
        source_current=False,
    )
    response.update(
        {
            "dry_run_status": decision.get("dry_run_status"),
            "plan_projection_status": decision.get("plan_projection_status"),
            "candidate_projection_status": decision.get("candidate_projection_status"),
            "privacy_status": decision.get("privacy_status"),
            "completeness_status": decision.get("completeness_status"),
            "trust_status": decision.get("trust_status"),
            "freshness_status": decision.get("freshness_status"),
            "exclusion_status": decision.get("exclusion_status"),
            "raw_content_status": decision.get("raw_content_status"),
            "display_readiness_status": display_decision.get("display_readiness_status"),
            "dry_run_truth_labels": _truth_labels(result_class),
            "candidate_counts": {
                "included": int(decision.get("included_candidate_count") or 0),
                "excluded": int(decision.get("excluded_candidate_count") or 0),
                "operator_review": int(decision.get("operator_review_candidate_count") or 0),
                "future_gated": int(decision.get("future_gated_candidate_count") or 0),
            },
            "human_review_required": bool(decision.get("human_review_required")),
            "future_gated": bool(decision.get("future_gated")),
            "blocked": bool(decision.get("failure_reasons")),
            "failure_reasons": tuple(decision.get("failure_reasons") or ()),
            "source_refs": _plan_input_tuple(decision, "source_refs"),
            "provenance": _plan_input_tuple(decision, "provenance"),
            "limitations": _plan_input_tuple(decision, "limitations"),
            "unknowns": _plan_input_tuple(decision, "unknowns"),
            "api_projection_semantics": _api_projection_semantics(result_class),
            "truthfulness_classification": (
                "not_repo_read_not_source_truth_not_evidence_not_verifier_success_"
                "not_report_not_compliance_or_passport_proof"
            ),
            "action_semantics": "no_run_retry_fetch_clone_or_read_authorized_by_api_surface",
        }
    )
    return response


def _no_current_projection_response() -> dict[str, Any]:
    response = _base_response(
        projection_result_class=NO_CURRENT_PROJECTION_RESULT_CLASS,
        api_surface_status_class=NO_CURRENT_DRY_RUN_STATUS_CLASS,
        projection_available=False,
        current_projection_available=False,
        source_current=False,
    )
    response.update(
        {
            "dry_run_status": "repo_audit_dry_run_not_observed",
            "plan_projection_status": "not_observed",
            "candidate_projection_status": "not_observed",
            "privacy_status": "not_observed",
            "completeness_status": "not_observed",
            "trust_status": "not_observed",
            "freshness_status": "not_observed",
            "exclusion_status": "not_observed",
            "raw_content_status": "not_observed",
            "display_readiness_status": None,
            "dry_run_truth_labels": (
                "metadata_only",
                "not_repo_read",
                "not_source_truth",
                "not_evidence",
                "not_verifier_success",
                "not_report",
                "not_compliance_proof",
                "not_passport_proof",
            ),
            "candidate_counts": {
                "included": 0,
                "excluded": 0,
                "operator_review": 0,
                "future_gated": 0,
            },
            "human_review_required": False,
            "future_gated": False,
            "blocked": False,
            "failure_reasons": (),
            "source_refs": (),
            "provenance": (
                {
                    "ref_id": "repo-audit-dry-run-projection:current-source-unavailable",
                    "ref_type": "absence_projection",
                },
            ),
            "limitations": (
                "No durable/current Repo Audit dry-run projection source is available.",
                "Prior design examples are not replayed as current runtime state.",
            ),
            "unknowns": ("Current Repo Audit dry-run source plan state is not observed.",),
            "api_projection_semantics": (
                "no_current_dry_run_projection_available_not_repo_read_or_source_truth"
            ),
            "truthfulness_classification": (
                "not_repo_read_not_source_truth_not_evidence_not_verifier_success_"
                "not_report_not_compliance_or_passport_proof"
            ),
            "action_semantics": "no_run_retry_fetch_clone_or_read_authorized_by_api_surface",
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
        "api_surface_version": REPO_AUDIT_DRY_RUN_API_SURFACE_VERSION,
        "read_only": True,
        "projection_result_class": projection_result_class,
        "api_surface_status_class": api_surface_status_class,
        "projection_available": projection_available,
        "current_projection_available": current_projection_available,
        "source_current": source_current,
        "mutation_performed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_DRY_RUN_API_SURFACE_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_provided": False,
        "verifier_success": False,
        "frontend_authority": False,
        "api_authority": False,
        "repo_read_performed": False,
        "repo_scan_performed": False,
        "directory_scan_performed": False,
        "file_list_performed": False,
        "file_stat_performed": False,
        "file_hash_performed": False,
        "file_read_performed": False,
        "github_api_called": False,
        "github_url_fetched": False,
        "browser_fetch_performed": False,
        "raw_file_fetch_performed": False,
        "git_clone_performed": False,
        "http_request_performed": False,
        "external_api_called": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "model_call_performed": False,
        "web_query_performed": False,
        "memory_retrieval_performed": False,
        "context_retrieval_performed": False,
        "context_package_created": False,
        "cache_written": False,
        "source_record_created": False,
        "citation_record_created": False,
        "report_generated": False,
        "generated_artifact_created": False,
        "data_sent_external": False,
        "source_truth_claimed": False,
        "repo_audit_proof_claimed": False,
        "compliance_proof_claimed": False,
        "passport_proof_claimed": False,
        "runtime_state_mutated": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "replay_mutated": False,
        "api_route_added": False,
        "runtime_command_added": False,
        "scheduler_added": False,
        "action_endpoint_added": False,
        "run_authorized": False,
        "retry_authorized": False,
        "repo_read_authorized": False,
        "github_fetch_authorized": False,
        "raw_content_ingestion_allowed": False,
        "private_repo_access_allowed": False,
        "fake_current_projection_created": False,
    }


def _dry_run_source_plan_request(metadata: Mapping[str, Any]) -> dict[str, Any]:
    candidate_sources = metadata.get("candidate_sources") or (
        {
            "ref_id": "synthetic:repo-audit-dry-run-candidate",
            "source_kind": "repository_metadata",
            "disposition": "include_candidate_metadata_only",
            "privacy_class": metadata.get("privacy_class", "public_metadata"),
            "trust_class": metadata.get("trust_class", "backend_supplied_metadata"),
            "freshness_class": metadata.get("freshness_class", "commit_pinned"),
        },
    )
    return {
        "request_id": str(metadata.get("request_id") or "repo-audit-dry-run-api-surface:fixture"),
        "dry_run_plan_class": str(metadata.get("dry_run_plan_class") or "github_repo_source_plan"),
        "plan_operation": str(metadata.get("plan_operation") or "project_candidate_sources"),
        "plan_status_class": str(metadata.get("plan_status_class") or "metadata_only_projection"),
        "projection_completeness_class": str(
            metadata.get("projection_completeness_class") or "bounded_metadata_only"
        ),
        "privacy_class": str(metadata.get("privacy_class") or "public_metadata"),
        "trust_class": str(metadata.get("trust_class") or "backend_supplied_metadata"),
        "freshness_class": str(metadata.get("freshness_class") or "commit_pinned"),
        "namespace": str(metadata.get("namespace") or "repo_audit_dry_run_api_surface"),
        "source_refs": metadata.get("source_refs")
        or [{"ref_id": "synthetic:repo-audit-dry-run-source", "ref_type": "test_fixture"}],
        "provenance": metadata.get("provenance")
        or [{"ref_id": "caller-supplied-dry-run-projection-metadata", "ref_type": "synthetic_fixture"}],
        "candidate_sources": candidate_sources,
        "exclusion_classes": metadata.get("exclusion_classes") or _required_exclusion_classes(),
        "limitations": tuple(metadata.get("limitations") or ("caller-supplied fixture only",)),
        "unknowns": tuple(metadata.get("unknowns") or ()),
        "human_review_required": bool(metadata.get("human_review_required", False)),
        "project_or_repository_scoped": bool(metadata.get("project_or_repository_scoped", False)),
        "memory_derived_context": bool(metadata.get("memory_derived_context", False)),
        "raw_content_requested": bool(metadata.get("raw_content_requested", False)),
        "complete_repo_plan_claimed": bool(metadata.get("complete_repo_plan_claimed", False)),
        "authority": bool(metadata.get("authority") or metadata.get("api_authority")),
        "local_repo_read_performed": bool(
            metadata.get("local_repo_read_performed") or metadata.get("repo_read_performed")
        ),
        **_forward_safety_flags(metadata),
    }


def _required_exclusion_classes() -> tuple[str, ...]:
    return (
        "secrets_excluded",
        "credentials_excluded",
        "env_files_excluded",
        "private_keys_excluded",
        "generated_artifacts_excluded",
        "build_outputs_excluded",
        "dependency_vendor_dirs_excluded",
        "model_files_excluded",
        "vector_db_files_excluded",
        "runtime_journals_excluded",
        "raw_evidence_files_excluded",
    )


def _forward_safety_flags(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: metadata[key]
        for key in (
            "runtime_dispatch_allowed",
            "mutation_performed",
            "frontend_authority",
            "api_authority",
            "approval_grant",
            "capability_grant",
            "lease_grant",
            "evidence_created",
            "evidence_provided",
            "verifier_success",
            "github_api_called",
            "github_url_fetched",
            "browser_fetch_performed",
            "raw_file_fetch_performed",
            "git_clone_performed",
            "local_repo_read_performed",
            "repo_read_performed",
            "repo_scan_performed",
            "directory_scan_performed",
            "file_list_performed",
            "file_stat_performed",
            "file_hash_performed",
            "file_read_performed",
            "http_request_performed",
            "external_api_called",
            "mcp_call_performed",
            "tool_call_performed",
            "model_call_performed",
            "web_query_performed",
            "memory_retrieval_performed",
            "context_retrieval_performed",
            "context_package_created",
            "cache_written",
            "source_record_created",
            "citation_record_created",
            "report_generated",
            "generated_artifact_created",
            "data_sent_external",
            "source_truth_claimed",
            "repo_audit_proof_claimed",
            "compliance_proof_claimed",
            "passport_proof_claimed",
            "runtime_state_mutated",
            "journal_mutated",
            "evidence_mutated",
            "replay_mutated",
            "private_repo_access_allowed",
            "raw_content_ingestion_allowed",
        )
        if key in metadata
    }


def _projection_result_class(
    decision: Mapping[str, Any],
    display_decision: Mapping[str, Any],
) -> str:
    if display_decision and not display_decision.get("failure_reasons"):
        status = str(display_decision.get("display_readiness_status") or "")
        if status == "display_ready_metadata_only":
            return "source_plan_display_candidate"
    if decision.get("failure_reasons"):
        return "blocked_by_policy"
    if decision.get("future_gated"):
        return "future_gated"
    if decision.get("human_review_required") or int(decision.get("operator_review_candidate_count") or 0):
        return "operator_review_required_candidate"
    if int(decision.get("excluded_candidate_count") or 0):
        return "exclusions_available"
    if int(decision.get("included_candidate_count") or 0):
        return "candidate_sources_available"
    status = str(decision.get("dry_run_status") or "")
    return DRY_RUN_STATUS_TO_RESULT_CLASS.get(status, "unknown")


def _api_surface_status(result_class: str) -> str:
    if result_class == NO_CURRENT_PROJECTION_RESULT_CLASS:
        return NO_CURRENT_DRY_RUN_STATUS_CLASS
    if result_class in BLOCKED_RESULT_CLASSES:
        return "blocked_by_policy"
    if result_class in FUTURE_RESULT_CLASSES:
        return "future_gated"
    if result_class in OPERATOR_REVIEW_RESULT_CLASSES:
        return "metadata_candidate_available"
    if result_class in METADATA_RESULT_CLASSES:
        return "metadata_candidate_available"
    return "read_only_projection_available"


def _truth_labels(result_class: str) -> tuple[str, ...]:
    labels = [
        "metadata_only",
        "candidate_only",
        "not_repo_read",
        "not_source_truth",
        "not_evidence",
        "not_verifier_success",
        "not_report",
        "not_compliance_proof",
        "not_passport_proof",
    ]
    if result_class == "operator_review_required_candidate":
        labels.append("operator_review_required")
    if result_class == "future_gated":
        labels.append("future_gated")
    return tuple(labels)


def _api_projection_semantics(result_class: str) -> str:
    if result_class == "blocked_by_policy":
        return "blocked_metadata_projection_only_not_permission_or_execution"
    if result_class == "future_gated":
        return "future_gated_metadata_projection_only_not_permission_or_execution"
    if result_class == "operator_review_required_candidate":
        return "operator_review_metadata_projection_only_not_run_authorization"
    return "dry_run_metadata_projection_only_not_repo_read_or_source_truth"


def _plan_input_tuple(decision: Mapping[str, Any], field: str) -> tuple[Any, ...]:
    plan_input = decision.get("plan_input")
    if isinstance(plan_input, Mapping):
        value = plan_input.get(field)
        if value is None:
            return ()
        if isinstance(value, tuple):
            return value
        if isinstance(value, list):
            return tuple(value)
        return (value,)
    return ()


def _to_mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}
