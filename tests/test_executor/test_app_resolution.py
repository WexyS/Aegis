from __future__ import annotations

from aegis.core.constants import ExecutionMode, IntentSource, RiskLevel
from aegis.core.schemas import GuardResult, IntentResult
from aegis.executor import executor as executor_module
from aegis.executor.executor import Executor
from aegis.executor.utils import verify_path


def test_verify_path_allows_known_launcher_uri_schemes() -> None:
    assert verify_path("steam://rungameid/730") == (True, "steam://rungameid/730")
    assert verify_path("com.epicgames.launcher://apps/Fortnite?action=launch&silent=true") == (
        True,
        "com.epicgames.launcher://apps/Fortnite?action=launch&silent=true",
    )


class AllowingSafety:
    def evaluate(self, intent: IntentResult) -> GuardResult:
        return GuardResult(allowed=True, reason="ok", risk=intent.risk)


async def fake_tool_run(**kwargs) -> str:
    return f"Successfully launched '{kwargs['app']}'."


async def test_executor_refreshes_app_registry_before_failing_unknown_app(monkeypatch) -> None:
    calls = {"resolve": 0, "refresh": 0}

    def fake_resolve_app_name(name: str) -> str | None:
        calls["resolve"] += 1
        return "steam" if calls["refresh"] else None

    def fake_refresh_installed_app_registry():
        calls["refresh"] += 1
        return {}

    monkeypatch.setattr(executor_module, "resolve_app_name", fake_resolve_app_name)
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "refresh_installed_app_registry", fake_refresh_installed_app_registry)
    monkeypatch.setattr(executor_module, "get_app_config", lambda name: {
        "path": "steam://rungameid/730",
        "process_name": None,
        "window_keywords": ["Steam"],
        "fallback": None,
    })
    monkeypatch.setattr(executor_module, "verify_path", lambda path: (True, path))
    monkeypatch.setattr(executor_module, "is_process_alive", lambda process_name: True)
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [])
    monkeypatch.setitem(executor_module.TOOLS, "open_app", type("FakeOpenAppTool", (), {"run": staticmethod(fake_tool_run)})())

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "steam"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open steam",
        ),
        ExecutionMode.LIVE,
    )

    assert calls["refresh"] == 1
    assert result[0].output == "Successfully launched 'steam'."


async def test_open_app_focus_existing_window_returns_verified_execution_evidence(monkeypatch) -> None:
    class FakeWindow:
        title = "Steam Library"
        _hWnd = 101
        isMinimized = False

        def __init__(self) -> None:
            self.activated = False

        def activate(self) -> None:
            self.activated = True

    window = FakeWindow()
    monkeypatch.setattr(executor_module, "resolve_app_name", lambda name: "steam")
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "get_app_config", lambda name: {
        "path": "steam.exe",
        "process_name": "steam.exe",
        "window_keywords": ["Steam"],
        "fallback": None,
    })
    monkeypatch.setattr(executor_module, "verify_path", lambda path: (True, r"C:\Steam\steam.exe"))
    monkeypatch.setattr(executor_module, "get_running_pids", lambda process_name: [4242])
    monkeypatch.setattr(executor_module, "score_window", lambda w, pids: 150)
    monkeypatch.setattr(executor_module, "get_window_pid", lambda hwnd: 4242)
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [window])
    monkeypatch.setattr(executor_module.gw, "getActiveWindow", lambda: window)

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "steam"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open steam",
        ),
        ExecutionMode.LIVE,
    )

    action = result[0]
    evidence = action.proof["execution_evidence"]
    assert action.success is True
    assert action.focus_verified is True
    assert evidence["verification_state"] == "verified"
    assert evidence["method"] == "focus_existing_window"
    assert evidence["target"] == "steam"
    assert evidence["process_name"] == "steam.exe"
    assert evidence["pids"] == [4242]
    assert evidence["window"]["title"] == "Steam Library"
    assert evidence["window"]["hwnd"] == 101
    assert evidence["window"]["pid"] == 4242
    assert evidence["started_at_ms"] <= evidence["completed_at_ms"]


async def test_open_app_launch_with_live_process_returns_verified_execution_evidence(monkeypatch) -> None:
    monkeypatch.setattr(executor_module, "resolve_app_name", lambda name: "steam")
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "get_app_config", lambda name: {
        "path": "steam.exe",
        "process_name": "steam.exe",
        "window_keywords": ["Steam"],
        "fallback": None,
    })
    monkeypatch.setattr(executor_module, "verify_path", lambda path: (True, r"C:\Steam\steam.exe"))
    monkeypatch.setattr(executor_module, "get_running_pids", lambda process_name: [4242])
    monkeypatch.setattr(executor_module, "score_window", lambda w, pids: 0)
    monkeypatch.setattr(executor_module, "is_process_alive", lambda process_name: True)
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [])
    monkeypatch.setitem(executor_module.TOOLS, "open_app", type("FakeOpenAppTool", (), {"run": staticmethod(fake_tool_run)})())

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "steam"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open steam",
        ),
        ExecutionMode.LIVE,
    )

    action = result[0]
    evidence = action.proof["execution_evidence"]
    assert action.success is True
    assert evidence["verification_state"] == "verified"
    assert evidence["method"] == "launch"
    assert evidence["process_alive"] is True
    assert evidence["pids"] == [4242]


