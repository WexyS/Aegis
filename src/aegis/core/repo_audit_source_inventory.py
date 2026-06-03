from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_SOURCE_INVENTORY_DESIGN_VERSION = "repo-audit-source-inventory-design/1"
REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_source_inventory_design"
)

MAX_REVIEW_FILE_COUNT = 5_000
MAX_REVIEW_FILE_SIZE_BYTES = 2_000_000
MAX_REVIEW_TOTAL_BYTES = 50_000_000

ALLOWED_SOURCE_INVENTORY_SCOPES = {
    "source_inventory_design",
    "path_policy_validation",
    "exclusion_policy_validation",
    "source_budget_validation",
    "metadata_only_inventory_candidate",
    "generated_artifact_exclusion_design",
    "secret_exclusion_design",
    "symlink_policy_design",
    "hidden_file_policy_design",
    "future_read_plan_candidate",
}

FORBIDDEN_SOURCE_INVENTORY_SCOPES = {
    "actual_source_inventory",
    "repo_filesystem_walk",
    "file_content_read",
    "file_stat_execution",
    "git_ls_files",
    "git_status",
    "test_execution",
    "dependency_install",
    "model_assisted_inventory",
    "external_api_inventory",
    "report_export",
    "signed_inventory",
    "evidence_creation",
    "verifier_success_claim",
    "proof_repo_state",
    "proof_file_exists",
    "proof_tests_passed",
    "proof_code_safe",
    "proof_secure",
    "proof_compliant",
}

HIGH_RISK_SOURCE_INVENTORY_SCOPES = {
    "generated_artifact_exclusion_design",
    "secret_exclusion_design",
    "future_read_plan_candidate",
}

ALLOWED_GENERATED_ARTIFACT_POLICIES = {
    "deny_by_default",
    "explicit_future_gate_required",
    "metadata_only",
    "blocked",
}
ALLOWED_SECRET_PRIVACY_POLICIES = {
    "deny_by_default",
    "explicit_allowlist_required",
    "blocked",
}
ALLOWED_HIDDEN_PATH_POLICIES = {
    "deny_by_default",
    "metadata_only_future",
    "explicit_future_gate_required",
    "blocked",
}
ALLOWED_SYMLINK_POLICIES = {
    "blocked",
    "metadata_only_future",
    "explicit_future_gate_required",
}
ALLOWED_BLOCKING_POLICIES = {
    "deny_by_default",
    "explicit_future_gate_required",
    "metadata_only",
    "blocked",
}

FORBIDDEN_EXECUTION_FIELDS = {
    "actual_source_inventory_performed": "repo_scan_request_denied",
    "actual_source_inventory": "repo_scan_request_denied",
    "repo_scan_performed": "repo_scan_request_denied",
    "repo_scanning": "repo_scan_request_denied",
    "file_read_performed": "file_read_request_denied",
    "read_repo_files": "file_read_request_denied",
    "file_content_read": "file_read_request_denied",
    "filesystem_traversal_performed": "filesystem_traversal_request_denied",
    "filesystem_traversal_requested": "filesystem_traversal_request_denied",
    "repo_filesystem_walk": "filesystem_traversal_request_denied",
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
    "signed_inventory_requested": "signed_inventory_request_denied",
    "sign_inventory": "signed_inventory_request_denied",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_inventory": "inventory_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "inventory_cannot_provide_evidence",
    "verifier_success": "inventory_cannot_mark_verifier_success",
    "verified_success": "inventory_cannot_mark_verifier_success",
    "success": "success_claim_denied",
}

FORBIDDEN_PROOF_FIELDS = {
    "proof_repo_state": "proof_repo_state_claim_denied",
    "proof_file_exists": "proof_file_exists_claim_denied",
    "proof_tests_passed": "test_success_claim_denied",
    "proof_code_safe": "code_safety_claim_denied",
    "proof_secure": "security_proof_claim_denied",
    "proof_compliant": "compliance_proof_claim_denied",
}

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

RUNTIME_OR_LOG_PREFIXES = {
    "logs/",
    "runtime/",
    "journal/",
    "journals/",
    "evidence/",
    "replay/",
}

GENERATED_OR_CACHE_PREFIXES = {
    ".git/",
    ".hg/",
    ".svn/",
    ".venv/",
    "venv/",
    "node_modules/",
    ".next/",
    "dist/",
    "build/",
    "coverage/",
    ".pytest_cache/",
    "__pycache__/",
    ".mypy_cache/",
    ".ruff_cache/",
    "scratch/",
    "tmp/",
    "temp/",
}

