from __future__ import annotations

from copy import deepcopy

import pytest

from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION, validate_plugin_manifest
from aegis.core.plugin_manifest_integrity import (
    MANIFEST_INTEGRITY_CONTRACT_VERSION,
    MANIFEST_INTEGRITY_EXECUTION_PERMISSION,
    calculate_manifest_checksum,
    compare_manifest_scope_expansion,
    evaluate_manifest_drift,
    normalize_manifest_for_checksum,
)


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "plugin-manifest/1",
        "pack_id": "repo-audit-readonly",
        "pack_name": "Repo Audit Read-only Pack",
        "pack_type": "read_only_pack",
        "pack_version": "0.1.0",
        "source": "local-review-fixture",
        "owner": "aegis",
        "trust_level": "local_review_required",
        "provenance_refs": ["docs/plugin-manifest-type-contract-v1.md"],
        "capabilities": ["summarize repository findings"],
        "capability_categories": ["local_tool_read"],
        "risk_tiers": ["local_state_read"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": ["read_file", "search_files"],
        "model_requirements": [],
        "memory_namespaces": ["project"],
        "external_api_scopes": [],
        "audit_requirements": ["source_refs", "staleness"],
    }
    manifest.update(overrides)
    return manifest


def test_checksum_is_deterministic_for_equivalent_manifest_key_order() -> None:
    first = _manifest()
    second = {
        "pack_version": "0.1.0",
        "pack_type": "read_only_pack",
        "pack_name": "Repo Audit Read-only Pack",
        "pack_id": "repo-audit-readonly",
        "manifest_version": "plugin-manifest/1",
        "source": "local-review-fixture",
        "owner": "aegis",
        "trust_level": "local_review_required",
        "provenance_refs": ["docs/plugin-manifest-type-contract-v1.md"],
        "capabilities": ["summarize repository findings"],
        "capability_categories": ["local_tool_read"],
        "risk_tiers": ["local_state_read"],
        "disabled_by_default": True,
        "authority": False,
        "execution_permission": PLUGIN_MANIFEST_EXECUTION_PERMISSION,
        "allowed_tools": ["read_file", "search_files"],
        "model_requirements": [],
        "memory_namespaces": ["project"],
        "external_api_scopes": [],
        "audit_requirements": ["source_refs", "staleness"],
    }

    assert normalize_manifest_for_checksum(first) == normalize_manifest_for_checksum(second)
    assert calculate_manifest_checksum(first) == calculate_manifest_checksum(second)


def test_checksum_helper_does_not_mutate_input() -> None:
    manifest = _manifest(reviewed_manifest_checksum="old", signature_status="signature_verified")
    before = deepcopy(manifest)

    checksum = calculate_manifest_checksum(manifest)

    assert len(checksum) == 64
    assert manifest == before


def test_checksum_excludes_review_and_signature_bookkeeping_fields() -> None:
    manifest = _manifest()
    with_bookkeeping = _manifest(
        manifest_checksum="stored",
        reviewed_manifest_checksum="reviewed",
        reviewed_at="2026-06-01T00:00:00Z",
        review_status="reviewed",
        signature="abc",
        signature_status="signature_present_unverified",
        signed_by="operator",
    )

    assert calculate_manifest_checksum(manifest) == calculate_manifest_checksum(with_bookkeeping)


def test_non_json_serializable_manifest_value_is_rejected() -> None:
    manifest = _manifest(callback=lambda: None)

    with pytest.raises(TypeError):
        calculate_manifest_checksum(manifest)


def test_no_review_record_requires_review_but_does_not_quarantine() -> None:
    decision = evaluate_manifest_drift(_manifest())

    assert decision.contract_version == MANIFEST_INTEGRITY_CONTRACT_VERSION
    assert decision.decision_state == "no_review_record"
    assert decision.review_required is True
    assert decision.quarantine_required is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == MANIFEST_INTEGRITY_EXECUTION_PERMISSION


