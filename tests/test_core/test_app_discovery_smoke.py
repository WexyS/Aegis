from __future__ import annotations

from aegis.core.app_discovery_smoke import build_configured_app_discovery_smoke
from aegis.tools.desktop_tools import FocusTool, OpenAppTool


class FakeWindow:
    def __init__(self, title: str, hwnd: int, *, visible: bool = True) -> None:
        self.title = title
        self._hWnd = hwnd
        self.visible = visible
        self.isMinimized = False

    def activate(self) -> None:
        raise AssertionError("diagnostic must not focus windows")


def _entry(report: dict, app_id: str) -> dict:
    return next(item for item in report["entries"] if item["app_id"] == app_id)


def test_smoke_reports_antigravity_ide_and_agent_manager_distinctly(monkeypatch, tmp_path) -> None:
    ide = tmp_path / "Programs" / "Antigravity IDE" / "Antigravity IDE.exe"
    manager = tmp_path / "Programs" / "Antigravity" / "Antigravity.exe"
    ide.parent.mkdir(parents=True)
    manager.parent.mkdir(parents=True)
    ide.write_text("", encoding="utf-8")
    manager.write_text("", encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = build_configured_app_discovery_smoke(["antigravity", "antigravity_agent_manager"])
    ide_entry = _entry(report, "antigravity")
    manager_entry = _entry(report, "antigravity_agent_manager")

    assert report["read_only"] is True
    assert report["actions_performed"] == []
    assert ide_entry["aliases"] == ["antigravity", "antigravity ide", "antigravity i", "google antigravity"]
    assert ide_entry["process_name_candidates"] == ["Antigravity IDE.exe"]
    assert ide_entry["executable_candidates"][0]["path_exists"] is True
    assert manager_entry["process_name_candidates"] == ["Antigravity.exe"]
    assert manager_entry["executable_candidates"][0]["path_exists"] is True
    assert manager_entry["app_id"] != ide_entry["app_id"]


def test_missing_path_reports_missing_not_success(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = build_configured_app_discovery_smoke(["antigravity"])
    entry = _entry(report, "antigravity")

    assert entry["executable_candidates"][0]["path_exists"] is False
    assert entry["executable_candidates"][0]["resolved_read_only"] is False
    assert entry["deterministic_verification_possible"] is False
    assert "running_process_not_observed" in entry["verification_blockers"]
    assert "matching_window_not_observed" in entry["verification_blockers"]
    assert "verified" not in entry
    assert "verification_state" not in entry


def test_matching_window_without_process_identity_remains_unverified(monkeypatch, tmp_path) -> None:
    window = FakeWindow("Antigravity IDE", 101)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [window])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_window_pid", lambda hwnd: None)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = build_configured_app_discovery_smoke(["antigravity"])
    entry = _entry(report, "antigravity")

    assert entry["matching_window_count"] == 1
    assert entry["matching_windows"][0]["pid_matches_process"] is None
    assert entry["process_alive"] is False
    assert entry["deterministic_verification_possible"] is False
    assert entry["diagnostic_state"] in {"ambiguous", "partially_observed"}


def test_multiple_matching_windows_report_ambiguous(monkeypatch, tmp_path) -> None:
    first = FakeWindow("Antigravity IDE", 101)
    second = FakeWindow("Antigravity IDE - Settings", 202)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [first, second])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_window_pid", lambda hwnd: 4242 if hwnd in {101, 202} else None)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [4242])

    report = build_configured_app_discovery_smoke(["antigravity"])
    entry = _entry(report, "antigravity")

    assert entry["matching_window_count"] == 2
    assert entry["pid_matched_window_count"] == 2
    assert entry["ambiguity_status"] == "ambiguous"
    assert "ambiguous_pid_matched_windows" in entry["verification_blockers"]
    assert entry["deterministic_verification_possible"] is False


def test_antigravity_ide_window_reports_cross_app_title_ambiguity(monkeypatch, tmp_path) -> None:
    window = FakeWindow("Antigravity IDE", 101)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [window])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_window_pid", lambda hwnd: 4242)
    monkeypatch.setattr(
        "aegis.core.app_discovery_smoke.get_running_pids",
        lambda process_name: [4242] if process_name == "Antigravity IDE.exe" else [],
    )

    report = build_configured_app_discovery_smoke(["antigravity"])
    entry = _entry(report, "antigravity")

    assert entry["matching_windows"][0]["matching_configured_app_ids"] == [
        "antigravity",
        "antigravity_agent_manager",
    ]
    assert entry["ambiguity_status"] == "ambiguous"
    assert "ambiguous_title_matches_multiple_configured_apps" in entry["verification_blockers"]
    assert entry["deterministic_verification_possible"] is False


def test_unknown_app_reports_unknown_safely(monkeypatch) -> None:
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])

    report = build_configured_app_discovery_smoke(["missing_app"])
    entry = _entry(report, "missing_app")

    assert entry["known"] is False
    assert entry["diagnostic_state"] == "unknown"
    assert entry["deterministic_verification_possible"] is False
    assert entry["verification_blockers"] == ["unknown_configured_app"]


def test_smoke_does_not_launch_focus_or_click(monkeypatch) -> None:
    window = FakeWindow("Antigravity IDE", 101)
    calls = {"open": 0, "focus": 0}

    async def forbidden_open(*args, **kwargs):
        calls["open"] += 1
        raise AssertionError("diagnostic must not launch apps")

    async def forbidden_focus(*args, **kwargs):
        calls["focus"] += 1
        raise AssertionError("diagnostic must not focus apps")

    monkeypatch.setattr(OpenAppTool, "run", forbidden_open)
    monkeypatch.setattr(FocusTool, "run", forbidden_focus)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [window])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_window_pid", lambda hwnd: None)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = build_configured_app_discovery_smoke(["antigravity"])

    assert report["actions_performed"] == []
    assert calls == {"open": 0, "focus": 0}


def test_structured_output_avoids_evidence_success_fields(monkeypatch) -> None:
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = build_configured_app_discovery_smoke(["notepad"])
    entry = _entry(report, "notepad")

    assert set(report) >= {"scan_version", "read_only", "entry_count", "entries"}
    assert "execution_evidence" not in entry
    assert "verification_state" not in entry
    assert "success" not in entry
    assert entry["deterministic_verification_possible"] is False
