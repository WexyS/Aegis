from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_mock_runner import (
    LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_MOCK_RUNNER_VERSION,
    validate_local_provider_probe_mock_runner_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-mock-runner:aegis:1",
        "runner_request_class": "mock_models_list_probe",
        "mock_result_class": "mock_success_metadata_candidate",
        "runner_readiness_class": "mock_runner_ready",
        "metadata_response_shape_class": "models_list_shape_candidate",
        "namespace": "local_provider_probe_mock_runner",
        "source_refs": [{"ref_id": "synthetic:mock-runner", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "paired_probe_wiring_ref": "probe-wiring:synthetic:1",
        "paired_probe_boundary_ref": "probe-boundary:synthetic:1",
        "limitations": ["mock metadata only"],
        "unknowns": [],
        "mock_transport_only": True,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        wiring_readiness_status="mock_transport_candidate",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_mock_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        api_route_added=False,
        runtime_command_added=False,
        scheduler_added=False,
        real_endpoint_probed=False,
        socket_opened=False,
        http_request_performed=False,
        provider_probed=False,
        mock_transport_only=True,
        real_transport_used=False,
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
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_mock_probe is False
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
    assert decision.mock_transport_only is True
    assert decision.real_transport_used is False
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
    assert (
        decision.mock_runner_status.startswith("blocked_by_")
        or decision.mock_runner_status.startswith("requires_")
        or decision.mock_runner_status == "unknown"
    )
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("runner_request_class", "shape_class"),
    [
        ("mock_provider_root_probe", "provider_metadata_shape_candidate"),
        ("mock_models_list_probe", "models_list_shape_candidate"),
        ("mock_health_metadata_probe", "health_metadata_shape_candidate"),
    ],
)
def test_valid_mock_metadata_probes_are_metadata_only(
    runner_request_class: str,
    shape_class: str,
) -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(runner_request_class=runner_request_class, metadata_response_shape_class=shape_class)
    )

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_MOCK_RUNNER_VERSION
    assert decision.mock_runner_status == "mock_runner_ready"
    assert decision.runner_classification == "mock_transport_runner_metadata_only"
    assert decision.mock_result_classification == "mock_success_metadata_only_not_health_proof"
    _assert_non_authority(decision)


def test_mock_success_result_remains_candidate_only() -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request())

    assert decision.mock_runner_status == "mock_runner_ready"
    assert decision.response_shape_classification == "models_list_shape_candidate_not_availability_proof"
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False


@pytest.mark.parametrize(
    ("runner_request_class", "mock_result_class"),
    [
        ("mock_timeout_probe", "mock_timeout_negative_candidate"),
        ("mock_connection_refused_probe", "mock_connection_refused_negative_candidate"),
        ("mock_invalid_response_probe", "mock_invalid_response_negative_candidate"),
        ("mock_unauthorized_probe", "mock_unauthorized_negative_candidate"),
    ],
)
def test_mock_negative_results_become_candidate_metadata_only(
    runner_request_class: str,
    mock_result_class: str,
) -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(
            runner_request_class=runner_request_class,
            mock_result_class=mock_result_class,
            metadata_response_shape_class="malformed_response_negative_candidate",
        )
    )

    assert decision.mock_runner_status == "mock_runner_ready"
    assert decision.mock_result_classification == "negative_mock_candidate_metadata_only_not_runtime_failure"
    assert decision.evidence_provided_by_mock_probe is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("runner_request_class", "missing_runner_request_class"),
        ("mock_result_class", "missing_mock_result_class"),
        ("runner_readiness_class", "missing_runner_readiness_class"),
        ("metadata_response_shape_class", "missing_metadata_response_shape_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


def test_missing_probe_wiring_reference_blocks() -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(paired_probe_wiring_ref=None))

    _assert_blocked(decision, "missing_probe_wiring_reference")


def test_missing_probe_boundary_reference_blocks() -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(paired_probe_boundary_ref=None))

    _assert_blocked(decision, "missing_probe_boundary_reference")


@pytest.mark.parametrize(
    ("shape_class", "expected"),
    [
        ("provider_metadata_shape_candidate", "metadata_shape_candidate_only"),
        ("models_list_shape_candidate", "models_list_shape_candidate_not_availability_proof"),
        ("health_metadata_shape_candidate", "metadata_shape_candidate_only"),
        ("empty_response_negative_candidate", "negative_response_shape_candidate_only"),
        ("malformed_response_negative_candidate", "negative_response_shape_candidate_only"),
    ],
)
def test_response_shape_classification_is_candidate_only(shape_class: str, expected: str) -> None:
    result = "mock_invalid_response_negative_candidate" if "negative" in shape_class else "mock_success_metadata_candidate"
    runner = "mock_invalid_response_probe" if "negative" in shape_class else "mock_models_list_probe"
    decision = validate_local_provider_probe_mock_runner_request(
        _request(
            runner_request_class=runner,
            mock_result_class=result,
            metadata_response_shape_class=shape_class,
        )
    )

    assert decision.mock_runner_status == "mock_runner_ready"
    assert decision.response_shape_classification == expected


