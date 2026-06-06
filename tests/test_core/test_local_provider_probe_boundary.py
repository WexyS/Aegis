from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_probe_boundary import (
    LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_PROBE_BOUNDARY_VERSION,
    validate_local_provider_probe_boundary_request,
)


def _endpoint(**overrides: object) -> dict[str, object]:
    endpoint: dict[str, object] = {
        "url": "http://localhost:1234/v1/models",
        "metadata_endpoint_class": "models_list_metadata_candidate",
    }
    endpoint.update(overrides)
    return endpoint


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-provider-probe-boundary:aegis:1",
        "provider_class": "lm_studio_localhost_openai_compatible_metadata",
        "endpoint_host_class": "localhost",
        "endpoint_url_metadata": _endpoint(),
        "probe_phase": "models_list_probe_candidate",
        "probe_scope": "models_list_metadata_only",
        "timeout_ms": 1500,
        "payload_class": "empty_get",
        "secret_policy": "no_secret",
        "namespace": "local_provider_probe_boundary",
        "source_refs": [{"ref_id": "synthetic:provider-probe-boundary", "ref_type": "test_fixture"}],
        "provenance": [{"ref_id": "caller:metadata", "ref_type": "test_fixture"}],
        "limitations": ["metadata-only boundary"],
        "unknowns": [],
        "authorization_header_present": False,
        "operator_approval_future_required": True,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        readiness_status="metadata_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_probe=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        provider_health_verified=False,
        model_availability_verified=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
        provider_probed=False,
        endpoint_probed=False,
        http_request_performed=False,
        socket_opened=False,
        provider_authenticated=False,
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
        cloud_provider_called=False,
        lan_or_remote_endpoint_called=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_probe is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
    assert decision.provider_probed is False
    assert decision.endpoint_probed is False
    assert decision.http_request_performed is False
    assert decision.socket_opened is False
    assert decision.provider_authenticated is False
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
    assert decision.probe_boundary_status.startswith("blocked_by_") or decision.probe_boundary_status == "unknown"
    _assert_non_authority(decision)


def test_valid_lm_studio_localhost_metadata_probe_request_is_candidate_only() -> None:
    decision = validate_local_provider_probe_boundary_request(_request())

    assert decision.contract_version == LOCAL_PROVIDER_PROBE_BOUNDARY_VERSION
    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert decision.provider_class == "lm_studio_localhost_openai_compatible_metadata"
    assert decision.endpoint_classification == "models_list_metadata_candidate_not_availability_proof"
    assert decision.truthfulness_classification == "metadata_candidate_not_health_or_model_proof"
    assert decision.endpoint_metadata is not None
    assert decision.endpoint_metadata.is_loopback_url is True
    _assert_non_authority(decision)


def test_valid_openai_compatible_localhost_model_list_probe_request_is_candidate_only() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(provider_class="openai_compatible_localhost_metadata")
    )

    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert decision.model_availability_verified is False


def test_mock_provider_metadata_request_is_candidate_only() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(
            provider_class="mock_test_provider_metadata",
            endpoint_host_class="loopback",
            endpoint_url_metadata=_endpoint(url="http://127.0.0.1:9999/health", metadata_endpoint_class="mock_metadata_candidate"),
            probe_phase="health_metadata_probe_candidate",
            probe_scope="mock_metadata_only",
            payload_class="empty_head",
        )
    )

    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert decision.endpoint_classification == "local_metadata_endpoint_candidate"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("provider_class", "missing_provider_class"),
        ("endpoint_host_class", "missing_endpoint_host_class"),
        ("probe_phase", "missing_probe_phase"),
        ("probe_scope", "missing_probe_scope"),
        ("timeout_ms", "missing_timeout_ms"),
        ("payload_class", "missing_payload_class"),
        ("secret_policy", "missing_secret_policy"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_endpoint_descriptor_blocks() -> None:
    decision = validate_local_provider_probe_boundary_request(_request(endpoint_url_metadata={}))

    _assert_blocked(decision, "missing_endpoint_descriptor")


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_local_provider_probe_boundary_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


@pytest.mark.parametrize(
    ("endpoint_host_class", "url"),
    [
        ("localhost", "http://localhost:1234/v1/models"),
        ("loopback", "http://127.0.0.1:1234/v1/models"),
        ("loopback", "http://[::1]:1234/v1/models"),
    ],
)
def test_localhost_and_loopback_hosts_are_accepted_as_candidates(endpoint_host_class: str, url: str) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_host_class=endpoint_host_class, endpoint_url_metadata=_endpoint(url=url))
    )

    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert decision.endpoint_metadata is not None
    assert decision.endpoint_metadata.is_loopback_url is True


