from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_READ_PLAN_VERSION = "repo-audit-future-read-plan/1"
REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_read_plan"
)

MAX_READ_PLAN_FILE_COUNT = 5_000
MAX_READ_PLAN_FILE_SIZE_BYTES = 2_000_000
MAX_READ_PLAN_TOTAL_BYTES = 50_000_000

FUTURE_GATE_POLICIES = {"explicit_future_gate_required", "metadata_only_future"}

SECRET_PATH_MARKERS = {
    ".env",
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "credential",
    "credentials",
    "private_key",
    "private",
}

SECRET_PATH_SUFFIXES = {
    ".env",
    ".env.local",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}

RUNTIME_JOURNAL_PREFIXES = {
    "runtime/",
    "journal/",
    "journals/",
    "evidence/",
    "replay/",
    "archive/",
    "archives/",
}

LOG_PREFIXES = {
    "logs/",
    "log/",
}

DEPENDENCY_PREFIXES = {
    ".git/",
    ".hg/",
    ".svn/",
    ".venv/",
    "venv/",
    "node_modules/",
}

BUILD_CACHE_PREFIXES = {
    ".next/",
    "dist/",
    "build/",
    "coverage/",
    ".pytest_cache/",
    "__pycache__/",
    ".mypy_cache/",
    ".ruff_cache/",
    "cache/",
    "tmp/",
    "temp/",
    "scratch/",
}

MODEL_PREFIXES = {
    "model/",
    "models/",
    "datasets/",
    "dataset/",
    "artifacts/",
}

VECTOR_PREFIXES = {
    "vector_db/",
    "vectordb/",
    "vectors/",
}

MODEL_SUFFIXES = {
    ".gguf",
    ".safetensors",
    ".onnx",
}

VECTOR_SUFFIXES = {
    ".sqlite",
    ".db",
}

BROWSER_OUTPUT_PREFIXES = {
    "screenshots/",
    "browser-output/",
    "browser_outputs/",
    "playwright-report/",
    "test-results/",
}

BROWSER_OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".mp4",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_read_plan": "read_plan_cannot_provide_evidence",
    "evidence_provided_by_inventory": "read_plan_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "read_plan_cannot_provide_evidence",
    "evidence_provided_by_report": "read_plan_cannot_provide_evidence",
    "verifier_success": "read_plan_cannot_mark_verifier_success",
    "verified_success": "read_plan_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "certification_claim": "certification_claim_denied",
    "source_existence_proven": "source_existence_claim_denied",
    "file_content_observed": "file_content_observation_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "repo_scan_performed": "repo_scan_request_denied",
    "actual_repo_scan": "repo_scan_request_denied",
    "actual_source_inventory_performed": "repo_scan_request_denied",
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
}

FORBIDDEN_TEXT_FIELDS = {
    "git_command": "git_command_request_denied",
    "mcp_tool_call": "mcp_call_request_denied",
    "requested_tool": "tool_call_request_denied",
}

PROOF_FIELDS = {
    "proof_repo_state": "proof_repo_state_claim_denied",
    "proof_file_exists": "proof_file_exists_claim_denied",
    "proof_tests_passed": "test_success_claim_denied",
    "proof_code_safe": "code_safety_claim_denied",
    "proof_secure": "security_proof_claim_denied",
    "proof_compliant": "compliance_proof_claim_denied",
    "legal_certification": "legal_certification_claim_denied",
    "security_certification": "security_certification_claim_denied",
    "compliance_certification": "compliance_certification_claim_denied",
}

SOURCE_INVENTORY_BUDGET_REVIEW_REASONS = {
    "budget_file_count_exceeds_review_limit",
    "budget_file_size_exceeds_review_limit",
    "budget_total_bytes_exceeds_review_limit",
}


@dataclass(frozen=True)
class RepoAuditReadPlanFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditReadPlanSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class RepoAuditReadPlanCandidatePath:
    path: str
    path_type: str | None = None
    size_bytes: int | None = None
    is_binary: bool = False
    is_generated: bool = False
    is_hidden: bool = False
    is_symlink: bool = False
    privacy_label: str | None = None
    future_gate_ref: str | None = None
    source_policy_refs: tuple[str, ...] = ()
    metadata_only: bool = False


@dataclass(frozen=True)
class RepoAuditReadPlanBudget:
    max_file_count: int | None
    max_file_size_bytes: int | None
    max_total_bytes: int | None
    budget_policy: str | None
    within_design_limits: bool
    requires_human_review: bool
    actual_files_counted: bool = False
    actual_bytes_counted: bool = False


@dataclass(frozen=True)
class RepoAuditReadPlanInput:
    request_id: str | None
    project_ref: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    source_inventory_decision_ref: str | None
    source_inventory_scope: tuple[str, ...]
    candidate_paths: tuple[RepoAuditReadPlanCandidatePath, ...]
    source_refs: tuple[RepoAuditReadPlanSourceRef, ...]
    policy_refs: tuple[str, ...]
    source_policy_refs: tuple[str, ...]
    privacy_class: str | None
    data_sensitivity: str | None
    secret_exclusion_policy: str | None
    generated_artifact_policy: str | None
    hidden_file_policy: str | None
    symlink_policy: str | None
    evidence_expectation: tuple[str, ...]
    verifier_expectation: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    future_runner_requirements: tuple[str, ...]


