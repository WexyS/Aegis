from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_DRY_RUN_SOURCE_PLAN_VERSION = "repo-audit-dry-run-source-plan/1"
REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_dry_run_source_plan"
)

DRY_RUN_PLAN_CLASSES = {
    "github_repo_source_plan",
    "github_file_source_plan",
    "github_issue_pr_source_plan",
    "local_repo_metadata_plan",
    "local_clone_future_plan",
    "web_source_plan",
    "package_dependency_plan",
    "documentation_plan",
    "release_notes_plan",
    "security_advisory_plan",
    "mixed_source_plan",
    "unknown",
}

PLAN_OPERATIONS = {
    "classify_dry_run_plan",
    "project_candidate_sources",
    "project_allowed_scopes",
    "project_blocked_scopes",
    "project_exclusion_policy",
    "project_privacy_boundaries",
    "project_freshness_requirements",
    "project_provenance_requirements",
    "project_context_budget_requirements",
    "project_operator_review_requirements",
    "project_future_execution_gates",
    "unknown",
}

PLAN_STATUS_CLASSES = {
    "dry_run_ready",
    "metadata_only_projection",
    "requires_identity_scope",
    "requires_context_policy",
    "requires_source_intake",
    "requires_github_source_connector",
    "requires_web_gateway",
    "requires_repo_audit_readiness",
    "requires_operator_review",
    "blocked_by_privacy",
    "blocked_by_exclusion_policy",
    "blocked_by_unknown_scope",
    "blocked_by_secret_or_credential",
    "future_gated",
    "unknown",
}

CANDIDATE_SOURCE_DISPOSITIONS = {
    "include_candidate_metadata_only",
    "exclude_by_policy",
    "exclude_generated",
    "exclude_build_output",
    "exclude_vendor_dependency",
    "exclude_secret_like",
    "exclude_credential_like",
    "exclude_runtime_journal",
    "exclude_raw_evidence",
    "exclude_model_or_vector_artifact",
    "require_operator_review",
    "future_gated",
    "unknown",
}

PROJECTION_COMPLETENESS_CLASSES = {
    "complete_for_supplied_metadata",
    "bounded_metadata_only",
    "partial",
    "stale",
    "unavailable",
    "unknown",
}

TRUST_CLASSES = {
    "backend_supplied_metadata",
    "source_intake_candidate",
    "github_connector_candidate",
    "web_gateway_candidate",
    "repo_audit_read_plan_candidate",
    "user_supplied_low_trust",
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
    "unknown",
}

PRIVACY_CLASSES = {
    "public_metadata",
    "public_source_candidate",
    "private_repo_metadata",
    "private_repo_content",
    "internal_repo_future",
    "secret_like",
    "credential_like",
    "sensitive",
    "unknown",
}

FRESHNESS_CLASSES = {
    "commit_pinned",
    "tag_or_release_pinned",
    "branch_floating",
    "local_snapshot_metadata",
    "current_required",
    "stale",
    "unknown",
}

EXCLUSION_CLASSES = {
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
    "unknown_sensitive_excluded",
    "unknown",
}

REQUIRED_EXCLUSIONS = {
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
}

FUTURE_GATED_PLAN_CLASSES = {"local_clone_future_plan"}
FUTURE_GATED_OPERATIONS = {"project_future_execution_gates"}
PRIVATE_PRIVACY_CLASSES = {"private_repo_metadata", "private_repo_content", "internal_repo_future", "sensitive", "unknown"}
LOW_TRUST_CLASSES = {
    "user_supplied_low_trust",
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
    "unknown",
}
PINNED_FRESHNESS_CLASSES = {"commit_pinned", "tag_or_release_pinned"}
EXCLUDED_DISPOSITIONS = {
    "exclude_by_policy",
    "exclude_generated",
    "exclude_build_output",
    "exclude_vendor_dependency",
    "exclude_secret_like",
    "exclude_credential_like",
    "exclude_runtime_journal",
    "exclude_raw_evidence",
    "exclude_model_or_vector_artifact",
}
BLOCKING_DISPOSITIONS = {"exclude_secret_like", "exclude_credential_like", "unknown"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_dry_run_plan": "dry_run_plan_cannot_provide_evidence",
    "evidence_created": "dry_run_plan_cannot_provide_evidence",
    "verifier_success": "dry_run_plan_cannot_mark_verifier_success",
    "verified_success": "dry_run_plan_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "frontend_output_is_truth": "frontend_output_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "source_truth_claimed": "source_truth_claim_denied",
    "repo_audit_proof_claimed": "repo_audit_proof_claim_denied",
    "compliance_proof_claimed": "compliance_proof_claim_denied",
    "passport_proof_claimed": "passport_proof_claim_denied",
    "private_repo_access_allowed": "private_repo_access_permission_denied",
    "raw_content_ingestion_allowed": "raw_content_ingestion_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
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
    "report_generated": "report_generation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
}