MODEL_VECTOR_DATASET_PREFIXES = {
    "model/",
    "models/",
    "vector_db/",
    "vectordb/",
    "vectors/",
    "datasets/",
    "dataset/",
    "artifacts/",
}

MODEL_VECTOR_DATASET_SUFFIXES = {
    ".gguf",
    ".safetensors",
    ".onnx",
    ".sqlite",
    ".db",
}

SCREENSHOT_BROWSER_OUTPUT_PREFIXES = {
    "screenshots/",
    "browser-output/",
    "browser_outputs/",
    "playwright-report/",
    "test-results/",
}

SCREENSHOT_BROWSER_OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".mp4",
}


@dataclass(frozen=True)
class SourceInventoryFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class SourceInventorySourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class SourceInventoryCandidatePath:
    path: str
    path_type: str | None = None
    size_bytes: int | None = None
    is_binary: bool = False
    is_generated: bool = False
    is_hidden: bool = False
    is_symlink: bool = False
    future_gate_ref: str | None = None


@dataclass(frozen=True)
class SourceInventoryPathPolicy:
    allowed_prefixes: tuple[str, ...]
    allow_repo_root_files: bool
    forbidden_paths: tuple[str, ...]
    forbidden_extensions: tuple[str, ...]
    generated_artifact_policy: str | None
    secret_privacy_policy: str | None
    hidden_path_policy: str | None
    symlink_policy: str | None
    external_path_policy: str | None
    path_traversal_policy: str | None
    runtime_log_policy: str | None
    model_vector_policy: str | None
    browser_output_policy: str | None
    dependency_build_policy: str | None


@dataclass(frozen=True)
class SourceInventoryBudget:
    max_file_count: int | None
    max_file_size_bytes: int | None
    max_total_bytes: int | None
    budget_policy: str | None


@dataclass(frozen=True)
class RepoAuditSourceInventoryInput:
    inventory_id: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    commit_ref: str | None
    branch_ref: str | None
    tenant_scope: str | None
    project_scope: str | None
    namespace: str | None
    source_refs: tuple[SourceInventorySourceRef, ...]
    source_inventory_scope: tuple[str, ...]
    candidate_paths: tuple[SourceInventoryCandidatePath, ...]
    path_policy: SourceInventoryPathPolicy
    budget: SourceInventoryBudget
    output_categories: tuple[str, ...]
    privacy_class: str | None
    data_sensitivity: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class SourceInventoryContract:
    design_only: bool = True
    actual_source_inventory_performed: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
    filesystem_traversal_performed: bool = False
    file_stat_performed: bool = False
    git_command_performed: bool = False
    test_execution_performed: bool = False
    subprocess_performed: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    api_call_performed: bool = False
    mcp_call_performed: bool = False
    memory_access_performed: bool = False
    report_generated: bool = False
    export_performed: bool = False
    evidence_provided_by_inventory: bool = False
    verifier_success: bool = False


@dataclass(frozen=True)
class SourceInventoryAllowedPathCandidate:
    path: str
    normalized_path: str
    path_type: str | None
    metadata_only: bool = True
    exists_confirmed: bool = False
    file_read_performed: bool = False
    file_stat_performed: bool = False
    evidence_provided_by_inventory: bool = False
    verifier_success: bool = False


@dataclass(frozen=True)
class SourceInventoryDeniedPath:
    path: str
    normalized_path: str
    reason: str
    category: str


@dataclass(frozen=True)
class SourceInventoryBudgetDecision:
    max_file_count: int | None
    max_file_size_bytes: int | None
    max_total_bytes: int | None
    budget_policy: str | None
    within_design_limits: bool
    requires_human_review: bool
    actual_bytes_counted: bool = False
    actual_files_counted: bool = False


@dataclass(frozen=True)
class SourceInventoryFutureReadPlan:
    future_read_plan_candidate: bool
    plan_id: str | None
    requires_boundary_approval: bool
    requires_evidence_boundary: bool
    requires_verifier_boundary: bool
    can_read_now: bool = False


@dataclass(frozen=True)
class SourceInventoryFinding:
    finding_type: str
    summary: str
    evidence_provided: bool = False
    verifier_success: bool = False
    requires_human_review: bool = True


