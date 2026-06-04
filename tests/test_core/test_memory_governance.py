from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.identity_scope import validate_identity_scope_request
from aegis.core.memory_governance import (
    MEMORY_GOVERNANCE_CONTRACT_VERSION,
    MEMORY_GOVERNANCE_EXECUTION_PERMISSION,
    validate_memory_governance_request,
)


def _identity_scope(**overrides: object):
    request: dict[str, object] = {
        "request_id": "identity:memory:test",
        "scope_id": "scope:memory:test",
        "subject_kind": "project",
        "subject_ref": "subject:project:aegis",
        "user_ref": "user:local-metadata-only",
        "profile_ref": "profile:local-metadata-only",
        "tenant_ref": "tenant:local",
        "workspace_ref": "workspace:aegis",
        "project_ref": "project:aegis",
        "repository_ref": "repo:WexyS/Aegis",
        "session_ref": "session:test",
        "namespace": "memory_governance",
        "privacy_class": "local_private",
        "data_boundary": "project_local_only",
        "persistence_scope": "project_scoped",
    }
    request.update(overrides)
    return validate_identity_scope_request(request)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "memory-governance:aegis:1",
        "memory_id": "memory:proposal:1",
        "memory_category": "temporary_scratch",
        "memory_status": "proposed",
        "memory_scope": "session_only",
        "operation": "propose_write",
        "identity_scope_ref": "scope:memory:test",
        "project_ref": "project:aegis",
        "repository_ref": "repo:WexyS/Aegis",
        "session_ref": "session:test",
        "tenant_ref": "tenant:local",
        "workspace_ref": "workspace:aegis",
        "profile_ref": "profile:local-metadata-only",
        "user_ref": "user:local-metadata-only",
        "namespace": "memory_governance",
        "data_boundary": "local_only",
        "privacy_class": "local_private",
        "sensitivity_class": "private",
        "retention_policy": "no_persistence",
        "source_refs": [{"ref_id": "synthetic:memory-test", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "synthetic:caller-supplied", "ref_type": "test_fixture"}],
        "confidence": 0.5,
        "freshness": "caller_supplied",
        "limitations": ["synthetic metadata only"],
        "unknowns": [],
        "human_review_required": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": MEMORY_GOVERNANCE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related: object):
    return validate_memory_governance_request(request, **related)


def test_valid_session_only_temporary_scratch_proposal_is_non_authoritative() -> None:
    decision = _validate(_request())

    assert decision.contract_version == MEMORY_GOVERNANCE_CONTRACT_VERSION
    assert decision.governance_status == "proposal_ready"
    assert decision.operation_status == "proposed_only"
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == MEMORY_GOVERNANCE_EXECUTION_PERMISSION
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.memory_delete_allowed is False
    assert decision.memory_export_allowed is False
    assert decision.memory_write_performed is False
    assert decision.vector_index_touched is False
    assert decision.embedding_generated is False
    assert decision.model_call_performed is False
    assert decision.evidence_provided_by_memory_governance is False
    assert decision.verifier_success is False


def test_project_scoped_project_preference_requires_project_ref() -> None:
    decision = _validate(
        _request(
            memory_category="project_preference",
            memory_scope="project_scoped",
            project_ref=None,
            retention_policy="project_ttl",
        )
    )

    assert "missing_project_ref" in decision.failure_reasons
    assert decision.governance_status == "blocked_by_missing_scope"
    assert decision.memory_write_allowed is False


def test_valid_project_scoped_project_preference_consumes_identity_scope() -> None:
    decision = _validate(
        _request(
            memory_category="project_preference",
            memory_scope="project_scoped",
            retention_policy="project_ttl",
        ),
        identity_scope_decision=_identity_scope(),
    )

    assert decision.governance_status == "proposal_ready"
    assert decision.operation_status == "proposed_only"
    assert decision.memory_write_allowed is False


def test_repository_scoped_repo_memory_requires_repo_and_project_ref() -> None:
    missing_repo = _validate(
        _request(memory_category="repo_memory", memory_scope="repository_scoped", repository_ref=None)
    )
    missing_project = _validate(
        _request(memory_category="repo_memory", memory_scope="repository_scoped", project_ref=None)
    )

    assert "missing_repository_ref" in missing_repo.failure_reasons
    assert "missing_project_ref" in missing_project.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("memory_category", "missing_memory_category"),
        ("operation", "missing_operation"),
        ("memory_scope", "missing_memory_scope"),
        ("namespace", "missing_namespace"),
    ],
)
def test_required_memory_fields_block_when_missing(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: None}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_missing_privacy_or_sensitivity_blocks() -> None:
    decision = _validate(_request(privacy_class=None, sensitivity_class=None))

    assert "missing_privacy_or_sensitivity" in decision.failure_reasons


