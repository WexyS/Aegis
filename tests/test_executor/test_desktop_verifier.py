from __future__ import annotations

from aegis.executor.desktop_verifier import (
    make_desktop_execution_evidence,
    observe_desktop_target,
    resolve_desktop_target,
    verification_to_execution_evidence,
    verify_desktop_action,
)


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
    assert evidence.verifier == "process-window-verifier/2"
    assert evidence.observed["primary_hwnd"] == 303
    assert evidence.expected["process_name"] == "steam.exe"


def test_verify_desktop_action_open_requires_pid_and_window_title(monkeypatch) -> None:
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

    verification = verify_desktop_action(action="open_app", app="steam")
    evidence = verification_to_execution_evidence(
        verification=verification,
        app="steam",
        started_at_ms=1,
    )

    assert verification.verified is True
    assert evidence.verification_state == "verified"
    assert evidence.verification_reason == "target process is alive and a matching window is present"
    assert evidence.process_alive is True
    assert evidence.pids == [777]
    assert evidence.window["hwnd"] == 303
    assert evidence.window["pid"] == 777
    assert evidence.window["title"] == "Steam Library"
    assert {check["check_name"] for check in evidence.verification_checks} >= {
        "process_name_known",
        "process_alive",
        "window_manifested",
        "window_pid_matches_target_process",
    }


def test_verify_desktop_action_can_use_expected_pids(monkeypatch) -> None:
    window = FakeWindow("Aegis Smoke", 303)
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "smoke")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Aegis Smoke"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [111])
    monkeypatch.setattr("aegis.executor.desktop_verifier.psutil.pid_exists", lambda pid: pid == 777)
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 777)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: window)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [window])

    verification = verify_desktop_action(action="open_app", app="smoke", expected_pids=[777])

    assert verification.verified is True
    assert verification.observation.pids == [777]


def test_verify_desktop_action_focus_marks_ambiguous_windows_failed(monkeypatch) -> None:
    first = FakeWindow("Untitled - Notepad", 101)
    second = FakeWindow("Notes - Notepad", 202)
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "notepad")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Notepad"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [4242, 5150])
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 4242 if hwnd == 101 else 5150)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: first)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [first, second])

    verification = verify_desktop_action(action="focus_app", app="notepad")
    evidence = verification_to_execution_evidence(
        verification=verification,
        app="notepad",
        started_at_ms=1,
    )

    assert verification.verification_state == "failed"
    assert verification.ambiguous is True
    assert evidence.verification_state == "failed"
    assert evidence.observed["matching_window_count"] == 2
    assert len(evidence.matching_windows) == 2
    assert any(
        check["check_name"] == "single_matching_window" and check["passed"] is False
        for check in evidence.verification_checks
    )


def test_verify_desktop_action_close_records_inferred_process_not_alive(monkeypatch) -> None:
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "portal")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"window_keywords": ["Portal"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: None)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [])

    verification = verify_desktop_action(action="close_app", app="portal")
    evidence = verification_to_execution_evidence(
        verification=verification,
        app="portal",
        started_at_ms=1,
    )

    assert verification.verification_state == "verified"
    assert evidence.process_name == "portal.exe"
    assert evidence.process_alive is False
    assert evidence.verification_reason == "target process is no longer alive"


def test_antigravity_alias_uses_explicit_process_mapping() -> None:
    target = resolve_desktop_target("antigravity i")

    assert target.app_id == "antigravity"
    assert target.process_name == "Antigravity IDE.exe"
    assert "Antigravity IDE" in target.window_keywords


def test_unknown_multi_word_app_does_not_infer_invalid_exe() -> None:
    target = resolve_desktop_target("unknown ide")

    assert target.app_id == "unknown ide"
    assert target.process_name is None
    assert target.window_keywords == ["unknown ide", "unknown ide"]


def test_window_title_without_process_identity_remains_unverified(monkeypatch) -> None:
    window = FakeWindow("Unknown IDE", 909)
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: None)
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_app_config", lambda app_id: None)
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: None)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: window)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [window])

    verification = verify_desktop_action(action="open_app", app="unknown ide")

    assert verification.verified is False
    assert verification.verification_state == "unverified"
    assert verification.reason == "process_name is not configured"
    assert verification.observation.process_alive is None
    assert verification.observation.matching_windows[0]["title"] == "Unknown IDE"


def test_verify_desktop_action_focus_records_foreground_pid_match_check(monkeypatch) -> None:
    active = FakeWindow("Untitled - Notepad", 101)
    monkeypatch.setattr("aegis.executor.desktop_verifier.resolve_app_name", lambda app: "notepad")
    monkeypatch.setattr(
        "aegis.executor.desktop_verifier.get_app_config",
        lambda app_id: {"process_name": "notepad.exe", "window_keywords": ["Notepad"]},
    )
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_running_pids", lambda process_name: [4242])
    monkeypatch.setattr("aegis.executor.desktop_verifier.get_window_pid", lambda hwnd: 4242)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getActiveWindow", lambda: active)
    monkeypatch.setattr("aegis.executor.desktop_verifier.gw.getAllWindows", lambda: [active])

    verification = verify_desktop_action(action="focus_app", app="notepad")
    evidence = verification_to_execution_evidence(
        verification=verification,
        app="notepad",
        started_at_ms=1,
    )

    checks = {check["check_name"]: check for check in evidence.verification_checks}
    assert checks["foreground_hwnd_present"]["observed"] == 101
    assert checks["foreground_pid_matches_target_process"]["expected"] == [4242]
    assert checks["foreground_pid_matches_target_process"]["observed"] == 4242
    assert checks["foreground_pid_matches_target_process"]["passed"] is True
