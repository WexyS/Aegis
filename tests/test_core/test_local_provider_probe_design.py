from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_design import (
    LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_DESIGN_VERSION,
    validate_local_provider_probe_design_request,
)


def _provider(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        readiness_status="metadata_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_local_provider_health",
        endpoint_probed=False,
        health_verified=False,
        model_call_performed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _lease(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        lifecycle_state="ready_for_operator_review",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_capability_lease",
        lease_active=False,
        lease_grant=False,
        lease_used=False,
        provider_probe_allowed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _policy(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        policy_outcome="allowed_metadata_only",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_policy_extension",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _context(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        policy_status="metadata_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_context_policy",
        context_payload_sent=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _safe_related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        authority=False,
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        verifier_success=False,
        evidence_provided_by_probe_design=False,
        probe_executed=False,
        endpoint_probed=False,
        model_call_performed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "provider-probe-design:aegis:1",
        "probe_target_class": "lm_studio_local_openai_compatible",
        "probe_phase": "endpoint_reachability_probe_future",
        "endpoint_host_class": "localhost",
        "namespace": "local_provider_probe_design",
        "endpoint_ref": "lmstudio-localhost",
        "provider_ref": "lmstudio:local",
        "max_timeout_ms": 2000,
        "max_retries": 0,
        "max_redirects": 0,
        "allowed_methods": ["GET", "HEAD"],
        "allowed_paths": ["/v1/models"],
        "disallowed_paths": ["/v1/chat/completions", "/v1/embeddings"],
        "no_auth_required": True,
        "no_secret_logging": True,
        "no_prompt_payload": True,
        "no_user_context_payload": True,
        "no_repo_context_payload": True,
        "no_memory_context_payload": True,
        "no_raw_journal_payload": True,
        "no_raw_evidence_payload": True,
        "no_external_network": True,
        "local_only": True,
        "cancellable": True,
        "rate_limited": True,
        "requires_operator_review": True,
        "requires_capability_lease_future": False,
        "requires_policy_check": True,
        "requires_negative_evidence_on_failure": True,
        "source_refs": [{"ref_id": "synthetic:probe-design", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related: object):
    if "local_provider_health_decision" not in related:
        related["local_provider_health_decision"] = _provider()
    return validate_local_provider_probe_design_request(request, **related)


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_probe_design is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.probe_executed is False
    assert decision.endpoint_probed is False
    assert decision.socket_opened is False
    assert decision.provider_authenticated is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.model_list_requested is False
    assert decision.model_loaded is False
    assert decision.model_call_performed is False
    assert decision.minimal_generation_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_probe_performed is False
    assert decision.provider_process_inspected is False
    assert decision.live_model_files_inspected is False
    assert decision.context_payload_sent is False
    assert decision.memory_payload_sent is False
    assert decision.repo_payload_sent is False
    assert decision.journal_payload_sent is False
    assert decision.evidence_payload_sent is False
    assert decision.data_sent_external is False
    assert decision.health_verified is False
    assert decision.provider_selected_for_execution is False
    assert decision.model_selected_for_execution is False


def test_valid_localhost_lm_studio_endpoint_probe_design_is_future_candidate_not_executed() -> None:
    decision = _validate(_request())

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_DESIGN_VERSION
    assert decision.probe_result_status == "future_probe_candidate"
    assert decision.probe_target_class == "lm_studio_local_openai_compatible"
    assert decision.endpoint_host_class == "localhost"
    assert "provider_probe_attempt_future" in decision.future_evidence_candidates
    assert "endpoint_reachable_future" in decision.future_evidence_candidates
    assert "timeout_negative_evidence_future" in decision.future_negative_evidence_candidates
    _assert_non_authority(decision)


def test_valid_loopback_provider_metadata_probe_design_is_non_authoritative() -> None:
    decision = _validate(
        _request(
            probe_target_class="generic_openai_compatible_local",
            probe_phase="provider_metadata_probe_future",
            endpoint_host_class="loopback",
            allowed_paths=["/v1/models"],
        )
    )

    assert decision.probe_result_status == "future_probe_candidate"
    assert "provider_metadata_response_future" in decision.future_evidence_candidates
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("probe_target_class", "missing_probe_target_class"),
        ("probe_phase", "missing_probe_phase"),
        ("endpoint_host_class", "missing_endpoint_host_class"),
        ("namespace", "missing_namespace"),
        ("max_timeout_ms", "missing_max_timeout_ms"),
        ("max_retries", "missing_max_retries"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: None}))

    assert reason in decision.failure_reasons
    assert decision.probe_result_status in {"unsupported", "blocked_by_policy"}
    _assert_non_authority(decision)


@pytest.mark.parametrize("endpoint_host_class", ["lan", "remote", "cloud"])
def test_lan_remote_and_cloud_endpoint_hosts_block(endpoint_host_class: str) -> None:
    decision = _validate(_request(endpoint_host_class=endpoint_host_class))

    assert decision.probe_result_status == "blocked_by_endpoint_host"
    assert "endpoint_host_blocked" in decision.failure_reasons
    assert decision.data_sent_external is False


def test_unknown_endpoint_host_class_blocks() -> None:
    decision = _validate(_request(endpoint_host_class="unknown"))

    assert decision.probe_result_status == "blocked_by_endpoint_host"
    assert "unknown_endpoint_host_blocked" in decision.failure_reasons


def test_localhost_and_loopback_do_not_prove_health() -> None:
    localhost = _validate(_request(endpoint_host_class="localhost"))
    loopback = _validate(_request(endpoint_host_class="loopback"))

    assert localhost.health_verified is False
    assert localhost.endpoint_probed is False
    assert loopback.health_verified is False
    assert loopback.endpoint_probed is False


def test_external_network_must_be_disallowed() -> None:
    decision = _validate(_request(no_external_network=False))

    assert "no_external_network_required" in decision.failure_reasons
    assert decision.data_sent_external is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("no_secret_logging", "no_secret_logging_required"),
        ("no_prompt_payload", "no_prompt_payload_required"),
        ("no_user_context_payload", "no_user_context_payload_required"),
        ("no_repo_context_payload", "no_repo_context_payload_required"),
        ("no_memory_context_payload", "no_memory_context_payload_required"),
        ("no_raw_journal_payload", "no_raw_journal_payload_required"),
        ("no_raw_evidence_payload", "no_raw_evidence_payload_required"),
        ("local_only", "local_only_required"),
        ("cancellable", "cancellable_required"),
        ("rate_limited", "rate_limited_required"),
        ("requires_policy_check", "requires_policy_check_required"),
        ("requires_negative_evidence_on_failure", "requires_negative_evidence_on_failure_required"),
    ],
)
def test_required_safety_constraints_must_be_true(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: False}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_auth_requirement_and_secret_boundary_block() -> None:
    decision = _validate(_request(no_auth_required=False))

    assert decision.probe_result_status == "blocked_by_secret_boundary"
    assert "auth_requirement_blocked" in decision.failure_reasons
    assert decision.secret_read is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("max_timeout_ms", 0, "invalid_timeout_policy"),
        ("max_timeout_ms", 20000, "timeout_policy_too_broad"),
        ("max_retries", -1, "invalid_retry_policy"),
        ("max_retries", 3, "retry_policy_too_broad"),
        ("max_redirects", 1, "redirects_not_allowed"),
    ],
)
def test_timeout_retry_and_redirect_constraints(field: str, value: int, reason: str) -> None:
    decision = _validate(_request(**{field: value}))

    assert reason in decision.failure_reasons


