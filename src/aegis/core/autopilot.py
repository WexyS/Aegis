from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


AUTOPILOT_RC1_VERSION = "autopilot-rc1-core/1"
AUTOPILOT_EXECUTION_PERMISSION = "not_granted_by_autopilot_rc1"
SUPPORTED_TASK_ID = "repo_structure_audit"

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

KEY_FILE_NAMES = {
    "readme.md",
    "readme",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "poetry.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "next.config.js",
    "vite.config.ts",
    "dockerfile",
    "docker-compose.yml",
    ".env",
    ".env.example",
    ".gitignore",
    "pytest.ini",
    "tox.ini",
    "vitest.config.ts",
    "jest.config.js",
    "playwright.config.ts",
}

PACKAGE_CONFIG_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
}

TEST_CONFIG_NAMES = {
    "pytest.ini",
    "tox.ini",
    "vitest.config.ts",
    "jest.config.js",
    "playwright.config.ts",
}

ENV_LIKE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
}

LARGE_FILE_BYTES = 2_000_000
MAX_FILES = 10_000


@dataclass(frozen=True)
class ScanValidation:
    ok: bool
    status: str
    root_path: str | None = None
    failure_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class AutoPilotReportStore:
    """Process-local report store for RC1.

    This is intentionally not durable. It avoids writing generated report files
    while allowing API retrieval in the same backend process.
    """

    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}

    def save(self, report: Mapping[str, Any]) -> None:
        self._reports[str(report["report_id"])] = dict(report)

    def get(self, report_id: str) -> dict[str, Any] | None:
        report = self._reports.get(report_id)
        return dict(report) if report is not None else None

    def list(self) -> list[dict[str, Any]]:
        return sorted(
            (dict(report) for report in self._reports.values()),
            key=lambda item: str(item.get("started_at") or ""),
            reverse=True,
        )


