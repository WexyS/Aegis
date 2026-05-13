"""
AEGIS AI Parser — LLM-based intent extraction.
Fallback for when rule-based parsing fails.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from aegis.core.constants import IntentSource, RiskLevel, IntentType
from aegis.core.schemas import IntentResult
from aegis.models.llm import get_llm
from aegis.intent.rules import APP_ALIASES

logger = logging.getLogger(__name__)

# Capability Whitelist
ALLOWED_INTENTS = {it.value for it in IntentType if it != IntentType.UNKNOWN}
SUPPORTED_APPS = set(APP_ALIASES.keys())

SYSTEM_PROMPT = f"""
You are the AEGIS AI Intent Parser. Your job is to extract structured intents from user commands.
Supported intents: {', '.join(ALLOWED_INTENTS)}
Supported apps: {', '.join(SUPPORTED_APPS)}

Rules:
1. Return a JSON list of objects. Each object must have "intent" and "params".
2. If multiple actions are requested, return them in order.
3. ONLY use internal app names for open_app: {', '.join(SUPPORTED_APPS)}.
4. If an app is requested but not in the list, try to find a URL instead (e.g., spotify -> open_url: https://open.spotify.com).
5. NO prose, NO explanation. ONLY JSON.
"""

class AIParser:
    """Uses an LLM to parse complex or natural language intents with strict validation."""

    def __init__(self) -> None:
        self.llm = get_llm()

    async def parse(self, text: str) -> list[IntentResult]:
        """Send text to LLM and parse the JSON response with validation."""
        logger.info("[AI-PARSER] Attempting AI parse for: %r", text)
        
        # Using chat model for general intent parsing
        response = await self.llm.generate(prompt=text, system_prompt=SYSTEM_PROMPT, model_type="chat")
        if not response:
            return []

        try:
            clean_json = self._clean_json_response(response)
            data = json.loads(clean_json)
            if not isinstance(data, list):
                data = [data]

            raw_intents = data
            valid_intents = self._validate_and_filter(raw_intents, text)
            
            logger.info("[AI-PARSER] Successfully parsed and validated %d intents", len(valid_intents))
            return valid_intents

        except Exception as e:
            logger.error("[AI-PARSER] Failed to parse LLM response: %s", e)
            logger.debug("[AI-PARSER] Raw response: %r", response)
            return []

    def _clean_json_response(self, response: str) -> str:
        """Extract JSON from markdown blocks if present."""
        clean = response.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        return clean

    def _validate_and_filter(self, raw_data: list[dict[str, Any]], original_text: str) -> list[IntentResult]:
        """Strict validation of LLM output."""
        valid_results = []
        
        for item in raw_data:
            intent_name = item.get("intent")
            params = item.get("params", {})

            # 1. Intent Whitelist Check
            if intent_name not in ALLOWED_INTENTS:
                logger.warning("[AI-PARSER] Discarding unknown/forbidden intent: %s", intent_name)
                continue

            # 2. Schema/Param Validation
            if not self._is_schema_valid(intent_name, params):
                logger.warning("[AI-PARSER] Discarding intent with invalid schema: %s (params=%s)", intent_name, params)
                continue

            # 3. Capability/App Check
            if intent_name == "open_app":
                app = params.get("app", "").lower()
                if app not in SUPPORTED_APPS:
                    logger.warning("[AI-PARSER] App '%s' not supported. Dropping.", app)
                    continue

            # 4. Construct Result
            valid_results.append(IntentResult(
                intent=intent_name,
                confidence=0.8,
                params=params,
                risk=self._resolve_risk(intent_name),
                source=IntentSource.AI,
                raw_input=original_text,
                timestamp=datetime.utcnow()
            ))
            
        return valid_results

    def _is_schema_valid(self, intent: str, params: dict[str, Any]) -> bool:
        """Check if required parameters are present for an intent."""
        if intent == "type":
            return "text" in params
        if intent == "open_url":
            return "url" in params
        if intent == "open_app":
            return "app" in params
        if intent == "click":
            return ("x" in params and "y" in params) or "selector" in params
        if intent == "search_web":
            return "query" in params
        return True

    def _resolve_risk(self, intent: str) -> RiskLevel:
        """Assign risk levels to AI-generated intents."""
        if intent in ["click", "type", "open_app"]:
            return RiskLevel.MEDIUM
        if intent in ["read_file", "summarize_file"]:
            return RiskLevel.LOW
        return RiskLevel.NONE

    async def fix_execution_failure(self, failed_intent: IntentResult, error_message: str) -> list[IntentResult]:
        """Attempt to fix a failed execution step using AI."""
        logger.info("[AI-PARSER] Attempting self-healing for failed step: %s", failed_intent.intent)
        
        prompt = f"""
The following execution step failed:
Intent: {failed_intent.intent}
Params: {failed_intent.params}
Error: {error_message}

Your task is to provide an alternative way to achieve the same goal.
Example: If 'open_app: spotify' failed because it's not installed, try 'open_url: https://open.spotify.com'.

Return ONLY a JSON list of alternative steps.
"""
        # Using code model for self-healing/logic fixes
        response = await self.llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT, model_type="code")
        if not response:
            return []

        try:
            clean_json = self._clean_json_response(response)
            data = json.loads(clean_json)
            if not isinstance(data, list):
                data = [data]
            
            return self._validate_and_filter(data, failed_intent.raw_input)
        except:
            return []

# Singleton
_ai_parser: AIParser | None = None

def get_ai_parser() -> AIParser:
    global _ai_parser
    if _ai_parser is None:
        _ai_parser = AIParser()
    return _ai_parser
