from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_wiring import (
    LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_WIRING_VERSION,
    validate_local_provider_probe_wiring_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-wiring:aegis:1",
        "probe_wiring_class": "local_model_list_probe_wiring",
        "execution_mode_class": "metadata_only",
        "transport_class": "no_transport",
        "endpoint_host_class": "localhost",
        "endpoint_scope_class": "models_list_metadata_candidate",
        "payload_class": "metadata_only_empty_request",
        "secret_policy_class": "no_secret",
        "timeout_policy_class": "bounded_short_timeout",
        "cancellation_policy_class": "cancellation_supported_candidate",
        "probe_result_class": "not_executed",
        "runtime_api_readiness_class": "no_runtime_wiring",
        "namespace": "local_provider_probe_wiring",
        "source_refs": [{"ref_id": "synthetic:probe-wiring", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "limitations": ["readiness-only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        probe_boundary_status="probe_allowed_candidate",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_probe_wiring=False,
        evidence_provided_by_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        api_route_added=False,
        runtime_command_added=False,
        scheduler_added=False,
        real_endpoint_probed=False,
        endpoint_probed=False,
        socket_opened=False,
        http_request_performed=False,
        provider_probed=False,
        model_loaded=False,
        model_call_performed=False,
        generation_performed=False,
        embedding_generated=False,
        reranking_performed=False,
        multimodal_inference_performed=False,
        prompt_payload_sent=False,
        context_payload_sent=False,
        memory_payload_sent=False,
        repo_payload_sent=False,
        raw_journal_payload_sent=False,
        raw_evidence_payload_sent=False,
        api_key_validated=False,
        secret_read=False,
        authorization_header_sent=False,
        cloud_provider_called=False,
        lan_or_remote_endpoint_called=False,
        data_sent_external=False,
        provider_health_verified=False,
        model_availability_verified=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_probe_wiring is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.api_route_added is False
    assert decision.runtime_command_added is False
    assert decision.scheduler_added is False
    assert decision.real_endpoint_probed is False
    assert decision.socket_opened is False
    assert decision.http_request_performed is False
    assert decision.provider_probed is False
    assert decision.model_loaded is False
    assert decision.model_call_performed is False
    assert decision.generation_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_inference_performed is False
    assert decision.prompt_payload_sent is False
    assert decision.context_payload_sent is False
    assert decision.memory_payload_sent is False
    assert decision.repo_payload_sent is False
    assert decision.raw_journal_payload_sent is False
    assert decision.raw_evidence_payload_sent is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.authorization_header_sent is False
    assert decision.cloud_provider_called is False
    assert decision.lan_or_remote_endpoint_called is False
    assert decision.data_sent_external is False
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def _assert_blocked(decision: object, reason: str) -> None:
    assert reason in decision.failure_reasons
    assert decision.wiring_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_valid_metadata_only_wiring_request_is_read_only_candidate() -> None:
    decision = validate_local_provider_probe_wiring_request(_request())

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_WIRING_VERSION
    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert decision.wiring_classification == "readiness_metadata_only"
    assert decision.transport_classification == "no_transport_no_execution"
    assert decision.endpoint_classification == "models_list_candidate_not_availability_proof"
    assert decision.truthfulness_classification == "metadata_and_mock_results_not_health_model_or_benchmark_proof"
    _assert_non_authority(decision)


def test_valid_mock_transport_only_wiring_request_is_candidate_only() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(
            probe_wiring_class="mock_transport_probe_wiring",
            execution_mode_class="mock_transport_only",
            transport_class="injected_mock_transport",
            probe_result_class="mock_success_metadata_candidate",
        )
    )

    assert decision.wiring_readiness_status == "mock_transport_candidate"
    assert decision.transport_classification == "mock_transport_metadata_only"
    assert decision.probe_result_classification == "mock_success_metadata_only_not_health_proof"
    _assert_non_authority(decision)


def test_valid_future_httpx_localhost_transport_is_future_gated_not_executed() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(
            execution_mode_class="future_live_localhost_probe",
            transport_class="future_httpx_localhost_transport",
            runtime_api_readiness_class="requires_policy_gate",
        )
    )

    assert decision.wiring_readiness_status == "future_gated"
    assert "future_live_localhost_probe_requires_explicit_runtime_gate" in decision.required_future_gates
    assert "future_httpx_localhost_transport_requires_future_injected_client" in decision.required_future_gates
    assert decision.transport_classification == "future_localhost_transport_not_executed"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("probe_result_class", "expected"),
    [
        ("mock_timeout_negative_candidate", "negative_mock_candidate_metadata_only_not_runtime_failure"),
        ("mock_connection_refused_negative_candidate", "negative_mock_candidate_metadata_only_not_runtime_failure"),
    ],
)
def test_mock_negative_results_become_negative_candidate_metadata_only(
    probe_result_class: str,
    expected: str,
) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(
            probe_wiring_class="mock_transport_probe_wiring",
            execution_mode_class="mock_transport_only",
            transport_class="injected_mock_transport",
            probe_result_class=probe_result_class,
        )
    )

    assert decision.wiring_readiness_status == "mock_transport_candidate"
    assert decision.probe_result_classification == expected
    assert decision.evidence_provided_by_probe_wiring is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("probe_wiring_class", "missing_probe_wiring_class"),
        ("execution_mode_class", "missing_execution_mode_class"),
        ("transport_class", "missing_transport_class"),
        ("endpoint_host_class", "missing_endpoint_host_class"),
        ("endpoint_scope_class", "missing_endpoint_scope_class"),
        ("payload_class", "missing_payload_class"),
        ("secret_policy_class", "missing_secret_policy_class"),
        ("timeout_policy_class", "missing_timeout_policy_class"),
        ("cancellation_policy_class", "missing_cancellation_policy_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_local_provider_probe_wiring_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


@pytest.mark.parametrize("endpoint_host_class", ["localhost", "loopback"])
def test_localhost_and_loopback_hosts_are_accepted_as_metadata_candidates(endpoint_host_class: str) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(endpoint_host_class=endpoint_host_class)
    )

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    _assert_non_authority(decision)