def run_repo_structure_audit(
    *,
    root_path: str,
    task_id: str = SUPPORTED_TASK_ID,
    include_dirs: tuple[str, ...] | list[str] | None = None,
    exclude_dirs: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    started = _now()
    report_id = f"autopilot_{uuid4().hex}"
    task_id = str(task_id or SUPPORTED_TASK_ID)
    if task_id != SUPPORTED_TASK_ID:
        completed = _now()
        return _failure_report(
            report_id=report_id,
            task_id=task_id,
            root_path=root_path,
            started_at=started,
            completed_at=completed,
            status="failed",
            failure_reasons=("unsupported_task_id",),
        )

    validation = validate_scan_root(root_path)
    if not validation.ok:
        completed = _now()
        report = _failure_report(
            report_id=report_id,
            task_id=task_id,
            root_path=root_path,
            started_at=started,
            completed_at=completed,
            status="failed",
            failure_reasons=validation.failure_reasons,
            warnings=validation.warnings,
        )
        report["verifier_lite"] = _verifier_lite(report)
        return report

    ignored_dirs = set(DEFAULT_IGNORED_DIRS)
    ignored_dirs.update(str(item) for item in (exclude_dirs or ()) if str(item).strip())
    if include_dirs:
        ignored_dirs.difference_update(str(item) for item in include_dirs if str(item).strip())

    inventory = _scan_directory(Path(validation.root_path or root_path), ignored_dirs=ignored_dirs)
    completed = _now()
    findings = _build_findings(inventory)
    risk_markers = _risk_markers(inventory)
    report = _base_report(
        report_id=report_id,
        task_id=task_id,
        root_path=str(validation.root_path),
        started_at=started,
        completed_at=completed,
        status="completed",
    )
    report.update(
        {
            "source_inventory": inventory,
            "findings": findings,
            "risk_markers": risk_markers,
            "memory_candidate_proposals": _memory_candidate_proposals(inventory, risk_markers),
            "warnings": tuple(dict.fromkeys((*validation.warnings, *inventory["warnings"]))),
            "limitations": _limitations(),
            "degraded_state": _degraded_state(inventory, risk_markers),
        }
    )
    report["verifier_lite"] = _verifier_lite(report)
    if report["verifier_lite"]["state"] != "pass":
        report["status"] = "completed_with_verifier_lite_warning"
    return report


def validate_scan_root(root_path: str) -> ScanValidation:
    if not str(root_path or "").strip():
        return ScanValidation(ok=False, status="invalid", failure_reasons=("missing_root_path",))
    if "\x00" in str(root_path):
        return ScanValidation(ok=False, status="invalid", failure_reasons=("invalid_root_path",))

    try:
        raw = Path(root_path).expanduser()
    except RuntimeError:
        return ScanValidation(ok=False, status="invalid", failure_reasons=("invalid_root_path",))

    if str(root_path).startswith("~"):
        return ScanValidation(ok=False, status="invalid", failure_reasons=("home_relative_path_refused",))

    try:
        resolved = raw.resolve(strict=True)
    except FileNotFoundError:
        return ScanValidation(ok=False, status="invalid", failure_reasons=("root_path_not_found",))
    except OSError:
        return ScanValidation(ok=False, status="invalid", failure_reasons=("root_path_not_accessible",))

    if not resolved.is_dir():
        return ScanValidation(ok=False, status="invalid", failure_reasons=("root_path_not_directory",))
    if _is_drive_or_filesystem_root(resolved):
        return ScanValidation(ok=False, status="invalid", failure_reasons=("root_path_too_broad",))
    if resolved.is_symlink():
        return ScanValidation(ok=False, status="invalid", failure_reasons=("root_path_symlink_refused",))

    return ScanValidation(ok=True, status="valid", root_path=str(resolved))


def _scan_directory(root: Path, *, ignored_dirs: set[str]) -> dict[str, Any]:
    total_files = 0
    total_dirs = 0
    included_files: list[dict[str, Any]] = []
    excluded_dirs: list[dict[str, Any]] = []
    excluded_files: list[dict[str, Any]] = []
    extensions: Counter[str] = Counter()
    key_files: list[str] = []
    package_config_files: list[str] = []
    docs_paths: list[str] = []
    tests_paths: list[str] = []
    frontend_indicators: set[str] = set()
    backend_indicators: set[str] = set()
    warnings: list[str] = []

    stack = [root]
    stopped_by_limit = False
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda path: path.name.lower())
        except OSError:
            excluded_dirs.append({"path": _rel(current, root), "reason": "directory_not_accessible"})
            continue

        for entry in entries:
            rel = _rel(entry, root)
            name_lower = entry.name.lower()
            try:
                if entry.is_symlink():
                    if entry.is_dir():
                        excluded_dirs.append({"path": rel, "reason": "symlink_not_followed"})
                    else:
                        excluded_files.append({"path": rel, "reason": "symlink_not_followed"})
                    continue
                if entry.is_dir():
                    total_dirs += 1
                    if entry.name in ignored_dirs or name_lower in ignored_dirs:
                        excluded_dirs.append({"path": rel, "reason": "ignored_generated_or_heavy_dir"})
                        continue
                    _classify_dir(rel, name_lower, docs_paths, tests_paths, frontend_indicators, backend_indicators)
                    stack.append(entry)
                    continue
                if not entry.is_file():
                    excluded_files.append({"path": rel, "reason": "not_regular_file"})
                    continue
                total_files += 1
                stat = entry.stat()
            except OSError:
                excluded_files.append({"path": rel, "reason": "file_not_accessible"})
                continue

            if stat.st_size > LARGE_FILE_BYTES:
                excluded_files.append(
                    {"path": rel, "reason": "large_file_metadata_only", "size_bytes": stat.st_size}
                )
                continue
            if total_files > MAX_FILES:
                stopped_by_limit = True
                excluded_files.append({"path": rel, "reason": "scan_file_limit_reached"})
                continue

            extension = entry.suffix.lower() or "[no_extension]"
            extensions[extension] += 1
            file_record = {
                "path": rel,
                "extension": extension,
                "size_bytes": stat.st_size,
                "modified_at": int(stat.st_mtime),
            }
            included_files.append(file_record)
            _classify_file(
                rel,
                name_lower,
                key_files,
                package_config_files,
                docs_paths,
                tests_paths,
                frontend_indicators,
                backend_indicators,
            )
            if name_lower in ENV_LIKE_NAMES or name_lower.endswith(".key"):
                warnings.append("env_or_key_like_file_detected_metadata_only")

    if stopped_by_limit:
        warnings.append("scan_file_limit_reached")

    return {
        "root_path": str(root),
        "scanned_at": _now_iso(),
        "total_files": total_files,
        "total_dirs": total_dirs,
        "included_file_count": len(included_files),
        "included_files": included_files,
        "excluded_dirs": excluded_dirs,
        "excluded_files": excluded_files,
        "file_extensions": dict(sorted(extensions.items())),
        "key_files": sorted(set(key_files)),
        "package_config_files": sorted(set(package_config_files)),
        "docs_paths": sorted(set(docs_paths)),
        "tests_paths": sorted(set(tests_paths)),
        "frontend_indicators": sorted(frontend_indicators),
        "backend_indicators": sorted(backend_indicators),
        "warnings": tuple(dict.fromkeys(warnings)),
        "limitations": _inventory_limitations(),
        "file_contents_read": False,
        "symlinks_followed": False,
    }


