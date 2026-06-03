from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

from aegis.core.compliance_evidence_pack import validate_compliance_evidence_request
from aegis.core.developer_work_passport import validate_developer_work_passport_request
from aegis.core.mission_control import build_mission_control_preview
from aegis.core.plugin_lifecycle import evaluate_plugin_lifecycle_transition
from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import calculate_manifest_checksum, evaluate_manifest_drift
from aegis.core.plugin_review_store import validate_plugin_review_record
from aegis.core.repo_audit_implementation_readiness import (
    REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION,
    REPO_AUDIT_IMPLEMENTATION_READINESS_VERSION,
    validate_repo_audit_implementation_readiness,
)
from aegis.core.repo_audit_pack import validate_repo_audit_request
from aegis.core.tool_simulation import build_tool_simulation
from aegis.core.vertical_pack import VERTICAL_PACK_EXECUTION_PERMISSION, validate_vertical_pack_descriptor


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "repo-audit-implementation-readiness",
        "pack_name": "Repo Audit Implementation Readiness",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["review caller supplied repo audit implementation readiness metadata"],
        "capability_categories": ["vertical_pack_read"],
        "risk_tiers": ["read_only"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": [],
        "memory_namespaces": [],
        "external_api_scopes": [],
        "namespace_scope": "repo_audit",
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
        "pack_id": "repo-audit.implementation-readiness",
        "pack_category": "repo_audit",
        "operating_profile": "read_only",
        "namespace": "repo_audit",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "required_capabilities": ["vertical_pack_read", "repo_read"],
        "required_tools": [],
        "tool_scopes": ["workspace_read"],
        "required_model_roles": [],
        "model_provider_scopes": [],
        "required_memory_namespaces": [],
        "required_external_api_scopes": [],
        "required_eval_families": ["repo-audit-implementation-readiness-negative"],
        "evidence_expectations": ["source_ref_traceability"],
        "verifier_expectations": ["human_review_required"],
        "policy_requirements": ["vertical_pack_read.read_only"],
        "approval_requirements": [],
        "lease_requirements": [],
        "data_sensitivity": "source_code",
        "privacy_class": "project_internal",
        "provenance_requirements": ["source_ref", "commit_ref", "path_ref"],
        "trust_positioning": "readiness_metadata",
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
        "commit_ref": "29b3eba",
        "branch_ref": "main",
        "source_refs": [{"ref_id": "commit:29b3eba", "ref_type": "commit"}],
        "audit_scope": ["architecture_summary"],
        "requested_checks": ["project_structure", "unknowns_and_limitations"],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
    }
    request.update(overrides)
    return validate_repo_audit_request(request)


def _passport_decision(**overrides: object):
    request: dict[str, object] = {
        "passport_id": "passport:aegis:repo-audit-implementation-readiness",
        "developer_ref": "developer:local",
        "project_ref": "project:aegis",
        "source_refs": [{"ref_id": "repo-audit-implementation-readiness", "ref_type": "source_ref"}],
        "disclosure_scope": ["repo_audit_summary"],
        "disclosure_categories": ["repo_audit_candidate", "human_review_required"],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "developer_work_passport",
    }
    request.update(overrides)
    return validate_developer_work_passport_request(request)


def _compliance_decision(**overrides: object):
    request: dict[str, object] = {
        "package_id": "compliance:aegis:repo-audit-implementation-readiness",
        "project_ref": "project:aegis",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "compliance_evidence",
        "source_refs": [{"ref_id": "repo-audit-implementation-readiness", "ref_type": "source_ref"}],
        "evidence_scope": ["audit_readiness_notes"],
        "candidates": [
            {
                "candidate_id": "candidate-1",
                "category": "repo_audit_reference",
                "summary": "Readiness metadata only.",
                "repo_audit_refs": ["repo-audit:implementation-readiness"],
                "uncertainty": "candidate only",
            }
        ],
    }
    request.update(overrides)
    return validate_compliance_evidence_request(request)


def _mission_control_decision(**overrides: object):
    request: dict[str, object] = {
        "request_id": "req-repo-audit-readiness",
        "command_id": "cmd-repo-audit-readiness",
        "raw_user_request": "review repo audit implementation readiness",
        "normalized_intent": "readiness_review",
        "route_kind": "contract",
        "proposed_action": "validate metadata only",
        "proposed_tool": "",
        "affected_resources": ["repo-audit-implementation-readiness"],
        "risk_tier": "read_only",
        "capability_category": "read_only",
        "evidence_expectation": ["human_review_required"],
        "rollback_status": "not_applicable",
        "operator_options": ["request_dry_run_details", "cancel"],
        "source_refs": ["repo-audit-implementation-readiness"],
    }
    request.update(overrides)
    return build_mission_control_preview(request)


