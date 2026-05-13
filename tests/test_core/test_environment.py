from __future__ import annotations

from pathlib import Path

from aegis.core import environment


def test_environment_diagnostics_reports_path_and_project_state(monkeypatch, tmp_path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (frontend / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".git").mkdir()

    monkeypatch.setattr(environment.sys, "executable", r"C:\Aegis\.venv\Scripts\python.exe")
    monkeypatch.setattr(environment.platform, "python_version", lambda: "3.11.9")
    monkeypatch.setattr(environment.shutil, "which", lambda command: rf"C:\Tools\{command}.exe")
    monkeypatch.setattr(environment, "_module_available", lambda name: name in {"pytest", "playwright"})
    monkeypatch.setattr(environment, "_run_version", lambda command: "v1.2.3")
    monkeypatch.setattr(environment, "_resolve_git_executable", lambda: r"C:\Program Files\Git\cmd\git.exe")

    report = environment.collect_environment_diagnostics(project_root=tmp_path)

    assert report["scan_version"] == "environment-diagnostics/1"
    assert report["read_only"] is True
    assert report["checks"]["python"]["status"] == "ok"
    assert report["checks"]["python"]["in_virtualenv"] is True
    assert report["checks"]["git"]["status"] == "ok"
    assert report["checks"]["git"]["repository_present"] is True
    assert report["checks"]["node"]["status"] == "ok"
    assert report["checks"]["npm"]["preferred_command"] == "npm.cmd"
    assert report["checks"]["frontend"]["package_json"] is True
    assert report["checks"]["playwright"]["status"] == "ok"
    assert report["recommendations"] == []


def test_environment_diagnostics_warns_for_missing_tools(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(environment.sys, "executable", r"C:\Python311\python.exe")
    monkeypatch.setattr(environment.sys, "prefix", r"C:\Python311")
    monkeypatch.setattr(environment.sys, "base_prefix", r"C:\Python311")
    monkeypatch.setattr(environment.platform, "python_version", lambda: "3.11.9")
    monkeypatch.setattr(environment.shutil, "which", lambda command: None)
    monkeypatch.setattr(environment, "_module_available", lambda name: False)
    monkeypatch.setattr(environment, "_run_version", lambda command: None)
    monkeypatch.setattr(environment, "_resolve_git_executable", lambda: None)

    report = environment.collect_environment_diagnostics(project_root=tmp_path)

    assert report["overall_status"] == "warning"
    assert report["checks"]["python"]["status"] == "warning"
    assert report["checks"]["git"]["status"] == "warning"
    assert report["checks"]["git"]["repository_present"] is False
    assert report["checks"]["node"]["status"] == "warning"
    assert report["checks"]["npm"]["status"] == "warning"
    assert report["checks"]["pytest"]["status"] == "warning"
    assert report["checks"]["playwright"]["status"] == "warning"
    assert any("Git" in item for item in report["recommendations"])
    assert any(".venv" in item for item in report["recommendations"])