@dataclass(frozen=True)
class SourceInventoryDecision:
    contract_version: str
    validation_status: str
    inventory_id: str | None
    repo_id: str | None
    repo_name: str | None
    source_inventory_scope: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[SourceInventoryFailure, ...]
    source_inventory_input: RepoAuditSourceInventoryInput | None
    source_inventory_contract: SourceInventoryContract
    allowed_path_candidates: tuple[SourceInventoryAllowedPathCandidate, ...]
    denied_paths: tuple[SourceInventoryDeniedPath, ...]
    budget_decision: SourceInventoryBudgetDecision
    future_read_plan: SourceInventoryFutureReadPlan
    findings: tuple[SourceInventoryFinding, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    execution_permission: str = REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION


def validate_repo_audit_source_inventory_design(
    request: Mapping[str, Any] | None,
    *,
    implementation_readiness_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    policy_decision: Any | None = None,
) -> SourceInventoryDecision:
    """Validate caller-supplied source inventory metadata without touching the repo."""
    failures: list[SourceInventoryFailure] = []
    source_inventory_contract = SourceInventoryContract()

    if request is None:
        _add_failure(
            failures,
            "missing_request",
            "request",
            "source inventory design request is required",
        )
        return _decision(
            validation_status="failed_validation",
            inventory_id=None,
            repo_id=None,
            repo_name=None,
            source_inventory_scope=(),
            failures=tuple(failures),
            source_inventory_input=None,
            source_inventory_contract=source_inventory_contract,
            allowed_path_candidates=(),
            denied_paths=(),
            budget_decision=_budget_decision(None),
            future_read_plan=_future_read_plan(None),
            findings=_findings((), ()),
        )

    data = deepcopy(dict(request))
    inventory_id = _text(data.get("inventory_id")) or None
    repo_id = _text(data.get("repo_id")) or None
    repo_name = _text(data.get("repo_name")) or None
    tenant_scope = _text(data.get("tenant_scope")) or None
    project_scope = _text(data.get("project_scope")) or None
    namespace = _text(data.get("namespace")) or None
    source_inventory_scope = _strings(data.get("source_inventory_scope"))
    candidate_paths = _candidate_paths(data.get("candidate_paths"))
    path_policy = _path_policy(data.get("path_policy"))
    budget = _budget(data.get("budget"))
    future_plan = _future_read_plan(data.get("future_read_plan"))
    limitations = _strings(data.get("limitations"))
    unknowns = _strings(data.get("unknowns"))

    inventory_input = RepoAuditSourceInventoryInput(
        inventory_id=inventory_id,
        repo_id=repo_id,
        repo_name=repo_name,
        repo_root_ref=_text(data.get("repo_root_ref")) or None,
        commit_ref=_text(data.get("commit_ref")) or None,
        branch_ref=_text(data.get("branch_ref")) or None,
        tenant_scope=tenant_scope,
        project_scope=project_scope,
        namespace=namespace,
        source_refs=_source_refs(data.get("source_refs")),
        source_inventory_scope=source_inventory_scope,
        candidate_paths=candidate_paths,
        path_policy=path_policy,
        budget=budget,
        output_categories=_strings(data.get("output_categories")),
        privacy_class=_text(data.get("privacy_class")) or None,
        data_sensitivity=_text(data.get("data_sensitivity")) or None,
        limitations=limitations,
        unknowns=unknowns,
    )

    if not inventory_id:
        _add_failure(
            failures,
            "inventory_identity_required",
            "inventory_id",
            "source inventory design requires a stable inventory id",
        )
    if not repo_id or not repo_name:
        _add_failure(
            failures,
            "repo_identity_required",
            "repo_id",
            "source inventory design requires caller-supplied repo identity",
        )
    if not tenant_scope:
        _add_failure(
            failures,
            "tenant_scope_required",
            "tenant_scope",
            "source inventory design requires tenant scope",
        )
    if not namespace:
        _add_failure(
            failures,
            "namespace_required",
            "namespace",
            "source inventory design requires namespace",
        )
    if not source_inventory_scope:
        _add_failure(
            failures,
            "source_inventory_scope_required",
            "source_inventory_scope",
            "source inventory design requires explicit scope",
        )
    if not candidate_paths and not future_plan.future_read_plan_candidate:
        _add_failure(
            failures,
            "candidate_paths_or_future_read_plan_required",
            "candidate_paths",
            "source inventory design requires candidate path metadata or an explicit future read plan",
        )

    _validate_scopes(source_inventory_scope, failures)
    _validate_policy(path_policy, failures)
    _validate_budget(budget, failures)
    _validate_high_risk_metadata(inventory_input, failures)
    _validate_forbidden_request_fields(data, failures)

    allowed_paths, denied_paths = _validate_candidate_paths(candidate_paths, path_policy)
    for denied in denied_paths:
        _add_failure(
            failures,
            denied.reason,
            "candidate_paths",
            f"candidate path {denied.path!r} is outside the source inventory design boundary",
        )

    budget_decision = _budget_decision(budget)
    _validate_related_decision(
        "implementation_readiness",
        implementation_readiness_decision,
        failures,
    )
    _validate_related_decision("repo_audit", repo_audit_decision, failures)
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
    _validate_related_decision("mission_control", mission_control_decision, failures)
    _validate_related_decision("tool_simulation", tool_simulation_decision, failures)
    _validate_related_decision("plugin_review", plugin_review_decision, failures)
    _validate_related_decision("context_compiler", context_compiler_decision, failures)
    _validate_related_decision("policy", policy_decision, failures)

    return _decision(
        validation_status=_validation_status(failures, budget_decision),
        inventory_id=inventory_id,
        repo_id=repo_id,
        repo_name=repo_name,
        source_inventory_scope=source_inventory_scope,
        failures=tuple(failures),
        source_inventory_input=inventory_input,
        source_inventory_contract=source_inventory_contract,
        allowed_path_candidates=tuple(allowed_paths) if not denied_paths else (),
        denied_paths=tuple(denied_paths),
        budget_decision=budget_decision,
        future_read_plan=future_plan,
        findings=_findings(limitations, unknowns),
    )


def _validate_scopes(
    source_inventory_scope: tuple[str, ...],
    failures: list[SourceInventoryFailure],
) -> None:
    for scope in source_inventory_scope:
        if scope in FORBIDDEN_SOURCE_INVENTORY_SCOPES:
            _add_failure(
                failures,
                "forbidden_source_inventory_scope_denied",
                "source_inventory_scope",
                f"{scope} is not permitted by the source inventory design contract",
            )
        elif scope not in ALLOWED_SOURCE_INVENTORY_SCOPES:
            _add_failure(
                failures,
                "unknown_source_inventory_scope",
                "source_inventory_scope",
                f"{scope} is not a known source inventory design scope",
            )


def _validate_policy(
    path_policy: SourceInventoryPathPolicy,
    failures: list[SourceInventoryFailure],
) -> None:
    _validate_policy_value(
        path_policy.generated_artifact_policy,
        ALLOWED_GENERATED_ARTIFACT_POLICIES,
        "generated_artifact_policy",
        failures,
    )
    _validate_policy_value(
        path_policy.secret_privacy_policy,
        ALLOWED_SECRET_PRIVACY_POLICIES,
        "secret_privacy_policy",
        failures,
    )
    _validate_policy_value(
        path_policy.hidden_path_policy,
        ALLOWED_HIDDEN_PATH_POLICIES,
        "hidden_path_policy",
        failures,
    )
    _validate_policy_value(
        path_policy.symlink_policy,
        ALLOWED_SYMLINK_POLICIES,
        "symlink_policy",
        failures,
    )
    _validate_policy_value(
        path_policy.external_path_policy,
        ALLOWED_BLOCKING_POLICIES,
        "external_path_policy",
        failures,
    )
    _validate_policy_value(
        path_policy.path_traversal_policy,
        ALLOWED_BLOCKING_POLICIES,
        "path_traversal_policy",
        failures,
    )


def _validate_policy_value(
    value: str | None,
    allowed_values: set[str],
    field: str,
    failures: list[SourceInventoryFailure],
) -> None:
    if value is None:
        return
    if value not in allowed_values:
        _add_failure(
            failures,
            f"{field}_unknown",
            f"path_policy.{field}",
            f"{field} is not recognized by the source inventory design contract",
        )


def _validate_budget(
    budget: SourceInventoryBudget,
    failures: list[SourceInventoryFailure],
) -> None:
    if not budget.budget_policy:
        _add_failure(
            failures,
            "budget_policy_required",
            "budget.budget_policy",
            "source inventory design requires a budget policy",
        )
    if budget.max_file_count is None:
        _add_failure(
            failures,
            "budget_file_count_required",
            "budget.max_file_count",
            "source inventory design requires a maximum file count",
        )
    if budget.max_file_size_bytes is None:
        _add_failure(
            failures,
            "budget_file_size_required",
            "budget.max_file_size_bytes",
            "source inventory design requires a maximum file size",
        )
    if budget.max_total_bytes is None:
        _add_failure(
            failures,
            "budget_total_bytes_required",
            "budget.max_total_bytes",
            "source inventory design requires a maximum total byte budget",
        )
    if budget.max_file_count is not None and budget.max_file_count > MAX_REVIEW_FILE_COUNT:
        _add_failure(
            failures,
            "budget_file_count_exceeds_review_limit",
            "budget.max_file_count",
            "source inventory design file count exceeds the review limit",
        )
    if (
        budget.max_file_size_bytes is not None
        and budget.max_file_size_bytes > MAX_REVIEW_FILE_SIZE_BYTES
    ):
        _add_failure(
            failures,
            "budget_file_size_exceeds_review_limit",
            "budget.max_file_size_bytes",
            "source inventory design file size exceeds the review limit",
        )
    if budget.max_total_bytes is not None and budget.max_total_bytes > MAX_REVIEW_TOTAL_BYTES:
        _add_failure(
            failures,
            "budget_total_bytes_exceeds_review_limit",
            "budget.max_total_bytes",
            "source inventory design total byte budget exceeds the review limit",
        )


def _validate_high_risk_metadata(
    inventory_input: RepoAuditSourceInventoryInput,
    failures: list[SourceInventoryFailure],
) -> None:
    scopes = set(inventory_input.source_inventory_scope)
    if not (scopes & HIGH_RISK_SOURCE_INVENTORY_SCOPES):
        return
    if not inventory_input.privacy_class:
        _add_failure(
            failures,
            "high_risk_inventory_requires_privacy_class",
            "privacy_class",
            "high risk source inventory scopes require privacy classification",
        )
    if not inventory_input.data_sensitivity:
        _add_failure(
            failures,
            "high_risk_inventory_requires_data_sensitivity",
            "data_sensitivity",
            "high risk source inventory scopes require data sensitivity classification",
        )


def _validate_forbidden_request_fields(
    request: Mapping[str, Any],
    failures: list[SourceInventoryFailure],
) -> None:
    for field, reason in FORBIDDEN_EXECUTION_FIELDS.items():
        if request.get(field) is True:
            _add_failure(
                failures,
                reason,
                field,
                f"{field} is not allowed in source inventory design",
            )
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field) is True:
            _add_failure(
                failures,
                reason,
                field,
                f"{field} is not allowed in source inventory design",
            )
    for field, reason in FORBIDDEN_PROOF_FIELDS.items():
        if request.get(field) is True:
            _add_failure(
                failures,
                reason,
                field,
                f"{field} is not allowed in source inventory design",
            )
    execution_permission = _text(request.get("execution_permission"))
    if execution_permission and execution_permission != REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION:
        _add_failure(
            failures,
            "execution_permission_must_be_not_granted",
            "execution_permission",
            "source inventory design cannot request execution permission",
        )


