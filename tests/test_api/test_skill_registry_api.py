from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.core.skill_registry import SKILL_REGISTRY_EXECUTION_PERMISSION
from aegis.main import app


def _assert_non_execution(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["permission_granted"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["evidence_created"] is False
    assert data["verifier_success"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == SKILL_REGISTRY_EXECUTION_PERMISSION
    assert data["memory_write_performed"] is False
    assert data["model_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["network_call_performed"] is False
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False


@pytest.mark.asyncio
async def test_skill_registry_list_endpoint_returns_catalog() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/skills")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "listed"
    assert data["skill_count"] == 6
    assert {skill["skill_id"] for skill in data["skills"]} >= {
        "repo_structure_audit",
        "memory_candidate_review",
        "society_review",
        "report_summarization",
        "context_package_review",
        "model_assisted_explanation",
    }
    assert data["skill_execution_allowed"] is False
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_skill_registry_get_endpoint_returns_manifest() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/skills/model_assisted_explanation")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "found"
    assert data["skill"]["skill_id"] == "model_assisted_explanation"
    assert data["skill"]["requires_model"] is True
    assert data["skill"]["non_authority_flags"]["model_call_performed"] is False
    assert data["skill_execution_allowed"] is False
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_skill_registry_missing_skill_returns_404() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/skills/not-a-skill")

    assert response.status_code == 404
    assert response.json()["detail"] == {"status": "not_found", "skill_id": "not-a-skill"}


@pytest.mark.asyncio
async def test_skill_registry_has_no_execution_endpoint() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/skills/repo_structure_audit/run", json={})

    assert response.status_code == 404
