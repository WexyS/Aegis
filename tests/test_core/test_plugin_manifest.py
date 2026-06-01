from __future__ import annotations

from copy import deepcopy

from aegis.core.plugin_manifest import (
    PLUGIN_MANIFEST_CONTRACT_VERSION,
    PLUGIN_MANIFEST_EXECUTION_PERMISSION,
    validate_plugin_manifest,
)


def _base_manifest(**overrides: object) -> dict[str, object]:
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


def test_valid_read_only_manifest_is_metadata_only_not_dispatchable() -> None:
    decision = validate_plugin_manifest(_base_manifest())

    assert decision.contract_version == PLUGIN_MANIFEST_CONTRACT_VERSION
    assert decision.manifest_present is True
    assert decision.pack_id == "repo-audit-readonly"
    assert decision.pack_type == "read_only_pack"
    assert decision.activation_status == "metadata_only"
    assert decision.failure_reasons == ()
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PLUGIN_MANIFEST_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True


def test_missing_manifest_is_failed_validation_and_non_dispatchable() -> None:
    decision = validate_plugin_manifest(None)

    assert decision.manifest_present is False
    assert decision.activation_status == "failed_validation"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PLUGIN_MANIFEST_EXECUTION_PERMISSION
    assert "missing_manifest" in decision.failure_reasons


def test_required_fields_are_required_for_review() -> None:
    manifest = _base_manifest()
    del manifest["pack_id"]

    decision = validate_plugin_manifest(manifest)

    assert decision.activation_status == "failed_validation"
    assert decision.runtime_dispatch_allowed is False
    assert "missing_required_field" in decision.failure_reasons


def test_enabled_or_installed_state_cannot_grant_permission() -> None:
    decision = validate_plugin_manifest(_base_manifest(enabled=True, installed=True))

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "enabled_state_cannot_grant_permission" in decision.failure_reasons
    assert "installed_state_cannot_grant_permission" in decision.failure_reasons


def test_authority_or_grants_are_rejected() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            authority=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
            runtime_dispatch_allowed=True,
        )
    )

    assert decision.activation_status == "blocked"
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert "authority_must_be_false" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons
    assert "runtime_dispatch_not_allowed" in decision.failure_reasons


def test_execution_permission_must_be_not_granted_by_manifest() -> None:
    decision = validate_plugin_manifest(_base_manifest(execution_permission="granted"))

    assert decision.activation_status == "blocked"
    assert decision.execution_permission == PLUGIN_MANIFEST_EXECUTION_PERMISSION
    assert "execution_permission_not_granted_by_manifest_required" in decision.failure_reasons


def test_unknown_capability_and_risk_are_denied() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            capability_categories=["hallucinated_capability"],
            risk_tiers=["unknown_risk"],
        )
    )

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "unknown_capability" in decision.failure_reasons
    assert "unknown_risk_tier" in decision.failure_reasons


def test_risk_tier_must_match_capability_category() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            capability_categories=["context_compilation"],
            risk_tiers=["local_file_write"],
            approval_required=True,
            lease_required=True,
            evidence_expectations={"kind": "mutation"},
            verifier_strategy="postcondition",
            rollback_strategy="restore",
            eval_requirements=["policy-bypass"],
        )
    )

    assert decision.runtime_dispatch_allowed is False
    assert "risk_tier_not_allowed_for_capability" in decision.failure_reasons


def test_unknown_tool_model_memory_and_api_scope_are_denied() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            allowed_tools=["imaginary_tool"],
            model_requirements=["imaginary_model"],
            memory_namespaces=["imaginary_namespace"],
            external_api_scopes=["imaginary_scope"],
        )
    )

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "unknown_tool" in decision.failure_reasons
    assert "unknown_model_provider" in decision.failure_reasons
    assert "unknown_memory_namespace" in decision.failure_reasons
    assert "unknown_external_api_scope" in decision.failure_reasons


def test_unresolved_unknown_references_remain_blocked_metadata_not_permission() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            allowed_tools=[{"tool_id": "future_tool", "status": "unresolved"}],
            model_requirements=[{"provider_id": "future_provider", "status": "blocked"}],
        )
    )

    assert decision.activation_status == "metadata_only"
    assert decision.runtime_dispatch_allowed is False
    assert "unknown_tool" not in decision.failure_reasons
    assert "unknown_model_provider" not in decision.failure_reasons


