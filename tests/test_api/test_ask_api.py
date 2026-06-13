from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_ask
from aegis.main import app


def _maintenance_scan() -> dict:
    return {
        "scan_version": "maintenance-scan/1",
        "read_only": True,
        "summary": {
            "scan_version": "runtime-health/1",
            "read_only": True,
            "status": "warning",
            "source_of_truth": "backend_snapshot_protocol_event_journal",
            "component_statuses": {"evidence_audit": "warning", "replay_diagnostics": "warning"},
            "raw_component_statuses": {"evidence_audit": "fail", "replay_diagnostics": "fail"},
            "active_failure_components": [],
            "attention": ["evidence_audit", "replay_diagnostics"],
            "active_runtime_projections": {
                "evidence_audit": {"status": "warning", "raw_status": "fail"},
                "replay_diagnostics": {"status": "warning", "raw_status": "fail"},
            },
        },
        "checks": {
            "foundation_closure_readiness": {
                "scan_version": "foundation-closure-readiness/1",
                "status": "warning",
                "current_blocker_count": 0,
                "current_evidence_failure_count": 0,
                "current_missing_evidence_count": 0,
                "restored_pending_count": 0,
                "current_session_pending_count": 0,
                "historical_evidence_debt_count": 17,
                "historical_missing_evidence_count": 13,
                "replay_boundary_classification": "historical_mixed_sequence_eras_or_reset_boundaries",
                "mutation_performed": False,
            },
            "pending_decision_hygiene": {
                "scan_version": "pending-decision-hygiene/1",
                "status": "ok",
                "pending_count": 0,
                "mutation_performed": False,
            },
            "evidence_audit": {
                "scan_version": "evidence-audit/2",
                "status": "fail",
                "current_evidence_failure_count": 0,
                "current_missing_evidence_count": 0,
                "historical_evidence_debt_count": 17,
                "historical_missing_evidence_count": 13,
                "mutation_performed": False,
            },
            "replay_diagnostics": {"scan_version": "runtime-replay-gap-diagnostics/1", "status": "fail"},
        },
    }


@pytest.fixture(autouse=True)
def ask_sources(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes_ask, "get_maintenance_scan_for_ask", lambda: _maintenance_scan())
    monkeypatch.setattr(
        routes_ask,
        "get_skill_catalog_for_ask",
        lambda: {
            "status": "listed",
            "skill_count": 1,
            "skills": [{"skill_id": "repo_structure_audit"}],
            "runtime_dispatch_allowed": False,
        },
    )
    monkeypatch.setattr(
        routes_ask,
        "get_tool_registry_for_ask",
        lambda: {"status": "ok", "registered_count": 21, "configured_count": 21, "tools": []},
    )
    monkeypatch.setattr(
        routes_ask,
        "get_model_gateway_status_for_ask",
        lambda: {"status": "disabled", "enabled": False, "provider": "lm_studio", "model_call_performed": False},
    )
    monkeypatch.setattr(
        routes_ask,
        "get_agent_profile_catalog_for_ask",
        lambda: {"status": "listed", "profile_count": 6, "agent_execution_performed": False},
    )
    monkeypatch.setattr(routes_ask, "get_plugin_summary_for_ask", lambda: {"status": "metadata_only"})


def _assert_non_execution(data: dict) -> None:
    assert data["runtime_dispatch_allowed"] is False
    assert data["memory_written"] is False
    assert data["execution_performed"] is False
    assert data["evidence_created"] is False
    assert data["verifier_success"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["tool_execution_performed"] is False
    assert data["plugin_execution_performed"] is False
    assert data["agent_execution_performed"] is False


@pytest.mark.asyncio
async def test_ask_endpoint_returns_read_only_status_response() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ask", json={"question": "Aegis su an ne durumda?"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "system_status"
    assert data["runtime_health_summary"]["status"] == "warning"
    assert data["runtime_health_summary"]["current_blocker_count"] == 0
    assert data["runtime_health_summary"]["raw_evidence_status"] == "fail"
    assert data["runtime_health_summary"]["active_evidence_status"] == "warning"
    assert data["source_refs"]
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_ask_endpoint_handles_skill_question_without_execution() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ask", json={"question": "Hangi skill'ler var?"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "skill_registry_question"
    assert any("Skill Registry lists 1 skills" in item for item in data["known"])
    _assert_non_execution(data)


@pytest.mark.asyncio
async def test_ask_endpoint_blocks_malformed_request() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ask", json={"include_memory": True})

    assert response.status_code == 400
    assert response.json()["detail"]["reason"] == "question_required"


@pytest.mark.asyncio
async def test_ask_endpoint_keeps_execution_requests_in_safe_path() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ask", json={"question": "Notepad ac ve dosya olustur"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "unsupported_or_risky"
    assert "cannot execute or mutate" in data["answer"]
    _assert_non_execution(data)
