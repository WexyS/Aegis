from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


COMPLIANCE_EVIDENCE_PACK_CONTRACT_VERSION = "compliance-evidence-pack-readiness/1"
COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION = "not_granted_by_compliance_evidence_pack"

ALLOWED_EVIDENCE_SCOPES = {
    "policy_alignment_notes",
    "evidence_refs_summary",
    "repo_audit_candidate_notes",
    "developer_work_passport_candidate_notes",
    "control_mapping_candidate",
    "audit_readiness_notes",
    "forensic_readiness_notes",
    "limitations_and_unknowns",
    "risk_register_candidate",
    "remediation_plan_candidate",
    "compliance_gap_candidate",
    "human_review_queue_candidate",
}

FORBIDDEN_EVIDENCE_SCOPES = {
    "write",
    "execute",
    "file_write",
    "git_command",
    "run_tests",
    "test_execution",
    "repo_scan",
    "model_review",
    "tool_execution",
    "api_export",
    "external_sharing",
    "court_admissible_evidence",
    "legal_certification",
    "compliance_certification",
    "security_certification",
}

ALLOWED_MAPPING_STATUSES = {
    "candidate",
    "mapped_with_refs",
    "missing_refs",
    "uncertain",
    "not_applicable",
    "blocked",
}

ALLOWED_CANDIDATE_CATEGORIES = {
    "policy_reference",
    "evidence_reference",
    "repo_audit_reference",
    "developer_work_passport_reference",
    "control_mapping",
    "risk_note",
    "remediation_note",
    "limitation_note",
    "unknown_note",
}

FORBIDDEN_REQUEST_FLAGS = {
    "legal_certification": "legal_certification_claim_denied",
    "compliance_certification": "compliance_certification_claim_denied",
    "security_certification": "security_certification_claim_denied",
    "court_admissible_evidence": "court_admissible_claim_denied",
    "court_admissible_claim": "court_admissible_claim_denied",
    "official_audit_result": "official_audit_result_claim_denied",
    "proof_of_compliance": "proof_of_compliance_claim_denied",
    "proof_controls_effective": "proof_control_effective_claim_denied",
    "controls_effective": "proof_control_effective_claim_denied",
    "proof_organization_safe": "proof_organization_safe_claim_denied",
    "organization_safe": "proof_organization_safe_claim_denied",
    "external_sharing": "external_sharing_denied",
    "share_externally": "external_sharing_denied",
    "export_report": "external_export_denied",
    "forensic_export": "external_export_denied",
    "sign_report": "report_signing_denied",
    "run_git": "git_command_request_denied",
    "git_command": "git_command_request_denied",
    "execute_tests": "test_execution_request_denied",
    "run_tests": "test_execution_request_denied",
    "mutate_files": "file_mutation_request_denied",
    "write_files": "file_mutation_request_denied",
    "repo_scanning": "repo_scanning_request_denied",
    "read_repo_files": "repo_file_read_request_denied",
    "model_review": "model_review_request_denied",
    "call_model": "model_review_request_denied",
    "call_tools": "tool_call_request_denied",
    "mcp_tool_call": "tool_call_request_denied",
    "external_api_request": "api_request_denied",
    "call_external_api": "api_request_denied",
}


@dataclass(frozen=True)
class ComplianceEvidenceSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class ComplianceFrameworkRef:
    framework_name: str
    framework_version: str | None = None
    source_refs: tuple[str, ...] = ()
    human_review_required: bool = True


@dataclass(frozen=True)
class ComplianceControlRef:
    control_id: str
    framework_name: str
    framework_version: str | None
    mapping_status: str
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    confidence: str | None = None
    uncertainty: str | None = None
    human_review_required: bool = True


@dataclass(frozen=True)
class ComplianceEvidenceCandidate:
    candidate_id: str
    category: str
    summary: str
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    policy_refs: tuple[str, ...]
    repo_audit_refs: tuple[str, ...]
    developer_work_passport_refs: tuple[str, ...]
    confidence: str | None = None
    uncertainty: str | None = None
    limitations: tuple[str, ...] = ()
    human_review_required: bool = True
    blocked_by_missing_source: bool = False
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComplianceLimitation:
    note: str
    source_refs: tuple[str, ...] = ()
    uncertainty: str | None = None