FORBIDDEN_BEHAVIOR_REASONS = set(FORBIDDEN_BEHAVIOR_FIELDS.values())


@dataclass(frozen=True)
class RepoAuditDryRunSourcePlanFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditDryRunCandidateSource:
    ref_id: str | None
    source_kind: str | None
    disposition: str | None
    privacy_class: str | None = None
    trust_class: str | None = None
    freshness_class: str | None = None
    scope_class: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RelatedRepoAuditDryRunSourcePlanReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class RepoAuditDryRunSourcePlanInput:
    request_id: str | None
    dry_run_plan_class: str | None
    plan_operation: str | None
    plan_status_class: str | None
    projection_completeness_class: str | None
    privacy_class: str | None
    trust_class: str | None
    freshness_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    candidate_sources: tuple[RepoAuditDryRunCandidateSource, ...]
    exclusion_classes: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    memory_derived_context: bool
    project_or_repository_scoped: bool
    raw_content_requested: bool
    complete_repo_plan_claimed: bool


@dataclass(frozen=True)
class RepoAuditDryRunSourcePlanDecision:
    contract_version: str
    dry_run_status: str
    request_id: str | None
    dry_run_plan_class: str | None
    plan_operation: str | None
    plan_status_class: str | None
    projection_completeness_class: str | None
    privacy_class: str | None
    trust_class: str | None
    freshness_class: str | None
    namespace: str | None
    plan_projection_status: str
    candidate_projection_status: str
    privacy_status: str
    completeness_status: str
    trust_status: str
    freshness_status: str
    exclusion_status: str
    raw_content_status: str
    candidate_sources: tuple[RepoAuditDryRunCandidateSource, ...]
    included_candidate_count: int
    excluded_candidate_count: int
    operator_review_candidate_count: int
    future_gated_candidate_count: int
    lower_trust_source: bool
    human_review_required: bool
    future_gated: bool
    related_references: tuple[RelatedRepoAuditDryRunSourcePlanReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditDryRunSourcePlanFailure, ...]
    plan_input: RepoAuditDryRunSourcePlanInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_dry_run_plan: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
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
    report_generated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    private_repo_access_allowed: bool = False
    raw_content_ingestion_allowed: bool = False
    source_truth_claimed: bool = False
    repo_audit_proof_claimed: bool = False
    compliance_proof_claimed: bool = False
    passport_proof_claimed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_repo_audit_dry_run_source_plan_request(
    request: Mapping[str, Any] | None,
    *,
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
) -> RepoAuditDryRunSourcePlanDecision:
    """Validate dry-run source plan projection metadata without source access."""

    if not isinstance(request, Mapping):
        failure = RepoAuditDryRunSourcePlanFailure(
            reason="missing_request",
            field="request",
            message="Repo Audit dry-run source plan requires caller-supplied metadata",
        )
        return _decision(plan_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[RepoAuditDryRunSourcePlanFailure] = []
    related_references: list[RelatedRepoAuditDryRunSourcePlanReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
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

    plan_input = RepoAuditDryRunSourcePlanInput(
        request_id=_text(data.get("request_id")),
        dry_run_plan_class=_text(data.get("dry_run_plan_class")),
        plan_operation=_text(data.get("plan_operation")),
        plan_status_class=_text(data.get("plan_status_class")),
        projection_completeness_class=_text(data.get("projection_completeness_class")),
        privacy_class=_text(data.get("privacy_class")),
        trust_class=_text(data.get("trust_class")),
        freshness_class=_text(data.get("freshness_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        candidate_sources=_candidate_tuple(data.get("candidate_sources")),
        exclusion_classes=_text_tuple(data.get("exclusion_classes", data.get("exclusion_policy"))),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        memory_derived_context=_truthy(data.get("memory_derived_context")),
        project_or_repository_scoped=_truthy(data.get("project_or_repository_scoped")),
        raw_content_requested=_truthy(data.get("raw_content_requested")),
        complete_repo_plan_claimed=_truthy(data.get("complete_repo_plan_claimed")),
    )

    _validate_required(plan_input, failures)
    _validate_privacy(plan_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)
    _validate_candidates(plan_input, failures)
    _validate_exclusions(plan_input, failures)
    _validate_trust_freshness_completeness(plan_input, failures)

    return _decision(
        plan_input=plan_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    plan_input: RepoAuditDryRunSourcePlanInput | None,
    related_references: tuple[RelatedRepoAuditDryRunSourcePlanReference, ...],
    failures: tuple[RepoAuditDryRunSourcePlanFailure, ...],
) -> RepoAuditDryRunSourcePlanDecision:
    future_gated = bool(plan_input and _is_future_gated(plan_input))
    candidates = plan_input.candidate_sources if plan_input else ()
    return RepoAuditDryRunSourcePlanDecision(
        contract_version=REPO_AUDIT_DRY_RUN_SOURCE_PLAN_VERSION,
        dry_run_status=_dry_run_status(plan_input, list(failures), future_gated),
        request_id=plan_input.request_id if plan_input else None,
        dry_run_plan_class=plan_input.dry_run_plan_class if plan_input else None,
        plan_operation=plan_input.plan_operation if plan_input else None,
        plan_status_class=plan_input.plan_status_class if plan_input else None,
        projection_completeness_class=plan_input.projection_completeness_class if plan_input else None,
        privacy_class=plan_input.privacy_class if plan_input else None,
        trust_class=plan_input.trust_class if plan_input else None,
        freshness_class=plan_input.freshness_class if plan_input else None,
        namespace=plan_input.namespace if plan_input else None,
        plan_projection_status=_plan_projection_status(plan_input, list(failures), future_gated),
        candidate_projection_status=_candidate_projection_status(plan_input, list(failures)),
        privacy_status=_privacy_status(plan_input, list(failures)),
        completeness_status=_completeness_status(plan_input, list(failures)),
        trust_status=_trust_status(plan_input, list(failures)),
        freshness_status=_freshness_status(plan_input, list(failures)),
        exclusion_status=_exclusion_status(plan_input, list(failures)),
        raw_content_status=_raw_content_status(plan_input, list(failures)),
        candidate_sources=candidates,
        included_candidate_count=sum(1 for candidate in candidates if candidate.disposition == "include_candidate_metadata_only"),
        excluded_candidate_count=sum(1 for candidate in candidates if candidate.disposition in EXCLUDED_DISPOSITIONS),
        operator_review_candidate_count=sum(1 for candidate in candidates if candidate.disposition == "require_operator_review"),
        future_gated_candidate_count=sum(1 for candidate in candidates if candidate.disposition == "future_gated"),
        lower_trust_source=bool(plan_input and _is_low_trust(plan_input)),
        human_review_required=_human_review_required(plan_input, list(failures), future_gated),
        future_gated=future_gated,
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        plan_input=plan_input,
    )


def _validate_required(plan_input: RepoAuditDryRunSourcePlanInput, failures: list[RepoAuditDryRunSourcePlanFailure]) -> None:
    for field in (
        "request_id",
        "dry_run_plan_class",
        "plan_operation",
        "plan_status_class",
        "projection_completeness_class",
        "privacy_class",
        "trust_class",
        "freshness_class",
        "namespace",
    ):
        if not getattr(plan_input, field):
            _add_failure(failures, f"missing_{field}", field, f"Repo Audit dry-run source plan is missing {field}")
    if plan_input.dry_run_plan_class and plan_input.dry_run_plan_class not in DRY_RUN_PLAN_CLASSES:
        _add_failure(failures, "unsupported_dry_run_plan_class", "dry_run_plan_class", "dry-run plan class is not recognized")
    if plan_input.plan_operation and plan_input.plan_operation not in PLAN_OPERATIONS:
        _add_failure(failures, "unsupported_plan_operation", "plan_operation", "plan operation is not recognized")
    if plan_input.plan_status_class and plan_input.plan_status_class not in PLAN_STATUS_CLASSES:
        _add_failure(failures, "unsupported_plan_status_class", "plan_status_class", "plan status class is not recognized")
    if plan_input.projection_completeness_class and plan_input.projection_completeness_class not in PROJECTION_COMPLETENESS_CLASSES:
        _add_failure(failures, "unsupported_projection_completeness_class", "projection_completeness_class", "projection completeness class is not recognized")
    if plan_input.privacy_class and plan_input.privacy_class not in PRIVACY_CLASSES:
        _add_failure(failures, "unsupported_privacy_class", "privacy_class", "privacy class is not recognized")
    if plan_input.trust_class and plan_input.trust_class not in TRUST_CLASSES:
        _add_failure(failures, "unsupported_trust_class", "trust_class", "trust class is not recognized")
    if plan_input.freshness_class and plan_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")
    if not (plan_input.source_refs or plan_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "dry-run projection requires source refs or provenance")
    if not plan_input.candidate_sources:
        _add_failure(failures, "missing_candidate_source_metadata", "candidate_sources", "dry-run projection requires candidate source metadata")
    if not plan_input.exclusion_classes:
        _add_failure(failures, "missing_exclusion_policy", "exclusion_classes", "dry-run projection requires exclusion policy metadata")


def _validate_privacy(
    plan_input: RepoAuditDryRunSourcePlanInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[RepoAuditDryRunSourcePlanFailure],
) -> None:
    if plan_input.privacy_class in {"secret_like", "credential_like"}:
        _add_failure(failures, "secret_or_credential_candidate_blocked", "privacy_class", "secret and credential dry-run candidates are blocked")
    if plan_input.privacy_class == "private_repo_content":
        _add_failure(failures, "private_repo_content_projection_blocked", "privacy_class", "private repo content cannot be projected without a later policy boundary")
    if plan_input.privacy_class == "unknown":
        _add_failure(failures, "unknown_privacy_blocks_dry_run_plan", "privacy_class", "unknown privacy blocks dry-run plan readiness")
    if plan_input.raw_content_requested:
        _add_failure(failures, "raw_content_request_blocked", "raw_content_requested", "raw content ingestion is not allowed by dry-run projection")
    if plan_input.memory_derived_context and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "memory-derived dry-run metadata requires Memory Governance")
    if _requires_identity(plan_input) and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private or repository-scoped dry-run metadata requires Identity Scope")
    if context_policy_decision is not None and _field_bool(context_policy_decision, "data_sent_external"):
        _add_failure(failures, "context_policy_contradicted", "context_policy_decision", "Context Policy cannot allow external transfer here")


def _validate_candidates(plan_input: RepoAuditDryRunSourcePlanInput, failures: list[RepoAuditDryRunSourcePlanFailure]) -> None:
    for index, candidate in enumerate(plan_input.candidate_sources):
        prefix = f"candidate_sources[{index}]"
        if not candidate.ref_id:
            _add_failure(failures, "candidate_missing_ref_id", f"{prefix}.ref_id", "candidate source requires a ref id")
        if not candidate.disposition:
            _add_failure(failures, "candidate_missing_disposition", f"{prefix}.disposition", "candidate source requires a disposition")
        elif candidate.disposition not in CANDIDATE_SOURCE_DISPOSITIONS:
            _add_failure(failures, "unsupported_candidate_disposition", f"{prefix}.disposition", "candidate disposition is not recognized")
        elif candidate.disposition in BLOCKING_DISPOSITIONS:
            _add_failure(failures, f"candidate_{candidate.disposition}_blocked", f"{prefix}.disposition", "candidate disposition remains blocked")
        if candidate.privacy_class in {"secret_like", "credential_like"}:
            _add_failure(failures, "candidate_secret_or_credential_blocked", f"{prefix}.privacy_class", "secret and credential candidates remain blocked")
        if candidate.privacy_class == "private_repo_content":
            _add_failure(failures, "candidate_private_repo_content_blocked", f"{prefix}.privacy_class", "private repo content candidate is blocked")


def _validate_exclusions(plan_input: RepoAuditDryRunSourcePlanInput, failures: list[RepoAuditDryRunSourcePlanFailure]) -> None:
    for exclusion in plan_input.exclusion_classes:
        if exclusion not in EXCLUSION_CLASSES:
            _add_failure(failures, "unsupported_exclusion_class", "exclusion_classes", "exclusion class is not recognized")
    missing = REQUIRED_EXCLUSIONS.difference(plan_input.exclusion_classes)
    if missing:
        _add_failure(
            failures,
            "incomplete_exclusion_policy",
            "exclusion_classes",
            f"dry-run source plan is missing required exclusions: {', '.join(sorted(missing))}",
        )


def _validate_trust_freshness_completeness(
    plan_input: RepoAuditDryRunSourcePlanInput,
    failures: list[RepoAuditDryRunSourcePlanFailure],
) -> None:
    if plan_input.dry_run_plan_class == "security_advisory_plan":
        if plan_input.trust_class not in {None, "github_connector_candidate", "web_gateway_candidate", "backend_supplied_metadata"}:
            _add_failure(failures, "security_advisory_requires_trusted_metadata", "trust_class", "security advisory plans require trusted source metadata")
        if plan_input.freshness_class not in {None, "current_required", "commit_pinned", "tag_or_release_pinned"}:
            _add_failure(failures, "security_advisory_requires_freshness", "freshness_class", "security advisory plans require current or pinned freshness")
    if plan_input.projection_completeness_class == "bounded_metadata_only" and plan_input.complete_repo_plan_claimed:
        _add_failure(failures, "bounded_metadata_cannot_claim_complete_repo_plan", "complete_repo_plan_claimed", "bounded metadata cannot claim complete repo source planning")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[RepoAuditDryRunSourcePlanFailure],
    related_references: list[RelatedRepoAuditDryRunSourcePlanReference],
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
            f"{label} cannot authorize source access, repo reads, file list/stat/hash/read, context packages, model calls, proof, evidence, verifier success, dispatch, or grants",
        )
    related_references.append(
        RelatedRepoAuditDryRunSourcePlanReference(
            label=label,
            observed_status=_related_status(decision),
            authority=False,
            future_gated=_field_bool(decision, "future_gated"),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(label: str, source: Any, failures: list[RepoAuditDryRunSourcePlanFailure]) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, truth, proof, or access permission",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot call GitHub/web/API, fetch, clone, read, list, stat, hash, create context, cache, report, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "Repo Audit dry-run source plan metadata cannot grant execution permission",
            )


def _dry_run_status(
    plan_input: RepoAuditDryRunSourcePlanInput | None,
    failures: list[RepoAuditDryRunSourcePlanFailure],
    future_gated: bool,
) -> str:
    if plan_input is None:
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
        if any("secret" in reason or "credential" in reason or "private" in reason or "privacy" in reason or "raw_content" in reason or "exclusion" in reason or "candidate_exclude" in reason for reason in reasons):
            return "blocked_by_privacy_or_exclusion"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        return "blocked_by_policy"
    if future_gated:
        return "dry_run_future_gated"
    if plan_input.human_review_required or _human_review_required(plan_input, failures, future_gated):
        return "dry_run_requires_operator_review"
    return "dry_run_ready"


def _plan_projection_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure], future_gated: bool) -> str:
    if plan_input is None or failures:
        return "blocked"
    if future_gated:
        return "future_projection_candidate_only"
    if plan_input.plan_status_class == "metadata_only_projection":
        return "metadata_only_projection"
    return "dry_run_projection_only"


def _candidate_projection_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    if any(candidate.disposition == "require_operator_review" for candidate in plan_input.candidate_sources):
        return "operator_review_candidates_present"
    if any(candidate.disposition == "future_gated" for candidate in plan_input.candidate_sources):
        return "future_gated_candidates_present"
    return "candidate_dispositions_preserved"


def _privacy_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    if plan_input.privacy_class in {"public_metadata", "public_source_candidate"}:
        return "public_metadata_candidate"
    if plan_input.privacy_class in {"private_repo_metadata", "private_repo_content", "internal_repo_future"}:
        return "private_reference_only"
    return "restricted_reference_only"


def _completeness_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    if plan_input.projection_completeness_class == "bounded_metadata_only":
        return "bounded_metadata_only_not_complete_repo"
    if plan_input.projection_completeness_class in {"partial", "stale", "unavailable", "unknown"}:
        return f"{plan_input.projection_completeness_class}_projection_preserved"
    return "complete_for_supplied_metadata_only"


def _trust_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    if _is_low_trust(plan_input):
        return "low_trust_metadata_candidate"
    if plan_input.trust_class == "repo_audit_read_plan_candidate":
        return "read_plan_candidate_not_read_permission"
    return "source_candidate_not_truth"


def _freshness_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    if plan_input.freshness_class == "branch_floating":
        return "floating_branch_not_pinned"
    if plan_input.freshness_class in PINNED_FRESHNESS_CLASSES:
        return "pinned_metadata_candidate_not_proof"
    if plan_input.freshness_class == "current_required":
        return "freshness_requirement_preserved"
    if plan_input.freshness_class == "stale":
        return "stale_metadata_preserved"
    return "freshness_metadata_only"


def _exclusion_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    return "exclusion_policy_preserved"


def _raw_content_status(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure]) -> str:
    if plan_input is None or failures:
        return "blocked"
    return "metadata_only_no_raw_ingestion"


