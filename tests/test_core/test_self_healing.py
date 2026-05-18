from __future__ import annotations

from aegis.core.commands import CancellationToken
from aegis.core.self_healing import SelfHealing, get_self_healer


def test_get_self_healer_returns_singleton_instance() -> None:
    assert get_self_healer() is get_self_healer()


async def test_self_healing_stops_before_tool_call_when_cancelled() -> None:
    token = CancellationToken(command_id="cmd-1")
    token.cancel("cancelled in test")
    calls = 0

    async def tool(**kwargs):
        nonlocal calls
        calls += 1
        return "ok"

    result = await SelfHealing().run(tool, cancellation_token=token)

    assert calls == 0
    assert result == "Error: cancelled in test"


async def test_self_healing_failure_detection_uses_explicit_prefixes() -> None:
    calls = 0

    async def tool():
        nonlocal calls
        calls += 1
        return "No errors found: completed successfully"

    result = await SelfHealing().run(tool)

    assert calls == 1
    assert result == "No errors found: completed successfully"