def _tool_simulation_decision(**overrides: object):
    request: dict[str, object] = {
        "request_id": "req-repo-audit-sim",
        "command_id": "cmd-repo-audit-sim",
        "raw_user_request": "simulate metadata review",
        "normalized_intent": "read_file",
        "route_kind": "filesystem",
        "proposed_action": "reference docs only",
        "proposed_tool": "read_file",
        "tool_category": "file_tool",
        "capability_category": "local_file_read",
        "risk_tier": "read_only",
        "affected_resources": ["docs/repo-audit-pack-implementation-readiness-v1.md"],
        "policy_rule_refs": ["policy:repo_audit.metadata_only"],
        "policy_decision_hint": "ready",
        "approval_hint": {"required": False, "reason": "metadata only"},
        "lease_hint": {"required": False, "reason": "lease not required"},
        "evidence_expectation_hint": ["policy_decision_ref_expected"],
        "rollback_status": "not_applicable",
        "source_refs": ["policy:repo_audit.metadata_only"],
    }
    request.update(overrides)
    return build_tool_simulation(request)


def _plugin_review_decision(**overrides: object):
    manifest_decision = validate_plugin_manifest(_manifest())
    record: dict[str, object] = {
        "review_record_id": "review:repo-audit-implementation-readiness",
        "plugin_id": "repo-audit-implementation-readiness",
        "plugin_name": "Repo Audit Implementation Readiness",
        "plugin_version": "0.1.0",
        "manifest_ref": "manifest:repo-audit-implementation-readiness",
        "review_status": "review_ready",
        "review_scope": ["manifest_metadata_only", "read_only_pack_candidate"],
        "source_refs": ["manifest:repo-audit-implementation-readiness"],
        "limitations": ["metadata-only readiness review"],
        "unknowns": ["no repo scan implementation reviewed"],
        "required_policy_review": True,
        "allowed_operations": ["metadata_review"],
        "forbidden_operations": ["repo_scan", "read_file", "run_git", "run_tests"],
        "declared_capabilities": ["vertical_pack_read"],
        "declared_risk_tiers": ["read_only"],
        "requested_permissions": [],
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
    }
    record.update(overrides)
    return validate_plugin_review_record(record, manifest_decision=manifest_decision)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "readiness_id": "repo-audit-implementation-readiness:aegis:1",
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "commit_ref": "29b3eba",
        "branch_ref": "main",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
        "source_refs": [
            {"ref_id": "commit:29b3eba", "ref_type": "commit"},
            {"ref_id": "contract:repo-audit-pack", "ref_type": "contract"},
        ],
        "allowed_source_scopes": ["source_inventory_readiness", "architecture_review_readiness"],
        "requested_audit_scopes": ["source_inventory_readiness"],
        "file_access_policy": "caller_supplied_refs_only",
        "allowed_path_prefixes": ["src/aegis", "tests", "docs"],
        "candidate_file_refs": [
            "src/aegis/core/repo_audit_pack.py",
            "tests/test_core/test_repo_audit_pack.py",
            "docs/repo-audit-pack-read-only-contract-v1.md",
        ],
        "excluded_path_patterns": [
            "logs/**",
            ".git/**",
            ".venv/**",
            "node_modules/**",
            "dist/**",
            "build/**",
            ".next/**",
            "**/*.env",
            "**/*.key",
            "**/*.pem",
            "**/*secret*",
            "**/*token*",
        ],
        "generated_artifact_policy": "exclude_generated_artifacts",
        "secret_privacy_policy": "deny_by_default",
        "hidden_path_policy": "deny_hidden_and_system_paths",
        "symlink_policy": "deny_symlink_targets",
        "git_metadata_mode": "caller_supplied_refs_only",
        "test_metadata_mode": "caller_supplied_test_refs_only",
        "test_refs": ["tests/test_core/test_repo_audit_pack.py"],
        "dependency_refs": ["pyproject.toml"],
        "output_categories": ["architecture_note_candidate", "limitation_note"],
        "report_contract": "candidate_metadata_only",
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "limitations": ["metadata only"],
        "unknowns": ["no repo scan performed"],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related):
    defaults = {
        "repo_audit_decision": _repo_audit_decision(),
        "developer_work_passport_decision": _passport_decision(),
        "compliance_evidence_decision": _compliance_decision(),
        "mission_control_decision": _mission_control_decision(),
        "tool_simulation_decision": _tool_simulation_decision(),
        "plugin_review_decision": _plugin_review_decision(),
        "vertical_pack_decision": _vertical_pack_decision(),
    }
    defaults.update(related)
    return validate_repo_audit_implementation_readiness(request, **defaults)


