from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api.local_provider_probe_projection import (
    LOCAL_PROVIDER_PROBE_API_SURFACE_EXECUTION_PERMISSION,
    build_local_provider_probe_projection_api_response,
)
from aegis.main import app


API_PATH = "/maintenance/local-provider/probe-projection"


def _assert_read_only_invariants(data: dict[str, object]) -> None:
    assert data["read_only"] is True
    assert data["mutation_performed"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == LOCAL_PROVIDER_PROBE_API_SURFACE_EXECUTION_PERMISSION
    assert data["approval_grant"] is False
    assert data["capability_grant"] is False
    assert data["lease_grant"] is False
    assert data["evidence_provided"] is False
    assert data["verifier_success"] is False
    assert data["frontend_authority"] is False
    assert data["api_authority"] is False
    assert data["api_route_added"] is False
    assert data["runtime_command_added"] is False
    assert data["scheduler_added"] is False
    assert data["provider_health_verified"] is False
    assert data["model_availability_verified"] is False
    assert data["model_identity_verified"] is False
    assert data["benchmark_claim_verified"] is False
    assert data["retry_authorized"] is False
    assert data["auto_mode_selection_performed"] is False
    assert data["live_probe_performed"] is False
    assert data["real_endpoint_probed"] is False
    assert data["socket_opened"] is False
    assert data["http_request_performed"] is False
    assert data["model_loaded"] is False
    assert data["model_call_performed"] is False
    assert data["generation_performed"] is False
    assert data["embedding_generated"] is False
    assert data["reranking_performed"] is False
    assert data["multimodal_inference_performed"] is False
    assert data["prompt_payload_sent"] is False
    assert data["context_payload_sent"] is False
    assert data["memory_payload_sent"] is False
    assert data["repo_payload_sent"] is False
    assert data["raw_journal_payload_sent"] is False
    assert data["raw_evidence_payload_sent"] is False
    assert data["api_key_validated"] is False
    assert data["secret_read"] is False
    assert data["authorization_header_sent"] is False
    assert data["response_body_logged"] is False
    assert data["secret_logged"] is False
    assert data["cloud_provider_called"] is False
    assert data["lan_or_remote_endpoint_called"] is False
    assert data["runtime_health_mutated"] is False
    assert data["maintenance_health_mutated"] is False
    assert data["runtime_state_mutated"] is False
    assert data["journal_mutated"] is False
    assert data["evidence_mutated"] is False
    assert data["replay_mutated"] is False
    assert data["data_sent_external"] is False


@pytest.mark.asyncio
async def test_endpoint_returns_honest_no_current_projection_without_probe() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_PATH)

    assert response.status_code == 200
    data = response.json()
    assert data["projection_result_class"] == "no_projection_available"
    assert data["api_surface_status_class"] == "no_current_probe_result"
    assert data["projection_available"] is False
    assert data["current_projection_available"] is False
    assert data["source_current"] is False
    assert data["probe_result_class"] == "not_observed"
    assert data["provider_health_verified"] is False
    assert data["model_availability_verified"] is False
    assert data["retry_authorized"] is False
    assert data["requires_operator_approval_for_retry"] is False
    assert "Previous manual smoke results are not replayed as current runtime state." in data["limitations"]
    assert "unreachable_negative_candidate" not in str(data)
    _assert_read_only_invariants(data)


@pytest.mark.asyncio
async def test_endpoint_has_no_action_or_retry_post_surface() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_PATH)

    assert response.status_code == 405


@pytest.mark.parametrize(
    ("probe_result_class", "expected_api_result"),
    [
        ("unreachable_negative_candidate", "provider_probe_unreachable_candidate"),
        ("timeout_negative_candidate", "provider_probe_timeout_candidate"),
        ("connection_refused_negative_candidate", "provider_probe_connection_refused_candidate"),
        ("invalid_response_negative_candidate", "provider_probe_invalid_response_candidate"),
        ("unauthorized_negative_candidate", "provider_probe_unauthorized_candidate"),
        ("unsupported_endpoint_negative_candidate", "provider_probe_unsupported_endpoint_candidate"),
    ],
)
def test_negative_candidate_fixtures_preserve_distinctions_without_runtime_failure(
    probe_result_class: str,
    expected_api_result: str,
) -> None:
    data = build_local_provider_probe_projection_api_response(
        projection_metadata={
            "probe_result_class": probe_result_class,
            "source_refs": [{"ref_id": f"fixture:{probe_result_class}"}],
            "provenance": [{"ref_id": "synthetic-test-fixture"}],
        }
    )

    assert data["projection_result_class"] == expected_api_result
    assert data["api_surface_status_class"] == "negative_candidate_available"
    assert data["retry_authorized"] is False
    assert data["runtime_health_mutated"] is False
    assert data["provider_health_verified"] is False
    assert data["blocked"] is False
    _assert_read_only_invariants(data)


