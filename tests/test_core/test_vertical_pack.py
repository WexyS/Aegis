from __future__ import annotations

from copy import deepcopy

from aegis.core.plugin_lifecycle import evaluate_plugin_lifecycle_transition
from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import (
    calculate_manifest_checksum,
    evaluate_manifest_drift,
)
from aegis.core.vertical_pack import (
    VERTICAL_PACK_EXECUTION_PERMISSION,
    VERTICAL_PACK_FRAMEWORK_VERSION,
    validate_vertical_pack_descriptor,
)


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "vertical-pack-fixture",
        "pack_name": "Vertical Pack Fixture",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["review metadata"],
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


def _action_manifest(**overrides: object) -> dict[str, object]:
    manifest = _manifest(
        pack_type="approval_gated_action_pack",
        lifecycle_status="policy_review_required",
        capability_categories=["local_tool_write"],
        risk_tiers=["local_file_write"],
        approval_required=True,
        lease_required=True,
        evidence_expectations={"kind": "postcondition"},
        verifier_strategy="postcondition",
        rollback_strategy="restore",
        eval_requirements=["approval-bypass-negative-test"],
        audit_requirements=["journal_ref", "evidence_ref"],
    )
    manifest.update(overrides)
    return manifest


def _valid_decisions(manifest: dict[str, object] | None = None):
    source = manifest or _manifest()
    manifest_decision = validate_plugin_manifest(source)
    integrity_decision = evaluate_manifest_drift(
        source,
        reviewed_checksum=calculate_manifest_checksum(source),
        reviewed_version=str(source["pack_version"]),
        signature_status="signature_verified",
    )
    lifecycle_decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=manifest_decision,
        integrity_decision=integrity_decision,
    )
    return manifest_decision, integrity_decision, lifecycle_decision


def _action_decisions():
    manifest = _action_manifest()
    manifest_decision = validate_plugin_manifest(manifest)
    integrity_decision = evaluate_manifest_drift(
        manifest,
        reviewed_checksum=calculate_manifest_checksum(manifest),
        reviewed_version=str(manifest["pack_version"]),
        signature_status="signature_verified",
    )
    lifecycle_decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=manifest_decision,
        integrity_decision=integrity_decision,
        requested_capability="local_tool_write",
        risk_tier="local_file_write",
        approval_present=True,
        lease_present=True,
        evidence_expectation_present=True,
        verifier_strategy_present=True,
        audit_requirements_present=True,
        eval_present=True,
        rollback_present=True,
    )
    return manifest_decision, integrity_decision, lifecycle_decision


def _base_descriptor(**overrides: object) -> dict[str, object]:
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
    descriptor.update(overrides)
    return descriptor


def _validate(descriptor: dict[str, object], *, decisions=None):
    manifest_decision, integrity_decision, lifecycle_decision = decisions or _valid_decisions()
    return validate_vertical_pack_descriptor(
        descriptor,
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
    )


def test_valid_repo_audit_read_only_descriptor_is_non_dispatchable() -> None:
    decision = _validate(_base_descriptor())

    assert decision.framework_version == VERTICAL_PACK_FRAMEWORK_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.pack_category == "repo_audit"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == VERTICAL_PACK_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False


def test_valid_developer_work_passport_evidence_report_descriptor_is_non_dispatchable() -> None:
    descriptor = _base_descriptor(
        pack_id="developer-work-passport.evidence",
        pack_category="developer_work_passport",
        operating_profile="evidence_reporting",
        namespace="developer_work_passport",
        tenant_scope="local",
        project_scope="aegis",
        required_capabilities=["vertical_pack_read"],
        required_tools=[],
        tool_scopes=[],
        required_eval_families=["passport-transparency-negative"],
        evidence_expectations=["activity_provenance_summary"],
        verifier_expectations=["source_traceability_check"],
        trust_positioning="transparency_report",
        audit_requirements=["visible_report"],
    )

    decision = _validate(descriptor)

    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False


def test_valid_skopos_terminology_proposal_descriptor_is_non_dispatchable() -> None:
    descriptor = _base_descriptor(
        pack_id="skopos.terminology.proposal",
        pack_category="skopos_terminology",
        operating_profile="proposal_only",
        namespace="skopos_terminology",
        tenant_scope="local",
        project_scope="aegis",
        required_capabilities=["vertical_pack_read"],
        required_tools=[],
        tool_scopes=[],
        required_model_roles=["terminology_reviewer"],
        model_provider_scopes=["local_model_only"],
        required_eval_families=["terminology-proposal-negative"],
        source_language="en",
        target_language="tr",
        domain_refs=["software_runtime"],
        reviewer_refs=["operator_review"],
    )

    decision = _validate(descriptor)

    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False


