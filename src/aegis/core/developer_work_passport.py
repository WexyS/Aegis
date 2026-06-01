from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


DEVELOPER_WORK_PASSPORT_CONTRACT_VERSION = "developer-work-passport-contract/1"
DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION = "not_granted_by_developer_work_passport"

ALLOWED_PASSPORT_SCOPES = {
    "work_summary",
    "repo_audit_summary",
    "change_summary",
    "test_summary_refs",
    "policy_alignment_summary",
    "evidence_refs_summary",
    "llm_assistance_disclosure",
    "tool_usage_disclosure",
    "limitations_and_unknowns",
    "client_delivery_summary",
    "compliance_candidate_notes",
}

ALLOWED_DISCLOSURE_CATEGORIES = {
    "changed_files",
    "commits",
    "tests_referenced",
    "reviews_referenced",
    "repo_audit_candidate",
    "llm_assistance",
    "tool_usage",
    "policy_alignment",
    "evidence_refs",
    "limitations",
    "unknowns",
    "human_review_required",
}

FORBIDDEN_PASSPORT_SCOPES = {
    "write",
    "execute",
    "git_command",
    "git_commit",
    "git_push",
    "run_tests",
    "test_execution",
    "file_write",
    "file_mutation",
    "model_review",
    "tool_execution",
    "api_delivery",
    "external_sharing",
    "surveillance",
    "worker_monitoring",
}

FORBIDDEN_REQUEST_FLAGS = {
    "external_sharing": "external_sharing_denied",
    "share_externally": "external_sharing_denied",
    "surveillance_mode": "surveillance_denied",
    "hidden_monitoring": "hidden_monitoring_denied",
    "background_tracking": "hidden_monitoring_denied",
    "keystroke_logging": "surveillance_denied",
    "screen_recording": "surveillance_denied",
    "activity_surveillance": "surveillance_denied",
    "worker_monitoring": "worker_monitoring_denied",
    "productivity_score": "productivity_score_denied",
    "worker_compliance_score": "productivity_score_denied",
    "work_quality_proof": "proof_of_quality_denied",
    "proof_of_quality": "proof_of_quality_denied",
    "tests_passed": "test_success_claim_denied",
    "proof_tests_passed": "test_success_claim_denied",
    "code_safe": "code_safety_claim_denied",
    "proof_code_safe": "code_safety_claim_denied",
    "developer_work_passport_certification": "certification_claim_denied",
    "compliance_certification": "certification_claim_denied",
    "legal_certification": "certification_claim_denied",
    "security_certification": "certification_claim_denied",
    "run_git": "git_command_request_denied",
    "git_command": "git_command_request_denied",
    "execute_tests": "test_execution_request_denied",
    "run_tests": "test_execution_request_denied",
    "mutate_files": "file_mutation_request_denied",
    "write_files": "file_mutation_request_denied",
    "model_review": "model_review_request_denied",
    "call_model": "model_review_request_denied",
    "call_tools": "tool_call_request_denied",
    "mcp_tool_call": "tool_call_request_denied",
    "external_api_request": "api_request_denied",
    "call_external_api": "api_request_denied",
    "repo_scanning": "repo_scanning_request_denied",
    "read_repo_files": "repo_file_read_request_denied",
}


@dataclass(frozen=True)
class DeveloperWorkPassportSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class DeveloperWorkPassportScope:
    disclosure_scope: tuple[str, ...]
    disclosure_categories: tuple[str, ...]
    audience: str | None = None


@dataclass(frozen=True)
class DeveloperWorkPassportDisclosure:
    disclosure_id: str
    category: str
    summary: str
    source_refs: tuple[str, ...]
    confidence: str | None = None
    uncertainty: str | None = None
    blocked_by_missing_source: bool = False
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeveloperWorkPassportInput:
    passport_id: str | None
    developer_ref: str | None
    project_ref: str | None
    repo_ref: str | None
    commit_refs: tuple[str, ...]
    branch_ref: str | None
    source_refs: tuple[DeveloperWorkPassportSourceRef, ...]
    changed_file_refs: tuple[str, ...]
    test_refs: tuple[str, ...]
    review_refs: tuple[str, ...]
    repo_audit_refs: tuple[str, ...]
    policy_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    llm_assistance_refs: tuple[str, ...]
    tool_usage_refs: tuple[str, ...]
    limitation_notes: tuple[str, ...]
    unknowns: tuple[str, ...]
    scope: DeveloperWorkPassportScope
    tenant_scope: str | None
    project_scope: str
    namespace: str
    privacy_class: str | None
    data_sensitivity: str | None
    generated_at: str | None