def test_allowed_methods_are_metadata_only_get_or_head() -> None:
    missing = _validate(_request(allowed_methods=[]))
    post = _validate(_request(allowed_methods=["POST"]))

    assert "missing_allowed_methods" in missing.failure_reasons
    assert "unsafe_method_blocked" in post.failure_reasons


@pytest.mark.parametrize("path", ["/v1/chat/completions", "/v1/embeddings", "/rerank", "/responses"])
def test_generation_embedding_rerank_and_response_paths_are_blocked(path: str) -> None:
    decision = _validate(_request(allowed_paths=[path]))

    assert "unsafe_probe_path_blocked" in decision.failure_reasons


def test_disallowed_generation_and_embedding_paths_must_be_explicit() -> None:
    decision = _validate(_request(disallowed_paths=[]))

    assert "missing_disallowed_generation_paths" in decision.failure_reasons


@pytest.mark.parametrize(
    ("phase", "evidence"),
    [
        ("endpoint_reachability_probe_future", "endpoint_reachable_future"),
        ("provider_metadata_probe_future", "provider_metadata_response_future"),
        ("model_list_probe_future", "model_list_response_future"),
        ("model_role_match_probe_future", "provider_probe_attempt_future"),
    ],
)
def test_future_probe_phases_do_not_execute(phase: str, evidence: str) -> None:
    decision = _validate(_request(probe_phase=phase))

    assert decision.probe_result_status == "future_probe_candidate"
    assert evidence in decision.future_evidence_candidates
    assert decision.probe_executed is False
    assert decision.endpoint_probed is False


