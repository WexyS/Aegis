from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_SOURCE_PLAN_DISPLAY_VERSION = "repo-audit-source-plan-display-readiness/1"
REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_source_plan_display"
)

DISPLAY_SURFACE_CLASSES = {
    "ui_panel_future",
    "cli_summary_future",
    "mission_control_card_future",
    "audit_query_projection_future",
    "report_preview_future",
    "operator_review_queue_future",
    "unknown",
}

DISPLAY_INTENT_CLASSES = {
    "summarize_dry_run_plan",
    "show_candidate_sources",
    "show_exclusions",
    "show_blockers",
    "show_operator_review_items",
    "show_future_gates",
    "show_privacy_boundaries",
    "show_trust_freshness_completeness",
    "show_provenance_refs",
    "show_non_authority_notice",
    "unknown",
}

DISPLAY_STATUS_CLASSES = {
    "display_ready_metadata_only",
    "requires_dry_run_source_plan",
    "requires_operator_review",
    "blocked_by_privacy",
    "blocked_by_unknown_scope",
    "blocked_by_missing_provenance",
    "future_gated",
    "unavailable",
    "unknown",
}

DISPLAY_TRUTH_LABELS = {
    "metadata_only",
    "candidate_only",
    "excluded_by_policy",
    "blocked",
    "future_gated",
    "operator_review_required",
    "bounded_projection",
    "stale_or_unverified",
    "low_trust",
    "unavailable",
    "unknown",
}

DISPLAY_RISK_LABELS = {"info", "low", "medium", "high", "critical", "unknown"}

LOW_TRUST_LABELS = {"low_trust", "stale_or_unverified", "unknown"}
REVIEW_TRUTH_LABELS = {"operator_review_required", "future_gated", "blocked", "unavailable", "unknown"}
BLOCKED_TRUTH_LABELS = {"blocked", "excluded_by_policy", "unavailable"}
FUTURE_GATED_SURFACES = {
    "ui_panel_future",
    "cli_summary_future",
    "mission_control_card_future",
    "audit_query_projection_future",
    "report_preview_future",
    "operator_review_queue_future",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_display": "display_cannot_provide_evidence",
    "evidence_created": "display_cannot_provide_evidence",
    "verifier_success": "display_cannot_mark_verifier_success",
    "verified_success": "display_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "cli_authority": "cli_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "cli_result_is_authority": "cli_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "frontend_output_is_truth": "frontend_output_truth_claim_denied",
    "cli_output_is_truth": "cli_output_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "source_truth_claimed": "source_truth_claim_denied",
    "repo_audit_proof_claimed": "repo_audit_proof_claim_denied",
    "compliance_proof_claimed": "compliance_proof_claim_denied",
    "passport_proof_claimed": "passport_proof_claim_denied",
    "private_repo_access_allowed": "private_repo_access_permission_denied",
    "raw_content_ingestion_allowed": "raw_content_ingestion_denied",
    "display_overclaims_authority": "display_overclaim_denied",
    "display_claims_source_truth": "display_source_truth_claim_denied",
    "display_claims_repo_read": "display_repo_read_claim_denied",
    "display_claims_evidence": "display_evidence_claim_denied",
    "display_claims_verifier_success": "display_verifier_claim_denied",
    "display_claims_permission": "display_permission_claim_denied",
    "display_claims_deleted": "display_deletion_claim_denied",
    "display_claims_cleaned": "display_cleanup_claim_denied",
    "display_claims_deleted_or_cleaned": "display_cleanup_claim_denied",
    "display_claims_available": "display_availability_claim_denied",
    "display_claims_permitted": "display_permission_claim_denied",
    "display_claims_complete_repo_plan": "bounded_projection_complete_claim_denied",
    "low_trust_shown_as_authority": "low_trust_authority_claim_denied",
    "bounded_projection_claims_complete": "bounded_projection_complete_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "ui_render_performed": "ui_render_denied",
    "cli_output_performed": "cli_output_denied",
    "report_generated": "report_generation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "github_api_called": "github_api_call_denied",
    "github_url_fetched": "github_url_fetch_denied",
    "browser_fetch_performed": "browser_fetch_denied",
    "raw_file_fetch_performed": "raw_file_fetch_denied",
    "git_clone_performed": "git_clone_denied",
    "local_repo_read_performed": "local_repo_read_denied",
    "repo_scan_performed": "repo_scan_denied",
    "directory_scan_performed": "directory_scan_denied",
    "file_list_performed": "file_list_denied",
    "file_stat_performed": "file_stat_denied",
    "file_hash_performed": "file_hash_denied",
    "file_read_performed": "file_read_denied",
    "http_request_performed": "http_request_denied",
    "external_api_called": "external_api_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
    "model_call_performed": "model_call_denied",
    "web_query_performed": "web_query_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "context_package_created": "context_package_creation_denied",
    "cache_written": "cache_write_denied",
    "source_record_created": "source_record_creation_denied",
    "citation_record_created": "citation_record_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
}

