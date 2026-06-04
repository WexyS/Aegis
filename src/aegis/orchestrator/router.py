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
    model_hint_status: str = "legacy_hint_only"
    model_hint_authoritative: bool = False
    model_call_authorized: bool = False
    provider_selection_granted: bool = False
    auto_mode_decision_granted: bool = False
    execution_permission: str = "not_granted_by_legacy_router_hint"
    evidence_created: bool = False
    verifier_success: bool = False

class CapabilityRouter:
    """
    AEGIS Production-Grade Capability Router.
    Computes legacy routing metadata, vision necessity, and risk escalation.

    The planner_model field is a legacy model hint only. It is not provider
    selection, model-call permission, Auto Mode authorization, evidence, or
    verifier success.
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
        
        # 3. Legacy Model Hint Logic
        # This remains metadata only until Model Auto Mode authorizes provider
        # selection through explicit future gates.
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
