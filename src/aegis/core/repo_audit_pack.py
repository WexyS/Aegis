from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REPO_AUDIT_PACK_CONTRACT_VERSION = "repo-audit-pack-contract/1"
REPO_AUDIT_EXECUTION_PERMISSION = "not_granted_by_repo_audit_pack"

ALLOWED_AUDIT_SCOPES = {
    "architecture_summary",
    "dependency_review",
    "test_inventory",
    "risk_findings",
    "security_static_notes",
    "documentation_review",
    "maintainability_review",
    "migration_readiness",
    "release_readiness_notes",
    "evidence_gap_notes",
    "policy_gap_notes",
    "developer_work_passport_candidate",
    "compliance_evidence_candidate",
}

ALLOWED_REQUESTED_CHECKS = {
    "project_structure",
    "dependency_metadata",
    "test_metadata",
    "config_metadata",
    "documentation_metadata",
    "risk_annotation",
    "policy_alignment_notes",
    "evidence_alignment_notes",
    "security_review_notes",
    "migration_notes",
    "release_notes",
    "unknowns_and_limitations",
}

ALLOWED_FINDING_SEVERITIES = {"info", "low", "medium", "high", "critical", "unknown"}
FORBIDDEN_AUDIT_SCOPES = {
    "write",
    "write_files",
    "file_write",
    "code_write",
    "modify_files",
    "git_commit",
    "git_push",
    "run_tests",
    "test_execution",
    "repo_scan",
    "model_review",
    "external_api",
}
FORBIDDEN_REQUEST_FLAGS = {
    "run_git": "git_command_request_denied",
    "git_command": "git_command_request_denied",
    "execute_tests": "test_execution_request_denied",
    "run_tests": "test_execution_request_denied",
    "mutate_files": "file_mutation_request_denied",
    "write_files": "file_mutation_request_denied",
    "model_review": "model_review_request_denied",
    "call_model": "model_review_request_denied",
    "external_api_request": "external_api_request_denied",
    "call_external_api": "external_api_request_denied",
    "call_tools": "tool_call_request_denied",
    "mcp_tool_call": "tool_call_request_denied",
    "repo_scanning": "repo_scanning_request_denied",
    "read_repo_files": "repo_file_read_request_denied",
    "developer_work_passport_certification": "developer_work_passport_certification_denied",
    "compliance_certification": "certification_claim_denied",
    "legal_certification": "certification_claim_denied",
    "security_certification": "certification_claim_denied",
}


@dataclass(frozen=True)
class RepoAuditSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class RepoAuditScope:
    audit_scope: tuple[str, ...]
    requested_checks: tuple[str, ...]
    excluded_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepoAuditFinding:
    finding_id: str
    severity: str
    category: str
    title: str
    summary: str
    source_refs: tuple[str, ...]
    confidence: str | None = None
    uncertainty: str | None = None
    suggested_next_step: str | None = None
    blocked_by_missing_source: bool = False
    evidence_refs: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepoAuditInput:
    repo_id: str | None
    repo_name: str | None
    repo_root_ref: str | None
    commit_ref: str | None
    branch_ref: str | None
    source_refs: tuple[RepoAuditSourceRef, ...]
    file_refs: tuple[str, ...]
    test_refs: tuple[str, ...]
    dependency_refs: tuple[str, ...]
    config_refs: tuple[str, ...]
    docs_refs: tuple[str, ...]
    scope: RepoAuditScope
    tenant_scope: str | None
    project_scope: str
    namespace: str
    privacy_class: str | None
    data_sensitivity: str | None
    generated_at: str | None


@dataclass(frozen=True)
class RepoAuditReportContract:
    report_id: str | None
    repo_id: str | None
    commit_ref: str | None
    scope: tuple[str, ...]
    findings: tuple[RepoAuditFinding, ...]
    limitations: tuple[str, ...]
    source_refs: tuple[str, ...]
    unknowns: tuple[str, ...]
    generated_by: str | None
    authority: bool = False
    evidence_provided_by_report: bool = False
    verifier_success: bool = False
    execution_permission: str = REPO_AUDIT_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


