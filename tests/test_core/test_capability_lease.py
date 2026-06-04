from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.capability_lease import (
    CAPABILITY_LEASE_EXECUTION_PERMISSION,
    CAPABILITY_LEASE_VERSION,
    validate_capability_lease_request,
)


def _policy(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        policy_outcome="allowed_metadata_only",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_policy_extension",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        verifier_success=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _identity(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        scope_status="scope_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_identity_scope",
        authority=False,
        approval_grant=False,
        lease_grant=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _memory(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        governance_status="governance_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_memory_governance",
        memory_write_allowed=False,
        memory_retrieval_allowed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _context(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        policy_status="proposal_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_context_policy",
        context_retrieval_allowed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _provider(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        readiness_status="metadata_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_local_provider_health",
        provider_probe_allowed=False,
        endpoint_probed=False,
        model_call_performed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _auto_mode(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        selection_mode="local_model_candidate",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_model_auto_mode",
        model_call_allowed=False,
        provider_selected=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _repo_audit(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        readiness_status="readiness_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_repo_audit",
        repo_file_read_allowed=False,
        repo_file_read_performed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "lease:aegis:1",
        "lease_id": "lease:candidate:1",
        "lease_subject": "tool_action_future",
        "lease_scope": "tool_scoped",
        "risk_tier": "metadata_only",
        "namespace": "capability_lease",
        "allowed_tools": ["read_only_preview"],
        "max_duration_seconds": 600,
        "max_actions": 3,
        "requires_evidence_plan": True,
        "requires_verifier_plan": True,
        "requires_negative_evidence_on_failure": True,
        "requires_secret_safe_logging": True,
        "revocable": True,
        "source_refs": [{"ref_id": "synthetic:lease", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": CAPABILITY_LEASE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related: object):
    if "policy_extension_decision" not in related:
        related["policy_extension_decision"] = _policy()
    return validate_capability_lease_request(request, **related)


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == CAPABILITY_LEASE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.lease_active is False
    assert decision.lease_created is False
    assert decision.lease_used is False
    assert decision.evidence_provided_by_lease is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.model_call_allowed is False
    assert decision.provider_probe_allowed is False
    assert decision.repo_file_read_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.memory_retrieval_allowed is False
    assert decision.context_retrieval_allowed is False
    assert decision.web_query_allowed is False
    assert decision.plugin_execution_allowed is False
    assert decision.playbook_execution_allowed is False
    assert decision.rollback_execution_allowed is False
    assert decision.external_agent_tracking_allowed is False
    assert decision.data_sent_external is False


def test_valid_metadata_only_lease_candidate_is_proposal_only() -> None:
    decision = _validate(_request())

    assert decision.contract_version == CAPABILITY_LEASE_VERSION
    assert decision.lifecycle_state == "proposed"
    assert decision.lease_subject == "tool_action_future"
    assert decision.lease_scope == "tool_scoped"
    assert decision.risk_tier == "metadata_only"
    _assert_non_authority(decision)


def test_valid_read_only_session_scoped_candidate_requires_session_ref() -> None:
    decision = _validate(
        _request(
            lease_subject="local_provider_health_probe_future",
            lease_scope="session_scoped",
            risk_tier="read_only",
            session_ref="session:1",
            allowed_provider_classes=["lm_studio_local"],
        ),
        identity_scope_decision=_identity(),
        local_provider_health_decision=_provider(),
    )

    assert decision.lifecycle_state == "ready_for_operator_review"
    assert "requires_future_provider_probe_boundary" in decision.required_future_gates
    assert decision.provider_probe_allowed is False
    _assert_non_authority(decision)


def test_project_and_repository_scopes_require_identity_refs() -> None:
    project = _validate(
        _request(lease_scope="project_scoped", risk_tier="read_only", project_ref="project:aegis"),
        identity_scope_decision=_identity(),
    )
    repository = _validate(
        _request(
            lease_scope="repository_scoped",
            risk_tier="read_only",
            project_ref="project:aegis",
            repository_ref="repo:WexyS/Aegis",
        ),
        identity_scope_decision=_identity(),
    )

    assert project.lifecycle_state == "ready_for_operator_review"
    assert repository.lifecycle_state == "ready_for_operator_review"


def test_path_scoped_candidate_requires_bounded_path_prefixes() -> None:
    decision = _validate(
        _request(
            lease_subject="repo_audit_read_future",
            lease_scope="path_scoped",
            risk_tier="read_only",
            project_ref="project:aegis",
            repository_ref="repo:WexyS/Aegis",
            path_prefixes=["src/aegis/core", "tests/test_core"],
        ),
        identity_scope_decision=_identity(),
        repo_audit_decision=_repo_audit(),
    )

    assert decision.lifecycle_state == "ready_for_operator_review"
    assert "requires_future_repo_runner_boundary" in decision.required_future_gates
    assert decision.repo_file_read_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("lease_subject", "missing_lease_subject"),
        ("lease_scope", "missing_lease_scope"),
        ("risk_tier", "missing_risk_tier"),
        ("namespace", "missing_namespace"),
        ("max_duration_seconds", "missing_max_duration_seconds"),
        ("max_actions", "missing_max_actions"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: None}))

    assert decision.lifecycle_state == "blocked"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_non_revocable_and_missing_provenance_block() -> None:
    decision = _validate(_request(revocable=False, source_refs=[], provenance=[]))

    assert decision.lifecycle_state == "blocked"
    assert "lease_must_be_revocable" in decision.failure_reasons
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize("lease_scope", ["unknown", "disabled"])
def test_unknown_or_disabled_scope_blocks(lease_scope: str) -> None:
    decision = _validate(_request(lease_scope=lease_scope))

    assert "unknown_or_disabled_scope_blocked" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("allowed_tools", ["*"], "wildcard_allowed_tools_blocked"),
        ("allowed_model_roles", ["all"], "wildcard_allowed_model_roles_blocked"),
        ("allowed_provider_classes", ["any"], "wildcard_allowed_provider_classes_blocked"),
        ("allowed_context_categories", ["global"], "wildcard_allowed_context_categories_blocked"),
        ("allowed_memory_categories", ["everything"], "wildcard_allowed_memory_categories_blocked"),
    ],
)
def test_broad_wildcard_scopes_block(field: str, value: list[str], reason: str) -> None:
    decision = _validate(_request(**{field: value}))

    assert decision.lifecycle_state == "blocked"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("../secrets", "path_traversal_blocked"),
        ("/", "broad_filesystem_scope_blocked"),
        ("C:/Users/nemes", "absolute_or_external_path_blocked"),
        ("~", "broad_filesystem_scope_blocked"),
        ("*", "broad_wildcard_path_blocked"),
        ("config/.env", "secret_or_credential_scope_blocked"),
    ],
)
def test_unsafe_path_scopes_block(path: str, reason: str) -> None:
    decision = _validate(
        _request(
            lease_scope="path_scoped",
            risk_tier="read_only",
            project_ref="project:aegis",
            repository_ref="repo:WexyS/Aegis",
            path_prefixes=[path],
        ),
        identity_scope_decision=_identity(),
    )

    assert decision.lifecycle_state == "blocked"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize(
    ("risk_tier", "reason"),
    [
        ("destructive", "destructive_risk_blocked"),
        ("unknown", "unknown_risk_blocked"),
        ("high_risk", "high_risk_lease_activation_blocked"),
        ("cloud_data_transfer", "cloud_data_transfer_requires_future_policy"),
        ("external_network", "external_network_requires_future_policy"),
    ],
)
def test_risk_tiers_block_or_require_future_policy(risk_tier: str, reason: str) -> None:
    decision = _validate(_request(risk_tier=risk_tier))

    assert decision.lifecycle_state == "blocked"
    assert reason in decision.failure_reasons


def test_sensitive_data_requires_human_review() -> None:
    blocked = _validate(_request(risk_tier="sensitive_data"))
    reviewed = _validate(_request(risk_tier="sensitive_data", requires_operator_review=True))

    assert blocked.lifecycle_state == "requires_human_approval"
    assert "sensitive_data_requires_human_review" in blocked.failure_reasons
    assert reviewed.lifecycle_state == "ready_for_operator_review"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("allowed_tools", ["secret_reader"]),
        ("allowed_context_categories", ["credential_like"]),
        ("allowed_memory_categories", ["api_token_memory"]),
    ],
)
def test_secret_or_credential_access_blocks(field: str, value: list[str]) -> None:
    decision = _validate(_request(**{field: value}))

    assert "secret_or_credential_scope_blocked" in decision.failure_reasons


