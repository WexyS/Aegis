from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from aegis.core.model_gateway import (
    ModelGatewayTransport,
    build_model_gateway_status,
    complete_model_gateway,
    probe_model_gateway,
)


router = APIRouter(prefix="/model-gateway", tags=["model-gateway"])

_MODEL_GATEWAY_TRANSPORT: ModelGatewayTransport | None = None


def set_model_gateway_transport_for_tests(transport: ModelGatewayTransport | None) -> None:
    global _MODEL_GATEWAY_TRANSPORT
    _MODEL_GATEWAY_TRANSPORT = transport


@router.get("/status")
async def model_gateway_status() -> dict[str, Any]:
    return build_model_gateway_status()


@router.post("/probe")
async def model_gateway_probe() -> dict[str, Any]:
    return await probe_model_gateway(transport=_MODEL_GATEWAY_TRANSPORT)


@router.post("/complete")
async def model_gateway_complete(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return await complete_model_gateway(body, transport=_MODEL_GATEWAY_TRANSPORT)
