from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from aegis.core.plugin_lifecycle import evaluate_plugin_lifecycle_transition
from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import (
    calculate_manifest_checksum,
    evaluate_manifest_drift,
)
from aegis.core.repo_audit_pack import (
    REPO_AUDIT_EXECUTION_PERMISSION,
    REPO_AUDIT_PACK_CONTRACT_VERSION,
    validate_repo_audit_request,
)
from aegis.core.vertical_pack import (
    VERTICAL_PACK_EXECUTION_PERMISSION,
    validate_vertical_pack_descriptor,
)


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "repo-audit-readonly",
        "pack_name": "Repo Audit Read-only Pack",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["review caller supplied repo metadata"],
        "capability_categories": ["local_tool_read"],
        "risk_tiers": ["local_state_read"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": ["read_file", "search_files"],
        "memory_namespaces": ["project"],
        "external_api_scopes": [],
        "audit_requirements": ["source_refs", "staleness"],
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
        "pack_id": "repo-audit.readonly",
        "pack_category": "repo_audit",
        "operating_profile": "read_only",
        "namespace": "repo_audit",
        "project_scope": "aegis",
        "required_capabilities": ["local_tool_read", "repo_read"],
        "required_tools": ["read_file", "search_files"],
        "tool_scopes": ["workspace_read"],
        "required_model_roles": [],
        "model_provider_scopes": [],
        "required_memory_namespaces": [],
        "required_external_api_scopes": [],
        "required_eval_families": ["repo-audit-read-only-negative"],
        "evidence_expectations": [],
        "verifier_expectations": [],
        "policy_requirements": ["vertical_pack_read.read_only"],
        "approval_requirements": [],
        "lease_requirements": [],
        "data_sensitivity": "source_code",
        "privacy_class": "project_internal",
        "provenance_requirements": ["source_ref", "commit_ref", "path_ref"],
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


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "commit_ref": "c9dbb62",
        "branch_ref": "main",
        "source_refs": [
            {"ref_id": "commit:c9dbb62", "ref_type": "commit"},
            {"ref_id": "path:src/aegis", "ref_type": "path"},
        ],
        "file_refs": ["src/aegis/core/repo_audit_pack.py"],
        "test_refs": ["tests/test_core/test_repo_audit_pack.py"],
        "dependency_refs": [],
        "config_refs": [],
        "docs_refs": ["docs/repo-audit-pack-read-only-contract-v1.md"],
        "audit_scope": ["architecture_summary"],
        "requested_checks": ["project_structure", "unknowns_and_limitations"],
        "excluded_paths": [],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "generated_at": "2026-06-01T00:00:00Z",
        "generated_by": "repo_audit_pack_contract",
        "authority": False,
        "execution_permission": REPO_AUDIT_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], *, vertical_pack_decision=None):
    return validate_repo_audit_request(
        request,
        vertical_pack_decision=vertical_pack_decision or _vertical_pack_decision(),
    )


def test_valid_minimal_repo_audit_request_validates_as_non_dispatchable() -> None:
    decision = _validate(_request())

    assert decision.contract_version == REPO_AUDIT_PACK_CONTRACT_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.repo_id == "WexyS/Aegis"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == REPO_AUDIT_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False


def test_valid_architecture_summary_scope_validates() -> None:
    decision = _validate(_request(audit_scope=["architecture_summary"]))

    assert decision.validation_status == "review_ready"
    assert decision.audit_scope == ("architecture_summary",)
    assert decision.runtime_dispatch_allowed is False


