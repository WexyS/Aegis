from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aegis.core.skill_registry import (
    SKILL_REGISTRY_EXECUTION_PERMISSION,
    build_skill_catalog,
    get_skill_manifest,
)


router = APIRouter(prefix="/skills", tags=["skill-registry"])


@router.get("")
async def list_skills() -> dict[str, Any]:
    return build_skill_catalog()


@router.get("/{skill_id}")
async def get_skill(skill_id: str) -> dict[str, Any]:
    manifest = get_skill_manifest(skill_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail={"status": "not_found", "skill_id": skill_id})
    return {
        "status": "found",
        "skill": manifest,
        "skill_execution_allowed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": SKILL_REGISTRY_EXECUTION_PERMISSION,
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
