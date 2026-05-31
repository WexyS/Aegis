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
from aegis.core.approval_hygiene import (
    HYGIENE_CONFIRMATION_PHRASE,
    approval_hygiene_resolution_metadata,
    build_approval_hygiene_preview,
    reject_grant_like_payload,
)
from aegis.core.constants import CommandStatus, ExecutionMode
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.maintenance import get_last_maintenance_scan, run_read_only_maintenance_scan
from aegis.core.maintenance_actions import (
    is_maintenance_action_record,
    request_maintenance_action_approval,
)
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
            except Exception as e:
                api_logger.debug("Failed to decode bytes with %s: %s", enc, e)
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
        except Exception:
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

    await ws_bridge.emit_approval_resolved(record, decision="granted")
    await ws_bridge.emit_event(
        ws_bridge.ProtocolEventType.COMMAND_APPROVED,
        {"command": record.to_dict()},
        trace_id=record.trace_id,
        source=ws_bridge.Component.GUARD,
    )

    if record.status != CommandStatus.APPROVED:
        await ws_bridge.emit_command_status(
            command_id=record.command_id,
            status=record.status,
            trace_id=record.trace_id,
            risk_level=record.risk_level,
            reason=record.reason,
            verification_state=record.verification_state,
        )
        return CommandResponse(
            trace_id=record.trace_id or command_id,
            status=record.status,
            intent=str(record.metadata.get("decision_status") or "approval"),
            message=record.reason,
            actions=[],
            warnings=record.warnings,
        )

    if is_maintenance_action_record(record):
        return await ws_bridge.execute_maintenance_action_record(record)

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

        await ws_bridge.emit_approval_resolved(record, decision="denied")
        await ws_bridge.emit_event(
            ws_bridge.ProtocolEventType.COMMAND_REJECTED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=ws_bridge.Component.GUARD,
        )
        return {"command": record.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown command") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/command/approvals/{approval_id}/resolve")
