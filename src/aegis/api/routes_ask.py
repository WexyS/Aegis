from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from aegis.api import ws_bridge
from aegis.core.agent_runtime import build_agent_profile_catalog
from aegis.core.ask import build_ask_response
from aegis.core.maintenance import run_read_only_maintenance_scan
from aegis.core.model_gateway import build_model_gateway_status
from aegis.core.skill_registry import build_skill_catalog
from aegis.tools.registry import get_tool_registry_snapshot


router = APIRouter(tags=["aegis-ask"])


def get_maintenance_scan_for_ask() -> dict[str, Any]:
    return run_read_only_maintenance_scan(**ws_bridge.maintenance_scan_context())


def get_skill_catalog_for_ask() -> dict[str, Any]:
    return build_skill_catalog()


def get_tool_registry_for_ask() -> dict[str, Any]:
    return get_tool_registry_snapshot()


def get_model_gateway_status_for_ask() -> dict[str, Any]:
    return build_model_gateway_status()


def get_agent_profile_catalog_for_ask() -> dict[str, Any]:
    return build_agent_profile_catalog()


def get_plugin_summary_for_ask() -> dict[str, Any]:
    return {
        "status": "metadata_only",
        "manifest_contract": "available",
        "lifecycle_contract": "available",
        "review_store_contract": "available",
        "plugin_execution_performed": False,
        "dynamic_import_performed": False,
        "runtime_dispatch_allowed": False,
    }


@router.post("/ask")
async def ask_aegis(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"status": "invalid_request", "reason": "request_body_must_be_object"})
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise HTTPException(status_code=400, detail={"status": "invalid_request", "reason": "question_required"})

    try:
        return build_ask_response(
            body,
            maintenance_scan=get_maintenance_scan_for_ask(),
            skill_catalog=get_skill_catalog_for_ask(),
            tool_registry_snapshot=get_tool_registry_for_ask(),
            model_gateway_status=get_model_gateway_status_for_ask(),
            agent_profile_catalog=get_agent_profile_catalog_for_ask(),
            plugin_summary=get_plugin_summary_for_ask(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "invalid_request", "reason": str(exc)}) from exc
