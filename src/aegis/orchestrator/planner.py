from __future__ import annotations
import logging
from typing import Any
from aegis.core.schemas import IntentResult, ActionResult
from aegis.core.constants import ActionStatus
from aegis.core.app_map import resolve_app_name, get_app_config
from aegis.executor.utils import smart_match_app

logger = logging.getLogger(__name__)

class Planner:
    """
    AEGIS Planner — Converts high-level intents into a robust execution graph/plan.
    Ensures dependencies like window focus, waiting, and context sharing are handled.
    """

    def plan(self, intents: list[IntentResult]) -> list[IntentResult]:
        """
        Takes a raw list of intents and injects necessary intermediate steps 
        (e.g., focus before type, wait after open_app).
        """
        logger.info("[PLANNER] Creating execution plan for %d intents", len(intents))
        plan: list[IntentResult] = []
        
        last_app = None
        last_focus_keywords = None
        last_focus_process_name = None
        
        for i, intent in enumerate(intents):
            # 1. Focus Logic
            # If we are typing and we know which app was just opened, ensure focus
            if intent.intent == "type":
                if last_app:
                    logger.info("[PLANNER] Injecting focus dependency for '%s' before type", last_app)
                    # We could inject a special 'focus' intent here, 
                    # but for now we'll just tag the 'type' intent with metadata
                    intent.params["_require_focus"] = last_app
                    if last_focus_keywords:
                        intent.params["_require_focus_keywords"] = last_focus_keywords
                    if last_focus_process_name:
                        intent.params["_require_focus_process_name"] = last_focus_process_name
            
            # 2. Dependency Tracking & Metadata Enrichment
            if intent.intent in {"open_app", "focus_app", "close_app"}:
                app_query = intent.params.get("app")
                
                # Enrich with Metadata for Tier 4 Determinism
                resolved = resolve_app_name(app_query) or smart_match_app(app_query)
                if resolved:
                    config = get_app_config(resolved)
                    intent.params["app"] = resolved
                    if intent.intent == "open_app":
                        intent.params["_resolved_path"] = config.get("path")
                    intent.params["_process_name"] = config.get("process_name")
                    intent.params["_keywords"] = config.get("window_keywords")
                    last_app = resolved
                    last_focus_keywords = config.get("window_keywords")
                    last_focus_process_name = config.get("process_name")
                elif app_query:
                    last_app = app_query
                    last_focus_keywords = [str(app_query)]
                    last_focus_process_name = f"{app_query}.exe" if not str(app_query).lower().endswith(".exe") else str(app_query)
                
                # Apps need time to launch, but we optimize for chaining
                if intent.intent == "open_app":
                    is_chaining_type = (i + 1 < len(intents) and intents[i+1].intent == "type")
                    intent.params["_wait_after"] = 0.5 if is_chaining_type else 2.0
            
            plan.append(intent)
            
        logger.info("[PLAN]: %s", plan)
        return plan

def get_planner() -> Planner:
    return Planner()