def test_durable_memory_without_provenance_or_source_refs_blocks() -> None:
    decision = _validate(
        _request(
            memory_scope="project_scoped",
            retention_policy="project_ttl",
            source_refs=[],
            provenance=[],
        )
    )

    assert "missing_provenance_for_durable_memory" in decision.failure_reasons


def test_session_only_requires_session_ref() -> None:
    decision = _validate(_request(session_ref=None))

    assert "missing_session_ref" in decision.failure_reasons


def test_user_profile_scoped_requires_explicit_profile_and_user_refs() -> None:
    decision = _validate(
        _request(memory_scope="user_profile_scoped", profile_ref=None, user_ref=None)
    )

    assert "missing_user_profile_scope" in decision.failure_reasons


def test_unknown_identity_blocks_persistent_memory() -> None:
    identity = _identity_scope(subject_kind="unknown")

    decision = _validate(
        _request(memory_scope="project_scoped", retention_policy="project_ttl"),
        identity_scope_decision=identity,
    )

    assert "identity_scope_not_ready" in decision.failure_reasons
    assert decision.governance_status == "blocked_by_identity_scope"


def test_local_account_or_os_username_is_not_human_identity() -> None:
    decision = _validate(_request(local_account_is_human_identity=True))

    assert "local_account_not_human_identity" in decision.failure_reasons


def test_cross_project_memory_mixing_rejected() -> None:
    decision = _validate(_request(related_project_refs=["project:aegis", "project:other"]))

    assert "cross_project_memory_mixing_denied" in decision.failure_reasons
    assert decision.governance_status == "blocked_by_cross_project_scope"


def test_aegis_and_ultron_memory_scopes_cannot_merge() -> None:
    decision = _validate(_request(project_ref="project:aegis", merge_project_refs=["project:ultron"]))

    assert "aegis_ultron_memory_merge_denied" in decision.failure_reasons


def test_identity_scope_decision_cannot_grant_memory_permissions() -> None:
    identity = _identity_scope()

    decision = _validate(_request(), identity_scope_decision=identity)

    assert decision.governance_status == "proposal_ready"
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False


@pytest.mark.parametrize("sensitivity", ["secret_like", "credential_like"])
def test_secret_and_credential_memory_persistence_blocked(sensitivity: str) -> None:
    decision = _validate(
        _request(
            memory_scope="project_scoped",
            retention_policy="project_ttl",
            sensitivity_class=sensitivity,
        )
    )

    assert "sensitive_secret_memory_blocked" in decision.failure_reasons


def test_unknown_sensitivity_blocks_persistence() -> None:
    decision = _validate(
        _request(
            memory_scope="project_scoped",
            retention_policy="project_ttl",
            sensitivity_class="unknown",
        )
    )

    assert "unknown_sensitivity_blocks_persistence" in decision.failure_reasons


def test_personal_private_memory_requires_confirmation() -> None:
    decision = _validate(_request(memory_category="personal_private_memory", explicit_user_confirmation=False))

    assert "personal_private_memory_requires_confirmation" in decision.failure_reasons


def test_health_or_personal_sensitive_requires_human_review() -> None:
    decision = _validate(_request(sensitivity_class="health_or_personal_sensitive", human_review_required=False))

    assert "health_or_personal_sensitive_requires_review" in decision.failure_reasons


def test_model_inferred_personal_memory_cannot_be_active_without_confirmation() -> None:
    decision = _validate(
        _request(
            memory_category="personal_private_memory",
            memory_status="active",
            inferred_by_model=True,
            explicit_user_confirmation=False,
        )
    )

    assert "personal_private_memory_requires_confirmation" in decision.failure_reasons
    assert "model_inferred_personal_memory_requires_confirmation" in decision.failure_reasons


@pytest.mark.parametrize(
    ("operation", "performed_field"),
    [
        ("propose_write", "memory_write_performed"),
        ("propose_retrieve", "memory_retrieval_performed"),
        ("propose_delete", "memory_delete_performed"),
        ("propose_forget", "memory_delete_performed"),
        ("propose_export", "memory_export_performed"),
    ],
)
def test_memory_operation_proposals_do_not_perform_behavior(operation: str, performed_field: str) -> None:
    clean = _validate(_request(operation=operation))
    claimed = _validate(_request(operation=operation, **{performed_field: True}))

    assert clean.operation_status == "proposed_only"
    assert clean.memory_write_performed is False
    assert clean.memory_retrieval_performed is False
    assert clean.memory_delete_performed is False
    assert clean.memory_export_performed is False
    assert performed_field.replace("_performed", "_request_denied") in claimed.failure_reasons


