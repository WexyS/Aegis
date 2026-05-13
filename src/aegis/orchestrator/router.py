# src/aegis/orchestrator/router.py

import logging
from pydantic import BaseModel
from aegis.core.schemas import CommandRequest
from aegis.core.constants import RiskLevel
from aegis.core.config import get_settings

logger = logging.getLogger(__name__)

class RoutingVerdict(BaseModel):
    planner_model: str
    requires_vision: bool
    risk: RiskLevel
    reasoning: str

class CapabilityRouter:
    """
    AEGIS Production-Grade Capability Router.
    Decides model selection, vision necessity, and risk escalation.
    """
    def __init__(self):
        self.settings = get_settings()

    async def route(self, request: CommandRequest) -> RoutingVerdict:
        text = request.text.lower()
        
        # 1. Risk Analysis
        high_risk_keywords = ["delete", "format", "kill", "write_file", "git_push", "rm -rf"]
        is_high_risk = any(k in text for k in high_risk_keywords)
        
        # 2. Vision Necessity
        vision_keywords = ["see", "look", "button", "icon", "where is", "image", "screen"]
        needs_vision = any(k in text for k in vision_keywords)
        
        # 3. Model Escalation Logic (VRAM Optimized)
        # 9B is our resident coordinator. 27B is escalated on-demand.
        if len(text.split()) > 20 or is_high_risk or "plan" in text:
            verdict = RoutingVerdict(
                planner_model=self.settings.models.default_model, # Usually qwen3.6-27b
                requires_vision=needs_vision,
                risk=RiskLevel.HIGH if is_high_risk else RiskLevel.MEDIUM,
                reasoning="Task complexity or risk triggers 27B escalation."
            )
        else:
            verdict = RoutingVerdict(
                planner_model="qwen/qwen3.5-9b",
                requires_vision=needs_vision,
                risk=RiskLevel.LOW,
                reasoning="Simple instruction routed to resident 9B model."
            )
            
        logger.info(f"[ROUTER] Verdict: {verdict.planner_model} | Risk: {verdict.risk} | Vision: {verdict.requires_vision}")
        return verdict

def get_router() -> CapabilityRouter:
    return CapabilityRouter()