def _build_findings(inventory: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    findings = []
    if inventory.get("key_files"):
        findings.append(
            {
                "id": "key_files_detected",
                "severity": "info",
                "title": "Key project files detected",
                "details": tuple(inventory["key_files"]),
            }
        )
    if inventory.get("frontend_indicators"):
        findings.append(
            {
                "id": "frontend_indicators_detected",
                "severity": "info",
                "title": "Frontend indicators detected",
                "details": tuple(inventory["frontend_indicators"]),
            }
        )
    if inventory.get("backend_indicators"):
        findings.append(
            {
                "id": "backend_indicators_detected",
                "severity": "info",
                "title": "Backend indicators detected",
                "details": tuple(inventory["backend_indicators"]),
            }
        )
    return tuple(findings)


def _risk_markers(inventory: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    markers = []
    key_files = set(inventory.get("key_files") or ())
    docs_paths = tuple(inventory.get("docs_paths") or ())
    tests_paths = tuple(inventory.get("tests_paths") or ())
    package_files = tuple(inventory.get("package_config_files") or ())
    frontend = tuple(inventory.get("frontend_indicators") or ())
    backend = tuple(inventory.get("backend_indicators") or ())

    if not any(path.lower().startswith("readme") for path in key_files):
        markers.append(_marker("missing_readme", "warning", "No README file detected."))
    if not tests_paths:
        markers.append(_marker("missing_tests_directory", "warning", "No obvious tests directory detected."))
    if not docs_paths:
        markers.append(_marker("missing_docs_directory", "info", "No obvious docs directory detected."))
    if package_files:
        markers.append(_marker("dependency_files_present", "info", "Package/dependency files detected."))
    if any("env_or_key_like" in item for item in inventory.get("warnings") or ()):
        markers.append(_marker("env_like_file_detected", "warning", "Env/key-like file detected; content not read."))
    if inventory.get("excluded_files"):
        if any(item.get("reason") == "large_file_metadata_only" for item in inventory["excluded_files"]):
            markers.append(_marker("large_files_skipped", "info", "Large files skipped as metadata-only."))
    if inventory.get("excluded_dirs"):
        markers.append(_marker("generated_folders_skipped", "info", "Ignored/generated folders were skipped."))
    if frontend:
        markers.append(_marker("frontend_detected", "info", "Frontend indicators detected."))
    if backend:
        markers.append(_marker("backend_detected", "info", "Backend indicators detected."))
    if not frontend and not backend:
        markers.append(_marker("unknown_project_type", "info", "No obvious frontend/backend indicators detected."))
    if not _has_test_config(key_files):
        markers.append(_marker("no_obvious_test_config", "info", "No obvious test config detected."))
    return tuple(markers)


def _verifier_lite(report: Mapping[str, Any]) -> dict[str, Any]:
    checks = {
        "scan_completed_without_mutation": bool(report.get("mutation_performed") is False),
        "root_path_validated": bool(report.get("root_path") and report.get("status") != "failed"),
        "counts_coherent": _counts_coherent(report.get("source_inventory") or {}),
        "excluded_dirs_recorded": isinstance((report.get("source_inventory") or {}).get("excluded_dirs", ()), list),
        "required_fields_present": all(
            key in report
            for key in (
                "report_id",
                "task_id",
                "task_name",
                "status",
                "root_path",
                "context_preflight",
                "policy_gate",
                "source_inventory",
                "findings",
                "risk_markers",
                "memory_candidate_proposals",
            )
        ),
        "no_shell_network_model_mcp_used": not any(
            bool(report.get(field))
            for field in (
                "shell_command_performed",
                "network_call_performed",
                "model_call_performed",
                "mcp_call_performed",
            )
        ),
        "operation_read_only": report.get("policy_gate", {}).get("read_only") is True,
    }
    if report.get("status") == "failed":
        state = "error"
    elif all(checks.values()):
        state = "pass"
    elif any(value is False for value in checks.values()):
        state = "fail"
    else:
        state = "inconclusive"
    return {
        "state": state,
        "checks": checks,
        "limitations": (
            "verifier_lite_is_not_evidence",
            "verifier_lite_does_not_certify_findings",
            "verifier_lite_does_not_grant_execution_permission",
        ),
    }


def _base_report(
    *,
    report_id: str,
    task_id: str,
    root_path: str,
    started_at: int,
    completed_at: int,
    status: str,
) -> dict[str, Any]:
    return {
        "autopilot_version": AUTOPILOT_RC1_VERSION,
        "report_id": report_id,
        "task_id": task_id,
        "task_name": SUPPORTED_TASK_ID,
        "status": status,
        "root_path": root_path,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": max(0, int((completed_at - started_at) * 1000)),
        "context_preflight": _context_preflight(),
        "policy_gate": _policy_gate(),
        "source_inventory": {},
        "findings": (),
        "risk_markers": (),
        "memory_candidate_proposals": (),
        "verifier_lite": {"state": "inconclusive", "checks": {}},
        "warnings": (),
        "limitations": _limitations(),
        "degraded_state": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": AUTOPILOT_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_provided_by_report": False,
        "verifier_success": False,
        "mutation_performed": False,
        "frontend_authority": False,
        "shell_command_performed": False,
        "network_call_performed": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "memory_write_performed": False,
        "memory_candidate_persisted": False,
        "context_package_created": False,
        "source_inventory_is_proof": False,
        "report_is_evidence": False,
        "report_is_verifier": False,
    }


def _failure_report(
    *,
    report_id: str,
    task_id: str,
    root_path: str,
    started_at: int,
    completed_at: int,
    status: str,
    failure_reasons: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> dict[str, Any]:
    report = _base_report(
        report_id=report_id,
        task_id=task_id,
        root_path=root_path,
        started_at=started_at,
        completed_at=completed_at,
        status=status,
    )
    report.update(
        {
            "failure_reasons": failure_reasons,
            "warnings": warnings,
            "degraded_state": True,
        }
    )
    return report


def _memory_candidate_proposals(
    inventory: Mapping[str, Any],
    risk_markers: tuple[Mapping[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    stack_bits = []
    if inventory.get("frontend_indicators"):
        stack_bits.append("frontend indicators: " + ", ".join(inventory["frontend_indicators"]))
    if inventory.get("backend_indicators"):
        stack_bits.append("backend indicators: " + ", ".join(inventory["backend_indicators"]))
    risk_ids = ", ".join(marker["id"] for marker in risk_markers) or "no deterministic risk markers"
    return (
        {
            "type": "repo_memory",
            "content": (
                f"Repo structure audit saw {inventory.get('included_file_count', 0)} included files, "
                f"{inventory.get('total_dirs', 0)} directories, and risk markers: {risk_ids}."
            ),
            "scope_suggestion": "repository",
            "sensitivity_suggestion": "private",
            "source_ref": "autopilot_rc1_repo_structure_audit",
            "rationale": "Useful project structure summary for later explicit Memory OS proposal.",
            "status": "candidate_only",
            "persisted": False,
            "active_memory": False,
        },
        {
            "type": "project_preference",
            "content": "AutoPilot RC1 should keep repo audit output read-only and candidate-only.",
            "scope_suggestion": "project",
            "sensitivity_suggestion": "internal",
            "source_ref": "autopilot_rc1_policy_gate",
            "rationale": "Preserves S2 safety boundary for future Mission Control display.",
            "status": "candidate_only",
            "persisted": False,
            "active_memory": False,
        },
        {
            "type": "repo_memory",
            "content": "Detected stack summary: " + ("; ".join(stack_bits) if stack_bits else "unknown stack"),
            "scope_suggestion": "repository",
            "sensitivity_suggestion": "private",
            "source_ref": "autopilot_rc1_source_inventory",
            "rationale": "Stack hints may help later deterministic Society Session planning.",
            "status": "candidate_only",
            "persisted": False,
            "active_memory": False,
        },
    )


def _context_preflight() -> dict[str, Any]:
    return {
        "context_policy_status": "rc1_explicit_preflight_only",
        "local_repo_read_only_context": True,
        "model_provider_required": False,
        "network_context_allowed": False,
        "mcp_or_tool_context_allowed": False,
        "memory_consumed": False,
        "context_package_created": False,
        "context_grants_execution_permission": False,
        "limitations": (
            "full_context_policy_integration_future_gated",
            "no_provider_token_budget_enforcement_in_s2",
        ),
    }


def _policy_gate() -> dict[str, Any]:
    return {
        "mutation_allowed": False,
        "shell_allowed": False,
        "network_allowed": False,
        "model_allowed": False,
        "mcp_allowed": False,
        "tool_allowed": False,
        "memory_write_allowed": False,
        "read_only": True,
    }


def _degraded_state(inventory: Mapping[str, Any], risk_markers: tuple[Mapping[str, Any], ...]) -> bool:
    return bool(inventory.get("warnings")) or any(marker["severity"] == "warning" for marker in risk_markers)


def _counts_coherent(inventory: Mapping[str, Any]) -> bool:
    if not inventory:
        return False
    return int(inventory.get("total_files") or 0) >= int(inventory.get("included_file_count") or 0)


def _classify_dir(
    rel: str,
    name_lower: str,
    docs_paths: list[str],
    tests_paths: list[str],
    frontend_indicators: set[str],
    backend_indicators: set[str],
) -> None:
    if name_lower in {"docs", "doc", "documentation"}:
        docs_paths.append(rel)
    if name_lower in {"test", "tests", "__tests__", "spec"}:
        tests_paths.append(rel)
    if name_lower in {"frontend", "ui", "web", "app"}:
        frontend_indicators.add(rel)
    if name_lower in {"backend", "server", "api", "src"}:
        backend_indicators.add(rel)


def _classify_file(
    rel: str,
    name_lower: str,
    key_files: list[str],
    package_config_files: list[str],
    docs_paths: list[str],
    tests_paths: list[str],
    frontend_indicators: set[str],
    backend_indicators: set[str],
) -> None:
    if name_lower in KEY_FILE_NAMES:
        key_files.append(rel)
    if name_lower in PACKAGE_CONFIG_NAMES:
        package_config_files.append(rel)
    if name_lower.endswith(".md") and (rel.lower().startswith("docs/") or name_lower.startswith("readme")):
        docs_paths.append(rel)
    if "test" in rel.lower() or "spec" in rel.lower():
        tests_paths.append(rel)
    if name_lower in {"package.json", "next.config.js", "vite.config.ts", "tsconfig.json"}:
        frontend_indicators.add(name_lower)
    if name_lower in {"pyproject.toml", "requirements.txt", "go.mod", "cargo.toml"}:
        backend_indicators.add(name_lower)


def _has_test_config(key_files: set[str]) -> bool:
    lowered = {item.lower().split("/")[-1] for item in key_files}
    return bool(lowered.intersection(TEST_CONFIG_NAMES))


def _marker(marker_id: str, severity: str, message: str) -> dict[str, str]:
    return {"id": marker_id, "severity": severity, "message": message}


def _is_drive_or_filesystem_root(path: Path) -> bool:
    anchor = Path(path.anchor) if path.anchor else None
    return (anchor is not None and path == anchor) or path.parent == path


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix() or "."
    except ValueError:
        return str(path)


def _now() -> int:
    return int(time.time())


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _limitations() -> tuple[str, ...]:
    return (
        "autopilot_rc1_core_only",
        "report_is_not_evidence",
        "report_is_not_full_verifier",
        "source_inventory_is_not_proof",
        "no_file_content_reading",
        "no_shell_network_model_mcp_or_tool_calls",
        "memory_candidates_not_persisted",
    )


def _inventory_limitations() -> tuple[str, ...]:
    return (
        "metadata_only_file_inventory",
        "file_contents_not_read",
        "large_files_skipped_metadata_only",
        "symlinks_not_followed",
        "generated_and_dependency_dirs_skipped",
    )