def test_unknown_shape_remains_unknown() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(metadata_response_shape_class="unknown_shape")
    )

    _assert_blocked(decision, "unknown_response_shape")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mock_success_is_health_proof", "mock_success_health_proof_denied"),
        ("mock_model_list_is_availability_proof", "mock_model_list_availability_proof_denied"),
        ("mock_health_metadata_is_verifier_success", "mock_health_verifier_success_claim_denied"),
        ("negative_mock_result_is_runtime_failure", "negative_mock_runtime_failure_claim_denied"),
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
    decision = validate_local_provider_probe_mock_runner_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_wiring_decision", {"real_endpoint_probed": True}),
        ("local_provider_probe_boundary_decision", {"real_transport_used": True}),
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
    decision = validate_local_provider_probe_mock_runner_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_probe_wiring_and_boundary_decisions_can_be_referenced() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(paired_probe_wiring_ref=None, paired_probe_boundary_ref=None),
        local_provider_probe_wiring_decision=_related(wiring_readiness_status="mock_transport_candidate"),
        local_provider_probe_boundary_decision=_related(probe_boundary_status="probe_allowed_candidate"),
    )

    assert decision.mock_runner_status == "mock_runner_ready"
    assert [ref.label for ref in decision.related_references] == [
        "local_provider_probe_wiring",
        "local_provider_probe_boundary",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


@pytest.mark.parametrize(
    ("runner_readiness_class", "reason"),
    [
        ("requires_probe_wiring", "missing_probe_wiring_reference"),
        ("requires_probe_boundary", "missing_probe_boundary_reference"),
        ("blocked_by_transport", "blocked_by_transport"),
        ("blocked_by_endpoint_scope", "blocked_by_endpoint_scope"),
        ("blocked_by_payload", "blocked_by_payload"),
        ("blocked_by_secret_policy", "blocked_by_secret_policy"),
        ("blocked_by_timeout_policy", "blocked_by_timeout_policy"),
        ("blocked_by_unknown_host", "blocked_by_unknown_host"),
        ("blocked_by_real_transport", "blocked_by_real_transport"),
    ],
)
def test_blocked_runner_readiness_metadata_blocks(runner_readiness_class: str, reason: str) -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(runner_readiness_class=runner_readiness_class)
    )

    _assert_blocked(decision, reason)


def test_future_gated_runner_readiness_is_not_executed() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(runner_readiness_class="future_gated")
    )

    assert decision.mock_runner_status == "future_gated"
    assert decision.runner_classification == "future_gated_not_executed"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("api_route_added", "api_route_addition_denied"),
        ("runtime_command_added", "runtime_command_addition_denied"),
        ("scheduler_added", "scheduler_addition_denied"),
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
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
        ("evidence_provided_by_mock_probe", "mock_runner_cannot_provide_evidence"),
        ("verifier_success", "mock_runner_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_execution_authority_and_proof_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_mock_transport_only_false_is_rejected_for_candidate_results() -> None:
    decision = validate_local_provider_probe_mock_runner_request(_request(mock_transport_only=False))

    _assert_blocked(decision, "mock_transport_only_required")


def test_mock_transport_only_false_can_describe_not_executed_blocked_state_without_execution() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(
            mock_transport_only=False,
            mock_result_class="not_executed",
            runner_readiness_class="future_gated",
            metadata_response_shape_class="provider_metadata_shape_candidate",
        )
    )

    assert decision.mock_runner_status == "future_gated"
    assert decision.mock_transport_only is True
    _assert_non_authority(decision)


def test_mismatched_negative_runner_request_is_blocked() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(
            runner_request_class="mock_models_list_probe",
            mock_result_class="mock_timeout_negative_candidate",
            metadata_response_shape_class="empty_response_negative_candidate",
        )
    )

    _assert_blocked(decision, "mock_timeout_runner_mismatch")


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request()
    original_request = deepcopy(request)
    related = _related(wiring_readiness_status="mock_transport_candidate")
    original_status = related.wiring_readiness_status

    decision = validate_local_provider_probe_mock_runner_request(
        request,
        local_provider_probe_wiring_decision=related,
    )

    assert request == original_request
    assert related.wiring_readiness_status == original_status
    assert decision.probe_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_local_provider_probe_mock_runner_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.probe_input is None


def test_output_never_sets_real_transport_probe_or_model_flags_even_when_blocked() -> None:
    decision = validate_local_provider_probe_mock_runner_request(
        _request(real_transport_used=True, http_request_performed=True, model_call_performed=True)
    )

    assert decision.mock_runner_status.startswith("blocked_by_")
    _assert_non_authority(decision)
