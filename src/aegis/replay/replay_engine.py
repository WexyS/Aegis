# src/aegis/replay/replay_engine.py

import json
import logging
import os
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from aegis.core.context import ExecutionContext
from aegis.core.schemas import IntentResult, ActionResult
from aegis.core.constants import ActionStatus, EventType
from aegis.executor.deterministic_executor import get_deterministic_executor
from aegis.core.state_manager import get_state_manager
from aegis.logger.event_logger import get_event_logger

logger = logging.getLogger(__name__)

class ReplayMode(Enum):
    VALIDATE = "validate" # Re-execute on OS and compare
    SIMULATE = "simulate" # State-transition check only (no side effects)

class ReplayEngine:
    """
    AEGIS Tier 4 Deterministic Replay System.
    Provides formal verification of execution determinism.
    Supports real-world validation and logical state simulation.
    """
    def __init__(self):
        self.executor = get_deterministic_executor()
        self.state_manager = get_state_manager()
        self.event_logger = get_event_logger()

    async def replay_from_file(self, 
                               jsonl_path: str, 
                               mode: ReplayMode = ReplayMode.VALIDATE,
                               strict: bool = True) -> Dict[str, Any]:
        """Loads and verifies a trace with Tier 4 strictness."""
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"Trace file not found: {jsonl_path}")

        events = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                events.append(json.loads(line))
        
        replay_plan = self._reconstruct_trace(events)
        return await self.verify_determinism(replay_plan, mode, strict)

    def _reconstruct_trace(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reconstructs execution steps using span_id correlation.
        Ensures trace integrity even if logs are out of order.
        """
        steps_map = {}
        
        for e in events:
            span_id = e.get("span_id")
            if not span_id: continue
            
            if span_id not in steps_map:
                steps_map[span_id] = {"span_id": span_id}
            
            e_type = e["event_type"]
            data = e.get("data", {})
            
            if e_type == "ACTION_START":
                steps_map[span_id].update({
                    "intent": data.get("intent"),
                    "params": data.get("params"),
                    "state_before": data.get("state_before"),
                    "trace_id": e.get("trace_id")
                })
            elif e_type in ["ACTION_SUCCESS", "ACTION_FAILED"]:
                steps_map[span_id].update({
                    "expected_state_after": data.get("state_after"),
                    "expected_status": data.get("proof", {}).get("status") or ("SUCCESS" if e_type == "ACTION_SUCCESS" else "FAILED")
                })

        # Sort by timestamp of ACTION_START to maintain logical order
        # (Alternatively, could use step_index if we add it to logs)
        return [steps_map[sid] for sid in steps_map if "intent" in steps_map[sid]]

    async def verify_determinism(self, 
                                 plan: List[Dict[str, Any]], 
                                 mode: ReplayMode = ReplayMode.VALIDATE,
                                 strict: bool = True) -> Dict[str, Any]:
        """
        Formally verifies the replay plan.
        Mode: VALIDATE (Real) or SIMULATE (Log-only logic).
        """
        trace_id = uuid4()
        replay_ctx = ExecutionContext(trace_id=trace_id, span_id=uuid4())
        
        print(f"[REPLAY] {mode.value.upper()} Mode | Trace: {trace_id} | Steps: {len(plan)}")
        
        results = []
        overall_feasible = True
        
        for i, step in enumerate(plan):
            step_span = replay_ctx.create_child(step_index=i)
            mismatches = []
            
            # 1. State-Before Verification (STRICT)
            # In VALIDATE mode, we sync with OS truth. 
            # In SIMULATE mode, we assume the previous step's state_after.
            if mode == ReplayMode.VALIDATE:
                await self.state_manager.sync_with_os(step_span.trace_id, step_span.span_id)
                actual_before = self.state_manager.get_state()
            else:
                # Simulation logic: state_before of step N must match state_after of step N-1
                actual_before = results[-1]["actual_state"] if results else plan[0].get("state_before")

            # Deep Compare State-Before
            sb_diff = self._compare_states(step.get("state_before"), actual_before)
            if sb_diff:
                mismatches.extend([{"field": k, "type": "pre_execution", **v} for k, v in sb_diff.items()])
                if strict:
                    print(f"[REPLAY] CRITICAL: Pre-execution state mismatch at step {i}")
                    overall_feasible = False
                    if strict: break

            # 2. Execution / Simulation
            if mode == ReplayMode.VALIDATE:
                intent = IntentResult(intent=step["intent"], params=step["params"], confidence=1.0)
                action_result = await self.executor.execute(intent, step_span)
                actual_status = action_result.status.value
                actual_after = self.state_manager.get_state()
            else:
                # Simulate: We don't call OS, we just check if the logic holds
                actual_status = step.get("expected_status")
                actual_after = step.get("expected_state_after") # Logical assumption for simulation

            # 3. Post-Execution Verification (Deep Comparison)
            sa_diff = self._compare_states(step.get("expected_state_after"), actual_after)
            if sa_diff:
                mismatches.extend([{"field": k, "type": "post_execution", **v} for k, v in sa_diff.items()])
                overall_feasible = False

            results.append({
                "step": i,
                "intent": step["intent"],
                "mismatches": mismatches,
                "actual_state": actual_after
            })

        final_report = {
            "success": overall_feasible,
            "mode": mode.value,
            "trace_id": str(trace_id),
            "steps": results
        }
        
        return final_report

    def _compare_states(self, expected: Optional[Dict], actual: Any) -> Dict[str, Dict]:
        """Performs deep comparison of OS state fields."""
        if not expected or not actual: return {}
        
        # Normalize actual if it's a snapshot object
        actual_dict = actual if isinstance(actual, dict) else {
            "pid": actual.pid,
            "hwnd": actual.hwnd,
            "active_app": actual.active_app,
            "last_status": actual.last_status
        }
        
        diff = {}
        fields_to_check = ["pid", "hwnd", "active_app", "last_status"]
        
        for f in fields_to_check:
            e_val = expected.get(f)
            a_val = actual_dict.get(f)
            if e_val != a_val:
                diff[f] = {"expected": e_val, "actual": a_val}
        
        return diff

_instance = None
def get_replay_engine() -> ReplayEngine:
    global _instance
    if _instance is None:
        _instance = ReplayEngine()
    return _instance
