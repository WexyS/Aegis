from __future__ import annotations

from copy import deepcopy

from aegis.core.plugin_lifecycle import (
    PLUGIN_LIFECYCLE_CONTRACT_VERSION,
    PLUGIN_LIFECYCLE_EXECUTION_PERMISSION,
    evaluate_plugin_lifecycle_transition,
)
from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import (
    calculate_manifest_checksum,
    evaluate_manifest_drift,
)


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "repo-audit-readonly",
        "pack_name": "Repo Audit Read-only Pack",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "capabilities": ["summarize repository findings"],
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
        evidence_expectations={"kind": "file_write_postcondition"},
        verifier_strategy="filesystem_postcondition",
        rollback_strategy="restore_original_content",
        eval_requirements=["approval-bypass-negative-test"],
        audit_requirements=["journal_ref", "evidence_ref"],
    )
    manifest.update(overrides)
    return manifest


def _valid_manifest_decision(manifest: dict[str, object] | None = None):
    return validate_plugin_manifest(manifest or _manifest())


def _unchanged_integrity(manifest: dict[str, object] | None = None, *, signature_status: str = "unsigned"):
    source = manifest or _manifest()
    return evaluate_manifest_drift(
        source,
        reviewed_checksum=calculate_manifest_checksum(source),
        reviewed_version=str(source["pack_version"]),
        signature_status=signature_status,
    )


def test_discovered_to_registered_metadata_only_allowed_but_non_dispatchable() -> None:
    manifest = _manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "discovered",
        "registered_metadata_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=evaluate_manifest_drift(manifest),
    )

    assert decision.contract_version == PLUGIN_LIFECYCLE_CONTRACT_VERSION
    assert decision.transition_allowed is True
    assert decision.activation_allowed is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PLUGIN_LIFECYCLE_EXECUTION_PERMISSION


def test_registered_to_approved_read_only_requires_valid_manifest_and_integrity() -> None:
    manifest = _manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "registered_metadata_only",
        "approved_for_read_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest),
    )

    assert decision.transition_allowed is True
    assert decision.activation_allowed is False
    assert decision.runtime_dispatch_allowed is False


def test_approved_read_only_to_active_read_only_remains_non_dispatchable() -> None:
    manifest = _manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest),
    )

    assert decision.transition_allowed is True
    assert decision.activation_allowed is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False


def test_approved_proposal_to_active_proposal_remains_non_dispatchable() -> None:
    manifest = _manifest(pack_type="proposal_only_pack")
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_proposal_only",
        "active_proposal_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest),
        eval_present=True,
    )

    assert decision.transition_allowed is True
    assert decision.activation_allowed is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PLUGIN_LIFECYCLE_EXECUTION_PERMISSION


def test_active_action_gated_still_remains_non_dispatchable() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
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

    assert decision.transition_allowed is True
    assert decision.activation_allowed is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.authority is False
    assert decision.execution_permission == PLUGIN_LIFECYCLE_EXECUTION_PERMISSION


def test_active_action_gated_requires_all_action_gates() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
        requested_capability="local_tool_write",
        risk_tier="local_file_write",
    )

    assert decision.transition_allowed is False
    assert "approval_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "lease_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "evidence_expectation_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "verifier_strategy_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "audit_requirements_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "eval_required_for_action_gated_lifecycle" in decision.failure_reasons
    assert "rollback_required_for_mutating_action_gated_lifecycle" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_unknown_state_is_denied() -> None:
    decision = evaluate_plugin_lifecycle_transition(
        "mystery",
        "active_read_only",
        manifest_validation=_valid_manifest_decision(),
        integrity_decision=_unchanged_integrity(),
    )

    assert decision.transition_allowed is False
    assert "unknown_current_state" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_failed_manifest_validation_blocks_activation() -> None:
    invalid_manifest = _manifest(authority=True)
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validate_plugin_manifest(invalid_manifest),
        integrity_decision=_unchanged_integrity(invalid_manifest),
    )

    assert decision.transition_allowed is False
    assert "failed_manifest_validation" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_checksum_mismatch_blocks_activation_and_quarantines() -> None:
    manifest = _manifest()
    integrity = evaluate_manifest_drift(manifest, reviewed_checksum="not-current")
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=integrity,
    )

    assert decision.transition_allowed is False
    assert "integrity_quarantine_required" in decision.failure_reasons
    assert "manifest_quarantine_blocks_activation" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_drift_requiring_review_blocks_active_state() -> None:
    reviewed = _manifest()
    current = _manifest(capability_categories=["local_tool_read", "local_tool_write"])
    integrity = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validate_plugin_manifest(current),
        integrity_decision=integrity,
    )

    assert decision.transition_allowed is False
    assert "integrity_quarantine_required" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_signature_verified_does_not_grant_dispatch() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
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

    assert decision.transition_allowed is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.lease_grant is False