async def test_open_app_retries_once_when_process_not_alive_then_verifies(monkeypatch) -> None:
    tool_calls = {"count": 0}
    pid_snapshots = iter([[], [], [4242]])

    async def flaky_tool_run(**kwargs) -> str:
        tool_calls["count"] += 1
        return f"Successfully launched '{kwargs['app']}'."

    def fake_get_running_pids(process_name: str) -> list[int]:
        try:
            return next(pid_snapshots)
        except StopIteration:
            return [4242]

    monkeypatch.setattr(executor_module, "resolve_app_name", lambda name: "steam")
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "get_app_config", lambda name: {
        "path": "steam.exe",
        "process_name": "steam.exe",
        "window_keywords": ["Steam"],
        "fallback": None,
    })
    monkeypatch.setattr(executor_module, "verify_path", lambda path: (True, r"C:\Steam\steam.exe"))
    monkeypatch.setattr(executor_module, "get_running_pids", fake_get_running_pids)
    monkeypatch.setattr(executor_module, "score_window", lambda w, pids: 0)
    monkeypatch.setattr(executor_module, "is_process_alive", lambda process_name: False)
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [])
    monkeypatch.setitem(executor_module.TOOLS, "open_app", type("FakeOpenAppTool", (), {"run": staticmethod(flaky_tool_run)})())

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "steam"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open steam",
        ),
        ExecutionMode.LIVE,
    )

    action = result[0]
    evidence = action.proof["execution_evidence"]
    assert tool_calls["count"] == 2
    assert action.success is True
    assert action.metrics.retries == 1
    assert action.metrics.recovery_triggered is True
    assert evidence["verification_state"] == "verified"
    assert evidence["retry_count"] == 1
    assert evidence["recovery_triggered"] is True
    assert evidence["attempts"][0]["verification_state"] == "failed"
    assert evidence["attempts"][1]["verification_state"] == "verified"


async def test_open_app_records_fallback_chain_when_primary_path_invalid(monkeypatch) -> None:
    tool_calls = {"count": 0}
    pid_snapshots = iter([[], [5150]])

    async def fallback_tool_run(**kwargs) -> str:
        tool_calls["count"] += 1
        return f"Successfully launched '{kwargs['app']}'."

    def fake_get_app_config(name: str):
        if name == "primary":
            return {
                "path": "missing-primary.exe",
                "process_name": "primary.exe",
                "window_keywords": ["Primary"],
                "fallback": "fallback",
            }
        if name == "fallback":
            return {
                "path": "fallback.exe",
                "process_name": "fallback.exe",
                "window_keywords": ["Fallback"],
                "fallback": None,
            }
        return None

    def fake_verify_path(path: str):
        if path == "missing-primary.exe":
            return False, None
        return True, r"C:\Fallback\fallback.exe"

    def fake_get_running_pids(process_name: str) -> list[int]:
        try:
            return next(pid_snapshots)
        except StopIteration:
            return [5150]

    monkeypatch.setattr(executor_module, "resolve_app_name", lambda name: "primary")
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "get_app_config", fake_get_app_config)
    monkeypatch.setattr(executor_module, "verify_path", fake_verify_path)
    monkeypatch.setattr(executor_module, "get_running_pids", fake_get_running_pids)
    monkeypatch.setattr(executor_module, "score_window", lambda w, pids: 0)
    monkeypatch.setattr(executor_module, "is_process_alive", lambda process_name: False)
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [])
    monkeypatch.setitem(executor_module.TOOLS, "open_app", type("FakeOpenAppTool", (), {"run": staticmethod(fallback_tool_run)})())

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "primary"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open primary",
        ),
        ExecutionMode.LIVE,
    )

    action = result[0]
    evidence = action.proof["execution_evidence"]
    assert tool_calls["count"] == 1
    assert action.success is True
    assert action.metrics.recovery_triggered is True
    assert evidence["target"] == "fallback"
    assert evidence["verification_state"] == "verified"
    assert evidence["fallback_chain"] == [
        {
            "from": "primary",
            "to": "fallback",
            "reason": "invalid_path",
            "path": "missing-primary.exe",
        }
    ]
    assert evidence["recovery_triggered"] is True


async def test_open_app_launch_without_process_or_window_evidence_is_unverified(monkeypatch) -> None:
    monkeypatch.setattr(executor_module, "resolve_app_name", lambda name: "portal")
    monkeypatch.setattr(executor_module, "smart_match_app", lambda name: None)
    monkeypatch.setattr(executor_module, "get_app_config", lambda name: {
        "path": "portal://open",
        "process_name": None,
        "window_keywords": ["Portal"],
        "fallback": None,
    })
    monkeypatch.setattr(executor_module, "verify_path", lambda path: (True, path))
    monkeypatch.setattr(executor_module.gw, "getAllWindows", lambda: [])
    monkeypatch.setitem(executor_module.TOOLS, "open_app", type("FakeOpenAppTool", (), {"run": staticmethod(fake_tool_run)})())

    result = await Executor(AllowingSafety(), dry_run_default=False).execute(
        IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "portal"},
            risk=RiskLevel.MEDIUM,
            source=IntentSource.RULE,
            raw_input="open portal",
        ),
        ExecutionMode.LIVE,
    )

    action = result[0]
    evidence = action.proof["execution_evidence"]
    assert action.success is True
    assert action.focus_verified is False
    assert evidence["verification_state"] == "unverified"
    assert evidence["process_alive"] is None
    assert evidence["window"] is None
    assert any("No process_name configured" in warning for warning in evidence["warnings"])
