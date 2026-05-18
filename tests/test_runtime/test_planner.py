from __future__ import annotations

from aegis.core.constants import IntentSource, RiskLevel
from aegis.core.schemas import IntentResult
from aegis.orchestrator.orchestrator import PlanSimulator
from aegis.orchestrator.planner import Planner


def _intent(intent: str, params: dict) -> IntentResult:
    return IntentResult(
        intent=intent,
        confidence=1.0,
        params=params,
        risk=RiskLevel.MEDIUM,
        source=IntentSource.RULE,
        raw_input=intent,
    )


def test_planner_enriches_focus_and_close_with_desktop_metadata() -> None:
    plan = Planner().plan([
        _intent("focus_app", {"app": "notepad"}),
        _intent("close_app", {"app": "notepad"}),
    ])

    assert plan[0].params["_process_name"] == "notepad.exe"
    assert "Notepad" in plan[0].params["_keywords"]
    assert plan[1].params["_process_name"] == "notepad.exe"
    assert "Notepad" in plan[1].params["_keywords"]


def test_planner_passes_required_focus_metadata_to_type_after_open() -> None:
    plan = Planner().plan([
        _intent("open_app", {"app": "notepad"}),
        _intent("type", {"text": "hello"}),
    ])

    assert plan[1].params["_require_focus"] == "notepad"
    assert plan[1].params["_require_focus_process_name"] == "notepad.exe"
    assert "Notepad" in plan[1].params["_require_focus_keywords"]


def test_plan_simulator_blocks_mixed_unknown_segments_before_side_effects() -> None:
    plan = Planner().plan([
        _intent("open_app", {"app": "notepad"}),
        _intent("unknown", {}),
    ])

    result = PlanSimulator({"open_app"}).simulate(plan)

    assert result["feasible"] is False
    assert "Tool 'unknown' not allowed" in result["blockers"][0]
