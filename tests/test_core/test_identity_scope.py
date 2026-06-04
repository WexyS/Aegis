from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.identity_scope import (
    IDENTITY_SCOPE_EXECUTION_PERMISSION,
    IDENTITY_SCOPE_CONTRACT_VERSION,
    validate_identity_scope_request,
)
from aegis.core.local_model_inventory import validate_local_model_inventory_request


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "identity-scope:aegis:session",
        "scope_id": "scope:aegis:session:1",
        "subject_kind": "local_single_user",
        "subject_ref": "subject:local-single-user",
        "user_ref": "user:local-metadata-only",
        "profile_ref": "profile:local-metadata-only",
        "operator_ref": "operator:local",
        "tenant_ref": "tenant:local",
        "workspace_ref": "workspace:aegis",
        "project_ref": "project:aegis",
        "session_ref": "session:test",
        "machine_ref": "machine:local",
        "local_account_ref": "local-account:metadata-only",
        "namespace": "foundation_identity",
        "privacy_class": "local_private",
        "data_boundary": "local_only",
        "persistence_scope": "session_only",
        "retention_scope": "none",
        "source_refs": [{"ref_id": "synthetic:identity-scope-test", "ref_type": "test_fixture"}],
        "limitations": ["synthetic metadata only"],
        "unknowns": [],
        "human_review_required": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": IDENTITY_SCOPE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _local_model_inventory_metadata_only():
    return validate_local_model_inventory_request(
        {
            "request_id": "identity-scope:local-model-inventory",
            "project_ref": "project:aegis",
            "tenant_scope": "local",
            "namespace": "model_inventory",
            "provider_id": "provider:offline",
            "provider_class": "offline_disabled_provider",
            "provider_status": "disabled_by_policy",
            "privacy_class": "local_only",
            "data_sensitivity_allowed": ["none"],
            "context_policy": {
                "can_receive_secret_like_content": False,
                "can_receive_raw_journal": False,
                "requires_source_refs": True,
                "output_requires_validation": True,
            },
        }
    )


def test_valid_local_single_user_session_only_scope_is_non_authoritative() -> None:
    decision = validate_identity_scope_request(_request())

    assert decision.scope_contract_version == IDENTITY_SCOPE_CONTRACT_VERSION
    assert decision.scope_status == "scope_ready"
    assert decision.persistence_eligibility == "session_only_no_persistent_memory"
    assert decision.cloud_routing_eligibility == "blocked_by_data_boundary"
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == IDENTITY_SCOPE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_identity_scope is False
    assert decision.verifier_success is False
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.cloud_routing_allowed is False
    assert decision.model_call_allowed is False
    assert decision.vector_index_allowed is False


def test_project_scoped_scope_requires_project_ref() -> None:
    decision = validate_identity_scope_request(
        _request(persistence_scope="project_scoped", project_ref=None)
    )

    assert decision.scope_status == "blocked_by_missing_project_ref"
    assert "missing_project_ref" in decision.failure_reasons
    assert decision.context_persistence_allowed is False


def test_valid_project_scoped_metadata_still_does_not_allow_memory_write() -> None:
    decision = validate_identity_scope_request(
        _request(persistence_scope="project_scoped", data_boundary="project_local_only")
    )

    assert decision.scope_status == "scope_ready"
    assert decision.persistence_eligibility == "metadata_ready_policy_required"
    assert decision.memory_write_allowed is False
    assert decision.context_persistence_allowed is False


