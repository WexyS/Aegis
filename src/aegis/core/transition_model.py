# src/aegis/core/transition_model.py

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from aegis.core.state_manager import AegisStateSnapshot

logger = logging.getLogger(__name__)

class StateTransitionModel:
    """
    AEGIS Tier 4.5 Formal Transition Model.
    Treats OS interaction as a Mathematical State Transition Function: S2 = T(S1, Action).
    Enforces Invariants and Formal Postconditions.
    """
    
    @staticmethod
    def validate_preconditions(intent: str, state: AegisStateSnapshot) -> List[str]:
        """Checks if the system state allows the requested action."""
        errors = []
        if intent == "type":
            if not state.hwnd:
                errors.append("No active window handle for typing.")
            if not state.focus_stable:
                errors.append("Focus is unstable.")
        return errors

    @staticmethod
    def predict_next_state(initial_state: AegisStateSnapshot, 
                           intent: str, 
                           params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formal Transition Function: T(S1, Action) -> S2.
        Predicts the deterministic outcome of an action on the state space.
        """
        # Baseline: State remains unchanged unless specified
        s2 = asdict(initial_state)
        s2.update({
            "last_action": intent,
            "last_status": "SUCCESS",
            "version": initial_state.version + 1
        })

        # 1. 'open_app' Transformation
        if intent == "open_app":
            s2.update({
                "active_app": params.get("app"),
                "pid": "REQUIRED_IDENTIFIER",
                "hwnd": "REQUIRED_HANDLE",
            })

        return s2

    @staticmethod
    def calculate_deviation(expected_s2: Dict[str, Any], 
                            actual_s2: AegisStateSnapshot) -> List[Dict[str, Any]]:
        """
        Compares the actual resulting state against the formal transition prediction.
        Any mismatch is a Determinism Breach.
        """
        breaches = []
        actual_dict = asdict(actual_s2)

        for key, expected_val in expected_s2.items():
            if key in ["timestamp", "metadata", "version"]: continue
            
            actual_val = actual_dict.get(key)
            
            if expected_val == "REQUIRED_IDENTIFIER" or expected_val == "REQUIRED_HANDLE":
                if actual_val is None:
                    breaches.append({"field": key, "expected": "NOT_NONE", "actual": None})
                continue

            if expected_val != actual_val:
                breaches.append({
                    "field": key,
                    "expected": expected_val,
                    "actual": actual_val
                })

        return breaches

    @staticmethod
    def validate_postconditions(intent: str, state: AegisStateSnapshot) -> List[str]:
        """Strict post-execution verification."""
        errors = []
        if intent == "open_app":
            if not state.pid or not state.hwnd:
                errors.append("Process failed to manifest required handles.")
            if not state.is_responsive:
                errors.append("Manifested window is not responsive.")
        return errors

_instance = None
def get_transition_model() -> StateTransitionModel:
    global _instance
    if _instance is None:
        _instance = StateTransitionModel()
    return _instance
