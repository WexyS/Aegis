from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_agent_runtime
from aegis.core.agent_runtime import AGENT_RUNTIME_EXECUTION_PERMISSION, AgentSessionStore
from aegis.main import app


def _assert_non_execution(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["permission_granted"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["evidence_created"] is False
    assert data["verifier_success"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == AGENT_RUNTIME_EXECUTION_PERMISSION
    assert data["memory_write_performed"] is False
    assert data["model_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["network_call_performed"] is False
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False


@pytest.fixture()
def session_store(monkeypatch: pytest.MonkeyPatch) -> AgentSessionStore:
    store = AgentSessionStore()
    monkeypatch.setattr(routes_agent_runtime, "get_session_store", lambda: store)
    return store


@pytest.mark.asyncio
async def test_agent_profiles_endpoint_works() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/agents/profiles")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "listed"
    assert data["profile_count"] == 6
    assert {profile["agent_id"] for profile in data["profiles"]} >= {"context_agent", "report_agent"}
    assert data["agent_execution_allowed"] is False
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_agent_profile_get_endpoint_works() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/agents/profiles/policy_agent")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "found"
    assert data["profile"]["agent_id"] == "policy_agent"
    assert "ecc_security_config_review" in data["profile"]["allowed_skill_ids"]
    assert data["skill_execution_allowed"] is False
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_missing_agent_profile_returns_404() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/agents/profiles/missing_agent")

    assert response.status_code == 404
    assert response.json()["detail"] == {"status": "not_found", "agent_id": "missing_agent"}


@pytest.mark.asyncio
async def test_agent_session_create_and_get_work(session_store: AgentSessionStore) -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/agents/sessions",
            json={"objective": "Review the bounded runtime.", "agent_ids": ["context_agent", "report_agent"]},
        )
        assert create_response.status_code == 200
        created = create_response.json()
        session_id = created["session_id"]
        assert created["status"] == "completed"
        assert len(created["proposals"]) == 2
        _assert_non_execution(created)

        get_response = await client.get(f"/agents/sessions/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["session_id"] == session_id

    assert session_store.get(session_id) is not None


@pytest.mark.asyncio
async def test_agent_sessions_list_works(session_store: AgentSessionStore) -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/agents/sessions", json={"objective": "List this session."})
        response = await client.get("/agents/sessions")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "listed"
    assert data["session_count"] == 1
    assert data["session_persistence"] == "process_local_in_memory"
    assert data["sessions"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_invalid_agent_request_returns_clear_error(session_store: AgentSessionStore) -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/agents/sessions",
            json={"objective": "Invalid agent.", "agent_ids": ["missing_agent"]},
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["status"] == "failed"
    assert "unknown_agent:missing_agent" in detail["failure_reasons"]
    assert detail["proposals"] == []


@pytest.mark.asyncio
async def test_use_model_future_gated_behavior_visible(session_store: AgentSessionStore) -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/agents/sessions",
            json={"objective": "Try model assistance.", "use_model": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "model_assisted_agents_future_gated" in data["warnings"]
    assert data["model_gateway_awareness"]["model_completion_called"] is False
    assert data["model_call_performed"] is False
    _assert_non_execution(data)