def test_unchanged_reviewed_manifest_is_non_dispatchable() -> None:
    manifest = _manifest()
    checksum = calculate_manifest_checksum(manifest)

    decision = evaluate_manifest_drift(
        manifest,
        reviewed_checksum=checksum,
        reviewed_version="0.1.0",
    )

    assert decision.decision_state == "unchanged"
    assert decision.review_required is False
    assert decision.quarantine_required is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False


def test_manifest_changed_after_review_requires_quarantine_review() -> None:
    reviewed = _manifest()
    current = _manifest(pack_name="Repo Audit Read-only Pack Updated")
    reviewed_checksum = calculate_manifest_checksum(reviewed)

    decision = evaluate_manifest_drift(current, reviewed_checksum=reviewed_checksum)

    assert decision.decision_state == "checksum_mismatch_requires_quarantine"
    assert decision.review_required is True
    assert decision.quarantine_required is True
    assert "checksum_mismatch" in decision.quarantine_reasons
    assert decision.runtime_dispatch_allowed is False


def test_version_change_requires_review() -> None:
    reviewed = _manifest()
    current = _manifest(pack_version="0.2.0")
    reviewed_checksum = calculate_manifest_checksum(current)

    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=reviewed_checksum,
        reviewed_version="0.1.0",
    )

    assert decision.decision_state == "version_changed_requires_review"
    assert decision.review_required is True
    assert decision.quarantine_required is True
    assert "version_drift" in decision.quarantine_reasons


def test_checksum_mismatch_requires_quarantine() -> None:
    decision = evaluate_manifest_drift(_manifest(), reviewed_checksum="not-the-current-checksum")

    assert decision.decision_state == "checksum_mismatch_requires_quarantine"
    assert decision.quarantine_required is True
    assert "checksum_mismatch" in decision.quarantine_reasons


def test_unsupported_checksum_algorithm_is_blocked() -> None:
    decision = evaluate_manifest_drift(_manifest(), checksum_algorithm="md5")

    assert decision.decision_state == "unsupported_algorithm"
    assert decision.review_required is True
    assert decision.quarantine_required is True
    assert "unsupported_algorithm" in decision.failure_reasons
    assert "algorithm_unsupported" in decision.quarantine_reasons


def test_unsigned_manifest_is_not_trusted_and_not_permission() -> None:
    manifest = _manifest()
    checksum = calculate_manifest_checksum(manifest)

    decision = evaluate_manifest_drift(manifest, reviewed_checksum=checksum, signature_status="unsigned")

    assert decision.signature_status == "unsigned"
    assert decision.signature_trusted is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == MANIFEST_INTEGRITY_EXECUTION_PERMISSION


def test_signature_present_unverified_is_not_trusted() -> None:
    decision = evaluate_manifest_drift(_manifest(), signature_status="signature_present_unverified")

    assert decision.signature_status == "signature_present_unverified"
    assert decision.signature_trusted is False
    assert decision.runtime_dispatch_allowed is False


def test_signature_verified_still_grants_no_permission() -> None:
    manifest = _manifest()
    checksum = calculate_manifest_checksum(manifest)

    decision = evaluate_manifest_drift(
        manifest,
        reviewed_checksum=checksum,
        signature_status="signature_verified",
    )

    assert decision.signature_trusted is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False


def test_invalid_revoked_or_expired_signature_blocks_activation() -> None:
    for status, reason in (
        ("signature_invalid", "signature_invalid"),
        ("signer_untrusted", "signer_untrusted"),
        ("signature_expired", "signature_expired"),
        ("signature_revoked", "signature_revoked"),
    ):
        decision = evaluate_manifest_drift(_manifest(), signature_status=status)

        assert decision.decision_state == "blocked"
        assert decision.review_required is True
        assert decision.quarantine_required is True
        assert reason in decision.quarantine_reasons
        assert decision.runtime_dispatch_allowed is False