@dataclass(frozen=True)
class RepoAuditReadPlanContract:
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_read_plan: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
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
    read_plan_only: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True


@dataclass(frozen=True)
class RepoAuditReadTarget:
    original_path: str
    normalized_relative_path: str | None
    category: str
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
    evidence_provided_by_read_plan: bool = False
    verifier_success: bool = False


@dataclass(frozen=True)
class RepoAuditReadPlanDecision:
    contract_version: str
    plan_status: str
    request_id: str | None
    project_ref: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditReadPlanFailure, ...]
    read_plan_input: RepoAuditReadPlanInput | None
    read_plan_contract: RepoAuditReadPlanContract
    budget: RepoAuditReadPlanBudget
    planned_targets: tuple[RepoAuditReadTarget, ...]
    denied_targets: tuple[RepoAuditReadTarget, ...]
    future_gated_targets: tuple[RepoAuditReadTarget, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_read_plan: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
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
    read_plan_only: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True


def build_repo_audit_future_read_plan(
    request: Mapping[str, Any] | None,
    *,
    source_inventory_decision: Any | None = None,
    implementation_readiness_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> RepoAuditReadPlanDecision:
    """Build a future read plan from caller-supplied metadata only."""

    failures: list[RepoAuditReadPlanFailure] = []
    contract = RepoAuditReadPlanContract()

    if not isinstance(request, Mapping):
        failure = RepoAuditReadPlanFailure(
            reason="missing_request",
            field="request",
            message="repo audit future read plan request must be a mapping",
        )
        return _decision(
            plan_status="clarification_required",
            request_id=None,
            project_ref=None,
            repo_id=None,
            repo_name=None,
            repo_root_ref=None,
            failures=(failure,),
            read_plan_input=None,
            read_plan_contract=contract,
            budget=_budget_decision(None),
            planned_targets=(),
            denied_targets=(),
            future_gated_targets=(),
        )

    data = deepcopy(dict(request))
    source_inventory_safe, source_inventory_review_required = (
        _validate_source_inventory_decision(source_inventory_decision, failures)
    )
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

    request_id = _text(data.get("request_id")) or None
    project_ref = _text(data.get("project_ref")) or _text(data.get("project_scope")) or None
    repo_id = _text(data.get("repo_id")) or None
    repo_name = _text(data.get("repo_name")) or None
    repo_root_ref = _text(data.get("repo_root_ref")) or None
    tenant_scope = _text(data.get("tenant_scope")) or None
    namespace = _text(data.get("namespace")) or None
    evidence_expectation = _strings(data.get("evidence_expectation"))
    verifier_expectation = _strings(data.get("verifier_expectation"))
    source_inventory_scope = _strings(data.get("source_inventory_scope"))
    candidate_paths = _candidate_paths(data.get("candidate_paths"))
    if not candidate_paths and source_inventory_safe:
        candidate_paths = _candidate_paths_from_source_inventory(source_inventory_decision)

    budget = _budget_decision(_budget_input(data, source_inventory_decision))
    read_plan_input = RepoAuditReadPlanInput(
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        source_inventory_decision_ref=_source_inventory_ref(data, source_inventory_decision),
        source_inventory_scope=source_inventory_scope,
        candidate_paths=candidate_paths,
        source_refs=_source_refs(data.get("source_refs")),
        policy_refs=_strings(data.get("policy_refs")),
        source_policy_refs=_strings(data.get("source_policy_refs")),
        privacy_class=_text(data.get("privacy_class")) or None,
        data_sensitivity=_text(data.get("data_sensitivity")) or None,
        secret_exclusion_policy=_policy_value(
            data,
            "secret_exclusion_policy",
            "secret_privacy_policy",
        ),
        generated_artifact_policy=_policy_value(
            data,
            "generated_artifact_policy",
        ),
        hidden_file_policy=_policy_value(
            data,
            "hidden_file_policy",
            "hidden_path_policy",
        ),
        symlink_policy=_policy_value(data, "symlink_policy"),
        evidence_expectation=evidence_expectation,
        verifier_expectation=verifier_expectation,
        limitations=_strings(data.get("limitations")),
        unknowns=_strings(data.get("unknowns")),
        future_runner_requirements=_strings(data.get("future_runner_requirements")),
    )

    _validate_required_identity(read_plan_input, failures)
    _validate_request_fields(data, failures)
    _validate_budget(budget, failures)
    _validate_read_plan_context(read_plan_input, source_inventory_decision, failures)

    planned, denied, future_gated = _classify_candidates(
        read_plan_input.candidate_paths,
        read_plan_input,
        budget,
    )
    for target in denied:
        _add_failure(
            failures,
            target.decision_reason,
            "candidate_paths",
            f"{target.original_path!r} is outside the future read plan boundary",
        )
    if budget.requires_human_review:
        _add_failure(
            failures,
            "budget_excess_requires_human_review",
            "budget_policy",
            "read plan budget exceeds the design review limit",
        )
    if source_inventory_review_required:
        _add_failure(
            failures,
            "source_inventory_requires_human_review",
            "source_inventory_decision",
            "source inventory decision requires human review before future read planning",
        )

    plan_status = _plan_status(
        failures,
        planned,
        denied,
        future_gated,
        budget,
        source_inventory_review_required,
    )
    if plan_status.startswith("blocked") or plan_status == "clarification_required":
        planned = ()

    return _decision(
        plan_status=plan_status,
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        failures=tuple(failures),
        read_plan_input=read_plan_input,
        read_plan_contract=contract,
        budget=budget,
        planned_targets=tuple(planned),
        denied_targets=tuple(denied),
        future_gated_targets=tuple(future_gated),
    )


def _validate_required_identity(
    read_plan_input: RepoAuditReadPlanInput,
    failures: list[RepoAuditReadPlanFailure],
) -> None:
    if not read_plan_input.request_id:
        _add_failure(
            failures,
            "request_identity_required",
            "request_id",
            "future read plan requires a stable request id",
        )
    if not read_plan_input.project_ref or not (
        read_plan_input.repo_id or read_plan_input.repo_name
    ) or not read_plan_input.repo_root_ref:
        _add_failure(
            failures,
            "project_repo_identity_required",
            "project_ref",
            "future read plan requires caller-supplied project, repo, and root refs",
        )
    if not read_plan_input.tenant_scope:
        _add_failure(
            failures,
            "tenant_scope_required",
            "tenant_scope",
            "future read plan requires tenant scope",
        )
    if not read_plan_input.namespace:
        _add_failure(
            failures,
            "namespace_required",
            "namespace",
            "future read plan requires namespace",
        )


def _validate_read_plan_context(
    read_plan_input: RepoAuditReadPlanInput,
    source_inventory_decision: Any | None,
    failures: list[RepoAuditReadPlanFailure],
) -> None:
    if source_inventory_decision is None and not read_plan_input.candidate_paths:
        _add_failure(
            failures,
            "source_inventory_or_candidate_metadata_required",
            "candidate_paths",
            "future read plan requires source inventory decision or candidate path metadata",
        )
    if read_plan_input.candidate_paths:
        if not read_plan_input.privacy_class:
            _add_failure(
                failures,
                "privacy_class_required",
                "privacy_class",
                "future read plan with path candidates requires privacy class",
            )
        if not read_plan_input.data_sensitivity:
            _add_failure(
                failures,
                "data_sensitivity_required",
                "data_sensitivity",
                "future read plan with path candidates requires data sensitivity",
            )
        if not read_plan_input.evidence_expectation:
            _add_failure(
                failures,
                "missing_evidence_expectation",
                "evidence_expectation",
                "future read candidates require evidence expectations",
            )
        if not read_plan_input.verifier_expectation:
            _add_failure(
                failures,
                "missing_verifier_expectation",
                "verifier_expectation",
                "future read candidates require verifier expectations",
            )


def _validate_request_fields(
    request: Mapping[str, Any],
    failures: list[RepoAuditReadPlanFailure],
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
                f"{field_name} is outside future read plan metadata",
            )
    for field_name, reason in FORBIDDEN_TEXT_FIELDS.items():
        if _text(request.get(field_name)):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside future read plan metadata",
            )
    for field_name, reason in PROOF_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is not allowed in a future read plan",
            )
    if _strings(request.get("requested_tools")):
        _add_failure(
            failures,
            "tool_call_request_denied",
            "requested_tools",
            "future read plan cannot request tools",
        )
    if _strings(request.get("requested_models")) or _strings(request.get("model_roles")):
        _add_failure(
            failures,
            "model_call_request_denied",
            "requested_models",
            "future read plan cannot request models",
        )
    if _strings(request.get("requested_mcp_tools")):
        _add_failure(
            failures,
            "mcp_call_request_denied",
            "requested_mcp_tools",
            "future read plan cannot request MCP tools",
        )
    if _strings(request.get("claims")):
        claims = " ".join(_strings(request.get("claims"))).lower()
        for phrase, reason in (
            ("tests passed", "test_success_claim_denied"),
            ("code is safe", "code_safety_claim_denied"),
            ("proof file exists", "proof_file_exists_claim_denied"),
            ("compliance certification", "compliance_certification_claim_denied"),
            ("security certification", "security_certification_claim_denied"),
            ("legal certification", "legal_certification_claim_denied"),
        ):
            if phrase in claims:
                _add_failure(
                    failures,
                    reason,
                    "claims",
                    f"future read plan cannot claim {phrase}",
                )
    if request.get("execution_permission") not in (
        None,
        "",
        REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_read_plan_required",
            "execution_permission",
            "future read plan cannot grant execution permission",
        )


