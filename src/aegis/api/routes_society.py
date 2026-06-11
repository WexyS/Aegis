from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from aegis.api.routes_autopilot import get_report_store
from aegis.core.society import (
    DEFAULT_SOCIETY_NAME,
    SocietySessionStore,
    run_deterministic_society_session,
)


router = APIRouter(prefix="/society", tags=["society"])

_SESSION_STORE = SocietySessionStore()


def get_session_store() -> SocietySessionStore:
    return _SESSION_STORE


@router.post("/run")
async def run_society_session(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    autopilot_report_id = _text(body.get("autopilot_report_id"))
    report_payload = body.get("report_payload")
    report = report_payload if isinstance(report_payload, dict) else None

    if autopilot_report_id:
        report = get_report_store().get(autopilot_report_id)

    session = run_deterministic_society_session(
        autopilot_report=report,
        autopilot_report_id=autopilot_report_id,
        memory_ids=body.get("memory_ids") or (),
        society_name=_text(body.get("society_name")) or DEFAULT_SOCIETY_NAME,
    )

    if session["status"] == "input_missing":
        raise HTTPException(status_code=404, detail=session)

    get_session_store().save(session)
    return session


@router.get("/sessions/{session_id}")
async def get_society_session(session_id: str) -> dict[str, Any]:
    session = get_session_store().get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"status": "not_found", "session_id": session_id})
    return session


@router.get("/sessions")
async def list_society_sessions() -> dict[str, Any]:
    sessions = get_session_store().list()
    return {
        "status": "listed",
        "session_count": len(sessions),
        "sessions": sessions,
        "session_persistence": "process_local_in_memory",
        "runtime_dispatch_allowed": False,
        "execution_permission": "not_granted_by_society_session_rc1",
        "evidence_provided_by_society": False,
        "verifier_success": False,
    }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