def test_rebuild_index_future_does_not_touch_vector_db() -> None:
    decision = _validate(_request(operation="propose_rebuild_index_future"))

    assert decision.governance_status == "future_gated"
    assert decision.operation_status == "future_gated_no_vector_touch"
    assert decision.vector_index_touched is False


@pytest.mark.parametrize("status", ["stale", "quarantined", "superseded", "deleted", "expired"])
def test_non_current_memory_status_cannot_be_treated_as_active_current(status: str) -> None:
    decision = _validate(_request(memory_status=status, treat_as_current=True))

    assert "non_current_memory_cannot_be_current" in decision.failure_reasons
    assert decision.current_memory_candidate is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_memory_governance", "memory_governance_cannot_provide_evidence"),
        ("verifier_success", "memory_governance_cannot_mark_verifier_success"),
        ("model_call_requested", "model_call_request_denied"),
        ("cloud_sync_requested", "cloud_sync_request_denied"),
        ("vector_index_requested", "vector_index_request_denied"),
        ("memory_write_allowed", "memory_write_not_allowed"),
        ("memory_retrieval_allowed", "memory_retrieval_not_allowed"),
    ],
)
def test_memory_governance_rejects_authority_and_permission_claims(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("vector_index_touched", "vector_index_request_denied"),
        ("embedding_generated", "embedding_generation_request_denied"),
        ("reranking_performed", "reranking_request_denied"),
        ("model_call_performed", "model_call_request_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("api_call_requested", "api_call_request_denied"),
        ("mcp_call_requested", "mcp_call_request_denied"),
        ("tool_call_requested", "tool_call_request_denied"),
        ("surveillance_allowed", "surveillance_not_allowed"),
        ("productivity_scoring_allowed", "productivity_scoring_not_allowed"),
    ],
)
def test_memory_governance_rejects_behavior_and_scoring_claims(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.surveillance_allowed is False
    assert decision.productivity_scoring_allowed is False


@pytest.mark.parametrize(
    "source_field",
    [
        "source_is_model_output",
        "source_is_web",
        "source_is_mcp",
        "source_is_tool",
        "source_is_frontend",
    ],
)
def test_low_trust_sources_are_preserved_but_not_truth(source_field: str) -> None:
    decision = _validate(_request(**{source_field: True}, confidence=0.2, freshness="unknown"))

    assert decision.governance_status == "proposal_requires_human_review"
    assert decision.source_trust == "lower_trust_source_material"
    assert source_field in decision.memory_input.low_trust_sources
    assert decision.evidence_provided_by_memory_governance is False
    assert decision.verifier_success is False


def test_runtime_evidence_refs_are_source_refs_but_memory_is_not_evidence() -> None:
    decision = _validate(_request(source_is_runtime_evidence=True))

    assert decision.governance_status == "proposal_ready"
    assert decision.evidence_provided_by_memory_governance is False
    assert decision.verifier_success is False


def test_unsafe_related_decisions_are_rejected() -> None:
    unsafe = SimpleNamespace(
        authority=True,
        runtime_dispatch_allowed=True,
        memory_write_allowed=True,
        evidence_provided_by_memory_governance=True,
        verifier_success=True,
        model_call_performed=True,
        api_call_requested=True,
    )

    decision = _validate(
        _request(),
        identity_scope_decision=unsafe,
        model_auto_mode_decision=unsafe,
        repo_audit_decision=unsafe,
    )

    assert decision.governance_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    assert "authority_must_be_false" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "before", "nested": {"value": 1}}])
    related = SimpleNamespace(authority=False, nested={"value": 1})
    before_request = deepcopy(request)
    before_related = deepcopy(related.__dict__)

    decision = _validate(request, mission_control_decision=related)

    assert request == before_request
    assert related.__dict__ == before_related
    assert decision.memory_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.memory_input.project_ref = "project:mutated"  # type: ignore[misc]


def test_output_never_sets_runtime_or_memory_permissions() -> None:
    decision = _validate(_request(operation="propose_retrieve"))

    assert decision.runtime_dispatch_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.memory_delete_allowed is False
    assert decision.memory_export_allowed is False
    assert decision.model_call_performed is False
    assert decision.cloud_sync_performed is False
    assert decision.data_sent_external is False
    assert decision.mutation_performed is False
