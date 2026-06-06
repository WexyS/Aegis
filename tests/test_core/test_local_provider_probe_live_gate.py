from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_live_gate import (
    LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_LIVE_GATE_VERSION,
    validate_local_provider_probe_live_gate_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-live-gate:aegis:1",
        "live_gate_class": "localhost_model_list_probe_gate",
        "live_gate_status_class": "design_gate_ready_metadata_only",
        "future_live_transport_class": "no_transport",
        "endpoint_host_class": "localhost",
        "endpoint_scope_class": "models_list_metadata_future",
        "payload_policy_class": "empty_metadata_request_only",
        "logging_redaction_class": "response_shape_only_future",
        "timeout_policy_class": "bounded_short_timeout",
        "cancellation_policy_class": "cancellation_supported_candidate",
        "future_result_class": "future_model_list_candidate",
        "namespace": "local_provider_probe_live_gate",
        "source_refs": [{"ref_id": "synthetic:live-gate", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "paired_probe_boundary_ref": "probe-boundary:synthetic:1",
        "paired_probe_wiring_ref": "probe-wiring:synthetic:1",
        "paired_mock_runner_ref": "mock-runner:synthetic:1",
        "limitations": ["design gate only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        live_gate_status="design_gate_ready_metadata_only",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_live_gate=False,
        evidence_provided_by_mock_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        api_route_added=False,
        runtime_command_added=False,
        scheduler_added=False,
        live_probe_performed=False,
        real_endpoint_probed=False,
        socket_opened=False,
        http_request_performed=False,
        provider_probed=False,
        real_transport_used=False,
        mock_transport_only=True,
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
        response_body_logged=False,
        secret_logged=False,
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
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_live_gate is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.api_route_added is False
    assert decision.runtime_command_added is False
    assert decision.scheduler_added is False
    assert decision.live_probe_performed is False
    assert decision.real_endpoint_probed is False
    assert decision.socket_opened is False
    assert decision.http_request_performed is False
    assert decision.provider_probed is False
    assert decision.real_transport_used is False
    assert decision.mock_transport_only is False
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
    assert decision.response_body_logged is False
    assert decision.secret_logged is False
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
    assert (
        decision.live_gate_status.startswith("blocked_by_")
        or decision.live_gate_status.startswith("requires_")
        or decision.live_gate_status == "unknown"
    )
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("live_gate_class", "endpoint_scope_class", "future_result_class", "expected_endpoint_classification"),
    [
        ("localhost_metadata_probe_gate", "provider_root_metadata_future", "future_metadata_success_candidate", "future_metadata_endpoint_candidate_only"),
        ("localhost_model_list_probe_gate", "models_list_metadata_future", "future_model_list_candidate", "future_model_list_candidate_not_availability_proof"),
        ("localhost_health_metadata_probe_gate", "health_metadata_future", "future_metadata_success_candidate", "future_metadata_endpoint_candidate_only"),
    ],
)
def test_valid_localhost_live_gates_are_metadata_only(
    live_gate_class: str,
    endpoint_scope_class: str,
    future_result_class: str,
    expected_endpoint_classification: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(
            live_gate_class=live_gate_class,
            endpoint_scope_class=endpoint_scope_class,
            future_result_class=future_result_class,
        )
    )

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_LIVE_GATE_VERSION
    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.live_gate_classification == "live_gate_metadata_only"
    assert decision.endpoint_classification == expected_endpoint_classification
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("live_gate_class", "live_gate_status_class"),
    [
        ("operator_review_gate", "requires_operator_review"),
        ("evidence_semantics_gate", "requires_negative_evidence_semantics"),
        ("verifier_semantics_gate", "requires_result_classifier"),
    ],
)
def test_review_evidence_and_verifier_gates_are_future_gated(
    live_gate_class: str,
    live_gate_status_class: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(live_gate_class=live_gate_class, live_gate_status_class=live_gate_status_class)
    )

    assert decision.live_gate_status == "future_gated"
    assert decision.live_gate_classification == "future_gated_not_executed"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("live_gate_class", "missing_live_gate_class"),
        ("live_gate_status_class", "missing_live_gate_status_class"),
        ("future_live_transport_class", "missing_future_live_transport_class"),
        ("endpoint_host_class", "missing_endpoint_host_class"),
        ("endpoint_scope_class", "missing_endpoint_scope_class"),
        ("payload_policy_class", "missing_payload_policy_class"),
        ("logging_redaction_class", "missing_logging_redaction_class"),
        ("timeout_policy_class", "missing_timeout_policy_class"),
        ("cancellation_policy_class", "missing_cancellation_policy_class"),
        ("future_result_class", "missing_future_result_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_local_provider_probe_live_gate_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("paired_probe_boundary_ref", "missing_probe_boundary_reference"),
        ("paired_probe_wiring_ref", "missing_probe_wiring_reference"),
        ("paired_mock_runner_ref", "missing_mock_runner_reference"),
    ],
)
def test_missing_paired_references_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize("endpoint_host_class", ["localhost", "loopback"])
def test_localhost_and_loopback_are_future_candidates_only(endpoint_host_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(endpoint_host_class=endpoint_host_class)
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.live_probe_performed is False


@pytest.mark.parametrize("endpoint_host_class", ["lan", "remote", "cloud", "unknown"])
def test_lan_remote_cloud_and_unknown_hosts_are_blocked(endpoint_host_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(endpoint_host_class=endpoint_host_class)
    )

    _assert_blocked(decision, "blocked_by_host")


@pytest.mark.parametrize(
    "future_live_transport_class",
    ["future_injected_http_client", "future_httpx_localhost_only", "future_requests_localhost_only"],
)
def test_future_transport_classes_are_future_gated_not_executed(future_live_transport_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(future_live_transport_class=future_live_transport_class)
    )

    assert decision.live_gate_status == "future_gated"
    assert decision.transport_classification == "future_localhost_transport_not_executed"
    _assert_non_authority(decision)


def test_blocked_real_transport_is_rejected() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(future_live_transport_class="blocked_real_transport")
    )

    _assert_blocked(decision, "blocked_real_transport")


def test_no_transport_means_no_execution() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(future_live_transport_class="no_transport")
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.transport_classification == "no_transport_no_execution"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("endpoint_scope_class", "future_result_class", "expected"),
    [
        ("provider_root_metadata_future", "future_metadata_success_candidate", "future_metadata_endpoint_candidate_only"),
        ("models_list_metadata_future", "future_model_list_candidate", "future_model_list_candidate_not_availability_proof"),
        ("health_metadata_future", "future_metadata_success_candidate", "future_metadata_endpoint_candidate_only"),
    ],
)
def test_metadata_endpoint_scopes_are_design_candidates(
    endpoint_scope_class: str,
    future_result_class: str,
    expected: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(endpoint_scope_class=endpoint_scope_class, future_result_class=future_result_class)
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.endpoint_classification == expected


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
def test_generation_embedding_reranker_multimodal_audio_upload_and_tool_endpoints_block(
    endpoint_scope_class: str,
    reason: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(endpoint_scope_class=endpoint_scope_class)
    )

    _assert_blocked(decision, reason)


def test_unknown_endpoint_blocks() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(endpoint_scope_class="unknown")
    )

    _assert_blocked(decision, "unknown_endpoint_scope_blocked")