def _validate_budget(
    budget: RepoAuditReadPlanBudget,
    failures: list[RepoAuditReadPlanFailure],
) -> None:
    if budget.budget_policy is None:
        _add_failure(
            failures,
            "missing_budget_policy",
            "budget_policy",
            "future read plan requires budget policy",
        )
    if budget.max_file_count is None:
        _add_failure(
            failures,
            "missing_budget_file_count",
            "budget_policy.max_file_count",
            "future read plan requires max file count budget",
        )
    if budget.max_file_size_bytes is None:
        _add_failure(
            failures,
            "missing_budget_file_size",
            "budget_policy.max_file_size_bytes",
            "future read plan requires max file size budget",
        )
    if budget.max_total_bytes is None:
        _add_failure(
            failures,
            "missing_budget_total_bytes",
            "budget_policy.max_total_bytes",
            "future read plan requires total byte budget",
        )


def _validate_source_inventory_decision(
    decision: Any | None,
    failures: list[RepoAuditReadPlanFailure],
) -> tuple[bool, bool]:
    if decision is None:
        return False, False
    before_count = len(failures)
    _validate_related_decision("source_inventory", decision, failures)
    if _bool_field(decision, "actual_source_inventory_performed") or _bool_field(
        decision,
        "source_existence_proven",
    ):
        _add_failure(
            failures,
            "source_inventory_live_inventory_claim_denied",
            "source_inventory_decision",
            "source inventory decision cannot prove live source state",
        )
    contract = _field(decision, "source_inventory_contract")
    for field_name in (
        "repo_scan_performed",
        "file_read_performed",
        "filesystem_traversal_performed",
        "file_stat_performed",
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
        "evidence_provided_by_inventory",
        "verifier_success",
    ):
        if _bool_field(contract, field_name):
            _add_failure(
                failures,
                "source_inventory_unsafe_behavior_claim_denied",
                f"source_inventory_decision.source_inventory_contract.{field_name}",
                "source inventory decision reports behavior outside read-plan input",
            )
    failure_reasons = set(_tuple_field(decision, "failure_reasons"))
    unsafe_reasons = failure_reasons - SOURCE_INVENTORY_BUDGET_REVIEW_REASONS
    if unsafe_reasons:
        _add_failure(
            failures,
            "source_inventory_decision_has_failures",
            "source_inventory_decision.failure_reasons",
            "source inventory failures block future read planning",
        )
    status = _text(_field(decision, "validation_status"))
    if status and status not in {"design_ready", "requires_human_review"}:
        _add_failure(
            failures,
            "source_inventory_decision_not_design_ready",
            "source_inventory_decision.validation_status",
            "source inventory decision must be design-ready or human-review-only",
        )
    if len(failures) == before_count:
        candidates = _candidate_paths_from_source_inventory(decision)
        for candidate in candidates:
            classification = _classify_path(
                candidate,
                RepoAuditReadPlanInput(
                    request_id=None,
                    project_ref=None,
                    repo_id=None,
                    repo_name=None,
                    repo_root_ref=None,
                    tenant_scope=None,
                    namespace=None,
                    source_inventory_decision_ref=None,
                    source_inventory_scope=(),
                    candidate_paths=(),
                    source_refs=(),
                    policy_refs=(),
                    source_policy_refs=(),
                    privacy_class=None,
                    data_sensitivity=None,
                    secret_exclusion_policy=None,
                    generated_artifact_policy=None,
                    hidden_file_policy="deny_by_default",
                    symlink_policy="blocked",
                    evidence_expectation=(),
                    verifier_expectation=(),
                    limitations=(),
                    unknowns=(),
                    future_runner_requirements=(),
                ),
                _budget_decision(None),
            )
            if classification.category.startswith("denied_"):
                _add_failure(
                    failures,
                    "source_inventory_allowed_forbidden_path_denied",
                    "source_inventory_decision.allowed_path_candidates",
                    "source inventory decision allowed a path denied by read-plan policy",
                )
                break
    return len(failures) == before_count, bool(failure_reasons & SOURCE_INVENTORY_BUDGET_REVIEW_REASONS)


