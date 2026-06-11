from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from aegis.memory.store import MemoryOperationResult, MemoryStore


router = APIRouter(prefix="/memory", tags=["memory"])


def get_memory_store() -> MemoryStore:
    return MemoryStore()


def _result_or_error(result: MemoryOperationResult) -> dict[str, Any]:
    payload = result.to_dict()
    if result.ok:
        return payload
    status_code = 400
    if result.status == "not_found":
        status_code = 404
    elif result.status == "blocked_by_invalid_transition":
        status_code = 409
    raise HTTPException(status_code=status_code, detail=payload)


@router.post("/propose")
async def propose_memory(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return _result_or_error(get_memory_store().propose(body))


@router.post("/{memory_id}/approve")
async def approve_memory(memory_id: str) -> dict[str, Any]:
    return _result_or_error(get_memory_store().approve(memory_id))


@router.post("/{memory_id}/reject")
async def reject_memory(memory_id: str, body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    reason = str((body or {}).get("reason") or "").strip() or None
    return _result_or_error(get_memory_store().reject(memory_id, reason=reason))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str) -> dict[str, Any]:
    return _result_or_error(get_memory_store().delete(memory_id))


@router.get("")
async def list_memory(
    status: str | None = None,
    scope: str | None = None,
    sensitivity: str | None = None,
    project_ref: str | None = None,
    repository_ref: str | None = None,
    session_ref: str | None = None,
    include_deleted: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    result = get_memory_store().list_memories(
        status=status,
        scope=scope,
        sensitivity=sensitivity,
        project_ref=project_ref,
        repository_ref=repository_ref,
        session_ref=session_ref,
        include_deleted=include_deleted,
        limit=limit,
    )
    return result.to_dict()


@router.get("/search")
async def search_memory(
    keyword: str | None = None,
    scope: str | None = None,
    sensitivity: str | None = None,
    project_ref: str | None = None,
    repository_ref: str | None = None,
    session_ref: str | None = None,
    status: str | None = None,
    include_sensitive: bool = False,
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    result = get_memory_store().search(
        keyword=keyword,
        scope=scope,
        sensitivity=sensitivity,
        project_ref=project_ref,
        repository_ref=repository_ref,
        session_ref=session_ref,
        status=status,
        include_sensitive=include_sensitive,
        limit=limit,
    )
    return result.to_dict()
