from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from aegis.core.agent_runtime import (
    AGENT_RUNTIME_EXECUTION_PERMISSION,
    AgentSessionStore,
    build_agent_profile_catalog,
    get_agent_profile,
    run_bounded_agent_session,
)


router = APIRouter(prefix="/agents", tags=["agent-runtime"])

_SESSION_STORE = AgentSessionStore()


def get_session_store() -> AgentSessionStore:
    return _SESSION_STORE


@router.get("/profiles")
async def list_agent_profiles() -> dict[str, Any]:
    return build_agent_profile_catalog()


@router.get("/profiles/{agent_id}")
async def get_agent_profile_endpoint(agent_id: str) -> dict[str, Any]:
    profile = get_agent_profile(agent_id)
    if profile is None:
        raise HTTPException(status_code=404, detail={"status": "not_found", "agent_id": agent_id})
    return {
        "status": "found",
        "profile": profile,
        "agent_execution_allowed": False,
        "skill_execution_allowed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": AGENT_RUNTIME_EXECUTION_PERMISSION,
        "authority": False,
        "permission_granted": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "evidence_created": False,
        "verifier_success": False,
        "memory_write_performed": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "network_call_performed": False,
        "external_api_called": False,
        "data_sent_external": False,
    }


@router.post("/sessions")
async def create_agent_session(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    session = run_bounded_agent_session(body)
    if session["status"] in {"failed", "input_missing", "error"}:
        raise HTTPException(status_code=400, detail=session)
    get_session_store().save(session)
    return session


@router.get("/sessions")
async def list_agent_sessions() -> dict[str, Any]:
    sessions = get_session_store().list()
    return {
        "status": "listed",
        "session_count": len(sessions),
        "sessions": sessions,
        "session_persistence": "process_local_in_memory",
        "agent_execution_allowed": False,
        "skill_execution_allowed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": AGENT_RUNTIME_EXECUTION_PERMISSION,
        "authority": False,
        "permission_granted": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "evidence_created": False,
        "verifier_success": False,
    }


@router.get("/sessions/{session_id}")
async def get_agent_session(session_id: str) -> dict[str, Any]:
    session = get_session_store().get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"status": "not_found", "session_id": session_id})
    return session