def test_surveillance_and_productivity_scoring_block() -> None:
    decision = _validate(_request(allowed_tools=["productivity_score_monitor"]))

    assert "surveillance_or_productivity_scoring_blocked" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("max_duration_seconds", 86401, "excessive_duration_blocked"),
        ("max_duration_seconds", 0, "invalid_max_duration"),
        ("max_actions", 101, "excessive_action_count_blocked"),
        ("max_actions", 0, "invalid_max_actions"),
    ],
)
def test_duration_and_action_bounds(field: str, value: int, reason: str) -> None:
    decision = _validate(_request(**{field: value}))

    assert reason in decision.failure_reasons


def test_local_provider_health_probe_requires_provider_readiness_but_remains_not_allowed() -> None:
    missing = _validate(
        _request(
            lease_subject="local_provider_health_probe_future",
            lease_scope="provider_scoped",
            risk_tier="read_only",
            allowed_provider_classes=["lm_studio_local"],
        )
    )
    ready = _validate(
        _request(
            lease_subject="local_provider_health_probe_future",
            lease_scope="provider_scoped",
            risk_tier="read_only",
            allowed_provider_classes=["lm_studio_local"],
        ),
        local_provider_health_decision=_provider(),
    )

    assert missing.lifecycle_state == "requires_provider_health"
    assert "missing_local_provider_health" in missing.failure_reasons
    assert ready.lifecycle_state == "ready_for_operator_review"
    assert ready.provider_probe_allowed is False