def _validate_related_decision(
    prefix: str,
    decision: Any | None,
    failures: list[RepoAuditReadPlanFailure],
) -> None:
    if decision is None:
        return
    if _bool_field(decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            f"{prefix}_runtime_dispatch_attempt_denied",
            f"{prefix}_decision.runtime_dispatch_allowed",
            f"{prefix} decision cannot grant future read plan dispatch",
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
            f"{prefix} decision cannot grant future read plan permissions",
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
    )
    if any(_bool_field(decision, field_name) for field_name in evidence_fields):
        _add_failure(
            failures,
            f"{prefix}_evidence_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot create future read plan evidence",
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
            f"{prefix} decision cannot create future read plan success",
        )
    failure_reasons = set(_tuple_field(decision, "failure_reasons"))
    if failure_reasons and not (
        prefix == "source_inventory"
        and failure_reasons <= SOURCE_INVENTORY_BUDGET_REVIEW_REASONS
    ):
        _add_failure(
            failures,
            f"{prefix}_decision_has_failures",
            f"{prefix}_decision.failure_reasons",
            f"{prefix} decision failures require future read plan revalidation",
        )


def _classify_candidates(
    candidates: tuple[RepoAuditReadPlanCandidatePath, ...],
    read_plan_input: RepoAuditReadPlanInput,
    budget: RepoAuditReadPlanBudget,
) -> tuple[
    tuple[RepoAuditReadTarget, ...],
    tuple[RepoAuditReadTarget, ...],
    tuple[RepoAuditReadTarget, ...],
]:
    planned: list[RepoAuditReadTarget] = []
    denied: list[RepoAuditReadTarget] = []
    future_gated: list[RepoAuditReadTarget] = []
    for candidate in candidates:
        classification = _classify_path(candidate, read_plan_input, budget)
        target = RepoAuditReadTarget(
            original_path=candidate.path,
            normalized_relative_path=classification.normalized_path,
            category=classification.category,
            decision_reason=classification.reason,
            denial_reason=classification.reason if classification.category.startswith("denied_") else None,
            future_gate_reason=(
                classification.reason
                if classification.category.startswith("future_gated_")
                else None
            ),
            privacy_label=candidate.privacy_label or read_plan_input.privacy_class,
            expected_evidence=read_plan_input.evidence_expectation,
            expected_verifier=read_plan_input.verifier_expectation,
            source_policy_refs=_dedupe(
                candidate.source_policy_refs + read_plan_input.source_policy_refs
            ),
            limitations=read_plan_input.limitations,
            unknowns=(
                read_plan_input.unknowns
                or ("candidate path is caller supplied; existence not proven",)
            ),
        )
        if target.category.startswith("denied_"):
            denied.append(target)
        elif target.category.startswith("future_gated_"):
            future_gated.append(target)
        else:
            planned.append(target)
    return tuple(planned), tuple(denied), tuple(future_gated)


