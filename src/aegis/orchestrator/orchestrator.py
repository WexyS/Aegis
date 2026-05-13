# src/aegis/orchestrator/orchestrator.py

import time
import json
import logging
from typing import List, Optional, Set, Dict, Any
from uuid import UUID
from datetime import datetime

from aegis.core.commands import CancellationToken, get_approval_manager
from aegis.core.constants import ActionStatus, CommandStatus, EventType, ExecutionMode, RiskLevel
from aegis.core.schemas import (
    ActionResult,
    CommandRequest,
    CommandResponse,
    IntentResult,
)
from aegis.core.config import get_settings
from aegis.core.context import ExecutionContext
from aegis.logger.event_logger import get_event_logger
from aegis.core.state_manager import get_state_manager
from aegis.intent.parser import get_parser
from aegis.orchestrator.planner import get_planner
from aegis.orchestrator.router import get_router
from aegis.replay.golden_journal import get_journal
from aegis.executor.semantic_verifier import get_semantic_verifier
from aegis.guard.action_guard import get_guard
from aegis.executor.deterministic_executor import get_deterministic_executor
from aegis.executor.utils import verify_path
from aegis.api import ws_bridge
from aegis.tools.registry import get_tool_spec, list_tools

logger = logging.getLogger(__name__)

RISK_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
VERIFIED_TOOLS = {
    "read_file",
    "list_directory",
    "search_files",
    "grep_in_files",
    "file_info",
    "write_file",
    "create_file",
    "edit_file",
    "read_page",
    "scroll",
    "search_web",
    "open_url",
    "click",
    "type",
    "open_app",
    "focus_app",
    "close_app",
    "run_command",
    "git_action",
    "general_chat",
}
SIDE_EFFECTING_TOOLS = {"click", "type", "write_file", "create_file", "edit_file", "git_action", "open_url", "open_app", "close_app", "focus_app"}
SIDE_EFFECT_PROOF_KEYS = {
    "browser_evidence",
    "execution_evidence",
    "git_evidence",
    "shell_evidence",
    "type_evidence",
    "write_evidence",
}


def _highest_risk_from_guards(guard_events: list[Dict[str, Any]]) -> RiskLevel:
    highest = max(
        (str(g.get("risk", "none")) for g in guard_events),
        default="none",
        key=lambda value: RISK_RANK.get(value, 0),
    )
    return RiskLevel(highest) if highest in RiskLevel._value2member_map_ else RiskLevel.NONE


def _verification_state_for_plan(plan: list[IntentResult]) -> str:
    if not plan:
        return "verified"
    return "verified" if all(intent.intent in VERIFIED_TOOLS for intent in plan) else "unverified"


def _unverified_side_effects(plan: list[IntentResult]) -> list[str]:
    unverified = []
    for intent in plan:
        spec = get_tool_spec(intent.intent)
        side_effecting = bool(spec.side_effecting) if spec else intent.intent in SIDE_EFFECTING_TOOLS
        if side_effecting and intent.intent not in VERIFIED_TOOLS:
            unverified.append(intent.intent)
    return unverified


def _has_side_effect_proof(action: ActionResult) -> bool:
    if action.execution_evidence:
        return action.execution_evidence.verification_state == "verified"
    return any(key in action.proof for key in SIDE_EFFECT_PROOF_KEYS)


def _completion_verification_state(
    actions: list[ActionResult],
    final_status: CommandStatus,
    avg_determinism: float,
) -> str:
    if final_status != CommandStatus.EXECUTED:
        return "unverified"
    for action in actions:
        evidence = action.execution_evidence
        if evidence and evidence.verification_state != "verified":
            return "unverified"
        if action.action in SIDE_EFFECTING_TOOLS and not _has_side_effect_proof(action):
            return "unverified"
    return "verified" if avg_determinism >= 0.5 else "unverified"