def _validate_candidate_paths(
    candidate_paths: tuple[SourceInventoryCandidatePath, ...],
    path_policy: SourceInventoryPathPolicy,
) -> tuple[list[SourceInventoryAllowedPathCandidate], list[SourceInventoryDeniedPath]]:
    allowed: list[SourceInventoryAllowedPathCandidate] = []
    denied: list[SourceInventoryDeniedPath] = []
    for index, candidate in enumerate(candidate_paths):
        classification = _classify_path(candidate, path_policy)
        if classification.reason:
            denied.append(
                SourceInventoryDeniedPath(
                    path=candidate.path,
                    normalized_path=classification.normalized_path,
                    reason=classification.reason,
                    category=classification.category,
                )
            )
            continue
        allowed.append(
            SourceInventoryAllowedPathCandidate(
                path=candidate.path,
                normalized_path=classification.normalized_path,
                path_type=candidate.path_type,
            )
        )
    return allowed, denied


@dataclass(frozen=True)
class _PathClassification:
    normalized_path: str
    reason: str | None
    category: str


def _classify_path(
    candidate: SourceInventoryCandidatePath,
    path_policy: SourceInventoryPathPolicy,
) -> _PathClassification:
    raw_path = _text(candidate.path).replace("\\", "/")
    if not raw_path:
        return _PathClassification("", "empty_path_denied", "empty")
    if any(ord(character) < 32 for character in raw_path):
        return _PathClassification(raw_path, "path_control_character_denied", "invalid")
    lowered_raw = raw_path.lower()
    if lowered_raw.startswith(("file://", "http://", "https://", "s3://", "gs://")):
        return _PathClassification(raw_path, "external_path_denied", "external")
    if _is_drive_root(raw_path):
        return _PathClassification(raw_path, "drive_root_path_denied", "absolute")
    if raw_path.startswith("//"):
        return _PathClassification(raw_path, "unc_path_denied", "absolute")
    if raw_path.startswith("/") or _is_windows_absolute_path(raw_path):
        return _PathClassification(raw_path, "absolute_path_denied", "absolute")
    if raw_path.startswith("~"):
        return _PathClassification(raw_path, "home_relative_path_denied", "home")

    normalized = _collapse_slashes(raw_path)
    lowered = normalized.lower()
    if _has_path_traversal(normalized):
        return _PathClassification(normalized, "path_traversal_denied", "traversal")
    if _is_secret_path(lowered):
        return _PathClassification(normalized, "secret_path_denied", "secret")
    if _starts_with_any(lowered, RUNTIME_OR_LOG_PREFIXES):
        return _PathClassification(normalized, "runtime_or_log_path_denied", "runtime_log")
    if _starts_with_any(lowered, GENERATED_OR_CACHE_PREFIXES):
        return _PathClassification(
            normalized,
            "generated_or_cache_path_denied",
            "generated_or_cache",
        )
    if lowered.startswith("data/"):
        return _PathClassification(normalized, "data_path_denied", "data")
    if _starts_with_any(lowered, MODEL_VECTOR_DATASET_PREFIXES) or _ends_with_any(
        lowered,
        MODEL_VECTOR_DATASET_SUFFIXES,
    ):
        return _PathClassification(
            normalized,
            "model_vector_dataset_path_denied",
            "model_vector_dataset",
        )
    if _starts_with_any(lowered, SCREENSHOT_BROWSER_OUTPUT_PREFIXES) or _ends_with_any(
        lowered,
        SCREENSHOT_BROWSER_OUTPUT_SUFFIXES,
    ):
        return _PathClassification(
            normalized,
            "screenshot_browser_output_path_denied",
            "screenshot_browser_output",
        )
    if candidate.is_generated or candidate.is_binary:
        return _PathClassification(
            normalized,
            "generated_or_cache_path_denied",
            "generated_or_cache",
        )
    if _is_hidden_path(normalized) or candidate.is_hidden:
        if not _future_gate_allows(path_policy.hidden_path_policy, candidate.future_gate_ref):
            return _PathClassification(normalized, "hidden_path_denied", "hidden")
    if candidate.is_symlink:
        if not _future_gate_allows(path_policy.symlink_policy, candidate.future_gate_ref):
            return _PathClassification(normalized, "symlink_candidate_denied", "symlink")
    if path_policy.allowed_prefixes and not _path_prefix_allowed(normalized, path_policy):
        return _PathClassification(normalized, "path_prefix_not_allowed", "policy")
    return _PathClassification(normalized, None, "allowed_candidate")


