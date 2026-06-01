from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from aegis.core.developer_work_passport import (
    DEVELOPER_WORK_PASSPORT_CONTRACT_VERSION,
    DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION,
    validate_developer_work_passport_request,
)
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
        "pack_id": "developer-work-passport",
        "pack_name": "Developer Work Passport",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["review caller supplied work transparency metadata"],
        "capability_categories": ["vertical_pack_read"],
        "risk_tiers": ["read_only"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": [],
        "memory_namespaces": ["project"],
        "external_api_scopes": [],
        "audit_requirements": ["source_refs", "staleness"],
        "namespace_scope": "developer_work_passport",
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
        "pack_id": "developer-work-passport.evidence",
        "pack_category": "developer_work_passport",
        "operating_profile": "evidence_reporting",
        "namespace": "developer_work_passport",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "required_capabilities": ["vertical_pack_read"],
        "required_tools": [],
        "tool_scopes": [],
        "required_model_roles": [],
        "model_provider_scopes": [],
        "required_memory_namespaces": [],
        "required_external_api_scopes": [],
        "required_eval_families": ["passport-transparency-negative"],
        "evidence_expectations": ["source_ref_traceability"],
        "verifier_expectations": ["human_review_required"],
        "policy_requirements": ["vertical_pack_read.read_only"],
        "approval_requirements": [],
        "lease_requirements": [],
        "data_sensitivity": "source_code",
        "privacy_class": "project_internal",
        "trust_positioning": "transparency_report",
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
        "branch_ref": "main",
        "source_refs": [
            {"ref_id": "commit:1f47f3d", "ref_type": "commit"},
            {"ref_id": "path:src/aegis", "ref_type": "path"},
        ],
        "file_refs": ["src/aegis/core/repo_audit_pack.py"],
        "test_refs": ["tests/test_core/test_repo_audit_pack.py"],
        "audit_scope": ["developer_work_passport_candidate"],
        "requested_checks": ["project_structure", "unknowns_and_limitations"],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
    }
    request.update(overrides)
    return validate_repo_audit_request(request)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "passport_id": "passport:aegis:1",
        "developer_ref": "developer:local",
        "project_ref": "project:aegis",
        "repo_ref": "WexyS/Aegis",
        "commit_refs": ["commit:1f47f3d"],
        "branch_ref": "main",
        "source_refs": [
            {"ref_id": "commit:1f47f3d", "ref_type": "commit"},
            {"ref_id": "repo-audit:candidate", "ref_type": "repo_audit"},
        ],
        "changed_file_refs": ["src/aegis/core/repo_audit_pack.py"],
        "test_refs": ["tests/test_core/test_repo_audit_pack.py"],
        "review_refs": ["review:operator"],
        "repo_audit_refs": ["repo-audit:candidate"],
        "policy_refs": ["policy:passport.read_only"],
        "evidence_refs": [],
        "llm_assistance_refs": ["llm-disclosure:operator-declared"],
        "tool_usage_refs": ["tool-usage:operator-declared"],
        "limitation_notes": ["caller supplied metadata only"],
        "unknowns": ["no hidden monitoring performed"],
        "disclosure_scope": ["work_summary"],
        "disclosure_categories": ["changed_files", "human_review_required"],
        "audience": "client_safe_review",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "developer_work_passport",
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "generated_at": "2026-06-01T00:00:00Z",
        "generated_by": "developer_work_passport_contract",
        "authority": False,
        "execution_permission": DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], *, vertical_pack_decision=None, repo_audit_decision=None):
    return validate_developer_work_passport_request(
        request,
        vertical_pack_decision=vertical_pack_decision or _vertical_pack_decision(),
        repo_audit_decision=repo_audit_decision,
    )


def test_valid_minimal_passport_request_validates_as_non_dispatchable() -> None:
    decision = _validate(_request())

    assert decision.contract_version == DEVELOPER_WORK_PASSPORT_CONTRACT_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == DEVELOPER_WORK_PASSPORT_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.not_surveillance is True
    assert decision.not_certification is True


def test_valid_work_summary_scope_validates() -> None:
    decision = _validate(_request(disclosure_scope=["work_summary"]))

    assert decision.validation_status == "review_ready"
    assert decision.disclosure_scope == ("work_summary",)
    assert decision.runtime_dispatch_allowed is False


def test_valid_repo_audit_summary_scope_with_repo_audit_decision_validates() -> None:
    decision = _validate(
        _request(
            disclosure_scope=["repo_audit_summary"],
            disclosure_categories=["repo_audit_candidate", "limitations"],
        ),
        repo_audit_decision=_repo_audit_decision(),
    )

    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False


def test_missing_developer_project_identity_denied() -> None:
    decision = _validate(_request(passport_id="", developer_ref="", project_ref=""))

    assert decision.validation_status == "failed_validation"
    assert "passport_or_developer_project_identity_required" in decision.failure_reasons


def test_missing_namespace_or_project_scope_denied() -> None:
    decision = _validate(_request(namespace="", project_scope=""))

    assert decision.validation_status == "failed_validation"
    assert "namespace_required" in decision.failure_reasons
    assert "project_scope_required" in decision.failure_reasons


def test_unknown_passport_scope_denied() -> None:
    decision = _validate(_request(disclosure_scope=["imaginary_scope"]))

    assert decision.validation_status == "blocked"
    assert "unknown_passport_scope" in decision.failure_reasons


def test_unknown_disclosure_category_denied() -> None:
    decision = _validate(_request(disclosure_categories=["imaginary_disclosure"]))

    assert decision.validation_status == "blocked"
    assert "unknown_disclosure_category" in decision.failure_reasons


