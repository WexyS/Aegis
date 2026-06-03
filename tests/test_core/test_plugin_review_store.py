from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import calculate_manifest_checksum, evaluate_manifest_drift
from aegis.core.plugin_lifecycle import evaluate_plugin_lifecycle_transition
from aegis.core.plugin_review_store import (
    PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION,
    PLUGIN_REVIEW_STORE_VERSION,
    validate_plugin_review_record,
)
from aegis.core.vertical_pack import VERTICAL_PACK_EXECUTION_PERMISSION, validate_vertical_pack_descriptor


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "aegis.reviewed.pack",
        "pack_name": "Reviewed Pack",
        "pack_type": "read_only_pack",
        "pack_version": "1.0.0",
        "capabilities": ["read metadata"],
        "capability_categories": ["vertical_pack_read"],
        "risk_tiers": ["read_only"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": [],
        "memory_namespaces": [],
        "external_api_scopes": [],
        "namespace_scope": "reviewed_pack",
        "tenant_scope": "local",
        "training_data_policy": {"namespace_specific": True},
    }
    manifest.update(overrides)
    return manifest


def _related_decisions():
    manifest = _manifest()
    manifest_decision = validate_plugin_manifest(manifest)
    checksum = calculate_manifest_checksum(manifest)
    integrity_decision = evaluate_manifest_drift(
        manifest,
        reviewed_checksum=checksum,
        reviewed_version="1.0.0",
        signature_status="signature_verified",
    )
    lifecycle_decision = evaluate_plugin_lifecycle_transition(
        "registered_metadata_only",
        "approved_for_read_only",
        manifest_validation=manifest_decision,
        integrity_decision=integrity_decision,
        signature_state="signature_verified",
    )
    vertical_pack_decision = validate_vertical_pack_descriptor(
        {
            "pack_id": "aegis.reviewed.pack",
            "pack_category": "compliance_evidence",
            "operating_profile": "evidence_reporting",
            "namespace": "reviewed_pack",
            "tenant_scope": "local",
            "project_scope": "aegis",
            "required_capabilities": ["vertical_pack_read"],
            "required_tools": [],
            "tool_scopes": [],
            "required_model_roles": [],
            "model_provider_scopes": [],
            "required_memory_namespaces": [],
            "required_external_api_scopes": [],
            "required_eval_families": ["review-store-contract"],
            "evidence_expectations": ["source_refs"],
            "verifier_expectations": ["human_review"],
            "policy_requirements": ["vertical_pack_read.read_only"],
            "approval_requirements": [],
            "lease_requirements": [],
            "data_sensitivity": "metadata",
            "privacy_class": "project_internal",
            "trust_positioning": "forensic_readiness",
            "claims": ["audit-readiness metadata only"],
            "authority": False,
            "execution_permission": VERTICAL_PACK_EXECUTION_PERMISSION,
            "runtime_dispatch_allowed": False,
        },
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
    )
    return manifest_decision, integrity_decision, lifecycle_decision, vertical_pack_decision


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "review_record_id": "review:aegis.reviewed.pack:1",
        "plugin_id": "aegis.reviewed.pack",
        "plugin_name": "Reviewed Pack",
        "plugin_version": "1.0.0",
        "manifest_ref": "manifest:aegis.reviewed.pack:1.0.0",
        "manifest_checksum_ref": "sha256:reviewed",
        "signature_ref": "signature:reviewed",
        "lifecycle_decision_ref": "lifecycle:approved_for_read_only",
        "vertical_pack_decision_ref": "vertical-pack:review-ready",
        "policy_refs": ["policy:vertical_pack_read.read_only"],
        "evidence_refs": ["evidence:manifest-review"],
        "reviewer_ref": "reviewer:local",
        "review_timestamp": "2026-06-03T00:00:00Z",
        "review_status": "review_ready",
        "review_scope": ["manifest_metadata_only", "vertical_pack_metadata_only"],
        "review_version": "plugin-review-store/1",
        "source_refs": ["manifest:aegis.reviewed.pack:1.0.0"],
        "limitations": ["metadata-only review"],
        "unknowns": ["runtime behavior not evaluated"],
        "required_followups": ["revalidate on manifest drift"],
        "required_operator_review": True,
        "required_security_review": False,
        "required_privacy_review": False,
        "required_policy_review": True,
        "allowed_operations": ["metadata_review"],
        "forbidden_operations": ["execute_plugin", "dynamic_import", "publish_marketplace"],
        "declared_capabilities": ["vertical_pack_read"],
        "declared_risk_tiers": ["read_only"],
        "requested_permissions": [],
        "data_sensitivity": "metadata",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "reviewed_pack",
        "provenance_refs": ["reviewer:local", "checksum:reviewed"],
        "expiry_or_revalidation_at": "2026-12-03T00:00:00Z",
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_provided_by_review": False,
        "verifier_success": False,
        "mutation_performed": False,
        "frontend_authority": False,
        "plugin_execution_allowed": False,
        "dynamic_import_allowed": False,
        "marketplace_publication_allowed": False,
    }
    record.update(overrides)
    return record