@dataclass(frozen=True)
class ComplianceEvidenceInput:
    package_id: str | None
    project_ref: str | None
    tenant_scope: str
    project_scope: str
    namespace: str
    audit_context_ref: str | None
    source_refs: tuple[ComplianceEvidenceSourceRef, ...]
    policy_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    repo_audit_refs: tuple[str, ...]
    developer_work_passport_refs: tuple[str, ...]
    control_refs: tuple[ComplianceControlRef, ...]
    framework_refs: tuple[ComplianceFrameworkRef, ...]
    limitation_notes: tuple[str, ...]
    unknowns: tuple[str, ...]
    review_status: str | None
    evidence_scope: tuple[str, ...]
    data_sensitivity: str | None
    privacy_class: str | None
    generated_at: str | None


@dataclass(frozen=True)
class ComplianceEvidencePackageContract:
    package_id: str | None
    project_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    evidence_scope: tuple[str, ...]
    candidates: tuple[ComplianceEvidenceCandidate, ...]
    control_refs: tuple[ComplianceControlRef, ...]
    limitations: tuple[ComplianceLimitation, ...]
    unknowns: tuple[str, ...]
    source_refs: tuple[str, ...]
    policy_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    generated_by: str | None
    authority: bool = False
    evidence_provided_by_package: bool = False
    verifier_success: bool = False
    execution_permission: str = COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    not_certification: bool = True
    not_legal_advice: bool = True
    not_court_admissible_claim: bool = True


@dataclass(frozen=True)
class ComplianceEvidenceValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ComplianceEvidenceDecision:
    contract_version: str
    validation_status: str
    package_id: str | None
    project_ref: str | None
    evidence_scope: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[ComplianceEvidenceValidationFailure, ...]
    compliance_input: ComplianceEvidenceInput | None = None
    package_contract: ComplianceEvidencePackageContract | None = None
    authority: bool = False
    execution_permission: str = COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_package: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    requires_human_review: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_source_refs: bool = True
    not_certification: bool = True
    not_legal_advice: bool = True
    not_court_admissible_claim: bool = True