def _human_review_required(plan_input: RepoAuditDryRunSourcePlanInput | None, failures: list[RepoAuditDryRunSourcePlanFailure], future_gated: bool) -> bool:
    if plan_input is None:
        return False
    return bool(
        failures
        or future_gated
        or plan_input.human_review_required
        or plan_input.plan_status_class == "requires_operator_review"
        or plan_input.privacy_class in PRIVATE_PRIVACY_CLASSES
        or plan_input.freshness_class in {"branch_floating", "unknown"}
        or _is_low_trust(plan_input)
        or any(candidate.disposition == "require_operator_review" for candidate in plan_input.candidate_sources)
    )


def _is_future_gated(plan_input: RepoAuditDryRunSourcePlanInput) -> bool:
    return bool(
        plan_input.dry_run_plan_class in FUTURE_GATED_PLAN_CLASSES
        or plan_input.plan_operation in FUTURE_GATED_OPERATIONS
        or plan_input.plan_status_class in {
            "future_gated",
            "requires_source_intake",
            "requires_github_source_connector",
            "requires_web_gateway",
            "requires_repo_audit_readiness",
        }
        or plan_input.privacy_class == "internal_repo_future"
        or any(candidate.disposition == "future_gated" for candidate in plan_input.candidate_sources)
    )