def _validate(record: dict[str, object], **related):
    defaults = _related_decisions()
    keys = (
        "manifest_decision",
        "integrity_decision",
        "lifecycle_decision",
        "vertical_pack_decision",
    )
    kwargs = dict(zip(keys, defaults))
    kwargs.update(related)
    return validate_plugin_review_record(record, **kwargs)


def test_valid_metadata_only_plugin_review_record_validates_as_non_authoritative() -> None:
    decision = _validate(_record())

    assert decision.contract_version == PLUGIN_REVIEW_STORE_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.review_record is not None
    assert decision.review_record.authority is False
    assert decision.review_record.runtime_dispatch_allowed is False
    assert decision.review_record.execution_permission == PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION
    assert decision.review_record.approval_grant is False
    assert decision.review_record.capability_grant is False
    assert decision.review_record.lease_grant is False
    assert decision.review_record.evidence_provided_by_review is False
    assert decision.review_record.verifier_success is False
    assert decision.review_record.mutation_performed is False
    assert decision.review_record.frontend_authority is False
    assert decision.review_record.plugin_execution_allowed is False
    assert decision.review_record.dynamic_import_allowed is False
    assert decision.review_record.marketplace_publication_allowed is False


def test_review_ready_does_not_grant_execution() -> None:
    decision = _validate(_record(review_status="review_ready"))

    assert decision.validation_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.plugin_execution_allowed is False
    assert decision.review_record is not None
    assert decision.review_record.requires_operator_approval_for_execution is True


def test_approved_metadata_only_does_not_grant_execution() -> None:
    decision = _validate(_record(review_status="approved_metadata_only"))

    assert decision.validation_status == "approved_metadata_only"
    assert decision.review_record is not None
    assert decision.review_record.runtime_dispatch_allowed is False
    assert decision.review_record.plugin_execution_allowed is False


def test_catalog_review_candidate_does_not_allow_marketplace_publication() -> None:
    decision = _validate(
        _record(
            review_status="approved_for_catalog_review",
            review_scope=["catalog_review_candidate"],
        )
    )

    assert decision.validation_status == "approved_for_catalog_review"
    assert decision.review_record is not None
    assert decision.review_record.marketplace_publication_allowed is False


def test_execution_candidate_future_only_does_not_allow_execution() -> None:
    decision = _validate(_record(review_scope=["execution_candidate_future_only"]))

    assert decision.review_record is not None
    assert decision.review_record.plugin_execution_allowed is False
    assert decision.review_record.execution_permission == PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION


def test_rejected_blocked_and_quarantined_status_blocks_review_decision() -> None:
    for status in ("rejected", "blocked", "quarantined"):
        decision = _validate(_record(review_status=status))

        assert decision.validation_status == status
        assert decision.review_record is not None
        assert decision.review_record.review_blocked is True
        assert decision.runtime_dispatch_allowed is False