def validate_compliance_evidence_request(
    request: Mapping[str, Any] | None,
    *,
    vertical_pack_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
) -> ComplianceEvidenceDecision:
    """Validate caller-supplied Compliance Evidence Pack readiness metadata.

    The helper is pure. It does not generate reports, scan repos, read files,
    run git, run tests, call tools, call models, call APIs, write memory,
    persist packages, sign outputs, export files, or connect to runtime
    execution.
    """

    failures: list[ComplianceEvidenceValidationFailure] = []
    if not isinstance(request, Mapping):
        failure = ComplianceEvidenceValidationFailure(
            reason="missing_request",
            field="request",
            message="compliance evidence request must be a mapping",
        )
        return _decision(
            validation_status="failed_validation",
            package_id=None,
            project_ref=None,
            evidence_scope=(),
            failures=(failure,),
        )

    package_id = _text(request.get("package_id")) or None
    project_ref = _text(request.get("project_ref")) or None
    evidence_scope = _strings(request.get("evidence_scope"))

    if not package_id and not project_ref:
        _add_failure(
            failures,
            "package_or_project_identity_required",
            "package_id",
            "package_id or project_ref is required",
        )
    for field_name in ("tenant_scope", "project_scope", "namespace"):
        if not _text(request.get(field_name)):
            _add_failure(
                failures,
                f"{field_name}_required",
                field_name,
                f"{field_name} is required for compliance evidence review",
            )
    if not evidence_scope:
        _add_failure(
            failures,
            "evidence_scope_required",
            "evidence_scope",
            "at least one evidence scope is required",
        )

    _validate_evidence_scopes(evidence_scope, failures)
    _validate_non_authority_fields(request, failures)
    _validate_forbidden_requests(request, evidence_scope, failures)
    _validate_source_refs(request, failures)
    framework_refs = _framework_refs(request.get("framework_refs"))
    control_refs = _validate_control_refs(request.get("control_refs"), failures)
    candidates = _validate_candidates(request.get("candidates"), failures)
    limitations = _limitations(request.get("limitation_notes") or request.get("limitations"))
    _validate_claims(request, failures)
    _validate_repo_audit_relationship(repo_audit_decision, failures)
    _validate_developer_work_passport_relationship(developer_work_passport_decision, failures)
    _validate_vertical_pack_relationship(vertical_pack_decision, failures)

    compliance_input = None
    if (
        _text(request.get("tenant_scope"))
        and _text(request.get("project_scope"))
        and _text(request.get("namespace"))
    ):
        compliance_input = ComplianceEvidenceInput(
            package_id=package_id,
            project_ref=project_ref,
            tenant_scope=_text(request.get("tenant_scope")),
            project_scope=_text(request.get("project_scope")),
            namespace=_text(request.get("namespace")),
            audit_context_ref=_text(request.get("audit_context_ref")) or None,
            source_refs=_source_refs(request.get("source_refs")),
            policy_refs=_strings(request.get("policy_refs")),
            evidence_refs=_strings(request.get("evidence_refs")),
            repo_audit_refs=_strings(request.get("repo_audit_refs")),
            developer_work_passport_refs=_strings(request.get("developer_work_passport_refs")),
            control_refs=tuple(control_refs),
            framework_refs=tuple(framework_refs),
            limitation_notes=_strings(request.get("limitation_notes")),
            unknowns=_strings(request.get("unknowns")),
            review_status=_text(request.get("review_status")) or None,
            evidence_scope=evidence_scope,
            data_sensitivity=_text(request.get("data_sensitivity")) or None,
            privacy_class=_text(request.get("privacy_class")) or None,
            generated_at=_text(request.get("generated_at")) or None,
        )

    package_contract = ComplianceEvidencePackageContract(
        package_id=package_id,
        project_ref=project_ref,
        tenant_scope=_text(request.get("tenant_scope")) or None,
        namespace=_text(request.get("namespace")) or None,
        evidence_scope=evidence_scope,
        candidates=tuple(candidates),
        control_refs=tuple(control_refs),
        limitations=tuple(limitations),
        unknowns=_strings(request.get("unknowns")),
        source_refs=_ref_ids(request.get("source_refs")),
        policy_refs=_strings(request.get("policy_refs")),
        evidence_refs=_strings(request.get("evidence_refs")),
        generated_by=_text(request.get("generated_by")) or None,
    )

    validation_status = "review_ready"
    if any(
        failure.reason
        in {
            "missing_request",
            "package_or_project_identity_required",
            "tenant_scope_required",
            "project_scope_required",
            "namespace_required",
            "evidence_scope_required",
            "source_refs_required",
        }
        for failure in failures
    ):
        validation_status = "failed_validation"
    elif failures:
        validation_status = "blocked"

    return _decision(
        validation_status=validation_status,
        package_id=package_id,
        project_ref=project_ref,
        evidence_scope=evidence_scope,
        failures=tuple(failures),
        compliance_input=compliance_input,
        package_contract=package_contract,
    )


def _validate_evidence_scopes(
    evidence_scope: tuple[str, ...],
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    for scope in evidence_scope:
        if scope in FORBIDDEN_EVIDENCE_SCOPES:
            _add_failure(
                failures,
                "write_execute_or_certification_scope_denied",
                "evidence_scope",
                f"{scope} is outside the Compliance Evidence Pack readiness contract",
            )
        elif scope not in ALLOWED_EVIDENCE_SCOPES:
            _add_failure(failures, "unknown_evidence_scope", "evidence_scope", scope)


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    forbidden_truthy = {
        "authority": "authority_must_be_false",
        "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
        "approval_grant": "approval_grant_not_allowed",
        "capability_grant": "capability_grant_not_allowed",
        "lease_grant": "lease_grant_not_allowed",
        "evidence_provided_by_package": "package_cannot_provide_evidence",
        "evidence_provided_by_pack_output": "package_cannot_provide_evidence",
        "verifier_success": "package_cannot_mark_verifier_success",
        "verified_success": "package_cannot_mark_verifier_success",
        "controls_verified": "proof_control_effective_claim_denied",
        "compliance_verified": "proof_of_compliance_claim_denied",
        "success": "success_claim_denied",
    }
    for field_name, reason in forbidden_truthy.items():
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
        COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_compliance_pack_required",
            "execution_permission",
            "Compliance Evidence Pack cannot grant execution permission",
        )