@dataclass(frozen=True)
class _PathClassification:
    normalized_path: str | None
    category: str
    reason: str


def _classify_path(
    candidate: RepoAuditReadPlanCandidatePath,
    read_plan_input: RepoAuditReadPlanInput,
    budget: RepoAuditReadPlanBudget,
) -> _PathClassification:
    raw_path = _text(candidate.path).replace("\\", "/")
    if not raw_path:
        return _PathClassification(None, "denied_unknown", "empty_path_denied")
    if any(ord(character) < 32 for character in raw_path):
        return _PathClassification(raw_path, "denied_unknown", "path_control_character_denied")
    lowered_raw = raw_path.lower()
    if lowered_raw.startswith(("file://", "http://", "https://", "s3://", "gs://")):
        return _PathClassification(raw_path, "denied_external_path", "external_path_denied")
    if _is_drive_root(raw_path):
        return _PathClassification(raw_path, "denied_external_path", "drive_root_path_denied")
    if raw_path.startswith("//"):
        return _PathClassification(raw_path, "denied_external_path", "unc_path_denied")
    if raw_path.startswith("/") or _is_windows_absolute_path(raw_path):
        return _PathClassification(raw_path, "denied_external_path", "absolute_path_denied")
    if raw_path.startswith("~"):
        return _PathClassification(raw_path, "denied_external_path", "home_relative_path_denied")

    normalized = _collapse_slashes(raw_path)
    lowered = normalized.lower()
    if _has_path_traversal(normalized):
        return _PathClassification(normalized, "denied_traversal_path", "path_traversal_denied")
    if _is_secret_path(lowered):
        return _PathClassification(normalized, "denied_secret_path", "secret_path_denied")
    if _starts_with_any(lowered, LOG_PREFIXES) or lowered.endswith(".log"):
        return _PathClassification(normalized, "denied_log_path", "log_path_denied")
    if _starts_with_any(lowered, RUNTIME_JOURNAL_PREFIXES) or "runtime_events.jsonl" in lowered:
        return _PathClassification(
            normalized,
            "denied_runtime_journal",
            "runtime_journal_path_denied",
        )
    if _starts_with_any(lowered, DEPENDENCY_PREFIXES):
        return _PathClassification(
            normalized,
            "denied_dependency_path",
            "dependency_path_denied",
        )
    if _starts_with_any(lowered, BUILD_CACHE_PREFIXES):
        return _PathClassification(
            normalized,
            "denied_build_cache",
            "build_cache_path_denied",
        )
    if _starts_with_any(lowered, VECTOR_PREFIXES) or _ends_with_any(lowered, VECTOR_SUFFIXES):
        return _PathClassification(normalized, "denied_vector_db", "vector_db_path_denied")
    if _starts_with_any(lowered, MODEL_PREFIXES) or _ends_with_any(lowered, MODEL_SUFFIXES):
        return _PathClassification(
            normalized,
            "denied_model_artifact",
            "model_artifact_path_denied",
        )
    if _starts_with_any(lowered, BROWSER_OUTPUT_PREFIXES) or _ends_with_any(
        lowered,
        BROWSER_OUTPUT_SUFFIXES,
    ):
        return _PathClassification(
            normalized,
            "denied_generated_artifact",
            "browser_output_or_screenshot_path_denied",
        )
    if candidate.is_generated or candidate.is_binary:
        return _PathClassification(
            normalized,
            "denied_generated_artifact",
            "generated_artifact_path_denied",
        )
    if _is_hidden_path(normalized) or candidate.is_hidden:
        if _future_gate_allows(read_plan_input.hidden_file_policy, candidate.future_gate_ref):
            return _PathClassification(
                normalized,
                "future_gated_hidden_path",
                "hidden_path_requires_future_gate",
            )
        return _PathClassification(normalized, "denied_hidden_path", "hidden_path_denied")
    if candidate.is_symlink:
        if _future_gate_allows(read_plan_input.symlink_policy, candidate.future_gate_ref):
            return _PathClassification(
                normalized,
                "future_gated_symlink",
                "symlink_requires_future_gate",
            )
        return _PathClassification(normalized, "denied_symlink", "symlink_path_denied")
    if candidate.size_bytes is not None and budget.max_file_size_bytes is not None:
        if candidate.size_bytes > budget.max_file_size_bytes:
            return _PathClassification(
                normalized,
                "future_gated_large_file",
                "large_file_requires_future_gate",
            )
    privacy_label = _text(candidate.privacy_label).lower()
    if privacy_label in {"personal_data", "sensitive", "regulated", "secret_adjacent"}:
        if _future_gate_allows(_policy_value_from_input(read_plan_input, "sensitive"), candidate.future_gate_ref):
            return _PathClassification(
                normalized,
                "future_gated_sensitive_path",
                "sensitive_path_requires_future_gate",
            )
        return _PathClassification(normalized, "denied_unknown", "sensitive_path_denied")
    if candidate.metadata_only:
        return _PathClassification(
            normalized,
            "planned_metadata_only_candidate",
            "metadata_only_candidate",
        )
    return _PathClassification(normalized, "future_read_candidate", "future_read_candidate")


