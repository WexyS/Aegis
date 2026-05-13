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

    result = await FocusTool().run("notepad")

    assert window.restored is True
    assert window.activated is True
    assert "Focused 'notepad'" in result
    assert "HWND: 4242" in result


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
    def __init__(self, name: str) -> None:
        self.info = {"name": name}
        self.terminated = False
        self.killed = False

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True


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