@dataclass(frozen=True)
class RepoAuditValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RepoAuditDecision:
    contract_version: str
    validation_status: str
    repo_id: str | None
    repo_name: str | None
    audit_scope: tuple[str, ...]
    requested_checks: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[RepoAuditValidationFailure, ...]
    audit_input: RepoAuditInput | None = None
    report_contract: RepoAuditReportContract | None = None
    authority: bool = False
    execution_permission: str = REPO_AUDIT_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_report: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_source_refs: bool = True
    requires_human_review: bool = True


def validate_repo_audit_request(
    request: Mapping[str, Any] | None,
    *,
    vertical_pack_decision: Any | None = None,
) -> RepoAuditDecision:
    """Validate a caller-supplied Repo Audit Pack request.

    This helper validates metadata contracts only. It never scans a repo,
    reads files, runs git, runs tests, calls tools, calls models, persists
    reports, or connects to runtime execution.
    """

    failures: list[RepoAuditValidationFailure] = []
    if not isinstance(request, Mapping):
        failure = RepoAuditValidationFailure(
            reason="missing_request",
            field="request",
            message="repo audit request must be a mapping",
        )
        return _decision(
            validation_status="failed_validation",
            repo_id=None,
            repo_name=None,
            audit_scope=(),
            requested_checks=(),
            failures=(failure,),
        )

    repo_id = _text(request.get("repo_id")) or None
    repo_name = _text(request.get("repo_name")) or None
    commit_ref = _text(request.get("commit_ref")) or None
    audit_scope = _strings(request.get("audit_scope"))
    requested_checks = _strings(request.get("requested_checks"))

    if not repo_id and not repo_name:
        _add_failure(
            failures,
            "repo_identity_required",
            "repo_id",
            "repo_id or repo_name is required",
        )
    if not commit_ref and request.get("commit_ref_unknown") is not True:
        _add_failure(
            failures,
            "commit_ref_or_unknown_marker_required",
            "commit_ref",
            "commit_ref is required unless commit_ref_unknown=true",
        )
    if not _text(request.get("namespace")):
        _add_failure(failures, "namespace_required", "namespace", "namespace is required")
    if not _text(request.get("project_scope")):
        _add_failure(
            failures,
            "project_scope_required",
            "project_scope",
            "project scope is required",
        )
    if not audit_scope:
        _add_failure(
            failures,
            "audit_scope_required",
            "audit_scope",
            "at least one audit scope is required",
        )
    if not requested_checks:
        _add_failure(
            failures,
            "requested_checks_required",
            "requested_checks",
            "at least one requested check family is required",
        )

    _validate_scopes(audit_scope, failures)
    _validate_requested_checks(requested_checks, failures)
    _validate_non_authority_fields(request, failures)
    _validate_forbidden_requests(request, audit_scope, requested_checks, failures)
    _validate_source_refs(request, failures)
    findings = _validate_findings(request.get("findings"), failures)
    _validate_report_contract_request(request, findings, failures)
    _validate_vertical_pack_relationship(vertical_pack_decision, failures)

    audit_input = None
    if _text(request.get("namespace")) and _text(request.get("project_scope")):
        audit_input = RepoAuditInput(
            repo_id=repo_id,
            repo_name=repo_name,
            repo_root_ref=_text(request.get("repo_root_ref")) or None,
            commit_ref=commit_ref,
            branch_ref=_text(request.get("branch_ref")) or None,
            source_refs=_source_refs(request.get("source_refs")),
            file_refs=_strings(request.get("file_refs")),
            test_refs=_strings(request.get("test_refs")),
            dependency_refs=_strings(request.get("dependency_refs")),
            config_refs=_strings(request.get("config_refs")),
            docs_refs=_strings(request.get("docs_refs")),
            scope=RepoAuditScope(
                audit_scope=audit_scope,
                requested_checks=requested_checks,
                excluded_paths=_strings(request.get("excluded_paths")),
            ),
            tenant_scope=_text(request.get("tenant_scope")) or None,
            project_scope=_text(request.get("project_scope")),
            namespace=_text(request.get("namespace")),
            privacy_class=_text(request.get("privacy_class")) or None,
            data_sensitivity=_text(request.get("data_sensitivity")) or None,
            generated_at=_text(request.get("generated_at")) or None,
        )

    report_contract = RepoAuditReportContract(
        report_id=_text(request.get("report_id")) or None,
        repo_id=repo_id,
        commit_ref=commit_ref,
        scope=audit_scope,
        findings=tuple(findings),
        limitations=_strings(request.get("limitations")),
        source_refs=_ref_ids(request.get("source_refs")),
        unknowns=_strings(request.get("unknowns")),
        generated_by=_text(request.get("generated_by")) or None,
    )

    validation_status = "review_ready"
    if any(
        failure.reason
        in {
            "missing_request",
            "repo_identity_required",
            "namespace_required",
            "project_scope_required",
            "audit_scope_required",
            "requested_checks_required",
        }
        for failure in failures
    ):
        validation_status = "failed_validation"
    elif failures:
        validation_status = "blocked"

    return _decision(
        validation_status=validation_status,
        repo_id=repo_id,
        repo_name=repo_name,
        audit_scope=audit_scope,
        requested_checks=requested_checks,
        failures=tuple(failures),
        audit_input=audit_input,
        report_contract=report_contract,
    )


