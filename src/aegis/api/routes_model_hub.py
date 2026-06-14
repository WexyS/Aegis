from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from aegis.core.model_hub import build_model_hub_status


router = APIRouter(prefix="/model-hub", tags=["model-hub"])


@router.get("/status")
async def model_hub_status() -> dict[str, Any]:
    return build_model_hub_status()
