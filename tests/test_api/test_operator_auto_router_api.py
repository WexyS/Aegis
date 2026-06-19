from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.core.operator_auto_router import CONTRACT_NAME, NO_ACTION_FLAGS
from aegis.main import app


API_ROUTE = "/operator/preview-route"


def _assert_no_action_flags(data: dict[str, object]) -> None:
    for field, expected in NO_ACTION_FLAGS.items():
        assert data[field] is expected, field
    assert data["proposal_only"] is True
    assert data["requires_backend_owned_policy_before_execution"] is True
    assert data["process_trace_is_summary_not_hidden_reasoning"] is True


@pytest.mark.asyncio
async def test_operator_preview_route_returns_contract() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_ROUTE, json={"request": "Aegis şu an ne durumda?"})

    assert response.status_code == 200
    data = response.json()
    assert data["contract"] == CONTRACT_NAME
    assert data["status"] == "preview_only"
    assert data["router_mode"] == "deterministic_preview"
    assert data["route_id"] == "status_explainer"
    _assert_no_action_flags(data)


@pytest.mark.asyncio
async def test_operator_preview_empty_request_fails_safely() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_ROUTE, json={"request": "   "})

    assert response.status_code == 400
    assert response.json()["detail"]["reason"] == "request_required"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "route_id"),
    (
        ("Bu UI sorununu analiz et ve Codex promptu hazırla", "vision_to_code_prompt"),
        ("Bunu hafızaya al ama önce açıkla", "memory_policy_preview"),
        ("Gerekirse web araştırması yap", "research_plan"),
        ("LM Studio modelimi değerlendir", "model_hub_review"),
        ("Kimi K2.7 Code modelini Aegis için değerlendir", "model_hub_review"),
        ("Bu komutu çalıştırmadan önce güvenli plan hazırla", "command_approval_preview"),
    ),
)
async def test_operator_preview_route_for_rendered_qa_prompts(prompt: str, route_id: str) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_ROUTE, json={"request": prompt})

    assert response.status_code == 200
    data = response.json()
    assert data["route_id"] == route_id
    assert data["artifact"]["status"] == "preview_only"
    assert data["trace_items"]
    _assert_no_action_flags(data)


@pytest.mark.asyncio
async def test_operator_preview_does_not_expose_secrets_or_claim_authority() -> None:
    secret = "sk-operator-preview-secret-should-not-return"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_ROUTE,
            json={"request": f"Explain Kimi provider boundary without using {secret}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert secret not in repr(data)
    assert data["authority"] is False
    assert data["output_authority"] is False
    assert data["evidence_created"] is False
    assert data["output_is_evidence"] is False
    assert data["verifier_success"] is False
    assert data["output_is_verifier_success"] is False
    assert data["approval_granted"] is False
    assert data["permission_granted"] is False
    assert data["capability_lease_granted"] is False
    _assert_no_action_flags(data)


@pytest.mark.asyncio
async def test_kimi_request_remains_disabled_metadata_only_no_call() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_ROUTE,
            json={"request": "Moonshot Kimi K2.7 Code ile cloud coding yapabilir miyim?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["route_id"] == "model_hub_review"
    assert data["external_cloud_candidate_disabled"] is True
    assert data["cloud_fallback_allowed"] is False
    assert data["cloud_call_performed"] is False
    assert data["external_provider_call_performed"] is False
    assert data["kimi_moonshot_call_performed"] is False
    assert data["data_sent_external"] is False
    assert data["prompt_payload_sent_external"] is False
    _assert_no_action_flags(data)
