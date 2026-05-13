"""
AEGIS API — POST /command endpoint.

Thin HTTP layer. All logic lives in the orchestrator.
"""

from __future__ import annotations
import logging
import re
from typing import Any
from fastapi import APIRouter, Request, Body, HTTPException
from aegis.core.schemas import CommandResponse, CommandRequest
from aegis.core.app_map import get_app_registry_snapshot, refresh_installed_app_registry
from aegis.core.commands import get_approval_manager
from aegis.core.constants import CommandStatus, ExecutionMode
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.maintenance import run_read_only_maintenance_scan
from aegis.orchestrator.orchestrator import get_orchestrator
from aegis.tools.registry import get_tool_registry_snapshot

router = APIRouter()
api_logger = logging.getLogger(__name__)

def clean_text(data: Any) -> str:
    """Bulletproof input cleaning: Handles bytes, stringified bytes, and multiple encodings."""
    if data is None: return ""
    
    # 1. Handle actual bytes with fallback encodings
    if isinstance(data, bytes):
        for enc in ["utf-8", "latin-1", "cp1254"]:
            try:
                return data.decode(enc).strip()
            except:
                continue
        return str(data)

    text = str(data).strip()
    
    # 2. Handle stringified bytes "b'...' " or "b\"...\" "
    if text.startswith("b'") or text.startswith('b"'):
        import ast
        try:
            evaluated = ast.literal_eval(text)
            if isinstance(evaluated, bytes):
                return clean_text(evaluated)
        except:
            # Fallback manual strip if ast fails
            text = text[2:-1]

    # 3. Handle double-escapes and unicode literals (\xe7 -> ç)
    escape_pattern = r"\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}"
    if re.search(escape_pattern, text):
        try:
            decoded = text.encode("latin-1", errors="backslashreplace").decode("unicode_escape")
            try:
                text = decoded.encode("latin-1").decode("utf-8")
            except UnicodeError:
                text = decoded
        except UnicodeError:
            pass
        
    return text.strip()


@router.post("/command", response_model=CommandResponse)
async def handle_command(
    request: Request,
    # Any to allow flexible input but keep UI
    body: Any = Body(
        ...,
        description="Komut metni (string) veya JSON objesi {'text': '...'}",
        openapi_examples={
            "raw_text": {"summary": "Raw Text Örneği", "value": "not defterini aç ve merhaba yaz"},
            "json_format": {"summary": "JSON Örneği", "value": {"text": "chrome aç"}}
        }
    )
) -> CommandResponse:
    """Process a user command through the full pipeline.
    
    Supports:
    - JSON: {"text": "..."}
    - Raw: "..." (plain text)
    """
    # 1. ARINDIRMA (CLEAN): Kapıdaki ilk ve en önemli filtre
    if isinstance(body, dict):
        raw_val = body.get("text", "")
        text = clean_text(raw_val)
        context = dict(body.get("context", {}) or {})
        mode_value = body.get("mode", ExecutionMode.AUTO.value)
    else:
        # Body might be the raw bytes from request if Body(None) was used, 
        # or it might be the parsed Any from FastAPI.
        text = clean_text(body)
        context = {}
        mode_value = ExecutionMode.AUTO.value

    if not text:
        raise HTTPException(status_code=400, detail="Empty command body")

    api_logger.info("[API] Received clean text: %r", text)
    try:
        mode = ExecutionMode(mode_value)
    except Exception:
        mode = ExecutionMode.AUTO
    cmd_req = CommandRequest(text=text, mode=mode, context=context)

    # 2. Process
    try:
        orchestrator = get_orchestrator()
        return await orchestrator.process(cmd_req)
    except Exception as e:
        import traceback
        api_logger.error("🔥 PIPELINE CRASH: %s", str(e))
        traceback.print_exc()
        from uuid import uuid4
        return CommandResponse(
            trace_id=str(uuid4()),
            status=CommandStatus.ERROR,
            intent="error",
            message=f"Critical Error: {str(e)}",
            actions=[],
            warnings=[str(e)]
        )


@router.post("/command/{command_id}/approve", response_model=CommandResponse)
async def approve_command(command_id: str) -> CommandResponse:
    manager = get_approval_manager()
    try:
        record = manager.approve(command_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown command") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    from aegis.api import ws_bridge

    await ws_bridge.emit_event(
        ws_bridge.ProtocolEventType.COMMAND_APPROVED,
        {"command": record.to_dict()},
        trace_id=record.trace_id,
        source=ws_bridge.Component.GUARD,
    )

    token = manager.token_for(command_id)
    request = CommandRequest(
        text=record.text,
        mode=ExecutionMode.LIVE,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": token,
        },
    )
    return await get_orchestrator().process(request)


@router.post("/command/{command_id}/reject")
async def reject_command(command_id: str, body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    try:
        reason = str((body or {}).get("reason") or "rejected by user")
        record = get_approval_manager().reject(command_id, reason=reason)
        from aegis.api import ws_bridge

        await ws_bridge.emit_event(
            ws_bridge.ProtocolEventType.COMMAND_REJECTED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=ws_bridge.Component.GUARD,
        )
        return {"command": record.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown command") from None


@router.post("/command/{command_id}/cancel")
async def cancel_command(command_id: str, body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    try:
        reason = str((body or {}).get("reason") or "cancelled by user")
        record = get_approval_manager().cancel(command_id, reason=reason)
        from aegis.api import ws_bridge

        await ws_bridge.emit_event(
            ws_bridge.ProtocolEventType.COMMAND_CANCELLED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=ws_bridge.Component.SYSTEM,
            severity=ws_bridge.Severity.WARNING,
        )
        return {"command": record.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown command") from None


@router.get("/maintenance/scan")
async def maintenance_scan() -> dict[str, Any]:
    return run_read_only_maintenance_scan()


@router.get("/environment/diagnostics")
async def environment_diagnostics() -> dict[str, Any]:
    return collect_environment_diagnostics()


@router.get("/apps/registry")
async def app_registry(refresh: bool = False) -> dict[str, Any]:
    report = refresh_installed_app_registry() if refresh else get_app_registry_snapshot()
    report["read_only"] = True
    return report


@router.get("/tools/registry")
async def tool_registry() -> dict[str, Any]:
    return get_tool_registry_snapshot()