def test_expired_superseded_and_deprecated_require_revalidation_or_block() -> None:
    for status in ("expired", "superseded", "deprecated"):
        missing = _validate(_record(review_status=status, expiry_or_revalidation_at="", supersedes_review_record_id=""))
        valid = _validate(
            _record(
                review_status=status,
                expiry_or_revalidation_at="2026-12-03T00:00:00Z",
                supersedes_review_record_id="review:previous",
            )
        )

        assert "revalidation_metadata_required_for_stale_review" in missing.failure_reasons
        assert valid.review_record is not None
        assert valid.review_record.revalidation_required is True


def test_unknown_status_requires_attention() -> None:
    decision = _validate(_record(review_status="unknown"))

    assert decision.validation_status == "requires_operator_attention"
    assert decision.requires_operator_attention is True
    assert "unknown_review_status_requires_attention" in decision.failure_reasons


def test_missing_review_identity_denied() -> None:
    decision = _validate(_record(review_record_id="", plugin_id="", plugin_version=""))

    assert decision.validation_status == "failed_validation"
    assert "review_identity_required" in decision.failure_reasons


def test_missing_manifest_or_source_refs_denied_for_non_draft() -> None:
    decision = _validate(_record(manifest_ref="", source_refs=[]))

    assert decision.validation_status == "failed_validation"
    assert "manifest_or_source_ref_required_for_non_draft" in decision.failure_reasons


def test_missing_tenant_namespace_project_scope_denied_for_non_draft() -> None:
    decision = _validate(_record(tenant_scope="", namespace="", project_scope=""))

    assert decision.validation_status == "failed_validation"
    assert "tenant_scope_required_for_non_draft" in decision.failure_reasons
    assert "namespace_required_for_non_draft" in decision.failure_reasons
    assert "project_scope_required_for_non_draft" in decision.failure_reasons


def test_high_risk_capability_requires_security_privacy_and_policy_review_flags() -> None:
    decision = _validate(
        _record(
            declared_capabilities=["plugin_execution"],
            declared_risk_tiers=["plugin_execution"],
            required_security_review=False,
            required_privacy_review=False,
            required_policy_review=False,
        )
    )

    assert decision.validation_status == "blocked"
    assert "security_review_required_for_high_risk_review" in decision.failure_reasons
    assert "privacy_review_required_for_high_risk_review" in decision.failure_reasons
    assert "policy_review_required_for_high_risk_review" in decision.failure_reasons


def test_wildcard_and_hidden_permissions_denied() -> None:
    decision = _validate(
        _record(
            requested_permissions=["*", {"scope": "all"}],
            allowed_operations=["metadata_review", "*"],
            hidden_permissions=["secret"],
        )
    )

    assert "wildcard_permission_denied" in decision.failure_reasons
    assert "wildcard_operation_denied" in decision.failure_reasons
    assert "hidden_permissions_denied" in decision.failure_reasons


def test_plugin_execution_dynamic_import_and_marketplace_publication_rejected() -> None:
    decision = _validate(
        _record(
            plugin_execution_allowed=True,
            dynamic_import_allowed=True,
            marketplace_publication_allowed=True,
        )
    )

    assert "plugin_execution_not_allowed" in decision.failure_reasons
    assert "dynamic_import_not_allowed" in decision.failure_reasons
    assert "marketplace_publication_not_allowed" in decision.failure_reasons


def test_runtime_dispatch_and_grants_rejected() -> None:
    decision = _validate(
        _record(
            runtime_dispatch_allowed=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
        )
    )

    assert "runtime_dispatch_not_allowed" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons


def test_evidence_verifier_success_and_frontend_authority_rejected() -> None:
    decision = _validate(
        _record(
            evidence_provided_by_review=True,
            verifier_success=True,
            verified_success=True,
            frontend_authority=True,
        )
    )

    assert "review_cannot_provide_evidence" in decision.failure_reasons
    assert "review_cannot_mark_verifier_success" in decision.failure_reasons
    assert "frontend_authority_not_allowed" in decision.failure_reasons


