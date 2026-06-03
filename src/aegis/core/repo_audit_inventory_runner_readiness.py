from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_INVENTORY_RUNNER_READINESS_VERSION = (
    "repo-audit-inventory-runner-readiness/1"
)
REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_inventory_runner_readiness"
)

ALLOWED_RUNNER_SCOPES = {
    "metadata_only_runner_readiness",
    "path_normalization_runner_readiness",
    "exclusion_enforcement_runner_readiness",
    "budget_enforcement_runner_readiness",
    "read_attempt_evidence_readiness",
    "read_result_envelope_readiness",
    "redaction_boundary_readiness",
    "verifier_postcondition_readiness",
}

FORBIDDEN_RUNNER_SCOPES = {
    "actual_repo_scan",
    "actual_file_read",
    "file_content_read",
    "filesystem_traversal",
    "file_stat_execution",
    "git_ls_files",
    "git_status",
    "test_execution",
    "subprocess_execution",
    "model_assisted_read",
    "tool_assisted_read",
    "api_read",
    "mcp_read",
    "memory_read",
    "report_export",
    "signed_report",
    "audit_report_generation",
    "passport_generation",
    "compliance_evidence_generation",
    "evidence_creation",
    "verifier_success_claim",
    "runtime_dispatch",
    "planner_execution",
}

PLANNED_TARGET_CATEGORIES = {
    "planned_metadata_only_candidate",
    "future_read_candidate",
}

FUTURE_GATED_TARGET_CATEGORIES = {
    "future_gated_hidden_path",
    "future_gated_symlink",
    "future_gated_large_file",
    "future_gated_sensitive_path",
}

DENIED_TARGET_STATUS = {
    "denied_secret_path": "blocked_by_secret_policy",
    "denied_generated_artifact": "blocked_by_generated_artifact_policy",
    "denied_runtime_journal": "blocked_by_runtime_journal_policy",
    "denied_log_path": "blocked_by_log_policy",
    "denied_dependency_path": "blocked_by_dependency_policy",
    "denied_build_cache": "blocked_by_build_artifact_policy",
    "denied_model_artifact": "blocked_by_model_artifact_policy",
    "denied_vector_db": "blocked_by_vector_db_policy",
    "denied_hidden_path": "blocked_by_hidden_path_policy",
    "denied_symlink": "blocked_by_symlink_policy",
    "denied_external_path": "blocked_by_unsafe_read_plan",
    "denied_traversal_path": "blocked_by_unsafe_read_plan",
    "denied_unknown": "blocked_by_unsafe_read_plan",
}

FUTURE_GATED_STATUS = {
    "future_gated_hidden_path": "readiness_ready_requires_human_review",
    "future_gated_symlink": "readiness_ready_requires_human_review",
    "future_gated_large_file": "readiness_ready_requires_human_review",
    "future_gated_sensitive_path": "readiness_ready_requires_human_review",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_readiness": "readiness_cannot_provide_evidence",
    "evidence_provided_by_read_plan": "readiness_cannot_provide_evidence",
    "evidence_provided_by_inventory": "readiness_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "readiness_cannot_provide_evidence",
    "evidence_provided_by_report": "readiness_cannot_provide_evidence",
    "verifier_success": "readiness_cannot_mark_verifier_success",
    "verified_success": "readiness_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "certification_claim": "certification_claim_denied",
    "source_existence_proven": "source_existence_claim_denied",
    "file_content_observed": "file_content_observation_claim_denied",
    "read_result_created": "read_result_creation_denied",
    "read_attempt_evidence_created": "read_attempt_evidence_creation_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "runner_executed": "runner_execution_request_denied",
    "actual_runner_execution": "runner_execution_request_denied",
    "repo_scan_performed": "repo_scan_request_denied",
    "actual_repo_scan": "repo_scan_request_denied",
    "repo_scanning": "repo_scan_request_denied",
    "file_read_performed": "file_read_request_denied",
    "read_repo_files": "file_read_request_denied",
    "file_content_read": "file_read_request_denied",
    "filesystem_traversal_performed": "filesystem_traversal_request_denied",
    "filesystem_traversal_requested": "filesystem_traversal_request_denied",
    "repo_filesystem_walk": "filesystem_traversal_request_denied",
    "stat_performed": "stat_request_denied",
    "file_stat_performed": "stat_request_denied",
    "stat_files": "stat_request_denied",
    "git_command_performed": "git_command_request_denied",
    "run_git": "git_command_request_denied",
    "git_command": "git_command_request_denied",
    "test_execution_performed": "test_execution_request_denied",
    "execute_tests": "test_execution_request_denied",
    "run_tests": "test_execution_request_denied",
    "subprocess_performed": "subprocess_request_denied",
    "subprocess_requested": "subprocess_request_denied",
    "model_call_performed": "model_call_request_denied",
    "model_call_requested": "model_call_request_denied",
    "call_model": "model_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
    "tool_call_requested": "tool_call_request_denied",
    "api_call_performed": "api_call_request_denied",
    "api_call_requested": "api_call_request_denied",
    "external_api_request": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "mcp_call_requested": "mcp_call_request_denied",
    "mcp_tool_call": "mcp_call_request_denied",
    "memory_access_performed": "memory_access_request_denied",
    "memory_access_requested": "memory_access_request_denied",
    "memory_read_requested": "memory_access_request_denied",
    "memory_write_requested": "memory_access_request_denied",
    "report_generated": "report_generation_request_denied",
    "generate_report": "report_generation_request_denied",
    "export_performed": "export_request_denied",
    "export_report": "export_request_denied",
    "sign_report": "report_signing_request_denied",
    "signing_requested": "report_signing_request_denied",
    "audit_report_generated": "audit_report_generation_denied",
    "passport_generated": "passport_generation_denied",
    "compliance_evidence_generated": "compliance_evidence_generation_denied",
}

