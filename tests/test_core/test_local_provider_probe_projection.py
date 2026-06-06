from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_projection import (
    LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_PROJECTION_VERSION,
    validate_local_provider_probe_projection_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-projection:aegis:1",
        "projection_source_class": "manual_smoke_result",
        "probe_result_class": "unreachable_negative_candidate",
        "maintenance_surface_status_class": "provider_probe_unreachable_candidate",
        "truth_label_class": "retry_requires_operator_approval",
        "display_severity_class": "warning",
        "freshness_class": "current_manual_smoke",
        "namespace": "local_provider_probe_projection",
        "source_refs": [{"ref_id": "manual-smoke:lm-studio:models:1", "ref_type": "probe_result_summary"}],
        "provenance": [{"ref_id": "operator-approved:127.0.0.1:1234:v1:models", "ref_type": "manual_smoke_scope"}],
        "limitations": ["projection only", "raw response body not captured"],
        "unknowns": ["LM Studio endpoint reachability may change"],
        "model_count_candidate": None,
        "response_status_code": None,
        "response_shape_classification": "not_observed",
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        runner_status="unreachable_negative_candidate",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_probe_projection=False,
        evidence_provided_by_probe_runner=False,
        evidence_provided_by_live_gate=False,
        evidence_provided_by_mock_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        maintenance_health_mutated=False,
        runtime_health_mutated=False,
        provider_health_verified=False,
        model_availability_verified=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
        auto_mode_selection_performed=False,
        live_probe_performed=False,
        real_endpoint_probed=False,
        socket_opened=False,
        http_request_performed=False,
        api_route_added=False,
        runtime_command_added=False,
        scheduler_added=False,
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
        response_body_logged=False,
        secret_logged=False,
        cloud_provider_called=False,
        lan_or_remote_endpoint_called=False,
        data_sent_external=False,
        runtime_state_mutated=False,
        journal_mutated=False,
        evidence_mutated=False,
        replay_mutated=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_probe_projection is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.maintenance_health_mutated is False
    assert decision.runtime_health_mutated is False
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
    assert decision.auto_mode_selection_performed is False
    assert decision.model_loaded is False
    assert decision.model_call_performed is False
    assert decision.generation_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_inference_performed is False
    assert decision.live_probe_performed is False
    assert decision.real_endpoint_probed is False
    assert decision.socket_opened is False
    assert decision.http_request_performed is False
    assert decision.api_route_added is False
    assert decision.runtime_command_added is False
    assert decision.scheduler_added is False
    assert decision.prompt_payload_sent is False
    assert decision.context_payload_sent is False
    assert decision.memory_payload_sent is False
    assert decision.repo_payload_sent is False
    assert decision.raw_journal_payload_sent is False
    assert decision.raw_evidence_payload_sent is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.authorization_header_sent is False
    assert decision.response_body_logged is False
    assert decision.secret_logged is False
    assert decision.cloud_provider_called is False
    assert decision.lan_or_remote_endpoint_called is False
    assert decision.data_sent_external is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def _assert_blocked(decision: object, reason: str) -> None:
    assert reason in decision.failure_reasons
    assert decision.projection_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_valid_manual_smoke_unreachable_result_projects_as_negative_candidate_only() -> None:
    decision = validate_local_provider_probe_projection_request(_request())

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_PROJECTION_VERSION
    assert decision.projection_status == "negative_candidate_projected"
    assert decision.display_status_candidate == "provider_probe_unreachable_candidate"
    assert decision.result_semantics == "unreachable_negative_candidate_not_runtime_failure"
    assert decision.retry_semantics == "retry_requires_operator_approval"
    assert "operator_approval_required_before_retry" in decision.required_operator_actions
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("probe_result_class", "truth_label_class", "expected_semantics"),
    [
        ("metadata_success_candidate", "metadata_candidate_only", "metadata_success_candidate_not_provider_health_proof"),
        ("model_list_success_candidate", "not_model_availability_proof", "model_list_candidate_not_model_availability_proof"),
        ("health_metadata_success_candidate", "not_provider_health_proof", "health_metadata_success_candidate_not_provider_health_proof"),
    ],
)
def test_success_candidates_project_as_metadata_only(
    probe_result_class: str,
    truth_label_class: str,
    expected_semantics: str,
) -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            probe_result_class=probe_result_class,
            maintenance_surface_status_class="provider_probe_candidate_ok",
            truth_label_class=truth_label_class,
            display_severity_class="info",
            response_shape_classification="models_list_shape_candidate",
        )
    )

    assert decision.projection_status == "metadata_candidate_projected"
    assert decision.result_semantics == expected_semantics
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("probe_result_class", "maintenance_status", "expected_semantics"),
    [
        ("timeout_negative_candidate", "provider_probe_timeout_candidate", "timeout_negative_candidate_not_runtime_failure"),
        ("connection_refused_negative_candidate", "provider_probe_unreachable_candidate", "connection_refused_negative_candidate_not_runtime_failure"),
        ("invalid_response_negative_candidate", "provider_probe_invalid_response_candidate", "invalid_response_negative_candidate_not_runtime_failure"),
        ("unauthorized_negative_candidate", "provider_probe_blocked_by_policy", "unauthorized_negative_candidate_not_runtime_failure"),
        ("unsupported_endpoint_negative_candidate", "provider_probe_blocked_by_policy", "unsupported_endpoint_negative_candidate_not_runtime_failure"),
        ("cancelled_negative_candidate", "provider_probe_negative_candidate", "cancelled_negative_candidate_not_runtime_failure"),
    ],
)
def test_negative_result_distinctions_are_preserved(
    probe_result_class: str,
    maintenance_status: str,
    expected_semantics: str,
) -> None:
    truth = "retry_requires_operator_approval" if probe_result_class in {
        "timeout_negative_candidate",
        "connection_refused_negative_candidate",
        "invalid_response_negative_candidate",
    } else "negative_candidate_only"
    decision = validate_local_provider_probe_projection_request(
        _request(
            probe_result_class=probe_result_class,
            maintenance_surface_status_class=maintenance_status,
            truth_label_class=truth,
        )
    )

    assert decision.projection_status == "negative_candidate_projected"
    assert decision.result_semantics == expected_semantics
    assert decision.provider_health_verified is False
    assert decision.runtime_health_mutated is False


