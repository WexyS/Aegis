"""
API smoke tests for the stabilized command pipeline.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api import routes_command
from aegis.core import maintenance_actions
from aegis.core.commands import get_approval_manager
from aegis.main import app
from aegis.api.routes_command import clean_text


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestCommandEndpoint:
    def test_clean_text_preserves_windows_paths(self) -> None:
        text = r"write nope to c:\windows\temp\aegis-test.txt"

        assert clean_text(text) == text

    def test_clean_text_decodes_hex_escapes(self) -> None:
        assert clean_text(r"a\xc3\xa7") == "aç"

    @pytest.mark.asyncio
    async def test_unknown_command_blocks_at_plan(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": "bilinmeyen komut"})
            assert r.status_code == 200
            data = r.json()
            assert data["intent"] == "unknown"
            assert data["status"] == "blocked"
            assert data["actions"][0]["status"] == "blocked"
            assert "not allowed" in data["actions"][0]["output"]

    @pytest.mark.asyncio
    async def test_guard_blocks_excessive_clicks_before_execution(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": "click 50 times"})
            assert r.status_code == 200
            data = r.json()
            assert data["intent"] == "click"
            assert data["status"] == "blocked"
            assert data["actions"][0]["status"] == "blocked"
            assert "exceeds maximum" in data["actions"][0]["output"]

    @pytest.mark.asyncio
    async def test_forbidden_write_path_blocks_instead_of_crashing_parser(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": "write nope to c:\\windows\\temp\\aegis-test.txt"})
            assert r.status_code == 200
            data = r.json()
            assert data["intent"] == "write_file"
            assert data["status"] == "blocked"
            assert data["actions"][0]["status"] == "blocked"
            assert "forbidden" in data["actions"][0]["output"]

    @pytest.mark.asyncio
    async def test_empty_text_rejected(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": ""})
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_trace_id_present(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": "bilinmeyen komut"})
            assert "trace_id" in r.json()

    @pytest.mark.asyncio
    async def test_duration_measured(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command", json={"text": "bilinmeyen komut"})
            assert r.json()["duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_http_approval_emits_protocol_event_before_resume(self, monkeypatch) -> None:
        from aegis.core.commands import get_approval_manager
        from aegis.core.constants import CommandStatus, RiskLevel
        from aegis.core.schemas import CommandResponse

        manager = get_approval_manager()
        manager.reset_for_tests()
        manager.create_received("open notepad", command_id="cmd-http-approve")
        manager.register_pending(
            command_id="cmd-http-approve",
            text="open notepad",
            trace_id="trace-http-approve",
            risk_level=RiskLevel.MEDIUM,
            reason="medium risk command requires approval",
        )
        emitted: list[tuple[str, dict]] = []

        async def fake_emit_event(event_type, payload, **kwargs):
            emitted.append((event_type.value, payload))

        class FakeOrchestrator:
            async def process(self, request):
                return CommandResponse(
                    trace_id="trace-http-approve",
                    status=CommandStatus.EXECUTED,
                    intent="open_app",
                    message="ok",
                )

        monkeypatch.setattr("aegis.api.ws_bridge.emit_event", fake_emit_event)
        monkeypatch.setattr("aegis.api.routes_command.get_orchestrator", lambda: FakeOrchestrator())

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command/cmd-http-approve/approve")

        assert r.status_code == 200
        assert r.json()["status"] == CommandStatus.EXECUTED.value
        assert [event[0] for event in emitted[:2]] == ["APPROVAL_RESOLVED", "COMMAND_APPROVED"]
        assert emitted[1][1]["command"]["command_id"] == "cmd-http-approve"

    @pytest.mark.asyncio
    async def test_http_approval_decision_grant_for_quarantined_click_does_not_resume(self, monkeypatch) -> None:
        from aegis.core.constants import RiskLevel

        manager = get_approval_manager()
        manager.reset_for_tests()
        manager.register_pending(
            command_id="cmd-http-click-approval",
            text="click 10 20",
            trace_id="trace-http-click-approval",
            risk_level=RiskLevel.HIGH,
            reason="generic click quarantine",
            metadata={
                "approval_id": "approval-http-click",
                "resume_allowed": False,
                "policy_rule": "generic_click.quarantined.approval_required",
            },
        )
        emitted: list[tuple[str, dict]] = []

        async def fake_emit_approval_resolved(record, *, decision):
            emitted.append(("APPROVAL_RESOLVED", record.to_dict()))

        monkeypatch.setattr("aegis.api.ws_bridge.emit_approval_resolved", fake_emit_approval_resolved)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/command/approvals/approval-http-click/resolve", json={"decision": "grant"})

        data = r.json()["command"]
        assert r.status_code == 200
        assert data["status"] == "blocked"
        assert data["metadata"]["approval_resolution_status"] == "approval_granted"
        assert data["metadata"]["completed_without_execution"] is True
        assert data["metadata"]["mutation_performed"] is False
        assert emitted[0][0] == "APPROVAL_RESOLVED"

    @pytest.mark.asyncio
    async def test_http_clarification_decision_cancel_remains_non_executed(self, monkeypatch) -> None:
        from aegis.core.constants import RiskLevel

        manager = get_approval_manager()
        manager.reset_for_tests()
        manager.register_waiting_clarification(
            command_id="cmd-http-clarification",
            text="click that",
            trace_id="trace-http-clarification",
            risk_level=RiskLevel.HIGH,
            reason="generic click quarantine",
            metadata={"clarification_id": "clarification-http-click"},
        )
        emitted: list[tuple[str, dict]] = []

        async def fake_emit_clarification_resolved(record):
            emitted.append(("CLARIFICATION_RESOLVED", record.to_dict()))

        monkeypatch.setattr("aegis.api.ws_bridge.emit_clarification_resolved", fake_emit_clarification_resolved)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/command/clarifications/clarification-http-click/resolve",
                json={"cancelled": True},
            )

        data = r.json()["command"]
        assert r.status_code == 200
        assert data["status"] == "cancelled"
        assert data["metadata"]["clarification_resolution_status"] == "clarification_cancelled"
        assert data["metadata"]["mutation_performed"] is False
        assert data["metadata"]["not_executed"] is True
        assert emitted[0][0] == "CLARIFICATION_RESOLVED"


class TestMaintenanceEndpoint:
    @pytest.mark.asyncio
    async def test_maintenance_scan_is_read_only_report(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/maintenance/scan")
            assert r.status_code == 200
            data = r.json()
            assert data["read_only"] is True
            assert data["scan_version"] == "maintenance-scan/1"
            assert data["finding_version"] == "maintenance-finding/1"
            assert data["summary"]["scan_version"] == "runtime-health/1"
            assert data["summary"]["read_only"] is True
            assert data["summary"]["source_of_truth"] == "backend_snapshot_protocol_event_journal"
            assert isinstance(data["findings"], list)
            assert data["recommendations"] == data["findings"]
            assert isinstance(data["action_proposals"], list)
            assert "action_proposal_count" in data["summary"]
            assert "categories" in data
            assert "event_journal" in data["checks"]
            assert "integrity_status" in data["checks"]["event_journal"]
            assert "historical_integrity_status" in data["checks"]["event_journal"]
            assert data["checks"]["finding_summary"]["scan_version"] == "maintenance-finding-summary/1"
            assert data["checks"]["read_only_contract"]["scan_version"] == "maintenance-read-only-contract/1"
            assert data["checks"]["read_only_contract"]["observed_mutations"] == []
            assert data["checks"]["documentation"]["scan_version"] == "documentation-check/1"
            assert data["checks"]["runtime_health"]["scan_version"] == "runtime-health/1"
            assert data["checks"]["runtime_snapshot"]["scan_version"] == "runtime-snapshot/1"
            assert data["checks"]["command_lifecycle"]["scan_version"] == "command-lifecycle/1"
            assert data["checks"]["websocket"]["scan_version"] == "websocket-runtime/1"
            assert data["checks"]["action_timeline"]["scan_version"] == "action-timeline-health/1"
            assert data["checks"]["runtime_snapshot"]["sequence_aligned"] is True
            assert data["checks"]["evidence_audit"]["scan_version"] == "evidence-audit/2"
            assert data["checks"]["evidence_audit"]["read_only"] is True
            assert "missing_evidence_count" in data["checks"]["evidence_audit"]
            assert "critical_failure_count" in data["checks"]["evidence_audit"]
            assert "check_fail_count" in data["checks"]["evidence_audit"]
            assert "app_registry" in data["checks"]
            assert data["checks"]["app_registry"]["scan_version"] == "app-registry/1"
            assert data["checks"]["app_registry"]["read_only"] is True
            assert data["checks"]["app_registry"]["entry_count"] >= 1
            assert "app_discovery" in data["checks"]
            assert data["checks"]["app_discovery"]["scan_version"] == "app-discovery-smoke/1"
            assert data["checks"]["app_discovery"]["read_only"] is True
            assert data["checks"]["app_discovery"]["actions_performed"] == []
            app_discovery_entries = {
                entry["app_id"]: entry
                for entry in data["checks"]["app_discovery"]["entries"]
            }
            assert "antigravity" in app_discovery_entries
            assert "antigravity_agent_manager" in app_discovery_entries
            assert "success" not in app_discovery_entries["antigravity"]
            assert "verification_state" not in app_discovery_entries["antigravity"]
            assert data["checks"]["tool_registry"]["registry"]["scan_version"] == "tool-registry/1"
            assert data["checks"]["tool_registry"]["registry"]["read_only"] is True
            assert data["checks"]["tool_registry"]["registry"]["status"] == "ok"
            assert data["checks"]["environment"]["scan_version"] == "environment-diagnostics/1"
            assert data["checks"]["environment"]["read_only"] is True
            assert data["checks"]["system_resources"]["scan_version"] == "system-resources/1"
            assert data["checks"]["system_resources"]["read_only"] is True
            assert data["checks"]["process_resources"]["scan_version"] == "process-resources/1"
            assert data["checks"]["process_resources"]["read_only"] is True
            assert data["checks"]["network_ports"]["scan_version"] == "network-ports/1"
            assert data["checks"]["network_ports"]["read_only"] is True
            assert data["checks"]["workspace_directories"]["scan_version"] == "workspace-directories/1"
            assert data["checks"]["workspace_directories"]["read_only"] is True
            assert "pending_action_proposal_count" in data["summary"]

    @pytest.mark.asyncio
    async def test_maintenance_action_proposal_requires_approval_and_executes_after_approval(self, monkeypatch, tmp_path) -> None:
        manager = get_approval_manager()
        manager.reset_for_tests()
        monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
        finding = {
            "finding_id": "config.logging.directory_missing",
            "category": "config",
            "severity": "warning",
            "source": "checks.logging.directory",
            "reason": "Configured logging directory does not exist.",
            "evidence": {"directory": str(tmp_path / "logs")},
            "recommendation": "Create the configured logging directory before long-running runtime sessions.",
            "read_only": True,
        }
        checks = {
            "logging": {
                "status": "warning",
                "directory": str(tmp_path / "logs"),
            },
        }
        report = {
            "scan_version": "maintenance-scan/1",
            "read_only": True,
            "action_proposals": maintenance_actions.build_maintenance_action_proposals([finding], checks),
        }
        monkeypatch.setattr(routes_command, "get_last_maintenance_scan", lambda: report)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request = await client.post("/maintenance/action-proposals/maintenance.create_logging_directory/request")
            assert request.status_code == 200
            command = request.json()["command"]
            assert command["status"] == "pending_approval"
            assert command["risk_level"] == "medium"
            assert command["metadata"]["kind"] == "maintenance_action"
            assert not (tmp_path / "logs").exists()

            approval = await client.post(f"/command/{command['command_id']}/approve")
            assert approval.status_code == 200
            data = approval.json()
            assert data["status"] == "executed"
            assert data["intent"] == "create_logging_directory"
            assert (tmp_path / "logs").is_dir()
            evidence = data["actions"][0]["execution_evidence"]
            assert evidence["verifier"] == "maintenance-action-verifier/1"
            assert evidence["verification_state"] == "verified"
        manager.reset_for_tests()

    @pytest.mark.asyncio
    async def test_environment_diagnostics_endpoint_is_read_only_report(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/environment/diagnostics")
            assert r.status_code == 200
            data = r.json()
            assert data["read_only"] is True
            assert data["scan_version"] == "environment-diagnostics/1"
            assert "python" in data["checks"]
            assert "git" in data["checks"]
            assert "node" in data["checks"]
            assert "npm" in data["checks"]


class TestAppRegistryEndpoint:
    @pytest.mark.asyncio
    async def test_app_registry_endpoint_is_read_only_and_runtime_independent(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/apps/registry")
            assert r.status_code == 200
            data = r.json()
            assert data["read_only"] is True
            assert data["scan_version"] == "app-registry/1"
            assert data["configured_count"] >= 1
            assert data["entry_count"] >= data["configured_count"]
            assert isinstance(data["entries"], list)

    @pytest.mark.asyncio
    async def test_app_registry_endpoint_can_refresh_read_only_scan(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/apps/registry?refresh=true")
            assert r.status_code == 200
            data = r.json()
            assert data["read_only"] is True
            assert data["scan_version"] == "app-registry/1"


class TestToolRegistryEndpoint:
    @pytest.mark.asyncio
    async def test_tool_registry_endpoint_is_read_only_backend_snapshot(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/tools/registry")
            assert r.status_code == 200
            data = r.json()
            assert data["read_only"] is True
            assert data["scan_version"] == "tool-registry/1"
            assert data["status"] == "ok"
            assert data["registered_count"] == len(data["tools"])
            assert any(tool["name"] == "run_command" for tool in data["tools"])