def test_manifest_and_integrity_input_claiming_permission_rejected() -> None:
    manifest_decision, integrity_decision, lifecycle_decision, vertical_pack_decision = _related_decisions()
    manifest_decision = replace(manifest_decision, runtime_dispatch_allowed=True, capability_grant=True)
    integrity_decision = replace(integrity_decision, runtime_dispatch_allowed=True, capability_grant=True)

    decision = validate_plugin_review_record(
        _record(),
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
        vertical_pack_decision=vertical_pack_decision,
    )

    assert "manifest_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "manifest_permission_claim_denied" in decision.failure_reasons
    assert "integrity_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "integrity_permission_claim_denied" in decision.failure_reasons


def test_lifecycle_input_claiming_runtime_dispatch_rejected() -> None:
    manifest_decision, integrity_decision, lifecycle_decision, vertical_pack_decision = _related_decisions()
    lifecycle_decision = replace(lifecycle_decision, runtime_dispatch_allowed=True, approval_grant=True)

    decision = validate_plugin_review_record(
        _record(),
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
        vertical_pack_decision=vertical_pack_decision,
    )

    assert "lifecycle_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "lifecycle_permission_claim_denied" in decision.failure_reasons


def test_vertical_pack_input_claiming_dispatch_evidence_or_verifier_success_rejected() -> None:
    manifest_decision, integrity_decision, lifecycle_decision, vertical_pack_decision = _related_decisions()
    vertical_pack_decision = replace(
        vertical_pack_decision,
        runtime_dispatch_allowed=True,
        evidence_provided_by_pack_output=True,
        verifier_success=True,
    )

    decision = validate_plugin_review_record(
        _record(),
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
        vertical_pack_decision=vertical_pack_decision,
    )

    assert "vertical_pack_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "vertical_pack_evidence_claim_denied" in decision.failure_reasons
    assert "vertical_pack_verifier_success_claim_denied" in decision.failure_reasons


def test_legal_security_and_compliance_certification_claim_rejected() -> None:
    decision = _validate(
        _record(
            claims=[
                "legal certification",
                "security certification",
                "compliance certification",
                "official audit result",
                "court-admissible evidence",
            ]
        )
    )

    assert "legal_certification_claim_denied" in decision.failure_reasons
    assert "security_certification_claim_denied" in decision.failure_reasons
    assert "compliance_certification_claim_denied" in decision.failure_reasons
    assert "official_audit_result_claim_denied" in decision.failure_reasons
    assert "court_admissible_claim_denied" in decision.failure_reasons


def test_input_and_supplied_decision_objects_are_not_mutated() -> None:
    record = _record(
        requested_permissions=["*"],
        hidden_permissions=["secret"],
    )
    before = deepcopy(record)
    manifest_decision, integrity_decision, lifecycle_decision, vertical_pack_decision = _related_decisions()

    decision = validate_plugin_review_record(
        record,
        manifest_decision=manifest_decision,
        integrity_decision=integrity_decision,
        lifecycle_decision=lifecycle_decision,
        vertical_pack_decision=vertical_pack_decision,
    )

    assert record == before
    assert manifest_decision.runtime_dispatch_allowed is False
    assert integrity_decision.runtime_dispatch_allowed is False
    assert lifecycle_decision.runtime_dispatch_allowed is False
    assert vertical_pack_decision.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False


def test_review_output_never_sets_runtime_dispatch_allowed_true() -> None:
    decision = _validate(_record())

    assert decision.runtime_dispatch_allowed is False
    assert decision.review_record is not None
    assert decision.review_record.runtime_dispatch_allowed is False


def test_plain_mapping_policy_decision_claiming_permission_rejected() -> None:
    decision = _validate(
        _record(),
        policy_decision={
            "runtime_dispatch_allowed": True,
            "approval_grant": True,
            "capability_grant": True,
            "lease_grant": True,
        },
    )

    assert "policy_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "policy_permission_claim_denied" in decision.failure_reasons


def test_related_decision_with_failure_reasons_blocks_revalidation() -> None:
    bad_lifecycle = SimpleNamespace(
        runtime_dispatch_allowed=False,
        failure_reasons=("transition_not_allowed",),
    )

    decision = _validate(_record(), lifecycle_decision=bad_lifecycle)

    assert "lifecycle_decision_has_failures" in decision.failure_reasons
