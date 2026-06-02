from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from aegis.core.compliance_evidence_pack import (
    COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION,
    COMPLIANCE_EVIDENCE_PACK_CONTRACT_VERSION,
    validate_compliance_evidence_request,
)
from aegis.core.developer_work_passport import validate_developer_work_passport_request
from aegis.core.plugin_lifecycle import evaluate_plugin_lifecycle_transition
from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import (
    calculate_manifest_checksum,
    evaluate_manifest_drift,
)
from aegis.core.repo_audit_pack import validate_repo_audit_request
from aegis.core.vertical_pack import (
    VERTICAL_PACK_EXECUTION_PERMISSION,
    validate_vertical_pack_descriptor,
)


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "compliance-evidence-pack",
        "pack_name": "Compliance Evidence Pack",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["review caller supplied compliance evidence metadata"],
        "capability_categories": ["vertical_pack_read"],
        "risk_tiers": ["read_only"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": [],
        "memory_namespaces": [],
        "external_api_scopes": [],
        "audit_requirements": ["source_refs", "human_review_required"],
        "namespace_scope": "compliance_evidence",
        "tenant_scope": "local",
        "training_data_policy": {"namespace_specific": True},
    }
    manifest.update(overrides)
    return manifest


def _vertical_pack_decision(**descriptor_overrides: object):
    manifest = _manifest()
    manifest_decision = validate_plugin_manifest(manifest)
    integrity_decision = evaluate_manifest_drift(
        manifest,
        reviewed_checksum=calculate_manifest_checksum(manifest),
        reviewed_version=str(manifest["pack_version"]),
        signature_status="signature_verified",
    )
    lifecycle_decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=manifest_decision,
        integrity_decision=integrity_decision,
    )
    descriptor: dict[str, object] = {
        "pack_id": "compliance.evidence.readiness",
        "pack_category": "compliance_evidence",
        "operating_profile": "evidence_reporting",
        "namespace": "compliance_evidence",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "required_capabilities": ["vertical_pack_read"],
        "required_tools": [],
        "tool_scopes": [],
        "required_model_roles": [],
        "model_provider_scopes": [],
        "required_memory_namespaces": [],
        "required_external_api_scopes": [],
        "required_eval_families": ["compliance-evidence-negative"],
        "evidence_expectations": ["source_ref_traceability"],
        "verifier_expectations": ["human_review_required"],
        "policy_requirements": ["vertical_pack_read.read_only"],
        "approval_requirements": [],
        "lease_requirements": [],
        "data_sensitivity": "source_code",
        "privacy_class": "project_internal",
        "trust_positioning": "forensic_readiness",
        "claims": ["audit-readiness support"],
        "authority": False,
        "execution_permission": VERTICAL_PACK_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    descriptor.update(descriptor_overrides)
    return validate_vertical_pack_descriptor(
        descriptor,
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
    )


def _repo_audit_decision(**overrides: object):
    request: dict[str, object] = {
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "commit_ref": "1f47f3d",
        "source_refs": [{"ref_id": "commit:1f47f3d", "ref_type": "commit"}],
        "audit_scope": ["compliance_evidence_candidate"],
        "requested_checks": ["policy_alignment_notes", "unknowns_and_limitations"],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
    }
    request.update(overrides)
    return validate_repo_audit_request(request)


def _passport_decision(**overrides: object):
    request: dict[str, object] = {
        "passport_id": "passport:aegis:1",
        "developer_ref": "developer:local",
        "project_ref": "project:aegis",
        "source_refs": [{"ref_id": "passport:source", "ref_type": "passport"}],
        "disclosure_scope": ["compliance_candidate_notes"],
        "disclosure_categories": ["human_review_required", "limitations"],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "developer_work_passport",
    }
    request.update(overrides)
    return validate_developer_work_passport_request(request)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "package_id": "compliance:evidence:aegis:1",
        "project_ref": "project:aegis",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "compliance_evidence",
        "audit_context_ref": "audit-context:foundation-v1",
        "source_refs": [
            {"ref_id": "doc:foundation-baseline", "ref_type": "doc"},
            {"ref_id": "repo-audit:candidate", "ref_type": "repo_audit"},
        ],
        "policy_refs": ["policy:post-foundation"],
        "evidence_refs": ["evidence:audit-summary"],
        "repo_audit_refs": ["repo-audit:candidate"],
        "developer_work_passport_refs": ["passport:candidate"],
        "framework_refs": [
            {
                "framework_name": "SOC2-candidate",
                "framework_version": "unofficial",
                "source_refs": ["doc:framework-note"],
            }
        ],
        "control_refs": [
            {
                "control_id": "CC-candidate-1",
                "framework_name": "SOC2-candidate",
                "framework_version": "unofficial",
                "mapping_status": "candidate",
                "source_refs": ["doc:foundation-baseline"],
                "evidence_refs": ["evidence:audit-summary"],
                "uncertainty": "candidate mapping only",
                "human_review_required": True,
            }
        ],
        "candidates": [
            {
                "candidate_id": "candidate-1",
                "category": "evidence_reference",
                "summary": "Caller supplied evidence ref for human review.",
                "source_refs": ["doc:foundation-baseline"],
                "evidence_refs": ["evidence:audit-summary"],
                "confidence": "medium",
                "uncertainty": "audit-readiness metadata only",
            }
        ],
        "limitation_notes": ["not certification"],
        "unknowns": ["control effectiveness not verified"],
        "review_status": "human_review_required",
        "evidence_scope": ["forensic_readiness_notes"],
        "data_sensitivity": "source_code",
        "privacy_class": "project_internal",
        "generated_at": "2026-06-03T00:00:00Z",
        "generated_by": "compliance_evidence_pack_contract",
        "authority": False,
        "execution_permission": COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _validate(
    request: dict[str, object],
    *,
    vertical_pack_decision=None,
    repo_audit_decision=None,
    developer_work_passport_decision=None,
):
    return validate_compliance_evidence_request(
        request,
        vertical_pack_decision=vertical_pack_decision or _vertical_pack_decision(),
        repo_audit_decision=repo_audit_decision,
        developer_work_passport_decision=developer_work_passport_decision,
    )


def test_valid_minimal_compliance_evidence_request_validates_as_non_dispatchable() -> None:
    decision = _validate(_request())

    assert decision.contract_version == COMPLIANCE_EVIDENCE_PACK_CONTRACT_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == COMPLIANCE_EVIDENCE_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.not_certification is True
    assert decision.not_legal_advice is True
    assert decision.not_court_admissible_claim is True


def test_valid_forensic_readiness_scope_validates_without_certification() -> None:
    decision = _validate(_request(evidence_scope=["forensic_readiness_notes"]))

    assert decision.validation_status == "review_ready"
    assert decision.evidence_scope == ("forensic_readiness_notes",)
    assert decision.package_contract is not None
    assert decision.package_contract.not_certification is True
    assert decision.package_contract.not_court_admissible_claim is True


def test_valid_control_mapping_candidate_preserves_uncertainty() -> None:
    decision = _validate(
        _request(
            evidence_scope=["control_mapping_candidate"],
            control_refs=[
                {
                    "control_id": "AC-1",
                    "framework_name": "SOC2-candidate",
                    "mapping_status": "uncertain",
                    "source_refs": [],
                    "evidence_refs": [],
                    "uncertainty": "no control owner review yet",
                }
            ],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.package_contract is not None
    assert decision.package_contract.control_refs[0].mapping_status == "uncertain"
    assert decision.package_contract.control_refs[0].human_review_required is True


def test_missing_package_project_identity_denied() -> None:
    decision = _validate(_request(package_id="", project_ref=""))

    assert decision.validation_status == "failed_validation"
    assert "package_or_project_identity_required" in decision.failure_reasons


def test_missing_tenant_project_namespace_scope_denied() -> None:
    decision = _validate(_request(tenant_scope="", project_scope="", namespace=""))

    assert decision.validation_status == "failed_validation"
    assert "tenant_scope_required" in decision.failure_reasons
    assert "project_scope_required" in decision.failure_reasons
    assert "namespace_required" in decision.failure_reasons


def test_unknown_evidence_scope_denied() -> None:
    decision = _validate(_request(evidence_scope=["imaginary_scope"]))

    assert decision.validation_status == "blocked"
    assert "unknown_evidence_scope" in decision.failure_reasons


def test_source_less_candidate_claim_blocked_or_uncertain() -> None:
    blocked = _validate(
        _request(
            candidates=[
                {
                    "candidate_id": "candidate-1",
                    "category": "risk_note",
                    "summary": "No refs and no uncertainty.",
                }
            ]
        )
    )
    uncertain = _validate(
        _request(
            candidates=[
                {
                    "candidate_id": "candidate-1",
                    "category": "risk_note",
                    "summary": "No refs but explicitly uncertain.",
                    "uncertainty": "source refs not supplied",
                }
            ]
        )
    )

    assert "candidate_without_refs_requires_uncertainty_or_blocked" in blocked.failure_reasons
    assert uncertain.validation_status == "review_ready"
    assert uncertain.package_contract is not None
    assert uncertain.package_contract.candidates[0].uncertainty


def test_legal_compliance_security_and_court_claims_denied() -> None:
    decision = _validate(
        _request(
            claims=[
                "legal certification",
                "compliance certification",
                "security certification",
                "court-admissible evidence",
            ]
        )
    )

    assert "legal_certification_claim_denied" in decision.failure_reasons
    assert "compliance_certification_claim_denied" in decision.failure_reasons
    assert "security_certification_claim_denied" in decision.failure_reasons
    assert "court_admissible_claim_denied" in decision.failure_reasons


def test_proof_and_official_audit_claims_denied() -> None:
    decision = _validate(
        _request(
            claims=[
                "official audit result",
                "proof of compliance",
                "controls are effective",
                "organization is safe",
            ]
        )
    )

    assert "official_audit_result_claim_denied" in decision.failure_reasons
    assert "proof_of_compliance_claim_denied" in decision.failure_reasons
    assert "proof_control_effective_claim_denied" in decision.failure_reasons
    assert "proof_organization_safe_claim_denied" in decision.failure_reasons


def test_external_sharing_export_and_signing_requests_denied() -> None:
    decision = _validate(_request(external_sharing=True, export_report=True, sign_report=True))

    assert "external_sharing_denied" in decision.failure_reasons
    assert "external_export_denied" in decision.failure_reasons
    assert "report_signing_denied" in decision.failure_reasons


def test_write_execute_git_test_file_model_tool_and_api_requests_denied() -> None:
    decision = _validate(
        _request(
            evidence_scope=["write"],
            git_command="git status",
            execute_tests=True,
            write_files=True,
            repo_scanning=True,
            read_repo_files=True,
            model_review=True,
            requested_tools=["git", "read_file"],
            external_api_request=True,
        )
    )

    assert "write_execute_or_certification_scope_denied" in decision.failure_reasons
    assert "git_command_request_denied" in decision.failure_reasons
    assert "test_execution_request_denied" in decision.failure_reasons
    assert "file_mutation_request_denied" in decision.failure_reasons
    assert "repo_scanning_request_denied" in decision.failure_reasons
    assert "repo_file_read_request_denied" in decision.failure_reasons
    assert "model_review_request_denied" in decision.failure_reasons
    assert "requested_tool_execution_denied" in decision.failure_reasons
    assert "api_request_denied" in decision.failure_reasons


def test_authority_runtime_dispatch_and_grants_rejected() -> None:
    decision = _validate(
        _request(
            authority=True,
            runtime_dispatch_allowed=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
        )
    )

    assert "authority_must_be_false" in decision.failure_reasons
    assert "runtime_dispatch_not_allowed" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_evidence_verifier_and_success_claims_rejected() -> None:
    decision = _validate(
        _request(
            evidence_provided_by_package=True,
            verifier_success=True,
            verified_success=True,
            success=True,
        )
    )

    assert decision.evidence_provided_by_package is False
    assert decision.verifier_success is False
    assert "package_cannot_provide_evidence" in decision.failure_reasons
    assert "package_cannot_mark_verifier_success" in decision.failure_reasons
    assert "success_claim_denied" in decision.failure_reasons


def test_repo_audit_decision_with_dispatch_evidence_or_verifier_success_rejected() -> None:
    repo_decision = replace(
        _repo_audit_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_report=True,
        verifier_success=True,
    )

    decision = _validate(_request(), repo_audit_decision=repo_decision)

    assert "repo_audit_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "repo_audit_evidence_claim_denied" in decision.failure_reasons
    assert "repo_audit_verifier_success_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_developer_work_passport_decision_with_dispatch_evidence_or_verifier_success_rejected() -> None:
    passport_decision = replace(
        _passport_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_passport=True,
        verifier_success=True,
    )

    decision = _validate(_request(), developer_work_passport_decision=passport_decision)

    assert "developer_work_passport_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "developer_work_passport_evidence_claim_denied" in decision.failure_reasons
    assert "developer_work_passport_verifier_success_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_vertical_pack_decision_not_compliance_evidence_rejected() -> None:
    vertical_decision = _vertical_pack_decision(pack_category="repo_audit")

    decision = _validate(_request(), vertical_pack_decision=vertical_decision)

    assert "vertical_pack_category_must_be_compliance_evidence" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_package_contract_remains_non_authoritative() -> None:
    decision = _validate(_request())

    assert decision.package_contract is not None
    assert decision.package_contract.runtime_dispatch_allowed is False
    assert decision.package_contract.evidence_provided_by_package is False
    assert decision.package_contract.verifier_success is False
    assert decision.package_contract.mutation_performed is False
    assert decision.package_contract.requires_human_review is True
    assert decision.package_contract.not_certification is True
    assert decision.package_contract.not_legal_advice is True
    assert decision.package_contract.not_court_admissible_claim is True


def test_validation_does_not_mutate_input_or_supplied_decisions() -> None:
    request = _request()
    before = deepcopy(request)
    vertical_decision = _vertical_pack_decision()
    repo_decision = _repo_audit_decision()
    passport_decision = _passport_decision()

    decision = _validate(
        request,
        vertical_pack_decision=vertical_decision,
        repo_audit_decision=repo_decision,
        developer_work_passport_decision=passport_decision,
    )

    assert request == before
    assert vertical_decision.runtime_dispatch_allowed is False
    assert repo_decision.runtime_dispatch_allowed is False
    assert passport_decision.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