def _path_prefix_allowed(path: str, path_policy: SourceInventoryPathPolicy) -> bool:
    if path_policy.allow_repo_root_files and "/" not in path:
        return True
    return any(path.startswith(prefix) for prefix in path_policy.allowed_prefixes)


def _future_gate_allows(policy: str | None, future_gate_ref: str | None) -> bool:
    return policy in {"explicit_future_gate_required", "metadata_only_future"} and bool(
        _text(future_gate_ref)
    )


def _validate_related_decision(
    prefix: str,
    decision: Any | None,
    failures: list[SourceInventoryFailure],
) -> None:
    if decision is None:
        return
    if _bool_field(decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            f"{prefix}_runtime_dispatch_attempt_denied",
            f"{prefix}_decision.runtime_dispatch_allowed",
            f"{prefix} decision cannot grant source inventory dispatch",
        )
    permission_fields = (
        "approval_grant",
        "capability_grant",
        "lease_grant",
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
            f"{prefix} decision cannot grant source inventory permissions",
        )
    evidence_fields = (
        "evidence_provided_by_pack_output",
        "evidence_provided_by_readiness",
        "evidence_provided_by_inventory",
        "evidence_provided",
        "proof_repo_state",
        "proof_file_exists",
    )
    if any(_bool_field(decision, field_name) for field_name in evidence_fields):
        _add_failure(
            failures,
            f"{prefix}_evidence_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot create source inventory evidence",
        )
    if _bool_field(decision, "verifier_success") or _bool_field(
        decision,
        "verified_success",
    ):
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
            f"{prefix} decision cannot create source inventory success",
        )
    if _tuple_field(decision, "failure_reasons"):
        _add_failure(
            failures,
            f"{prefix}_decision_has_failures",
            f"{prefix}_decision.failure_reasons",
            f"{prefix} decision failures require source inventory revalidation",
        )


