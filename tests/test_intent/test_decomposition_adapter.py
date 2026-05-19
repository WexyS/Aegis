"""Tests for adapting normalized decomposition plans to runtime intents."""

from __future__ import annotations

import pytest

from aegis.core.constants import IntentSource, RiskLevel
from aegis.intent.decomposition import (
    NormalizedPlan,
    PrimitiveStep,
    normalized_plan_to_intents,
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
        language="en",
        source_text="source command",
        status=status,
        risk=risk,
        steps=steps,
        ambiguities=ambiguities or [],
        guard_notes=[],
    )


def test_ready_open_type_plan_adapts_to_intents_in_order() -> None:
    plan = _plan([
        PrimitiveStep("open_app", {"app": "notepad"}, source_span="notepad", risk="medium"),
        PrimitiveStep("type", {"text": "hello", "_require_focus": "notepad"}, source_span="hello", risk="medium"),
    ])

    intents = normalized_plan_to_intents(plan, raw_text="open notepad and type hello")

    assert [intent.intent for intent in intents] == ["open_app", "type"]
    assert intents[1].params == {"text": "hello", "_require_focus": "notepad"}
    assert intents[0].risk == RiskLevel.MEDIUM
    assert intents[1].risk == RiskLevel.MEDIUM


def test_ready_open_search_plan_adapts_to_intents_in_order() -> None:
    plan = _plan([
        PrimitiveStep("open_app", {"app": "brave"}, source_span="brave", risk="medium"),
        PrimitiveStep("search_web", {"query": "python", "browser": "brave"}, source_span="python", risk="low"),
    ])

    intents = normalized_plan_to_intents(plan, raw_text="open brave and search python")

    assert [intent.intent for intent in intents] == ["open_app", "search_web"]
    assert intents[1].params == {"query": "python", "browser": "brave"}
    assert intents[0].risk == RiskLevel.MEDIUM
    assert intents[1].risk == RiskLevel.LOW


def test_adapter_sets_rule_source_confidence_and_raw_input() -> None:
    plan = _plan([PrimitiveStep("open_app", {"app": "notepad"}, source_span="notepad", risk="medium")])

    intents = normalized_plan_to_intents(plan, raw_text="open notepad")

    assert len(intents) == 1
    assert intents[0].source == IntentSource.RULE
    assert intents[0].confidence == 1.0
    assert intents[0].raw_input == "open notepad"


def test_adapter_metadata_preserves_decomposition_context() -> None:
    plan = _plan([
        PrimitiveStep("open_app", {"app": "notepad"}, source_span="notepad", risk="medium"),
        PrimitiveStep("type", {"text": "hello", "_require_focus": "notepad"}, source_span="hello", risk="medium"),
    ])

    intents = normalized_plan_to_intents(plan, raw_text="open notepad and type hello")

    assert intents[0].metadata["decomposition"] == "deterministic"
    assert intents[0].metadata["plan_kind"] == "deterministic_decomposition"
    assert intents[0].metadata["plan_status"] == "ready"
    assert intents[0].metadata["plan_risk"] == "medium"
    assert intents[0].metadata["step_index"] == 0
    assert intents[0].metadata["step_count"] == 2
    assert intents[0].metadata["source_span"] == "notepad"
    assert intents[0].metadata["guard_notes"] == []
    assert intents[0].metadata["ambiguities"] == []
    assert intents[1].metadata["step_index"] == 1
    assert intents[1].metadata["source_span"] == "hello"


def test_invalid_plan_does_not_produce_executable_intents() -> None:
    plan = _plan([PrimitiveStep("unknown_tool", {"target": "x"}, source_span="x", risk="low")])

    with pytest.raises(ValueError, match="invalid normalized plan"):
        normalized_plan_to_intents(plan, raw_text="bad command")


@pytest.mark.parametrize(
    ("status", "risk", "ambiguities"),
    [
        ("clarification_required", "none", ["unknown app"]),
        ("approval_required", "critical", ["destructive action"]),
        ("blocked", "medium", []),
    ],
)
def test_non_ready_plan_raises(status: str, risk: str, ambiguities: list[str]) -> None:
    plan = _plan([], status=status, risk=risk, ambiguities=ambiguities)

    with pytest.raises(ValueError, match="cannot adapt non-ready normalized plan"):
        normalized_plan_to_intents(plan, raw_text="non-ready command")


def test_unknown_risk_mapping_fails_closed() -> None:
    plan = _plan([PrimitiveStep("open_app", {"app": "notepad"}, source_span="notepad", risk="spicy")])

    with pytest.raises(ValueError, match="invalid normalized plan"):
        normalized_plan_to_intents(plan, raw_text="open notepad")


def test_plan_step_order_is_preserved() -> None:
    plan = _plan([
        PrimitiveStep("open_app", {"app": "brave"}, source_span="brave", risk="medium"),
        PrimitiveStep("search_web", {"query": "python", "browser": "brave"}, source_span="python", risk="low"),
    ])

    intents = normalized_plan_to_intents(plan, raw_text="open brave and search python")

    assert [intent.metadata["step_index"] for intent in intents] == [0, 1]
    assert [intent.intent for intent in intents] == ["open_app", "search_web"]
