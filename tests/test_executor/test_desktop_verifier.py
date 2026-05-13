from __future__ import annotations

from aegis.executor.desktop_verifier import make_desktop_execution_evidence, observe_desktop_target


class FakeWindow:
    def __init__(self, title: str, hwnd: int, *, visible: bool = True) -> None:
        self.title = title
        self._hWnd = hwnd
        self.visible = visible
        self.isMinimized = False


def test_observe_desktop_target_verifies_active_window_by_pid_and_title(monkeypatch) -> None:
    active = FakeWindow("Untitled - Notepad", 101)
    other = FakeWindow("Calculator", 202)

    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "notepad")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Notepad"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [4242])
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 4242 if hwnd == 101 else 5150)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: active)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [active, other])

    observation = observe_desktop_target("notepad")

    assert observation.process_alive is True
    assert observation.focus_verified is True
    assert observation.primary_window["hwnd"] == 101
    assert observation.matching_windows == [
        {
            "title": "Untitled - Notepad",
            "hwnd": 101,
            "pid": 4242,
            "is_minimized": False,
            "visible": True,
        }
    ]


def test_desktop_execution_evidence_uses_observed_process_and_window(monkeypatch) -> None:
    window = FakeWindow("Steam Library", 303)
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "steam")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"process_name": "steam.exe", "window_keywords": ["Steam"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [777])
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 777)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: window)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [window])

    observation = observe_desktop_target("steam")
    evidence = make_desktop_execution_evidence(
        action="focus_app",
        app="steam",
        method="focus_window",
        started_at_ms=1,
        observation=observation,
        verification_state="verified",
    )

    assert evidence.action == "focus_app"
    assert evidence.target == "steam"
    assert evidence.process_name == "steam.exe"
    assert evidence.pids == [777]
    assert evidence.process_alive is True
    assert evidence.window["title"] == "Steam Library"
    assert evidence.verification_state == "verified"