def _validate_forbidden_requests(
    request: Mapping[str, Any],
    evidence_scope: tuple[str, ...],
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    for field_name, reason in FORBIDDEN_REQUEST_FLAGS.items():
        if request.get(field_name) is True or _text(request.get(field_name)):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside the Compliance Evidence Pack readiness contract",
            )
    forbidden_tools = {
        "git",
        "git_commit",
        "git_push",
        "pytest",
        "run_tests",
        "read_file",
        "write_file",
        "create_file",
        "edit_file",
        "subprocess",
        "model_call",
        "mcp_tool_call",
        "external_api",
        "browser",
    }
    if forbidden_tools & set(_strings(request.get("requested_tools"))):
        _add_failure(
            failures,
            "requested_tool_execution_denied",
            "requested_tools",
            "Compliance Evidence Pack readiness does not request tools",
        )
    if "human_review_queue_candidate" in evidence_scope and request.get("auto_approve") is True:
        _add_failure(
            failures,
            "human_review_cannot_be_auto_approved",
            "auto_approve",
            "human-review queue candidates cannot create approval",
        )


def _validate_source_refs(
    request: Mapping[str, Any],
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    refs = _source_refs(request.get("source_refs"))
    if not refs:
        _add_failure(
            failures,
            "source_refs_required",
            "source_refs",
            "Compliance Evidence Pack requires caller-supplied source refs",
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


def _validate_control_refs(
    raw_controls: Any,
    failures: list[ComplianceEvidenceValidationFailure],
) -> list[ComplianceControlRef]:
    controls: list[ComplianceControlRef] = []
    for index, raw_control in enumerate(_items(raw_controls)):
        if not isinstance(raw_control, Mapping):
            _add_failure(
                failures,
                "control_ref_mapping_required",
                f"control_refs[{index}]",
                "control refs must be mappings",
            )
            continue
        mapping_status = _text(raw_control.get("mapping_status")) or "candidate"
        framework_name = _text(raw_control.get("framework_name"))
        source_refs = _strings(raw_control.get("source_refs"))
        evidence_refs = _strings(raw_control.get("evidence_refs"))
        uncertainty = _text(raw_control.get("uncertainty")) or None

        if mapping_status not in ALLOWED_MAPPING_STATUSES:
            _add_failure(
                failures,
                "unknown_control_mapping_status",
                f"control_refs[{index}].mapping_status",
                mapping_status,
            )
        if not _text(raw_control.get("control_id")):
            _add_failure(
                failures,
                "control_id_required",
                f"control_refs[{index}].control_id",
                "control refs require control_id",
            )
        if not framework_name:
            _add_failure(
                failures,
                "framework_name_required",
                f"control_refs[{index}].framework_name",
                "control refs require framework_name",
            )
        if framework_name.lower() == "unknown" and mapping_status not in {"uncertain", "blocked"}:
            _add_failure(
                failures,
                "unknown_framework_requires_uncertain_or_blocked_mapping",
                f"control_refs[{index}].framework_name",
                "unknown frameworks must remain uncertain or blocked",
            )
        if mapping_status == "mapped_with_refs" and not (source_refs or evidence_refs):
            _add_failure(
                failures,
                "mapped_control_requires_refs",
                f"control_refs[{index}].source_refs",
                "mapped controls require source or evidence refs",
            )
        if mapping_status in {"candidate", "missing_refs"} and not uncertainty:
            _add_failure(
                failures,
                "candidate_or_missing_control_requires_uncertainty",
                f"control_refs[{index}].uncertainty",
                "candidate or missing-ref control mappings must preserve uncertainty",
            )
        controls.append(
            ComplianceControlRef(
                control_id=_text(raw_control.get("control_id")) or f"control-{index + 1}",
                framework_name=framework_name or "unknown",
                framework_version=_text(raw_control.get("framework_version")) or None,
                mapping_status=mapping_status,
                source_refs=source_refs,
                evidence_refs=evidence_refs,
                confidence=_text(raw_control.get("confidence")) or None,
                uncertainty=uncertainty,
                human_review_required=raw_control.get("human_review_required") is not False,
            )
        )
    return controls


def _validate_candidates(
    raw_candidates: Any,
    failures: list[ComplianceEvidenceValidationFailure],
) -> list[ComplianceEvidenceCandidate]:
    candidates: list[ComplianceEvidenceCandidate] = []
    for index, raw_candidate in enumerate(_items(raw_candidates)):
        if not isinstance(raw_candidate, Mapping):
            _add_failure(
                failures,
                "candidate_mapping_required",
                f"candidates[{index}]",
                "evidence candidates must be mappings",
            )
            continue
        category = _text(raw_candidate.get("category")) or "unknown_note"
        if category not in ALLOWED_CANDIDATE_CATEGORIES:
            _add_failure(
                failures,
                "unknown_candidate_category",
                f"candidates[{index}].category",
                category,
            )
        source_refs = _strings(raw_candidate.get("source_refs"))
        evidence_refs = _strings(raw_candidate.get("evidence_refs"))
        policy_refs = _strings(raw_candidate.get("policy_refs"))
        repo_audit_refs = _strings(raw_candidate.get("repo_audit_refs"))
        passport_refs = _strings(raw_candidate.get("developer_work_passport_refs"))
        uncertainty = _text(raw_candidate.get("uncertainty")) or None
        blocked = raw_candidate.get("blocked_by_missing_source") is True
        has_refs = bool(source_refs or evidence_refs or policy_refs or repo_audit_refs or passport_refs)
        if not has_refs and not uncertainty and not blocked:
            _add_failure(
                failures,
                "candidate_without_refs_requires_uncertainty_or_blocked",
                f"candidates[{index}].source_refs",
                "candidate claims without refs must be uncertain or blocked",
            )
        candidates.append(
            ComplianceEvidenceCandidate(
                candidate_id=_text(raw_candidate.get("candidate_id"))
                or f"candidate-{index + 1}",
                category=category,
                summary=_text(raw_candidate.get("summary")) or "",
                source_refs=source_refs,
                evidence_refs=evidence_refs,
                policy_refs=policy_refs,
                repo_audit_refs=repo_audit_refs,
                developer_work_passport_refs=passport_refs,
                confidence=_text(raw_candidate.get("confidence")) or None,
                uncertainty=uncertainty,
                limitations=_strings(raw_candidate.get("limitations")),
                human_review_required=raw_candidate.get("human_review_required") is not False,
                blocked_by_missing_source=blocked,
                labels=_strings(raw_candidate.get("labels")),
            )
        )
    return candidates


def _validate_claims(
    request: Mapping[str, Any],
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    blocked_claims = {
        "legal certification": "legal_certification_claim_denied",
        "compliance certification": "compliance_certification_claim_denied",
        "security certification": "security_certification_claim_denied",
        "court-admissible": "court_admissible_claim_denied",
        "court admissible": "court_admissible_claim_denied",
        "official audit result": "official_audit_result_claim_denied",
        "proof of compliance": "proof_of_compliance_claim_denied",
        "controls are effective": "proof_control_effective_claim_denied",
        "control effectiveness": "proof_control_effective_claim_denied",
        "organization is safe": "proof_organization_safe_claim_denied",
        "liability shield": "liability_shield_claim_denied",
        "regulator-approved": "regulator_approved_claim_denied",
        "regulator approved": "regulator_approved_claim_denied",
    }
    for phrase, reason in blocked_claims.items():
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"Compliance Evidence Pack cannot claim {phrase}",
            )


def _validate_repo_audit_relationship(
    repo_audit_decision: Any | None,
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    if repo_audit_decision is None:
        return
    if _bool_field(repo_audit_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "repo_audit_runtime_dispatch_attempt_denied",
            "repo_audit_decision.runtime_dispatch_allowed",
            "repo audit candidate cannot grant dispatch to compliance evidence",
        )
    if _bool_field(repo_audit_decision, "evidence_provided_by_report"):
        _add_failure(
            failures,
            "repo_audit_evidence_claim_denied",
            "repo_audit_decision.evidence_provided_by_report",
            "repo audit output cannot become compliance evidence by itself",
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
            "repo audit input must remain review-ready candidate metadata",
        )


def _validate_developer_work_passport_relationship(
    developer_work_passport_decision: Any | None,
    failures: list[ComplianceEvidenceValidationFailure],
) -> None:
    if developer_work_passport_decision is None:
        return
    if _bool_field(developer_work_passport_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "developer_work_passport_runtime_dispatch_attempt_denied",
            "developer_work_passport_decision.runtime_dispatch_allowed",
            "passport candidate cannot grant dispatch to compliance evidence",
        )
    if _bool_field(developer_work_passport_decision, "evidence_provided_by_passport"):
        _add_failure(
            failures,
            "developer_work_passport_evidence_claim_denied",
            "developer_work_passport_decision.evidence_provided_by_passport",
            "passport output cannot become compliance evidence by itself",
        )
    if _bool_field(developer_work_passport_decision, "verifier_success"):
        _add_failure(
            failures,
            "developer_work_passport_verifier_success_claim_denied",
            "developer_work_passport_decision.verifier_success",
            "passport output cannot become verifier success",
        )
    if _field(developer_work_passport_decision, "validation_status") not in {"review_ready", ""}:
        _add_failure(
            failures,
            "developer_work_passport_decision_not_review_ready",
            "developer_work_passport_decision.validation_status",
            "passport input must remain review-ready candidate metadata",
        )


def _validate_vertical_pack_relationship(
    vertical_pack_decision: Any | None,
    failures: list[ComplianceEvidenceValidationFailure],
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
    if _field(vertical_pack_decision, "pack_category") != "compliance_evidence":
        _add_failure(
            failures,
            "vertical_pack_category_must_be_compliance_evidence",
            "vertical_pack_decision.pack_category",
            "Compliance Evidence Pack requires compliance_evidence vertical pack category",
        )
    if _field(vertical_pack_decision, "operating_profile") != "evidence_reporting":
        _add_failure(
            failures,
            "vertical_pack_profile_must_be_evidence_reporting",
            "vertical_pack_decision.operating_profile",
            "Compliance Evidence Pack requires evidence_reporting vertical pack profile",
        )
    if _field(vertical_pack_decision, "validation_status") != "review_ready":
        _add_failure(
            failures,
            "vertical_pack_decision_not_review_ready",
            "vertical_pack_decision.validation_status",
            "Compliance Evidence Pack requires a review-ready vertical pack decision",
        )
    if _tuple_field(vertical_pack_decision, "failure_reasons"):
        _add_failure(
            failures,
            "vertical_pack_decision_has_failures",
            "vertical_pack_decision.failure_reasons",
            "Compliance Evidence Pack requires a clean vertical pack decision",
        )


def _source_refs(value: Any) -> tuple[ComplianceEvidenceSourceRef, ...]:
    refs: list[ComplianceEvidenceSourceRef] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            ref_id = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
            if not ref_id:
                continue
            refs.append(
                ComplianceEvidenceSourceRef(
                    ref_id=ref_id,
                    ref_type=_text(item.get("ref_type")) or _text(item.get("type")),
                    description=_text(item.get("description")) or None,
                )
            )
        else:
            item_id = _text(item)
            if item_id:
                refs.append(ComplianceEvidenceSourceRef(ref_id=item_id, ref_type="unspecified"))
    return tuple(refs)


def _framework_refs(value: Any) -> tuple[ComplianceFrameworkRef, ...]:
    refs: list[ComplianceFrameworkRef] = []
    for item in _items(value):
        if not isinstance(item, Mapping):
            continue
        framework_name = _text(item.get("framework_name")) or _text(item.get("name"))
        if not framework_name:
            continue
        refs.append(
            ComplianceFrameworkRef(
                framework_name=framework_name,
                framework_version=_text(item.get("framework_version")) or None,
                source_refs=_strings(item.get("source_refs")),
                human_review_required=item.get("human_review_required") is not False,
            )
        )
    return tuple(refs)


def _limitations(value: Any) -> tuple[ComplianceLimitation, ...]:
    limitations: list[ComplianceLimitation] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            note = _text(item.get("note")) or _text(item.get("summary"))
            if note:
                limitations.append(
                    ComplianceLimitation(
                        note=note,
                        source_refs=_strings(item.get("source_refs")),
                        uncertainty=_text(item.get("uncertainty")) or None,
                    )
                )
        else:
            note = _text(item)
            if note:
                limitations.append(ComplianceLimitation(note=note))
    return tuple(limitations)


def _ref_ids(value: Any) -> tuple[str, ...]:
    return tuple(ref.ref_id for ref in _source_refs(value))


def _decision(
    *,
    validation_status: str,
    package_id: str | None,
    project_ref: str | None,
    evidence_scope: tuple[str, ...],
    failures: tuple[ComplianceEvidenceValidationFailure, ...],
    compliance_input: ComplianceEvidenceInput | None = None,
    package_contract: ComplianceEvidencePackageContract | None = None,
) -> ComplianceEvidenceDecision:
    return ComplianceEvidenceDecision(
        contract_version=COMPLIANCE_EVIDENCE_PACK_CONTRACT_VERSION,
        validation_status=validation_status,
        package_id=package_id,
        project_ref=project_ref,
        evidence_scope=evidence_scope,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        compliance_input=compliance_input,
        package_contract=package_contract,
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
    failures: list[ComplianceEvidenceValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(ComplianceEvidenceValidationFailure(reason=reason, field=field, message=message))