def test_wildcard_scopes_are_denied_by_default() -> None:
    decision = validate_plugin_manifest(_base_manifest(allowed_tools=["*"]))

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "wildcard_scope_denied" in decision.failure_reasons


def test_side_effecting_pack_requires_approval_lease_evidence_verifier_audit_and_eval() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            pack_type="approval_gated_action_pack",
            capability_categories=["local_tool_write"],
            risk_tiers=["local_file_write"],
        )
    )

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "approval_required_for_side_effecting_pack" in decision.failure_reasons
    assert "lease_required_for_side_effecting_pack" in decision.failure_reasons
    assert "missing_evidence_expectation" in decision.failure_reasons
    assert "missing_verifier_strategy" in decision.failure_reasons
    assert "missing_rollback_strategy" in decision.failure_reasons
    assert "missing_eval_requirements" in decision.failure_reasons


def test_side_effecting_pack_with_metadata_still_does_not_dispatch() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
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
    )

    assert decision.failure_reasons == ()
    assert decision.activation_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PLUGIN_MANIFEST_EXECUTION_PERMISSION


def test_vertical_pack_requires_namespace_and_namespace_specific_training_policy() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            pack_id="glossa-pack",
            pack_type="vertical_pack",
            capability_categories=["vertical_pack_read"],
            risk_tiers=["read_only"],
        )
    )

    assert decision.activation_status == "blocked"
    assert decision.runtime_dispatch_allowed is False
    assert "vertical_pack_requires_namespace_and_tenant_scope" in decision.failure_reasons
    assert "vertical_pack_requires_namespace_specific_training_policy" in decision.failure_reasons


def test_vertical_pack_cannot_define_aegis_platform_identity() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            pack_id="glossa-pack",
            pack_type="vertical_pack",
            capability_categories=["vertical_pack_read"],
            risk_tiers=["read_only"],
            namespace_scope="glossa",
            tenant_scope="local",
            training_data_policy={"namespace_specific": True},
            defines_aegis_platform_identity=True,
        )
    )

    assert decision.runtime_dispatch_allowed is False
    assert "pack_cannot_define_aegis_platform_identity" in decision.failure_reasons


def test_pack_output_cannot_create_evidence_or_verifier_success() -> None:
    decision = validate_plugin_manifest(
        _base_manifest(
            evidence_provided_by_pack_output=True,
            verifier_success=True,
        )
    )

    assert decision.evidence_provided_by_pack_output is False
    assert decision.verifier_success is False
    assert decision.runtime_dispatch_allowed is False
    assert "pack_output_cannot_provide_evidence" in decision.failure_reasons
    assert "pack_output_cannot_mark_verifier_success" in decision.failure_reasons


def test_context_memory_model_api_tool_frontend_permission_sources_are_denied() -> None:
    for field in (
        "context_derived_permission",
        "memory_derived_permission",
        "model_derived_permission",
        "api_derived_permission",
        "tool_derived_permission",
        "frontend_derived_permission",
        "plugin_derived_permission",
        "skill_derived_permission",
    ):
        decision = validate_plugin_manifest(_base_manifest(**{field: True}))

        assert decision.runtime_dispatch_allowed is False
        assert f"{field}_denied" in decision.failure_reasons


def test_permission_source_from_untrusted_surface_is_denied() -> None:
    decision = validate_plugin_manifest(_base_manifest(permission_source="context_compiler"))

    assert decision.runtime_dispatch_allowed is False
    assert "context_compiler_permission_source_denied" in decision.failure_reasons


def test_validator_does_not_mutate_manifest_input() -> None:
    manifest = _base_manifest(
        model_requirements=[{"provider_id": "lm_studio_local", "status": "unresolved"}],
        memory_namespaces=["project"],
    )
    before = deepcopy(manifest)

    decision = validate_plugin_manifest(manifest)

    assert manifest == before
    assert decision.runtime_dispatch_allowed is False
