from __future__ import annotations

from copy import deepcopy

from aegis.core.ask import ASK_EXECUTION_PERMISSION, build_ask_response, route_ask_intent


def _maintenance_scan() -> dict:
    return {
        "scan_version": "maintenance-scan/1",
        "read_only": True,
        "summary": {
            "scan_version": "runtime-health/1",
            "read_only": True,
            "status": "warning",
            "source_of_truth": "backend_snapshot_protocol_event_journal",
            "component_statuses": {
                "evidence_audit": "warning",
                "replay_diagnostics": "warning",
                "runtime_snapshot": "ok",
            },
            "raw_component_statuses": {
                "evidence_audit": "fail",
                "replay_diagnostics": "fail",
                "runtime_snapshot": "ok",
            },
            "active_failure_components": [],
            "attention": ["evidence_audit", "replay_diagnostics"],
            "active_runtime_projections": {
                "evidence_audit": {
                    "status": "warning",
                    "raw_status": "fail",
                    "active_evidence_failure_count": 0,
                    "active_missing_evidence_count": 0,
                },
                "replay_diagnostics": {
                    "status": "warning",
                    "raw_status": "fail",
                    "active_replay_failure": False,
                    "replay_boundary_classification": "historical_mixed_sequence_eras_or_reset_boundaries",
                },
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
            "replay_diagnostics": {
                "scan_version": "runtime-replay-gap-diagnostics/1",
                "status": "fail",
            },
        },
    }


def _skill_catalog() -> dict:
    return {
        "status": "listed",
        "skill_count": 2,
        "skills": [
            {"skill_id": "repo_structure_audit"},
            {"skill_id": "model_assisted_explanation"},
        ],
        "runtime_dispatch_allowed": False,
    }


def _tool_registry() -> dict:
    return {
        "status": "ok",
        "registered_count": 21,
        "configured_count": 21,
        "tools": [{"name": "open_app"}],
    }


def _model_status() -> dict:
    return {
        "status": "disabled",
        "enabled": False,
        "provider": "lm_studio",
        "model_call_performed": False,
        "runtime_dispatch_allowed": False,
    }


def _response(question: str, **request_overrides):
    request = {"question": question}
    request.update(request_overrides)
    return build_ask_response(
        request,
        maintenance_scan=_maintenance_scan(),
        skill_catalog=_skill_catalog(),
        tool_registry_snapshot=_tool_registry(),
        model_gateway_status=_model_status(),
        agent_profile_catalog={"status": "listed", "profile_count": 6},
        plugin_summary={"status": "metadata_only"},
    )


def _assert_non_execution(response: dict) -> None:
    assert response["runtime_dispatch_allowed"] is False
    assert response["execution_permission"] == ASK_EXECUTION_PERMISSION
    assert response["memory_written"] is False
    assert response["execution_performed"] is False
    assert response["evidence_created"] is False
    assert response["verifier_success"] is False
    assert response["approval_granted"] is False
    assert response["capability_lease_granted"] is False
    assert response["tool_execution_performed"] is False
    assert response["plugin_execution_performed"] is False
    assert response["agent_execution_performed"] is False
    assert response["model_used"] is None


def test_intent_router_supports_status_skill_model_and_risky_requests() -> None:
    assert route_ask_intent("Aegis su an ne durumda?") == "system_status"
    assert route_ask_intent("Bu warning active blocker mi historical debt mi?") == "runtime_health_explanation"
    assert route_ask_intent("Hangi skill'ler var?") == "skill_registry_question"
    assert route_ask_intent("Skill Registry ne durumda?") == "skill_registry_question"
    assert route_ask_intent("Tool Registry ne durumda?") == "tool_registry_question"
    assert route_ask_intent("Hangi tool registry bilgileri var?") == "tool_registry_question"
    assert route_ask_intent("Plugin registry var mi?") == "plugin_question"
    assert route_ask_intent("Model Gateway acik mi?") == "model_gateway_question"
    assert route_ask_intent("Siradaki guvenli adim ne?") == "next_step_planning"
    assert route_ask_intent("Notepad ac") == "unsupported_or_risky"
    assert route_ask_intent("Memory'ye yaz") == "unsupported_or_risky"


def test_status_question_preserves_raw_fail_and_active_warning_distinction() -> None:
    response = _response("Aegis su an ne durumda?")

    assert response["intent"] == "system_status"
    assert "fully healthy" not in response["answer"].lower()
    summary = response["runtime_health_summary"]
    assert summary["status"] == "warning"
    assert summary["current_blocker_count"] == 0
    assert summary["current_evidence_failure_count"] == 0
    assert summary["current_missing_evidence_count"] == 0
    assert summary["raw_evidence_status"] == "fail"
    assert summary["active_evidence_status"] == "warning"
    assert summary["raw_replay_status"] == "fail"
    assert summary["active_replay_status"] == "warning"
    assert summary["historical_evidence_debt_count"] == 17
    _assert_non_execution(response)


def test_current_blockers_zero_is_not_reported_as_green_production_readiness() -> None:
    response = _response("Bu uyarı aktif blocker mı yoksa historical debt mi?")

    assert response["runtime_health_summary"]["current_blocker_count"] == 0
    assert response["runtime_health_summary"]["status"] == "warning"
    assert "not fully green" in response["answer"].lower()
    assert any("Raw evidence/replay failures remain visible" in item for item in response["known"])
    _assert_non_execution(response)


def test_skill_registry_question_uses_catalog_without_execution() -> None:
    response = _response("Hangi skill'ler var ve hangileri calistirilabilir degil?")

    assert response["intent"] == "skill_registry_question"
    assert any("Skill Registry lists 2 skills" in item for item in response["known"])
    assert any("does not grant skill execution permission" in item for item in response["known"])
    _assert_non_execution(response)


def test_tool_registry_question_uses_metadata_without_tool_call() -> None:
    response = _response("Hangi tool'lar var?")

    assert response["intent"] == "tool_registry_question"
    assert any("21 registered tools" in item for item in response["known"])
    assert response["tool_execution_performed"] is False
    _assert_non_execution(response)


def test_plugin_question_does_not_load_or_execute_plugins() -> None:
    response = _response("Plugin katmani ne durumda?")

    assert response["intent"] == "plugin_question"
    assert any("No plugin load" in item for item in response["known"])
    assert response["plugin_execution_performed"] is False
    _assert_non_execution(response)


def test_model_gateway_disabled_produces_deterministic_non_model_answer() -> None:
    response = _response("Model Gateway acik mi?", include_model_polish=True)

    assert response["intent"] == "model_gateway_question"
    assert any("Model Gateway status: disabled" in item for item in response["known"])
    assert any("Model polish was requested but not performed" in item for item in response["limitations"])
    assert response["model_used"] is None
    _assert_non_execution(response)


def test_memory_not_included_by_default_and_include_does_not_write_memory() -> None:
    default_response = _response("Memory ne durumda?")
    include_response = _response("Memory ne durumda?", include_memory=True)

    assert default_response["memory_written"] is False
    assert not any("Memory search result count" in item for item in default_response["known"])
    assert include_response["memory_written"] is False
    assert any("Ask did not perform a MemoryStore read" in item for item in include_response["limitations"])
    _assert_non_execution(include_response)


def test_autopilot_and_agent_runtime_are_not_primary_ask_engine() -> None:
    response = _response("AutoPilot ve Agent Runtime ne yapabilir?", include_autopilot=True, include_agent_proposal=True)

    assert response["intent"] == "autopilot_question"
    assert any("Ask did not run a repo scan" in item for item in response["limitations"])
    assert response["non_authority_flags"]["agent_runtime_is_ask_engine"] is False
    assert response["agent_execution_performed"] is False
    _assert_non_execution(response)


def test_unsupported_execution_request_returns_safe_limitation() -> None:
    response = _response("Dosya olustur ve notepad ac")

    assert response["intent"] == "unsupported_or_risky"
    assert "cannot execute or mutate" in response["answer"]
    _assert_non_execution(response)


def test_response_does_not_mutate_request_or_supplied_sources() -> None:
    request = {"question": "Aegis su an ne durumda?", "include_memory": True}
    maintenance = _maintenance_scan()
    request_before = deepcopy(request)
    maintenance_before = deepcopy(maintenance)

    build_ask_response(
        request,
        maintenance_scan=maintenance,
        skill_catalog=_skill_catalog(),
        tool_registry_snapshot=_tool_registry(),
        model_gateway_status=_model_status(),
    )

    assert request == request_before
    assert maintenance == maintenance_before
