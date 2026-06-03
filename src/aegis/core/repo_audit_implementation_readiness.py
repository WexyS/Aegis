from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_IMPLEMENTATION_READINESS_VERSION = "repo-audit-implementation-readiness/1"
REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION = (
    "not_granted_by_repo_audit_implementation_readiness"
)

ALLOWED_AUDIT_SCOPES = {
    "source_inventory_readiness",
    "architecture_review_readiness",
    "test_reference_readiness",
    "dependency_metadata_readiness",
    "security_smell_readiness",
    "documentation_alignment_readiness",
    "policy_alignment_readiness",
    "evidence_reference_readiness",
    "developer_passport_candidate_readiness",
    "compliance_candidate_readiness",
    "generated_artifact_exclusion_readiness",
    "secret_exclusion_readiness",
    "repo_health_candidate_readiness",
}

FORBIDDEN_AUDIT_SCOPES = {
    "actual_repo_scan",
    "file_content_read",
    "git_command_execution",
    "test_execution",
    "dependency_install",
    "model_assisted_audit",
    "external_api_audit",
    "plugin_execution",
    "memory_write",
    "report_export",
    "signed_report",
    "proof_tests_passed",
    "proof_code_safe",
    "proof_secure",
    "proof_compliant",
    "legal_certification",
    "security_certification",
    "compliance_certification",
    "official_audit_result",
    "court_admissible_evidence",
    "worker_surveillance",
    "productivity_score",
}

ALLOWED_OUTPUT_CATEGORIES = {
    "architecture_note_candidate",
    "test_reference_candidate",
    "dependency_note_candidate",
    "security_smell_candidate",
    "documentation_alignment_candidate",
    "policy_alignment_candidate",
    "evidence_reference_candidate",
    "limitation_note",
    "unknown_note",
    "remediation_candidate",
    "developer_passport_candidate_ref",
    "compliance_candidate_ref",
}

ALLOWED_FILE_ACCESS_POLICIES = {
    "caller_supplied_refs_only",
    "future_read_only_file_refs_only",
    "blocked",
}
ALLOWED_GENERATED_ARTIFACT_POLICIES = {
    "exclude_generated_artifacts",
    "deny_by_default",
    "blocked",
}
ALLOWED_SECRET_PRIVACY_POLICIES = {
    "deny_by_default",
    "explicit_allowlist_required",
    "caller_supplied_only_untrusted",
    "blocked",
}
ALLOWED_HIDDEN_PATH_POLICIES = {"deny_hidden_and_system_paths", "blocked"}
ALLOWED_SYMLINK_POLICIES = {"deny_symlink_targets", "blocked"}
ALLOWED_GIT_METADATA_MODES = {
    "none",
    "caller_supplied_refs_only",
    "read_only_git_metadata_future",
    "blocked",
}
ALLOWED_TEST_METADATA_MODES = {
    "none",
    "caller_supplied_test_refs_only",
    "future_read_only_test_result_refs",
    "blocked",
}

HIGH_RISK_AUDIT_SCOPES = {
    "security_smell_readiness",
    "secret_exclusion_readiness",
    "compliance_candidate_readiness",
    "generated_artifact_exclusion_readiness",
}

REQUIRED_EXCLUSION_PATTERNS = {
    "logs/**",
    ".git/**",
    "node_modules/**",
    "build/**",
    "**/*.env",
    "**/*.key",
    "**/*.pem",
    "**/*secret*",
    "**/*token*",
}

FORBIDDEN_PATH_PREFIXES = {
    ".git/",
    ".hg/",
    ".svn/",
    ".venv/",
    "venv/",
    "node_modules/",
    "logs/",
    "runtime/",
    "journals/",
    "journal/",
    "data/runtime/",
    "model/",
    "models/",
    "vector_db/",
    "vectordb/",
    "dist/",
    "build/",
    ".next/",
    "__pycache__/",
}