PROOF_FIELDS = {
    "proof_repo_state": "proof_repo_state_claim_denied",
    "proof_file_exists": "proof_file_exists_claim_denied",
    "proof_file_content": "proof_file_content_claim_denied",
    "proof_tests_passed": "test_success_claim_denied",
    "proof_code_safe": "code_safety_claim_denied",
    "proof_secure": "security_proof_claim_denied",
    "proof_compliant": "compliance_proof_claim_denied",
    "legal_certification": "legal_certification_claim_denied",
    "security_certification": "security_certification_claim_denied",
    "compliance_certification": "compliance_certification_claim_denied",
    "official_audit_result": "official_audit_result_claim_denied",
}

SAFE_READ_PLAN_STATUSES = {"plan_ready", "plan_ready_requires_human_review"}
HUMAN_REVIEW_FAILURES = {
    "budget_excess_requires_human_review",
    "source_inventory_requires_human_review",
}


@dataclass(frozen=True)
class RepoAuditInventoryRunnerReadinessFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditInventoryRunnerSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class RepoAuditInventoryRunnerBudget:
    max_file_count: int | None
    max_file_size_bytes: int | None
    max_total_bytes: int | None
    budget_policy: str | None
    within_readiness_limits: bool
    requires_human_review: bool
    actual_files_counted: bool = False
    actual_bytes_counted: bool = False


@dataclass(frozen=True)
class RepoAuditRunnerContentPolicy:
    content_logging_policy: str | None
    redaction_policy: str | None
    raw_content_logging_default: bool = False
    secrets_never_logged: bool = True
    binary_content_logged: bool = False
    generated_artifact_content_logged: bool = False
    runtime_journal_content_logged: bool = False
    model_vector_content_logged: bool = False
    redaction_required_for_sensitive: bool = True
    excerpts_require_policy: bool = True


@dataclass(frozen=True)
class RepoAuditRunnerReadinessTarget:
    original_path: str
    normalized_relative_path: str | None
    category: str
    readiness_category: str
    decision_reason: str
    denial_reason: str | None = None
    future_gate_reason: str | None = None
    privacy_label: str | None = None
    expected_evidence: tuple[str, ...] = ()
    expected_verifier: tuple[str, ...] = ()
    source_policy_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    human_review_required: bool = True
    source_existence_proven: bool = False
    file_content_observed: bool = False
    file_read_performed: bool = False
    evidence_provided_by_readiness: bool = False
    verifier_success: bool = False


@dataclass(frozen=True)
class RepoAuditFutureReadAttemptEnvelope:
    attempt_id: str
    target_path: str
    normalized_relative_path: str | None
    read_mode: str
    content_logging_allowed: bool = False
    redaction_required: bool = True
    max_bytes: int | None = None
    expected_evidence_type: tuple[str, ...] = ()
    expected_verifier: tuple[str, ...] = ()
    failure_classification: str | None = None
    policy_refs: tuple[str, ...] = ()
    privacy_class: str | None = None
    data_sensitivity: str | None = None
    read_performed: bool = False
    content_observed: bool = False
    evidence_created: bool = False
    verifier_success: bool = False


@dataclass(frozen=True)
class RepoAuditInventoryRunnerReadinessInput:
    request_id: str | None
    project_ref: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    read_plan_ref: str | None
    runner_scope: tuple[str, ...]
    file_access_mode: str | None
    path_normalization_policy: str | None
    secret_exclusion_policy: str | None
    generated_artifact_policy: str | None
    runtime_journal_policy: str | None
    log_policy: str | None
    dependency_policy: str | None
    build_artifact_policy: str | None
    model_artifact_policy: str | None
    vector_db_policy: str | None
    hidden_path_policy: str | None
    symlink_policy: str | None
    privacy_class: str | None
    data_sensitivity: str | None
    evidence_expectation: tuple[str, ...]
    verifier_expectation: tuple[str, ...]
    source_refs: tuple[RepoAuditInventoryRunnerSourceRef, ...]
    policy_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    future_runner_requirements: tuple[str, ...]


@dataclass(frozen=True)
class RepoAuditInventoryRunnerReadinessContract:
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_readiness: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    runner_executed: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
    filesystem_traversal_performed: bool = False
    stat_performed: bool = False
    file_stat_performed: bool = False
    git_command_performed: bool = False
    subprocess_performed: bool = False
    test_execution_performed: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    api_call_performed: bool = False
    mcp_call_performed: bool = False
    memory_access_performed: bool = False
    report_generated: bool = False
    export_performed: bool = False
    certification_claim: bool = False
    source_existence_proven: bool = False
    file_content_observed: bool = False
    read_result_created: bool = False
    read_attempt_evidence_created: bool = False
    read_only_runner_readiness_only: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True