def test_added_capability_and_risk_tier_require_review() -> None:
    reviewed = _manifest()
    current = _manifest(
        capability_categories=["local_tool_read", "local_tool_write"],
        risk_tiers=["local_state_read", "local_file_write"],
    )

    expansion = compare_manifest_scope_expansion(reviewed, current)
    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )

    assert expansion.expansion_detected is True
    assert expansion.added_capabilities == ("local_tool_write",)
    assert expansion.added_risk_tiers == ("local_file_write",)
    assert "capability_expansion" in decision.expansion_reasons
    assert "risk_tier_expansion" in decision.expansion_reasons
    assert decision.quarantine_required is True
    assert decision.runtime_dispatch_allowed is False


def test_added_tool_model_memory_and_api_scope_require_review() -> None:
    reviewed = _manifest()
    current = _manifest(
        allowed_tools=["read_file", "search_files", "write_file"],
        model_requirements=["lm_studio_local"],
        memory_namespaces=["project", "tenant"],
        external_api_scopes=["pack_read"],
    )

    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )

    assert "new_tool_reference" in decision.expansion_reasons
    assert "new_model_reference" in decision.expansion_reasons
    assert "new_memory_namespace" in decision.expansion_reasons
    assert "new_external_api_scope" in decision.expansion_reasons
    assert decision.quarantine_required is True
    assert decision.runtime_dispatch_allowed is False


def test_scope_expansion_requires_review() -> None:
    reviewed = _manifest(tenant_scope="local", project_scope="aegis")
    current = _manifest(tenant_scope="all", project_scope="*")

    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )

    assert "tenant_scope_expansion" in decision.expansion_reasons
    assert "scope_expansion" in decision.expansion_reasons
    assert decision.quarantine_required is True


def test_changed_disabled_authority_or_execution_permission_is_quarantined() -> None:
    reviewed = _manifest()
    current = _manifest(
        disabled_by_default=False,
        authority=True,
        execution_permission="granted",
    )

    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )

    assert "disabled_by_default_changed_to_false" in decision.expansion_reasons
    assert "authority_changed_to_true" in decision.expansion_reasons
    assert "execution_permission_changed" in decision.expansion_reasons
    assert decision.quarantine_required is True
    assert decision.runtime_dispatch_allowed is False


def test_vertical_pack_identity_override_requires_quarantine() -> None:
    reviewed = _manifest(
        pack_type="vertical_pack",
        capability_categories=["vertical_pack_read"],
        risk_tiers=["read_only"],
        namespace_scope="glossa",
        tenant_scope="local",
        training_data_policy={"namespace_specific": True},
    )
    current = dict(reviewed)
    current["defines_aegis_platform_identity"] = True

    decision = evaluate_manifest_drift(
        current,
        reviewed_checksum=calculate_manifest_checksum(current),
        reviewed_manifest=reviewed,
    )

    assert "platform_identity_override_attempt" in decision.expansion_reasons
    assert "platform_identity_override_attempt" in decision.quarantine_reasons
    assert decision.quarantine_required is True
    assert decision.runtime_dispatch_allowed is False


def test_quarantined_manifest_cannot_dispatch_or_grant_authority() -> None:
    decision = evaluate_manifest_drift(
        _manifest(authority=True),
        reviewed_checksum=calculate_manifest_checksum(_manifest(authority=True)),
        reviewed_manifest=_manifest(),
    )

    assert decision.quarantine_required is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_pack_output is False
    assert decision.verifier_success is False


def test_invalid_manifest_requires_quarantine() -> None:
    decision = evaluate_manifest_drift(None)

    assert decision.decision_state == "invalid_manifest_requires_quarantine"
    assert decision.review_required is True
    assert decision.quarantine_required is True
    assert "invalid_manifest" in decision.quarantine_reasons
    assert decision.runtime_dispatch_allowed is False


def test_validate_plugin_manifest_still_handles_manifest_independently() -> None:
    manifest = _manifest()
    drift = evaluate_manifest_drift(manifest)
    validation = validate_plugin_manifest(manifest)

    assert drift.runtime_dispatch_allowed is False
    assert validation.runtime_dispatch_allowed is False
    assert validation.failure_reasons == ()