def _decision(
    *,
    validation_status: str,
    inventory_id: str | None,
    repo_id: str | None,
    repo_name: str | None,
    source_inventory_scope: tuple[str, ...],
    failures: tuple[SourceInventoryFailure, ...],
    source_inventory_input: RepoAuditSourceInventoryInput | None,
    source_inventory_contract: SourceInventoryContract,
    allowed_path_candidates: tuple[SourceInventoryAllowedPathCandidate, ...],
    denied_paths: tuple[SourceInventoryDeniedPath, ...],
    budget_decision: SourceInventoryBudgetDecision,
    future_read_plan: SourceInventoryFutureReadPlan,
    findings: tuple[SourceInventoryFinding, ...],
) -> SourceInventoryDecision:
    return SourceInventoryDecision(
        contract_version=REPO_AUDIT_SOURCE_INVENTORY_DESIGN_VERSION,
        validation_status=validation_status,
        inventory_id=inventory_id,
        repo_id=repo_id,
        repo_name=repo_name,
        source_inventory_scope=source_inventory_scope,
        failure_reasons=tuple(dict.fromkeys(failure.reason for failure in failures)),
        failures=failures,
        source_inventory_input=source_inventory_input,
        source_inventory_contract=source_inventory_contract,
        allowed_path_candidates=allowed_path_candidates,
        denied_paths=denied_paths,
        budget_decision=budget_decision,
        future_read_plan=future_read_plan,
        findings=findings,
    )


