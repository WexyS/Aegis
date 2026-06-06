from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_VERSION = "repo-audit-dry-run-surface-display/1"
REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_dry_run_surface_display"
)

SURFACE_DISPLAY_SOURCE_CLASSES = {
    "repo_audit_dry_run_projection_api",
    "repo_audit_dry_run_source_plan",
    "repo_audit_source_intake",
    "repo_audit_source_plan_display",
    "synthetic_fixture",
    "mission_control_future",
    "maintenance_scan_future",
    "cli_summary_future",
    "unknown",
}

SURFACE_DISPLAY_STATE_CLASSES = {
    "no_projection_available",
    "repo_audit_dry_run_not_observed",
    "repo_audit_dry_run_not_configured",
    "dry_run_plan_metadata_candidate",
    "source_intake_metadata_candidate",
    "source_plan_display_candidate",
    "candidate_sources_available",
    "exclusions_available",
    "blockers_available",
    "operator_review_required_candidate",
    "future_gated",
    "blocked_by_policy",
    "unknown",
}

UI_MEANING_CLASSES = {
    "neutral_no_data",
    "informational_candidate",
    "exclusion_metadata",
    "blocked_notice",
    "future_gated_notice",
    "operator_review_required",
    "warning_attention",
    "unknown",
}

FORBIDDEN_UI_MEANINGS = {
    "repo_read_performed",
    "source_truth_verified",
    "source_available_verified",
    "evidence_available",
    "verifier_success",
    "report_generated",
    "compliance_proof",
    "passport_proof",
    "run_authorized",
    "execution_ready",
    "cleanup_performed",
    "deletion_performed",
    "frontend_authority",
}

DISPLAY_SEVERITY_CLASSES = {
    "neutral",
    "info",
    "attention",
    "warning",
    "blocked",
    "future",
    "unknown",
}

NO_DATA_STATES = {
    "no_projection_available",
    "repo_audit_dry_run_not_observed",
    "repo_audit_dry_run_not_configured",
}

METADATA_CANDIDATE_STATES = {
    "dry_run_plan_metadata_candidate",
    "source_intake_metadata_candidate",
    "source_plan_display_candidate",
    "candidate_sources_available",
}

