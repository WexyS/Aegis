"""Tests for normalized command decomposition contracts."""

from __future__ import annotations

import pytest

from aegis.intent.decomposition import (
    NormalizedPlan,
    PrimitiveStep,
    PlanStatus,
    decompose_command,
    decompose_open_type,
    decompose_open_search,
    validate_normalized_plan,
)


def _step(intent: str, params: dict | None = None, *, risk: str = "low") -> PrimitiveStep:
    return PrimitiveStep(
        intent=intent,
        params=params or {},
        source_span=intent,
        risk=risk,
    )


def _plan(
    steps: list[PrimitiveStep],
    *,
    status: str = "ready",
    risk: str = "medium",
    ambiguities: list[str] | None = None,
) -> NormalizedPlan:
    return NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language="tr",
        source_text="source command",
        status=status,
        risk=risk,
        steps=steps,
        ambiguities=ambiguities or [],
        guard_notes=[],
    )


def test_valid_ready_open_app_type_plan_passes_validation() -> None:
    plan = _plan([
        _step("open_app", {"app": "notepad"}, risk="medium"),
        _step("type", {"text": "merhaba", "_require_focus": "notepad"}, risk="medium"),
    ])

    result = validate_normalized_plan(plan)

    assert result.valid is True
    assert result.status == PlanStatus.READY
    assert result.errors == []
    assert [step.intent for step in result.plan.steps] == ["open_app", "type"]
    assert result.plan.steps[1].params["_require_focus"] == "notepad"


def test_valid_ready_open_app_search_web_plan_passes_validation() -> None:
    plan = _plan([
        _step("open_app", {"app": "brave"}, risk="medium"),
        _step("search_web", {"query": "python nedir", "browser": "brave"}, risk="low"),
    ])

    result = validate_normalized_plan(plan)

    assert result.valid is True
    assert [step.intent for step in result.plan.steps] == ["open_app", "search_web"]
    assert result.plan.steps[1].params["browser"] == "brave"


def test_ready_plan_with_unknown_intent_fails_validation() -> None:
    plan = _plan([_step("launch_spaceship", {"target": "moon"})])

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("unknown intent" in error for error in result.errors)


def test_ready_plan_with_raw_click_fails_validation() -> None:
    plan = _plan([_step("click", {"selector": "button.save"}, risk="medium")])

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("raw generic click" in error for error in result.errors)


@pytest.mark.parametrize("intent", ["browser_click", "desktop_click"])
def test_browser_or_desktop_click_is_blocked_before_target_resolution(intent: str) -> None:
    plan = _plan([_step(intent, {"target": "save"}, risk="high")], risk="high")

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("target resolution is not implemented" in error for error in result.errors)


def test_ready_plan_with_ambiguity_fails_validation() -> None:
    plan = _plan(
        [_step("open_app", {"app": "notepad"})],
        ambiguities=["target app could mean notepad or notepad++"],
    )

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("ready plan cannot contain ambiguities" in error for error in result.errors)


def test_clarification_required_plan_with_ambiguity_passes_validation() -> None:
    plan = _plan(
        [],
        status="clarification_required",
        risk="none",
        ambiguities=["click target is ambiguous"],
    )

    result = validate_normalized_plan(plan)

    assert result.valid is True
    assert result.status == PlanStatus.CLARIFICATION_REQUIRED


def test_approval_required_plan_for_destructive_action_passes_validation() -> None:
    plan = _plan(
        [],
        status="approval_required",
        risk="critical",
        ambiguities=["destructive action requires approval"],
    )

    result = validate_normalized_plan(plan)

    assert result.valid is True
    assert result.status == PlanStatus.APPROVAL_REQUIRED


def test_ready_plan_with_no_steps_fails_validation() -> None:
    plan = _plan([])

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("ready plan must contain at least one step" in error for error in result.errors)


def test_ready_plan_with_invalid_status_fails_validation() -> None:
    plan = _plan([_step("open_app", {"app": "notepad"})], status="done")

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("invalid status" in error for error in result.errors)