def _plan_status(
    failures: list[RepoAuditReadPlanFailure],
    planned_targets: tuple[RepoAuditReadTarget, ...],
    denied_targets: tuple[RepoAuditReadTarget, ...],
    future_gated_targets: tuple[RepoAuditReadTarget, ...],
    budget: RepoAuditReadPlanBudget,
    source_inventory_review_required: bool,
) -> str:
    reasons = {failure.reason for failure in failures}
    if "missing_request" in reasons or "source_inventory_or_candidate_metadata_required" in reasons:
        return "clarification_required"
    if {
        "request_identity_required",
        "project_repo_identity_required",
        "tenant_scope_required",
        "namespace_required",
    } & reasons:
        return "blocked_by_missing_scope"
    if {
        "missing_budget_policy",
        "missing_budget_file_count",
        "missing_budget_file_size",
        "missing_budget_total_bytes",
    } & reasons:
        return "blocked_by_missing_budget"
    if "missing_evidence_expectation" in reasons:
        return "blocked_by_missing_evidence_expectation"
    if "missing_verifier_expectation" in reasons:
        return "blocked_by_missing_verifier_expectation"
    if any(reason.startswith("source_inventory_") for reason in reasons):
        if source_inventory_review_required and reasons <= {
            "source_inventory_requires_human_review",
            "budget_excess_requires_human_review",
        }:
            return "plan_ready_requires_human_review"
        return "blocked_by_source_inventory"
    if any(reason.endswith("_decision_has_failures") for reason in reasons) or any(
        "_runtime_dispatch_attempt_denied" in reason
        or "_permission_claim_denied" in reason
        or "_evidence_claim_denied" in reason
        or "_verifier_success_claim_denied" in reason
        or "_success_claim_denied" in reason
        for reason in reasons
    ):
        return "blocked_by_unsafe_related_decision"
    if "secret_path_denied" in reasons:
        return "blocked_by_secret_policy"
    if {
        "generated_artifact_path_denied",
        "browser_output_or_screenshot_path_denied",
    } & reasons:
        return "blocked_by_generated_artifact_policy"
    if "runtime_journal_path_denied" in reasons or "log_path_denied" in reasons:
        return "blocked_by_runtime_journal_policy"
    if "hidden_path_denied" in reasons:
        return "blocked_by_hidden_path_policy"
    if "symlink_path_denied" in reasons:
        return "blocked_by_symlink_policy"
    if "sensitive_path_denied" in reasons or {
        "privacy_class_required",
        "data_sensitivity_required",
    } & reasons:
        return "blocked_by_privacy_policy"
    if budget.requires_human_review and _budget_policy_blocks(budget):
        return "blocked_by_budget_excess"
    if {
        "absolute_path_denied",
        "drive_root_path_denied",
        "unc_path_denied",
        "external_path_denied",
        "home_relative_path_denied",
        "path_traversal_denied",
        "empty_path_denied",
        "path_control_character_denied",
        "dependency_path_denied",
        "build_cache_path_denied",
        "model_artifact_path_denied",
        "vector_db_path_denied",
        "source_inventory_allowed_forbidden_path_denied",
    } & reasons:
        return "blocked_by_path_policy"
    if {
        "repo_scan_request_denied",
        "file_read_request_denied",
        "filesystem_traversal_request_denied",
        "stat_request_denied",
        "git_command_request_denied",
        "test_execution_request_denied",
        "subprocess_request_denied",
        "model_call_request_denied",
        "tool_call_request_denied",
        "api_call_request_denied",
        "mcp_call_request_denied",
        "memory_access_request_denied",
        "report_generation_request_denied",
        "export_request_denied",
        "report_signing_request_denied",
        "authority_must_be_false",
        "runtime_dispatch_not_allowed",
        "approval_grant_not_allowed",
        "capability_grant_not_allowed",
        "lease_grant_not_allowed",
        "read_plan_cannot_provide_evidence",
        "read_plan_cannot_mark_verifier_success",
        "success_claim_denied",
        "certification_claim_denied",
        "proof_repo_state_claim_denied",
        "proof_file_exists_claim_denied",
        "test_success_claim_denied",
        "code_safety_claim_denied",
        "security_proof_claim_denied",
        "compliance_proof_claim_denied",
        "execution_permission_not_granted_by_read_plan_required",
    } & reasons:
        return "blocked_by_unsafe_related_decision"
    if not planned_targets and not future_gated_targets and denied_targets:
        return "blocked_by_path_policy"
    if future_gated_targets or budget.requires_human_review or source_inventory_review_required:
        return "plan_ready_requires_human_review"
    return "plan_ready"