async def resolve_approval(
    approval_id: str,
    body: dict[str, Any] | None = Body(default=None),
) -> dict[str, Any]:
    payload = body or {}
    decision = str(payload.get("decision") or "").strip().lower()
    if decision not in {"grant", "granted", "approve", "approved", "deny", "denied", "reject", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be grant or deny")
    approved = decision in {"grant", "granted", "approve", "approved"}
    try:
        record = get_approval_manager().resolve_approval(
            approval_id,
            approved=approved,
            reason=str(payload.get("reason") or ""),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown approval decision") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    from aegis.api import ws_bridge

    await ws_bridge.emit_approval_resolved(record, decision="granted" if approved else "denied")
    if approved and record.status == CommandStatus.APPROVED:
        await ws_bridge.enqueue_approved_command_for_resume(
            record,
            mode=str(payload.get("mode") or "auto"),
        )
    return {"command": record.to_dict()}


@router.post("/command/approvals/hygiene/preview")
async def preview_approval_hygiene(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    payload = body or {}
    grant_error = reject_grant_like_payload(payload)
    if grant_error:
        raise HTTPException(status_code=400, detail=grant_error)
    approval_ids = payload.get("approval_ids")
    if approval_ids is not None and not isinstance(approval_ids, list):
        raise HTTPException(status_code=400, detail="approval_ids must be a list")
    restored_only = bool(payload.get("restored_only", True))
    include_current_session = bool(payload.get("include_current_session", False))
    return build_approval_hygiene_preview(
        get_approval_manager().snapshot(),
        [str(item) for item in approval_ids] if isinstance(approval_ids, list) else None,
        restored_only=restored_only,
        include_current_session=include_current_session,
    )


@router.post("/command/approvals/hygiene/deny-selected")
async def deny_selected_restored_approvals(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    payload = body or {}
    grant_error = reject_grant_like_payload(payload)
    if grant_error:
        raise HTTPException(status_code=400, detail=grant_error)

    approval_ids = payload.get("approval_ids")
    if not isinstance(approval_ids, list) or not approval_ids:
        raise HTTPException(status_code=400, detail="approval_ids must be a non-empty list")
    normalized_ids = []
    seen_ids: set[str] = set()
    for item in approval_ids:
        approval_id = str(item).strip()
        if not approval_id or approval_id in seen_ids:
            continue
        seen_ids.add(approval_id)
        normalized_ids.append(approval_id)
    if not normalized_ids:
        raise HTTPException(status_code=400, detail="approval_ids must include at least one non-empty id")

    if payload.get("restored_only", True) is not True:
        raise HTTPException(status_code=400, detail="deny-selected hygiene is restored-only")
    if payload.get("include_current_session", False) is True:
        raise HTTPException(status_code=400, detail="current-session approvals are excluded from restored hygiene")
    if str(payload.get("confirmation_phrase") or "") != HYGIENE_CONFIRMATION_PHRASE:
        raise HTTPException(status_code=400, detail="confirmation_phrase must be DENY RESTORED APPROVALS")
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="reason is required")

    manager = get_approval_manager()
    preview = build_approval_hygiene_preview(
        manager.snapshot(),
        normalized_ids,
        restored_only=True,
        include_current_session=False,
    )
    from aegis.api import ws_bridge

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    resolution_metadata = approval_hygiene_resolution_metadata(
        reason=reason,
        selected_count=len(normalized_ids),
        restored_only=True,
        idempotency_key=str(payload.get("idempotency_key") or "").strip() or None,
    )

    for item in preview["items"]:
        approval_id = str(item["approval_id"])
        if item.get("eligible") is not True:
            existing = manager.find_by_approval_id(approval_id)
            if (
                existing is not None
                and existing.status == CommandStatus.REJECTED
                and existing.metadata.get("approval_resolution_status") == "approval_denied"
                and existing.metadata.get("operator_action") == "restored_pending_hygiene_deny"
            ):
                results.append({
                    "approval_id": approval_id,
                    "command_id": existing.command_id,
                    "status": "already_denied",
                    "approval_resolution_status": existing.metadata.get("approval_resolution_status"),
                    "idempotent": True,
                    "command": existing.to_dict(),
                })
                continue
            failures.append({
                "approval_id": approval_id,
                "command_id": item.get("command_id"),
                "reason": item.get("ineligible_reason") or "ineligible",
                "status": item.get("status"),
            })
            continue
        try:
            record = manager.resolve_approval(
                approval_id,
                approved=False,
                reason=reason,
                resolution_metadata=resolution_metadata,
            )
        except KeyError:
            failures.append({"approval_id": approval_id, "reason": "missing_approval_id"})
            continue
        except ValueError as exc:
            failures.append({"approval_id": approval_id, "reason": str(exc)})
            continue

        await ws_bridge.emit_approval_resolved(record, decision="denied")
        await ws_bridge.emit_event(
            ws_bridge.ProtocolEventType.COMMAND_REJECTED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=ws_bridge.Component.GUARD,
        )
        results.append({
            "approval_id": approval_id,
            "command_id": record.command_id,
            "status": record.status.value,
            "approval_resolution_status": record.metadata.get("approval_resolution_status"),
            "not_executed": record.metadata.get("not_executed") is True,
            "command": record.to_dict(),
        })

    return {
        "mutation_performed": bool([item for item in results if item.get("status") == CommandStatus.REJECTED.value]),
        "operator_action": "deny_selected_restored_approvals",
        "requested_count": len(normalized_ids),
        "resolved_count": sum(1 for item in results if item.get("status") == CommandStatus.REJECTED.value),
        "failed_count": len(failures),
        "not_executed": True,
        "approval_grant_exposed": False,
        "restored_only": True,
        "current_session_excluded": True,
        "preview": preview,
        "results": results,
        "failures": failures,
    }


@router.post("/command/clarifications/{clarification_id}/resolve")
async def resolve_clarification(
    clarification_id: str,
    body: dict[str, Any] | None = Body(default=None),
) -> dict[str, Any]:
    payload = body or {}
    try:
        record = get_approval_manager().resolve_clarification(
            clarification_id,
            answer=payload.get("answer"),
            cancelled=bool(payload.get("cancelled", False)),
            reason=str(payload.get("reason") or ""),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clarification decision") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    from aegis.api import ws_bridge

    await ws_bridge.emit_clarification_resolved(record)
    return {"command": record.to_dict()}


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
    from aegis.api import ws_bridge

    return run_read_only_maintenance_scan(**ws_bridge.maintenance_scan_context())


@router.post("/maintenance/action-proposals/{proposal_id}/request")
async def request_maintenance_action(proposal_id: str) -> dict[str, Any]:
    from aegis.api import ws_bridge

    report = get_last_maintenance_scan() or run_read_only_maintenance_scan(**ws_bridge.maintenance_scan_context())
    try:
        record = request_maintenance_action_approval(proposal_id, report=report)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown maintenance action proposal") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    await ws_bridge.emit_approval_required(record.to_dict(), trace_id=record.trace_id)
    refreshed_report = run_read_only_maintenance_scan(**ws_bridge.maintenance_scan_context())
    await ws_bridge.emit_event(
        ws_bridge.ProtocolEventType.MAINTENANCE_SCAN_COMPLETED,
        {"report": refreshed_report, "reason": "maintenance_action_approval_requested"},
        trace_id=record.trace_id,
        source=ws_bridge.Component.SYSTEM,
    )
    return {
        "command": record.to_dict(),
        "proposal": record.metadata.get("proposal"),
        "report": refreshed_report,
    }


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