@pytest.mark.parametrize(
    "phase",
    [
        "minimal_generation_probe_future_blocked_for_now",
        "embedding_probe_future_blocked_for_now",
        "reranker_probe_future_blocked_for_now",
        "multimodal_probe_future_blocked_for_now",
    ],
)
def test_generation_embedding_reranker_and_multimodal_phases_block_for_now(phase: str) -> None:
    decision = _validate(_request(probe_phase=phase))

    assert decision.probe_result_status == "blocked_by_policy"
    assert "probe_phase_blocked_for_now" in decision.failure_reasons
    _assert_non_authority(decision)


def test_model_list_probe_future_does_not_list_models() -> None:
    decision = _validate(_request(probe_phase="model_list_probe_future", allowed_paths=["/v1/models"]))

    assert decision.probe_result_status == "future_probe_candidate"
    assert "model_list_response_future" in decision.future_evidence_candidates
    assert decision.model_list_requested is False


def test_missing_local_provider_health_readiness_blocks() -> None:
    decision = validate_local_provider_probe_design_request(_request())

    assert decision.probe_result_status == "blocked_by_missing_provider_health_readiness"
    assert "missing_local_provider_health_readiness" in decision.failure_reasons


def test_capability_lease_candidate_does_not_activate_probe() -> None:
    decision = _validate(_request(requires_capability_lease_future=True), capability_lease_decision=_lease())

    assert decision.probe_result_status == "future_probe_candidate"
    assert "requires_future_capability_lease_use_boundary" in decision.required_future_gates
    assert decision.probe_executed is False
    assert decision.lease_grant is False


def test_missing_capability_lease_blocks_when_required() -> None:
    decision = _validate(_request(requires_capability_lease_future=True))

    assert decision.probe_result_status == "blocked_by_missing_lease"
    assert "missing_capability_lease_candidate" in decision.failure_reasons


def test_model_auto_mode_and_local_inventory_do_not_authorize_probe_or_model_call() -> None:
    decision = _validate(
        _request(),
        model_auto_mode_decision=SimpleNamespace(
            selection_mode="local_model_candidate",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_model_auto_mode",
            provider_selected_for_execution=False,
            model_call_performed=False,
        ),
        local_model_inventory_decision=SimpleNamespace(
            inventory_status="inventory_ready",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_local_model_inventory",
            model_call_performed=False,
        ),
    )

    assert decision.probe_result_status == "future_probe_candidate"
    assert decision.provider_selected_for_execution is False
    assert decision.model_call_performed is False


