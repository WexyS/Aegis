from __future__ import annotations

import pytest

from aegis.tools.desktop_tools import CloseAppTool, FocusTool, OpenAppTool
from aegis.tools.registry import get_tool, list_tools
from aegis.orchestrator.orchestrator import VERIFIED_TOOLS


class FakeWindow:
    def __init__(self, title: str, *, visible: bool = True, minimized: bool = False) -> None:
        self.title = title
        self.visible = visible
        self.isMinimized = minimized
        self.restored = False
        self.activated = False
        self._hWnd = 4242

    def restore(self) -> None:
        self.restored = True
        self.isMinimized = False

    def activate(self) -> None:
        self.activated = True


@pytest.mark.asyncio
async def test_focus_app_activates_matching_visible_window(monkeypatch) -> None:
    window = FakeWindow("Untitled - Notepad", minimized=True)
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getAllWindows", lambda: [window])
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getActiveWindow", lambda: window)
    monkeypatch.setattr("aegis.tools.desktop_tools.get_window_pid", lambda hwnd: 4242)

    result = await FocusTool().run("notepad")

    assert window.restored is True
    assert window.activated is True
    assert "Focused 'notepad'" in result
    assert "HWND: 4242" in result


@pytest.mark.asyncio
async def test_focus_app_records_selection_and_foreground_evidence(monkeypatch) -> None:
    window = FakeWindow("Untitled - Notepad")
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getAllWindows", lambda: [window])
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getActiveWindow", lambda: window)
    monkeypatch.setattr("aegis.tools.desktop_tools.get_window_pid", lambda hwnd: 4242)
    evidence: list[dict] = []

    result = await FocusTool().run("notepad", _focus_evidence=evidence)

    assert "Focused 'notepad'" in result
    assert evidence[0]["candidate_count"] == 1
    assert evidence[0]["selected_window"]["hwnd"] == 4242
    assert evidence[0]["selected_window"]["pid"] == 4242
    assert evidence[0]["foreground_after"]["hwnd"] == 4242
    assert evidence[0]["activate_called"] is True
    assert evidence[0]["outcome"] == "focused"


@pytest.mark.asyncio
async def test_focus_app_can_filter_by_expected_pid(monkeypatch) -> None:
    other = FakeWindow("Aegis Smoke", visible=True)
    other._hWnd = 1111
    target = FakeWindow("Aegis Smoke", visible=True)
    target._hWnd = 2222
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getAllWindows", lambda: [other, target])
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getActiveWindow", lambda: target)
    monkeypatch.setattr("aegis.tools.desktop_tools.get_window_pid", lambda hwnd: 5150 if hwnd == 2222 else 4242)
    evidence: list[dict] = []

    result = await FocusTool().run("smoke", _keywords=["Aegis Smoke"], _expected_pids=[5150], _focus_evidence=evidence)

    assert "Focused 'smoke'" in result
    assert target.activated is True
    assert other.activated is False
    assert evidence[0]["candidate_count"] == 1
    assert evidence[0]["selected_window"]["pid"] == 5150


@pytest.mark.asyncio
async def test_focus_app_reports_missing_window(monkeypatch) -> None:
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getAllWindows", lambda: [FakeWindow("Calculator")])

    result = await FocusTool().run("notepad")

    assert result == "Error: No visible window found for 'notepad'."


@pytest.mark.asyncio
async def test_open_app_subprocess_fallback_does_not_use_shell(monkeypatch) -> None:
    calls = []
    window = FakeWindow("Untitled - Notepad")

    def fake_startfile(path: str) -> None:
        raise OSError("startfile unavailable")

    class FakePopen:
        def __init__(self, path, **kwargs) -> None:
            calls.append({"path": path, **kwargs})

        def poll(self):
            return None

    monkeypatch.setattr("aegis.tools.desktop_tools.os.startfile", fake_startfile, raising=False)
    monkeypatch.setattr("aegis.tools.desktop_tools.subprocess.Popen", FakePopen)
    monkeypatch.setattr("aegis.tools.desktop_tools.gw.getAllWindows", lambda: [window])

    result = await OpenAppTool().run("notepad", _resolved_path="notepad.exe", _keywords=["Notepad"])

    assert calls == [{"path": ["notepad.exe"], "shell": False}]
    assert "Successfully launched 'notepad'" in result