def test_signature_present_unverified_blocks_trusted_action_gated_activation() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_present_unverified"),
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

    assert decision.transition_allowed is False
    assert "trusted_signature_required_for_action_gated_activation" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_revoked_cannot_become_active() -> None:
    decision = evaluate_plugin_lifecycle_transition(
        "revoked",
        "active_read_only",
        manifest_validation=_valid_manifest_decision(),
        integrity_decision=_unchanged_integrity(),
    )

    assert decision.transition_allowed is False
    assert "revoked_cannot_activate" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_quarantined_cannot_become_active() -> None:
    decision = evaluate_plugin_lifecycle_transition(
        "quarantined",
        "active_read_only",
        manifest_validation=_valid_manifest_decision(),
        integrity_decision=_unchanged_integrity(),
    )

    assert decision.transition_allowed is False
    assert "quarantined_cannot_activate" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_deprecated_cannot_become_new_action_gated_activation() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "deprecated",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
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

    assert decision.transition_allowed is False
    assert "deprecated_cannot_become_action_gated" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_enabled_and_installed_flags_do_not_bypass_denial() -> None:
    decision = evaluate_plugin_lifecycle_transition(
        "revoked",
        "active_read_only",
        manifest_validation=_valid_manifest_decision(),
        integrity_decision=_unchanged_integrity(),
        enabled=True,
        installed=True,
    )

    assert decision.transition_allowed is False
    assert "enabled_flag_is_metadata_only" in decision.audit_notes
    assert "installed_flag_is_metadata_only" in decision.audit_notes
    assert decision.runtime_dispatch_allowed is False


def test_approval_alone_does_not_grant_dispatch() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
        requested_capability="local_tool_write",
        risk_tier="local_file_write",
        approval_present=True,
    )

    assert decision.transition_allowed is False
    assert "approval_presence_is_not_dispatch_permission" in decision.audit_notes
    assert decision.runtime_dispatch_allowed is False


def test_lease_alone_does_not_grant_dispatch() -> None:
    manifest = _action_manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
        requested_capability="local_tool_write",
        risk_tier="local_file_write",
        lease_present=True,
    )

    assert decision.transition_allowed is False
    assert "lease_presence_is_not_dispatch_permission" in decision.audit_notes
    assert decision.runtime_dispatch_allowed is False


def test_valid_manifest_unchanged_checksum_signature_verified_still_no_runtime_dispatch() -> None:
    manifest = _manifest()
    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
    )

    assert decision.transition_allowed is True
    assert decision.activation_allowed is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_lifecycle is False
    assert decision.verifier_success is False


def test_vertical_action_gated_requires_namespace_and_tenant_scope() -> None:
    manifest = _action_manifest(
        pack_type="vertical_pack",
        capability_categories=["vertical_pack_write"],
        namespace_scope="glossa",
        tenant_scope="local",
        training_data_policy={"namespace_specific": True},
    )
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
        requested_capability="vertical_pack_write",
        risk_tier="local_file_write",
        approval_present=True,
        lease_present=True,
        evidence_expectation_present=True,
        verifier_strategy_present=True,
        audit_requirements_present=True,
        eval_present=True,
        rollback_present=True,
    )

    assert decision.transition_allowed is False
    assert "namespace_scope_required_for_vertical_pack_lifecycle" in decision.failure_reasons
    assert "tenant_scope_required_for_vertical_pack_lifecycle" in decision.failure_reasons


def test_vertical_action_gated_with_scope_still_does_not_dispatch() -> None:
    manifest = _action_manifest(
        pack_type="vertical_pack",
        capability_categories=["vertical_pack_write"],
        namespace_scope="glossa",
        tenant_scope="local",
        training_data_policy={"namespace_specific": True},
    )
    decision = evaluate_plugin_lifecycle_transition(
        "lease_required",
        "active_action_gated",
        manifest_validation=validate_plugin_manifest(manifest),
        integrity_decision=_unchanged_integrity(manifest, signature_status="signature_verified"),
        requested_capability="vertical_pack_write",
        risk_tier="local_file_write",
        approval_present=True,
        lease_present=True,
        evidence_expectation_present=True,
        verifier_strategy_present=True,
        audit_requirements_present=True,
        eval_present=True,
        rollback_present=True,
        namespace_scope_present=True,
        tenant_scope_present=True,
    )

    assert decision.transition_allowed is True
    assert decision.activation_allowed is True
    assert decision.runtime_dispatch_allowed is False


def test_input_manifest_validation_and_integrity_objects_are_not_mutated() -> None:
    manifest = _manifest()
    before = deepcopy(manifest)
    validation = validate_plugin_manifest(manifest)
    integrity = _unchanged_integrity(manifest)

    decision = evaluate_plugin_lifecycle_transition(
        "approved_for_read_only",
        "active_read_only",
        manifest_validation=validation,
        integrity_decision=integrity,
    )

    assert manifest == before
    assert validation.runtime_dispatch_allowed is False
    assert integrity.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
