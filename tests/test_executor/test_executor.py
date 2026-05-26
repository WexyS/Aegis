"""
Executor tests that avoid OS side effects by exercising failure contracts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

import aegis.executor.deterministic_executor as deterministic_executor_module
from aegis.core.context import ExecutionContext
from aegis.core.config import PROJECT_ROOT
from aegis.core.constants import ActionStatus, RiskLevel
from aegis.core.schemas import IntentResult
from aegis.core.state_manager import AegisStateSnapshot
from aegis.executor.deterministic_executor import get_deterministic_executor
from aegis.executor.deterministic_executor import DeterministicExecutor
from aegis.executor.deterministic_executor import _type_evidence
from aegis.executor.desktop_verifier import DesktopObservation, DesktopTarget, DesktopVerificationResult


def _snapshot(*, hwnd: int | None, pid: int | None = 1234, focus_stable: bool = True) -> AegisStateSnapshot:
    return AegisStateSnapshot(
        version=1,
        timestamp="2026-05-11T00:00:00Z",
        active_app="notepad",
        pid=pid,
        hwnd=hwnd,
        last_action=None,
        last_status=None,
        is_responsive=True,
        focus_stable=focus_stable,
    )


class TypeStateManager:
    def __init__(self, before: AegisStateSnapshot, after: AegisStateSnapshot) -> None:
        self.before = before
        self.after = after
        self._reads = 0

    async def sync_with_os(self, trace_id, span_id) -> None:
        return None

    def get_state(self):
        self._reads += 1
        return self.before if self._reads == 1 else self.after

    def update(self, trace_id, span_id, **kwargs):
        return self.after


def _assert_evidence_state_source_of_truth(
    result: Any,
    *,
    expected_state: str,
    expected_success: bool,
) -> None:
    assert result.success is expected_success
    assert result.execution_evidence is not None
    assert result.execution_evidence.verification_state == expected_state
    assert result.proof["execution_evidence"]["verification_state"] == expected_state
    assert result.execution_evidence.verification_reason
    if expected_state == "unverified":
        failed_checks = [
            check
            for check in result.execution_evidence.verification_checks
            if check.get("passed") is False
        ]
        assert failed_checks
        assert all(check.get("reason") for check in failed_checks)


class FakeTypeTool:
    async def run(self, text: str, **kwargs) -> str:
        assert text == "secret text"
        return "Typed: '[redacted]'"


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
    async def test_open_app_launch_error_can_attach_to_verified_existing_window(self, monkeypatch) -> None:
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

        class FakeOpenTool:
            async def run(self, app: str, **kwargs) -> str:
                return "Error launching 'notepad': Error code from Windows: 0"

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
                active_window={"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242},
                matching_windows=[{"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242}],
                focus_verified=True,
            )
            return DesktopVerificationResult(
                action="open_app",
                method="open_or_focus_window",
                observation=observation,
                verification_state="verified",
                reason="target process is alive and a matching window is present",
                checks=[
                    {
                        "check_name": "window_manifested",
                        "expected": "matching HWND/title",
                        "observed": {"title": "Untitled - Notepad", "hwnd": 101, "pid": 4242},
                        "passed": True,
                        "reason": "Open is window-verified only when a matching HWND/title is observed.",
                    },
                ],
            )

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setattr("aegis.executor.deterministic_executor.verify_desktop_action", fake_verify_desktop_action)
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "open_app", FakeOpenTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "notepad", "_process_name": "notepad.exe", "_keywords": ["Notepad"]},
            risk=RiskLevel.MEDIUM,
            raw_input="open notepad",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.success is True
        assert result.execution_evidence is not None
        assert result.execution_evidence.method == "verified_existing_after_launch_error"
        assert result.execution_evidence.verification_state == "verified"
        assert any("Error launching" in warning for warning in result.execution_evidence.warnings)
        assert result.execution_evidence.observed["dispatch_warning"] == "Error launching 'notepad': Error code from Windows: 0"
        assert result.execution_evidence.observed["dispatch_warning_did_not_determine_verification"] is True

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
        assert result.execution_evidence is not None
        assert result.execution_evidence.verifier == "executor-negative-evidence/1"
        assert result.execution_evidence.verification_state == "failed"
        assert result.execution_evidence.observed["failure_kind"] == "tool_returned_error"
        assert result.execution_evidence.observed["dispatch_succeeded"] is False

    @pytest.mark.asyncio
    async def test_open_app_verifier_failure_is_backed_by_failed_evidence(self, monkeypatch) -> None:
        snapshot = AegisStateSnapshot(
            version=1,
            timestamp="2026-05-13T00:00:00Z",
            active_app=None,
            pid=None,
            hwnd=None,
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

        class FakeOpenTool:
            async def run(self, app: str, **kwargs) -> str:
                return "Error launching 'steam': window did not manifest"

        def fake_verify_desktop_action(**kwargs):
            observation = DesktopObservation(
                target=DesktopTarget(
                    app_id="steam",
                    display_name="Steam",
                    process_name="steam.exe",
                    window_keywords=["Steam"],
                ),
                pids=[4242],
                process_alive=True,
                active_window=None,
                matching_windows=[],
                focus_verified=False,
            )
            return DesktopVerificationResult(
                action="open_app",
                method="process_window",
                observation=observation,
                verification_state="failed",
                reason="target process is alive but no matching window manifested",
                checks=[
                    {
                        "check_name": "process_alive",
                        "expected": True,
                        "observed": True,
                        "passed": True,
                        "reason": "Target process is alive.",
                    },
                    {
                        "check_name": "window_manifested",
                        "expected": "matching HWND/title",
                        "observed": None,
                        "passed": False,
                        "reason": "Open is window-verified only when a matching HWND/title is observed.",
                    },
                    {
                        "check_name": "window_pid_matches_target_process",
                        "expected": {"process_name": "steam.exe"},
                        "observed": None,
                        "passed": None,
                        "reason": "Window PID cannot be checked without a matching window.",
                    },
                ],
            )

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setattr("aegis.executor.deterministic_executor.get_state_manager", lambda: FakeStateManager())
        monkeypatch.setattr("aegis.executor.deterministic_executor.verify_desktop_action", fake_verify_desktop_action)
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "open_app", FakeOpenTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="open_app",
            confidence=1.0,
            params={"app": "steam", "_process_name": "steam.exe", "_keywords": ["Steam"]},
            risk=RiskLevel.MEDIUM,
            raw_input="open steam",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "open_app"
        assert result.execution_evidence.verification_state == "failed"
        checks = {check["check_name"]: check for check in result.execution_evidence.verification_checks}
        assert checks["process_alive"]["passed"] is True
        assert checks["window_manifested"]["passed"] is False
        assert checks["window_pid_matches_target_process"]["passed"] is None

    @pytest.mark.asyncio
    async def test_create_file_existing_path_emits_failed_negative_evidence(self, tmp_path) -> None:
        path = tmp_path / "already-exists.txt"
        path.write_text("existing content\n", encoding="utf-8")
        before_hash = hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="create_file",
            confidence=1.0,
            params={"path": str(path), "content": "new content\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="create file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "create_file"
        assert result.execution_evidence.target_type == "file"
        assert result.execution_evidence.verifier == "executor-negative-evidence/1"
        assert result.execution_evidence.verification_state == "failed"
        assert result.execution_evidence.observed["failure_kind"] == "tool_returned_error"
        assert result.execution_evidence.observed["file"]["mutation_performed"] is False
        assert result.execution_evidence.observed["file"]["before_sha256"] == before_hash
        assert result.execution_evidence.observed["file"]["after_sha256"] == before_hash
        assert path.read_text(encoding="utf-8") == "existing content\n"

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
        assert evidence["chars"] == len("hello evidence")
        assert evidence["sha256"]
        assert evidence["content_hash_captured"] is True
        assert evidence["dispatch_ok"] is True
        assert evidence["truncated"] is False
        assert evidence["resolved_path"] == str(path.resolve())
        assert evidence["file_exists"] is True
        assert evidence["is_file"] is True
        assert evidence["content_hash_matches_disk"] is True
        assert evidence["read_verification_state"] == "verified"
        checks = {check["check_name"]: check for check in evidence["verification_checks"]}
        assert checks["read_file_exists"]["passed"] is True
        assert checks["read_content_hash_matches_disk"]["passed"] is True
        assert result.execution_evidence is not None
        assert result.execution_evidence.verifier == "file-read-gate/1"
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_read_file_evidence_exists_but_missing_disk_source_is_not_verified_success(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "volatile.txt"
        path.write_text("volatile evidence", encoding="utf-8")

        class VanishingReadTool:
            async def run(self, path: str, **kwargs) -> str:
                content = Path(path).read_text(encoding="utf-8")
                Path(path).unlink()
                return content

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "read_file", VanishingReadTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": str(path)},
            risk=RiskLevel.LOW,
            raw_input="read volatile file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        evidence = result.proof["read_only_evidence"]
        assert evidence["read_verification_state"] == "unverified"
        assert evidence["file_exists"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_read_file_path_is_directory_is_unverified_not_success(self, tmp_path) -> None:
        path = tmp_path / "read-dir"
        path.mkdir()
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": str(path)},
            risk=RiskLevel.LOW,
            raw_input="read directory",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        evidence = result.proof["read_only_evidence"]
        assert evidence["file_exists"] is True
        assert evidence["is_file"] is False
        assert evidence["read_verification_state"] == "unverified"
        checks = {check["check_name"]: check for check in evidence["verification_checks"]}
        assert checks["read_path_is_file"]["passed"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_read_file_tool_returns_content_but_disk_hash_cannot_be_captured_is_unverified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "unreadable-after-tool.txt"

        class ReadTextRaisesPath:
            def exists(self) -> bool:
                return True

            def is_file(self) -> bool:
                return True

            def read_text(self, encoding: str = "utf-8") -> str:
                raise OSError("disk hash unavailable")

            def resolve(self):
                return self

            def __str__(self) -> str:
                return str(path)

        class ReturningReadTool:
            async def run(self, path: str, **kwargs) -> str:
                return "returned content"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "read_file", ReturningReadTool())
        monkeypatch.setattr(deterministic_executor_module, "_resolve_read_path", lambda raw_path: ReadTextRaisesPath())
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
        evidence = result.proof["read_only_evidence"]
        assert evidence["content_hash_captured"] is False
        assert evidence["read_error"] == "disk hash unavailable"
        assert evidence["read_verification_state"] == "unverified"
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_read_file_returned_output_differs_from_disk_content_is_unverified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "mismatch.txt"
        path.write_text("disk content", encoding="utf-8")

        class StaleReadTool:
            async def run(self, path: str, **kwargs) -> str:
                return "different returned content"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "read_file", StaleReadTool())
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
        evidence = result.proof["read_only_evidence"]
        assert evidence["content_hash_matches_disk"] is False
        assert evidence["read_verification_state"] == "unverified"
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_read_file_dispatch_exception_is_failed_not_verified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "raise-read.txt"
        path.write_text("disk content", encoding="utf-8")

        class RaisingReadTool:
            async def run(self, path: str, **kwargs) -> str:
                raise RuntimeError("read dispatch failed")

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "read_file", RaisingReadTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": str(path)},
            risk=RiskLevel.LOW,
            raw_input="read file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is None or result.execution_evidence.verification_state != "verified"
        assert "read dispatch failed" in result.output

    @pytest.mark.asyncio
    async def test_read_file_execution_evidence_does_not_contain_raw_file_content(self, tmp_path) -> None:
        path = tmp_path / "sensitive-read.txt"
        path.write_text("read-secret-token", encoding="utf-8")
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="read_file",
            confidence=1.0,
            params={"path": str(path)},
            risk=RiskLevel.LOW,
            raw_input="read sensitive file",
        )

        result = await executor.execute(intent, ctx)

        assert result.execution_evidence is not None
        assert "read-secret-token" not in str(result.execution_evidence.model_dump())
        assert result.execution_evidence.verification_state == "verified"

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
        browser_evidence = result.proof["browser_evidence"]
        assert browser_evidence["tool"] == "search_web"
        assert browser_evidence["query"] == "aegis runtime"
        assert browser_evidence["requested_url"] == "https://www.google.com/search?q=aegis+runtime"
        assert browser_evidence["observed_url"] == "https://www.google.com/search?q=aegis+runtime"
        assert browser_evidence["provider"] == "google"
        assert browser_evidence["provider_domain"] == "www.google.com"
        assert browser_evidence["browser_context_observable"] is True
        assert browser_evidence["dispatch_ok"] is True
        assert browser_evidence["browser_verification_state"] == "verified"
        assert result.execution_evidence is not None
        assert result.execution_evidence.verifier == "browser-url-gate/1"
        assert result.execution_evidence.verification_state == "verified"

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
        assert evidence["requested_url"] == "https://example.com"
        assert evidence["observed_url"] == "https://example.com"
        assert evidence["requested_url_valid"] is True
        assert evidence["browser_context_observable"] is True
        assert evidence["dispatch_ok"] is True
        assert evidence["url_matches_request"] is True
        assert evidence["browser_verification_state"] == "verified"
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "open_url"
        assert result.execution_evidence.target_type == "browser"
        assert result.execution_evidence.method == "browser"
        assert result.execution_evidence.verifier == "browser-url-gate/1"
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_open_url_evidence_exists_but_observed_url_mismatch_is_not_verified_success(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                self.url = "https://unexpected.example/"

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
        evidence = result.proof["browser_evidence"]
        assert evidence["browser_verification_state"] == "unverified"
        assert evidence["url_matches_request"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_open_url_dispatch_exception_is_failed_not_verified(self, monkeypatch) -> None:
        class RaisingOpenURLTool:
            async def run(self, url: str, page=None, **kwargs) -> str:
                raise RuntimeError("browser dispatch failed")

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "open_url", RaisingOpenURLTool())

        async def fake_get_page():
            return object()

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

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is None or result.execution_evidence.verification_state != "verified"
        assert "browser dispatch failed" in result.output

    @pytest.mark.asyncio
    async def test_search_web_query_missing_from_observable_url_is_unverified_not_success(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                self.url = "https://www.google.com/search?q=different"

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
        evidence = result.proof["browser_evidence"]
        assert evidence["browser_verification_state"] == "unverified"
        assert evidence["query_matches_observed_url"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_open_url_missing_browser_context_is_unverified_not_success(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                return None

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
        evidence = result.proof["browser_evidence"]
        assert evidence["browser_context_observable"] is False
        assert evidence["browser_verification_state"] == "unverified"
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_open_url_execution_evidence_does_not_contain_full_page_content(self, monkeypatch) -> None:
        secret_page_content = "full-page-secret-content"

        class ContentReturningOpenURLTool:
            async def run(self, url: str, page=None, **kwargs) -> str:
                page.url = url
                return secret_page_content

        class FakePage:
            url = ""

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "open_url", ContentReturningOpenURLTool())

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

        assert result.execution_evidence is not None
        assert secret_page_content not in str(result.execution_evidence.model_dump())
        assert result.execution_evidence.verification_state == "verified"

    @pytest.mark.asyncio
    async def test_search_web_bot_challenge_requires_approval_not_verified_success(self, monkeypatch) -> None:
        class FakePage:
            async def goto(self, url: str, wait_until: str = "networkidle") -> None:
                self.url = "https://www.google.com/sorry/index?continue=https://www.google.com/search%3Fq%3Daegis%2Bruntime"

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
        evidence = result.proof["browser_evidence"]
        assert evidence["bot_challenge_detected"] is True
        assert evidence["browser_verification_state"] == "approval_required"
        _assert_evidence_state_source_of_truth(result, expected_state="approval_required", expected_success=False)

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
            assert evidence["expected_after_sha256"] == hashlib.sha256("new line\n".encode("utf-8")).hexdigest()
            assert evidence["path_unchanged"] is True
            assert evidence["write_confirmed"] is True
            assert evidence["write_verification_state"] == "verified"
            assert "diff_preview" not in evidence
            assert "old line" not in str(evidence)
            assert "new line" not in str(evidence)
            assert result.execution_evidence is not None
            assert result.execution_evidence.action == "write_file"
            assert result.execution_evidence.target_type == "file"
            assert result.execution_evidence.method == "write"
            assert result.execution_evidence.verifier == "file-write-gate/1"
            assert result.execution_evidence.verification_state == "verified"
        finally:
            if path.exists():
                path.unlink()

    @pytest.mark.asyncio
    async def test_write_file_evidence_exists_but_unconfirmed_disk_write_is_not_verified_success(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "unchanged.txt"
        path.write_text("old line\n", encoding="utf-8")

        class NoopWriteTool:
            async def run(self, path: str, content: str, **kwargs) -> str:
                return f"Successfully written to {path}"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "write_file", NoopWriteTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new line\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        evidence = result.proof["write_evidence"]
        assert evidence["write_verification_state"] == "unverified"
        assert evidence["write_confirmed"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_write_file_new_file_success_records_existed_before_false_and_verifies(self) -> None:
        path = PROJECT_ROOT / "scratch" / "executor-write-new-file-test.txt"
        if path.exists():
            path.unlink()
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new file content\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write new file",
        )

        try:
            result = await executor.execute(intent, ctx)

            assert result.status == ActionStatus.EXECUTED
            assert result.success is True
            evidence = result.proof["write_evidence"]
            assert evidence["existed_before"] is False
            assert evidence["before_sha256"] is None
            assert evidence["before_state_known"] is True
            assert evidence["write_confirmed"] is True
            assert evidence["write_verification_state"] == "verified"
            assert result.execution_evidence is not None
            assert result.execution_evidence.verification_state == "verified"
        finally:
            if path.exists():
                path.unlink()

    @pytest.mark.asyncio
    async def test_write_file_success_text_but_target_missing_after_dispatch_is_unverified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "missing-after.txt"

        class NoCreateWriteTool:
            async def run(self, path: str, content: str, **kwargs) -> str:
                return f"Successfully written to {path}"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "write_file", NoCreateWriteTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new content\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        evidence = result.proof["write_evidence"]
        assert evidence["write_verification_state"] == "unverified"
        checks = {check["check_name"]: check for check in evidence["verification_checks"]}
        assert checks["write_file_exists_after"]["passed"] is False
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_write_file_after_hash_differs_from_requested_content_is_unverified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "wrong-content.txt"
        path.write_text("old line\n", encoding="utf-8")

        class WrongContentWriteTool:
            async def run(self, path: str, content: str, **kwargs) -> str:
                Path(path).write_text("different content\n", encoding="utf-8")
                return f"Successfully written to {path}"

        executor = DeterministicExecutor()
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "write_file", WrongContentWriteTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "requested content\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        evidence = result.proof["write_evidence"]
        assert evidence["write_verification_state"] == "unverified"
        assert evidence["write_confirmed"] is False
        assert evidence["after_sha256"] != evidence["expected_after_sha256"]
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)

    @pytest.mark.asyncio
    async def test_write_file_dispatch_exception_is_failed_not_verified(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "raise.txt"

        class RaisingWriteTool:
            async def run(self, path: str, content: str, **kwargs) -> str:
                raise RuntimeError("write dispatch failed")

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "write_file", RaisingWriteTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new content\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write file",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is not None
        assert result.execution_evidence.verifier == "executor-negative-evidence/1"
        assert result.execution_evidence.verification_state == "failed"
        assert result.execution_evidence.observed["failure_kind"] == "dispatch_exception"
        assert result.execution_evidence.observed["file"]["mutation_performed"] is False
        assert "write dispatch failed" in result.output

    @pytest.mark.asyncio
    async def test_write_file_execution_evidence_does_not_contain_raw_file_content(self) -> None:
        path = PROJECT_ROOT / "scratch" / "executor-write-sensitive-test.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old-secret-token\n", encoding="utf-8")
        executor = DeterministicExecutor()
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(path), "content": "new-secret-token\n"},
            risk=RiskLevel.MEDIUM,
            raw_input="write sensitive file",
        )

        try:
            result = await executor.execute(intent, ctx)

            assert result.execution_evidence is not None
            evidence_text = str(result.execution_evidence.model_dump())
            assert "old-secret-token" not in evidence_text
            assert "new-secret-token" not in evidence_text
            assert result.execution_evidence.verification_state == "verified"
        finally:
            if path.exists():
                path.unlink()

    @pytest.mark.asyncio
    async def test_type_success_includes_type_evidence_without_raw_text(self, monkeypatch) -> None:
        executor = DeterministicExecutor()
        monkeypatch.setattr(
            "aegis.executor.deterministic_executor.get_state_manager",
            lambda: TypeStateManager(_snapshot(hwnd=5678), _snapshot(hwnd=5678)),
        )
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "type", FakeTypeTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="type",
            confidence=1.0,
            params={
                "text": "secret text",
                "_require_focus": "notepad",
                "_require_focus_process_name": "notepad.exe",
                "_require_focus_keywords": ["Notepad"],
            },
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
        assert evidence["expected_focus"] == "notepad"
        assert evidence["expected_focus_process_name"] == "notepad.exe"
        assert evidence["expected_focus_keywords"] == ["Notepad"]
        assert evidence["focus_verified_before"] is True
        assert evidence["focus_verified_after"] is True
        assert evidence["focus_did_not_change_unexpectedly"] is True
        assert evidence["dispatch_ok"] is True
        assert evidence["type_verification_state"] == "verified"
        checks = {check["check_name"]: check for check in evidence["verification_checks"]}
        assert checks["dispatch_ok"]["passed"] is True
        assert evidence["target_before"]["hwnd"] == 5678
        assert evidence["target_after"]["pid"] == 1234
        assert "secret text" not in str(evidence)
        assert result.execution_evidence is not None
        assert result.execution_evidence.action == "type"
        assert result.execution_evidence.target == "focused_input"
        assert result.execution_evidence.target_type == "focused_input"
        assert result.execution_evidence.verification_state == "verified"
        assert "secret text" not in str(result.execution_evidence)

    @pytest.mark.parametrize(
        ("before", "after", "expected_failed_check"),
        [
            (_snapshot(hwnd=None), _snapshot(hwnd=5678), "before_hwnd_present"),
            (_snapshot(hwnd=5678), _snapshot(hwnd=None), "after_hwnd_present"),
            (_snapshot(hwnd=5678), _snapshot(hwnd=8765), "focus_did_not_change_unexpectedly"),
            (_snapshot(hwnd=5678, focus_stable=False), _snapshot(hwnd=5678), "focus_verified_before"),
        ],
    )
    def test_type_evidence_marks_missing_or_unstable_focus_unverified(
        self,
        before: AegisStateSnapshot,
        after: AegisStateSnapshot,
        expected_failed_check: str,
    ) -> None:
        evidence = _type_evidence(
            "type",
            {"text": "secret text", "_require_focus": "notepad"},
            before,
            after,
            "Typed: '[redacted]'",
        )

        assert evidence is not None
        assert evidence["type_verification_state"] == "unverified"
        assert evidence["focus_did_not_change_unexpectedly"] is bool(before.hwnd and after.hwnd and before.hwnd == after.hwnd)
        checks = {check["check_name"]: check for check in evidence["verification_checks"]}
        assert checks[expected_failed_check]["passed"] is False

    @pytest.mark.asyncio
    async def test_type_evidence_exists_but_focus_change_is_not_verified_success(self, monkeypatch) -> None:
        executor = DeterministicExecutor()
        monkeypatch.setattr(
            "aegis.executor.deterministic_executor.get_state_manager",
            lambda: TypeStateManager(_snapshot(hwnd=5678), _snapshot(hwnd=8765)),
        )
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "type", FakeTypeTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="type",
            confidence=1.0,
            params={"text": "secret text", "_require_focus": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="type secret text",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.EXECUTED
        assert result.proof["type_evidence"]["type_verification_state"] == "unverified"
        _assert_evidence_state_source_of_truth(result, expected_state="unverified", expected_success=False)
        assert result.execution_evidence.verification_reason == "focus changed unexpectedly during type action"

    @pytest.mark.asyncio
    async def test_type_dispatch_exception_is_failed_not_verified(self, monkeypatch) -> None:
        class RaisingTypeTool:
            async def run(self, text: str, **kwargs) -> str:
                raise RuntimeError("keyboard dispatch failed")

        executor = DeterministicExecutor()
        executor.max_retries = 0
        monkeypatch.setattr(
            "aegis.executor.deterministic_executor.get_state_manager",
            lambda: TypeStateManager(_snapshot(hwnd=5678), _snapshot(hwnd=5678)),
        )
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "type", RaisingTypeTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="type",
            confidence=1.0,
            params={"text": "secret text", "_require_focus": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="type secret text",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is not None
        assert result.execution_evidence.verifier == "executor-negative-evidence/1"
        assert result.execution_evidence.verification_state == "failed"
        assert result.execution_evidence.target_type == "focused_input"
        assert result.execution_evidence.observed["failure_kind"] == "dispatch_exception"
        assert result.execution_evidence.observed["verified_success"] is False
        assert "keyboard dispatch failed" in result.output

    @pytest.mark.asyncio
    async def test_type_precondition_failure_emits_non_executed_negative_evidence(self, monkeypatch) -> None:
        class PreconditionFailureTransitionModel:
            def validate_preconditions(self, intent, before_state):
                return ["focus is unstable"]

            def predict_next_state(self, before_state, intent, params):
                raise AssertionError("precondition failure must stop before planning next state")

        class ExplodingTypeTool:
            async def run(self, text: str, **kwargs) -> str:
                raise AssertionError("type tool must not run when preconditions fail")

        executor = DeterministicExecutor()
        executor.transition_model = PreconditionFailureTransitionModel()
        monkeypatch.setattr(
            "aegis.executor.deterministic_executor.get_state_manager",
            lambda: TypeStateManager(_snapshot(hwnd=5678, focus_stable=False), _snapshot(hwnd=5678)),
        )
        monkeypatch.setitem(deterministic_executor_module.TOOLS, "type", ExplodingTypeTool())
        ctx = ExecutionContext.create_root()
        intent = IntentResult(
            intent="type",
            confidence=1.0,
            params={"text": "secret text", "_require_focus": "notepad"},
            risk=RiskLevel.MEDIUM,
            raw_input="type secret text",
        )

        result = await executor.execute(intent, ctx)

        assert result.status == ActionStatus.FAILED
        assert result.success is False
        assert result.execution_evidence is not None
        assert result.execution_evidence.verification_state == "failed"
        assert result.execution_evidence.verifier == "executor-negative-evidence/1"
        assert result.execution_evidence.observed["failure_kind"] == "precondition_failed"
        assert result.execution_evidence.observed["dispatch_attempted"] is False
        assert result.execution_evidence.observed["dispatch_succeeded"] is False

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