@pytest.mark.parametrize(
    ("endpoint_host_class", "url"),
    [
        ("lan", "http://192.168.1.10:1234/v1/models"),
        ("remote", "http://example.com/v1/models"),
        ("cloud", "https://api.openai.com/v1/models"),
        ("unknown", "http://provider.invalid/v1/models"),
    ],
)
def test_lan_remote_cloud_and_unknown_hosts_are_blocked(endpoint_host_class: str, url: str) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_host_class=endpoint_host_class, endpoint_url_metadata=_endpoint(url=url))
    )

    _assert_blocked(decision, "blocked_by_host")


@pytest.mark.parametrize("url", ["http://localhost.evil.test/v1/models", "http://localhost.localdomain.evil/v1/models"])
def test_localhost_spoofing_is_rejected(url: str) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(url=url))
    )

    _assert_blocked(decision, "localhost_spoof_rejected")


def test_declared_localhost_with_remote_url_is_rejected() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_host_class="localhost", endpoint_url_metadata=_endpoint(url="http://10.0.0.5:1234/v1/models"))
    )

    _assert_blocked(decision, "endpoint_host_class_url_mismatch")


@pytest.mark.parametrize("url", ["not-a-url", "http://localhost:bad/v1/models"])
def test_malformed_endpoint_is_rejected(url: str) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(url=url))
    )

    assert "malformed_endpoint" in decision.failure_reasons or "non_loopback_endpoint_blocked" in decision.failure_reasons
    _assert_non_authority(decision)


def test_non_http_local_endpoint_rules_are_explicit_and_blocked() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(url="ws://localhost:1234/v1/models"))
    )

    _assert_blocked(decision, "unsupported_endpoint_scheme")


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("/v1/chat/completions", "generation_endpoint_blocked"),
        ("/v1/completions", "completion_endpoint_blocked"),
        ("/v1/embeddings", "embedding_endpoint_blocked"),
        ("/v1/rerank", "reranker_endpoint_blocked"),
        ("/v1/images/generations", "multimodal_endpoint_blocked"),
        ("/v1/audio/transcriptions", "audio_endpoint_blocked"),
        ("/v1/files", "file_upload_endpoint_blocked"),
        ("/v1/tool/call", "tool_call_endpoint_blocked"),
    ],
)
def test_generation_embedding_reranker_multimodal_audio_upload_and_tool_endpoints_block(path: str, reason: str) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(url=f"http://localhost:1234{path}"))
    )

    _assert_blocked(decision, reason)


def test_unknown_endpoint_path_blocks_or_future_gates() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(url="http://localhost:1234/custom/status"))
    )

    _assert_blocked(decision, "unknown_endpoint_blocked")


def test_unknown_metadata_endpoint_class_blocks() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_url_metadata=_endpoint(metadata_endpoint_class="unknown"))
    )

    _assert_blocked(decision, "unknown_metadata_endpoint_class_blocked")


@pytest.mark.parametrize(
    "payload_class",
    [
        "prompt_payload",
        "context_payload",
        "memory_payload",
        "repo_payload",
        "raw_journal_payload",
        "raw_evidence_payload",
        "secret_payload",
        "unknown",
    ],
)
def test_prompt_context_memory_repo_journal_evidence_and_secret_payloads_block(payload_class: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(payload_class=payload_class))

    _assert_blocked(decision, "blocked_by_payload")


@pytest.mark.parametrize(
    "secret_policy",
    ["authorization_header_blocked", "api_key_validation_requested", "secret_read_requested", "unknown"],
)
def test_secret_api_key_and_authorization_policy_blocks(secret_policy: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(secret_policy=secret_policy))

    _assert_blocked(decision, "blocked_by_secret_policy")