def test_ready_plan_with_invalid_risk_fails_validation() -> None:
    plan = _plan([_step("open_app", {"app": "notepad"})], risk="spicy")

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("invalid risk" in error for error in result.errors)


def test_llm_proposal_with_unknown_tool_name_fails_validation() -> None:
    plan = _plan(
        [_step("delete_everything", {"path": "C:\\"}, risk="critical")],
        risk="critical",
    )

    result = validate_normalized_plan(plan, source="llm")

    assert result.valid is False
    assert any("unknown intent" in error for error in result.errors)


def test_missing_required_params_for_known_intent_fails_validation() -> None:
    plan = _plan([_step("type", {}, risk="medium")])

    result = validate_normalized_plan(plan)

    assert result.valid is False
    assert any("missing required params" in error for error in result.errors)


def test_decompose_turkish_not_defteri_open_type_ready_plan() -> None:
    plan = decompose_open_type("not defterini aç ve merhaba yaz")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[0].params == {"app": "notepad"}
    assert plan.steps[1].params == {"text": "merhaba", "_require_focus": "notepad"}
    assert validate_normalized_plan(plan).valid is True


def test_decompose_turkish_notepad_acip_open_type_ready_plan() -> None:
    plan = decompose_open_type("notepad açıp merhaba yaz")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[0].params["app"] == "notepad"
    assert plan.steps[1].params["_require_focus"] == "notepad"
    assert plan.steps[1].params["text"] == "merhaba"


def test_decompose_turkish_preserves_typed_phrase_with_spaces() -> None:
    plan = decompose_open_type("not defteri aç sonra Merhaba   güzel dünya yaz")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert plan.steps[1].params["text"] == "Merhaba   güzel dünya"


def test_decompose_english_open_notepad_and_type_ready_plan() -> None:
    plan = decompose_open_type("open notepad and type hello world")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[0].params == {"app": "notepad"}
    assert plan.steps[1].params == {"text": "hello world", "_require_focus": "notepad"}


def test_decompose_english_open_notepad_then_type_ready_plan() -> None:
    plan = decompose_open_type("open notepad then type hello world")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[1].params["text"] == "hello world"


def test_decompose_unknown_app_open_type_returns_clarification_required() -> None:
    plan = decompose_open_type("unknownapp aç ve merhaba yaz")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.steps == []
    assert plan.ambiguities == ["unknown app for open+type: unknownapp"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_missing_type_text_returns_clarification_required() -> None:
    plan = decompose_open_type("notepad aç ve yaz")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.steps == []
    assert plan.ambiguities == ["missing text for type step"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_app_name_does_not_leak_into_typed_text() -> None:
    plan = decompose_open_type("notepad açıp notepad için not al yaz")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert plan.steps[1].params["text"] == "notepad için not al"


def test_decompose_type_step_has_require_focus() -> None:
    plan = decompose_open_type("open notepad and type Focus me")

    assert plan is not None
    assert plan.steps[1].params["_require_focus"] == "notepad"


def test_decompose_search_pattern_is_ignored() -> None:
    assert decompose_open_type("brave açıp python nedir ara") is None


def test_decompose_turkish_brave_open_search_ready_plan() -> None:
    plan = decompose_open_search("brave açıp python nedir ara")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "search_web"]
    assert plan.steps[0].params == {"app": "brave"}
    assert plan.steps[1].params == {"query": "python nedir", "browser": "brave"}
    assert validate_normalized_plan(plan).valid is True


def test_decompose_turkish_chrome_open_search_ready_plan() -> None:
    plan = decompose_open_search("chrome aç ve python nedir ara")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "search_web"]
    assert plan.steps[0].params["app"] == "chrome"
    assert plan.steps[1].params == {"query": "python nedir", "browser": "chrome"}


def test_decompose_turkish_open_then_search_ready_plan() -> None:
    plan = decompose_open_search("brave aç sonra yapay zeka ara")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "search_web"]
    assert plan.steps[1].params["query"] == "yapay zeka"