SECRET_PATH_MARKERS = {
    ".env",
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "credential",
    "private_key",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_readiness": "readiness_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "readiness_cannot_provide_evidence",
    "verifier_success": "readiness_cannot_mark_verifier_success",
    "verified_success": "readiness_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "certification_claim": "certification_claim_denied",
}

FORBIDDEN_EXECUTION_FIELDS = {
    "repo_scan_performed": "repo_scan_request_denied",
    "actual_repo_scan": "repo_scan_request_denied",
    "repo_scanning": "repo_scan_request_denied",
    "file_read_performed": "file_read_request_denied",
    "read_repo_files": "file_read_request_denied",
    "file_content_read": "file_read_request_denied",
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
}

FORBIDDEN_CLAIMS = {
    "tests passed": "test_success_claim_denied",
    "proof tests passed": "test_success_claim_denied",
    "code is safe": "code_safety_claim_denied",
    "proof code safe": "code_safety_claim_denied",
    "proof secure": "security_proof_claim_denied",
    "proof compliant": "compliance_proof_claim_denied",
    "legal certification": "legal_certification_claim_denied",
    "security certification": "security_certification_claim_denied",
    "compliance certification": "compliance_certification_claim_denied",
    "official audit result": "official_audit_result_claim_denied",
    "court-admissible": "court_admissible_claim_denied",
    "court admissible": "court_admissible_claim_denied",
    "worker surveillance": "surveillance_claim_denied",
    "productivity score": "productivity_score_denied",
}


@dataclass(frozen=True)
class RepoAuditImplementationSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class RepoAuditImplementationReadinessInput:
    readiness_id: str | None
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    commit_ref: str | None
    branch_ref: str | None
    tenant_scope: str | None
    project_scope: str | None
    namespace: str | None
    source_refs: tuple[RepoAuditImplementationSourceRef, ...]
    allowed_source_scopes: tuple[str, ...]
    requested_audit_scopes: tuple[str, ...]
    file_access_policy: str | None
    allowed_path_prefixes: tuple[str, ...]
    candidate_file_refs: tuple[str, ...]
    excluded_path_patterns: tuple[str, ...]
    generated_artifact_policy: str | None
    secret_privacy_policy: str | None
    hidden_path_policy: str | None
    symlink_policy: str | None
    git_metadata_mode: str | None
    test_metadata_mode: str | None
    test_refs: tuple[str, ...]
    dependency_refs: tuple[str, ...]
    output_categories: tuple[str, ...]
    report_contract: str | None
    privacy_class: str | None
    data_sensitivity: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RepoAuditImplementationOutputCandidate:
    candidate_id: str
    category: str
    summary: str
    source_refs: tuple[str, ...]
    confidence: str | None = None
    uncertainty: str | None = None
    blocked_by_missing_source: bool = False
    verified: bool = False


