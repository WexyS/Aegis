from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_autopilot
from aegis.core.autopilot import AutoPilotReportStore
from aegis.main import app


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sample_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / "README.md", "# Demo")
    _write(root / "package.json", "{}")
    _write(root / "src" / "index.ts", "export {}\n")
    _write(root / "tests" / "sample.test.ts", "test('x', () => {})\n")
    return root


@pytest.fixture()
def report_store(monkeypatch):
    store = AutoPilotReportStore()
    monkeypatch.setattr(routes_autopilot, "get_report_store", lambda: store)
    return store


@pytest.mark.asyncio
async def test_autopilot_api_run_and_retrieve_report(tmp_path, report_store):
    root = _sample_repo(tmp_path)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        run_response = await client.post(
            "/autopilot/run",
            json={"task_id": "repo_structure_audit", "root_path": str(root)},
        )
        assert run_response.status_code == 200
        run_body = run_response.json()
        report_id = run_body["report_id"]
        assert run_body["policy_gate"]["read_only"] is True
        assert run_body["verifier_lite"]["state"] == "pass"
        assert run_body["memory_candidate_persisted"] is False

        retrieved = await client.get(f"/autopilot/reports/{report_id}")
        assert retrieved.status_code == 200
        assert retrieved.json()["report_id"] == report_id

        listed = await client.get("/autopilot/reports")
        assert listed.status_code == 200
        listed_body = listed.json()
        assert listed_body["report_count"] == 1
        assert listed_body["reports"][0]["report_id"] == report_id
        assert listed_body["report_persistence"] == "process_local_in_memory"


@pytest.mark.asyncio
async def test_autopilot_api_invalid_path_failure_is_explicit(tmp_path, report_store):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/autopilot/run",
            json={"task_id": "repo_structure_audit", "root_path": str(tmp_path / "missing")},
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["status"] == "failed"
    assert "root_path_not_found" in detail["failure_reasons"]
    assert detail["verifier_lite"]["state"] == "error"
    assert detail["runtime_dispatch_allowed"] is False
    assert detail["shell_command_performed"] is False
    assert detail["network_call_performed"] is False
    assert detail["model_call_performed"] is False
    assert detail["mcp_call_performed"] is False


@pytest.mark.asyncio
async def test_autopilot_api_unknown_report_returns_404(report_store):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/autopilot/reports/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "not_found"