class PlanSimulator:
    """
    AEGIS Tier 4 Plan Simulator.
    Validates the plan's feasibility before a single side-effect is triggered.
    """
    def __init__(self, allowed_tools: Set[str]):
        self.allowed_tools = allowed_tools

    def simulate(self, plan: List[IntentResult]) -> Dict[str, Any]:
        blockers = []
        for i, intent in enumerate(plan):
            if intent.intent not in self.allowed_tools:
                blockers.append(f"Step {i}: Tool '{intent.intent}' not allowed.")
                continue
            if intent.intent == "open_app":
                path = intent.params.get("_resolved_path")
                if path:
                    is_valid, _ = verify_path(path)
                    if not is_valid: blockers.append(f"Step {i}: Path '{path}' not found.")
        return {"feasible": len(blockers) == 0, "blockers": blockers}

class Orchestrator:
    """
    AEGIS Elite Orchestrator (Tier 4).
    Orchestrates the provable execution pipeline and generates replayable traces.
    """
    def __init__(self):
        self.parser = get_parser()
        self.planner = get_planner()
        self.router = get_router()
        self.guard = get_guard()
        self.executor = get_deterministic_executor()
        self.journal = get_journal()
        self.verifier = get_semantic_verifier()
        self.event_logger = get_event_logger()
        self.state_manager = get_state_manager()
        
        self.allowed_tools: Set[str] = {
            *list_tools(),
            "general_chat",
        }
        self.simulator = PlanSimulator(self.allowed_tools)

    async def process(self, request: CommandRequest) -> CommandResponse:
        start_time = time.perf_counter()
        ctx = ExecutionContext.create_root()
        settings = get_settings()
        approval_manager = get_approval_manager()
        command_id = str(request.context.get("command_id") or ctx.trace_id)
        approval_granted = bool(request.context.get("approval_granted", False))
        command_record = approval_manager.create_received(request.text, command_id=command_id)
        cancellation_token: CancellationToken = request.context.get("cancellation_token") or approval_manager.token_for(command_id)
        
        self.event_logger.log(
            EventType.COMMAND_RECEIVED, 
            {"input": request.text, "mode": request.mode.value}, 
            ctx.trace_id, ctx.span_id
        )

        all_actions: List[ActionResult] = []
        all_warnings: List[str] = []
        guard_events: list[Dict[str, Any]] = []
        fsm_state = "IDLE"

        async def transition(to_state: str, reason: Optional[str] = None) -> None:
            nonlocal fsm_state
            if fsm_state == to_state:
                return
            await ws_bridge.emit_state_change(
                fsm_state,
                to_state,
                reason=reason,
                trace_id=str(ctx.trace_id),
            )
            fsm_state = to_state
        
        # 1. CAPABILITY ROUTING (9B Decision)
        routing = await self.router.route(request)
        
        # 2. RELIABILITY BUDGETS (Recovery Science)
        max_iterations = 10
        iteration = 0
        recovery_depth = 0
        vision_attempts = 0
        replan_count = 0
        
        current_goal = request.text
        plan = []
        primary_intent = "unknown"
        
        await ws_bridge.emit_event(
            ws_bridge.ProtocolEventType.COMMAND_RECEIVED,
            {"command_id": command_id, "text": request.text, "mode": request.mode.value},
            trace_id=str(ctx.trace_id),
            span_id=str(ctx.span_id),
            runtime_phase="THINKING",
            source=ws_bridge.Component.ORCHESTRATOR,
        )
        await transition("THINKING")
        await transition("PLANNING")
        
        try:
            # INITIAL PLANNING
            intents = await self.parser.parse(current_goal, model=routing.planner_model)
            if intents:
                primary_intent = intents[0].intent
            await ws_bridge.emit_event(
                ws_bridge.ProtocolEventType.INTENT_PARSED,
                {"intents": [intent.model_dump(mode="json") for intent in intents]},
                trace_id=str(ctx.trace_id),
                span_id=str(ctx.span_id),
                runtime_phase="PLANNING",
                source=ws_bridge.Component.INTENT_PARSER,
            )
            plan = self.planner.plan(intents)
            sim = self.simulator.simulate(plan)
            await ws_bridge.emit_event(
                ws_bridge.ProtocolEventType.PLAN_CREATED,
                {
                    "plan_id": str(ctx.span_id),
                    "steps": [
                        {
                            "step_id": f"{ctx.span_id}:{i}",
                            "tool": intent.intent,
                            "description": intent.raw_input or intent.intent,
                            "params": intent.params,
                        }
                        for i, intent in enumerate(plan)
                    ],
                    "feasible": sim["feasible"],
                    "blockers": sim["blockers"],
                },
                trace_id=str(ctx.trace_id),
                span_id=str(ctx.span_id),
                runtime_phase="PLANNING",
                source=ws_bridge.Component.PLANNER,
            )

            if not sim["feasible"]:
                all_actions.append(ActionResult(
                    action="plan",
                    params={},
                    status=ActionStatus.BLOCKED,
                    success=False,
                    output="Plan blocked: " + "; ".join(sim["blockers"]),
                ))
                await transition("FAILED", reason="Plan feasibility failed")
                plan = []

            if cancellation_token.cancelled:
                all_actions.append(ActionResult(
                    action="command",
                    params={},
                    status=ActionStatus.CANCELLED,
                    success=False,
                    output=cancellation_token.cancelled_reason or "Command cancelled",
                ))
                await transition("FAILED", reason="Command cancelled before execution")
                plan = []

            if plan:
                preflight_block: str | None = None
                approval_required = False
                for i, intent in enumerate(plan):
                    guard_result = self.guard.evaluate(intent)
                    guard_event = guard_result.model_dump(mode="json")
                    guard_events.append(guard_event)
                    all_warnings.extend(guard_result.warnings)
                    await ws_bridge.emit_event(
                        ws_bridge.ProtocolEventType.GUARD_EVALUATED,
                        {
                            "command_id": command_id,
                            "action": intent.intent,
                            "decision": "block" if not guard_result.allowed else ("escalate" if guard_result.requires_approval else "allow"),
                            "risk_level": guard_result.risk.value,
                            "requires_approval": guard_result.requires_approval,
                            "reason": guard_result.reason,
                            "warnings": guard_result.warnings,
                            "preflight": True,
                            "step_index": i,
                        },
                        trace_id=str(ctx.trace_id),
                        span_id=str(ctx.span_id),
                        runtime_phase=fsm_state,
                        source=ws_bridge.Component.GUARD,
                    )

                    if not guard_result.allowed:
                        preflight_block = guard_result.reason
                        break
                    approval_required = approval_required or guard_result.requires_approval

                highest_risk = _highest_risk_from_guards(guard_events)
                verification_state = _verification_state_for_plan(plan)

                if preflight_block:
                    all_actions.append(ActionResult(
                        action=plan[0].intent,
                        params=plan[0].params,
                        status=ActionStatus.BLOCKED,
                        success=False,
                        output=preflight_block,
                    ))
                    approval_manager.mark_blocked(
                        command_id,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=preflight_block,
                        verification_state=verification_state,
                    )
                    await ws_bridge.emit_command_status(
                        command_id=command_id,
                        status=CommandStatus.BLOCKED,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=preflight_block,
                        verification_state=verification_state,
                    )
                    await transition("FAILED", reason=preflight_block)
                    plan = []
                elif approval_required and not approval_granted:
                    pending_reason = f"{highest_risk.value} risk command requires approval"
                    record = approval_manager.register_pending(
                        command_id=command_id,
                        text=request.text,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=pending_reason,
                        warnings=all_warnings,
                        metadata={"plan": [intent.model_dump(mode="json") for intent in plan]},
                    )
                    await ws_bridge.emit_approval_required(record.to_dict(), trace_id=str(ctx.trace_id))
                    await transition("IDLE", reason="Command pending approval")
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return CommandResponse(
                        trace_id=str(ctx.trace_id),
                        status=CommandStatus.PENDING_APPROVAL,
                        intent=primary_intent,
                        message=pending_reason,
                        actions=[],
                        guard={
                            "allowed": False,
                            "reason": pending_reason,
                            "risk": highest_risk.value,
                            "warnings": all_warnings,
                            "evaluations": guard_events,
                        },
                        warnings=all_warnings,
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        duration_ms=duration_ms,
                    )
                elif approval_granted and command_record.status == CommandStatus.CANCELLED:
                    raise asyncio.CancelledError()
                elif approval_granted and _unverified_side_effects(plan):
                    blocked_tools = ", ".join(sorted(set(_unverified_side_effects(plan))))
                    reason = f"Unverified execution gate blocked side-effecting action(s): {blocked_tools}"
                    all_actions.append(ActionResult(
                        action="verification_gate",
                        params={},
                        status=ActionStatus.BLOCKED,
                        success=False,
                        output=reason,
                    ))
                    approval_manager.mark_blocked(
                        command_id,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=reason,
                        verification_state="unverified",
                    )
                    await ws_bridge.emit_command_status(
                        command_id=command_id,
                        status=CommandStatus.BLOCKED,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=reason,
                        verification_state="unverified",
                    )
                    await transition("FAILED", reason=reason)
                    plan = []
                elif plan:
                    record = approval_manager.mark_running(
                        command_id,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        verification_state=verification_state,
                    )
                    await ws_bridge.emit_command_status(
                        command_id=command_id,
                        status=CommandStatus.RUNNING,
                        trace_id=str(ctx.trace_id),
                        risk_level=highest_risk,
                        reason=record.reason,
                        verification_state=verification_state,
                    )
            
            while iteration < max_iterations and plan:
                if cancellation_token.cancelled:
                    all_actions.append(ActionResult(
                        action="command",
                        params={},
                        status=ActionStatus.CANCELLED,
                        success=False,
                        output=cancellation_token.cancelled_reason or "Command cancelled",
                    ))
                    await transition("FAILED", reason="Command cancelled")
                    break

                iteration += 1
                intent = plan.pop(0)
                step_ctx = ctx.create_child(step_index=len(all_actions))
                
                # A. OPTIONAL CHAOS INJECTION (Validation Mode)
                if settings.debug and iteration > 1:
                    from aegis.utils.chaos_engine import ChaosEngine
                    await ChaosEngine.inject_noise(probability=0.1)

                guard_result = self.guard.evaluate(intent)
                guard_events.append(guard_result.model_dump(mode="json"))
                all_warnings.extend(guard_result.warnings)
                await ws_bridge.emit_event(
                    ws_bridge.ProtocolEventType.GUARD_EVALUATED,
                    {
                        "command_id": command_id,
                        "action": intent.intent,
                        "decision": "block" if not guard_result.allowed else ("escalate" if guard_result.requires_approval else "allow"),
                        "risk_level": guard_result.risk.value,
                        "requires_approval": guard_result.requires_approval,
                        "reason": guard_result.reason,
                        "warnings": guard_result.warnings,
                    },
                    trace_id=str(ctx.trace_id),
                    span_id=str(step_ctx.span_id),
                    runtime_phase=fsm_state,
                    source=ws_bridge.Component.GUARD,
                )

                if not guard_result.allowed:
                    all_actions.append(ActionResult(
                        action=intent.intent,
                        params=intent.params,
                        status=ActionStatus.BLOCKED,
                        success=False,
                        output=guard_result.reason,
                    ))
                    await transition("FAILED", reason=guard_result.reason)
                    break

                # B. EMIT ACTION_STARTED to frontend
                action_id = str(step_ctx.span_id)
                await ws_bridge.emit_action_started(
                    action_id=action_id,
                    tool=intent.intent,
                    trace_id=str(ctx.trace_id),
                    target=str(intent.params),
                )
                await transition("EXECUTING")

                # C. FORMAL EXECUTION
                action_result = await self.executor.execute(intent, step_ctx, cancellation_token=cancellation_token)
                
                # D. SEMANTIC VERIFICATION (Execution != Success)
                action_result.semantic_score = await self.verifier.verify_result(action_result)
                if action_result.semantic_score < 0.5:
                    action_result.success = False
                    action_result.recovery_hint = "Semantic validation failed (e.g., wrong window title or content)."
                
                all_actions.append(action_result)

                # E. EMIT ACTION RESULT to frontend
                if action_result.success:
                    await ws_bridge.emit_action_completed(
                        action_id=action_id,
                        success=True,
                        latency_ms=action_result.metrics.execution_time_ms,
                        trace_id=str(ctx.trace_id),
                        retries=action_result.metrics.retries,
                        execution_evidence=action_result.execution_evidence,
                    )
                    await transition("VERIFYING")
                else:
                    await ws_bridge.emit_action_failed(
                        action_id=action_id,
                        error=action_result.output,
                        trace_id=str(ctx.trace_id),
                        is_recoverable=True,
                        execution_evidence=action_result.execution_evidence,
                    )

                # F. EMIT TELEMETRY UPDATE
                avg_det = sum(a.metrics.determinism_score for a in all_actions) / len(all_actions)
                recovery_budget_pct = 1.0 - (recovery_depth / max(settings.models.max_recovery_depth, 1))
                await ws_bridge.emit_telemetry(
                    determinism_score=avg_det,
                    recovery_budget=recovery_budget_pct,
                    active_app=self.state_manager.get_state().active_app or "None",
                )

                # G. ACTION JOURNALING (Timeline Pulse)
                self.event_logger.log(
                    EventType.ACTION_SUCCESS if action_result.success else EventType.SYSTEM_ERROR,
                    {
                        "action": action_result.action,
                        "success": action_result.success,
                        "determinism": action_result.metrics.determinism_score,
                        "time_ms": action_result.metrics.execution_time_ms,
                        "recovery_hint": action_result.recovery_hint
                    },
                    step_ctx.trace_id, step_ctx.span_id
                )

                # H. RECOVERY LOOP (Self-Healing Budget Enforcement)
                if not action_result.success:
                    recovery_depth += 1
                    
                    if recovery_depth > settings.models.max_recovery_depth:
                        logger.error("[ORCHESTRATOR] Recovery budget exceeded (depth). Halting.")
                        await ws_bridge.emit_event(
                            ws_bridge.ProtocolEventType.RECOVERY_EXHAUSTED,
                            {"reason": "Max recovery depth exceeded", "depth": recovery_depth},
                            trace_id=str(ctx.trace_id),
                            source=ws_bridge.Component.RECOVERY,
                        )
                        break
                    
                    # Emit recovery event
                    await ws_bridge.emit_event(
                        ws_bridge.ProtocolEventType.RECOVERY_TRIGGERED,
                        {"reason": action_result.recovery_hint or "Action failed", "depth": recovery_depth, "max_depth": settings.models.max_recovery_depth},
                        trace_id=str(ctx.trace_id),
                        source=ws_bridge.Component.RECOVERY,
                    )
                    await ws_bridge.emit_state_change("EXECUTING", "RECOVERING", reason=action_result.recovery_hint, trace_id=str(ctx.trace_id))
                    fsm_state = "RECOVERING"

                    # Escalation Logic
                    if action_result.metrics.determinism_score < 0.4 and vision_attempts < settings.models.max_vision_attempts:
                        logger.warning("[ORCHESTRATOR] Low determinism. Vision validation required.")
                        vision_attempts += 1
                    
                    if replan_count < settings.models.max_replans:
                        logger.info("[ORCHESTRATOR] Triggering re-plan...")
                        replan_count += 1
                        break
                    else:
                        break

        except Exception as e:
            self.event_logger.log(EventType.SYSTEM_ERROR, {"error": str(e)}, ctx.trace_id, ctx.span_id, level="ERROR")
            all_actions.append(ActionResult(action="orchestrator", status=ActionStatus.FAILED, success=False, output=str(e)))
            await transition("FAILED", reason=str(e))

        # 4. Final Status Resolution
        final_status = CommandStatus.EXECUTED if all_actions and all(a.success for a in all_actions) else CommandStatus.FAILED
        if any(a.status == ActionStatus.CANCELLED for a in all_actions) or cancellation_token.cancelled:
            final_status = CommandStatus.CANCELLED
        if any(a.status == ActionStatus.BLOCKED for a in all_actions):
            final_status = CommandStatus.BLOCKED

        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # RELIABILITY SCORE (Final Verdict)
        avg_determinism = sum(a.metrics.determinism_score for a in all_actions) / len(all_actions) if all_actions else 0.0
        
        summary = {
            "trace_id": str(ctx.trace_id), 
            "status": final_status.value, 
            "steps": len(all_actions), 
            "duration_ms": duration_ms,
            "avg_determinism": avg_determinism,
            "recovery_used": recovery_depth > 0
        }
        self.event_logger.log(EventType.ACTION_SUCCESS, {"summary": summary}, ctx.trace_id, ctx.span_id)

        # 5. SECURE GOLDEN TRACE (For Regression & Science)
        self.journal.record(str(ctx.trace_id), current_goal, all_actions, summary)

        # 6. EMIT TASK_FINISHED to frontend
        final_fsm = "COMPLETED" if final_status == CommandStatus.EXECUTED else "FAILED"
        await transition(final_fsm)
        await ws_bridge.emit_task_finished(trace_id=str(ctx.trace_id), final_state=final_fsm)

        risk_rank = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        highest_risk = max(
            (g.get("risk", "none") for g in guard_events),
            default="none",
            key=lambda value: risk_rank.get(str(value), 0),
        )
        guard_summary = {
            "allowed": final_status != CommandStatus.BLOCKED,
            "reason": "All evaluated guard checks passed" if final_status != CommandStatus.BLOCKED else "At least one guard check blocked execution",
            "risk": highest_risk,
            "warnings": all_warnings,
            "evaluations": guard_events,
        }

        if final_status not in (CommandStatus.PENDING_APPROVAL, CommandStatus.UNKNOWN):
            try:
                completion_state = _completion_verification_state(
                    all_actions,
                    final_status,
                    avg_determinism,
                )
                approval_manager.complete(
                    command_id,
                    final_status,
                    reason=summary.get("status", ""),
                    verification_state=completion_state,
                )
                await ws_bridge.emit_command_status(
                    command_id=command_id,
                    status=final_status,
                    trace_id=str(ctx.trace_id),
                    risk_level=RiskLevel(highest_risk) if highest_risk in RiskLevel._value2member_map_ else RiskLevel.NONE,
                    reason=summary.get("status", ""),
                    verification_state=completion_state,
                )
            except Exception:
                logger.exception("[ORCHESTRATOR] Failed to complete command record")

        return CommandResponse(
            trace_id=str(ctx.trace_id),
            status=final_status,
            intent=primary_intent,
            message=f"Task completed. Reliability Score: {avg_determinism:.2f}",
            actions=all_actions,
            guard=guard_summary,
            warnings=all_warnings,
            timestamp=datetime.utcnow().isoformat() + "Z",
            duration_ms=duration_ms
        )

_instance = None
def get_orchestrator() -> Orchestrator:
    global _instance
    if _instance is None:
        _instance = Orchestrator()
    return _instance