class FakeProcess:
    def __init__(self, name: str, pid: int | None = None) -> None:
        self.info = {"name": name, "pid": pid}
        self.pid = pid
        self.terminated = False
        self.killed = False

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def name(self) -> str:
        return self.info["name"]


@pytest.mark.asyncio
async def test_close_app_terminates_exact_matching_process(monkeypatch) -> None:
    target = FakeProcess("notepad.exe")
    near_miss = FakeProcess("notepad++.exe")

    monkeypatch.setattr("psutil.process_iter", lambda attrs: [target, near_miss])
    monkeypatch.setattr("psutil.wait_procs", lambda procs, timeout: (procs, []))

    result = await CloseAppTool().run("notepad")

    assert target.terminated is True
    assert near_miss.terminated is False
    assert result == "Closed 1 instance(s) of notepad."


@pytest.mark.asyncio
async def test_close_app_records_kill_fallback_evidence(monkeypatch) -> None:
    target = FakeProcess("notepad.exe", pid=4242)
    wait_calls = []

    def fake_wait_procs(procs, timeout):
        wait_calls.append(timeout)
        if len(wait_calls) == 1:
            return ([], procs)
        return (procs, [])

    monkeypatch.setattr("psutil.process_iter", lambda attrs: [target])
    monkeypatch.setattr("psutil.wait_procs", fake_wait_procs)
    evidence: list[dict] = []

    result = await CloseAppTool().run("notepad", timeout=0.01, _close_evidence=evidence)

    assert target.terminated is True
    assert target.killed is True
    assert result == "Closed 1 instance(s) of notepad."
    assert evidence[0]["initial_pids"] == [4242]
    assert evidence[0]["terminate_sent_pids"] == [4242]
    assert evidence[0]["kill_sent_pids"] == [4242]
    assert evidence[0]["killed_pids"] == [4242]
    assert evidence[0]["outcome"] == "killed"


@pytest.mark.asyncio
async def test_close_app_can_limit_to_expected_pids(monkeypatch) -> None:
    target = FakeProcess("notepad.exe", pid=4242)
    other = FakeProcess("notepad.exe", pid=5150)

    def fake_process(pid):
        return {4242: target, 5150: other}[pid]

    monkeypatch.setattr("psutil.Process", fake_process)
    monkeypatch.setattr("psutil.wait_procs", lambda procs, timeout: (procs, []))

    result = await CloseAppTool().run("notepad", _expected_pids=[4242])

    assert result == "Closed 1 instance(s) of notepad."
    assert target.terminated is True
    assert other.terminated is False


def test_search_web_is_registered_because_parser_can_emit_it() -> None:
    assert "search_web" in list_tools()
    assert get_tool("search_web") is not None


def test_verified_executable_tools_are_registered() -> None:
    non_executable_verified = {"general_chat"}
    registered = set(list_tools())
    missing = set(VERIFIED_TOOLS) - registered - non_executable_verified

    assert missing == set()


@pytest.mark.asyncio
async def test_search_web_navigates_to_search_url() -> None:
    class FakePage:
        def __init__(self) -> None:
            self.urls: list[str] = []

        async def goto(self, url: str, wait_until: str = "networkidle") -> None:
            assert wait_until == "networkidle"
            self.urls.append(url)

    page = FakePage()

    tool = get_tool("search_web")

    result = await tool.run("aegis runtime", page=page)

    assert page.urls == ["https://www.google.com/search?q=aegis+runtime"]
    assert result == "Search opened: aegis runtime"