def test_decompose_english_open_brave_and_search_ready_plan() -> None:
    plan = decompose_open_search("open brave and search what is python")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "search_web"]
    assert plan.steps[0].params == {"app": "brave"}
    assert plan.steps[1].params == {"query": "what is python", "browser": "brave"}


def test_decompose_english_open_chrome_then_search_ready_plan() -> None:
    plan = decompose_open_search("open chrome then search python tutorial")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "search_web"]
    assert plan.steps[1].params == {"query": "python tutorial", "browser": "chrome"}


def test_decompose_unknown_app_open_search_returns_clarification_required() -> None:
    plan = decompose_open_search("unknownapp aç ve python ara")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.steps == []
    assert plan.ambiguities == ["unknown app for open+search: unknownapp"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_missing_search_query_returns_clarification_required() -> None:
    plan = decompose_open_search("brave aç ve ara")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.steps == []
    assert plan.ambiguities == ["missing query for search_web step"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_app_name_does_not_leak_into_search_query() -> None:
    plan = decompose_open_search("brave açıp python nedir ara")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert plan.steps[1].params["query"] == "python nedir"
    assert "brave" not in plan.steps[1].params["query"]


def test_decompose_search_step_has_browser_context() -> None:
    plan = decompose_open_search("open chrome and search Focus me")

    assert plan is not None
    assert plan.steps[1].params["browser"] == "chrome"


def test_decompose_open_type_pattern_is_ignored_by_open_search() -> None:
    assert decompose_open_search("notepad açıp merhaba yaz") is None


def test_decompose_click_phrase_is_not_executable_click() -> None:
    plan = decompose_open_search("brave aç ve ilk sonuca tıkla")

    assert plan is None or plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    if plan is not None:
        assert all(step.intent != "click" for step in plan.steps)


def test_decompose_command_routes_turkish_open_type() -> None:
    plan = decompose_command("notepad açıp merhaba yaz")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[1].params == {"text": "merhaba", "_require_focus": "notepad"}
    assert validate_normalized_plan(plan).valid is True


def test_decompose_command_routes_turkish_open_search() -> None:
    plan = decompose_command("brave açıp python nedir ara")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["search_web"]
    assert plan.steps[0].params["query"] == "python nedir"
    assert plan.steps[0].params["browser"] == "brave"
    assert plan.steps[0].params["preferred_browser"] == "brave"
    assert validate_normalized_plan(plan).valid is True


def test_decompose_command_routes_english_open_type() -> None:
    plan = decompose_command("open notepad and type hello")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
    assert plan.steps[1].params["text"] == "hello"


def test_decompose_command_routes_english_open_search() -> None:
    plan = decompose_command("open brave and search python")

    assert plan is not None
    assert plan.status == PlanStatus.READY.value
    assert [step.intent for step in plan.steps] == ["search_web"]
    assert plan.steps[0].params["query"] == "python"
    assert plan.steps[0].params["browser"] == "brave"
    assert plan.steps[0].params["preferred_browser"] == "brave"


def test_decompose_command_unknown_open_type_returns_clarification_required() -> None:
    plan = decompose_command("unknownapp aç ve merhaba yaz")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.ambiguities == ["unknown app for open+type: unknownapp"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_command_unknown_open_search_returns_clarification_required() -> None:
    plan = decompose_command("unknownapp aç ve python ara")

    assert plan is not None
    assert plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    assert plan.ambiguities == ["unknown app for open+search: unknownapp"]
    assert validate_normalized_plan(plan).valid is True


def test_decompose_command_ambiguous_click_does_not_become_executable_click() -> None:
    plan = decompose_command("brave aç ve ilk sonuca tıkla")

    assert plan is None or plan.status == PlanStatus.CLARIFICATION_REQUIRED.value
    if plan is not None:
        assert all(step.intent != "click" for step in plan.steps)


def test_decompose_command_unrelated_text_returns_none() -> None:
    assert decompose_command("bugün hava nasıl") is None


def test_decompose_command_order_is_open_type_before_open_search() -> None:
    plan = decompose_command("notepad açıp merhaba yaz")

    assert plan is not None
    assert [step.intent for step in plan.steps] == ["open_app", "type"]