def _validation_status(
    failures: list[SourceInventoryFailure],
    budget_decision: SourceInventoryBudgetDecision,
) -> str:
    reasons = {failure.reason for failure in failures}
    failed_validation_reasons = {
        "missing_request",
        "inventory_identity_required",
        "repo_identity_required",
        "tenant_scope_required",
        "namespace_required",
        "source_inventory_scope_required",
        "candidate_paths_or_future_read_plan_required",
        "budget_policy_required",
        "budget_file_count_required",
        "budget_file_size_required",
        "budget_total_bytes_required",
        "high_risk_inventory_requires_privacy_class",
        "high_risk_inventory_requires_data_sensitivity",
    }
    review_budget_reasons = {
        "budget_file_count_exceeds_review_limit",
        "budget_file_size_exceeds_review_limit",
        "budget_total_bytes_exceeds_review_limit",
    }
    if reasons & failed_validation_reasons:
        return "failed_validation"
    if reasons - review_budget_reasons:
        return "blocked"
    if budget_decision.requires_human_review:
        return "requires_human_review"
    return "design_ready"


def _source_refs(value: Any) -> tuple[SourceInventorySourceRef, ...]:
    refs: list[SourceInventorySourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                SourceInventorySourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            ref_id = _text(item)
            if ref_id:
                refs.append(SourceInventorySourceRef(ref_id=ref_id, ref_type="unspecified"))
    return tuple(refs)


def _candidate_paths(value: Any) -> tuple[SourceInventoryCandidatePath, ...]:
    candidates: list[SourceInventoryCandidatePath] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            candidates.append(
                SourceInventoryCandidatePath(
                    path=_text(item.get("path")) or _text(item.get("path_ref")),
                    path_type=_text(item.get("path_type")) or None,
                    size_bytes=_int_or_none(item.get("size_bytes")),
                    is_binary=item.get("is_binary") is True,
                    is_generated=item.get("is_generated") is True,
                    is_hidden=item.get("is_hidden") is True,
                    is_symlink=item.get("is_symlink") is True,
                    future_gate_ref=_text(item.get("future_gate_ref")) or None,
                )
            )
        else:
            candidates.append(SourceInventoryCandidatePath(path=_text(item)))
    return tuple(candidates)


def _path_policy(value: Any) -> SourceInventoryPathPolicy:
    policy = value if isinstance(value, Mapping) else {}
    allowed_prefixes = tuple(
        _normalize_prefix(prefix)
        for prefix in _strings(policy.get("allowed_prefixes"))
        if _normalize_prefix(prefix)
    )
    return SourceInventoryPathPolicy(
        allowed_prefixes=allowed_prefixes,
        allow_repo_root_files=policy.get("allow_repo_root_files") is True,
        forbidden_paths=_strings(policy.get("forbidden_paths")),
        forbidden_extensions=_strings(policy.get("forbidden_extensions")),
        generated_artifact_policy=_text(policy.get("generated_artifact_policy")) or None,
        secret_privacy_policy=_text(policy.get("secret_privacy_policy")) or None,
        hidden_path_policy=_text(policy.get("hidden_path_policy")) or None,
        symlink_policy=_text(policy.get("symlink_policy")) or None,
        external_path_policy=_text(policy.get("external_path_policy")) or None,
        path_traversal_policy=_text(policy.get("path_traversal_policy")) or None,
        runtime_log_policy=_text(policy.get("runtime_log_policy")) or None,
        model_vector_policy=_text(policy.get("model_vector_policy")) or None,
        browser_output_policy=_text(policy.get("browser_output_policy")) or None,
        dependency_build_policy=_text(policy.get("dependency_build_policy")) or None,
    )


def _budget(value: Any) -> SourceInventoryBudget:
    budget = value if isinstance(value, Mapping) else {}
    return SourceInventoryBudget(
        max_file_count=_int_or_none(budget.get("max_file_count")),
        max_file_size_bytes=_int_or_none(budget.get("max_file_size_bytes")),
        max_total_bytes=_int_or_none(budget.get("max_total_bytes")),
        budget_policy=_text(budget.get("budget_policy")) or None,
    )


def _budget_decision(budget: SourceInventoryBudget | None) -> SourceInventoryBudgetDecision:
    if budget is None:
        return SourceInventoryBudgetDecision(
            max_file_count=None,
            max_file_size_bytes=None,
            max_total_bytes=None,
            budget_policy=None,
            within_design_limits=False,
            requires_human_review=True,
        )
    requires_human_review = any(
        value is not None and value > limit
        for value, limit in (
            (budget.max_file_count, MAX_REVIEW_FILE_COUNT),
            (budget.max_file_size_bytes, MAX_REVIEW_FILE_SIZE_BYTES),
            (budget.max_total_bytes, MAX_REVIEW_TOTAL_BYTES),
        )
    )
    complete = (
        budget.max_file_count is not None
        and budget.max_file_size_bytes is not None
        and budget.max_total_bytes is not None
        and bool(budget.budget_policy)
    )
    return SourceInventoryBudgetDecision(
        max_file_count=budget.max_file_count,
        max_file_size_bytes=budget.max_file_size_bytes,
        max_total_bytes=budget.max_total_bytes,
        budget_policy=budget.budget_policy,
        within_design_limits=complete and not requires_human_review,
        requires_human_review=requires_human_review,
    )


def _future_read_plan(value: Any) -> SourceInventoryFutureReadPlan:
    plan = value if isinstance(value, Mapping) else {}
    return SourceInventoryFutureReadPlan(
        future_read_plan_candidate=bool(plan),
        plan_id=_text(plan.get("plan_id")) or None,
        requires_boundary_approval=plan.get("requires_boundary_approval") is not False,
        requires_evidence_boundary=True,
        requires_verifier_boundary=True,
        can_read_now=False,
    )


def _findings(
    limitations: tuple[str, ...],
    unknowns: tuple[str, ...],
) -> tuple[SourceInventoryFinding, ...]:
    summaries = tuple(limitations) + tuple(unknowns)
    if not summaries:
        summaries = ("metadata-only design; no source inventory evidence produced",)
    return tuple(
        SourceInventoryFinding(
            finding_type="source_inventory_limitation",
            summary=summary,
        )
        for summary in summaries
    )


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


def _normalize_prefix(value: str) -> str:
    text = _text(value).replace("\\", "/")
    if not text:
        return ""
    return text if text.endswith("/") else f"{text}/"


def _tuple_field(value: Any, field_name: str) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        raw = value.get(field_name)
    else:
        raw = getattr(value, field_name, None)
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)


def _bool_field(value: Any, field_name: str) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return value.get(field_name) is True
    return getattr(value, field_name, None) is True


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
    failures: list[SourceInventoryFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(SourceInventoryFailure(reason=reason, field=field, message=message))