def test_authorization_header_present_blocks_even_with_no_secret_policy() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(authorization_header_present=True)
    )

    _assert_blocked(decision, "authorization_header_denied")


@pytest.mark.parametrize("timeout_ms", [0, -1])
def test_invalid_timeout_blocks(timeout_ms: int) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(timeout_ms=timeout_ms))

    _assert_blocked(decision, "invalid_timeout_policy")


def test_timeout_above_limit_blocks() -> None:
    decision = validate_local_provider_probe_boundary_request(_request(timeout_ms=6000))

    _assert_blocked(decision, "blocked_by_timeout_policy")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_probe", "probe_boundary_cannot_provide_evidence"),
        ("verifier_success", "probe_boundary_cannot_mark_verifier_success"),
        ("mutation_performed", "mutation_performed_denied"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
    ],
)
def test_authority_grant_evidence_verifier_and_truth_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("provider_probed", "provider_probe_execution_denied"),
        ("endpoint_probed", "endpoint_probe_execution_denied"),
        ("http_request_performed", "http_request_denied"),
        ("socket_opened", "socket_open_denied"),
        ("provider_authenticated", "provider_authentication_denied"),
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
        ("cloud_provider_called", "cloud_provider_call_denied"),
        ("lan_or_remote_endpoint_called", "lan_or_remote_endpoint_call_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_probe_execution_payload_secret_external_and_model_behavior_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("provider_metadata_is_truth", "provider_metadata_truth_claim_denied"),
        ("model_list_is_truth", "model_list_truth_claim_denied"),
        ("provider_health_is_proof", "provider_health_proof_denied"),
        ("model_availability_is_execution_ready", "model_availability_execution_ready_claim_denied"),
        ("probe_candidate_selects_auto_mode", "auto_mode_selection_claim_denied"),
        ("probe_candidate_is_model_profile_proof", "model_profile_proof_claim_denied"),
        ("quality_or_benchmark_verified", "benchmark_verification_denied"),
        ("self_reported_identity_is_authority", "self_reported_identity_authority_denied"),
    ],
)
def test_truthfulness_overclaims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_provider_probe_boundary_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_negative_result_candidate_is_metadata_only_not_runtime_failure() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(probe_phase="negative_result_candidate")
    )

    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert decision.probe_classification == "negative_candidate_metadata_only"
    assert decision.negative_result_classification == "negative_candidate_metadata_only_not_runtime_failure"
    assert decision.evidence_provided_by_probe is False


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_health_decision", {"provider_health_verified": True}),
        ("local_provider_probe_design_decision", {"endpoint_probed": True}),
        ("model_auto_mode_decision", {"auto_mode_execution_allowed": True}),
        ("local_model_inventory_decision", {"model_call_performed": True}),
        ("local_model_context_profile_decision", {"benchmark_claim_verified": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("context_policy_decision", {"context_payload_sent": True}),
        ("memory_governance_decision", {"memory_payload_sent": True}),
        ("identity_scope_decision", {"runtime_dispatch_allowed": True}),
        ("capability_lease_decision", {"lease_grant": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, kwargs: dict[str, object]) -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(),
        local_provider_health_decision=_related(readiness_status="metadata_ready"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        model_auto_mode_decision=_related(selection_status="local_model_candidate"),
    )

    assert decision.probe_boundary_status == "probe_allowed_candidate"
    assert [ref.label for ref in decision.related_references] == [
        "local_provider_health",
        "local_provider_probe_design",
        "model_auto_mode",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(endpoint_url_metadata=_endpoint(url="http://localhost:1234/v1/models"))
    original_request = deepcopy(request)
    related = _related(readiness_status="metadata_ready")
    original_status = related.readiness_status

    decision = validate_local_provider_probe_boundary_request(
        request,
        local_provider_health_decision=related,
    )

    assert request == original_request
    assert related.readiness_status == original_status
    assert decision.probe_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.probe_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_local_provider_probe_boundary_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.probe_input is None


def test_output_never_sets_probe_or_model_flags_even_when_blocked() -> None:
    decision = validate_local_provider_probe_boundary_request(
        _request(endpoint_probed=True, model_call_performed=True, data_sent_external=True)
    )

    assert decision.probe_boundary_status.startswith("blocked_by_")
    _assert_non_authority(decision)