@pytest.mark.parametrize("endpoint_host_class", ["lan", "remote", "cloud", "unknown"])
def test_lan_remote_cloud_and_unknown_hosts_are_blocked(endpoint_host_class: str) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(endpoint_host_class=endpoint_host_class)
    )

    _assert_blocked(decision, "blocked_by_host")


def test_unsupported_real_transport_blocks() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(transport_class="unsupported_real_transport")
    )

    _assert_blocked(decision, "unsupported_real_transport_blocked")


def test_injected_mock_transport_is_allowed_only_as_mock() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(transport_class="injected_mock_transport", execution_mode_class="metadata_only")
    )

    _assert_blocked(decision, "mock_transport_requires_mock_mode")


def test_no_transport_means_no_execution() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(transport_class="no_transport", execution_mode_class="metadata_only")
    )

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert decision.transport_classification == "no_transport_no_execution"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("endpoint_scope_class", "expected_classification"),
    [
        ("provider_root_metadata_candidate", "metadata_endpoint_candidate_only"),
        ("models_list_metadata_candidate", "models_list_candidate_not_availability_proof"),
        ("health_metadata_candidate", "metadata_endpoint_candidate_only"),
    ],
)
def test_metadata_endpoint_scopes_are_allowed_as_candidates(
    endpoint_scope_class: str,
    expected_classification: str,
) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(endpoint_scope_class=endpoint_scope_class)
    )

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert decision.endpoint_classification == expected_classification
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False


@pytest.mark.parametrize(
    ("endpoint_scope_class", "reason"),
    [
        ("generation_blocked", "generation_endpoint_blocked"),
        ("chat_completion_blocked", "chat_completion_endpoint_blocked"),
        ("completion_blocked", "completion_endpoint_blocked"),
        ("embeddings_blocked", "embedding_endpoint_blocked"),
        ("rerank_blocked", "reranker_endpoint_blocked"),
        ("multimodal_blocked", "multimodal_endpoint_blocked"),
        ("audio_blocked", "audio_endpoint_blocked"),
        ("file_upload_blocked", "file_upload_endpoint_blocked"),
        ("tool_call_blocked", "tool_call_endpoint_blocked"),
    ],
)
def test_generation_embedding_reranker_multimodal_audio_upload_and_tool_scopes_block(
    endpoint_scope_class: str,
    reason: str,
) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(endpoint_scope_class=endpoint_scope_class)
    )

    _assert_blocked(decision, reason)