RECOMMENDED_WORDING_BY_STATE = {
    "no_projection_available": "No current repo-audit dry-run projection is available.",
    "repo_audit_dry_run_not_observed": "Repo-audit dry-run has not been observed.",
    "repo_audit_dry_run_not_configured": "Repo-audit dry-run is not configured.",
    "candidate_sources_available": "Candidate sources only; not source truth or repo read.",
    "exclusions_available": "Exclusion metadata only; no cleanup or deletion performed.",
    "blockers_available": "Blocked items remain blocked; not permission.",
    "future_gated": "Future-gated; not execution-ready.",
    "operator_review_required_candidate": "Operator review required; run is not authorized.",
    "dry_run_plan_metadata_candidate": "Metadata candidate only; not evidence or verifier success.",
    "source_intake_metadata_candidate": "Metadata candidate only; not evidence or verifier success.",
    "source_plan_display_candidate": "Metadata candidate only; not evidence or verifier success.",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "frontend_authority": "frontend_authority_not_allowed",
    "api_authority": "api_authority_not_allowed",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_display": "display_cannot_provide_evidence",
    "evidence_provided": "display_cannot_provide_evidence",
    "evidence_created": "display_cannot_provide_evidence",
    "verifier_success": "display_cannot_mark_verifier_success",
    "verified_success": "display_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "run_authorized": "run_authorization_denied",
    "retry_authorized": "retry_authorization_denied",
    "run_control_exposed": "run_control_exposure_denied",
    "retry_control_exposed": "retry_control_exposure_denied",
    "action_control_exposed": "action_control_exposure_denied",
    "source_truth_claimed": "source_truth_claim_denied",
    "source_available_verified": "source_availability_verification_denied",
    "repo_audit_proof_claimed": "repo_audit_proof_claim_denied",
    "compliance_proof_claimed": "compliance_proof_claim_denied",
    "passport_proof_claimed": "passport_proof_claim_denied",
    "cleanup_performed": "cleanup_claim_denied",
    "deletion_performed": "deletion_claim_denied",
    "fake_current_projection_created": "fake_current_projection_denied",
    "fake_source_truth_created": "fake_source_truth_denied",
    "fake_success_created": "fake_success_denied",
    "fake_verification_created": "fake_verification_denied",
    "display_severity_is_backend_truth": "display_backend_truth_claim_denied",
    "candidate_source_is_verified": "candidate_source_verification_claim_denied",
    "exclusion_is_cleanup_or_deletion": "exclusion_cleanup_claim_denied",
    "blocker_is_permission": "blocker_permission_claim_denied",
    "future_gated_is_execution_ready": "future_gated_execution_ready_claim_denied",
    "operator_review_is_run_authorization": "operator_review_run_authorization_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "repo_read_performed": "repo_read_denied",
    "local_repo_read_performed": "repo_read_denied",
    "repo_scan_performed": "repo_scan_denied",
    "directory_scan_performed": "directory_scan_denied",
    "file_list_performed": "file_list_denied",
    "file_stat_performed": "file_stat_denied",
    "file_hash_performed": "file_hash_denied",
    "file_read_performed": "file_read_denied",
    "github_api_called": "github_api_call_denied",
    "github_url_fetched": "github_url_fetch_denied",
    "browser_fetch_performed": "browser_fetch_denied",
    "raw_file_fetch_performed": "raw_file_fetch_denied",
    "git_clone_performed": "git_clone_denied",
    "http_request_performed": "http_request_denied",
    "external_api_called": "external_api_call_denied",
    "model_call_performed": "model_call_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "web_query_performed": "web_query_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "context_package_created": "context_package_creation_denied",
    "cache_written": "cache_write_denied",
    "source_record_created": "source_record_creation_denied",
    "citation_record_created": "citation_record_creation_denied",
    "report_generated": "report_generation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "data_sent_external": "external_data_transfer_denied",
}


@dataclass(frozen=True)
class RepoAuditDryRunSurfaceDisplayFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditDryRunSurfaceDisplayInput:
    request_id: str | None
    surface_display_source_class: str | None
    surface_display_state_class: str | None
    ui_meaning_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    display_wording_candidate: str | None
    display_severity_class: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RelatedRepoAuditDryRunSurfaceDisplayReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class RepoAuditDryRunSurfaceDisplayDecision:
    contract_version: str
    display_readiness_status: str
    request_id: str | None
    surface_display_source_class: str | None
    surface_display_state_class: str | None
    ui_meaning_class: str | None
    namespace: str | None
    display_severity_class: str
    recommended_wording: str
    run_guidance: str
    truthfulness_classification: str
    color_semantics: str
    related_references: tuple[RelatedRepoAuditDryRunSurfaceDisplayReference, ...]
    required_operator_actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...]
    display_input: RepoAuditDryRunSurfaceDisplayInput | None
    authority: bool = False
    frontend_authority: bool = False
    api_authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_display: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    run_authorized: bool = False
    retry_authorized: bool = False
    run_control_exposed: bool = False
    retry_control_exposed: bool = False
    action_control_exposed: bool = False
    repo_read_performed: bool = False
    repo_scan_performed: bool = False
    directory_scan_performed: bool = False
    file_list_performed: bool = False
    file_stat_performed: bool = False
    file_hash_performed: bool = False
    file_read_performed: bool = False
    github_api_called: bool = False
    github_url_fetched: bool = False
    browser_fetch_performed: bool = False
    raw_file_fetch_performed: bool = False
    git_clone_performed: bool = False
    http_request_performed: bool = False
    external_api_called: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    mcp_call_performed: bool = False
    web_query_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    context_package_created: bool = False
    cache_written: bool = False
    source_record_created: bool = False
    citation_record_created: bool = False
    report_generated: bool = False
    generated_artifact_created: bool = False
    source_truth_claimed: bool = False
    repo_audit_proof_claimed: bool = False
    compliance_proof_claimed: bool = False
    passport_proof_claimed: bool = False
    cleanup_performed: bool = False
    deletion_performed: bool = False
    fake_current_projection_created: bool = False
    fake_source_truth_created: bool = False
    fake_success_created: bool = False
    fake_verification_created: bool = False
    data_sent_external: bool = False
    read_only_projection: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