def test_empty_model_list_projects_as_empty_metadata_candidate_only() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            probe_result_class="empty_model_list_candidate",
            maintenance_surface_status_class="provider_probe_candidate_ok",
            truth_label_class="metadata_candidate_only",
            display_severity_class="low",
            model_count_candidate=0,
            response_shape_classification="models_list_shape_candidate",
        )
    )

    assert decision.projection_status == "empty_model_list_candidate_projected"
    assert decision.result_semantics == "empty_model_list_candidate_not_runtime_failure_or_availability_proof"
    assert decision.model_availability_verified is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("projection_source_class", "missing_projection_source_class"),
        ("probe_result_class", "missing_probe_result_class"),
        ("maintenance_surface_status_class", "missing_maintenance_surface_status_class"),
        ("truth_label_class", "missing_truth_label_class"),
        ("display_severity_class", "missing_display_severity_class"),
        ("freshness_class", "missing_freshness_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_projection_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_local_provider_probe_projection_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("projection_source_class", "unsupported", "unsupported_projection_source_class"),
        ("probe_result_class", "unsupported", "unsupported_probe_result_class"),
        ("maintenance_surface_status_class", "unsupported", "unsupported_maintenance_surface_status_class"),
        ("truth_label_class", "unsupported", "unsupported_truth_label_class"),
        ("display_severity_class", "urgent", "unsupported_display_severity_class"),
        ("freshness_class", "fresh", "unsupported_freshness_class"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_local_provider_probe_projection_request(_request(**{field: value}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("unreachable_result_is_runtime_failure", "negative_runtime_failure_claim_denied"),
        ("timeout_result_is_runtime_failure", "negative_runtime_failure_claim_denied"),
        ("connection_refused_result_is_runtime_failure", "negative_runtime_failure_claim_denied"),
        ("empty_model_list_is_runtime_failure", "empty_model_list_runtime_failure_claim_denied"),
        ("metadata_success_is_health_proof", "metadata_success_health_proof_denied"),
        ("model_list_is_availability_proof", "model_list_availability_proof_denied"),
        ("downloaded_models_are_availability_proof", "downloaded_models_availability_proof_denied"),
        ("self_reported_identity_is_authority", "self_reported_identity_authority_denied"),
        ("quality_or_benchmark_verified", "benchmark_verification_denied"),
        ("probe_candidate_selects_auto_mode", "auto_mode_selection_claim_denied"),
        ("model_inventory_proves_availability", "model_inventory_availability_proof_denied"),
    ],
)
def test_truthfulness_overclaims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_projection_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_retryable_negative_result_must_preserve_operator_approval() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            probe_result_class="timeout_negative_candidate",
            maintenance_surface_status_class="provider_probe_timeout_candidate",
            truth_label_class="negative_candidate_only",
        )
    )

    _assert_blocked(decision, "retry_requires_operator_approval")