def test_repo_read_candidate_requires_repo_metadata_and_remains_not_file_permission() -> None:
    decision = _validate(
        _request(
            lease_subject="repo_audit_read_future",
            lease_scope="repository_scoped",
            risk_tier="read_only",
            project_ref="project:aegis",
            repository_ref="repo:WexyS/Aegis",
        ),
        identity_scope_decision=_identity(),
        repo_audit_decision=_repo_audit(),
    )

    assert decision.lifecycle_state == "ready_for_operator_review"
    assert decision.repo_file_read_allowed is False


def test_context_memory_and_model_subjects_require_related_boundaries() -> None:
    context = _validate(
        _request(
            lease_subject="context_retrieval_future",
            lease_scope="context_scoped",
            risk_tier="read_only",
            allowed_context_categories=["private_repo_code"],
        ),
        context_policy_decision=_context(),
    )
    memory = _validate(
        _request(
            lease_subject="memory_operation_future",
            lease_scope="memory_scoped",
            risk_tier="read_only",
            allowed_memory_categories=["repo_memory"],
        ),
        memory_governance_decision=_memory(),
    )
    model = _validate(
        _request(
            lease_subject="model_call_future",
            lease_scope="model_scoped",
            risk_tier="low_risk_local",
            allowed_model_roles=["coding"],
        ),
        model_auto_mode_decision=_auto_mode(),
        local_provider_health_decision=_provider(),
    )

    assert context.lifecycle_state == "ready_for_operator_review"
    assert memory.lifecycle_state == "ready_for_operator_review"
    assert model.lifecycle_state == "ready_for_operator_review"
    assert context.context_retrieval_allowed is False
    assert memory.memory_retrieval_allowed is False
    assert memory.memory_write_allowed is False
    assert model.model_call_allowed is False