def test_unknown_endpoint_scope_blocks_or_future_gates() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(endpoint_scope_class="unknown")
    )

    _assert_blocked(decision, "unknown_endpoint_scope_blocked")


@pytest.mark.parametrize("payload_class", ["no_payload", "metadata_only_empty_request"])
def test_safe_payload_classes_are_allowed(payload_class: str) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(payload_class=payload_class))

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert decision.payload_classification == "no_payload_or_metadata_empty_request_only"


@pytest.mark.parametrize(
    "payload_class",
    [
        "prompt_payload_blocked",
        "context_payload_blocked",
        "memory_payload_blocked",
        "repo_payload_blocked",
        "raw_journal_payload_blocked",
        "raw_evidence_payload_blocked",
        "secret_payload_blocked",
        "unknown",
    ],
)
def test_prompt_context_memory_repo_journal_evidence_secret_payloads_block(payload_class: str) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(payload_class=payload_class))

    _assert_blocked(decision, "blocked_by_payload")


@pytest.mark.parametrize(
    ("secret_policy_class", "reason"),
    [
        ("api_key_future_gated", "api_key_future_gated_not_allowed_now"),
        ("secret_read_blocked", "blocked_by_secret_policy"),
        ("api_key_validation_blocked", "blocked_by_secret_policy"),
        ("unknown", "blocked_by_secret_policy"),
    ],
)
def test_authorization_api_key_and_secret_policies_block(secret_policy_class: str, reason: str) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(secret_policy_class=secret_policy_class)
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("timeout_policy_class", "reason"),
    [
        ("missing_timeout", "missing_timeout_policy"),
        ("excessive_timeout", "excessive_timeout_policy"),
        ("unknown", "missing_timeout_policy"),
    ],
)
def test_timeout_policy_is_required_and_bounded(timeout_policy_class: str, reason: str) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(timeout_policy_class=timeout_policy_class)
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize("cancellation_policy_class", ["missing_cancellation_policy", "unknown"])
def test_cancellation_policy_is_required(cancellation_policy_class: str) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(cancellation_policy_class=cancellation_policy_class)
    )

    _assert_blocked(decision, "missing_cancellation_policy")


def test_cancellation_not_modeled_is_allowed_only_as_explicit_metadata() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(cancellation_policy_class="cancellation_not_modeled")
    )

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert decision.cancellation_classification == "cancellation_not_modeled_requires_future_review"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_probe_wiring", "probe_wiring_cannot_provide_evidence"),
        ("verifier_success", "probe_wiring_cannot_mark_verifier_success"),
        ("mutation_performed", "mutation_performed_denied"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
    ],
)
def test_authority_grants_evidence_verifier_and_proof_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("api_route_added", "api_route_addition_denied"),
        ("runtime_command_added", "runtime_command_addition_denied"),
        ("scheduler_added", "scheduler_addition_denied"),
        ("real_endpoint_probed", "real_endpoint_probe_denied"),
        ("socket_opened", "socket_open_denied"),
        ("http_request_performed", "http_request_denied"),
        ("provider_probed", "provider_probe_execution_denied"),
        ("model_loaded", "model_load_denied"),
        ("model_call_performed", "model_call_denied"),
        ("generation_performed", "generation_denied"),
        ("embedding_generated", "embedding_generation_denied"),
        ("reranking_performed", "reranking_denied"),
        ("multimodal_inference_performed", "multimodal_inference_denied"),
        ("prompt_payload_sent", "prompt_payload_denied"),
        ("context_payload_sent", "context_payload_denied"),
        ("memory_payload_sent", "memory_payload_denied"),
        ("repo_payload_sent", "repo_payload_denied"),
        ("raw_journal_payload_sent", "raw_journal_payload_denied"),
        ("raw_evidence_payload_sent", "raw_evidence_payload_denied"),
        ("api_key_validated", "api_key_validation_denied"),
        ("secret_read", "secret_read_denied"),
        ("authorization_header_sent", "authorization_header_denied"),
        ("cloud_provider_called", "cloud_provider_call_denied"),
        ("lan_or_remote_endpoint_called", "lan_or_remote_endpoint_call_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_runtime_api_probe_model_payload_secret_and_external_behavior_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("provider_metadata_is_truth", "provider_metadata_truth_claim_denied"),
        ("model_list_is_truth", "model_list_truth_claim_denied"),
        ("mock_success_is_health_proof", "mock_success_health_proof_denied"),
        ("negative_mock_result_is_runtime_failure", "negative_mock_runtime_failure_claim_denied"),
        ("provider_health_is_proof", "provider_health_proof_denied"),
        ("model_availability_is_execution_ready", "model_availability_execution_ready_claim_denied"),
        ("probe_candidate_selects_auto_mode", "auto_mode_selection_claim_denied"),
        ("quality_or_benchmark_verified", "benchmark_verification_denied"),
        ("self_reported_identity_is_authority", "self_reported_identity_authority_denied"),
        ("model_inventory_proves_availability", "model_inventory_availability_proof_denied"),
    ],
)
def test_truthfulness_overclaims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_wiring_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_future_live_result_claim_is_blocked_now() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(probe_result_class="future_live_success_metadata_candidate")
    )

    _assert_blocked(decision, "future_live_result_not_allowed_now")