def test_blocked_context_policy_and_policy_extension_block() -> None:
    context = _validate(_request(), context_policy_decision=_context(policy_status="blocked_by_secret_policy"))
    policy = _validate(_request(), policy_extension_decision=_policy(policy_outcome="blocked_by_policy"))

    assert context.probe_result_status == "blocked_by_policy"
    assert "context_policy_not_ready" in context.failure_reasons
    assert policy.probe_result_status == "blocked_by_policy"
    assert "policy_extension_not_ready" in policy.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("local_provider_health_decision", _provider(endpoint_probed=True)),
        ("capability_lease_decision", _lease(lease_active=True)),
        ("model_auto_mode_decision", _safe_related(provider_selected_for_execution=True)),
        ("context_policy_decision", _context(data_sent_external=True)),
        ("policy_extension_decision", _policy(runtime_dispatch_allowed=True)),
        ("identity_scope_decision", _safe_related(authority=True)),
        ("memory_governance_decision", _safe_related(memory_payload_sent=True)),
        ("local_model_inventory_decision", _safe_related(model_call_performed=True)),
        ("mission_control_decision", _safe_related(probe_executed=True)),
        ("tool_simulation_decision", _safe_related(tool_call_performed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    related = {related_name: related_value}
    if related_name != "local_provider_health_decision":
        related["local_provider_health_decision"] = _provider()
    decision = validate_local_provider_probe_design_request(_request(), **related)

    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_future_evidence_candidates_are_metadata_only_not_evidence_or_verifier_success() -> None:
    decision = _validate(_request(probe_phase="provider_metadata_probe_future"))

    assert "provider_probe_attempt_future" in decision.future_evidence_candidates
    assert "provider_metadata_response_future" in decision.future_evidence_candidates
    assert decision.evidence_provided_by_probe_design is False
    assert decision.verifier_success is False
    assert decision.health_verified is False


def test_future_positive_probe_evidence_is_not_task_success() -> None:
    decision = _validate(_request(endpoint_reachable_is_task_success=True))

    assert "endpoint_reachability_task_success_claim_denied" in decision.failure_reasons
    assert decision.verifier_success is False


def test_future_negative_evidence_must_not_be_hidden() -> None:
    decision = _validate(_request(requires_negative_evidence_on_failure=False))

    assert "requires_negative_evidence_on_failure_required" in decision.failure_reasons
    assert "timeout_negative_evidence_future" in decision.future_negative_evidence_candidates
    assert "refused_connection_negative_evidence_future" in decision.future_negative_evidence_candidates


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("probe_executed", "probe_execution_denied"),
        ("endpoint_probed", "endpoint_probe_denied"),
        ("socket_opened", "socket_open_denied"),
        ("provider_authenticated", "provider_authentication_denied"),
        ("api_key_validated", "api_key_validation_denied"),
        ("secret_read", "secret_read_denied"),
        ("model_list_requested", "model_list_request_denied"),
        ("model_loaded", "model_load_denied"),
        ("model_call_performed", "model_call_denied"),
        ("minimal_generation_performed", "minimal_generation_denied"),
        ("embedding_generated", "embedding_generation_denied"),
        ("reranking_performed", "reranking_denied"),
        ("multimodal_probe_performed", "multimodal_probe_denied"),
        ("provider_process_inspected", "provider_process_inspection_denied"),
        ("live_model_files_inspected", "live_model_file_inspection_denied"),
        ("context_payload_sent", "context_payload_denied"),
        ("memory_payload_sent", "memory_payload_denied"),
        ("repo_payload_sent", "repo_payload_denied"),
        ("journal_payload_sent", "journal_payload_denied"),
        ("evidence_payload_sent", "evidence_payload_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_execution_payload_and_transfer_flags_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_probe_design", "probe_design_cannot_provide_evidence"),
        ("verifier_success", "probe_design_cannot_mark_verifier_success"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("health_verified", "health_verification_claim_denied"),
        ("provider_selected_for_execution", "provider_execution_selection_denied"),
        ("model_selected_for_execution", "model_execution_selection_denied"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
    ],
)
def test_authority_grant_evidence_verifier_and_selection_claims_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = _validate(_request(execution_permission="granted_by_probe_design"))

    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _provider(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _validate(request, local_provider_health_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_never_sets_probe_health_or_external_flags() -> None:
    decision = _validate(_request())

    _assert_non_authority(decision)