@dataclass(frozen=True)
class RepoAuditImplementationOutputContract:
    output_categories: tuple[str, ...]
    candidates: tuple[RepoAuditImplementationOutputCandidate, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    policy_refs: tuple[str, ...]
    report_contract: str | None
    runtime_dispatch_allowed: bool = False
    authority: bool = False
    evidence_provided_by_output: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


@dataclass(frozen=True)
class RepoAuditImplementationReadinessContract:
    readiness_id: str | None
    repo_id: str | None
    repo_name: str | None
    requested_audit_scopes: tuple[str, ...]
    file_access_policy: str | None
    git_metadata_mode: str | None
    test_metadata_mode: str | None
    secret_privacy_policy: str | None
    generated_artifact_policy: str | None
    output_categories: tuple[str, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_readiness: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
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
    certification_claim: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True
    requires_secret_exclusion: bool = True
    requires_generated_artifact_exclusion: bool = True


@dataclass(frozen=True)
class RepoAuditImplementationReadinessFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditImplementationReadinessDecision:
    contract_version: str
    validation_status: str
    readiness_id: str | None
    repo_id: str | None
    repo_name: str | None
    requested_audit_scopes: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditImplementationReadinessFailure, ...]
    readiness_input: RepoAuditImplementationReadinessInput | None = None
    readiness_contract: RepoAuditImplementationReadinessContract | None = None
    output_contract: RepoAuditImplementationOutputContract | None = None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_readiness: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review: bool = True


def validate_repo_audit_implementation_readiness(
    request: Mapping[str, Any] | None,
    *,
    repo_audit_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
    vertical_pack_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    policy_decision: Any | None = None,
) -> RepoAuditImplementationReadinessDecision:
    """Validate Repo Audit implementation-readiness metadata only.

    This helper is pure. It does not scan repositories, read files, run git,
    execute tests, spawn subprocesses, call tools, call MCP, call APIs, call
    models, access memory, generate reports, export artifacts, create evidence,
    set verifier success, grant approval/leases/capabilities, dispatch runtime
    work, or mutate frontend/runtime state.
    """

    failures: list[RepoAuditImplementationReadinessFailure] = []
    if not isinstance(request, Mapping):
        failure = RepoAuditImplementationReadinessFailure(
            reason="missing_request",
            field="request",
            message="repo audit implementation-readiness request must be a mapping",
        )
        return _decision(
            validation_status="failed_validation",
            readiness_id=None,
            repo_id=None,
            repo_name=None,
            requested_audit_scopes=(),
            failures=(failure,),
        )

    request_copy = deepcopy(dict(request))
    readiness_input = _readiness_input(request_copy)

    _validate_identity(readiness_input, failures)
    _validate_scope(readiness_input, failures)
    _validate_source_refs(readiness_input, failures)
    _validate_access_policies(readiness_input, failures)
    _validate_paths(readiness_input, request_copy, failures)
    _validate_high_risk_context(readiness_input, failures)
    _validate_output_categories(readiness_input, failures)
    candidates = _validate_output_candidates(request_copy.get("output_candidates"), failures)
    _validate_non_authority_fields(request_copy, failures)
    _validate_execution_surfaces(request_copy, failures)
    _validate_claims(request_copy, failures)
    _validate_related_decision(
        "repo_audit",
        repo_audit_decision,
        failures,
        evidence_fields=("evidence_provided_by_report", "evidence_provided_by_pack_output"),
    )
    _validate_related_decision(
        "developer_work_passport",
        developer_work_passport_decision,
        failures,
        evidence_fields=("evidence_provided_by_passport",),
    )
    _validate_related_decision(
        "compliance_evidence",
        compliance_evidence_decision,
        failures,
        evidence_fields=("evidence_provided_by_package",),
    )
    _validate_related_decision(
        "mission_control",
        mission_control_decision,
        failures,
        evidence_fields=("evidence_provided_by_preview",),
    )
    _validate_related_decision(
        "tool_simulation",
        tool_simulation_decision,
        failures,
        evidence_fields=("evidence_provided_by_simulation", "evidence_created"),
    )
    _validate_related_decision(
        "plugin_review",
        plugin_review_decision,
        failures,
        evidence_fields=("evidence_provided_by_review",),
    )
    _validate_related_decision(
        "vertical_pack",
        vertical_pack_decision,
        failures,
        evidence_fields=("evidence_provided_by_pack_output", "pack_output_is_evidence"),
    )
    _validate_related_decision(
        "context_compiler",
        context_compiler_decision,
        failures,
        evidence_fields=("evidence_provided_by_context", "context_output_is_evidence"),
    )
    _validate_related_decision(
        "policy",
        policy_decision,
        failures,
        evidence_fields=("evidence_provided_by_policy",),
    )
    _validate_vertical_pack_relationship(vertical_pack_decision, failures)

    readiness_contract = RepoAuditImplementationReadinessContract(
        readiness_id=readiness_input.readiness_id,
        repo_id=readiness_input.repo_id,
        repo_name=readiness_input.repo_name,
        requested_audit_scopes=readiness_input.requested_audit_scopes,
        file_access_policy=readiness_input.file_access_policy,
        git_metadata_mode=readiness_input.git_metadata_mode,
        test_metadata_mode=readiness_input.test_metadata_mode,
        secret_privacy_policy=readiness_input.secret_privacy_policy,
        generated_artifact_policy=readiness_input.generated_artifact_policy,
        output_categories=readiness_input.output_categories,
    )
    output_contract = RepoAuditImplementationOutputContract(
        output_categories=readiness_input.output_categories,
        candidates=tuple(candidates),
        limitations=readiness_input.limitations,
        unknowns=readiness_input.unknowns,
        evidence_refs=_strings(request_copy.get("evidence_refs")),
        policy_refs=_strings(request_copy.get("policy_refs")),
        report_contract=readiness_input.report_contract,
    )
    validation_status = _validation_status(failures)

    return _decision(
        validation_status=validation_status,
        readiness_id=readiness_input.readiness_id,
        repo_id=readiness_input.repo_id,
        repo_name=readiness_input.repo_name,
        requested_audit_scopes=readiness_input.requested_audit_scopes,
        failures=tuple(failures),
        readiness_input=readiness_input,
        readiness_contract=readiness_contract,
        output_contract=output_contract,
    )


def _readiness_input(request: Mapping[str, Any]) -> RepoAuditImplementationReadinessInput:
    candidate_refs = _strings(request.get("candidate_file_refs"))
    file_refs = _strings(request.get("file_refs"))
    docs_refs = _strings(request.get("docs_refs"))
    config_refs = _strings(request.get("config_refs"))
    return RepoAuditImplementationReadinessInput(
        readiness_id=_text(request.get("readiness_id")) or None,
        repo_id=_text(request.get("repo_id")) or None,
        repo_name=_text(request.get("repo_name")) or None,
        repo_root_ref=_text(request.get("repo_root_ref")) or None,
        commit_ref=_text(request.get("commit_ref")) or None,
        branch_ref=_text(request.get("branch_ref")) or None,
        tenant_scope=_text(request.get("tenant_scope")) or None,
        project_scope=_text(request.get("project_scope")) or None,
        namespace=_text(request.get("namespace")) or None,
        source_refs=_source_refs(request.get("source_refs")),
        allowed_source_scopes=_strings(request.get("allowed_source_scopes")),
        requested_audit_scopes=_strings(
            request.get("requested_audit_scopes") or request.get("audit_scope")
        ),
        file_access_policy=_text(request.get("file_access_policy")) or None,
        allowed_path_prefixes=_strings(request.get("allowed_path_prefixes")),
        candidate_file_refs=_dedupe(candidate_refs + file_refs + docs_refs + config_refs),
        excluded_path_patterns=_strings(request.get("excluded_path_patterns")),
        generated_artifact_policy=_text(request.get("generated_artifact_policy")) or None,
        secret_privacy_policy=_text(request.get("secret_privacy_policy")) or None,
        hidden_path_policy=_text(request.get("hidden_path_policy")) or None,
        symlink_policy=_text(request.get("symlink_policy")) or None,
        git_metadata_mode=_text(request.get("git_metadata_mode")) or None,
        test_metadata_mode=_text(request.get("test_metadata_mode")) or None,
        test_refs=_strings(request.get("test_refs")),
        dependency_refs=_strings(request.get("dependency_refs")),
        output_categories=_strings(request.get("output_categories")),
        report_contract=_text(request.get("report_contract")) or None,
        privacy_class=_text(request.get("privacy_class")) or None,
        data_sensitivity=_text(request.get("data_sensitivity")) or None,
        limitations=_strings(request.get("limitations")),
        unknowns=_strings(request.get("unknowns")),
    )


def _validate_identity(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if not readiness_input.readiness_id and not (
        readiness_input.repo_id or readiness_input.repo_name or readiness_input.repo_root_ref
    ):
        _add_failure(
            failures,
            "repo_identity_required",
            "repo_id",
            "readiness_id or repo identity is required",
        )
    if not readiness_input.tenant_scope:
        _add_failure(
            failures,
            "tenant_scope_required",
            "tenant_scope",
            "tenant scope is required for implementation readiness",
        )
    if not readiness_input.project_scope:
        _add_failure(
            failures,
            "project_scope_required",
            "project_scope",
            "project scope is required for implementation readiness",
        )
    if not readiness_input.namespace:
        _add_failure(
            failures,
            "namespace_required",
            "namespace",
            "namespace is required for implementation readiness",
        )


def _validate_scope(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if not readiness_input.requested_audit_scopes:
        _add_failure(
            failures,
            "audit_scope_required",
            "requested_audit_scopes",
            "at least one implementation-readiness scope is required",
        )
    for field_name, scopes in (
        ("requested_audit_scopes", readiness_input.requested_audit_scopes),
        ("allowed_source_scopes", readiness_input.allowed_source_scopes),
    ):
        for scope in scopes:
            if scope in FORBIDDEN_AUDIT_SCOPES:
                _add_failure(
                    failures,
                    "forbidden_audit_scope_denied",
                    field_name,
                    f"{scope} is outside repo audit implementation-readiness",
                )
            elif scope not in ALLOWED_AUDIT_SCOPES:
                _add_failure(failures, "unknown_audit_scope", field_name, scope)


def _validate_source_refs(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if not readiness_input.source_refs:
        _add_failure(
            failures,
            "source_refs_required",
            "source_refs",
            "caller-supplied source refs are required",
        )
    for source_ref in readiness_input.source_refs:
        if source_ref.ref_id.lower() in {"*", "all", "any"}:
            _add_failure(
                failures,
                "wildcard_source_ref_denied",
                "source_refs",
                "wildcard source refs are denied",
            )
        if not source_ref.ref_type:
            _add_failure(
                failures,
                "source_ref_type_required",
                "source_refs",
                "source refs require ref_type",
            )


def _validate_access_policies(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    _require_allowed_policy(
        readiness_input.file_access_policy,
        "file_access_policy",
        "file_access_policy_required",
        "unknown_file_access_policy",
        ALLOWED_FILE_ACCESS_POLICIES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.generated_artifact_policy,
        "generated_artifact_policy",
        "generated_artifact_policy_required",
        "unknown_generated_artifact_policy",
        ALLOWED_GENERATED_ARTIFACT_POLICIES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.secret_privacy_policy,
        "secret_privacy_policy",
        "secret_privacy_policy_required",
        "unknown_secret_privacy_policy",
        ALLOWED_SECRET_PRIVACY_POLICIES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.hidden_path_policy,
        "hidden_path_policy",
        "hidden_path_policy_required",
        "unknown_hidden_path_policy",
        ALLOWED_HIDDEN_PATH_POLICIES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.symlink_policy,
        "symlink_policy",
        "symlink_policy_required",
        "unknown_symlink_policy",
        ALLOWED_SYMLINK_POLICIES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.git_metadata_mode,
        "git_metadata_mode",
        "git_metadata_mode_required",
        "unknown_git_metadata_mode",
        ALLOWED_GIT_METADATA_MODES,
        failures,
    )
    _require_allowed_policy(
        readiness_input.test_metadata_mode,
        "test_metadata_mode",
        "test_metadata_mode_required",
        "unknown_test_metadata_mode",
        ALLOWED_TEST_METADATA_MODES,
        failures,
    )
    missing = REQUIRED_EXCLUSION_PATTERNS - set(readiness_input.excluded_path_patterns)
    if missing:
        _add_failure(
            failures,
            "required_exclusion_patterns_missing",
            "excluded_path_patterns",
            "secret, generated-artifact, runtime, dependency, and git exclusions are required",
        )


def _require_allowed_policy(
    value: str | None,
    field: str,
    required_reason: str,
    unknown_reason: str,
    allowed: set[str],
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if not value:
        _add_failure(failures, required_reason, field, f"{field} is required")
    elif value not in allowed:
        _add_failure(failures, unknown_reason, field, value)


def _validate_paths(
    readiness_input: RepoAuditImplementationReadinessInput,
    request: Mapping[str, Any],
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    all_refs = _dedupe(
        readiness_input.candidate_file_refs
        + readiness_input.test_refs
        + readiness_input.dependency_refs
        + _strings(request.get("path_refs"))
    )
    for ref in all_refs:
        normalized = _normalize_path_ref(ref)
        if _is_absolute_path(normalized):
            _add_failure(
                failures,
                "absolute_or_external_path_denied",
                "candidate_file_refs",
                "absolute or external paths are not accepted by readiness metadata",
            )
        if _has_path_traversal(normalized):
            _add_failure(
                failures,
                "path_traversal_denied",
                "candidate_file_refs",
                "path traversal is denied",
            )
        if _is_forbidden_path(normalized):
            _add_failure(
                failures,
                "forbidden_path_ref_denied",
                "candidate_file_refs",
                "runtime, generated, dependency, model, vector, log, and git paths are excluded",
            )
        if _is_secret_path(normalized):
            _add_failure(
                failures,
                "secret_path_ref_denied",
                "candidate_file_refs",
                "secret, token, key, credential, and env paths are excluded",
            )
        if _is_hidden_path(normalized):
            _add_failure(
                failures,
                "hidden_path_ref_denied",
                "candidate_file_refs",
                "hidden and system paths are excluded",
            )
    if _strings(request.get("hidden_path_refs")):
        _add_failure(
            failures,
            "hidden_path_ref_denied",
            "hidden_path_refs",
            "hidden path refs are denied by default",
        )
    if _strings(request.get("symlink_refs")):
        _add_failure(
            failures,
            "symlink_path_ref_denied",
            "symlink_refs",
            "symlink targets are denied by default",
        )


def _validate_high_risk_context(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if set(readiness_input.requested_audit_scopes) & HIGH_RISK_AUDIT_SCOPES:
        if not readiness_input.privacy_class:
            _add_failure(
                failures,
                "privacy_class_required_for_high_risk_audit",
                "privacy_class",
                "privacy class is required for high-risk audit metadata",
            )
        if not readiness_input.data_sensitivity:
            _add_failure(
                failures,
                "data_sensitivity_required_for_high_risk_audit",
                "data_sensitivity",
                "data sensitivity is required for high-risk audit metadata",
            )


def _validate_output_categories(
    readiness_input: RepoAuditImplementationReadinessInput,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if not readiness_input.output_categories:
        _add_failure(
            failures,
            "output_categories_required",
            "output_categories",
            "at least one candidate output category is required",
        )
    for category in readiness_input.output_categories:
        if category not in ALLOWED_OUTPUT_CATEGORIES:
            _add_failure(
                failures,
                "unknown_output_category",
                "output_categories",
                category,
            )


def _validate_output_candidates(
    raw_candidates: Any,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> list[RepoAuditImplementationOutputCandidate]:
    candidates: list[RepoAuditImplementationOutputCandidate] = []
    for index, raw_candidate in enumerate(_items(raw_candidates)):
        if not isinstance(raw_candidate, Mapping):
            _add_failure(
                failures,
                "output_candidate_mapping_required",
                f"output_candidates[{index}]",
                "output candidates must be mappings",
            )
            continue
        category = _text(raw_candidate.get("category")) or "unknown_note"
        source_refs = _strings(raw_candidate.get("source_refs"))
        uncertainty = _text(raw_candidate.get("uncertainty")) or None
        blocked = raw_candidate.get("blocked_by_missing_source") is True
        if category not in ALLOWED_OUTPUT_CATEGORIES:
            _add_failure(
                failures,
                "unknown_output_category",
                f"output_candidates[{index}].category",
                category,
            )
        if not source_refs and not uncertainty and not blocked:
            _add_failure(
                failures,
                "candidate_without_source_requires_uncertainty",
                f"output_candidates[{index}].source_refs",
                "source-less candidates must remain uncertain or blocked",
            )
        if raw_candidate.get("verified") is True:
            _add_failure(
                failures,
                "output_candidate_cannot_be_verified",
                f"output_candidates[{index}].verified",
                "implementation-readiness output cannot verify itself",
            )
        candidates.append(
            RepoAuditImplementationOutputCandidate(
                candidate_id=_text(raw_candidate.get("candidate_id")) or f"candidate-{index + 1}",
                category=category,
                summary=_text(raw_candidate.get("summary")) or "",
                source_refs=source_refs,
                confidence=_text(raw_candidate.get("confidence")) or None,
                uncertainty=uncertainty,
                blocked_by_missing_source=blocked,
                verified=False,
            )
        )
    return candidates


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    for field_name, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority, evidence, verification, or success",
            )
    if request.get("execution_permission") not in (
        None,
        "",
        REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_readiness_required",
            "execution_permission",
            "repo audit implementation readiness cannot grant execution permission",
        )


def _validate_execution_surfaces(
    request: Mapping[str, Any],
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    for field_name, reason in FORBIDDEN_EXECUTION_FIELDS.items():
        value = request.get(field_name)
        if value is True or (field_name in {"git_command", "mcp_tool_call"} and _text(value)):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside implementation-readiness metadata",
            )
    if _strings(request.get("requested_tools")):
        _add_failure(
            failures,
            "tool_call_request_denied",
            "requested_tools",
            "readiness metadata does not request tools",
        )
    if _strings(request.get("requested_mcp_tools")):
        _add_failure(
            failures,
            "mcp_call_request_denied",
            "requested_mcp_tools",
            "readiness metadata does not request MCP tools",
        )
    if _strings(request.get("requested_models")) or _strings(request.get("model_roles")):
        _add_failure(
            failures,
            "model_call_request_denied",
            "requested_models",
            "readiness metadata does not request models",
        )


def _validate_claims(
    request: Mapping[str, Any],
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    for phrase, reason in FORBIDDEN_CLAIMS.items():
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"repo audit implementation readiness cannot claim {phrase}",
            )


def _validate_related_decision(
    prefix: str,
    decision: Any | None,
    failures: list[RepoAuditImplementationReadinessFailure],
    *,
    evidence_fields: tuple[str, ...],
) -> None:
    if decision is None:
        return
    if _bool_field(decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            f"{prefix}_runtime_dispatch_attempt_denied",
            f"{prefix}_decision.runtime_dispatch_allowed",
            f"{prefix} decision cannot grant repo audit implementation readiness dispatch",
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
            f"{prefix} decision cannot grant permission to repo audit implementation readiness",
        )
    if any(_bool_field(decision, field_name) for field_name in evidence_fields):
        _add_failure(
            failures,
            f"{prefix}_evidence_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot create readiness evidence",
        )
    if _bool_field(decision, "verifier_success") or _bool_field(
        decision,
        "pack_output_is_verifier_truth",
    ):
        _add_failure(
            failures,
            f"{prefix}_verifier_success_claim_denied",
            f"{prefix}_decision.verifier_success",
            f"{prefix} decision cannot create verifier success",
        )
    if _tuple_field(decision, "failure_reasons"):
        _add_failure(
            failures,
            f"{prefix}_decision_has_failures",
            f"{prefix}_decision.failure_reasons",
            f"{prefix} decision failures require readiness revalidation",
        )


def _validate_vertical_pack_relationship(
    vertical_pack_decision: Any | None,
    failures: list[RepoAuditImplementationReadinessFailure],
) -> None:
    if vertical_pack_decision is None:
        return
    category = _field(vertical_pack_decision, "pack_category")
    if category and category != "repo_audit":
        _add_failure(
            failures,
            "vertical_pack_category_must_be_repo_audit",
            "vertical_pack_decision.pack_category",
            "repo audit implementation readiness requires repo_audit pack category",
        )
    profile = _field(vertical_pack_decision, "operating_profile")
    if profile and profile not in {"read_only", "proposal_only"}:
        _add_failure(
            failures,
            "vertical_pack_profile_must_be_read_or_proposal_only",
            "vertical_pack_decision.operating_profile",
            "repo audit implementation readiness requires read_only or proposal_only profile",
        )


def _source_refs(value: Any) -> tuple[RepoAuditImplementationSourceRef, ...]:
    refs: list[RepoAuditImplementationSourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                RepoAuditImplementationSourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            ref_id = _text(item)
            if ref_id:
                refs.append(
                    RepoAuditImplementationSourceRef(
                        ref_id=ref_id,
                        ref_type="unspecified",
                    )
                )
    return tuple(refs)


def _decision(
    *,
    validation_status: str,
    readiness_id: str | None,
    repo_id: str | None,
    repo_name: str | None,
    requested_audit_scopes: tuple[str, ...],
    failures: tuple[RepoAuditImplementationReadinessFailure, ...],
    readiness_input: RepoAuditImplementationReadinessInput | None = None,
    readiness_contract: RepoAuditImplementationReadinessContract | None = None,
    output_contract: RepoAuditImplementationOutputContract | None = None,
) -> RepoAuditImplementationReadinessDecision:
    return RepoAuditImplementationReadinessDecision(
        contract_version=REPO_AUDIT_IMPLEMENTATION_READINESS_VERSION,
        validation_status=validation_status,
        readiness_id=readiness_id,
        repo_id=repo_id,
        repo_name=repo_name,
        requested_audit_scopes=requested_audit_scopes,
        failure_reasons=tuple(dict.fromkeys(failure.reason for failure in failures)),
        failures=failures,
        readiness_input=readiness_input,
        readiness_contract=readiness_contract,
        output_contract=output_contract,
    )


def _validation_status(failures: list[RepoAuditImplementationReadinessFailure]) -> str:
    reasons = {failure.reason for failure in failures}
    failed_validation_reasons = {
        "missing_request",
        "repo_identity_required",
        "tenant_scope_required",
        "project_scope_required",
        "namespace_required",
        "audit_scope_required",
        "source_refs_required",
        "output_categories_required",
    }
    if reasons & failed_validation_reasons:
        return "failed_validation"
    if failures:
        return "blocked"
    return "readiness_ready"


def _normalize_path_ref(value: str) -> str:
    return value.strip().replace("\\", "/")


def _is_absolute_path(path: str) -> bool:
    lowered = path.lower()
    if lowered.startswith("file://") or lowered.startswith("//"):
        return True
    if path.startswith("/"):
        return True
    return len(path) >= 3 and path[1] == ":" and path[2] == "/"


def _has_path_traversal(path: str) -> bool:
    return ".." in [part.strip() for part in path.split("/")]


def _is_forbidden_path(path: str) -> bool:
    lowered = path.lower().lstrip("/")
    return any(lowered.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES)


def _is_secret_path(path: str) -> bool:
    lowered = path.lower()
    return any(marker in lowered for marker in SECRET_PATH_MARKERS) or lowered.endswith(
        (".pem", ".key", ".pfx", ".p12")
    )


def _is_hidden_path(path: str) -> bool:
    return any(part.startswith(".") for part in path.split("/") if part)


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


def _field(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get(field_name))
    return _text(getattr(value, field_name, None))


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


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _add_failure(
    failures: list[RepoAuditImplementationReadinessFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(
        RepoAuditImplementationReadinessFailure(
            reason=reason,
            field=field,
            message=message,
        )
    )
