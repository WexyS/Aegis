from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_SOURCE_INTAKE_VERSION = "repo-audit-source-intake-readiness/1"
REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_source_intake"
)

SOURCE_INTAKE_CLASSES = {
    "github_source_candidate",
    "local_repo_metadata_candidate",
    "local_clone_reference_future",
    "web_source_candidate",
    "package_registry_candidate",
    "documentation_source_candidate",
    "release_notes_source_candidate",
    "security_advisory_source_candidate",
    "user_supplied_source_metadata",
    "repo_audit_read_plan_candidate",
    "unknown",
}

SOURCE_INTAKE_OPERATIONS = {
    "classify_source_intake",
    "propose_repo_audit_source_handoff",
    "propose_read_plan_link",
    "propose_scope_filter",
    "propose_exclusion_policy",
    "propose_privacy_boundary",
    "propose_context_budget_link",
    "propose_source_ref_mapping",
    "propose_provenance_mapping",
    "propose_future_fetch_gate",
    "propose_future_local_read_gate",
    "unknown",
}

REPO_SOURCE_SCOPE_CLASSES = {
    "repository_metadata_only",
    "readme_candidate",
    "docs_candidate",
    "dependency_manifest_candidate",
    "source_file_candidate",
    "test_file_candidate",
    "config_file_candidate",
    "selected_path_candidate",
    "issue_pr_metadata_candidate",
    "release_metadata_candidate",
    "advisory_metadata_candidate",
    "no_raw_content",
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

READINESS_STATUS_CLASSES = {
    "intake_ready_metadata_only",
    "requires_identity_scope",
    "requires_context_policy",
    "requires_repo_audit_readiness",
    "requires_github_source_connector",
    "requires_web_research_gateway",
    "requires_capability_lease_future",
    "requires_operator_review",
    "blocked_by_privacy",
    "blocked_by_unknown_scope",
    "blocked_by_secret_scope",
    "future_gated",
    "unknown",
}

SOURCE_TRUST_CLASSES = {
    "source_ref_candidate",
    "connector_metadata_candidate",
    "repo_audit_read_plan_candidate",
    "web_gateway_candidate",
    "local_metadata_candidate",
    "user_supplied_low_trust",
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
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

REQUIRED_FUTURE_READ_EXCLUSIONS = {
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

FUTURE_GATED_INTAKE_CLASSES = {"local_clone_reference_future"}
FUTURE_GATED_OPERATIONS = {"propose_future_fetch_gate", "propose_future_local_read_gate"}
FUTURE_READ_SCOPES = {
    "readme_candidate",
    "docs_candidate",
    "dependency_manifest_candidate",
    "source_file_candidate",
    "test_file_candidate",
    "config_file_candidate",
    "selected_path_candidate",
}
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

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_source_intake": "source_intake_cannot_provide_evidence",
    "evidence_created": "source_intake_cannot_provide_evidence",
    "verifier_success": "source_intake_cannot_mark_verifier_success",
    "verified_success": "source_intake_cannot_mark_verifier_success",
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
    "file_read_performed": "file_read_denied",
    "directory_scan_performed": "directory_scan_denied",
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
class RepoAuditSourceIntakeFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedRepoAuditSourceIntakeReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class RepoAuditSourceIntakeInput:
    request_id: str | None
    source_intake_class: str | None
    source_intake_operation: str | None
    repo_source_scope_class: str | None
    privacy_class: str | None
    readiness_status_class: str | None
    source_trust_class: str | None
    freshness_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    exclusion_classes: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    memory_derived_context: bool
    project_or_repository_scoped: bool
    raw_content_requested: bool


@dataclass(frozen=True)
class RepoAuditSourceIntakeDecision:
    contract_version: str
    intake_status: str
    request_id: str | None
    source_intake_class: str | None
    source_intake_operation: str | None
    repo_source_scope_class: str | None
    privacy_class: str | None
    readiness_status_class: str | None
    source_trust_class: str | None
    freshness_class: str | None
    namespace: str | None
    source_handoff_status: str
    privacy_status: str
    source_scope_status: str
    source_trust_status: str
    freshness_status: str
    exclusion_status: str
    raw_content_status: str
    exclusion_classes: tuple[str, ...]
    lower_trust_source: bool
    human_review_required: bool
    future_gated: bool
    related_references: tuple[RelatedRepoAuditSourceIntakeReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditSourceIntakeFailure, ...]
    source_input: RepoAuditSourceIntakeInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_source_intake: bool = False
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
    file_read_performed: bool = False
    directory_scan_performed: bool = False
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


def validate_repo_audit_source_intake_request(
    request: Mapping[str, Any] | None,
    *,
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
) -> RepoAuditSourceIntakeDecision:
    """Validate source-intake planning metadata without source access or repo reads."""

    if not isinstance(request, Mapping):
        failure = RepoAuditSourceIntakeFailure(
            reason="missing_request",
            field="request",
            message="Repo Audit source intake requires caller-supplied metadata",
        )
        return _decision(source_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[RepoAuditSourceIntakeFailure] = []
    related_references: list[RelatedRepoAuditSourceIntakeReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
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

    source_input = RepoAuditSourceIntakeInput(
        request_id=_text(data.get("request_id")),
        source_intake_class=_text(data.get("source_intake_class")),
        source_intake_operation=_text(data.get("source_intake_operation")),
        repo_source_scope_class=_text(data.get("repo_source_scope_class")),
        privacy_class=_text(data.get("privacy_class")),
        readiness_status_class=_text(data.get("readiness_status_class")),
        source_trust_class=_text(data.get("source_trust_class")),
        freshness_class=_text(data.get("freshness_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        exclusion_classes=_text_tuple(data.get("exclusion_classes", data.get("exclusion_policy"))),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        memory_derived_context=_truthy(data.get("memory_derived_context")),
        project_or_repository_scoped=_truthy(data.get("project_or_repository_scoped")),
        raw_content_requested=_truthy(data.get("raw_content_requested")),
    )

    _validate_required(source_input, failures)
    _validate_privacy_and_access(source_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)
    _validate_scope_and_exclusions(source_input, failures)
    _validate_trust_and_freshness(source_input, failures)

    return _decision(
        source_input=source_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    source_input: RepoAuditSourceIntakeInput | None,
    related_references: tuple[RelatedRepoAuditSourceIntakeReference, ...],
    failures: tuple[RepoAuditSourceIntakeFailure, ...],
) -> RepoAuditSourceIntakeDecision:
    future_gated = bool(source_input and _is_future_gated(source_input))
    return RepoAuditSourceIntakeDecision(
        contract_version=REPO_AUDIT_SOURCE_INTAKE_VERSION,
        intake_status=_intake_status(source_input, list(failures), future_gated),
        request_id=source_input.request_id if source_input else None,
        source_intake_class=source_input.source_intake_class if source_input else None,
        source_intake_operation=source_input.source_intake_operation if source_input else None,
        repo_source_scope_class=source_input.repo_source_scope_class if source_input else None,
        privacy_class=source_input.privacy_class if source_input else None,
        readiness_status_class=source_input.readiness_status_class if source_input else None,
        source_trust_class=source_input.source_trust_class if source_input else None,
        freshness_class=source_input.freshness_class if source_input else None,
        namespace=source_input.namespace if source_input else None,
        source_handoff_status=_source_handoff_status(source_input, list(failures), future_gated),
        privacy_status=_privacy_status(source_input, list(failures)),
        source_scope_status=_source_scope_status(source_input, list(failures)),
        source_trust_status=_source_trust_status(source_input, list(failures)),
        freshness_status=_freshness_status(source_input, list(failures)),
        exclusion_status=_exclusion_status(source_input, list(failures)),
        raw_content_status=_raw_content_status(source_input, list(failures)),
        exclusion_classes=source_input.exclusion_classes if source_input else (),
        lower_trust_source=bool(source_input and _is_low_trust(source_input)),
        human_review_required=_human_review_required(source_input, list(failures), future_gated),
        future_gated=future_gated,
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        source_input=source_input,
    )


def _validate_required(source_input: RepoAuditSourceIntakeInput, failures: list[RepoAuditSourceIntakeFailure]) -> None:
    for field in (
        "request_id",
        "source_intake_class",
        "source_intake_operation",
        "repo_source_scope_class",
        "privacy_class",
        "readiness_status_class",
        "source_trust_class",
        "freshness_class",
        "namespace",
    ):
        if not getattr(source_input, field):
            _add_failure(failures, f"missing_{field}", field, f"Repo Audit source intake is missing {field}")
    if source_input.source_intake_class and source_input.source_intake_class not in SOURCE_INTAKE_CLASSES:
        _add_failure(failures, "unsupported_source_intake_class", "source_intake_class", "source intake class is not recognized")
    if source_input.source_intake_operation and source_input.source_intake_operation not in SOURCE_INTAKE_OPERATIONS:
        _add_failure(failures, "unsupported_source_intake_operation", "source_intake_operation", "source intake operation is not recognized")
    if source_input.repo_source_scope_class and source_input.repo_source_scope_class not in REPO_SOURCE_SCOPE_CLASSES:
        _add_failure(failures, "unsupported_repo_source_scope_class", "repo_source_scope_class", "repo source scope class is not recognized")
    if source_input.privacy_class and source_input.privacy_class not in PRIVACY_CLASSES:
        _add_failure(failures, "unsupported_privacy_class", "privacy_class", "privacy class is not recognized")
    if source_input.readiness_status_class and source_input.readiness_status_class not in READINESS_STATUS_CLASSES:
        _add_failure(failures, "unsupported_readiness_status_class", "readiness_status_class", "readiness status class is not recognized")
    if source_input.source_trust_class and source_input.source_trust_class not in SOURCE_TRUST_CLASSES:
        _add_failure(failures, "unsupported_source_trust_class", "source_trust_class", "source trust class is not recognized")
    if source_input.freshness_class and source_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")
    if not (source_input.source_refs or source_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source intake requires source refs or provenance")
    if source_input.repo_source_scope_class in FUTURE_READ_SCOPES and not source_input.exclusion_classes:
        _add_failure(failures, "missing_exclusion_policy", "exclusion_classes", "future read candidates require exclusion policy metadata")


def _validate_privacy_and_access(
    source_input: RepoAuditSourceIntakeInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[RepoAuditSourceIntakeFailure],
) -> None:
    if source_input.privacy_class in {"secret_like", "credential_like"}:
        _add_failure(failures, "secret_or_credential_source_blocked", "privacy_class", "secret and credential source intake is blocked")
    if source_input.privacy_class == "private_repo_content":
        _add_failure(failures, "private_repo_content_handoff_blocked", "privacy_class", "private repo content cannot be handed off without a later policy boundary")
    if source_input.privacy_class == "unknown":
        _add_failure(failures, "unknown_privacy_blocks_source_access", "privacy_class", "unknown privacy blocks source intake access planning")
    if source_input.raw_content_requested:
        _add_failure(failures, "raw_content_request_blocked", "raw_content_requested", "raw content ingestion is not allowed by source intake readiness")
    if source_input.memory_derived_context and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "memory-derived source intake requires Memory Governance")
    if _requires_identity(source_input) and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private or repository-scoped source intake requires Identity Scope")
    if context_policy_decision is not None and _field_bool(context_policy_decision, "data_sent_external"):
        _add_failure(failures, "context_policy_contradicted", "context_policy_decision", "Context Policy cannot allow external transfer here")


def _validate_scope_and_exclusions(source_input: RepoAuditSourceIntakeInput, failures: list[RepoAuditSourceIntakeFailure]) -> None:
    for exclusion in source_input.exclusion_classes:
        if exclusion not in EXCLUSION_CLASSES:
            _add_failure(failures, "unsupported_exclusion_class", "exclusion_classes", "exclusion class is not recognized")
    if source_input.repo_source_scope_class in {"unknown"}:
        _add_failure(failures, "unknown_scope_blocks_source_intake", "repo_source_scope_class", "unknown source scope blocks source intake")
    if source_input.readiness_status_class == "blocked_by_secret_scope":
        _add_failure(failures, "readiness_status_blocks_secret_scope", "readiness_status_class", "secret-scope readiness remains blocked")
    if source_input.readiness_status_class == "blocked_by_unknown_scope":
        _add_failure(failures, "readiness_status_blocks_unknown_scope", "readiness_status_class", "unknown-scope readiness remains blocked")
    if source_input.repo_source_scope_class in FUTURE_READ_SCOPES:
        missing = REQUIRED_FUTURE_READ_EXCLUSIONS.difference(source_input.exclusion_classes)
        if missing:
            _add_failure(
                failures,
                "incomplete_exclusion_policy",
                "exclusion_classes",
                f"future read candidates are missing required exclusions: {', '.join(sorted(missing))}",
            )


def _validate_trust_and_freshness(source_input: RepoAuditSourceIntakeInput, failures: list[RepoAuditSourceIntakeFailure]) -> None:
    if source_input.source_intake_class == "security_advisory_source_candidate":
        if source_input.source_trust_class not in {None, "connector_metadata_candidate", "web_gateway_candidate", "source_ref_candidate"}:
            _add_failure(failures, "security_advisory_requires_trusted_metadata", "source_trust_class", "security advisories require trusted source metadata")
        if source_input.freshness_class not in {None, "current_required", "commit_pinned", "tag_or_release_pinned"}:
            _add_failure(failures, "security_advisory_requires_freshness", "freshness_class", "security advisories require current or pinned freshness")
    if source_input.source_intake_class == "repo_audit_read_plan_candidate" and source_input.repo_source_scope_class not in FUTURE_READ_SCOPES | {"repository_metadata_only", "no_raw_content"}:
        _add_failure(failures, "repo_audit_read_plan_scope_not_readiness_safe", "repo_source_scope_class", "read plan candidates must preserve safe metadata or future-read scopes")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[RepoAuditSourceIntakeFailure],
    related_references: list[RelatedRepoAuditSourceIntakeReference],
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
            f"{label} cannot authorize source access, repo reads, context packages, model calls, proof, evidence, verifier success, dispatch, or grants",
        )
    related_references.append(
        RelatedRepoAuditSourceIntakeReference(
            label=label,
            observed_status=_related_status(decision),
            authority=False,
            future_gated=_field_bool(decision, "future_gated"),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(label: str, source: Any, failures: list[RepoAuditSourceIntakeFailure]) -> None:
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
                f"{label} cannot call GitHub/web/API, fetch, clone, read, scan, create context, cache, report, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "Repo Audit source intake metadata cannot grant execution permission",
            )


def _intake_status(
    source_input: RepoAuditSourceIntakeInput | None,
    failures: list[RepoAuditSourceIntakeFailure],
    future_gated: bool,
) -> str:
    if source_input is None:
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
        if any("secret" in reason or "credential" in reason or "private" in reason or "privacy" in reason or "scope" in reason or "raw_content" in reason or "exclusion" in reason for reason in reasons):
            return "blocked_by_privacy_or_source_scope"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        return "blocked_by_policy"
    if future_gated:
        return "source_intake_future_gated"
    if source_input.human_review_required or _human_review_required(source_input, failures, future_gated):
        return "source_intake_requires_human_review"
    return "source_intake_ready_metadata_only"


def _source_handoff_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure], future_gated: bool) -> str:
    if source_input is None or failures:
        return "blocked"
    if future_gated:
        return "future_handoff_candidate_only"
    if source_input.source_intake_class == "repo_audit_read_plan_candidate":
        return "read_plan_link_candidate_not_permission"
    return "source_ref_handoff_metadata_only"


def _privacy_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.privacy_class in {"public_metadata", "public_source_candidate"}:
        return "public_metadata_candidate"
    if source_input.privacy_class in {"private_repo_metadata", "private_repo_content", "internal_repo_future"}:
        return "private_reference_only"
    return "restricted_reference_only"


def _source_scope_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.repo_source_scope_class == "repository_metadata_only":
        return "metadata_only"
    if source_input.repo_source_scope_class == "no_raw_content":
        return "no_raw_content"
    if source_input.repo_source_scope_class in FUTURE_READ_SCOPES:
        return "future_read_plan_candidate_only"
    return "scope_candidate_only"


def _source_trust_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if _is_low_trust(source_input):
        return "low_trust_metadata_candidate"
    if source_input.source_trust_class == "repo_audit_read_plan_candidate":
        return "read_plan_candidate_not_read_permission"
    return "source_ref_candidate_not_truth"


def _freshness_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.freshness_class == "branch_floating":
        return "floating_branch_not_pinned"
    if source_input.freshness_class in PINNED_FRESHNESS_CLASSES:
        return "pinned_metadata_candidate_not_proof"
    if source_input.freshness_class == "current_required":
        return "freshness_requirement_preserved"
    if source_input.freshness_class == "stale":
        return "stale_metadata_preserved"
    return "freshness_metadata_only"


def _exclusion_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.repo_source_scope_class in FUTURE_READ_SCOPES:
        return "future_read_exclusions_preserved"
    return "exclusion_metadata_only"


def _raw_content_status(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.repo_source_scope_class == "no_raw_content":
        return "raw_content_prohibited"
    return "metadata_only_no_raw_ingestion"


def _human_review_required(source_input: RepoAuditSourceIntakeInput | None, failures: list[RepoAuditSourceIntakeFailure], future_gated: bool) -> bool:
    if source_input is None:
        return False
    return bool(
        failures
        or future_gated
        or source_input.human_review_required
        or source_input.privacy_class in PRIVATE_PRIVACY_CLASSES
        or source_input.freshness_class in {"branch_floating", "unknown"}
        or _is_low_trust(source_input)
    )


def _is_future_gated(source_input: RepoAuditSourceIntakeInput) -> bool:
    return bool(
        source_input.source_intake_class in FUTURE_GATED_INTAKE_CLASSES
        or source_input.source_intake_operation in FUTURE_GATED_OPERATIONS
        or source_input.privacy_class == "internal_repo_future"
        or source_input.readiness_status_class in {
            "requires_capability_lease_future",
            "future_gated",
            "requires_github_source_connector",
            "requires_web_research_gateway",
        }
    )


def _is_low_trust(source_input: RepoAuditSourceIntakeInput) -> bool:
    return source_input.source_trust_class in LOW_TRUST_CLASSES


def _requires_identity(source_input: RepoAuditSourceIntakeInput) -> bool:
    return bool(
        source_input.project_or_repository_scoped
        or source_input.privacy_class in {"private_repo_metadata", "private_repo_content", "internal_repo_future", "sensitive"}
        or source_input.readiness_status_class == "requires_identity_scope"
    )


def _related_status(decision: Any) -> str | None:
    for field in (
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
    failures: list[RepoAuditSourceIntakeFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditSourceIntakeFailure(reason=reason, field=field, message=message))