def test_valid_compliance_evidence_descriptor_is_forensic_readiness_not_certification() -> None:
    descriptor = _base_descriptor(
        pack_id="compliance.evidence.readiness",
        pack_category="compliance_evidence",
        operating_profile="evidence_reporting",
        namespace="compliance_evidence",
        tenant_scope="local",
        project_scope="aegis",
        required_capabilities=["vertical_pack_read"],
        required_tools=[],
        tool_scopes=[],
        required_eval_families=["compliance-evidence-negative"],
        evidence_expectations=["audit_package_refs"],
        verifier_expectations=["source_traceability_check"],
        trust_positioning="forensic_readiness",
        claims=["operator audit package support"],
        audit_requirements=["policy_refs", "evidence_refs", "audit_refs"],
    )

    decision = _validate(descriptor)

    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False


def test_unknown_category_denied_unless_custom_has_explicit_namespace() -> None:
    unknown = _validate(_base_descriptor(pack_category="imaginary_vertical"))
    custom = _validate(
        _base_descriptor(
            pack_id="custom.operator.pack",
            pack_category="custom",
            namespace="custom.operator",
            custom_category_namespace="operator.custom",
            required_eval_families=[],
        )
    )

    assert "unknown_pack_category" in unknown.failure_reasons
    assert unknown.runtime_dispatch_allowed is False
    assert custom.validation_status == "review_ready"
    assert custom.runtime_dispatch_allowed is False


def test_unknown_operating_profile_denied() -> None:
    decision = _validate(_base_descriptor(operating_profile="auto_execute"))

    assert decision.validation_status == "blocked"
    assert "unknown_operating_profile" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_missing_namespace_denied() -> None:
    decision = _validate(_base_descriptor(namespace=""))

    assert decision.validation_status == "failed_validation"
    assert "missing_required_field" in decision.failure_reasons


def test_tenant_sensitive_pack_without_tenant_scope_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_category="language_learning",
            operating_profile="proposal_only",
            namespace="language_learning",
            tenant_scope="",
            project_scope="aegis",
            required_capabilities=["vertical_pack_read"],
            required_tools=[],
            tool_scopes=[],
            required_model_roles=["learning_reviewer"],
            model_provider_scopes=["local_model_only"],
            required_memory_namespaces=["learner"],
            required_eval_families=["learner-isolation"],
            learner_namespace="learner.local",
        )
    )

    assert "tenant_scope_required_for_pack" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_memory_using_pack_without_memory_namespace_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_category="glossa",
            operating_profile="proposal_only",
            namespace="glossa",
            tenant_scope="local",
            project_scope="aegis",
            translation_scope="project",
            user_scope="operator",
            required_model_roles=["translation_reviewer"],
            model_provider_scopes=["local_model_only"],
            required_memory_namespaces=[],
        )
    )

    assert "memory_namespace_required" in decision.failure_reasons


def test_tool_using_pack_without_tool_scope_denied() -> None:
    decision = _validate(_base_descriptor(tool_scopes=[]))

    assert "tool_scope_required" in decision.failure_reasons


def test_model_using_pack_without_model_role_or_provider_scope_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_category="document_analysis",
            namespace="document_analysis",
            tenant_scope="local",
            project_scope="aegis",
            required_capabilities=["vertical_pack_read"],
            required_tools=[],
            tool_scopes=[],
            required_model_roles=[],
            model_provider_scopes=[],
            document_provenance_requirements=["source_doc_ref"],
        )
    )

    assert "model_role_required" in decision.failure_reasons
    assert "model_provider_scope_required" in decision.failure_reasons


def test_external_integration_pack_without_api_scope_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_category="business_automation",
            operating_profile="external_integration_candidate",
            namespace="business_automation",
            tenant_scope="local",
            project_scope="aegis",
            required_capabilities=["vertical_pack_read"],
            required_memory_namespaces=["tenant"],
            required_external_api_scopes=[],
        )
    )

    assert "external_api_scope_required" in decision.failure_reasons


def test_evidence_reporting_pack_without_evidence_expectations_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_category="compliance_evidence",
            operating_profile="evidence_reporting",
            namespace="compliance_evidence",
            tenant_scope="local",
            project_scope="aegis",
            required_capabilities=["vertical_pack_read"],
            required_tools=[],
            tool_scopes=[],
            required_eval_families=["compliance-evidence-negative"],
            evidence_expectations=[],
            verifier_expectations=["source_traceability_check"],
            trust_positioning="forensic_readiness",
        )
    )

    assert "evidence_expectation_required" in decision.failure_reasons