def test_valid_minimal_readiness_validates_as_non_authoritative() -> None:
    decision = _validate(_request())

    assert decision.contract_version == REPO_AUDIT_IMPLEMENTATION_READINESS_VERSION
    assert decision.validation_status == "readiness_ready"
    assert decision.failure_reasons == ()
    assert decision.readiness_contract is not None
    assert decision.readiness_contract.runtime_dispatch_allowed is False
    assert decision.readiness_contract.execution_permission == REPO_AUDIT_IMPLEMENTATION_EXECUTION_PERMISSION
    assert decision.readiness_contract.repo_scan_performed is False
    assert decision.readiness_contract.file_read_performed is False
    assert decision.readiness_contract.git_command_performed is False
    assert decision.readiness_contract.test_execution_performed is False
    assert decision.readiness_contract.subprocess_performed is False
    assert decision.readiness_contract.model_call_performed is False
    assert decision.readiness_contract.tool_call_performed is False
    assert decision.readiness_contract.api_call_performed is False
    assert decision.readiness_contract.mcp_call_performed is False
    assert decision.readiness_contract.memory_access_performed is False
    assert decision.readiness_contract.report_generated is False
    assert decision.readiness_contract.export_performed is False
    assert decision.readiness_contract.certification_claim is False


def test_architecture_review_readiness_validates_without_scanning() -> None:
    decision = _validate(
        _request(
            requested_audit_scopes=["architecture_review_readiness"],
            output_categories=["architecture_note_candidate"],
        )
    )

    assert decision.validation_status == "readiness_ready"
    assert decision.readiness_input is not None
    assert decision.readiness_input.requested_audit_scopes == ("architecture_review_readiness",)
    assert decision.readiness_contract is not None
    assert decision.readiness_contract.repo_scan_performed is False


def test_security_smell_readiness_preserves_uncertain_candidate_output() -> None:
    decision = _validate(
        _request(
            requested_audit_scopes=["security_smell_readiness"],
            output_categories=["security_smell_candidate"],
            output_candidates=[
                {
                    "candidate_id": "security-smell-1",
                    "category": "security_smell_candidate",
                    "summary": "Caller-supplied metadata suggests a review item.",
                    "source_refs": [],
                    "uncertainty": "not scanned by product code",
                }
            ],
        )
    )

    assert decision.validation_status == "readiness_ready"
    assert decision.output_contract is not None
    assert decision.output_contract.candidates[0].uncertainty == "not scanned by product code"
    assert decision.output_contract.candidates[0].verified is False


def test_missing_request_or_repo_identity_denied() -> None:
    missing = validate_repo_audit_implementation_readiness(None)
    no_identity = _validate(_request(readiness_id="", repo_id="", repo_name="", repo_root_ref=""))

    assert missing.validation_status == "failed_validation"
    assert "missing_request" in missing.failure_reasons
    assert no_identity.validation_status == "failed_validation"
    assert "repo_identity_required" in no_identity.failure_reasons


def test_missing_tenant_namespace_project_scope_denied() -> None:
    decision = _validate(_request(tenant_scope="", project_scope="", namespace=""))

    assert decision.validation_status == "failed_validation"
    assert "tenant_scope_required" in decision.failure_reasons
    assert "project_scope_required" in decision.failure_reasons
    assert "namespace_required" in decision.failure_reasons


def test_unknown_audit_scope_denied() -> None:
    decision = _validate(_request(requested_audit_scopes=["imaginary_scope"]))

    assert decision.validation_status == "blocked"
    assert "unknown_audit_scope" in decision.failure_reasons


def test_forbidden_scopes_and_claims_are_denied() -> None:
    forbidden = [
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
    ]

    for scope in forbidden:
        decision = _validate(_request(requested_audit_scopes=[scope]))

        assert "forbidden_audit_scope_denied" in decision.failure_reasons
        assert decision.runtime_dispatch_allowed is False