def _validate_scopes(
    audit_scope: tuple[str, ...],
    failures: list[RepoAuditValidationFailure],
) -> None:
    for scope in audit_scope:
        if scope in FORBIDDEN_AUDIT_SCOPES:
            _add_failure(
                failures,
                "write_or_execute_scope_denied",
                "audit_scope",
                f"{scope} is not a read-only repo audit scope",
            )
        elif scope not in ALLOWED_AUDIT_SCOPES:
            _add_failure(failures, "unknown_audit_scope", "audit_scope", scope)


def _validate_requested_checks(
    requested_checks: tuple[str, ...],
    failures: list[RepoAuditValidationFailure],
) -> None:
    for check in requested_checks:
        if check not in ALLOWED_REQUESTED_CHECKS:
            _add_failure(failures, "unknown_requested_check", "requested_checks", check)


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[RepoAuditValidationFailure],
) -> None:
    forbidden_truthy = {
        "authority": "authority_must_be_false",
        "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
        "approval_grant": "approval_grant_not_allowed",
        "capability_grant": "capability_grant_not_allowed",
        "lease_grant": "lease_grant_not_allowed",
        "evidence_provided_by_report": "report_cannot_provide_evidence",
        "evidence_provided_by_pack_output": "report_cannot_provide_evidence",
        "verifier_success": "report_cannot_mark_verifier_success",
        "tests_passed": "test_success_claim_denied",
        "code_safe": "code_safety_claim_denied",
        "runtime_truth": "runtime_truth_claim_denied",
    }
    for field_name, reason in forbidden_truthy.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority or truth",
            )
    if request.get("execution_permission") not in (None, "", REPO_AUDIT_EXECUTION_PERMISSION):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_repo_audit_required",
            "execution_permission",
            "repo audit request cannot grant execution permission",
        )