FORBIDDEN_BEHAVIOR_REASONS = set(FORBIDDEN_BEHAVIOR_FIELDS.values())


@dataclass(frozen=True)
class RepoAuditSourcePlanDisplayFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedRepoAuditSourcePlanDisplayReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class RepoAuditSourcePlanDisplayInput:
    request_id: str | None
    display_surface_class: str | None
    display_intent_class: str | None
    display_status_class: str | None
    display_truth_label: str | None
    display_risk_label: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    dry_run_source_plan_refs: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    memory_derived_context: bool
    project_or_repository_scoped: bool
    private_display_metadata: bool


@dataclass(frozen=True)
class RepoAuditSourcePlanDisplayDecision:
    contract_version: str
    display_readiness_status: str
    request_id: str | None
    display_surface_class: str | None
    display_intent_class: str | None
    display_status_class: str | None
    display_truth_label: str | None
    display_risk_label: str | None
    namespace: str | None
    display_projection_status: str
    truth_label_status: str
    risk_label_status: str
    non_authority_notice_status: str
    source_ref_display_status: str
    operator_review_status: str
    human_review_required: bool
    future_gated: bool
    lower_trust_display: bool
    related_references: tuple[RelatedRepoAuditSourcePlanDisplayReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditSourcePlanDisplayFailure, ...]
    display_input: RepoAuditSourcePlanDisplayInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_display: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    cli_authority: bool = False
    ui_render_performed: bool = False
    cli_output_performed: bool = False
    report_generated: bool = False
    generated_artifact_created: bool = False
    github_api_called: bool = False
    github_url_fetched: bool = False
    browser_fetch_performed: bool = False
    raw_file_fetch_performed: bool = False
    git_clone_performed: bool = False
    local_repo_read_performed: bool = False
    repo_scan_performed: bool = False
    directory_scan_performed: bool = False
    file_list_performed: bool = False
    file_stat_performed: bool = False
    file_hash_performed: bool = False
    file_read_performed: bool = False
    http_request_performed: bool = False
    external_api_called: bool = False
    mcp_call_performed: bool = False
    tool_call_performed: bool = False
    model_call_performed: bool = False
    web_query_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    context_package_created: bool = False
    cache_written: bool = False
    source_record_created: bool = False
    citation_record_created: bool = False
    data_sent_external: bool = False
    private_repo_access_allowed: bool = False
    raw_content_ingestion_allowed: bool = False
    source_truth_claimed: bool = False
    repo_audit_proof_claimed: bool = False
    compliance_proof_claimed: bool = False
    passport_proof_claimed: bool = False
    display_overclaims_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_repo_audit_source_plan_display_request(
    request: Mapping[str, Any] | None,
    *,
    repo_audit_dry_run_source_plan_decision: Any | None = None,
    repo_audit_source_intake_decision: Any | None = None,
    github_source_connector_decision: Any | None = None,
    web_research_gateway_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    audit_query_layer_decision: Any | None = None,
    action_attribution_decision: Any | None = None,
    system_drift_integrity_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> RepoAuditSourcePlanDisplayDecision:
    """Validate display metadata without rendering UI, CLI output, or source access."""

    if not isinstance(request, Mapping):
        failure = RepoAuditSourcePlanDisplayFailure(
            reason="missing_request",
            field="request",
            message="Repo Audit source plan display requires caller-supplied metadata",
        )
        return _decision(display_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[RepoAuditSourcePlanDisplayFailure] = []
    related_references: list[RelatedRepoAuditSourcePlanDisplayReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "repo_audit_dry_run_source_plan": repo_audit_dry_run_source_plan_decision,
        "repo_audit_source_intake": repo_audit_source_intake_decision,
        "github_source_connector": github_source_connector_decision,
        "web_research_gateway": web_research_gateway_decision,
        "local_model_context_profile": local_model_context_profile_decision,
        "context_policy": context_policy_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "capability_lease": capability_lease_decision,
        "repo_audit": repo_audit_decision,
        "audit_query_layer": audit_query_layer_decision,
        "action_attribution": action_attribution_decision,
        "system_drift_integrity": system_drift_integrity_decision,
        "passive_observe": passive_observe_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    display_input = RepoAuditSourcePlanDisplayInput(
        request_id=_text(data.get("request_id")),
        display_surface_class=_text(data.get("display_surface_class")),
        display_intent_class=_text(data.get("display_intent_class")),
        display_status_class=_text(data.get("display_status_class")),
        display_truth_label=_text(data.get("display_truth_label")),
        display_risk_label=_text(data.get("display_risk_label")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        dry_run_source_plan_refs=_mapping_tuple(data.get("dry_run_source_plan_refs", data.get("dry_run_source_plan_ref"))),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        memory_derived_context=_truthy(data.get("memory_derived_context")),
        project_or_repository_scoped=_truthy(data.get("project_or_repository_scoped")),
        private_display_metadata=_truthy(data.get("private_display_metadata")),
    )

    _validate_required(display_input, failures)
    _validate_display_truthfulness(display_input, data, failures)
    _validate_identity_and_memory(display_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)

    return _decision(
        display_input=display_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    display_input: RepoAuditSourcePlanDisplayInput | None,
    related_references: tuple[RelatedRepoAuditSourcePlanDisplayReference, ...],
    failures: tuple[RepoAuditSourcePlanDisplayFailure, ...],
) -> RepoAuditSourcePlanDisplayDecision:
    future_gated = bool(display_input and _is_future_gated(display_input))
    return RepoAuditSourcePlanDisplayDecision(
        contract_version=REPO_AUDIT_SOURCE_PLAN_DISPLAY_VERSION,
        display_readiness_status=_display_readiness_status(display_input, list(failures), future_gated),
        request_id=display_input.request_id if display_input else None,
        display_surface_class=display_input.display_surface_class if display_input else None,
        display_intent_class=display_input.display_intent_class if display_input else None,
        display_status_class=display_input.display_status_class if display_input else None,
        display_truth_label=display_input.display_truth_label if display_input else None,
        display_risk_label=display_input.display_risk_label if display_input else None,
        namespace=display_input.namespace if display_input else None,
        display_projection_status=_display_projection_status(display_input, list(failures), future_gated),
        truth_label_status=_truth_label_status(display_input, list(failures)),
        risk_label_status=_risk_label_status(display_input, list(failures)),
        non_authority_notice_status=_non_authority_notice_status(display_input, list(failures)),
        source_ref_display_status=_source_ref_display_status(display_input, list(failures)),
        operator_review_status=_operator_review_status(display_input, list(failures), future_gated),
        human_review_required=_human_review_required(display_input, list(failures), future_gated),
        future_gated=future_gated,
        lower_trust_display=bool(display_input and display_input.display_truth_label in LOW_TRUST_LABELS),
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        display_input=display_input,
    )


def _validate_required(display_input: RepoAuditSourcePlanDisplayInput, failures: list[RepoAuditSourcePlanDisplayFailure]) -> None:
    for field in (
        "request_id",
        "display_surface_class",
        "display_intent_class",
        "display_status_class",
        "display_truth_label",
        "namespace",
    ):
        if not getattr(display_input, field):
            _add_failure(failures, f"missing_{field}", field, f"Repo Audit source plan display is missing {field}")
    if display_input.display_surface_class and display_input.display_surface_class not in DISPLAY_SURFACE_CLASSES:
        _add_failure(failures, "unsupported_display_surface_class", "display_surface_class", "display surface class is not recognized")
    if display_input.display_intent_class and display_input.display_intent_class not in DISPLAY_INTENT_CLASSES:
        _add_failure(failures, "unsupported_display_intent_class", "display_intent_class", "display intent class is not recognized")
    if display_input.display_status_class and display_input.display_status_class not in DISPLAY_STATUS_CLASSES:
        _add_failure(failures, "unsupported_display_status_class", "display_status_class", "display status class is not recognized")
    if display_input.display_truth_label and display_input.display_truth_label not in DISPLAY_TRUTH_LABELS:
        _add_failure(failures, "unsupported_display_truth_label", "display_truth_label", "display truth label is not recognized")
    if display_input.display_risk_label and display_input.display_risk_label not in DISPLAY_RISK_LABELS:
        _add_failure(failures, "unsupported_display_risk_label", "display_risk_label", "display risk label is not recognized")
    if not (display_input.source_refs or display_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "display metadata requires source refs or provenance")
    if not display_input.dry_run_source_plan_refs:
        _add_failure(failures, "missing_dry_run_source_plan_reference", "dry_run_source_plan_refs", "display metadata requires dry-run source plan reference metadata")


def _validate_display_truthfulness(
    display_input: RepoAuditSourcePlanDisplayInput,
    data: Mapping[str, Any],
    failures: list[RepoAuditSourcePlanDisplayFailure],
) -> None:
    truth = display_input.display_truth_label
    if truth == "metadata_only" and _truthy(data.get("display_claims_source_truth")):
        _add_failure(failures, "metadata_only_source_truth_overclaim", "display_truth_label", "metadata-only source cannot be displayed as source truth")
    if truth == "candidate_only" and _truthy(data.get("display_claims_repo_read")):
        _add_failure(failures, "candidate_only_read_overclaim", "display_truth_label", "candidate-only source cannot be displayed as read")
    if truth == "excluded_by_policy" and (_truthy(data.get("display_claims_deleted")) or _truthy(data.get("display_claims_cleaned"))):
        _add_failure(failures, "excluded_source_cleanup_overclaim", "display_truth_label", "excluded source cannot be displayed as deleted or cleaned")
    if truth == "future_gated" and _truthy(data.get("display_claims_available")):
        _add_failure(failures, "future_gated_availability_overclaim", "display_truth_label", "future-gated source cannot be displayed as available")
    if truth == "blocked" and _truthy(data.get("display_claims_permitted")):
        _add_failure(failures, "blocked_source_permission_overclaim", "display_truth_label", "blocked source cannot be displayed as permitted")
    if truth == "low_trust" and _truthy(data.get("low_trust_shown_as_authority")):
        _add_failure(failures, "low_trust_authority_claim_denied", "display_truth_label", "low-trust source cannot be displayed as authoritative")
    if truth == "bounded_projection" and _truthy(data.get("bounded_projection_claims_complete")):
        _add_failure(failures, "bounded_projection_complete_claim_denied", "display_truth_label", "bounded projection cannot be displayed as complete repo plan")


def _validate_identity_and_memory(
    display_input: RepoAuditSourcePlanDisplayInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[RepoAuditSourcePlanDisplayFailure],
) -> None:
    if display_input.memory_derived_context and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "memory-derived display metadata requires Memory Governance")
    if _requires_identity(display_input) and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private or repository-scoped display metadata requires Identity Scope")
    if context_policy_decision is not None and _field_bool(context_policy_decision, "data_sent_external"):
        _add_failure(failures, "context_policy_contradicted", "context_policy_decision", "Context Policy cannot allow external transfer here")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[RepoAuditSourcePlanDisplayFailure],
    related_references: list[RelatedRepoAuditSourcePlanDisplayReference],
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
            f"{label} cannot authorize display authority, source access, repo reads, file list/stat/hash/read, context packages, model calls, proof, evidence, verifier success, dispatch, or grants",
        )
    related_references.append(
        RelatedRepoAuditSourcePlanDisplayReference(
            label=label,
            observed_status=_related_status(decision),
            authority=False,
            future_gated=_field_bool(decision, "future_gated"),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(label: str, source: Any, failures: list[RepoAuditSourcePlanDisplayFailure]) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim display authority, grants, evidence, verifier success, truth, proof, source access, or permission",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot render UI, emit CLI output, call GitHub/web/API, fetch, clone, read, list, stat, hash, create context, cache, report, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "Repo Audit source plan display metadata cannot grant execution permission",
            )


def _display_readiness_status(
    display_input: RepoAuditSourcePlanDisplayInput | None,
    failures: list[RepoAuditSourcePlanDisplayFailure],
    future_gated: bool,
) -> str:
    if display_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if "execution_permission_claim_denied" in reasons:
            return "blocked_by_authority_claim"
        if any(reason in FORBIDDEN_BEHAVIOR_REASONS for reason in reasons):
            return "blocked_by_execution_claim"
        if any("authority" in reason or "grant" in reason or "permission" in reason or "overclaim" in reason for reason in reasons):
            return "blocked_by_display_overclaim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        return "blocked_by_policy"
    if future_gated:
        return "display_future_gated"
    if display_input.human_review_required or _human_review_required(display_input, failures, future_gated):
        return "display_requires_operator_review"
    return "display_ready_metadata_only"


def _display_projection_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure], future_gated: bool) -> str:
    if display_input is None or failures:
        return "blocked"
    if future_gated:
        return "future_display_projection_only"
    return "display_metadata_projection_only"


def _truth_label_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure]) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_truth_label in BLOCKED_TRUTH_LABELS:
        return "blocked_or_excluded_label_preserved"
    if display_input.display_truth_label in REVIEW_TRUTH_LABELS:
        return "review_or_gate_label_preserved"
    if display_input.display_truth_label in LOW_TRUST_LABELS:
        return "low_trust_or_stale_label_preserved"
    return "truth_label_metadata_only"


