# tests/determinism/test_engine_integrity.py

import asyncio
import pytest
import subprocess
import time
from uuid import uuid4
from aegis.orchestrator.orchestrator import get_orchestrator
from aegis.executor.deterministic_executor import get_deterministic_executor
from aegis.core.state_manager import get_state_manager
from aegis.core.schemas import CommandRequest, IntentResult
from aegis.core.constants import ActionStatus, CommandStatus, ExecutionMode
from aegis.core.context import ExecutionContext
from aegis.replay.replay_engine import get_replay_engine

pytestmark = pytest.mark.windows_live

@pytest.mark.asyncio
async def test_ambiguity_window_detection():
    """
    STRICTNESS TEST: System must FAIL when multiple matching windows exist.
    We open two Notepads and try to focus.
    """
    orchestrator = get_orchestrator()
    
    # 1. Setup: Open two identical apps
    p1 = subprocess.Popen(["notepad.exe"])
    p2 = subprocess.Popen(["notepad.exe"])
    await asyncio.sleep(2.0) # Wait for manifestation
    
    try:
        # 2. Execution: Attempt to focus 'notepad'
        request = CommandRequest(text="focus notepad", mode=ExecutionMode.EXECUTE)
        result = await orchestrator.process(request)
        
        # 3. Validation: Must be AMBIGUOUS failure, NOT success
        print(f"[TEST] Result Status: {result.status}")
        for action in result.actions:
            print(f"[TEST] Action Output: {action.output}")
            
        assert result.status == CommandStatus.FAILED
        assert any("ambiguity" in a.output.lower() for a in result.actions)
        
    finally:
        p1.terminate()
        p2.terminate()

@pytest.mark.asyncio
async def test_false_success_prevention():
    """
    INTEGRITY TEST: System must not mark success if process is killed mid-execution.
    """
    executor = get_deterministic_executor()
    ctx = ExecutionContext.create_root()
    
    # 1. Prepare intent
    intent = IntentResult(
        intent="open_app", 
        params={"app": "notepad", "_process_name": "notepad.exe", "_keywords": ["Notepad"]},
        confidence=1.0
    )
    
    # We can't easily 'kill mid-execution' in a single await, 
    # but we can simulate a verifier failure by providing a fake process name
    intent.params["_process_name"] = "non_existent_process.exe"
    
    result = await executor.execute(intent, ctx)
    
    # Must be FAILED because verification will never find the process
    assert result.status == ActionStatus.FAILED

@pytest.mark.asyncio
async def test_state_drift_detection():
    """
    INVARIANT TEST: System must detect when OS state diverges from internal state.
    """
    state_manager = get_state_manager()
    ctx = ExecutionContext.create_root()
    
    # 1. Set internal state to a fake PID
    state_manager.update(ctx.trace_id, ctx.span_id, pid=99999, hwnd=12345)
    
    # 2. Trigger Sync with real OS
    state_manager.sync_with_os(ctx.trace_id, ctx.span_id)
    
    state_after = state_manager.get_state()
    
    # 3. Validation: Drift must be detected (Real OS won't have PID 99999)
    assert state_after.pid != 99999
    # focus_stable should be False because current OS != 99999
    assert state_after.focus_stable is False

@pytest.mark.asyncio
async def test_replay_determinism_integrity():
    """
    REPLAY TEST: Replay must fail if OS state differs from recorded trace.
    """
    replay = get_replay_engine()
    
    # This requires a real log file. For this test, we simulate a mismatch.
    # We create a fake trace with an impossible PID
    fake_trace = [
        {
            "event_type": "ACTION_START",
            "trace_id": str(uuid4()), "span_id": str(uuid4()),
            "data": {"intent": "type", "params": {"text": "hello"}, "state_before": {"pid": 11111, "hwnd": 22222}}
        },
        {
            "event_type": "ACTION_SUCCESS",
            "trace_id": str(uuid4()), "span_id": str(uuid4()),
            "data": {"state_after": {"pid": 11111, "hwnd": 22222}}
        }
    ]
    
    # Replay should FAIL because PID 11111 is not active
    result = await replay.verify_determinism(fake_trace, mode="validate", strict=True)
    
    assert result["success"] is False
    assert any(m["field"] == "pid" for r in result["steps"] for m in r["mismatches"])

if __name__ == "__main__":
    # Quick manual run
    asyncio.run(test_ambiguity_window_detection())