def _budget_policy_blocks(budget: RepoAuditReadPlanBudget) -> bool:
    return budget.budget_policy in {
        "block_above_limits",
        "blocked_above_limits",
        "deny_above_limits",
    }


def _decision(
    *,
    plan_status: str,
    request_id: str | None,
    project_ref: str | None,
    repo_id: str | None,
    repo_name: str | None,
    repo_root_ref: str | None,
    failures: tuple[RepoAuditReadPlanFailure, ...],
    read_plan_input: RepoAuditReadPlanInput | None,
    read_plan_contract: RepoAuditReadPlanContract,
    budget: RepoAuditReadPlanBudget,
    planned_targets: tuple[RepoAuditReadTarget, ...],
    denied_targets: tuple[RepoAuditReadTarget, ...],
    future_gated_targets: tuple[RepoAuditReadTarget, ...],
) -> RepoAuditReadPlanDecision:
    return RepoAuditReadPlanDecision(
        contract_version=REPO_AUDIT_READ_PLAN_VERSION,
        plan_status=plan_status,
        request_id=request_id,
        project_ref=project_ref,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=repo_root_ref,
        failure_reasons=tuple(dict.fromkeys(failure.reason for failure in failures)),
        failures=failures,
        read_plan_input=read_plan_input,
        read_plan_contract=read_plan_contract,
        budget=budget,
        planned_targets=planned_targets,
        denied_targets=denied_targets,
        future_gated_targets=future_gated_targets,
    )


def _candidate_paths(value: Any) -> tuple[RepoAuditReadPlanCandidatePath, ...]:
    candidates: list[RepoAuditReadPlanCandidatePath] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            candidates.append(
                RepoAuditReadPlanCandidatePath(
                    path=_text(item.get("path")) or _text(item.get("path_ref")),
                    path_type=_text(item.get("path_type")) or None,
                    size_bytes=_int_or_none(item.get("size_bytes")),
                    is_binary=item.get("is_binary") is True,
                    is_generated=item.get("is_generated") is True,
                    is_hidden=item.get("is_hidden") is True,
                    is_symlink=item.get("is_symlink") is True,
                    privacy_label=_text(item.get("privacy_label")) or None,
                    future_gate_ref=_text(item.get("future_gate_ref")) or None,
                    source_policy_refs=_strings(item.get("source_policy_refs")),
                    metadata_only=item.get("metadata_only") is True,
                )
            )
        else:
            candidates.append(RepoAuditReadPlanCandidatePath(path=_text(item)))
    return tuple(candidates)


def _candidate_paths_from_source_inventory(decision: Any | None) -> tuple[RepoAuditReadPlanCandidatePath, ...]:
    candidates: list[RepoAuditReadPlanCandidatePath] = []
    for item in _tuple_field(decision, "allowed_path_candidates"):
        candidates.append(
            RepoAuditReadPlanCandidatePath(
                path=_text(_field(item, "normalized_path")) or _text(_field(item, "path")),
                path_type=_text(_field(item, "path_type")) or None,
                metadata_only=_bool_field(item, "metadata_only"),
            )
        )
    return tuple(candidates)