def test_unreachable_fixture_requires_operator_approval_but_does_not_authorize_retry() -> None:
    data = build_local_provider_probe_projection_api_response(
        projection_metadata={"probe_result_class": "unreachable_negative_candidate"}
    )

    assert data["projection_result_class"] == "provider_probe_unreachable_candidate"
    assert data["retry_semantics"] == "retry_requires_operator_approval"
    assert data["requires_operator_approval_for_retry"] is True
    assert data["retry_authorized"] is False
    assert data["live_probe_performed"] is False


@pytest.mark.parametrize(
    ("probe_result_class", "expected_api_result"),
    [
        ("metadata_success_candidate", "provider_probe_metadata_candidate"),
        ("health_metadata_success_candidate", "provider_probe_metadata_candidate"),
        ("model_list_success_candidate", "provider_probe_model_list_candidate"),
        ("empty_model_list_candidate", "provider_probe_empty_model_list_candidate"),
    ],
)
def test_metadata_candidate_fixtures_are_not_health_or_availability_proof(
    probe_result_class: str,
    expected_api_result: str,
) -> None:
    data = build_local_provider_probe_projection_api_response(
        projection_metadata={"probe_result_class": probe_result_class}
    )

    assert data["projection_result_class"] == expected_api_result
    assert data["api_surface_status_class"] == "metadata_candidate_available"
    assert data["provider_health_verified"] is False
    assert data["model_availability_verified"] is False
    assert data["model_identity_verified"] is False
    assert data["benchmark_claim_verified"] is False
    assert data["blocked"] is False
    _assert_read_only_invariants(data)


def test_empty_model_list_fixture_is_not_runtime_failure() -> None:
    data = build_local_provider_probe_projection_api_response(
        projection_metadata={"probe_result_class": "empty_model_list_candidate"}
    )

    assert data["projection_result_class"] == "provider_probe_empty_model_list_candidate"
    assert data["runtime_health_mutated"] is False
    assert data["maintenance_health_mutated"] is False
    assert data["provider_health_verified"] is False
    assert data["model_availability_verified"] is False


@pytest.mark.parametrize(
    "flag",
    [
        "generation_performed",
        "embedding_generated",
        "reranking_performed",
        "multimodal_inference_performed",
        "prompt_payload_sent",
        "context_payload_sent",
        "memory_payload_sent",
        "repo_payload_sent",
        "raw_journal_payload_sent",
        "raw_evidence_payload_sent",
        "api_key_validated",
        "secret_read",
        "authorization_header_sent",
        "response_body_logged",
        "secret_logged",
        "cloud_provider_called",
        "lan_or_remote_endpoint_called",
        "data_sent_external",
        "runtime_dispatch_allowed",
        "mutation_performed",
        "frontend_authority",
        "api_authority",
        "provider_health_verified",
        "model_availability_verified",
        "retry_authorized",
        "auto_mode_selection_performed",
        "live_probe_performed",
        "real_endpoint_probed",
        "socket_opened",
        "http_request_performed",
    ],
)
def test_unsafe_fixture_flags_are_blocked_and_not_reflected(flag: str) -> None:
    data = build_local_provider_probe_projection_api_response(
        projection_metadata={
            "probe_result_class": "metadata_success_candidate",
            flag: True,
        }
    )

    assert data["blocked"] is True
    assert data["api_surface_status_class"] == "blocked_by_policy"
    assert data[flag] is False
    _assert_read_only_invariants(data)


def test_api_module_does_not_import_runner_or_network_clients() -> None:
    source = Path("src/aegis/api/local_provider_probe_projection.py").read_text(encoding="utf-8")

    forbidden_fragments = (
        "local_provider_probe_runner",
        "run_local_provider_probe",
        "httpx",
        "requests",
        "socket.",
        "urllib",
        "Authorization",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