def _validate_forbidden_requests(
    request: Mapping[str, Any],
    audit_scope: tuple[str, ...],
    requested_checks: tuple[str, ...],
    failures: list[RepoAuditValidationFailure],
) -> None:
    for field_name, reason in FORBIDDEN_REQUEST_FLAGS.items():
        if request.get(field_name) is True or _text(request.get(field_name)):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside the read-only repo audit contract",
            )
    forbidden_tools = {
        "git",
        "git_commit",
        "git_push",
        "pytest",
        "run_tests",
        "write_file",
        "create_file",
        "edit_file",
        "subprocess",
        "model_call",
        "mcp_tool_call",
    }
    if forbidden_tools & set(_strings(request.get("requested_tools"))):
        _add_failure(
            failures,
            "requested_tool_execution_denied",
            "requested_tools",
            "repo audit contract does not request tools",
        )
    if "developer_work_passport_candidate" in audit_scope and request.get("final_passport") is True:
        _add_failure(
            failures,
            "developer_work_passport_certification_denied",
            "final_passport",
            "repo audit report is only candidate input for Developer Work Passport",
        )
    if "compliance_evidence_candidate" in audit_scope and request.get("final_compliance_certification") is True:
        _add_failure(
            failures,
            "certification_claim_denied",
            "final_compliance_certification",
            "repo audit report is not compliance certification",
        )
    if "test_metadata" in requested_checks and request.get("test_refs") in (None, "", []):
        _add_failure(
            failures,
            "test_metadata_requires_test_refs",
            "test_refs",
            "test metadata checks require caller-supplied test refs",
        )


def _validate_source_refs(
    request: Mapping[str, Any],
    failures: list[RepoAuditValidationFailure],
) -> None:
    source_refs = _source_refs(request.get("source_refs"))
    if not source_refs:
        _add_failure(
            failures,
            "source_refs_required",
            "source_refs",
            "repo audit contracts require caller-supplied source refs",
        )
    for ref in source_refs:
        if ref.ref_id in {"*", "all", "any"}:
            _add_failure(
                failures,
                "wildcard_source_ref_denied",
                "source_refs",
                "wildcard source refs are denied",
            )
        if not ref.ref_type:
            _add_failure(
                failures,
                "source_ref_type_required",
                "source_refs",
                "source refs require a type",
            )


def _validate_findings(
    raw_findings: Any,
    failures: list[RepoAuditValidationFailure],
) -> list[RepoAuditFinding]:
    findings: list[RepoAuditFinding] = []
    for index, raw_finding in enumerate(_items(raw_findings)):
        if not isinstance(raw_finding, Mapping):
            _add_failure(
                failures,
                "finding_mapping_required",
                f"findings[{index}]",
                "findings must be mappings",
            )
            continue
        severity = _text(raw_finding.get("severity")) or "unknown"
        if severity not in ALLOWED_FINDING_SEVERITIES:
            _add_failure(
                failures,
                "unknown_finding_severity",
                f"findings[{index}].severity",
                severity,
            )
        source_refs = _strings(raw_finding.get("source_refs"))
        uncertainty = _text(raw_finding.get("uncertainty")) or None
        blocked_by_missing_source = raw_finding.get("blocked_by_missing_source") is True
        if not source_refs and not uncertainty and not blocked_by_missing_source:
            _add_failure(
                failures,
                "finding_without_source_requires_uncertainty",
                f"findings[{index}].source_refs",
                "findings without source refs must be marked uncertain or blocked",
            )
        findings.append(
            RepoAuditFinding(
                finding_id=_text(raw_finding.get("finding_id")) or f"finding-{index + 1}",
                severity=severity,
                category=_text(raw_finding.get("category")) or "unknown",
                title=_text(raw_finding.get("title")) or "Untitled finding",
                summary=_text(raw_finding.get("summary")) or "",
                source_refs=source_refs,
                confidence=_text(raw_finding.get("confidence")) or None,
                uncertainty=uncertainty,
                suggested_next_step=_text(raw_finding.get("suggested_next_step")) or None,
                blocked_by_missing_source=blocked_by_missing_source,
                evidence_refs=_strings(raw_finding.get("evidence_refs")),
                policy_refs=_strings(raw_finding.get("policy_refs")),
                labels=_strings(raw_finding.get("labels")),
            )
        )
    return findings