def _risk_label_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure]) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_risk_label in {"high", "critical"}:
        return "high_risk_label_preserved"
    return "risk_label_metadata_only"


def _non_authority_notice_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure]) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_intent_class == "show_non_authority_notice":
        return "non_authority_notice_candidate"
    return "non_authority_required"


def _source_ref_display_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure]) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_intent_class == "show_provenance_refs":
        return "source_refs_only_not_evidence"
    return "source_refs_preserved"


def _operator_review_status(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure], future_gated: bool) -> str:
    if display_input is None or failures:
        return "blocked"
    if _human_review_required(display_input, failures, future_gated):
        return "operator_review_required"
    return "operator_review_not_required_by_metadata"


def _human_review_required(display_input: RepoAuditSourcePlanDisplayInput | None, failures: list[RepoAuditSourcePlanDisplayFailure], future_gated: bool) -> bool:
    if display_input is None:
        return False
    return bool(
        failures
        or future_gated
        or display_input.human_review_required
        or display_input.display_status_class == "requires_operator_review"
        or display_input.display_truth_label in REVIEW_TRUTH_LABELS
        or display_input.display_truth_label in LOW_TRUST_LABELS
        or display_input.display_risk_label in {"high", "critical", "unknown"}
        or display_input.private_display_metadata
    )


def _is_future_gated(display_input: RepoAuditSourcePlanDisplayInput) -> bool:
    return bool(
        display_input.display_status_class == "future_gated"
        or display_input.display_truth_label == "future_gated"
    )


def _requires_identity(display_input: RepoAuditSourcePlanDisplayInput) -> bool:
    return bool(
        display_input.project_or_repository_scoped
        or display_input.private_display_metadata
        or display_input.display_status_class in {"requires_operator_review", "blocked_by_privacy"}
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "display_readiness_status",
        "dry_run_status",
        "intake_status",
        "connector_status",
        "readiness_status",
        "profile_status",
        "policy_status",
        "scope_status",
        "governance_status",
        "audit_status",
        "read_plan_status",
        "plan_status",
        "passport_status",
        "compliance_status",
        "mission_status",
        "simulation_status",
    ):
        value = _field_value(decision, field)
        if value is not None:
            return str(value)
    return None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
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
    failures: list[RepoAuditSourcePlanDisplayFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditSourcePlanDisplayFailure(reason=reason, field=field, message=message))
