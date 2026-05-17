"""
Executor tests that avoid OS side effects by exercising failure contracts.
"""

from __future__ import annotations

import hashlib

import pytest

import aegis.executor.deterministic_executor as deterministic_executor_module
from aegis.core.context import ExecutionContext
from aegis.core.config import PROJECT_ROOT
from aegis.core.constants import ActionStatus, RiskLevel
from aegis.core.schemas import IntentResult
from aegis.core.state_manager import AegisStateSnapshot
from aegis.executor.deterministic_executor import get_deterministic_executor
from aegis.executor.deterministic_executor import DeterministicExecutor
from aegis.executor.desktop_verifier import DesktopObservation, DesktopTarget, DesktopVerificationResult


class TestDeterministicExecutorContracts:
    @pytest.mark.asyncio
    async def test_unknown_tool_fails_before_blind_execution(self) -> None:
        executor = get_deterministic_executor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="nonexistent_action",
            confidence=1.0,
            params={},
            risk=RiskLevel.NONE,
            raw_input="test",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert "Unknown tool" in result.output

    @pytest.mark.asyncio
    async def test_tool_error_string_becomes_failed_action(self) -> None:
        executor = get_deterministic_executor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": "__definitely_missing_aegis_test_file__.txt"},
            risk=RiskLevel.LOW,
            raw_input="read missing file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert "File not found" in result.output

    @pytest.mark.asyncio
    async def test_read_file_success_includes_read_only_evidence(self, tmp_path) -> None:
        path = tmp_path / "sample.txt"
        path.write_text("hello evidence", encoding="utf-8")
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": str(path)},
            risk=RiskLevel.LOW,
            raw_input="read file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["read_only_evidence"]
        assert evidence["tool"] == "read_file"
        assert evidence["path"] == str(path)
        assert evidence["bytes"] == len("hello evidence".encode("utf-8"))
        assert evidence["sha256"]
        assert evidence["truncated"] is False

    @pytest.mark.asyncio
    async def test_read_page_success_includes_read_only_evidence(self, monkeypatch) -> None:
        class FakePage:
            async def inner_text(self, selector: str) -> str:
                assert selector == "body"
                return "page evidence"

        executor = DeterministicExecutor()

        async def fake_get_page():
            return FakePage()

        monkeypatch.setattr(executor, "_get_page", fake_get_page)
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_page",
            confidence=1.0,
            params={},
            risk=RiskLevel.LOW,
            raw_input="read page",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["read_only_evidence"]
        assert evidence["tool"] == "read_page"
        assert evidence["bytes"] == len("page evidence".encode("utf-8"))
        assert evidence["sha256"]
        assert evidence["truncated"] is False

    @pytest.mark.asyncio
    async def test_search_web_success_includes_read_only_evidence(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                self.url = url

        executor = DeterministicExecutor()

        async def fake_get_page():
            return FakePage()

        monkeypatch.setattr(executor, "_get_page", fake_get_page)
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="search_web",
            confidence=1.0,
            params={"query": "aegis runtime"},
            risk=RiskLevel.LOW,
            raw_input="aegis runtime search",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["read_only_evidence"]
        assert evidence["tool"] == "search_web"
        assert evidence["query"] == "aegis runtime"
        assert evidence["search_url"] == "https://www.google.com/search?q=aegis+runtime"

    @pytest.mark.asyncio
    async def test_open_url_success_includes_browser_evidence(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                self.url = url

        executor = DeterministicExecutor()

        async def fake_get_page():
            return FakePage()

        monkeypatch.setattr(executor, "_get_page", fake_get_page)
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="open_url",
            confidence=1.0,
            params={"url": "https://example.com"},
            risk=RiskLevel.LOW,
            raw_input="open example",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["browser_evidence"]
        assert evidence["tool"] == "open_url"
        assert evidence["url"] == "https://example.com"
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "open_url"
        assert result.execution_evidence.target_type == "browser"
        assert result.execution_evidence.method == "browser"
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_scroll_success_includes_browser_evidence(self, monkeypatch) -> None:
        class FakePage:
            def __init__(self) -> None:
                self.expressions: list[str] = []

            async def evaluate(self, expression: str) -> None:
                self.expressions.append(expression)

        page = FakePage()
        executor = DeterministicExecutor()

        async def fake_get_page():
            return page

        monkeypatch.setattr(executor, "_get_page", fake_get_page)
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="scroll",
            confidence=1.0,
            params={"direction": "down", "amount": 300},
            risk=RiskLevel.LOW,
            raw_input="scroll down",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        assert page.expressions == ["window.scrollBy(0, 300)"]
        evidence = result.proof["browser_evidence"]
        assert evidence["tool"] == "scroll"
        assert evidence["direction"] == "down"
        assert evidence["amount"] == 300

    @pytest.mark.asyncio
    async def test_click_coordinates_success_includes_browser_evidence(self, monkeypatch) -> None:
        class FakeMouse:
            def __init__(self) -> None:
                self.clicks: list[tuple[int, int]] = []

            async def click(self, x: int, y: int) -> None:
                self.clicks.append((x, y))

        class FakePage:
            def __init__(self) -> None:
                self.url = "https://example.test"
                self.mouse = FakeMouse()

            async def evaluate(self, expression: str, arg=None):
                assert arg == {"x": 10, "y": 20}
                return {"tag": "BUTTON", "text": "Run", "x": 10, "y": 20}

        page = FakePage()
        executor = DeterministicExecutor()

        async def fake_get_page():
            return page

        monkeypatch.setattr(executor, "_get_page", fake_get_page)
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="click",
            confidence=1.0,
            params={"x": 10, "y": 20},
            risk=RiskLevel.MEDIUM,
            raw_input="click 10 20",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        assert page.mouse.clicks == [(10, 20)]
        evidence = result.proof["browser_evidence"]
        assert evidence["tool"] == "click"
        assert evidence["coordinates"] == {"x": 10, "y": 20}
        assert evidence["before"]["target"]["text"] == "Run"
        assert evidence["after"]["target"]["tag"] == "BUTTON"
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "click"
        assert result.execution_evidence.target_type == "browser"
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_write_file_success_includes_write_evidence(self) -> None:
        path = PROJECT_ROOT / "scratch" / "executor-write-evidence-test.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old line\n", encoding="utf-8")
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new line\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write file",
        )

        try:
            result = await executor.execute(intent, ctx)

            assert result.status == ActionStatus.EXECUTED
            assert result.success is True
            assert path.read_text(encoding="utf-8") == "new line\n"
            evidence = result.proof["write_evidence"]
            assert evidence["tool"] == "write_file"
            assert evidence["path"] == str(path.resolve())
            assert evidence["existed_before"] is True
            assert evidence["before_bytes"] == len("old line\n".encode("utf-8"))
            assert evidence["after_bytes"] == len("new line\n".encode("utf-8"))
            assert evidence["before_sha256"] == hashlib.sha256("old line\n".encode("utf-8")).hexdigest()
            assert evidence["after_sha256"] == hashlib.sha256("new line\n".encode("utf-8")).hexdigest()
            assert "-old line" in evidence["diff_preview"]
            assert "+new line" in evidence["diff_preview"]
            assert result.execution_evidence is not None
            assert result.execution_evidence.action == "write_file"
            assert result.execution_evidence.target_type == "file"
            assert result.execution_evidence.method == "write"
            assert result.execution_evidence.verification_state == "verified"
        finally:
            if path.exists():
                path.unlink()

    @pytest.mark.asyncio
    async def test_type_success_includes_type_evidence_without_raw_text(self, monkeypatch) -> None:
        snapshot = AegisStateSnapshot(
            version=1,
            timestamp="2026-05-11T00:00:00Z",
            active_app="notepad",
            pid=1234,
            hwnd=5678,
            last_action=None,
            last_status=None,
            is_responsive=True,
            focus_stable=True,
        )

        class FakeStateManager:
            async def sync_with_os(self, trace_id, span_id) -> None:
                return None

            def get_state(self):
                return snapshot

            def update(self, trace_id, span_id, **kwargs):
                return snapshot

        class FakeTypeTool:
            async def run(self, text: str, **kwargs) -> str:
                assert text == "secret text"
                return "Typed: '[redacted]'"

        executor = DeterministicExecutor()
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "type", FakeTypeTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="type",
            confidence=1.0,
            params={"text": "secret text"},
            risk=RiskLevel.MEDIUM,
            raw_input="type secret text",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["type_evidence"]
        assert evidence["tool"] == "type"
        assert evidence["text_chars"] == len("secret text")
        assert evidence["text_sha256"] == hashlib.sha256("secret text".encode("utf-8")).hexdigest()
        assert evidence["target_before"]["hwnd"] == 5678
        assert evidence["target_after"]["pid"] == 1234
        assert "secret text" not in str(evidence)
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "type"
        assert result.execution_evidence.target == "focused_input"
        assert result.execution_evidence.target_type == "focused_input"
        assert result.execution_evidence.verification_state == "verified"
        assert "secret text" not in str(result.execution_evidence)

    @pytest.mark.asyncio
    async def test_git_status_success_includes_git_evidence(self, monkeypatch) -> None:
        class FakeGitTool:
            async def run(self, git_cmd: str, **kwargs) -> str:
                assert git_cmd == "status"
                return "On branch main\nnothing to commit, working tree clean\n"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "git_action", FakeGitTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="git_action",
            confidence=1.0,
            params={"git_cmd": "status"},
            risk=RiskLevel.LOW,
            raw_input="git status",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        evidence = result.proof["git_evidence"]
        assert evidence["tool"] == "git_action"
        assert evidence["git_cmd"] == "status"
        assert evidence["read_only"] is True
        assert evidence["output_sha256"] == hashlib.sha256(result.output.encode("utf-8")).hexdigest()
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "git_action"
        assert result.execution_evidence.target_type == "git"
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_focus_app_success_includes_verified_execution_evidence(self, monkeypatch) -> None:
        snapshot = AegisStateSnapshot(
            version=1,
            timestamp="2026-05-13T00:00:00Z",
            active_app="desktop",
            pid=None,
            hwnd=None,
            last_action=None,
            last_status=None,
            is_responsive=True,
            focus_stable=False,
        )

        class FakeStateManager:
            async def sync_with_os(self, trace_id, span_id) -> None:
                return None

            def get_state(self):
                return snapshot

            def update(self, trace_id, span_id, **kwargs):
                return snapshot

        class FakeFocusTool:
            async def run(self, app: str, **kwargs) -> str:
                assert app == "notepad"
                kwargs["_focus_evidence"].append({
                    "action": "focus_app",
                    "app": app,
                    "keywords": ["notepad"],
                    "candidate_count": 1,
                    "candidates": [{"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242}],
                    "selected_window": {"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242},
                    "restored": False,
                    "activate_called": True,
                    "foreground_after": {"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242},
                    "outcome": "focused",
                })
                return "Focused 'notepad' (HWND: 101)."

        class FakeWindow:
            title = "Untitled - Notepad"
            _hWnd = 101
            visible = True
            isMinimized = False

        window = FakeWindow()
        executor = DeterministicExecutor()
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "focus_app", FakeFocusTool())
        monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "notepad")
        monkeypatch.setattr(
            "aegis.executor.desktop_verifier.get_app_config",
            lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Notepad"]},
        )
        monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [4242])
        monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 4242)
        monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: window)
        monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [window])
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="focus_app",
            confidence=1.0,
            params={"app": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="focus notepad",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        assert result.focus_verified is True
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "focus_app"
        assert result.execution_evidence.method == "focus_window"
        assert result.execution_evidence.verification_state == "verified"
        assert result.execution_evidence.attempts[0]["selected_window"]["hwnd"] == 101
        checks = {check["check_name"]: check for check in result.execution_evidence.verification_checks}
        assert checks["focus_attempt_recorded"]["passed"] is True
        assert checks["focus_selected_hwnd_matches_foreground"]["passed"] is True
        assert result.proof["execution_evidence"]["window"]["hwnd"] == 101

    @pytest.mark.asyncio
    async def test_focus_app_unverified_result_preserves_execution_evidence(self, monkeypatch) -> None:
        snapshot = AegisStateSnapshot(
            version=1,
            timestamp="2026-05-13T00:00:00Z",
            active_app="desktop",
            pid=None,
            hwnd=None,
            last_action=None,
            last_status=None,
            is_responsive=True,
            focus_stable=False,
        )

        class FakeStateManager:
            async def sync_with_os(self, trace_id, span_id) -> None:
                return None

            def get_state(self):
                return snapshot

            def update(self, trace_id, span_id, **kwargs):
                return snapshot

        class FakeFocusTool:
            async def run(self, app: str, **kwargs) -> str:
                kwargs["_focus_evidence"].append({
                    "action": "focus_app",
                    "app": app,
                    "keywords": ["notepad"],
                    "candidate_count": 1,
                    "candidates": [{"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242}],
                    "selected_window": {"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242},
                    "restored": False,
                    "activate_called": True,
                    "foreground_after": {"title": "Calculator", "hwnd": 202, "pid": 5150},
                    "outcome": "focused",
                })
                return "Focused 'notepad' (HWND: 101)."

        def fake_verify_desktop_action(**kwargs):
            observation = DesktopObservation(
                target=DesktopTarget(
                    app_id="notepad",
                    display_name="notepad",
                    process_name="notepad.exe",
                    window_keywords=["Notepad"],
                ),
                pids=[4242],
                process_alive=True,
                active_window={"title": "Calculator", "hwnd": 202, "pid": 5150},
                matching_windows=[],
                focus_verified=False,
            )
            return DesktopVerificationResult(
                action="focus_app",
                method="focus_window",
                observation=observation,
                verification_state="unverified",
                reason="active window did not match target",
                checks=[
                    {
                        "check_name": "foreground_pid_matches_target_process",
                        "expected": [4242],
                        "observed": 5150,
                        "passed": False,
                        "reason": "Foreground window PID must belong to the target process PID set.",
                    },
                ],
            )

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setattr("aegis.executor.deterministic_executor.verify_desktop_action", fake_verify_desktop_action)
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "focus_app", FakeFocusTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="focus_app",
            confidence=1.0,
            params={"app": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="focus notepad",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.output == "active window did not match target"
        assert result.execution_evidence is not None
        assert result.execution_evidence.verification_state == "unverified"
        assert result.execution_evidence.observed["active_pid"] == 5150
        assert result.execution_evidence.attempts[0]["foreground_after"]["pid"] == 5150
        assert result.proof["execution_evidence"]["verification_state"] == "unverified"
        checks = {check["check_name"]: check for check in result.execution_evidence.verification_checks}
        assert checks["foreground_pid_matches_target_process"]["passed"] is False
        assert checks["focus_selected_hwnd_matches_foreground"]["passed"] is False

    @pytest.mark.asyncio
    async def test_close_app_success_includes_verified_execution_evidence(self, monkeypatch) -> None:
        snapshot = AegisStateSnapshot(
            version=1,
            timestamp="2026-05-13T00:00:00Z",
            active_app="notepad",
            pid=4242,
            hwnd=101,
            last_action=None,
            last_status=None,
            is_responsive=True,
            focus_stable=True,
        )

        class FakeStateManager:
            async def sync_with_os(self, trace_id, span_id) -> None:
                return None

            def get_state(self):
                return snapshot

            def update(self, trace_id, span_id, **kwargs):
                return snapshot

        class FakeCloseTool:
            async def run(self, app: str, **kwargs) -> str:
                assert app == "notepad"
                kwargs["_close_evidence"].append({
                    "action": "close_app",
                    "process_name": "notepad.exe",
                    "initial_pids": [4242],
                    "terminate_sent_pids": [4242],
                    "graceful_timeout_seconds": 0.01,
                    "graceful_terminated_pids": [],
                    "kill_sent_pids": [4242],
                    "killed_pids": [4242],
                    "remaining_pids": [],
                    "outcome": "killed",
                })
                return "Closed 1 instance(s) of notepad."

        executor = DeterministicExecutor()
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "close_app", FakeCloseTool())
        monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "notepad")
        monkeypatch.setattr(
            "aegis.executor.desktop_verifier.get_app_config",
            lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Notepad"]},
        )
        monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [])
        monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: None)
        monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [])
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="close_app",
            confidence=1.0,
            params={"app": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="close notepad",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "close_app"
        assert result.execution_evidence.method == "terminate_process"
        assert result.execution_evidence.verification_state == "verified"
        assert result.execution_evidence.pids == []
        assert result.execution_evidence.process_alive is False
        assert result.execution_evidence.recovery_triggered is True
        assert result.execution_evidence.attempts[0]["kill_sent_pids"] == [4242]
        assert result.execution_evidence.fallback_chain[0]["method"] == "kill_after_graceful_timeout"
        checks = {check["check_name"]: check for check in result.execution_evidence.verification_checks}
        assert checks["close_initial_pids_accounted_for"]["passed"] is True
        assert checks["close_no_remaining_after_fallback"]["passed"] is True
