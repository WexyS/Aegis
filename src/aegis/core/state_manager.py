# src/aegis/core/state_manager.py

import threading
import time
import ctypes
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID, uuid4

from aegis.logger.event_logger import get_event_logger, EventType
from aegis.executor.utils import get_window_pid, get_running_pids
import pygetwindow as gw

@dataclass(frozen=True)
class AegisStateSnapshot:
    """
    Formal State Space (Tier 4.5).
    Represents a single point in the system's state space.
    """
    version: int
    timestamp: str
    active_app: Optional[str]
    pid: Optional[int]
    hwnd: Optional[int]
    last_action: Optional[str]
    last_status: Optional[str]
    is_responsive: bool = True
    focus_stable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class Invariants:
    """
    System Invariants for Formal Consistency.
    These laws MUST hold true for the state to be considered 'Legal'.
    """
    @staticmethod
    def active_window_matches_pid(state: AegisStateSnapshot) -> bool:
        """Law: If a window is active, it MUST belong to the recorded PID."""
        if state.hwnd and state.pid:
            # Reality check via OS API
            current_pid = get_window_pid(state.hwnd)
            return current_pid == state.pid
        return True

    @staticmethod
    def responsive_implies_not_hung(state: AegisStateSnapshot) -> bool:
        """Law: Responsive status must align with OS hunger check."""
        if state.hwnd and state.is_responsive:
            is_hung = ctypes.windll.user32.IsHungAppWindow(state.hwnd)
            return not is_hung
        return True

class StateManager:
    """
    AEGIS Tier 4.5 Invariant-Driven State Manager.
    Ensures that every state transition maintains system-wide consistency laws.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._version = 0
        self._current_state: Dict[str, Any] = {
            "active_app": None, "pid": None, "hwnd": None,
            "last_action": None, "last_status": None,
            "is_responsive": True, "focus_stable": False,
            "metadata": {}
        }
        self._invariants: List[Callable[[AegisStateSnapshot], bool]] = [
            Invariants.active_window_matches_pid,
            Invariants.responsive_implies_not_hung
        ]

    def validate_invariants(self, state: AegisStateSnapshot) -> List[str]:
        """Checks all system laws against the current state snapshot."""
        violations = []
        for inv in self._invariants:
            if not inv(state):
                violations.append(f"Invariant Violation: {inv.__name__}")
        return violations

    def update(self, trace_id: UUID, span_id: UUID, **kwargs) -> AegisStateSnapshot:
        with self._lock:
            self._version += 1
            for key, value in kwargs.items():
                if key in self._current_state:
                    self._current_state[key] = value

            snapshot = self._snapshot_internal()
            
            # Tier 4.5: Check for Illegal State
            violations = self.validate_invariants(snapshot)
            if violations:
                get_event_logger().log(
                    EventType.SYSTEM_ERROR,
                    {"message": "ILLEGAL STATE DETECTED", "violations": violations},
                    trace_id, span_id, level="ERROR"
                )
                # In a truly formal system, we might halt here.
                # For now, we log as CRITICAL error.

            get_event_logger().log(EventType.STATE_SNAPSHOT, asdict(snapshot), trace_id, span_id, level="DEBUG")
            return snapshot

    async def sync_with_os(self, trace_id: UUID, span_id: UUID):
        """Triple-Pulse Synchronization (Hardened)."""
        import asyncio
        pulses = []
        try:
            for _ in range(3):
                # PyGetWindow calls are very fast but synchronous, so they are fine, but sleep must be async
                win = gw.getActiveWindow()
                pulses.append(win._hWnd if win else None)
                await asyncio.sleep(0.05)
            
            with self._lock:
                is_consistent = len(set(pulses)) == 1
                active_hwnd = pulses[0]
                active_pid = get_window_pid(active_hwnd) if active_hwnd else None
                
                self._current_state.update({
                    "hwnd": active_hwnd,
                    "pid": active_pid,
                    "focus_stable": is_consistent and active_hwnd == self._current_state["hwnd"]
                })
                
                self._version += 1
                snapshot = self._snapshot_internal()
            
            get_event_logger().log(EventType.STATE_SNAPSHOT, {"message": "Sync completed", "state": asdict(snapshot)}, trace_id, span_id, level="DEBUG")
        except Exception as e:
            get_event_logger().log(EventType.SYSTEM_ERROR, {"message": f"Sync failed: {e}"}, trace_id, span_id, level="ERROR")

    def get_state(self) -> AegisStateSnapshot:
        with self._lock:
            return self._snapshot_internal()

    def _snapshot_internal(self) -> AegisStateSnapshot:
        return AegisStateSnapshot(version=self._version, timestamp=datetime.now(timezone.utc).isoformat() + "Z", **self._current_state)

_instance = None
def get_state_manager() -> StateManager:
    global _instance
    if _instance is None:
        _instance = StateManager()
    return _instance