def test_result_status_mismatch_blocks_projection() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            probe_result_class="unreachable_negative_candidate",
            maintenance_surface_status_class="provider_probe_candidate_ok",
        )
    )

    _assert_blocked(decision, "probe_result_status_mismatch")


def test_unknown_projection_source_result_status_and_truth_block() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            projection_source_class="unknown",
            probe_result_class="unknown",
            maintenance_surface_status_class="unknown",
            truth_label_class="unknown",
        )
    )

    assert "unknown_projection_source_blocked" in decision.failure_reasons
    assert "unknown_probe_result_blocked" in decision.failure_reasons
    assert "unknown_maintenance_status_blocked" in decision.failure_reasons
    assert "unknown_truth_label_blocked" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_runner_result_can_be_projected() -> None:
    related = _related(runner_status="unreachable_negative_candidate")

    decision = validate_local_provider_probe_projection_request(
        _request(),
        local_provider_probe_runner_decision=related,
    )

    assert decision.projection_status == "negative_candidate_projected"
    assert [ref.label for ref in decision.related_references] == ["local_provider_probe_runner"]
    assert all(ref.reference_only for ref in decision.related_references)
    assert related.runner_status == "unreachable_negative_candidate"


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_runner_decision", {"provider_health_verified": True}),
        ("local_provider_probe_live_gate_decision", {"live_probe_performed": True}),
        ("local_provider_probe_mock_runner_decision", {"model_availability_verified": True}),
        ("local_provider_probe_wiring_decision", {"http_request_performed": True}),
        ("local_provider_probe_boundary_decision", {"runtime_dispatch_allowed": True}),
        ("local_provider_probe_design_decision", {"model_call_performed": True}),
        ("local_provider_health_decision", {"provider_health_verified": True}),
        ("local_model_context_profile_decision", {"benchmark_claim_verified": True}),
        ("model_auto_mode_decision", {"auto_mode_selection_performed": True}),
        ("local_model_inventory_decision", {"model_inventory_proves_availability": True}),
        ("context_policy_decision", {"context_payload_sent": True}),
        ("identity_scope_decision", {"authority": True}),
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
    decision = validate_local_provider_probe_projection_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("maintenance_health_mutated", "maintenance_health_mutation_denied"),
        ("runtime_health_mutated", "runtime_health_mutation_denied"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
        ("auto_mode_selection_performed", "auto_mode_selection_denied"),
        ("live_probe_performed", "live_probe_execution_denied"),
        ("real_endpoint_probed", "real_endpoint_probe_denied"),
        ("socket_opened", "socket_open_denied"),
        ("http_request_performed", "http_request_denied"),
        ("api_route_added", "api_route_addition_denied"),
        ("runtime_command_added", "runtime_command_addition_denied"),
        ("scheduler_added", "scheduler_addition_denied"),
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
        ("response_body_logged", "response_body_logging_denied"),
        ("secret_logged", "secret_logging_denied"),
        ("cloud_provider_called", "cloud_provider_call_denied"),
        ("lan_or_remote_endpoint_called", "lan_or_remote_endpoint_call_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("evidence_provided_by_probe_projection", "probe_projection_cannot_provide_evidence"),
        ("verifier_success", "probe_projection_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_execution_authority_health_mutation_and_proof_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_projection_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_not_executed_projection_is_not_provider_status() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(
            projection_source_class="maintenance_scan_projection_future",
            probe_result_class="not_executed",
            maintenance_surface_status_class="provider_probe_future_gated",
            truth_label_class="operator_review_recommended",
            display_severity_class="info",
        )
    )

    assert decision.projection_status == "not_executed_projected"
    assert decision.retry_semantics == "no_retry_authorized_by_projection"
    _assert_non_authority(decision)


def test_stale_negative_projection_recommends_freshness_review_without_execution() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(freshness_class="stale_candidate")
    )

    assert decision.projection_status == "negative_candidate_projected"
    assert "freshness_review_recommended" in decision.required_operator_actions
    assert decision.live_probe_performed is False


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_local_provider_probe_projection_request(
        request,
        local_provider_probe_runner_decision=related,
    )

    assert request == request_before
    assert related.__dict__ == related_before
    assert decision.projection_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.projection_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_local_provider_probe_projection_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.projection_input is None


def test_output_never_sets_runtime_model_or_health_flags_even_when_blocked() -> None:
    decision = validate_local_provider_probe_projection_request(
        _request(model_call_performed=True, http_request_performed=True, provider_health_verified=True)
    )

    assert decision.projection_status.startswith("blocked_by_")
    _assert_non_authority(decision)