def test_absolute_external_path_and_path_traversal_denied() -> None:
    decision = _validate(
        _request(
            candidate_file_refs=[
                "C:/Users/nemes/Desktop/U.L.T.R.O.N/README.md",
                "../Ultron/secrets.env",
            ]
        )
    )

    assert "absolute_or_external_path_denied" in decision.failure_reasons
    assert "path_traversal_denied" in decision.failure_reasons


def test_missing_secret_generated_hidden_or_symlink_policy_denied() -> None:
    decision = _validate(
        _request(
            excluded_path_patterns=[],
            generated_artifact_policy="",
            secret_privacy_policy="",
            hidden_path_policy="",
            symlink_policy="",
        )
    )

    assert "generated_artifact_policy_required" in decision.failure_reasons
    assert "secret_privacy_policy_required" in decision.failure_reasons
    assert "hidden_path_policy_required" in decision.failure_reasons
    assert "symlink_policy_required" in decision.failure_reasons
    assert "required_exclusion_patterns_missing" in decision.failure_reasons


def test_runtime_logs_model_vector_build_and_secret_paths_excluded_by_default() -> None:
    decision = _validate(
        _request(
            candidate_file_refs=[
                "logs/backend.log",
                "runtime/events.jsonl",
                "models/local.gguf",
                "vector_db/index.bin",
                "build/output.js",
                ".next/server/app.js",
                ".env",
                "config/api_token.txt",
            ]
        )
    )

    assert "forbidden_path_ref_denied" in decision.failure_reasons
    assert "secret_path_ref_denied" in decision.failure_reasons


def test_symlink_and_hidden_paths_are_denied() -> None:
    decision = _validate(
        _request(
            candidate_file_refs=[".git/config", "src/aegis/link_to_external"],
            symlink_refs=["src/aegis/link_to_external"],
            hidden_path_refs=[".git/config"],
        )
    )

    assert "hidden_path_ref_denied" in decision.failure_reasons
    assert "symlink_path_ref_denied" in decision.failure_reasons


def test_high_risk_audit_scope_requires_privacy_and_data_sensitivity() -> None:
    decision = _validate(
        _request(
            requested_audit_scopes=["security_smell_readiness"],
            privacy_class="",
            data_sensitivity="",
        )
    )

    assert "privacy_class_required_for_high_risk_audit" in decision.failure_reasons
    assert "data_sensitivity_required_for_high_risk_audit" in decision.failure_reasons


def test_source_less_proof_claim_blocked_and_uncertainty_required() -> None:
    blocked = _validate(
        _request(
            claims=["tests passed", "code is safe"],
            output_candidates=[
                {
                    "candidate_id": "proof-claim",
                    "category": "test_reference_candidate",
                    "summary": "Tests passed.",
                    "source_refs": [],
                }
            ],
        )
    )
    uncertain = _validate(
        _request(
            output_candidates=[
                {
                    "candidate_id": "test-ref-1",
                    "category": "test_reference_candidate",
                    "summary": "Caller supplied test reference only.",
                    "source_refs": [],
                    "uncertainty": "test was not executed by product behavior",
                }
            ],
        )
    )

    assert "test_success_claim_denied" in blocked.failure_reasons
    assert "code_safety_claim_denied" in blocked.failure_reasons
    assert "candidate_without_source_requires_uncertainty" in blocked.failure_reasons
    assert uncertain.validation_status == "readiness_ready"


def test_authority_runtime_dispatch_and_grants_rejected() -> None:
    decision = _validate(
        _request(
            authority=True,
            runtime_dispatch_allowed=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
            frontend_authority=True,
        )
    )

    assert "authority_must_be_false" in decision.failure_reasons
    assert "runtime_dispatch_not_allowed" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons
    assert "frontend_authority_not_allowed" in decision.failure_reasons


def test_execution_surface_requests_rejected() -> None:
    decision = _validate(
        _request(
            repo_scan_performed=True,
            file_read_performed=True,
            git_command_performed=True,
            test_execution_performed=True,
            subprocess_performed=True,
            model_call_performed=True,
            tool_call_performed=True,
            api_call_performed=True,
            mcp_call_performed=True,
            memory_access_performed=True,
            report_generated=True,
            export_performed=True,
        )
    )

    assert "repo_scan_request_denied" in decision.failure_reasons
    assert "file_read_request_denied" in decision.failure_reasons
    assert "git_command_request_denied" in decision.failure_reasons
    assert "test_execution_request_denied" in decision.failure_reasons
    assert "subprocess_request_denied" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons
    assert "tool_call_request_denied" in decision.failure_reasons
    assert "api_call_request_denied" in decision.failure_reasons
    assert "mcp_call_request_denied" in decision.failure_reasons
    assert "memory_access_request_denied" in decision.failure_reasons
    assert "report_generation_request_denied" in decision.failure_reasons
    assert "export_request_denied" in decision.failure_reasons


