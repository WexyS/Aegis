from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_autopilot, routes_society
from aegis.core.autopilot import AutoPilotReportStore, run_repo_structure_audit
from aegis.core.society import SocietySessionStore
from aegis.main import app


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sample_report(tmp_path: Path) -> dict:
    root = tmp_path / "repo"
    _write(root / "README.md", "# Demo")
    _write(root / "package.json", "{}")
    _write(root / "src" / "index.ts", "export {}\n")
    _write(root / "tests" / "sample.test.ts", "test('x', () => {})\n")
    return run_repo_structure_audit(root_path=str(root))


@pytest.fixture()
def stores(monkeypatch):
    autopilot_store = AutoPilotReportStore()
    society_store = SocietySessionStore()
    monkeypatch.setattr(routes_autopilot, "get_report_store", lambda: autopilot_store)
    monkeypatch.setattr(routes_society, "get_report_store", lambda: autopilot_store)
    monkeypatch.setattr(routes_society, "get_session_store", lambda: society_store)
    return autopilot_store, society_store


@pytest.mark.asyncio
async def test_society_api_run_and_retrieve_session(tmp_path, stores):
    autopilot_store, _ = stores
    report = _sample_report(tmp_path)
    autopilot_store.save(report)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        run_response = await client.post(
            "/society/run",
            json={
                "autopilot_report_id": report["report_id"],
                "memory_ids": ["mem_existing"],
            },
        )
        assert run_response.status_code == 200
        body = run_response.json()
        session_id = body["session_id"]
        assert body["status"] == "completed"
        assert len(body["proposals"]) == 6
        assert body["memory_write_performed"] is False
        assert body["model_call_performed"] is False
        assert body["mcp_call_performed"] is False
        assert body["tool_call_performed"] is False

        retrieved = await client.get(f"/society/sessions/{session_id}")
        assert retrieved.status_code == 200
        assert retrieved.json()["session_id"] == session_id

        listed = await client.get("/society/sessions")
        assert listed.status_code == 200
        listed_body = listed.json()
        assert listed_body["session_count"] == 1
        assert listed_body["sessions"][0]["session_id"] == session_id
        assert listed_body["session_persistence"] == "process_local_in_memory"


@pytest.mark.asyncio
async def test_society_api_missing_report_returns_input_missing(stores):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/society/run", json={"autopilot_report_id": "missing"})

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["status"] == "input_missing"
    assert detail["input_report_id"] == "missing"
    assert detail["runtime_dispatch_allowed"] is False
    assert detail["proposals"] == []


@pytest.mark.asyncio
async def test_society_api_can_run_from_explicit_report_payload(tmp_path, stores):
    report = _sample_report(tmp_path)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/society/run", json={"report_payload": report})

    assert response.status_code == 200
    body = response.json()
    assert body["input_report_summary"]["report_id"] == report["report_id"]
    assert [proposal["role"] for proposal in body["proposals"]] == [
        "Context Planner",
        "Policy Reviewer",
        "Memory Curator",
        "AutoPilot Planner",
        "Verifier Reviewer",
        "Report Writer",
    ]


@pytest.mark.asyncio
async def test_society_api_unknown_session_returns_404(stores):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/society/sessions/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "not_found"
