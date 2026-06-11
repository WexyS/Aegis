from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_memory
from aegis.main import app
from aegis.memory.store import MemoryStore


@pytest.fixture()
def memory_store(tmp_path, monkeypatch):
    store = MemoryStore(tmp_path / "api-memory.sqlite3")
    monkeypatch.setattr(routes_memory, "get_memory_store", lambda: store)
    return store


def _payload(**overrides):
    payload = {
        "type": "task_session_memory",
        "content": "API memories stay candidate-only.",
        "summary": "API memory invariant",
        "scope": "session",
        "session_ref": "session:api",
        "sensitivity": "private",
        "source_refs": [{"ref_id": "api-test", "ref_type": "test"}],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_memory_api_happy_path_propose_approve_search_delete(memory_store):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proposed = await client.post("/memory/propose", json=_payload())
        assert proposed.status_code == 200
        proposed_body = proposed.json()
        memory_id = proposed_body["memory_id"]
        assert proposed_body["status"] == "proposed"
        assert proposed_body["runtime_dispatch_allowed"] is False
        assert proposed_body["evidence_provided_by_memory"] is False

        approved = await client.post(f"/memory/{memory_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "active"

        found = await client.get("/memory/search", params={"keyword": "candidate", "session_ref": "session:api"})
        assert found.status_code == 200
        found_body = found.json()
        assert found_body["result_count"] == 1
        assert found_body["memories"][0]["id"] == memory_id
        assert found_body["memory_retrieval_is_authority"] is False

        deleted = await client.delete(f"/memory/{memory_id}")
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "deleted"

        after_delete = await client.get("/memory/search", params={"keyword": "candidate"})
        assert after_delete.status_code == 200
        assert after_delete.json()["result_count"] == 0


@pytest.mark.asyncio
async def test_memory_api_validation_failure_is_explicit(memory_store):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/memory/propose",
            json=_payload(content="", sensitivity="secret-like"),
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["status"] == "blocked_by_validation"
    assert "missing_content" in detail["failure_reasons"]
    assert "blocked_sensitive_memory" in detail["failure_reasons"]
    assert detail["governance_result"]["status"] == "not_run_due_to_validation_failure"
    assert detail["runtime_dispatch_allowed"] is False


@pytest.mark.asyncio
async def test_memory_api_invalid_transition_returns_conflict(memory_store):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proposed = await client.post("/memory/propose", json=_payload(content="Reject through API."))
        memory_id = proposed.json()["memory_id"]
        rejected = await client.post(f"/memory/{memory_id}/reject", json={"reason": "not durable"})
        assert rejected.status_code == 200

        approve_rejected = await client.post(f"/memory/{memory_id}/approve")

    assert approve_rejected.status_code == 409
    detail = approve_rejected.json()["detail"]
    assert detail["status"] == "blocked_by_invalid_transition"
    assert "approve_requires_proposed_memory" in detail["failure_reasons"]
