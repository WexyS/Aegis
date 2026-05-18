# src/aegis/core/self_healing.py

import asyncio
import logging
from typing import Any
from aegis.core.schemas import ActionResult
from aegis.core.constants import ActionStatus

logger = logging.getLogger(__name__)

class SelfHealing:
    """
    AEGIS Self-Healing Engine.
    Wraps tool execution with retry logic and adaptive backoff.
    Ensures that transient failures or race conditions don't break the autonomous loop.
    """
    def __init__(self, max_retries: int = 2, base_delay: float = 0.5):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def run(self, tool_fn, *args, **kwargs) -> Any:
        """
        Executes a tool function with retry logic.
        Handles both string outputs and list[ActionResult] outputs.
        """
        last_result: Any = None
        cancellation_token = kwargs.get("cancellation_token")
        
        for attempt in range(self.max_retries + 1):
            if cancellation_token is not None and getattr(cancellation_token, "cancelled", False):
                return f"Error: {getattr(cancellation_token, 'cancelled_reason', None) or 'Command cancelled'}"
            if attempt > 0:
                delay = self.base_delay * attempt
                logger.info("[SELF-HEALING] Retry attempt %d/%d (Waiting %.1fs)", 
                            attempt, self.max_retries, delay)
                await asyncio.sleep(delay)
                if cancellation_token is not None and getattr(cancellation_token, "cancelled", False):
                    return f"Error: {getattr(cancellation_token, 'cancelled_reason', None) or 'Command cancelled'}"
            
            try:
                # Execute the wrapped action
                result = await tool_fn(*args, **kwargs)
                last_result = result
                
                # Adaptive failure detection
                if isinstance(result, str):
                    normalized = result.strip().lower()
                    is_failed = normalized.startswith(("error", "failed", "read error", "write error"))
                elif isinstance(result, list):
                    is_failed = any(r.status == ActionStatus.FAILED for r in result)
                else:
                    is_failed = False
                
                if not is_failed:
                    return result
                
                logger.warning("[SELF-HEALING] Attempt %d failed. Checking for retry eligibility...", attempt + 1)
                
            except Exception as e:
                logger.error("[SELF-HEALING] Exception during execution: %s", e)
                last_result = f"Error: Internal Exception - {str(e)}"

        return last_result

_self_healer: SelfHealing | None = None


def get_self_healer() -> SelfHealing:
    global _self_healer
    if _self_healer is None:
        _self_healer = SelfHealing()
    return _self_healer