@dataclass(frozen=True)
class RepoAuditInventoryRunnerReadinessDecision:
    contract_version: str
    readiness_status: str
    request_id: str | None
    project_ref: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditInventoryRunnerReadinessFailure, ...]
    readiness_input: RepoAuditInventoryRunnerReadinessInput | None
    readiness_contract: RepoAuditInventoryRunnerReadinessContract
    budget: RepoAuditInventoryRunnerBudget
    content_policy: RepoAuditRunnerContentPolicy
    planned_targets: tuple[RepoAuditRunnerReadinessTarget, ...]
    denied_targets: tuple[RepoAuditRunnerReadinessTarget, ...]
    future_gated_targets: tuple[RepoAuditRunnerReadinessTarget, ...]
    future_read_attempt_envelopes: tuple[RepoAuditFutureReadAttemptEnvelope, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_readiness: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    runner_executed: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
    filesystem_traversal_performed: bool = False
    stat_performed: bool = False
    git_command_performed: bool = False
    subprocess_performed: bool = False
    test_execution_performed: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    api_call_performed: bool = False
    mcp_call_performed: bool = False
    memory_access_performed: bool = False
    report_generated: bool = False
    export_performed: bool = False
    certification_claim: bool = False
    source_existence_proven: bool = False
    file_content_observed: bool = False
    read_result_created: bool = False
    read_attempt_evidence_created: bool = False
    read_only_runner_readiness_only: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True


def validate_repo_audit_inventory_runner_readiness(
    request: Mapping[str, Any] | None,
    *,
    read_plan_decision: Any | None = None,
    source_inventory_decision: Any | None = None,
    implementation_readiness_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> RepoAuditInventoryRunnerReadinessDecision:
    """Validate future inventory-runner readiness from supplied metadata only."""

    failures: list[RepoAuditInventoryRunnerReadinessFailure] = []
    contract = RepoAuditInventoryRunnerReadinessContract()

    if not isinstance(request, Mapping):
        failure = RepoAuditInventoryRunnerReadinessFailure(
            reason="missing_request",
            field="request",
            message="repo audit inventory runner readiness request must be a mapping",
        )
        return _decision(
            readiness_status="clarification_required",
            request_id=None,
            project_ref=None,
            repo_id=None,
            repo_name=None,
            repo_root_ref=None,
            failures=(failure,),
            readiness_input=None,
            readiness_contract=contract,
            budget=_budget_decision(None),
            content_policy=_content_policy({}),
            planned_targets=(),
            denied_targets=(),
            future_gated_targets=(),
            future_read_attempt_envelopes=(),
        )

    data = deepcopy(dict(request))
    read_plan_safe, read_plan_review_required = _validate_read_plan_decision(
        read_plan_decision,
        failures,
    )
    _validate_related_decision("source_inventory", source_inventory_decision, failures)
    _validate_related_decision(
        "implementation_readiness",
        implementation_readiness_decision,
        failures,
    )
    _validate_related_decision("repo_audit", repo_audit_decision, failures)
    _validate_related_decision("mission_control", mission_control_decision, failures)
    _validate_related_decision("tool_simulation", tool_simulation_decision, failures)
    _validate_related_decision(
        "developer_work_passport",
        developer_work_passport_decision,
        failures,
    )
    _validate_related_decision(
        "compliance_evidence",
        compliance_evidence_decision,
        failures,
    )
    _validate_related_decision("plugin_review", plugin_review_decision, failures)

    budget = _budget_decision(_budget_input(data, read_plan_decision))
    content_policy = _content_policy(data)
    planned_targets = _targets_from(data.get("planned_targets"))
    denied_targets = _targets_from(data.get("denied_targets"))
    future_gated_targets = _targets_from(data.get("future_gated_targets"))
    if read_plan_safe:
        if not planned_targets:
            planned_targets = _targets_from(_field(read_plan_decision, "planned_targets"))
        if not denied_targets:
            denied_targets = _targets_from(_field(read_plan_decision, "denied_targets"))
        if not future_gated_targets:
            future_gated_targets = _targets_from(
                _field(read_plan_decision, "future_gated_targets")
            )

    evidence_expectation = (
        _strings(data.get("evidence_expectation"))
        if "evidence_expectation" in data
        else _strings(_field(read_plan_decision, "read_plan_input.evidence_expectation"))
    )
    verifier_expectation = (
        _strings(data.get("verifier_expectation"))
        if "verifier_expectation" in data
        else _strings(_field(read_plan_decision, "read_plan_input.verifier_expectation"))
    )
    request_id = _text(data.get("request_id")) or None
    project_ref = _text(data.get("project_ref")) or _text(data.get("project_scope")) or None
    repo_id = _text(data.get("repo_id")) or None
    repo_name = _text(data.get("repo_name")) or None
    repo_root_ref = _text(data.get("repo_root_ref")) or None
    tenant_scope = _text(data.get("tenant_scope")) or None
    namespace = _text(data.get("namespace")) or None

    readiness_input = RepoAuditInventoryRunnerReadinessInput(
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        read_plan_ref=_text(data.get("read_plan_ref"))
        or _text(_field(read_plan_decision, "request_id"))
        or None,
        runner_scope=_strings(data.get("runner_scope")),
        file_access_mode=_text(data.get("file_access_mode")) or None,
        path_normalization_policy=_text(data.get("path_normalization_policy")) or None,
        secret_exclusion_policy=_policy_value(data, "secret_exclusion_policy"),
        generated_artifact_policy=_policy_value(data, "generated_artifact_policy"),
        runtime_journal_policy=_policy_value(data, "runtime_journal_policy"),
        log_policy=_policy_value(data, "log_policy"),
        dependency_policy=_policy_value(data, "dependency_policy"),
        build_artifact_policy=_policy_value(data, "build_artifact_policy"),
        model_artifact_policy=_policy_value(data, "model_artifact_policy"),
        vector_db_policy=_policy_value(data, "vector_db_policy"),
        hidden_path_policy=_policy_value(data, "hidden_path_policy", "hidden_file_policy"),
        symlink_policy=_policy_value(data, "symlink_policy"),
        privacy_class=_text(data.get("privacy_class")) or None,
        data_sensitivity=_text(data.get("data_sensitivity")) or None,
        evidence_expectation=evidence_expectation,
        verifier_expectation=verifier_expectation,
        source_refs=_source_refs(data.get("source_refs")),
        policy_refs=_strings(data.get("policy_refs")),
        limitations=_strings(data.get("limitations")),
        unknowns=_strings(data.get("unknowns")),
        future_runner_requirements=_strings(data.get("future_runner_requirements")),
    )

    _validate_required_identity(readiness_input, failures)
    _validate_request_fields(data, failures)
    _validate_scopes(readiness_input.runner_scope, failures)
    _validate_context(
        readiness_input,
        read_plan_decision,
        planned_targets,
        denied_targets,
        future_gated_targets,
        failures,
    )
    _validate_budget(budget, failures)
    _validate_policies(readiness_input, content_policy, failures)
    _validate_targets(
        planned_targets,
        denied_targets,
        future_gated_targets,
        failures,
    )
    if read_plan_review_required:
        _add_failure(
            failures,
            "read_plan_requires_human_review",
            "read_plan_decision",
            "read plan requires human review before runner readiness can proceed",
        )
    if budget.requires_human_review:
        _add_failure(
            failures,
            "budget_excess_requires_human_review",
            "budget_policy",
            "runner readiness budget exceeds the design review limit",
        )

    readiness_status = _readiness_status(failures, future_gated_targets, budget)
    if readiness_status.startswith("blocked") or readiness_status == "clarification_required":
        planned_targets = ()

    envelopes = _future_read_attempt_envelopes(
        planned_targets,
        budget,
        readiness_input,
        content_policy,
    )

    return _decision(
        readiness_status=readiness_status,
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        failures=tuple(failures),
        readiness_input=readiness_input,
        readiness_contract=contract,
        budget=budget,
        content_policy=content_policy,
        planned_targets=tuple(planned_targets),
        denied_targets=tuple(denied_targets),
        future_gated_targets=tuple(future_gated_targets),
        future_read_attempt_envelopes=tuple(envelopes),
    )


def _validate_required_identity(
    readiness_input: RepoAuditInventoryRunnerReadinessInput,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if not readiness_input.request_id:
        _add_failure(
            failures,
            "request_identity_required",
            "request_id",
            "runner readiness requires a stable request id",
        )
    if not readiness_input.project_ref or not (
        readiness_input.repo_id or readiness_input.repo_name
    ) or not readiness_input.repo_root_ref:
        _add_failure(
            failures,
            "project_repo_identity_required",
            "project_ref",
            "runner readiness requires caller-supplied project, repo, and root refs",
        )
    if not readiness_input.tenant_scope:
        _add_failure(
            failures,
            "tenant_scope_required",
            "tenant_scope",
            "runner readiness requires tenant scope",
        )
    if not readiness_input.namespace:
        _add_failure(
            failures,
            "namespace_required",
            "namespace",
            "runner readiness requires namespace",
        )


def _validate_context(
    readiness_input: RepoAuditInventoryRunnerReadinessInput,
    read_plan_decision: Any | None,
    planned_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    denied_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    future_gated_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if read_plan_decision is None and not (
        planned_targets or denied_targets or future_gated_targets
    ):
        _add_failure(
            failures,
            "read_plan_or_target_metadata_required",
            "read_plan_decision",
            "runner readiness requires a read plan decision or read-plan target metadata",
        )
    if not readiness_input.read_plan_ref:
        _add_failure(
            failures,
            "read_plan_ref_required",
            "read_plan_ref",
            "runner readiness requires a read plan reference",
        )
    if planned_targets or future_gated_targets:
        if not readiness_input.privacy_class:
            _add_failure(
                failures,
                "privacy_class_required",
                "privacy_class",
                "runner readiness for future targets requires privacy class",
            )
        if not readiness_input.data_sensitivity:
            _add_failure(
                failures,
                "data_sensitivity_required",
                "data_sensitivity",
                "runner readiness for future targets requires data sensitivity",
            )
        if not readiness_input.evidence_expectation:
            _add_failure(
                failures,
                "missing_evidence_expectation",
                "evidence_expectation",
                "future reads require evidence expectations before runner readiness",
            )
        if not readiness_input.verifier_expectation:
            _add_failure(
                failures,
                "missing_verifier_expectation",
                "verifier_expectation",
                "future reads require verifier expectations before runner readiness",
            )


def _validate_scopes(
    scopes: tuple[str, ...],
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if not scopes:
        _add_failure(
            failures,
            "runner_scope_required",
            "runner_scope",
            "runner readiness requires an explicit non-executing scope",
        )
        return
    for scope in scopes:
        if scope in FORBIDDEN_RUNNER_SCOPES:
            _add_failure(
                failures,
                "forbidden_runner_scope_denied",
                "runner_scope",
                f"{scope} is outside inventory runner readiness",
            )
        elif scope not in ALLOWED_RUNNER_SCOPES:
            _add_failure(
                failures,
                "unknown_runner_scope_denied",
                "runner_scope",
                f"{scope} is not an allowed runner readiness scope",
            )


def _validate_request_fields(
    request: Mapping[str, Any],
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    for field_name, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority, evidence, verification, or proof",
            )
    for field_name, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside inventory runner readiness metadata",
            )
    for field_name, reason in PROOF_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is not allowed in runner readiness",
            )
    if _strings(request.get("requested_tools")):
        _add_failure(
            failures,
            "tool_call_request_denied",
            "requested_tools",
            "runner readiness cannot request tools",
        )
    if _strings(request.get("requested_models")) or _strings(request.get("model_roles")):
        _add_failure(
            failures,
            "model_call_request_denied",
            "requested_models",
            "runner readiness cannot request models",
        )
    if _strings(request.get("requested_mcp_tools")):
        _add_failure(
            failures,
            "mcp_call_request_denied",
            "requested_mcp_tools",
            "runner readiness cannot request MCP tools",
        )
    claims = " ".join(_strings(request.get("claims"))).lower()
    for phrase, reason in (
        ("tests passed", "test_success_claim_denied"),
        ("code is safe", "code_safety_claim_denied"),
        ("proof file exists", "proof_file_exists_claim_denied"),
        ("proof file content", "proof_file_content_claim_denied"),
        ("official audit result", "official_audit_result_claim_denied"),
        ("compliance certification", "compliance_certification_claim_denied"),
        ("security certification", "security_certification_claim_denied"),
        ("legal certification", "legal_certification_claim_denied"),
    ):
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"runner readiness cannot claim {phrase}",
            )
    if request.get("execution_permission") not in (
        None,
        "",
        REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_runner_readiness_required",
            "execution_permission",
            "runner readiness cannot grant execution permission",
        )


def _validate_budget(
    budget: RepoAuditInventoryRunnerBudget,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if budget.budget_policy is None:
        _add_failure(
            failures,
            "missing_budget_policy",
            "budget_policy",
            "runner readiness requires budget policy",
        )
    if budget.max_file_count is None:
        _add_failure(
            failures,
            "missing_budget_file_count",
            "budget_policy.max_file_count",
            "runner readiness requires max file count budget",
        )
    if budget.max_file_size_bytes is None:
        _add_failure(
            failures,
            "missing_budget_file_size",
            "budget_policy.max_file_size_bytes",
            "runner readiness requires max file size budget",
        )
    if budget.max_total_bytes is None:
        _add_failure(
            failures,
            "missing_budget_total_bytes",
            "budget_policy.max_total_bytes",
            "runner readiness requires total byte budget",
        )


def _validate_policies(
    readiness_input: RepoAuditInventoryRunnerReadinessInput,
    content_policy: RepoAuditRunnerContentPolicy,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    required_policy_fields = (
        ("file_access_mode", readiness_input.file_access_mode),
        ("path_normalization_policy", readiness_input.path_normalization_policy),
        ("secret_exclusion_policy", readiness_input.secret_exclusion_policy),
        ("generated_artifact_policy", readiness_input.generated_artifact_policy),
        ("runtime_journal_policy", readiness_input.runtime_journal_policy),
        ("log_policy", readiness_input.log_policy),
        ("dependency_policy", readiness_input.dependency_policy),
        ("build_artifact_policy", readiness_input.build_artifact_policy),
        ("model_artifact_policy", readiness_input.model_artifact_policy),
        ("vector_db_policy", readiness_input.vector_db_policy),
        ("hidden_path_policy", readiness_input.hidden_path_policy),
        ("symlink_policy", readiness_input.symlink_policy),
    )
    for field_name, value in required_policy_fields:
        if not value:
            _add_failure(
                failures,
                f"{field_name}_required",
                field_name,
                f"runner readiness requires {field_name}",
            )
    if content_policy.content_logging_policy is None:
        _add_failure(
            failures,
            "content_logging_policy_required",
            "content_logging_policy",
            "runner readiness requires content logging policy",
        )
    if content_policy.redaction_policy is None:
        _add_failure(
            failures,
            "redaction_policy_required",
            "redaction_policy",
            "runner readiness requires redaction policy",
        )
    if content_policy.raw_content_logging_default:
        _add_failure(
            failures,
            "raw_content_logging_default_denied",
            "raw_content_logging_default",
            "runner readiness cannot allow raw content logging by default",
        )
    if content_policy.secrets_never_logged is False:
        _add_failure(
            failures,
            "secret_logging_denied",
            "secrets_never_logged",
            "runner readiness must keep secrets out of logs",
        )
    for field_name, reason in (
        ("binary_content_logged", "binary_content_logging_denied"),
        ("generated_artifact_content_logged", "generated_artifact_content_logging_denied"),
        ("runtime_journal_content_logged", "runtime_journal_content_logging_denied"),
        ("model_vector_content_logged", "model_vector_content_logging_denied"),
    ):
        if getattr(content_policy, field_name):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside runner readiness",
            )
    if content_policy.redaction_required_for_sensitive is False:
        _add_failure(
            failures,
            "sensitive_redaction_required",
            "redaction_required_for_sensitive",
            "sensitive content must require redaction in future runner readiness",
        )


def _validate_targets(
    planned_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    denied_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    future_gated_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    for target in planned_targets:
        if target.category not in PLANNED_TARGET_CATEGORIES:
            _add_failure(
                failures,
                f"planned_target_category_denied_{target.category}",
                "planned_targets",
                "denied or future-gated read-plan targets cannot become planned reads",
            )
        _validate_target_truth_claims(target, "planned_targets", failures)
    for target in denied_targets:
        _validate_target_truth_claims(target, "denied_targets", failures)
        status = DENIED_TARGET_STATUS.get(target.category, "blocked_by_unsafe_read_plan")
        _add_failure(
            failures,
            f"{target.category}_preserved",
            "denied_targets",
            f"{target.category} remains denied and cannot become runner-ready",
        )
        if status == "blocked_by_secret_policy":
            _add_failure(
                failures,
                "secret_path_denied",
                "denied_targets",
                "secret-like read-plan target remains denied",
            )
    for target in future_gated_targets:
        _validate_target_truth_claims(target, "future_gated_targets", failures)
        if target.category not in FUTURE_GATED_TARGET_CATEGORIES:
            _add_failure(
                failures,
                f"future_gated_target_category_denied_{target.category}",
                "future_gated_targets",
                "future-gated target category is not recognized",
            )


def _validate_target_truth_claims(
    target: RepoAuditRunnerReadinessTarget,
    field: str,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if target.source_existence_proven:
        _add_failure(
            failures,
            "target_source_existence_claim_denied",
            field,
            "runner readiness target cannot prove source existence",
        )
    if target.file_content_observed:
        _add_failure(
            failures,
            "target_file_content_observation_claim_denied",
            field,
            "runner readiness target cannot observe file content",
        )
    if target.file_read_performed:
        _add_failure(
            failures,
            "target_file_read_claim_denied",
            field,
            "runner readiness target cannot claim a file read",
        )
    if target.evidence_provided_by_readiness:
        _add_failure(
            failures,
            "target_evidence_claim_denied",
            field,
            "runner readiness target cannot create evidence",
        )
    if target.verifier_success:
        _add_failure(
            failures,
            "target_verifier_success_claim_denied",
            field,
            "runner readiness target cannot verify itself",
        )


def _validate_read_plan_decision(
    decision: Any | None,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> tuple[bool, bool]:
    if decision is None:
        return False, False
    before_count = len(failures)
    _validate_related_decision("read_plan", decision, failures)
    status = _text(_field(decision, "plan_status"))
    if status not in SAFE_READ_PLAN_STATUSES:
        _add_failure(
            failures,
            "read_plan_not_ready",
            "read_plan_decision.plan_status",
            "runner readiness requires a ready or human-review read plan",
        )
    failure_reasons = set(_tuple_field(decision, "failure_reasons"))
    unsafe_reasons = failure_reasons - HUMAN_REVIEW_FAILURES
    if unsafe_reasons:
        _add_failure(
            failures,
            "read_plan_decision_has_failures",
            "read_plan_decision.failure_reasons",
            "read plan failures block runner readiness",
        )
    for field_name in (
        "repo_scan_performed",
        "file_read_performed",
        "filesystem_traversal_performed",
        "stat_performed",
        "git_command_performed",
        "test_execution_performed",
        "subprocess_performed",
        "model_call_performed",
        "tool_call_performed",
        "api_call_performed",
        "mcp_call_performed",
        "memory_access_performed",
        "report_generated",
        "export_performed",
        "evidence_provided_by_read_plan",
        "verifier_success",
        "source_existence_proven",
        "file_content_observed",
    ):
        if _bool_field(decision, field_name):
            _add_failure(
                failures,
                "read_plan_unsafe_behavior_claim_denied",
                f"read_plan_decision.{field_name}",
                "read plan reports behavior outside runner readiness",
            )
    contract = _field(decision, "read_plan_contract")
    for field_name in (
        "repo_scan_performed",
        "file_read_performed",
        "filesystem_traversal_performed",
        "stat_performed",
        "git_command_performed",
        "subprocess_performed",
        "test_execution_performed",
        "model_call_performed",
        "tool_call_performed",
        "api_call_performed",
        "mcp_call_performed",
        "memory_access_performed",
        "report_generated",
        "export_performed",
        "evidence_provided_by_read_plan",
        "verifier_success",
        "source_existence_proven",
        "file_content_observed",
    ):
        if _bool_field(contract, field_name):
            _add_failure(
                failures,
                "read_plan_unsafe_contract_claim_denied",
                f"read_plan_decision.read_plan_contract.{field_name}",
                "read plan contract reports behavior outside runner readiness",
            )
    return len(failures) == before_count, bool(failure_reasons & HUMAN_REVIEW_FAILURES)


def _validate_related_decision(
    prefix: str,
    decision: Any | None,
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
) -> None:
    if decision is None:
        return
    if _bool_field(decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            f"{prefix}_runtime_dispatch_attempt_denied",
            f"{prefix}_decision.runtime_dispatch_allowed",
            f"{prefix} decision cannot grant runner readiness dispatch",
        )
    permission_fields = (
        "authority",
        "approval_grant",
        "capability_grant",
        "lease_grant",
        "frontend_authority",
        "plugin_execution_allowed",
        "dynamic_import_allowed",
        "marketplace_publication_allowed",
        "can_execute",
        "would_dispatch",
        "dispatch_performed",
    )
    if any(_bool_field(decision, field_name) for field_name in permission_fields):
        _add_failure(
            failures,
            f"{prefix}_permission_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot grant runner readiness permissions",
        )
    evidence_fields = (
        "evidence_provided_by_pack_output",
        "evidence_provided_by_readiness",
        "evidence_provided_by_inventory",
        "evidence_provided_by_report",
        "evidence_provided_by_preview",
        "evidence_provided_by_simulation",
        "evidence_created",
        "evidence_provided_by_passport",
        "evidence_provided_by_package",
        "evidence_provided_by_review",
        "evidence_provided_by_read_plan",
        "proof_repo_state",
        "proof_file_exists",
        "source_existence_proven",
        "file_content_observed",
        "read_result_created",
        "read_attempt_evidence_created",
    )
    if any(_bool_field(decision, field_name) for field_name in evidence_fields):
        _add_failure(
            failures,
            f"{prefix}_evidence_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot create runner readiness evidence",
        )
    if _bool_field(decision, "verifier_success") or _bool_field(
        decision,
        "verified_success",
    ) or _bool_field(decision, "pack_output_is_verifier_truth"):
        _add_failure(
            failures,
            f"{prefix}_verifier_success_claim_denied",
            f"{prefix}_decision.verifier_success",
            f"{prefix} decision cannot create verifier success",
        )
    if _bool_field(decision, "success"):
        _add_failure(
            failures,
            f"{prefix}_success_claim_denied",
            f"{prefix}_decision.success",
            f"{prefix} decision cannot create runner readiness success",
        )
    failure_reasons = set(_tuple_field(decision, "failure_reasons"))
    if failure_reasons and not (prefix == "read_plan" and failure_reasons <= HUMAN_REVIEW_FAILURES):
        _add_failure(
            failures,
            f"{prefix}_decision_has_failures",
            f"{prefix}_decision.failure_reasons",
            f"{prefix} decision failures require runner readiness revalidation",
        )


def _future_read_attempt_envelopes(
    planned_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    budget: RepoAuditInventoryRunnerBudget,
    readiness_input: RepoAuditInventoryRunnerReadinessInput,
    content_policy: RepoAuditRunnerContentPolicy,
) -> tuple[RepoAuditFutureReadAttemptEnvelope, ...]:
    envelopes: list[RepoAuditFutureReadAttemptEnvelope] = []
    for index, target in enumerate(planned_targets, start=1):
        envelopes.append(
            RepoAuditFutureReadAttemptEnvelope(
                attempt_id=f"{readiness_input.request_id or 'repo-audit-readiness'}:attempt:{index}",
                target_path=target.original_path,
                normalized_relative_path=target.normalized_relative_path,
                read_mode=(
                    "metadata_only"
                    if target.category == "planned_metadata_only_candidate"
                    else "future_read_only"
                ),
                content_logging_allowed=False,
                redaction_required=True,
                max_bytes=budget.max_file_size_bytes,
                expected_evidence_type=target.expected_evidence
                or readiness_input.evidence_expectation,
                expected_verifier=target.expected_verifier
                or readiness_input.verifier_expectation,
                failure_classification="future_runner_must_emit_negative_evidence_on_failure",
                policy_refs=readiness_input.policy_refs + target.source_policy_refs,
                privacy_class=target.privacy_label or readiness_input.privacy_class,
                data_sensitivity=readiness_input.data_sensitivity,
                read_performed=False,
                content_observed=False,
                evidence_created=False,
                verifier_success=False,
            )
        )
    return tuple(envelopes)


def _readiness_status(
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
    future_gated_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    budget: RepoAuditInventoryRunnerBudget,
) -> str:
    reasons = {failure.reason for failure in failures}
    if "missing_request" in reasons:
        return "clarification_required"
    if any(reason.startswith("read_plan_") for reason in reasons) or {
        "read_plan_or_target_metadata_required",
        "read_plan_ref_required",
    } & reasons:
        return "blocked_by_missing_read_plan"
    if {
        "request_identity_required",
        "project_repo_identity_required",
        "tenant_scope_required",
        "namespace_required",
        "runner_scope_required",
        "unknown_runner_scope_denied",
        "forbidden_runner_scope_denied",
    } & reasons:
        return "blocked_by_missing_scope"
    if any(reason.startswith("missing_budget_") for reason in reasons):
        return "blocked_by_missing_budget"
    if {"privacy_class_required", "data_sensitivity_required"} & reasons:
        return "blocked_by_missing_privacy_class"
    if "missing_evidence_expectation" in reasons:
        return "blocked_by_missing_evidence_expectation"
    if "missing_verifier_expectation" in reasons:
        return "blocked_by_missing_verifier_expectation"
    for category, status in DENIED_TARGET_STATUS.items():
        if f"{category}_preserved" in reasons:
            return status
    if {
        "secret_path_denied",
        "secret_exclusion_policy_required",
    } & reasons:
        return "blocked_by_secret_policy"
    if "generated_artifact_policy_required" in reasons:
        return "blocked_by_generated_artifact_policy"
    if "runtime_journal_policy_required" in reasons:
        return "blocked_by_runtime_journal_policy"
    if "log_policy_required" in reasons:
        return "blocked_by_log_policy"
    if "model_artifact_policy_required" in reasons:
        return "blocked_by_model_artifact_policy"
    if "vector_db_policy_required" in reasons:
        return "blocked_by_vector_db_policy"
    if "dependency_policy_required" in reasons:
        return "blocked_by_dependency_policy"
    if "build_artifact_policy_required" in reasons:
        return "blocked_by_build_artifact_policy"
    if "hidden_path_policy_required" in reasons:
        return "blocked_by_hidden_path_policy"
    if "symlink_policy_required" in reasons:
        return "blocked_by_symlink_policy"
    if any(
        reason.startswith("content_")
        or reason.endswith("_logging_denied")
        or reason == "raw_content_logging_default_denied"
        for reason in reasons
    ):
        return "blocked_by_content_logging_policy"
    if {
        "redaction_policy_required",
        "sensitive_redaction_required",
    } & reasons:
        return "blocked_by_redaction_policy"
    if any(reason.startswith("planned_target_category_denied_") for reason in reasons):
        return "blocked_by_unsafe_related_decision"
    if any(
        reason.endswith("_claim_denied")
        or reason.endswith("_request_denied")
        or reason.endswith("_not_allowed")
        or reason.endswith("_must_be_false")
        or reason.endswith("_denied")
        for reason in reasons
    ):
        return "blocked_by_unsafe_related_decision"
    future_statuses = {
        FUTURE_GATED_STATUS.get(target.category, "readiness_ready_requires_human_review")
        for target in future_gated_targets
    }
    if any(status.startswith("blocked") for status in future_statuses):
        return sorted(status for status in future_statuses if status.startswith("blocked"))[0]
    if future_gated_targets or budget.requires_human_review or "read_plan_requires_human_review" in reasons:
        return "readiness_ready_requires_human_review"
    return "readiness_ready"


def _decision(
    *,
    readiness_status: str,
    request_id: str | None,
    project_ref: str | None,
    repo_id: str | None,
    repo_name: str | None,
    repo_root_ref: str | None,
    failures: tuple[RepoAuditInventoryRunnerReadinessFailure, ...],
    readiness_input: RepoAuditInventoryRunnerReadinessInput | None,
    readiness_contract: RepoAuditInventoryRunnerReadinessContract,
    budget: RepoAuditInventoryRunnerBudget,
    content_policy: RepoAuditRunnerContentPolicy,
    planned_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    denied_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    future_gated_targets: tuple[RepoAuditRunnerReadinessTarget, ...],
    future_read_attempt_envelopes: tuple[RepoAuditFutureReadAttemptEnvelope, ...],
) -> RepoAuditInventoryRunnerReadinessDecision:
    return RepoAuditInventoryRunnerReadinessDecision(
        contract_version=REPO_AUDIT_INVENTORY_RUNNER_READINESS_VERSION,
        readiness_status=readiness_status,
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        readiness_input=readiness_input,
        readiness_contract=readiness_contract,
        budget=budget,
        content_policy=content_policy,
        planned_targets=planned_targets,
        denied_targets=denied_targets,
        future_gated_targets=future_gated_targets,
        future_read_attempt_envelopes=future_read_attempt_envelopes,
    )


def _budget_decision(value: Any | None) -> RepoAuditInventoryRunnerBudget:
    budget = value if isinstance(value, Mapping) else {}
    max_file_count = _int_or_none(budget.get("max_file_count"))
    max_file_size_bytes = _int_or_none(budget.get("max_file_size_bytes"))
    max_total_bytes = _int_or_none(budget.get("max_total_bytes"))
    budget_policy = _text(budget.get("budget_policy")) or None
    exceeds = any(
        value is not None and value > limit
        for value, limit in (
            (max_file_count, 5_000),
            (max_file_size_bytes, 2_000_000),
            (max_total_bytes, 50_000_000),
        )
    )
    return RepoAuditInventoryRunnerBudget(
        max_file_count=max_file_count,
        max_file_size_bytes=max_file_size_bytes,
        max_total_bytes=max_total_bytes,
        budget_policy=budget_policy,
        within_readiness_limits=not exceeds,
        requires_human_review=exceeds
        and budget_policy != "block_above_limits",
        actual_files_counted=False,
        actual_bytes_counted=False,
    )


def _budget_input(request: Mapping[str, Any], read_plan_decision: Any | None) -> Any | None:
    if isinstance(request.get("budget_policy"), Mapping):
        return request.get("budget_policy")
    if isinstance(request.get("budget"), Mapping):
        return request.get("budget")
    read_plan_budget = _field(read_plan_decision, "budget")
    if read_plan_budget is not None:
        return {
            "max_file_count": _field(read_plan_budget, "max_file_count"),
            "max_file_size_bytes": _field(read_plan_budget, "max_file_size_bytes"),
            "max_total_bytes": _field(read_plan_budget, "max_total_bytes"),
            "budget_policy": _field(read_plan_budget, "budget_policy"),
        }
    return None


def _content_policy(request: Mapping[str, Any]) -> RepoAuditRunnerContentPolicy:
    return RepoAuditRunnerContentPolicy(
        content_logging_policy=_text(request.get("content_logging_policy")) or None,
        redaction_policy=_text(request.get("redaction_policy")) or None,
        raw_content_logging_default=bool(request.get("raw_content_logging_default") is True),
        secrets_never_logged=request.get("secrets_never_logged") is not False,
        binary_content_logged=bool(request.get("binary_content_logged") is True),
        generated_artifact_content_logged=bool(
            request.get("generated_artifact_content_logged") is True
        ),
        runtime_journal_content_logged=bool(
            request.get("runtime_journal_content_logged") is True
        ),
        model_vector_content_logged=bool(request.get("model_vector_content_logged") is True),
        redaction_required_for_sensitive=request.get("redaction_required_for_sensitive")
        is not False,
        excerpts_require_policy=request.get("excerpts_require_policy") is not False,
    )


def _targets_from(value: Any) -> tuple[RepoAuditRunnerReadinessTarget, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        values = (value,)
    elif isinstance(value, (str, bytes)):
        return ()
    else:
        try:
            values = tuple(value)
        except TypeError:
            return ()
    targets: list[RepoAuditRunnerReadinessTarget] = []
    for item in values:
        original_path = _text(_field(item, "original_path")) or _text(_field(item, "path"))
        category = _text(_field(item, "category")) or "denied_unknown"
        if not original_path:
            continue
        targets.append(
            RepoAuditRunnerReadinessTarget(
                original_path=original_path,
                normalized_relative_path=_text(_field(item, "normalized_relative_path"))
                or _text(_field(item, "normalized_path"))
                or None,
                category=category,
                readiness_category=_readiness_category(category),
                decision_reason=_text(_field(item, "decision_reason"))
                or _text(_field(item, "denial_reason"))
                or _text(_field(item, "future_gate_reason"))
                or "read_plan_target_preserved",
                denial_reason=_text(_field(item, "denial_reason")) or None,
                future_gate_reason=_text(_field(item, "future_gate_reason")) or None,
                privacy_label=_text(_field(item, "privacy_label")) or None,
                expected_evidence=_strings(_field(item, "expected_evidence")),
                expected_verifier=_strings(_field(item, "expected_verifier")),
                source_policy_refs=_strings(_field(item, "source_policy_refs")),
                limitations=_strings(_field(item, "limitations")),
                unknowns=_strings(_field(item, "unknowns")),
                human_review_required=_field(item, "human_review_required") is not False,
                source_existence_proven=_bool_field(item, "source_existence_proven"),
                file_content_observed=_bool_field(item, "file_content_observed"),
                file_read_performed=_bool_field(item, "file_read_performed"),
                evidence_provided_by_readiness=_bool_field(
                    item,
                    "evidence_provided_by_readiness",
                )
                or _bool_field(item, "evidence_provided_by_read_plan"),
                verifier_success=_bool_field(item, "verifier_success"),
            )
        )
    return tuple(targets)


def _readiness_category(category: str) -> str:
    if category in PLANNED_TARGET_CATEGORIES:
        return "future_read_attempt_envelope_candidate"
    if category in FUTURE_GATED_TARGET_CATEGORIES:
        return "future_gated_target_preserved"
    if category.startswith("denied_"):
        return "denied_target_preserved"
    return "unknown_target_preserved"


def _source_refs(value: Any) -> tuple[RepoAuditInventoryRunnerSourceRef, ...]:
    refs: list[RepoAuditInventoryRunnerSourceRef] = []
    if value is None or isinstance(value, (str, bytes)):
        return ()
    try:
        raw_refs = tuple(value)
    except TypeError:
        return ()
    for raw_ref in raw_refs:
        if isinstance(raw_ref, Mapping):
            ref_id = _text(raw_ref.get("ref_id"))
            ref_type = _text(raw_ref.get("ref_type"))
            description = _text(raw_ref.get("description")) or None
        else:
            ref_id = _text(_field(raw_ref, "ref_id"))
            ref_type = _text(_field(raw_ref, "ref_type"))
            description = _text(_field(raw_ref, "description")) or None
        if ref_id and ref_type:
            refs.append(
                RepoAuditInventoryRunnerSourceRef(
                    ref_id=ref_id,
                    ref_type=ref_type,
                    description=description,
                )
            )
    return tuple(refs)


def _policy_value(request: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = _text(request.get(name))
        if value:
            return value
    return None


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    current = obj
    for part in name.split("."):
        if isinstance(current, Mapping):
            current = current.get(part, default)
        else:
            current = getattr(current, part, default)
        if current is default:
            return default
    return current


def _bool_field(obj: Any, name: str) -> bool:
    return bool(_field(obj, name) is True)


def _tuple_field(obj: Any, name: str) -> tuple[str, ...]:
    return _strings(_field(obj, name))


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, bytes):
        return ()
    try:
        raw_values = tuple(value)
    except TypeError:
        return ()
    result: list[str] = []
    for item in raw_values:
        text = _text(item)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _add_failure(
    failures: list[RepoAuditInventoryRunnerReadinessFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    if reason in {failure.reason for failure in failures}:
        return
    failures.append(
        RepoAuditInventoryRunnerReadinessFailure(
            reason=reason,
            field=field,
            message=message,
        )
    )