def _is_low_trust(plan_input: RepoAuditDryRunSourcePlanInput) -> bool:
    return bool(
        plan_input.trust_class in LOW_TRUST_CLASSES
        or any(candidate.trust_class in LOW_TRUST_CLASSES for candidate in plan_input.candidate_sources)
    )


def _requires_identity(plan_input: RepoAuditDryRunSourcePlanInput) -> bool:
    return bool(
        plan_input.project_or_repository_scoped
        or plan_input.privacy_class in {"private_repo_metadata", "private_repo_content", "internal_repo_future", "sensitive"}
        or plan_input.plan_status_class == "requires_identity_scope"
    )


def _related_status(decision: Any) -> str | None:
    for field in (
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


def _candidate_tuple(value: Any) -> tuple[RepoAuditDryRunCandidateSource, ...]:
    if value is None:
        return ()
    values: tuple[Any, ...]
    if isinstance(value, Mapping):
        values = (value,)
    elif isinstance(value, (list, tuple)):
        values = tuple(value)
    else:
        return ()
    candidates: list[RepoAuditDryRunCandidateSource] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        data = deepcopy(dict(item))
        candidates.append(
            RepoAuditDryRunCandidateSource(
                ref_id=_text(data.get("ref_id")),
                source_kind=_text(data.get("source_kind")),
                disposition=_text(data.get("disposition")),
                privacy_class=_text(data.get("privacy_class")),
                trust_class=_text(data.get("trust_class")),
                freshness_class=_text(data.get("freshness_class")),
                scope_class=_text(data.get("scope_class")),
                reason=_text(data.get("reason")),
            )
        )
    return tuple(candidates)


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
    failures: list[RepoAuditDryRunSourcePlanFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditDryRunSourcePlanFailure(reason=reason, field=field, message=message))