def test_valid_requested_checks_validate() -> None:
    decision = _validate(
        _request(
            requested_checks=[
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
            ]
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False


def test_missing_repo_identity_denied() -> None:
    decision = _validate(_request(repo_id="", repo_name=""))

    assert decision.validation_status == "failed_validation"
    assert "repo_identity_required" in decision.failure_reasons


def test_missing_commit_ref_requires_unknown_marker_or_is_denied() -> None:
    denied = _validate(_request(commit_ref=""))
    unknown = _validate(_request(commit_ref="", commit_ref_unknown=True))

    assert "commit_ref_or_unknown_marker_required" in denied.failure_reasons
    assert unknown.validation_status == "review_ready"
    assert unknown.runtime_dispatch_allowed is False


def test_missing_namespace_or_project_scope_denied() -> None:
    decision = _validate(_request(namespace="", project_scope=""))

    assert decision.validation_status == "failed_validation"
    assert "namespace_required" in decision.failure_reasons
    assert "project_scope_required" in decision.failure_reasons


def test_unknown_audit_scope_denied() -> None:
    decision = _validate(_request(audit_scope=["imaginary_scope"]))

    assert decision.validation_status == "blocked"
    assert "unknown_audit_scope" in decision.failure_reasons


def test_unknown_requested_check_denied() -> None:
    decision = _validate(_request(requested_checks=["imaginary_check"]))

    assert decision.validation_status == "blocked"
    assert "unknown_requested_check" in decision.failure_reasons


def test_write_scope_denied() -> None:
    decision = _validate(_request(audit_scope=["write_files"]))

    assert "write_or_execute_scope_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_git_command_request_denied() -> None:
    decision = _validate(_request(git_command="git status"))

    assert "git_command_request_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_test_execution_request_denied() -> None:
    decision = _validate(_request(execute_tests=True))

    assert "test_execution_request_denied" in decision.failure_reasons


def test_file_mutation_request_denied() -> None:
    decision = _validate(_request(write_files=True))

    assert "file_mutation_request_denied" in decision.failure_reasons


def test_model_review_request_denied() -> None:
    decision = _validate(_request(model_review=True))

    assert "model_review_request_denied" in decision.failure_reasons


def test_external_api_request_denied() -> None:
    decision = _validate(_request(external_api_request=True))

    assert "external_api_request_denied" in decision.failure_reasons


def test_tool_request_denied() -> None:
    decision = _validate(_request(requested_tools=["git"]))

    assert "requested_tool_execution_denied" in decision.failure_reasons


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
    decision = _validate(_request(evidence_provided_by_report=True, verifier_success=True))

    assert decision.evidence_provided_by_report is False
    assert decision.verifier_success is False
    assert "report_cannot_provide_evidence" in decision.failure_reasons
    assert "report_cannot_mark_verifier_success" in decision.failure_reasons


def test_developer_work_passport_final_certification_claim_rejected() -> None:
    decision = _validate(
        _request(
            audit_scope=["developer_work_passport_candidate"],
            final_passport=True,
        )
    )

    assert "developer_work_passport_certification_denied" in decision.failure_reasons


def test_compliance_legal_or_security_certification_claim_rejected() -> None:
    decision = _validate(
        _request(
            audit_scope=["compliance_evidence_candidate"],
            claims=[
                "compliance certification",
                "legal certification",
                "security certification",
            ],
        )
    )

    assert "certification_claim_denied" in decision.failure_reasons


def test_findings_without_source_refs_are_blocked_or_marked_uncertain() -> None:
    blocked = _validate(
        _request(
            findings=[
                {
                    "finding_id": "finding-1",
                    "severity": "medium",
                    "category": "risk",
                    "title": "Missing source",
                    "summary": "No source refs.",
                }
            ]
        )
    )
    uncertain = _validate(
        _request(
            findings=[
                {
                    "finding_id": "finding-1",
                    "severity": "medium",
                    "category": "risk",
                    "title": "Missing source",
                    "summary": "No source refs.",
                    "uncertainty": "caller did not provide source refs for this claim",
                }
            ]
        )
    )

    assert "finding_without_source_requires_uncertainty" in blocked.failure_reasons
    assert uncertain.validation_status == "review_ready"
    assert uncertain.report_contract is not None
    assert uncertain.report_contract.findings[0].uncertainty


def test_report_contract_remains_non_authoritative() -> None:
    decision = _validate(
        _request(
            report_id="repo-audit-report-1",
            findings=[
                {
                    "finding_id": "finding-1",
                    "severity": "info",
                    "category": "architecture",
                    "title": "Source-backed note",
                    "summary": "Caller supplied source ref.",
                    "source_refs": ["path:src/aegis"],
                    "confidence": "medium",
                }
            ],
            limitations=["caller supplied metadata only"],
            unknowns=["no repo scan performed"],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.report_contract is not None
    assert decision.report_contract.runtime_dispatch_allowed is False
    assert decision.report_contract.evidence_provided_by_report is False
    assert decision.report_contract.verifier_success is False
    assert decision.report_contract.mutation_performed is False
    assert decision.report_contract.requires_human_review is True


def test_vertical_pack_decision_with_dispatch_true_rejected() -> None:
    vertical_decision = replace(_vertical_pack_decision(), runtime_dispatch_allowed=True)

    decision = _validate(_request(), vertical_pack_decision=vertical_decision)

    assert "vertical_pack_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_vertical_pack_decision_not_repo_audit_rejected() -> None:
    vertical_decision = _vertical_pack_decision(pack_category="document_analysis")

    decision = _validate(_request(), vertical_pack_decision=vertical_decision)

    assert "vertical_pack_category_must_be_repo_audit" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_validation_does_not_mutate_input() -> None:
    request = _request(
        findings=[
            {
                "finding_id": "finding-1",
                "severity": "unknown",
                "category": "unknown",
                "title": "Uncertain",
                "summary": "Caller provided uncertainty.",
                "uncertainty": "metadata only",
            }
        ]
    )
    before = deepcopy(request)
    vertical_decision = _vertical_pack_decision()

    decision = _validate(request, vertical_pack_decision=vertical_decision)

    assert request == before
    assert vertical_decision.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