@pytest.mark.parametrize("payload_policy_class", ["no_payload", "empty_metadata_request_only"])
def test_safe_payload_policies_are_allowed(payload_policy_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(payload_policy_class=payload_policy_class)
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.payload_classification == "no_payload_or_empty_metadata_request_only"


@pytest.mark.parametrize(
    "payload_policy_class",
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
def test_prompt_context_memory_repo_journal_evidence_and_secret_payloads_block(
    payload_policy_class: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(payload_policy_class=payload_policy_class)
    )

    _assert_blocked(decision, "blocked_by_payload")


@pytest.mark.parametrize(
    "logging_redaction_class",
    ["no_payload_logging", "endpoint_only_redacted", "status_code_only_future", "response_shape_only_future"],
)
def test_redacted_logging_policies_are_allowed(logging_redaction_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(logging_redaction_class=logging_redaction_class)
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.logging_classification == "redacted_metadata_logging_only"


@pytest.mark.parametrize(
    ("logging_redaction_class", "reason"),
    [
        ("response_body_logging_blocked", "response_body_logging_denied"),
        ("secret_logging_blocked", "secret_logging_denied"),
        ("unknown", "unknown_logging_redaction_blocked"),
    ],
)
def test_response_body_secret_and_unknown_logging_are_blocked(
    logging_redaction_class: str,
    reason: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(logging_redaction_class=logging_redaction_class)
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
    decision = validate_local_provider_probe_live_gate_request(
        _request(timeout_policy_class=timeout_policy_class)
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize("cancellation_policy_class", ["missing_cancellation_policy", "unknown"])
def test_cancellation_policy_is_required(cancellation_policy_class: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(cancellation_policy_class=cancellation_policy_class)
    )

    _assert_blocked(decision, "missing_cancellation_policy")


def test_cancellation_not_modeled_is_review_metadata_only() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(cancellation_policy_class="cancellation_not_modeled")
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert decision.cancellation_classification == "cancellation_not_modeled_requires_future_review"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("future_result_class", "live_gate_status_class", "expected"),
    [
        ("future_timeout_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
        ("future_connection_refused_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
        ("future_invalid_response_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
        ("future_unauthorized_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
        ("future_unsupported_endpoint_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
        ("future_cancelled_negative_candidate", "requires_negative_evidence_semantics", "future_negative_candidate_not_runtime_failure"),
    ],
)
def test_future_negative_results_are_future_gated_not_runtime_failures(
    future_result_class: str,
    live_gate_status_class: str,
    expected: str,
) -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(future_result_class=future_result_class, live_gate_status_class=live_gate_status_class)
    )

    assert decision.live_gate_status == "future_gated"
    assert decision.future_result_classification == expected
    assert decision.evidence_provided_by_live_gate is False


def test_negative_result_without_evidence_semantics_gate_blocks() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(future_result_class="future_timeout_negative_candidate")
    )

    _assert_blocked(decision, "negative_result_requires_evidence_semantics_gate")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("future_result_is_provider_health_proof", "future_result_health_proof_denied"),
        ("future_model_list_is_availability_proof", "future_model_list_availability_proof_denied"),
        ("future_negative_result_is_runtime_failure", "future_negative_runtime_failure_claim_denied"),
        ("provider_metadata_is_truth", "provider_metadata_truth_claim_denied"),
        ("model_list_is_truth", "model_list_truth_claim_denied"),
        ("provider_health_is_proof", "provider_health_proof_denied"),
        ("model_availability_is_execution_ready", "model_availability_execution_ready_claim_denied"),
        ("quality_or_benchmark_verified", "benchmark_verification_denied"),
        ("self_reported_identity_is_authority", "self_reported_identity_authority_denied"),
        ("probe_candidate_selects_auto_mode", "auto_mode_selection_claim_denied"),
        ("model_inventory_proves_availability", "model_inventory_availability_proof_denied"),
    ],
)
def test_truthfulness_overclaims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_mock_runner_decision", {"real_transport_used": True}),
        ("local_provider_probe_wiring_decision", {"real_endpoint_probed": True}),
        ("local_provider_probe_boundary_decision", {"http_request_performed": True}),
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
    decision = validate_local_provider_probe_live_gate_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_related_decisions_can_be_referenced() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(
            paired_probe_boundary_ref=None,
            paired_probe_wiring_ref=None,
            paired_mock_runner_ref=None,
        ),
        local_provider_probe_mock_runner_decision=_related(mock_runner_status="mock_runner_ready"),
        local_provider_probe_wiring_decision=_related(wiring_readiness_status="mock_transport_candidate"),
        local_provider_probe_boundary_decision=_related(probe_boundary_status="probe_allowed_candidate"),
    )

    assert decision.live_gate_status == "design_gate_ready_metadata_only"
    assert [ref.label for ref in decision.related_references] == [
        "local_provider_probe_mock_runner",
        "local_provider_probe_wiring",
        "local_provider_probe_boundary",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("api_route_added", "api_route_addition_denied"),
        ("runtime_command_added", "runtime_command_addition_denied"),
        ("scheduler_added", "scheduler_addition_denied"),
        ("live_probe_performed", "live_probe_execution_denied"),
        ("real_endpoint_probed", "real_endpoint_probe_denied"),
        ("socket_opened", "socket_open_denied"),
        ("http_request_performed", "http_request_denied"),
        ("provider_probed", "provider_probe_execution_denied"),
        ("real_transport_used", "real_transport_use_denied"),
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
        ("response_body_logged", "response_body_logging_denied"),
        ("secret_logged", "secret_logging_denied"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
        ("evidence_provided_by_live_gate", "live_gate_cannot_provide_evidence"),
        ("verifier_success", "live_gate_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_execution_authority_logging_and_proof_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_live_gate_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request()
    original_request = deepcopy(request)
    related = _related(mock_runner_status="mock_runner_ready")
    original_status = related.mock_runner_status

    decision = validate_local_provider_probe_live_gate_request(
        request,
        local_provider_probe_mock_runner_decision=related,
    )

    assert request == original_request
    assert related.mock_runner_status == original_status
    assert decision.probe_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_local_provider_probe_live_gate_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.probe_input is None


def test_output_never_sets_live_transport_probe_or_model_flags_even_when_blocked() -> None:
    decision = validate_local_provider_probe_live_gate_request(
        _request(live_probe_performed=True, http_request_performed=True, model_call_performed=True)
    )

    assert decision.live_gate_status.startswith("blocked_by_")
    _assert_non_authority(decision)