def test_mock_success_requires_mock_transport() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(probe_result_class="mock_success_metadata_candidate")
    )

    _assert_blocked(decision, "mock_success_requires_mock_transport")


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_boundary_decision", {"real_endpoint_probed": True}),
        ("local_provider_probe_design_decision", {"probe_executed": True}),
        ("local_provider_health_decision", {"provider_health_verified": True}),
        ("local_model_context_profile_decision", {"benchmark_claim_verified": True}),
        ("model_auto_mode_decision", {"auto_mode_execution_allowed": True}),
        ("local_model_inventory_decision", {"model_availability_verified": True}),
        ("context_policy_decision", {"context_payload_sent": True}),
        ("identity_scope_decision", {"runtime_dispatch_allowed": True}),
        ("memory_governance_decision", {"memory_payload_sent": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("capability_lease_decision", {"lease_grant": True}),
        ("audit_query_layer_decision", {"api_route_added": True}),
        ("action_attribution_decision", {"evidence_created": True}),
        ("system_drift_integrity_decision", {"verifier_success": True}),
        ("passive_observe_decision", {"runtime_state_mutated": True}),
        ("mission_control_decision", {"frontend_authority": True}),
        ("tool_simulation_decision", {"tool_call_performed": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, kwargs: dict[str, object]) -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(),
        local_provider_probe_boundary_decision=_related(probe_boundary_status="probe_allowed_candidate"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        local_provider_health_decision=_related(readiness_status="metadata_ready"),
    )

    assert decision.wiring_readiness_status == "wiring_readiness_candidate"
    assert [ref.label for ref in decision.related_references] == [
        "local_provider_probe_boundary",
        "local_provider_probe_design",
        "local_provider_health",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request()
    original_request = deepcopy(request)
    related = _related(probe_boundary_status="probe_allowed_candidate")
    original_status = related.probe_boundary_status

    decision = validate_local_provider_probe_wiring_request(
        request,
        local_provider_probe_boundary_decision=related,
    )

    assert request == original_request
    assert related.probe_boundary_status == original_status
    assert decision.probe_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_local_provider_probe_wiring_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.probe_input is None


def test_output_never_sets_runtime_probe_or_model_flags_even_when_blocked() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(real_endpoint_probed=True, http_request_performed=True, model_call_performed=True)
    )

    assert decision.wiring_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_runtime_api_contract_candidate_is_future_gated_not_added() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(
            probe_wiring_class="api_route_readiness_future",
            runtime_api_readiness_class="api_contract_candidate",
        )
    )

    assert decision.wiring_readiness_status == "future_gated"
    assert "api_route_readiness_future_requires_future_runtime_boundary" in decision.required_future_gates
    assert decision.runtime_api_classification == "future_runtime_api_contract_not_added"
    assert decision.api_route_added is False


def test_runtime_command_contract_candidate_is_future_gated_not_added() -> None:
    decision = validate_local_provider_probe_wiring_request(
        _request(
            probe_wiring_class="runtime_command_readiness_future",
            runtime_api_readiness_class="runtime_command_contract_candidate",
        )
    )

    assert decision.wiring_readiness_status == "future_gated"
    assert "runtime_command_readiness_future_requires_future_runtime_boundary" in decision.required_future_gates
    assert decision.runtime_command_added is False
