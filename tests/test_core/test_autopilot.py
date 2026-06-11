from __future__ import annotations

from pathlib import Path

from aegis.core.autopilot import run_repo_structure_audit


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sample_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / "README.md", "# Demo")
    _write(root / "pyproject.toml", "[project]\nname='demo'\n")
    _write(root / "src" / "demo" / "__init__.py", "")
    _write(root / "tests" / "test_demo.py", "def test_demo(): assert True\n")
    _write(root / "docs" / "index.md", "# Docs")
    _write(root / "frontend" / "package.json", "{}")
    _write(root / "node_modules" / "ignored" / "index.js", "ignored")
    _write(root / ".git" / "config", "ignored")
    _write(root / ".env", "SECRET=not-read")
    return root


def test_repo_structure_audit_scans_valid_project(tmp_path):
    root = _sample_repo(tmp_path)

    report = run_repo_structure_audit(root_path=str(root))

    assert report["status"] in {"completed", "completed_with_verifier_lite_warning"}
    assert report["task_id"] == "repo_structure_audit"
    assert report["source_inventory"]["root_path"] == str(root.resolve())
    assert report["source_inventory"]["file_contents_read"] is False
    assert report["source_inventory"]["symlinks_followed"] is False
    assert "README.md" in report["source_inventory"]["key_files"]
    assert "pyproject.toml" in report["source_inventory"]["package_config_files"]
    assert report["policy_gate"]["read_only"] is True
    assert report["shell_command_performed"] is False
    assert report["network_call_performed"] is False
    assert report["model_call_performed"] is False
    assert report["mcp_call_performed"] is False


def test_scan_ignores_generated_folders(tmp_path):
    root = _sample_repo(tmp_path)

    report = run_repo_structure_audit(root_path=str(root))

    excluded = report["source_inventory"]["excluded_dirs"]
    assert {"path": ".git", "reason": "ignored_generated_or_heavy_dir"} in excluded
    assert {"path": "node_modules", "reason": "ignored_generated_or_heavy_dir"} in excluded
    included_paths = {item["path"] for item in report["source_inventory"]["included_files"]}
    assert "node_modules/ignored/index.js" not in included_paths


def test_detects_missing_readme_docs_tests_risk_markers(tmp_path):
    root = tmp_path / "minimal"
    _write(root / "src" / "main.py", "print('demo')\n")

    report = run_repo_structure_audit(root_path=str(root))

    marker_ids = {marker["id"] for marker in report["risk_markers"]}
    assert "missing_readme" in marker_ids
    assert "missing_tests_directory" in marker_ids
    assert "missing_docs_directory" in marker_ids
    assert "backend_detected" in marker_ids


def test_refuses_nonexistent_path(tmp_path):
    report = run_repo_structure_audit(root_path=str(tmp_path / "missing"))

    assert report["status"] == "failed"
    assert "root_path_not_found" in report["failure_reasons"]
    assert report["verifier_lite"]["state"] == "error"


def test_refuses_file_path_instead_of_directory(tmp_path):
    file_path = tmp_path / "README.md"
    _write(file_path, "# not a directory")

    report = run_repo_structure_audit(root_path=str(file_path))

    assert report["status"] == "failed"
    assert "root_path_not_directory" in report["failure_reasons"]
    assert report["verifier_lite"]["state"] == "error"


def test_report_shape_and_verifier_lite_pass_on_valid_scan(tmp_path):
    root = _sample_repo(tmp_path)

    report = run_repo_structure_audit(root_path=str(root))

    for field in (
        "report_id",
        "task_id",
        "task_name",
        "status",
        "root_path",
        "started_at",
        "completed_at",
        "duration_ms",
        "context_preflight",
        "policy_gate",
        "source_inventory",
        "findings",
        "risk_markers",
        "memory_candidate_proposals",
        "verifier_lite",
        "warnings",
        "limitations",
        "degraded_state",
    ):
        assert field in report
    assert report["verifier_lite"]["state"] == "pass"
    assert report["verifier_lite"]["checks"]["operation_read_only"] is True
    assert report["report_is_evidence"] is False
    assert report["report_is_verifier"] is False


def test_memory_candidate_proposals_are_candidate_only_and_not_persisted(tmp_path):
    root = _sample_repo(tmp_path)

    report = run_repo_structure_audit(root_path=str(root))

    assert report["memory_write_performed"] is False
    assert report["memory_candidate_persisted"] is False
    assert report["memory_candidate_proposals"]
    assert all(item["status"] == "candidate_only" for item in report["memory_candidate_proposals"])
    assert all(item["persisted"] is False for item in report["memory_candidate_proposals"])
    assert all(item["active_memory"] is False for item in report["memory_candidate_proposals"])


def test_unsupported_task_id_fails_without_scan(tmp_path):
    root = _sample_repo(tmp_path)

    report = run_repo_structure_audit(root_path=str(root), task_id="make_patch")

    assert report["status"] == "failed"
    assert "unsupported_task_id" in report["failure_reasons"]
    assert report["source_inventory"] == {}
