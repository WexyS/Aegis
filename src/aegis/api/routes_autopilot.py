from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from aegis.core.autopilot import AutoPilotReportStore, run_repo_structure_audit


router = APIRouter(prefix="/autopilot", tags=["autopilot"])

_REPORT_STORE = AutoPilotReportStore()


def get_report_store() -> AutoPilotReportStore:
    return _REPORT_STORE


@router.post("/run")
async def run_autopilot(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    task_id = str(body.get("task_id") or "repo_structure_audit")
    root_path = str(body.get("root_path") or "")
    report = run_repo_structure_audit(
        root_path=root_path,
        task_id=task_id,
        include_dirs=body.get("include_dirs"),
        exclude_dirs=body.get("exclude_dirs"),
    )
    get_report_store().save(report)
    status_code = 200 if report["status"] not in {"failed"} else 400
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=report)
    return report


@router.get("/reports/{report_id}")
async def get_autopilot_report(report_id: str) -> dict[str, Any]:
    report = get_report_store().get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail={"status": "not_found", "report_id": report_id})
    return report


@router.get("/reports")
async def list_autopilot_reports() -> dict[str, Any]:
    reports = get_report_store().list()
    return {
        "status": "listed",
        "report_count": len(reports),
        "reports": reports,
        "report_persistence": "process_local_in_memory",
        "runtime_dispatch_allowed": False,
        "execution_permission": "not_granted_by_autopilot_rc1",
        "evidence_provided_by_report": False,
        "verifier_success": False,
    }