def test_action_gated_pack_without_evidence_verifier_approval_and_lease_denied() -> None:
    decision = _validate(
        _base_descriptor(
            pack_id="business.action",
            pack_category="business_automation",
            operating_profile="approval_gated_action",
            namespace="business_automation",
            tenant_scope="local",
            project_scope="aegis",
            required_capabilities=["vertical_pack_write"],
            required_memory_namespaces=["tenant"],
            required_external_api_scopes=["project_read"],
            evidence_expectations=[],
            verifier_expectations=[],
            approval_requirements=[],
            lease_requirements=[],
            policy_requirements=[],
        ),
        decisions=_action_decisions(),
    )

    assert "evidence_expectation_required" in decision.failure_reasons
    assert "verifier_expectation_required" in decision.failure_reasons
    assert "approval_requirements_required" in decision.failure_reasons
    assert "lease_requirements_required" in decision.failure_reasons
    assert "policy_requirements_required" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_manifest_failure_blocks_pack_validation() -> None:
    manifest = _manifest(authority=True)
    manifest_decision, integrity_decision, lifecycle_decision = _valid_decisions(manifest)

    decision = _validate(
        _base_descriptor(),
        decisions=(manifest_decision, integrity_decision, lifecycle_decision),
    )

    assert "manifest_validation_failed" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_integrity_quarantine_or_drift_blocks_pack_validation() -> None:
    manifest = _manifest(pack_name="Changed")
    manifest_decision = validate_plugin_manifest(manifest)
    integrity_decision = evaluate_manifest_drift(manifest, reviewed_checksum="not-current")
    lifecycle_decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=manifest_decision,
        integrity_decision=integrity_decision,
    )

    decision = _validate(
        _base_descriptor(),
        decisions=(manifest_decision, integrity_decision, lifecycle_decision),
    )

    assert "integrity_quarantine_blocks_pack" in decision.failure_reasons
    assert "integrity_must_be_unchanged_for_pack_review" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_lifecycle_revoked_quarantined_deprecated_or_failed_blocks_validation() -> None:
    for state in ("revoked", "quarantined", "deprecated", "failed_validation"):
        manifest_decision, integrity_decision, _ = _valid_decisions()
        lifecycle_decision = evaluate_plugin_lifecycle_transition(
            state,
            "active_read_only",
            manifest_validation=manifest_decision,
            integrity_decision=integrity_decision,
        )

        decision = _validate(
            _base_descriptor(),
            decisions=(manifest_decision, integrity_decision, lifecycle_decision),
        )

        assert "lifecycle_validation_failed" in decision.failure_reasons
        assert decision.runtime_dispatch_allowed is False


def test_signature_verified_does_not_grant_dispatch() -> None:
    decision = _validate(_base_descriptor(), decisions=_valid_decisions())

    assert decision.validation_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False


def test_active_action_gated_does_not_grant_dispatch() -> None:
    descriptor = _base_descriptor(
        pack_id="business.action.valid",
        pack_category="business_automation",
        operating_profile="approval_gated_action",
        namespace="business_automation",
        tenant_scope="local",
        project_scope="aegis",
        required_capabilities=["vertical_pack_write"],
        required_memory_namespaces=["tenant"],
        required_external_api_scopes=["project_read"],
        evidence_expectations=["postcondition_evidence"],
        verifier_expectations=["postcondition_verifier"],
        approval_requirements=["operator_approval"],
        lease_requirements=["scoped_temporary_lease"],
        policy_requirements=["vertical_pack_write.approval_gated"],
    )

    decision = _validate(descriptor, decisions=_action_decisions())

    assert decision.validation_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == VERTICAL_PACK_EXECUTION_PERMISSION


def test_authority_runtime_dispatch_and_grant_fields_are_rejected() -> None:
    decision = _validate(
        _base_descriptor(
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


def test_aegis_platform_identity_override_rejected() -> None:
    decision = _validate(_base_descriptor(defines_aegis_platform_identity=True))

    assert "pack_cannot_define_aegis_platform_identity" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_pack_output_cannot_create_evidence_or_verifier_success() -> None:
    decision = _validate(
        _base_descriptor(
            evidence_provided_by_pack_output=True,
            verifier_success=True,
            pack_output_is_evidence=True,
            pack_output_is_verifier_truth=True,
        )
    )

    assert decision.evidence_provided_by_pack_output is False
    assert decision.verifier_success is False
    assert decision.pack_output_is_evidence is False
    assert decision.pack_output_is_verifier_truth is False
    assert "pack_output_cannot_provide_evidence" in decision.failure_reasons
    assert "pack_output_cannot_mark_verifier_success" in decision.failure_reasons


def test_compliance_evidence_legal_certification_claim_rejected() -> None:
    decision = _validate(
        _base_descriptor(
            pack_id="compliance.evidence.bad",
            pack_category="compliance_evidence",
            operating_profile="evidence_reporting",
            namespace="compliance_evidence",
            tenant_scope="local",
            project_scope="aegis",
            required_capabilities=["vertical_pack_read"],
            required_tools=[],
            tool_scopes=[],
            required_eval_families=["compliance-evidence-negative"],
            evidence_expectations=["audit_package_refs"],
            verifier_expectations=["source_traceability_check"],
            trust_positioning="forensic_readiness",
            claims=["court-admissible legal certification"],
        )
    )

    assert "compliance_evidence_cannot_claim_legal_certification" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_validation_does_not_mutate_input_or_supplied_decisions() -> None:
    descriptor = _base_descriptor()
    before_descriptor = deepcopy(descriptor)
    decisions = _valid_decisions()
    before_failure_sets = tuple(decision.failure_reasons for decision in decisions)

    decision = _validate(descriptor, decisions=decisions)

    assert descriptor == before_descriptor
    assert tuple(source.failure_reasons for source in decisions) == before_failure_sets
    assert decision.runtime_dispatch_allowed is False
