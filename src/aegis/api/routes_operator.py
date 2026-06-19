from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from aegis.core.operator_auto_router import build_operator_route_preview


router = APIRouter(prefix="/operator", tags=["operator"])


@router.post("/preview-route")
async def preview_operator_route(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(
            status_code=400,
            detail={"status": "invalid_request", "reason": "request_body_must_be_object"},
        )
    request = body.get("request")
    if not isinstance(request, str) or not request.strip():
        raise HTTPException(
            status_code=400,
            detail={"status": "invalid_request", "reason": "request_required"},
        )
    return build_operator_route_preview(request)
