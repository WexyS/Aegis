from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_runner import (
    LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_RUNNER_VERSION,
    LocalProviderProbeCancelled,
    LocalProviderProbeHttpResponse,
    LocalProviderProbeTransportRequest,
    run_local_provider_probe,
)


class MockTransport:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response or LocalProviderProbeHttpResponse(
            status_code=200,
            json_data={"object": "list", "data": [{"id": "synthetic-model"}]},
        )
        self.exc = exc
        self.calls: list[LocalProviderProbeTransportRequest] = []

    def __call__(self, request: LocalProviderProbeTransportRequest) -> object:
        self.calls.append(request)
        if self.exc is not None:
            raise self.exc
        return self.response


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-runner:aegis:1",
        "endpoint_url": "http://localhost:1234/v1/models",
        "endpoint_class": "models_list_metadata",
        "timeout_seconds": 2.0,
        "namespace": "local_provider_probe_runner",
        "source_refs": [{"ref_id": "synthetic:probe-runner", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "paired_live_gate_ref": "live-gate:synthetic:1",
        "limitations": ["localhost metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION,
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
        evidence_provided_by_probe_runner=False,
        evidence_provided_by_live_gate=False,
        evidence_provided_by_mock_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        api_route_added=False,
        runtime_command_added=False,
        scheduler_added=False,
        provider_health_verified=False,
        model_availability_verified=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
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
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_probe_runner is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.api_route_added is False
    assert decision.runtime_command_added is False
    assert decision.scheduler_added is False
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
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
        decision.runner_status.startswith("blocked_by_")
        or decision.runner_status == "not_executed"
    )
    _assert_non_authority(decision)


def test_valid_localhost_provider_root_metadata_probe_uses_injected_transport() -> None:
    transport = MockTransport(
        LocalProviderProbeHttpResponse(status_code=200, json_data={"provider": "lm-studio"})
    )

    decision = run_local_provider_probe(
        _request(endpoint_url="http://localhost:1234/v1", endpoint_class="provider_root_metadata"),
        transport=transport,
    )

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_RUNNER_VERSION
    assert decision.runner_status == "metadata_success_candidate"
    assert decision.result_class == "metadata_success_candidate"
    assert decision.response_shape_classification == "provider_metadata_shape_candidate"
    assert transport.calls == [
        LocalProviderProbeTransportRequest(
            method="GET",
            url="http://localhost:1234/v1",
            timeout_seconds=2.0,
            headers={},
        )
    ]
    _assert_non_authority(decision)


def test_valid_localhost_models_list_metadata_probe_uses_injected_transport() -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(), transport=transport)

    assert decision.runner_status == "model_list_success_candidate"
    assert decision.result_class == "model_list_success_candidate"
    assert decision.response_shape_classification == "models_list_shape_candidate"
    assert decision.model_count_candidate == 1
    assert decision.model_availability_verified is False
    assert len(transport.calls) == 1
    assert transport.calls[0].body is None
    assert transport.calls[0].headers == {}
    _assert_non_authority(decision)


@pytest.mark.parametrize("endpoint_url", ["http://127.0.0.1:1234/v1/models", "http://[::1]:1234/v1/models"])
def test_loopback_endpoints_are_accepted(endpoint_url: str) -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(endpoint_url=endpoint_url), transport=transport)

    assert decision.runner_status == "model_list_success_candidate"
    assert decision.host_classification == "loopback_only"
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (TimeoutError(), "timeout_negative_candidate"),
        (ConnectionRefusedError(), "connection_refused_negative_candidate"),
        (OSError(), "unreachable_negative_candidate"),
        (LocalProviderProbeCancelled(), "cancelled_negative_candidate"),
    ],
)
def test_transport_exceptions_become_negative_candidates(exc: Exception, expected: str) -> None:
    decision = run_local_provider_probe(_request(), transport=MockTransport(exc=exc))

    assert decision.runner_status == expected
    assert decision.result_class == expected
    assert decision.evidence_provided_by_probe_runner is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (LocalProviderProbeHttpResponse(status_code=401, json_data={"error": "unauthorized"}), "unauthorized_negative_candidate"),
        (LocalProviderProbeHttpResponse(status_code=404, json_data={"error": "not found"}), "unsupported_endpoint_negative_candidate"),
        (LocalProviderProbeHttpResponse(status_code=200, json_data="not a shape"), "invalid_response_negative_candidate"),
    ],
)
def test_invalid_unauthorized_and_unsupported_responses_become_negative_candidates(
    response: LocalProviderProbeHttpResponse,
    expected: str,
) -> None:
    decision = run_local_provider_probe(_request(), transport=MockTransport(response))

    assert decision.runner_status == expected
    assert decision.result_class == expected
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("endpoint_url", "reason"),
    [
        ("http://192.168.1.10:1234/v1/models", "lan_endpoint_blocked"),
        ("http://8.8.8.8:1234/v1/models", "cloud_or_remote_endpoint_blocked"),
        ("http://example.com:1234/v1/models", "remote_or_unknown_host_blocked"),
        ("http://localhost.evil.test:1234/v1/models", "spoofed_localhost_blocked"),
        ("http://127.0.0.1.evil.test:1234/v1/models", "spoofed_localhost_blocked"),
        ("not a url", "unsupported_url_scheme"),
    ],
)
def test_non_local_spoofed_and_malformed_urls_block_before_transport(
    endpoint_url: str,
    reason: str,
) -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(endpoint_url=endpoint_url), transport=transport)

    _assert_blocked(decision, reason)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("endpoint_class", "reason"),
    [
        ("generation", "generation_endpoint_blocked"),
        ("chat_completion", "chat_completion_endpoint_blocked"),
        ("completion", "completion_endpoint_blocked"),
        ("embeddings", "embedding_endpoint_blocked"),
        ("rerank", "rerank_endpoint_blocked"),
        ("multimodal", "multimodal_endpoint_blocked"),
        ("audio", "audio_endpoint_blocked"),
        ("file_upload", "file_upload_endpoint_blocked"),
        ("tool_call", "tool_call_endpoint_blocked"),
        ("unknown", "unknown_endpoint_blocked"),
    ],
)
def test_blocked_endpoint_classes_reject_before_transport(endpoint_class: str, reason: str) -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(endpoint_class=endpoint_class), transport=transport)

    _assert_blocked(decision, reason)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("endpoint_url", "reason"),
    [
        ("http://localhost:1234/v1/chat/completions", "chat_completion_endpoint_blocked"),
        ("http://localhost:1234/v1/completions", "completion_endpoint_blocked"),
        ("http://localhost:1234/v1/embeddings", "embedding_endpoint_blocked"),
        ("http://localhost:1234/v1/rerank", "rerank_endpoint_blocked"),
        ("http://localhost:1234/v1/audio/transcriptions", "audio_endpoint_blocked"),
        ("http://localhost:1234/v1/files", "file_upload_endpoint_blocked"),
        ("http://localhost:1234/v1/tools", "tool_call_endpoint_blocked"),
    ],
)
def test_blocked_endpoint_paths_reject_before_transport(endpoint_url: str, reason: str) -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(
        _request(endpoint_url=endpoint_url, endpoint_class="provider_root_metadata"),
        transport=transport,
    )

    _assert_blocked(decision, reason)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("request_body", {"prompt": "hello"}, "request_body_payload_blocked"),
        ("prompt", "hello", "prompt_payload_blocked"),
        ("context", "repo data", "context_payload_blocked"),
        ("memory", "memory data", "memory_payload_blocked"),
        ("repo_content", "source", "repo_content_payload_blocked"),
        ("raw_journal", "journal", "raw_journal_payload_blocked"),
        ("raw_evidence", "evidence", "raw_evidence_payload_blocked"),
        ("headers", {"Authorization": "Bearer secret"}, "authorization_header_denied"),
        ("validate_api_key", True, "api_key_validation_denied"),
        ("read_secret", True, "secret_read_denied"),
        ("log_response_body", True, "response_body_logging_denied"),
        ("log_secret", True, "secret_logging_denied"),
    ],
)
def test_payload_secret_and_logging_requests_reject_before_transport(
    field: str,
    value: object,
    reason: str,
) -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(**{field: value}), transport=transport)

    _assert_blocked(decision, reason)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("endpoint_url", "missing_endpoint_url"),
        ("endpoint_class", "missing_endpoint_class"),
        ("timeout_seconds", "missing_timeout_seconds"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = run_local_provider_probe(_request(**{field: None}), transport=MockTransport())

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = run_local_provider_probe(_request(source_refs=[], provenance=[]), transport=MockTransport())

    _assert_blocked(decision, "missing_source_refs_or_provenance")


def test_missing_live_gate_reference_blocks_without_transport() -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(_request(paired_live_gate_ref=None), transport=transport)

    _assert_blocked(decision, "missing_live_gate_reference")
    assert transport.calls == []


def test_safe_live_gate_decision_can_replace_ref() -> None:
    transport = MockTransport()

    decision = run_local_provider_probe(
        _request(paired_live_gate_ref=None),
        transport=transport,
        local_provider_probe_live_gate_decision=_related(live_gate_status="design_gate_ready_metadata_only"),
    )

    assert decision.runner_status == "model_list_success_candidate"
    assert [ref.label for ref in decision.related_references] == ["local_provider_probe_live_gate"]
    assert all(ref.reference_only for ref in decision.related_references)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("metadata_success_is_health_proof", "metadata_success_health_proof_denied"),
        ("model_list_is_availability_proof", "model_list_availability_proof_denied"),
        ("negative_result_is_runtime_failure", "negative_runtime_failure_claim_denied"),
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
    decision = run_local_provider_probe(_request(**{field: True}), transport=MockTransport())

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_live_gate_decision", {"model_call_performed": True}),
        ("local_provider_probe_wiring_decision", {"generation_performed": True}),
        ("local_provider_probe_boundary_decision", {"context_payload_sent": True}),
        ("local_provider_probe_mock_runner_decision", {"authorization_header_sent": True}),
        ("local_provider_health_decision", {"provider_health_verified": True}),
        ("model_auto_mode_decision", {"auto_mode_execution_allowed": True}),
        ("local_model_inventory_decision", {"model_availability_verified": True}),
        ("local_model_context_profile_decision", {"benchmark_claim_verified": True}),
        ("context_policy_decision", {"memory_payload_sent": True}),
        ("identity_scope_decision", {"runtime_dispatch_allowed": True}),
        ("memory_governance_decision", {"memory_payload_sent": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("capability_lease_decision", {"lease_grant": True}),
        ("mission_control_decision", {"frontend_authority": True}),
        ("tool_simulation_decision", {"tool_call_performed": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, kwargs: dict[str, object]) -> None:
    decision = run_local_provider_probe(
        _request(),
        transport=MockTransport(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
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
        ("cloud_provider_called", "cloud_provider_call_denied"),
        ("lan_or_remote_endpoint_called", "lan_or_remote_endpoint_call_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("response_body_logged", "response_body_logging_denied"),
        ("secret_logged", "secret_logging_denied"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
        ("evidence_provided_by_probe_runner", "probe_runner_cannot_provide_evidence"),
        ("verifier_success", "probe_runner_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_execution_authority_and_proof_flags_are_rejected(field: str, reason: str) -> None:
    decision = run_local_provider_probe(_request(**{field: True}), transport=MockTransport())

    _assert_blocked(decision, reason)


def test_missing_transport_does_not_execute() -> None:
    decision = run_local_provider_probe(_request(), transport=None)

    _assert_blocked(decision, "missing_transport")
    assert decision.result_class == "not_executed"


def test_successful_metadata_is_not_proof_and_negative_is_not_runtime_failure() -> None:
    success = run_local_provider_probe(_request(), transport=MockTransport())
    negative = run_local_provider_probe(_request(), transport=MockTransport(exc=TimeoutError()))

    assert success.model_availability_verified is False
    assert success.provider_health_verified is False
    assert success.verifier_success is False
    assert negative.result_class == "timeout_negative_candidate"
    assert negative.truthfulness_classification == (
        "metadata_result_not_health_model_identity_benchmark_evidence_or_verifier_proof"
    )
    assert negative.runtime_state_mutated is False


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request()
    original_request = deepcopy(request)
    related = _related(live_gate_status="design_gate_ready_metadata_only")
    original_status = related.live_gate_status

    decision = run_local_provider_probe(
        request,
        transport=MockTransport(),
        local_provider_probe_live_gate_decision=related,
    )

    assert request == original_request
    assert related.live_gate_status == original_status
    assert decision.probe_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = run_local_provider_probe(None, transport=MockTransport())

    _assert_blocked(decision, "missing_request")
    assert decision.probe_input is None


def test_output_never_sets_runtime_model_or_payload_flags_even_when_blocked() -> None:
    decision = run_local_provider_probe(
        _request(model_call_performed=True, context_payload_sent=True, verifier_success=True),
        transport=MockTransport(),
    )

    assert decision.runner_status.startswith("blocked_by_")
    _assert_non_authority(decision)