def test_repository_scope_requires_repository_and_project_ref() -> None:
    missing_repo = validate_identity_scope_request(
        _request(subject_kind="repository", persistence_scope="project_scoped", repository_ref=None)
    )
    missing_project = validate_identity_scope_request(
        _request(
            subject_kind="repository",
            persistence_scope="project_scoped",
            project_ref=None,
            repository_ref="repo:WexyS/Aegis",
        )
    )

    assert missing_repo.scope_status == "blocked_by_missing_repository_ref"
    assert "missing_repository_ref" in missing_repo.failure_reasons
    assert missing_project.scope_status == "blocked_by_missing_project_ref"
    assert "missing_project_ref" in missing_project.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("subject_kind", "missing_subject_kind"),
        ("namespace", "missing_namespace"),
    ],
)
def test_required_identity_fields_block_when_missing(field: str, reason: str) -> None:
    decision = validate_identity_scope_request(_request(**{field: None}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_missing_privacy_or_data_boundary_blocks() -> None:
    decision = validate_identity_scope_request(_request(privacy_class=None, data_boundary=None))

    assert "missing_privacy_or_data_boundary" in decision.failure_reasons
    assert decision.cloud_routing_allowed is False


def test_unknown_identity_is_explicit_and_requires_human_review() -> None:
    decision = validate_identity_scope_request(
        _request(subject_kind="unknown", tenant_ref=None, workspace_ref=None, user_ref=None, profile_ref=None)
    )

    assert decision.scope_status == "clarification_required"
    assert "identity_unknown_requires_human_review" in decision.failure_reasons
    assert "subject_kind" in decision.unknown_identity_fields
    assert "tenant_ref" in decision.unknown_identity_fields
    assert decision.identity_input is not None
    assert decision.identity_input.human_review_required is True


@pytest.mark.parametrize("boundary", ["local_only", "private_repo_local_only", "unknown"])
def test_local_or_unknown_data_boundaries_block_cloud_routing(boundary: str) -> None:
    decision = validate_identity_scope_request(_request(data_boundary=boundary))

    assert decision.cloud_routing_eligibility == "blocked_by_data_boundary"
    assert decision.cloud_routing_allowed is False


def test_missing_project_ref_blocks_project_memory_and_context_requests() -> None:
    decision = validate_identity_scope_request(
        _request(
            project_ref=None,
            persistence_scope="session_only",
            project_memory_requested=True,
            persistent_context_requested=True,
        )
    )

    assert "missing_project_ref" in decision.failure_reasons
    assert decision.memory_write_allowed is False
    assert decision.context_persistence_allowed is False


def test_cross_project_scope_mixing_is_rejected() -> None:
    decision = validate_identity_scope_request(
        _request(related_project_refs=["project:aegis", "project:other"])
    )

    assert decision.scope_status == "blocked_by_cross_project_scope"
    assert "cross_project_scope_mixing_denied" in decision.failure_reasons


def test_aegis_and_ultron_project_refs_cannot_be_merged() -> None:
    decision = validate_identity_scope_request(
        _request(project_ref="project:aegis", merge_project_refs=["project:ultron"])
    )

    assert decision.scope_status == "blocked_by_cross_project_scope"
    assert "aegis_ultron_scope_merge_denied" in decision.failure_reasons
    assert decision.cross_project_scope_allowed is False


def test_user_profile_scoped_metadata_is_not_memory_permission() -> None:
    decision = validate_identity_scope_request(
        _request(
            subject_kind="local_multi_profile_future",
            persistence_scope="user_profile_scoped",
            profile_ref="profile:future",
            data_boundary="local_only",
        )
    )

    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.persistence_eligibility == "metadata_ready_policy_required"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_identity_scope", "identity_scope_cannot_provide_evidence"),
        ("verifier_success", "identity_scope_cannot_mark_verifier_success"),
        ("model_call_allowed", "model_call_not_allowed"),
        ("memory_write_allowed", "memory_write_not_allowed"),
        ("memory_retrieval_allowed", "memory_retrieval_not_allowed"),
        ("vector_index_allowed", "vector_index_not_allowed"),
    ],
)
def test_identity_scope_rejects_authority_and_permission_claims(field: str, reason: str) -> None:
    decision = validate_identity_scope_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.cloud_routing_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("model_call_performed", "model_call_request_denied"),
        ("cloud_route_requested", "cloud_routing_request_denied"),
        ("memory_write_requested", "memory_write_request_denied"),
        ("tool_call_requested", "tool_call_request_denied"),
        ("api_call_requested", "api_call_request_denied"),
        ("mcp_call_requested", "mcp_call_request_denied"),
        ("surveillance_allowed", "surveillance_not_allowed"),
        ("productivity_scoring_allowed", "productivity_scoring_not_allowed"),
        ("external_agent_tracking_allowed", "external_agent_tracking_not_allowed"),
    ],
)
def test_identity_scope_rejects_behavior_and_surveillance_claims(field: str, reason: str) -> None:
    decision = validate_identity_scope_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.surveillance_allowed is False
    assert decision.productivity_scoring_allowed is False
    assert decision.external_agent_tracking_allowed is False


def test_external_agent_scope_is_future_gated_metadata_only() -> None:
    metadata_only = validate_identity_scope_request(
        _request(
            subject_kind="external_agent_future",
            data_boundary="external_agent_observation_future",
            human_review_required=True,
        )
    )
    active = validate_identity_scope_request(
        _request(
            subject_kind="external_agent_future",
            data_boundary="external_agent_observation_future",
            active_external_agent_tracking=True,
        )
    )

    assert metadata_only.scope_status == "scope_ready_requires_human_review"
    assert "external_agent_future_scope" in metadata_only.unknown_identity_fields
    assert metadata_only.external_agent_tracking_allowed is False
    assert "external_agent_tracking_not_allowed" in active.failure_reasons


@pytest.mark.parametrize(
    "field",
    [
        "human_identity_verified",
        "local_account_is_human_identity",
        "os_username_is_human_identity",
        "inferred_human_identity_from_local_account",
    ],
)
def test_local_account_or_os_username_cannot_verify_human_identity(field: str) -> None:
    decision = validate_identity_scope_request(_request(**{field: True}))

    assert "local_account_not_human_identity" in decision.failure_reasons


def test_safe_related_local_model_inventory_cannot_override_identity_scope() -> None:
    related = _local_model_inventory_metadata_only()

    decision = validate_identity_scope_request(
        _request(),
        local_model_inventory_decision=related,
    )

    assert decision.scope_status == "scope_ready"
    assert decision.model_call_allowed is False
    assert decision.memory_write_allowed is False


def test_unsafe_related_decisions_are_rejected() -> None:
    unsafe = SimpleNamespace(
        authority=True,
        runtime_dispatch_allowed=True,
        evidence_provided_by_identity_scope=True,
        verifier_success=True,
        memory_write_allowed=True,
        model_call_performed=True,
    )

    decision = validate_identity_scope_request(
        _request(),
        model_auto_mode_decision=unsafe,
        memory_governance_decision=unsafe,
        repo_audit_decision=unsafe,
    )

    assert decision.scope_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    assert "authority_must_be_false" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "before", "nested": {"value": 1}}])
    related = SimpleNamespace(authority=False, nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_identity_scope_request(
        request,
        mission_control_decision=related,
    )

    assert request == request_before
    assert related.__dict__ == related_before
    assert decision.identity_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.identity_input.project_ref = "project:mutated"  # type: ignore[misc]


def test_output_never_sets_runtime_memory_or_cloud_permissions() -> None:
    decision = validate_identity_scope_request(
        _request(data_boundary="cloud_allowed_later", persistence_scope="project_scoped")
    )

    assert decision.runtime_dispatch_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.cloud_routing_allowed is False
    assert decision.model_call_allowed is False
    assert decision.context_persistence_allowed is False
    assert decision.vector_index_allowed is False
    assert decision.cloud_routing_eligibility == "future_gated_policy_required"