def test_evidence_and_verifier_success_rejected() -> None:
    decision = _validate(
        _request(
            evidence_provided_by_readiness=True,
            evidence_provided_by_pack_output=True,
            verifier_success=True,
            verified_success=True,
            success=True,
        )
    )

    assert "readiness_cannot_provide_evidence" in decision.failure_reasons
    assert "readiness_cannot_mark_verifier_success" in decision.failure_reasons
    assert "success_claim_denied" in decision.failure_reasons
    assert decision.evidence_provided_by_readiness is False
    assert decision.verifier_success is False


def test_related_decisions_with_dispatch_evidence_or_verifier_success_rejected() -> None:
    repo_decision = replace(
        _repo_audit_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_report=True,
        verifier_success=True,
    )
    passport_decision = replace(
        _passport_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_passport=True,
        verifier_success=True,
    )
    compliance_decision = replace(
        _compliance_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_package=True,
        verifier_success=True,
    )
    mission_decision = replace(
        _mission_control_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_preview=True,
        verifier_success=True,
    )
    tool_decision = replace(
        _tool_simulation_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_simulation=True,
        verifier_success=True,
    )
    plugin_decision = replace(
        _plugin_review_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_review=True,
        verifier_success=True,
    )
    vertical_decision = replace(
        _vertical_pack_decision(),
        runtime_dispatch_allowed=True,
        evidence_provided_by_pack_output=True,
        verifier_success=True,
    )

    decision = _validate(
        _request(),
        repo_audit_decision=repo_decision,
        developer_work_passport_decision=passport_decision,
        compliance_evidence_decision=compliance_decision,
        mission_control_decision=mission_decision,
        tool_simulation_decision=tool_decision,
        plugin_review_decision=plugin_decision,
        vertical_pack_decision=vertical_decision,
    )

    assert "repo_audit_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "repo_audit_evidence_claim_denied" in decision.failure_reasons
    assert "repo_audit_verifier_success_claim_denied" in decision.failure_reasons
    assert "developer_work_passport_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "compliance_evidence_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "mission_control_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "tool_simulation_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "plugin_review_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "vertical_pack_runtime_dispatch_attempt_denied" in decision.failure_reasons


def test_related_decision_with_failure_reasons_blocks_readiness() -> None:
    bad_context = SimpleNamespace(
        runtime_dispatch_allowed=False,
        failure_reasons=("stale_context",),
    )

    decision = _validate(_request(), context_compiler_decision=bad_context)

    assert "context_compiler_decision_has_failures" in decision.failure_reasons


def test_validation_does_not_mutate_input_or_related_decisions() -> None:
    request = _request(
        fallback_expectation={"fallback_is_success": True},
        output_candidates=[
            {
                "candidate_id": "candidate-1",
                "category": "unknown_note",
                "summary": "Uncertain output.",
                "uncertainty": "metadata only",
            }
        ],
    )
    before = deepcopy(request)
    repo_decision = _repo_audit_decision()
    passport_decision = _passport_decision()
    compliance_decision = _compliance_decision()
    mission_decision = _mission_control_decision()
    tool_decision = _tool_simulation_decision()
    plugin_decision = _plugin_review_decision()

    decision = validate_repo_audit_implementation_readiness(
        request,
        repo_audit_decision=repo_decision,
        developer_work_passport_decision=passport_decision,
        compliance_evidence_decision=compliance_decision,
        mission_control_decision=mission_decision,
        tool_simulation_decision=tool_decision,
        plugin_review_decision=plugin_decision,
    )

    assert request == before
    assert repo_decision.runtime_dispatch_allowed is False
    assert passport_decision.runtime_dispatch_allowed is False
    assert compliance_decision.runtime_dispatch_allowed is False
    assert mission_decision.runtime_dispatch_allowed is False
    assert tool_decision.runtime_dispatch_allowed is False
    assert plugin_decision.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False


def test_output_never_sets_runtime_dispatch_allowed_true() -> None:
    decision = _validate(_request())

    assert decision.runtime_dispatch_allowed is False
    assert decision.readiness_contract is not None
    assert decision.readiness_contract.runtime_dispatch_allowed is False
    assert decision.output_contract is not None
    assert decision.output_contract.runtime_dispatch_allowed is False
