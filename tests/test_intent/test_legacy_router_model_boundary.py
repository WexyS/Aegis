from __future__ import annotations

from types import SimpleNamespace

import pytest

from aegis.core.constants import ActionStatus, CommandStatus, IntentSource, RiskLevel
from aegis.core.schemas import ActionResult, CommandRequest, IntentResult, ReliabilityMetrics
from aegis.intent.ai_parser import AIParser
from aegis.intent.parser import IntentParser
from aegis.orchestrator import orchestrator as orchestrator_module
from aegis.orchestrator.orchestrator import Orchestrator
from aegis.orchestrator.router import CapabilityRouter


@pytest.mark.asyncio
async def test_router_model_hint_is_non_authoritative_metadata_only() -> None:
    router = CapabilityRouter()

    verdict = await router.route(CommandRequest(text="plan a careful multi step workflow with high level risk review"))

    assert verdict.planner_model
    assert verdict.model_hint_status == "legacy_hint_only"
    assert verdict.model_hint_authoritative is False
    assert verdict.model_call_authorized is False
    assert verdict.provider_selection_granted is False
    assert verdict.auto_mode_decision_granted is False
    assert verdict.execution_permission == "not_granted_by_legacy_router_hint"
    assert verdict.evidence_created is False
    assert verdict.verifier_success is False


@pytest.mark.asyncio
async def test_parser_ignores_model_hint_when_agent_loop_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        features=SimpleNamespace(deterministic_decomposition=False, agent_loop=True)
    )
    monkeypatch.setattr("aegis.intent.parser.get_settings", lambda: settings)

    def forbidden_ai_parser():
        raise AssertionError("legacy model hint must not authorize AI parser")

    monkeypatch.setattr("aegis.intent.ai_parser.get_ai_parser", forbidden_ai_parser)

    results = await IntentParser().parse("unrecognized complex prompt", model="qwen/qwen3.5-9b")

    assert len(results) == 1
    assert results[0].intent == "unknown"
    assert results[0].source is IntentSource.RULE


@pytest.mark.asyncio
async def test_local_model_inventory_metadata_alone_does_not_authorize_parser_model_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        features=SimpleNamespace(deterministic_decomposition=False, agent_loop=True)
    )
    monkeypatch.setattr("aegis.intent.parser.get_settings", lambda: settings)

    def forbidden_ai_parser():
        raise AssertionError("Local Model Inventory metadata is not model-call permission")

    monkeypatch.setattr("aegis.intent.ai_parser.get_ai_parser", forbidden_ai_parser)

    results = await IntentParser().parse(
        "unknown request",
        model="local_model_inventory:qwen2.5-coder:metadata_only",
    )

    assert results[0].intent == "unknown"


@pytest.mark.asyncio
async def test_parser_requires_explicit_model_call_authorization_for_ai_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        features=SimpleNamespace(deterministic_decomposition=False, agent_loop=True)
    )
    monkeypatch.setattr("aegis.intent.parser.get_settings", lambda: settings)

    class FakeAIParser:
        async def parse(self, text: str, *, model_call_authorized: bool = False):
            assert text == "unknown request"
            assert model_call_authorized is True
            return [
                IntentResult(
                    intent="general_chat",
                    confidence=0.8,
                    params={},
                    risk=RiskLevel.NONE,
                    source=IntentSource.AI,
                    raw_input=text,
                )
            ]

    monkeypatch.setattr("aegis.intent.ai_parser.get_ai_parser", lambda: FakeAIParser())

    results = await IntentParser().parse("unknown request", model_call_authorized=True)

    assert results[0].intent == "general_chat"
    assert results[0].source is IntentSource.AI


@pytest.mark.asyncio
async def test_ai_parser_default_does_not_call_llm_provider() -> None:
    class ForbiddenLLM:
        async def generate(self, *args, **kwargs):
            raise AssertionError("AIParser default path must not call the LLM provider")

    parser = AIParser()
    parser.llm = ForbiddenLLM()

    assert await parser.parse("unknown request") == []


@pytest.mark.asyncio
async def test_orchestrator_does_not_pass_legacy_router_hint_to_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_emit_event(*args, **kwargs):
        return None

    async def fake_emit_command_status(*args, **kwargs):
        return None

    async def fake_emit_task_finished(*args, **kwargs):
        return None

    async def fake_emit_state_change(*args, **kwargs):
        return True

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_event", fake_emit_event)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_command_status", fake_emit_command_status)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_task_finished", fake_emit_task_finished)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_state_change", fake_emit_state_change)

    class LegacyHintRouter:
        async def route(self, _request):
            return SimpleNamespace(
                planner_model="qwen/qwen3.5-9b",
                model_hint_status="legacy_hint_only",
                model_call_authorized=False,
            )

    class RecordingParser:
        def __init__(self):
            self.calls = []

        async def parse(self, text: str, *args, **kwargs):
            self.calls.append((text, args, kwargs))
            return [
                IntentResult(
                    intent="unknown",
                    confidence=0.0,
                    params={},
                    risk=RiskLevel.NONE,
                    source=IntentSource.RULE,
                    raw_input=text,
                )
            ]

    class PassthroughPlanner:
        def plan(self, intents):
            return list(intents)

    class BlockingSimulator:
        def simulate(self, _plan):
            return {"feasible": False, "blockers": ["unknown intent"]}

    class ForbiddenExecutor:
        async def execute(self, *args, **kwargs):
            raise AssertionError("legacy model hint must not reach execution")

    class FakeVerifier:
        async def verify_result(self, _result, _intended_effect=None):
            return 0.0

    parser = RecordingParser()
    orchestrator = Orchestrator()
    orchestrator.router = LegacyHintRouter()
    orchestrator.parser = parser
    orchestrator.planner = PassthroughPlanner()
    orchestrator.simulator = BlockingSimulator()
    orchestrator.executor = ForbiddenExecutor()
    orchestrator.verifier = FakeVerifier()

    response = await orchestrator.process(CommandRequest(text="unknown request"))

    assert response.status is CommandStatus.BLOCKED
    assert parser.calls == [("unknown request", (), {})]
    assert response.actions
    assert response.actions[0].status is ActionStatus.BLOCKED
    assert response.actions[0].success is False
    assert response.actions[0].execution_evidence is None
    assert response.actions[0].metadata.get("model_call_authorized") is not True
    assert response.actions[0].metadata.get("verifier_success") is not True
    assert all(action.metrics == ReliabilityMetrics() for action in response.actions)