def test_disclosure_without_source_refs_is_blocked_or_uncertain() -> None:
    blocked = _validate(
        _request(
            disclosures=[
                {
                    "disclosure_id": "disclosure-1",
                    "category": "changed_files",
                    "summary": "No source refs.",
                }
            ]
        )
    )
    uncertain = _validate(
        _request(
            disclosures=[
                {
                    "disclosure_id": "disclosure-1",
                    "category": "changed_files",
                    "summary": "No source refs.",
                    "uncertainty": "caller did not provide source refs for this disclosure",
                }
            ]
        )
    )

    assert "disclosure_without_source_requires_uncertainty" in blocked.failure_reasons
    assert uncertain.validation_status == "review_ready"
    assert uncertain.report_contract is not None
    assert uncertain.report_contract.disclosures[0].uncertainty


def test_external_sharing_request_denied() -> None:
    decision = _validate(_request(external_sharing=True))

    assert "external_sharing_denied" in decision.failure_reasons


def test_hidden_monitoring_or_surveillance_denied() -> None:
    decision = _validate(_request(hidden_monitoring=True, surveillance_mode=True))

    assert "hidden_monitoring_denied" in decision.failure_reasons
    assert "surveillance_denied" in decision.failure_reasons


def test_productivity_score_or_worker_monitoring_claim_denied() -> None:
    decision = _validate(_request(productivity_score=True, worker_monitoring=True))

    assert "productivity_score_denied" in decision.failure_reasons
    assert "worker_monitoring_denied" in decision.failure_reasons


def test_certification_claim_denied() -> None:
    decision = _validate(_request(developer_work_passport_certification=True))

    assert "certification_claim_denied" in decision.failure_reasons


def test_proof_of_quality_claim_denied() -> None:
    decision = _validate(_request(proof_of_quality=True))

    assert "proof_of_quality_denied" in decision.failure_reasons


def test_proof_tests_passed_without_test_refs_denied() -> None:
    decision = _validate(_request(test_refs=[], tests_passed=True))

    assert "test_success_claim_denied" in decision.failure_reasons


def test_compliance_legal_or_security_certification_claim_denied() -> None:
    decision = _validate(
        _request(
            disclosure_scope=["compliance_candidate_notes"],
            claims=[
                "compliance certification",
                "legal certification",
                "security certification",
            ],
        )
    )

    assert "certification_claim_denied" in decision.failure_reasons


def test_write_execute_git_test_file_model_tool_and_api_requests_denied() -> None:
    decision = _validate(
        _request(
            disclosure_scope=["write"],
            git_command="git status",
            execute_tests=True,
            write_files=True,
            model_review=True,
            requested_tools=["git"],
            external_api_request=True,
        )
    )

    assert "write_or_execute_scope_denied" in decision.failure_reasons
    assert "git_command_request_denied" in decision.failure_reasons
    assert "test_execution_request_denied" in decision.failure_reasons
    assert "file_mutation_request_denied" in decision.failure_reasons
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


def test_evidence_and_verifier_success_claims_rejected() -> None:
    decision = _validate(_request(evidence_provided_by_passport=True, verifier_success=True))

    assert decision.evidence_provided_by_passport is False
    assert decision.verifier_success is False
    assert "passport_cannot_provide_evidence" in decision.failure_reasons
    assert "passport_cannot_mark_verifier_success" in decision.failure_reasons


def test_repo_audit_decision_with_dispatch_true_rejected() -> None:
    repo_decision = replace(_repo_audit_decision(), runtime_dispatch_allowed=True)

    decision = _validate(_request(), repo_audit_decision=repo_decision)

    assert "repo_audit_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_repo_audit_decision_that_claims_evidence_or_verifier_success_rejected() -> None:
    repo_decision = replace(
        _repo_audit_decision(),
        evidence_provided_by_report=True,
        verifier_success=True,
    )

    decision = _validate(_request(), repo_audit_decision=repo_decision)

    assert "repo_audit_evidence_claim_denied" in decision.failure_reasons
    assert "repo_audit_verifier_success_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_vertical_pack_decision_not_developer_work_passport_rejected() -> None:
    vertical_decision = _vertical_pack_decision(pack_category="repo_audit")

    decision = _validate(_request(), vertical_pack_decision=vertical_decision)

    assert "vertical_pack_category_must_be_developer_work_passport" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_report_contract_remains_non_authoritative() -> None:
    decision = _validate(
        _request(
            report_id="passport-report-1",
            disclosures=[
                {
                    "disclosure_id": "disclosure-1",
                    "category": "changed_files",
                    "summary": "Caller supplied changed-file refs.",
                    "source_refs": ["path:src/aegis"],
                    "confidence": "medium",
                }
            ],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.report_contract is not None
    assert decision.report_contract.runtime_dispatch_allowed is False
    assert decision.report_contract.evidence_provided_by_passport is False
    assert decision.report_contract.verifier_success is False
    assert decision.report_contract.mutation_performed is False
    assert decision.report_contract.not_surveillance is True
    assert decision.report_contract.not_certification is True


def test_validation_does_not_mutate_input_or_supplied_decisions() -> None:
    request = _request(
        disclosures=[
            {
                "disclosure_id": "disclosure-1",
                "category": "unknowns",
                "summary": "Caller supplied uncertainty.",
                "uncertainty": "metadata only",
            }
        ]
    )
    before = deepcopy(request)
    vertical_decision = _vertical_pack_decision()
    repo_decision = _repo_audit_decision()

    decision = _validate(
        request,
        vertical_pack_decision=vertical_decision,
        repo_audit_decision=repo_decision,
    )

    assert request == before
    assert vertical_decision.runtime_dispatch_allowed is False
    assert repo_decision.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