def _validate_report_contract_request(
    request: Mapping[str, Any],
    findings: list[RepoAuditFinding],
    failures: list[RepoAuditValidationFailure],
) -> None:
    if findings and not _source_refs(request.get("source_refs")):
        _add_failure(
            failures,
            "report_findings_require_source_refs",
            "source_refs",
            "report findings require caller-supplied source refs",
        )
    claims = " ".join(_strings(request.get("claims"))).lower()
    blocked_claims = {
        "developer work passport certification": "developer_work_passport_certification_denied",
        "compliance certification": "certification_claim_denied",
        "legal certification": "certification_claim_denied",
        "security certification": "certification_claim_denied",
        "tests passed": "test_success_claim_denied",
        "code is safe": "code_safety_claim_denied",
    }
    for phrase, reason in blocked_claims.items():
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"repo audit report cannot claim {phrase}",
            )


def _validate_vertical_pack_relationship(
    vertical_pack_decision: Any | None,
    failures: list[RepoAuditValidationFailure],
) -> None:
    if vertical_pack_decision is None:
        return
    if _bool_field(vertical_pack_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "vertical_pack_runtime_dispatch_attempt_denied",
            "vertical_pack_decision.runtime_dispatch_allowed",
            "vertical pack decision cannot grant dispatch",
        )
    if _field(vertical_pack_decision, "pack_category") != "repo_audit":
        _add_failure(
            failures,
            "vertical_pack_category_must_be_repo_audit",
            "vertical_pack_decision.pack_category",
            "Repo Audit Pack requires repo_audit vertical pack category",
        )
    if _field(vertical_pack_decision, "operating_profile") not in {"read_only", "proposal_only"}:
        _add_failure(
            failures,
            "vertical_pack_profile_must_be_read_or_proposal_only",
            "vertical_pack_decision.operating_profile",
            "Repo Audit Pack requires read_only or proposal_only vertical pack profile",
        )
    if _field(vertical_pack_decision, "validation_status") != "review_ready":
        _add_failure(
            failures,
            "vertical_pack_decision_not_review_ready",
            "vertical_pack_decision.validation_status",
            "Repo Audit Pack requires a review-ready vertical pack decision",
        )
    if _tuple_field(vertical_pack_decision, "failure_reasons"):
        _add_failure(
            failures,
            "vertical_pack_decision_has_failures",
            "vertical_pack_decision.failure_reasons",
            "Repo Audit Pack requires a clean vertical pack decision",
        )


def _source_refs(value: Any) -> tuple[RepoAuditSourceRef, ...]:
    refs: list[RepoAuditSourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                RepoAuditSourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            item_id = _text(item)
            if item_id:
                refs.append(RepoAuditSourceRef(ref_id=item_id, ref_type="unspecified"))
    return tuple(refs)


def _ref_ids(value: Any) -> tuple[str, ...]:
    return tuple(ref.ref_id for ref in _source_refs(value))


def _decision(
    *,
    validation_status: str,
    repo_id: str | None,
    repo_name: str | None,
    audit_scope: tuple[str, ...],
    requested_checks: tuple[str, ...],
    failures: tuple[RepoAuditValidationFailure, ...],
    audit_input: RepoAuditInput | None = None,
    report_contract: RepoAuditReportContract | None = None,
) -> RepoAuditDecision:
    return RepoAuditDecision(
        contract_version=REPO_AUDIT_PACK_CONTRACT_VERSION,
        validation_status=validation_status,
        repo_id=repo_id,
        repo_name=repo_name,
        audit_scope=audit_scope,
        requested_checks=requested_checks,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        audit_input=audit_input,
        report_contract=report_contract,
    )


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


def _tuple_field(value: Any, field_name: str) -> tuple[Any, ...]:
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
    if isinstance(value, Mapping):
        return _text(value.get(field_name))
    return _text(getattr(value, field_name, None))


def _bool_field(value: Any, field_name: str) -> bool:
    if isinstance(value, Mapping):
        return value.get(field_name) is True
    return getattr(value, field_name, None) is True


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _add_failure(
    failures: list[RepoAuditValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(RepoAuditValidationFailure(reason=reason, field=field, message=message))