def validate_repo_audit_dry_run_surface_display_request(
    request: Mapping[str, Any] | None,
    *,
    repo_audit_dry_run_api_surface_decision: Any | None = None,
    repo_audit_dry_run_source_plan_decision: Any | None = None,
    repo_audit_source_intake_decision: Any | None = None,
    repo_audit_source_plan_display_decision: Any | None = None,
    github_source_connector_decision: Any | None = None,
    web_research_gateway_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
) -> RepoAuditDryRunSurfaceDisplayDecision:
    """Validate Repo Audit dry-run display metadata without UI authority or source access."""

    if not isinstance(request, Mapping):
        failure = RepoAuditDryRunSurfaceDisplayFailure(
            reason="missing_request",
            field="request",
            message="Repo Audit dry-run surface display requires caller-supplied metadata",
        )
        return _decision(display_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[RepoAuditDryRunSurfaceDisplayFailure] = []
    related_references: list[RelatedRepoAuditDryRunSurfaceDisplayReference] = []

    _validate_forbidden_claims("request", data, failures)
    _validate_forbidden_ui_meaning(data, failures)
    for label, decision in {
        "repo_audit_dry_run_api_surface": repo_audit_dry_run_api_surface_decision,
        "repo_audit_dry_run_source_plan": repo_audit_dry_run_source_plan_decision,
        "repo_audit_source_intake": repo_audit_source_intake_decision,
        "repo_audit_source_plan_display": repo_audit_source_plan_display_decision,
        "github_source_connector": github_source_connector_decision,
        "web_research_gateway": web_research_gateway_decision,
        "context_policy": context_policy_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "capability_lease": capability_lease_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "mission_control": mission_control_decision,
        "passive_observe": passive_observe_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    display_input = RepoAuditDryRunSurfaceDisplayInput(
        request_id=_text(data.get("request_id")),
        surface_display_source_class=_text(data.get("surface_display_source_class")),
        surface_display_state_class=_normalized_state(data),
        ui_meaning_class=_text(data.get("ui_meaning_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        display_wording_candidate=_text(data.get("display_wording_candidate")),
        display_severity_class=_text(data.get("display_severity_class")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(display_input, failures)
    _validate_display_semantics(display_input, failures)
    _validate_wording(display_input, failures)

    return _decision(
        display_input=display_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    related_references: tuple[RelatedRepoAuditDryRunSurfaceDisplayReference, ...],
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> RepoAuditDryRunSurfaceDisplayDecision:
    return RepoAuditDryRunSurfaceDisplayDecision(
        contract_version=REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_VERSION,
        display_readiness_status=_display_readiness_status(display_input, failures),
        request_id=display_input.request_id if display_input else None,
        surface_display_source_class=display_input.surface_display_source_class if display_input else None,
        surface_display_state_class=display_input.surface_display_state_class if display_input else None,
        ui_meaning_class=display_input.ui_meaning_class if display_input else None,
        namespace=display_input.namespace if display_input else None,
        display_severity_class=_display_severity(display_input, failures),
        recommended_wording=_recommended_wording(display_input, failures),
        run_guidance=_run_guidance(display_input, failures),
        truthfulness_classification=_truthfulness_classification(display_input, failures),
        color_semantics=_color_semantics(display_input, failures),
        related_references=related_references,
        required_operator_actions=_required_operator_actions(display_input, failures),
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        display_input=display_input,
    )


def _validate_required(
    display_input: RepoAuditDryRunSurfaceDisplayInput,
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
) -> None:
    required = {
        "request_id": display_input.request_id,
        "surface_display_source_class": display_input.surface_display_source_class,
        "surface_display_state_class": display_input.surface_display_state_class,
        "ui_meaning_class": display_input.ui_meaning_class,
        "namespace": display_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (display_input.source_refs or display_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "source refs or provenance are required",
        )
    if (
        display_input.surface_display_source_class
        and display_input.surface_display_source_class not in SURFACE_DISPLAY_SOURCE_CLASSES
    ):
        _add_failure(failures, "unsupported_surface_display_source_class", "surface_display_source_class", "surface display source class is not recognized")
    if (
        display_input.surface_display_state_class
        and display_input.surface_display_state_class not in SURFACE_DISPLAY_STATE_CLASSES
    ):
        _add_failure(failures, "unsupported_surface_display_state_class", "surface_display_state_class", "surface display state class is not recognized")
    if display_input.ui_meaning_class and display_input.ui_meaning_class not in UI_MEANING_CLASSES:
        _add_failure(failures, "unsupported_ui_meaning_class", "ui_meaning_class", "UI meaning class is not recognized or is forbidden")
    if display_input.display_severity_class and display_input.display_severity_class not in DISPLAY_SEVERITY_CLASSES:
        _add_failure(failures, "unsupported_display_severity_class", "display_severity_class", "display severity class is not recognized")


def _validate_display_semantics(
    display_input: RepoAuditDryRunSurfaceDisplayInput,
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
) -> None:
    source = display_input.surface_display_source_class
    state = display_input.surface_display_state_class
    meaning = display_input.ui_meaning_class
    severity = display_input.display_severity_class

    if source == "unknown":
        _add_failure(failures, "unknown_surface_display_source_blocked", "surface_display_source_class", "unknown display source requires clarification")
    if state == "unknown":
        _add_failure(failures, "unknown_surface_display_state_blocked", "surface_display_state_class", "unknown display state requires clarification")
    if meaning == "unknown":
        _add_failure(failures, "unknown_ui_meaning_blocked", "ui_meaning_class", "unknown UI meaning requires clarification")

    if state in NO_DATA_STATES:
        if meaning != "neutral_no_data":
            _add_failure(failures, "no_data_state_requires_neutral_meaning", "ui_meaning_class", "no projection and not-observed states must be neutral no-data displays")
        if severity and severity not in {"neutral", "info"}:
            _add_failure(failures, "no_data_state_severity_overstated", "display_severity_class", "no-data Repo Audit display must not be warning, blocked, or failure severity")
    if state in METADATA_CANDIDATE_STATES:
        if meaning != "informational_candidate":
            _add_failure(failures, "candidate_state_requires_informational_meaning", "ui_meaning_class", "metadata and candidate source states must be informational candidates only")
        if severity and severity not in {"neutral", "info"}:
            _add_failure(failures, "candidate_state_severity_overstated", "display_severity_class", "candidate sources must not be displayed as verified source truth")
    if state == "exclusions_available":
        if meaning != "exclusion_metadata":
            _add_failure(failures, "exclusion_state_requires_exclusion_metadata", "ui_meaning_class", "exclusions are metadata only, not cleanup or deletion")
        if severity and severity not in {"neutral", "info"}:
            _add_failure(failures, "exclusion_state_severity_overstated", "display_severity_class", "exclusion metadata must not be displayed as cleanup success or source failure")
    if state in {"blockers_available", "blocked_by_policy"}:
        if meaning != "blocked_notice":
            _add_failure(failures, "blocked_state_requires_blocked_notice", "ui_meaning_class", "blocked items must remain blocked notices, not permission")
        if severity and severity not in {"warning", "blocked", "attention"}:
            _add_failure(failures, "blocked_state_severity_required", "display_severity_class", "blocked items should remain warning, attention, or blocked display metadata")
    if state == "future_gated":
        if meaning != "future_gated_notice":
            _add_failure(failures, "future_gated_state_requires_future_notice", "ui_meaning_class", "future-gated items must not become execution-ready")
        if severity and severity not in {"future", "neutral", "info"}:
            _add_failure(failures, "future_gated_state_severity_overstated", "display_severity_class", "future-gated items must not be displayed as execution failure or success")
    if state == "operator_review_required_candidate":
        if meaning != "operator_review_required":
            _add_failure(failures, "operator_review_state_requires_review_meaning", "ui_meaning_class", "operator-review candidates must not become run authorization")
        if severity and severity not in {"attention", "warning"}:
            _add_failure(failures, "operator_review_state_severity_required", "display_severity_class", "operator-review candidates should remain attention or warning display metadata")


def _validate_wording(
    display_input: RepoAuditDryRunSurfaceDisplayInput,
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
) -> None:
    wording = display_input.display_wording_candidate
    if not wording:
        return
    lowered = wording.lower()
    forbidden_fragments = {
        "repo read performed": "display_wording_repo_read_claim_denied",
        "source truth verified": "display_wording_source_truth_claim_denied",
        "source available verified": "display_wording_source_availability_claim_denied",
        "evidence available": "display_wording_evidence_claim_denied",
        "verifier success": "display_wording_verifier_claim_denied",
        "report generated": "display_wording_report_claim_denied",
        "compliance proof": "display_wording_compliance_claim_denied",
        "passport proof": "display_wording_passport_claim_denied",
        "run authorized": "display_wording_run_authorization_denied",
        "execution ready": "display_wording_execution_ready_claim_denied",
        "cleanup performed": "display_wording_cleanup_claim_denied",
        "deletion performed": "display_wording_deletion_claim_denied",
    }
    for fragment, reason in forbidden_fragments.items():
        if fragment in lowered:
            _add_failure(
                failures,
                reason,
                "display_wording_candidate",
                "display wording cannot claim repo reads, source truth, evidence, verifier success, report generation, proof, run authorization, execution readiness, cleanup, or deletion",
            )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
    related_references: list[RelatedRepoAuditDryRunSurfaceDisplayReference],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot authorize repo reads, source truth, run controls, cleanup, reports, evidence, verifier success, authority, or grants",
        )
    related_references.append(
        RelatedRepoAuditDryRunSurfaceDisplayReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, source truth, proof, fake status, run authorization, cleanup, or deletion",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot read repos, call GitHub/web/API, fetch, clone, list, stat, hash, read files, create context, report, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "Repo Audit dry-run surface display cannot grant execution permission",
            )


def _validate_forbidden_ui_meaning(
    data: Mapping[str, Any],
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
) -> None:
    meaning = _text(data.get("ui_meaning_class"))
    if meaning in FORBIDDEN_UI_MEANINGS:
        _add_failure(
            failures,
            "forbidden_ui_meaning_denied",
            "ui_meaning_class",
            "UI meaning cannot claim repo read, source truth, evidence, verifier success, report generation, proof, run authorization, cleanup, deletion, execution readiness, or frontend authority",
        )


def _display_readiness_status(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        state = display_input.surface_display_state_class
        if state in NO_DATA_STATES:
            return "display_ready_neutral_no_data"
        if state in METADATA_CANDIDATE_STATES:
            return "display_ready_informational_candidate"
        if state == "exclusions_available":
            return "display_ready_exclusion_metadata"
        if state in {"blockers_available", "blocked_by_policy"}:
            return "display_ready_blocked_notice"
        if state == "future_gated":
            return "display_ready_future_gated"
        if state == "operator_review_required_candidate":
            return "display_ready_operator_review"
        return "display_ready"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_unsafe_related_decision"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_missing_required_field"
    if any("wording" in reason or "truth" in reason or "proof" in reason or "verifier" in reason or "evidence" in reason or "available" in reason for reason in reasons):
        return "blocked_by_truthfulness_claim"
    if any("run_" in reason or "retry" in reason or "control" in reason or "execution_ready" in reason for reason in reasons):
        return "blocked_by_run_or_action_claim"
    if any("cleanup" in reason or "deletion" in reason for reason in reasons):
        return "blocked_by_cleanup_or_deletion_claim"
    if any("read" in reason or "scan" in reason or "list" in reason or "stat" in reason or "hash" in reason or "fetch" in reason or "clone" in reason or "http" in reason or "call" in reason or "context" in reason or "report" in reason for reason in reasons):
        return "blocked_by_execution_claim"
    if any("grant" in reason or "authority" in reason or "dispatch" in reason for reason in reasons):
        return "blocked_by_authority_claim"
    return "blocked_by_display_policy"


def _display_severity(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_severity_class:
        return display_input.display_severity_class
    state = display_input.surface_display_state_class
    if state in NO_DATA_STATES:
        return "neutral"
    if state in METADATA_CANDIDATE_STATES or state == "exclusions_available":
        return "info"
    if state in {"blockers_available", "blocked_by_policy"}:
        return "warning"
    if state == "future_gated":
        return "future"
    if state == "operator_review_required_candidate":
        return "attention"
    return "unknown"


def _recommended_wording(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "Display is blocked until required metadata and truthfulness constraints are satisfied."
    state = display_input.surface_display_state_class or "unknown"
    return RECOMMENDED_WORDING_BY_STATE.get(
        state,
        "Repo-audit dry-run display state is unknown and requires review.",
    )


def _run_guidance(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.surface_display_state_class == "operator_review_required_candidate":
        return "Operator review required; run is not authorized."
    return "No run, retry, fetch, clone, or read is authorized by Repo Audit dry-run surface display."


def _truthfulness_classification(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    return (
        "display_not_repo_read_not_source_truth_not_evidence_not_verifier_success_"
        "not_report_not_compliance_or_passport_proof_not_run_authorization"
    )


def _color_semantics(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked_display_not_backend_truth"
    state = display_input.surface_display_state_class
    if state in NO_DATA_STATES:
        return "neutral_not_failure"
    if state in METADATA_CANDIDATE_STATES:
        return "info_not_verified_source"
    if state == "exclusions_available":
        return "info_not_cleanup_success"
    if state in {"blockers_available", "blocked_by_policy"}:
        return "warning_not_permission"
    if state == "future_gated":
        return "future_not_execution_ready"
    if state == "operator_review_required_candidate":
        return "attention_not_run_authorized"
    return "unknown_requires_review"


def _required_operator_actions(
    display_input: RepoAuditDryRunSurfaceDisplayInput | None,
    failures: tuple[RepoAuditDryRunSurfaceDisplayFailure, ...],
) -> tuple[str, ...]:
    if display_input is None or failures:
        return ()
    state = display_input.surface_display_state_class
    actions: list[str] = []
    if state in {"operator_review_required_candidate", "blockers_available", "blocked_by_policy", "future_gated", "unknown"}:
        actions.append("operator_review_recommended")
    if state == "operator_review_required_candidate":
        actions.append("run_requires_separate_authorization")
    return tuple(dict.fromkeys(actions))


def _normalized_state(data: Mapping[str, Any]) -> str | None:
    explicit = _text(data.get("surface_display_state_class"))
    if explicit:
        return explicit
    projection_result = _text(data.get("projection_result_class"))
    dry_run_status = _text(data.get("dry_run_status"))
    if projection_result:
        return projection_result
    if dry_run_status:
        return dry_run_status
    return None


def _related_status(decision: Any) -> str | None:
    for field in (
        "display_readiness_status",
        "api_surface_status_class",
        "dry_run_status",
        "intake_status",
        "connector_status",
        "readiness_status",
        "policy_status",
        "scope_status",
        "governance_status",
        "passport_status",
        "compliance_status",
        "mission_status",
        "lifecycle_state",
    ):
        value = _field_value(decision, field)
        if value is not None:
            return str(value)
    return None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if source is None:
        return None
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "allowed", "grant"}
    return bool(value)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (deepcopy(dict(value)),)
    if isinstance(value, (list, tuple)):
        return tuple(deepcopy(dict(item)) for item in value if isinstance(item, Mapping))
    return ()


def _add_failure(
    failures: list[RepoAuditDryRunSurfaceDisplayFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditDryRunSurfaceDisplayFailure(reason=reason, field=field, message=message))