@pytest.mark.parametrize(
    ("subject", "scope", "risk", "expected_gate"),
    [
        ("web_research_query_future", "web_domain_scoped_future", "external_network", "requires_future_web_research_gateway"),
        ("external_agent_observation_future", "external_agent_scoped_future", "read_only", "requires_future_external_agent_oversight_boundary"),
        ("plugin_operation_future", "tool_scoped", "medium_risk_local", "requires_future_plugin_or_vertical_pack_boundary"),
        ("playbook_replay_future", "session_scoped", "medium_risk_local", "requires_future_playbook_boundary"),
        ("rollback_snapshot_future", "project_scoped", "read_only", "requires_future_rollback_boundary"),
    ],
)
def test_future_feature_subjects_remain_gated(subject: str, scope: str, risk: str, expected_gate: str) -> None:
    request = _request(
        lease_subject=subject,
        lease_scope=scope,
        risk_tier=risk,
        project_ref="project:aegis",
        repository_ref="repo:WexyS/Aegis",
        session_ref="session:1",
        allowed_tools=["preview"],
        allowed_domains_future=["example.com"],
    )
    decision = _validate(request, identity_scope_decision=_identity())

    assert expected_gate in decision.required_future_gates
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("policy_extension_decision", _policy(runtime_dispatch_allowed=True)),
        ("identity_scope_decision", _identity(authority=True)),
        ("memory_governance_decision", _memory(memory_write_allowed=True)),
        ("context_policy_decision", _context(context_retrieval_allowed=True)),
        ("model_auto_mode_decision", _auto_mode(model_call_allowed=True)),
        ("local_provider_health_decision", _provider(provider_probe_allowed=True)),
        ("repo_audit_decision", _repo_audit(repo_file_read_allowed=True)),
        ("mission_control_decision", SimpleNamespace(lease_active=True)),
        ("tool_simulation_decision", SimpleNamespace(tool_call_performed=True)),
        ("plugin_review_decision", SimpleNamespace(lease_grant=True)),
        ("compliance_evidence_decision", SimpleNamespace(verifier_success=True)),
        ("developer_work_passport_decision", SimpleNamespace(proof=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    related = {related_name: related_value}
    if related_name != "policy_extension_decision":
        related["policy_extension_decision"] = _policy()
    decision = validate_capability_lease_request(_request(), **related)

    assert decision.lifecycle_state == "blocked"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("lease_active", "lease_active_claim_denied"),
        ("lease_created", "lease_creation_claim_denied"),
        ("lease_used", "lease_use_claim_denied"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("evidence_provided_by_lease", "lease_cannot_provide_evidence"),
        ("verifier_success", "lease_cannot_mark_verifier_success"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("mcp_authority", "mcp_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
    ],
)
def test_active_grant_authority_evidence_and_verifier_claims_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_call_allowed", "model_call_permission_denied"),
        ("provider_probe_allowed", "provider_probe_permission_denied"),
        ("repo_file_read_allowed", "repo_file_read_permission_denied"),
        ("memory_write_allowed", "memory_write_permission_denied"),
        ("memory_retrieval_allowed", "memory_retrieval_permission_denied"),
        ("context_retrieval_allowed", "context_retrieval_permission_denied"),
        ("web_query_allowed", "web_query_permission_denied"),
        ("plugin_execution_allowed", "plugin_execution_permission_denied"),
        ("playbook_execution_allowed", "playbook_execution_permission_denied"),
        ("rollback_execution_allowed", "rollback_execution_permission_denied"),
        ("external_agent_tracking_allowed", "external_agent_tracking_permission_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_feature_permission_flags_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_call_performed", "model_call_request_denied"),
        ("provider_probe_performed", "provider_probe_request_denied"),
        ("repo_file_read_performed", "repo_file_read_request_denied"),
        ("memory_write_performed", "memory_write_request_denied"),
        ("memory_retrieval_performed", "memory_retrieval_request_denied"),
        ("context_retrieval_performed", "context_retrieval_request_denied"),
        ("web_query_performed", "web_query_request_denied"),
        ("plugin_execution_performed", "plugin_execution_request_denied"),
        ("playbook_execution_performed", "playbook_execution_request_denied"),
        ("rollback_execution_performed", "rollback_execution_request_denied"),
        ("api_call_performed", "api_call_request_denied"),
        ("mcp_call_performed", "mcp_call_request_denied"),
        ("tool_call_performed", "tool_call_request_denied"),
    ],
)
def test_behavior_flags_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_rejected() -> None:
    decision = _validate(_request(execution_permission="granted_by_lease"))

    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _identity(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _validate(request, identity_scope_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.lease_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_never_sets_active_grant_or_dispatch_flags() -> None:
    decision = _validate(_request())

    _assert_non_authority(decision)