def _budget_input(
    request: Mapping[str, Any],
    source_inventory_decision: Any | None,
) -> Mapping[str, Any] | None:
    budget = request.get("budget_policy") or request.get("budget")
    if isinstance(budget, Mapping):
        return budget
    source_budget = _field(source_inventory_decision, "budget_decision")
    if source_budget:
        return {
            "max_file_count": _field(source_budget, "max_file_count"),
            "max_file_size_bytes": _field(source_budget, "max_file_size_bytes"),
            "max_total_bytes": _field(source_budget, "max_total_bytes"),
            "budget_policy": _field(source_budget, "budget_policy"),
        }
    return None


def _budget_decision(value: Mapping[str, Any] | None) -> RepoAuditReadPlanBudget:
    if value is None:
        return RepoAuditReadPlanBudget(
            max_file_count=None,
            max_file_size_bytes=None,
            max_total_bytes=None,
            budget_policy=None,
            within_design_limits=False,
            requires_human_review=True,
        )
    max_file_count = _int_or_none(value.get("max_file_count"))
    max_file_size_bytes = _int_or_none(value.get("max_file_size_bytes"))
    max_total_bytes = _int_or_none(value.get("max_total_bytes"))
    budget_policy = _text(value.get("budget_policy")) or None
    requires_human_review = any(
        item is not None and item > limit
        for item, limit in (
            (max_file_count, MAX_READ_PLAN_FILE_COUNT),
            (max_file_size_bytes, MAX_READ_PLAN_FILE_SIZE_BYTES),
            (max_total_bytes, MAX_READ_PLAN_TOTAL_BYTES),
        )
    )
    complete = (
        max_file_count is not None
        and max_file_size_bytes is not None
        and max_total_bytes is not None
        and budget_policy is not None
    )
    return RepoAuditReadPlanBudget(
        max_file_count=max_file_count,
        max_file_size_bytes=max_file_size_bytes,
        max_total_bytes=max_total_bytes,
        budget_policy=budget_policy,
        within_design_limits=complete and not requires_human_review,
        requires_human_review=requires_human_review,
    )


def _source_inventory_ref(request: Mapping[str, Any], decision: Any | None) -> str | None:
    return (
        _text(request.get("source_inventory_decision_ref"))
        or _text(_field(decision, "inventory_id"))
        or None
    )


def _policy_value(request: Mapping[str, Any], *field_names: str) -> str | None:
    policy = request.get("path_policy")
    if not isinstance(policy, Mapping):
        policy = {}
    for field_name in field_names:
        value = _text(request.get(field_name)) or _text(policy.get(field_name))
        if value:
            return value
    return None


def _policy_value_from_input(read_plan_input: RepoAuditReadPlanInput, kind: str) -> str | None:
    if kind == "sensitive":
        return "explicit_future_gate_required"
    return None


def _source_refs(value: Any) -> tuple[RepoAuditReadPlanSourceRef, ...]:
    refs: list[RepoAuditReadPlanSourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                RepoAuditReadPlanSourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            ref_id = _text(item)
            if ref_id:
                refs.append(RepoAuditReadPlanSourceRef(ref_id=ref_id, ref_type="unspecified"))
    return tuple(refs)


def _is_drive_root(path: str) -> bool:
    return len(path) in {2, 3} and path[1:2] == ":" and (len(path) == 2 or path[2] == "/")


def _is_windows_absolute_path(path: str) -> bool:
    return len(path) >= 3 and path[1] == ":" and path[2] == "/"


def _has_path_traversal(path: str) -> bool:
    return ".." in [part.strip() for part in path.split("/")]


def _is_secret_path(lowered_path: str) -> bool:
    parts = [part for part in lowered_path.split("/") if part]
    if any(part in SECRET_PATH_SUFFIXES for part in parts):
        return True
    if any(lowered_path.endswith(suffix) for suffix in SECRET_PATH_SUFFIXES):
        return True
    return any(marker in lowered_path for marker in SECRET_PATH_MARKERS)


def _is_hidden_path(path: str) -> bool:
    return any(part.startswith(".") for part in path.split("/") if part)


def _starts_with_any(path: str, prefixes: set[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _ends_with_any(path: str, suffixes: set[str]) -> bool:
    return any(path.endswith(suffix) for suffix in suffixes)


def _collapse_slashes(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    return "/".join(parts)


def _future_gate_allows(policy: str | None, future_gate_ref: str | None) -> bool:
    return policy in FUTURE_GATE_POLICIES and bool(_text(future_gate_ref))


def _field(value: Any, field_name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _tuple_field(value: Any, field_name: str) -> tuple[Any, ...]:
    raw = _field(value, field_name)
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)


def _bool_field(value: Any, field_name: str) -> bool:
    return _field(value, field_name) is True


def _items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


def _strings(value: Any) -> tuple[str, ...]:
    strings: list[str] = []
    for item in _items(value):
        text = _text(item)
        if text:
            strings.append(text)
    return tuple(strings)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _add_failure(
    failures: list[RepoAuditReadPlanFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditReadPlanFailure(reason=reason, field=field, message=message))