@dataclass(frozen=True)
class DeveloperWorkPassportReportContract:
    report_id: str | None
    passport_id: str | None
    developer_ref: str | None
    project_ref: str | None
    repo_ref: str | None
    commit_refs: tuple[str, ...]
    disclosures: tuple[DeveloperWorkPassportDisclosure, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    source_refs: tuple[str, ...]
    repo_audit_refs: tuple[str, ...]
    generated_by: str | None
    authority: bool = False
    evidence_provided_by_passport: bool = False
    verifier_success: bool = False
    execution_permission: str = DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    not_surveillance: bool = True
    not_certification: bool = True


@dataclass(frozen=True)
class DeveloperWorkPassportValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class DeveloperWorkPassportDecision:
    contract_version: str
    validation_status: str
    passport_id: str | None
    developer_ref: str | None
    project_ref: str | None
    disclosure_scope: tuple[str, ...]
    disclosure_categories: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[DeveloperWorkPassportValidationFailure, ...]
    passport_input: DeveloperWorkPassportInput | None = None
    report_contract: DeveloperWorkPassportReportContract | None = None
    authority: bool = False
    execution_permission: str = DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_passport: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_source_refs: bool = True
    not_surveillance: bool = True
    not_certification: bool = True


def validate_developer_work_passport_request(
    request: Mapping[str, Any] | None,
    *,
    vertical_pack_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
) -> DeveloperWorkPassportDecision:
    """Validate caller-supplied Developer Work Passport metadata.

    The helper is pure. It does not generate passports, scan repos, read files,
    run git, run tests, call tools, call models, call APIs, write memory, or
    connect to runtime execution.
    """

    failures: list[DeveloperWorkPassportValidationFailure] = []
    if not isinstance(request, Mapping):
        failure = DeveloperWorkPassportValidationFailure(
            reason="missing_request",
            field="request",
            message="developer work passport request must be a mapping",
        )
        return _decision(
            validation_status="failed_validation",
            passport_id=None,
            developer_ref=None,
            project_ref=None,
            disclosure_scope=(),
            disclosure_categories=(),
            failures=(failure,),
        )

    passport_id = _text(request.get("passport_id")) or None
    developer_ref = _text(request.get("developer_ref")) or None
    project_ref = _text(request.get("project_ref")) or None
    disclosure_scope = _strings(request.get("disclosure_scope"))
    disclosure_categories = _strings(request.get("disclosure_categories"))

    if not passport_id and not (developer_ref and project_ref):
        _add_failure(
            failures,
            "passport_or_developer_project_identity_required",
            "passport_id",
            "passport_id or developer_ref plus project_ref is required",
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
    if not disclosure_scope:
        _add_failure(
            failures,
            "disclosure_scope_required",
            "disclosure_scope",
            "at least one disclosure scope is required",
        )
    if not disclosure_categories:
        _add_failure(
            failures,
            "disclosure_categories_required",
            "disclosure_categories",
            "at least one disclosure category is required",
        )

    _validate_scopes(disclosure_scope, failures)
    _validate_disclosure_categories(disclosure_categories, failures)
    _validate_non_authority_fields(request, failures)
    _validate_forbidden_requests(request, disclosure_scope, failures)
    _validate_source_refs(request, failures)
    disclosures = _validate_disclosures(request.get("disclosures"), failures)
    _validate_claims(request, failures)
    _validate_test_claims(request, disclosure_categories, failures)
    _validate_repo_audit_relationship(repo_audit_decision, failures)
    _validate_vertical_pack_relationship(vertical_pack_decision, failures)

    passport_input = None
    if _text(request.get("namespace")) and _text(request.get("project_scope")):
        passport_input = DeveloperWorkPassportInput(
            passport_id=passport_id,
            developer_ref=developer_ref,
            project_ref=project_ref,
            repo_ref=_text(request.get("repo_ref")) or None,
            commit_refs=_strings(request.get("commit_refs")),
            branch_ref=_text(request.get("branch_ref")) or None,
            source_refs=_source_refs(request.get("source_refs")),
            changed_file_refs=_strings(request.get("changed_file_refs")),
            test_refs=_strings(request.get("test_refs")),
            review_refs=_strings(request.get("review_refs")),
            repo_audit_refs=_strings(request.get("repo_audit_refs")),
            policy_refs=_strings(request.get("policy_refs")),
            evidence_refs=_strings(request.get("evidence_refs")),
            llm_assistance_refs=_strings(request.get("llm_assistance_refs")),
            tool_usage_refs=_strings(request.get("tool_usage_refs")),
            limitation_notes=_strings(request.get("limitation_notes")),
            unknowns=_strings(request.get("unknowns")),
            scope=DeveloperWorkPassportScope(
                disclosure_scope=disclosure_scope,
                disclosure_categories=disclosure_categories,
                audience=_text(request.get("audience")) or None,
            ),
            tenant_scope=_text(request.get("tenant_scope")) or None,
            project_scope=_text(request.get("project_scope")),
            namespace=_text(request.get("namespace")),
            privacy_class=_text(request.get("privacy_class")) or None,
            data_sensitivity=_text(request.get("data_sensitivity")) or None,
            generated_at=_text(request.get("generated_at")) or None,
        )

    report_contract = DeveloperWorkPassportReportContract(
        report_id=_text(request.get("report_id")) or None,
        passport_id=passport_id,
        developer_ref=developer_ref,
        project_ref=project_ref,
        repo_ref=_text(request.get("repo_ref")) or None,
        commit_refs=_strings(request.get("commit_refs")),
        disclosures=tuple(disclosures),
        limitations=_strings(request.get("limitation_notes")) or _strings(request.get("limitations")),
        unknowns=_strings(request.get("unknowns")),
        source_refs=_ref_ids(request.get("source_refs")),
        repo_audit_refs=_strings(request.get("repo_audit_refs")),
        generated_by=_text(request.get("generated_by")) or None,
    )

    validation_status = "review_ready"
    if any(
        failure.reason
        in {
            "missing_request",
            "passport_or_developer_project_identity_required",
            "namespace_required",
            "project_scope_required",
            "disclosure_scope_required",
            "disclosure_categories_required",
        }
        for failure in failures
    ):
        validation_status = "failed_validation"
    elif failures:
        validation_status = "blocked"

    return _decision(
        validation_status=validation_status,
        passport_id=passport_id,
        developer_ref=developer_ref,
        project_ref=project_ref,
        disclosure_scope=disclosure_scope,
        disclosure_categories=disclosure_categories,
        failures=tuple(failures),
        passport_input=passport_input,
        report_contract=report_contract,
    )


def _validate_scopes(
    disclosure_scope: tuple[str, ...],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    for scope in disclosure_scope:
        if scope in FORBIDDEN_PASSPORT_SCOPES:
            _add_failure(
                failures,
                "write_or_execute_scope_denied",
                "disclosure_scope",
                f"{scope} is not a Developer Work Passport transparency scope",
            )
        elif scope not in ALLOWED_PASSPORT_SCOPES:
            _add_failure(failures, "unknown_passport_scope", "disclosure_scope", scope)


def _validate_disclosure_categories(
    disclosure_categories: tuple[str, ...],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    for category in disclosure_categories:
        if category not in ALLOWED_DISCLOSURE_CATEGORIES:
            _add_failure(
                failures,
                "unknown_disclosure_category",
                "disclosure_categories",
                category,
            )


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    forbidden_truthy = {
        "authority": "authority_must_be_false",
        "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
        "approval_grant": "approval_grant_not_allowed",
        "capability_grant": "capability_grant_not_allowed",
        "lease_grant": "lease_grant_not_allowed",
        "evidence_provided_by_passport": "passport_cannot_provide_evidence",
        "evidence_provided_by_report": "passport_cannot_provide_evidence",
        "evidence_provided_by_pack_output": "passport_cannot_provide_evidence",
        "verifier_success": "passport_cannot_mark_verifier_success",
        "success": "success_claim_denied",
    }
    for field_name, reason in forbidden_truthy.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority or truth",
            )
    if request.get("execution_permission") not in (
        None,
        "",
        DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_passport_required",
            "execution_permission",
            "Developer Work Passport cannot grant execution permission",
        )


def _validate_forbidden_requests(
    request: Mapping[str, Any],
    disclosure_scope: tuple[str, ...],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    for field_name, reason in FORBIDDEN_REQUEST_FLAGS.items():
        if request.get(field_name) is True or _text(request.get(field_name)):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside the Developer Work Passport contract",
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
        "external_api",
    }
    if forbidden_tools & set(_strings(request.get("requested_tools"))):
        _add_failure(
            failures,
            "requested_tool_execution_denied",
            "requested_tools",
            "Developer Work Passport contract does not request tools",
        )
    if "compliance_candidate_notes" in disclosure_scope and request.get("final_compliance_certification") is True:
        _add_failure(
            failures,
            "certification_claim_denied",
            "final_compliance_certification",
            "Developer Work Passport is not compliance certification",
        )


def _validate_source_refs(
    request: Mapping[str, Any],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    refs = _source_refs(request.get("source_refs"))
    if not refs:
        _add_failure(
            failures,
            "source_refs_required",
            "source_refs",
            "Developer Work Passport requires caller-supplied source refs",
        )
    for ref in refs:
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


def _validate_disclosures(
    raw_disclosures: Any,
    failures: list[DeveloperWorkPassportValidationFailure],
) -> list[DeveloperWorkPassportDisclosure]:
    disclosures: list[DeveloperWorkPassportDisclosure] = []
    for index, raw_disclosure in enumerate(_items(raw_disclosures)):
        if not isinstance(raw_disclosure, Mapping):
            _add_failure(
                failures,
                "disclosure_mapping_required",
                f"disclosures[{index}]",
                "disclosures must be mappings",
            )
            continue
        category = _text(raw_disclosure.get("category")) or "unknowns"
        if category not in ALLOWED_DISCLOSURE_CATEGORIES:
            _add_failure(
                failures,
                "unknown_disclosure_category",
                f"disclosures[{index}].category",
                category,
            )
        source_refs = _strings(raw_disclosure.get("source_refs"))
        uncertainty = _text(raw_disclosure.get("uncertainty")) or None
        blocked = raw_disclosure.get("blocked_by_missing_source") is True
        if not source_refs and not uncertainty and not blocked:
            _add_failure(
                failures,
                "disclosure_without_source_requires_uncertainty",
                f"disclosures[{index}].source_refs",
                "disclosures without source refs must be uncertain or blocked",
            )
        disclosures.append(
            DeveloperWorkPassportDisclosure(
                disclosure_id=_text(raw_disclosure.get("disclosure_id"))
                or f"disclosure-{index + 1}",
                category=category,
                summary=_text(raw_disclosure.get("summary")) or "",
                source_refs=source_refs,
                confidence=_text(raw_disclosure.get("confidence")) or None,
                uncertainty=uncertainty,
                blocked_by_missing_source=blocked,
                labels=_strings(raw_disclosure.get("labels")),
            )
        )
    return disclosures


def _validate_claims(
    request: Mapping[str, Any],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    blocked_claims = {
        "legal certification": "certification_claim_denied",
        "compliance certification": "certification_claim_denied",
        "security certification": "certification_claim_denied",
        "work quality": "proof_of_quality_denied",
        "high quality work": "proof_of_quality_denied",
        "tests passed": "test_success_claim_denied",
        "code is safe": "code_safety_claim_denied",
        "complete llm usage": "llm_usage_completeness_claim_denied",
        "forensic-grade export": "certification_claim_denied",
        "worker compliance score": "productivity_score_denied",
        "productivity score": "productivity_score_denied",
    }
    for phrase, reason in blocked_claims.items():
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"Developer Work Passport cannot claim {phrase}",
            )


def _validate_test_claims(
    request: Mapping[str, Any],
    disclosure_categories: tuple[str, ...],
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    test_refs = _strings(request.get("test_refs"))
    if "tests_referenced" in disclosure_categories and request.get("tests_passed") is True and not test_refs:
        _add_failure(
            failures,
            "test_success_claim_requires_test_refs",
            "test_refs",
            "test success claims require caller-supplied test refs",
        )
    if request.get("tests_passed") is True and not test_refs:
        _add_failure(
            failures,
            "test_success_claim_denied",
            "tests_passed",
            "passport cannot prove tests passed without test refs",
        )


def _validate_repo_audit_relationship(
    repo_audit_decision: Any | None,
    failures: list[DeveloperWorkPassportValidationFailure],
) -> None:
    if repo_audit_decision is None:
        return
    if _bool_field(repo_audit_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "repo_audit_runtime_dispatch_attempt_denied",
            "repo_audit_decision.runtime_dispatch_allowed",
            "repo audit decision cannot grant dispatch to passport",
        )
    if _bool_field(repo_audit_decision, "evidence_provided_by_report"):
        _add_failure(
            failures,
            "repo_audit_evidence_claim_denied",
            "repo_audit_decision.evidence_provided_by_report",
            "repo audit output cannot become passport evidence",
        )
    if _bool_field(repo_audit_decision, "verifier_success"):
        _add_failure(
            failures,
            "repo_audit_verifier_success_claim_denied",
            "repo_audit_decision.verifier_success",
            "repo audit output cannot become verifier success",
        )
    if _field(repo_audit_decision, "validation_status") not in {"review_ready", ""}:
        _add_failure(
            failures,
            "repo_audit_decision_not_review_ready",
            "repo_audit_decision.validation_status",
            "repo audit candidate input must remain review-ready metadata",
        )


def _validate_vertical_pack_relationship(
    vertical_pack_decision: Any | None,
    failures: list[DeveloperWorkPassportValidationFailure],
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
    if _field(vertical_pack_decision, "pack_category") != "developer_work_passport":
        _add_failure(
            failures,
            "vertical_pack_category_must_be_developer_work_passport",
            "vertical_pack_decision.pack_category",
            "Developer Work Passport requires developer_work_passport vertical pack category",
        )
    if _field(vertical_pack_decision, "operating_profile") != "evidence_reporting":
        _add_failure(
            failures,
            "vertical_pack_profile_must_be_evidence_reporting",
            "vertical_pack_decision.operating_profile",
            "Developer Work Passport requires evidence_reporting vertical pack profile",
        )
    if _field(vertical_pack_decision, "validation_status") != "review_ready":
        _add_failure(
            failures,
            "vertical_pack_decision_not_review_ready",
            "vertical_pack_decision.validation_status",
            "Developer Work Passport requires a review-ready vertical pack decision",
        )
    if _tuple_field(vertical_pack_decision, "failure_reasons"):
        _add_failure(
            failures,
            "vertical_pack_decision_has_failures",
            "vertical_pack_decision.failure_reasons",
            "Developer Work Passport requires a clean vertical pack decision",
        )


def _source_refs(value: Any) -> tuple[DeveloperWorkPassportSourceRef, ...]:
    refs: list[DeveloperWorkPassportSourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                DeveloperWorkPassportSourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            item_id = _text(item)
            if item_id:
                refs.append(DeveloperWorkPassportSourceRef(ref_id=item_id, ref_type="unspecified"))
    return tuple(refs)


def _ref_ids(value: Any) -> tuple[str, ...]:
    return tuple(ref.ref_id for ref in _source_refs(value))


def _decision(
    *,
    validation_status: str,
    passport_id: str | None,
    developer_ref: str | None,
    project_ref: str | None,
    disclosure_scope: tuple[str, ...],
    disclosure_categories: tuple[str, ...],
    failures: tuple[DeveloperWorkPassportValidationFailure, ...],
    passport_input: DeveloperWorkPassportInput | None = None,
    report_contract: DeveloperWorkPassportReportContract | None = None,
) -> DeveloperWorkPassportDecision:
    return DeveloperWorkPassportDecision(
        contract_version=DEVELOPER_WORK_PASSPORT_CONTRACT_VERSION,
        validation_status=validation_status,
        passport_id=passport_id,
        developer_ref=developer_ref,
        project_ref=project_ref,
        disclosure_scope=disclosure_scope,
        disclosure_categories=disclosure_categories,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        passport_input=passport_input,
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
    failures: list[DeveloperWorkPassportValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(
        DeveloperWorkPassportValidationFailure(reason=reason, field=field, message=message)
    )
