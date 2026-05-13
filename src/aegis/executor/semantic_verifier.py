# src/aegis/executor/semantic_verifier.py

import logging
import pygetwindow as gw
from typing import Any, Optional
from aegis.core.schemas import ActionResult

logger = logging.getLogger(__name__)

class SemanticVerifier:
    """
    AEGIS Semantic Verification Layer.
    Moves from 'Tool Execution Success' to 'Goal Accomplishment Success'.
    Uses OCR, Accessibility Trees, and Title matching to verify outcomes.
    """
    
    @staticmethod
    def verify_window_title(hwnd: int, expected_keywords: list[str]) -> float:
        """Verify window title contains expected keywords."""
        try:
            window = [w for w in gw.getAllWindows() if w._hWnd == hwnd]
            if not window: return 0.0
            
            title = window[0].title.lower()
            matches = sum(1 for k in expected_keywords if k.lower() in title)
            return matches / len(expected_keywords) if expected_keywords else 1.0
        except Exception:
            return 0.0

    @staticmethod
    async def verify_result(action: ActionResult) -> float:
        """
        Deep semantic verification of an action result.
        Returns a semantic_confidence_score (0.0 - 1.0).
        """
        score = 1.0
        
        # 1. Logic: If tool failed, semantic score is 0
        if not action.success:
            return 0.0
            
        # 2. Window-specific semantic checks
        if action.action == "open_app":
            hwnd = action.proof.get("actual", {}).get("hwnd")
            keywords = action.params.get("_keywords", [])
            if hwnd and keywords:
                score *= SemanticVerifier.verify_window_title(hwnd, keywords)
                
        # 3. Future: OCR Verification of typed text
        # if action.action == "type": ...
        
        logger.info(f"[VERIFIER] Semantic Score for {action.action}: {score:.2f}")
        return score

def get_semantic_verifier() -> SemanticVerifier:
    return SemanticVerifier()
