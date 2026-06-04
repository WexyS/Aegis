"""
AEGIS Intent Parser — Rule-based intent engine.

Golden rules:
  1. Same input → same intent (deterministic)
  2. Unknown input → "unknown" intent (NEVER guess)
  3. Output is always a valid IntentResult
"""

from __future__ import annotations

import re
import logging
from datetime import datetime, timezone
from typing import Any

from aegis.core.constants import IntentSource, RiskLevel
from aegis.core.schemas import IntentResult
from aegis.core.app_map import resolve_app_name
from aegis.core.config import get_settings
from aegis.intent.decomposition import (
    NormalizedPlan,
    PlanStatus,
    decompose_command,
    normalized_plan_to_intents,
)
from aegis.intent.rules import RULES, KNOWN_SITES, APP_ALIASES, VERIFICATION_METADATA, IntentRule
from aegis.tools.file_tools import _is_allowed_write_path, _is_forbidden_write_path, _resolve_write_path
from aegis.tools.shell_tools import is_allowlisted_shell_command, is_destructive_shell_command


logger = logging.getLogger(__name__)


class IntentParser:
    """Deterministic, rule-based intent parser.

    Evaluates rules in order. First match wins.
    No match → "unknown" with confidence 0.0.
    """

    def __init__(self) -> None:
        self._rules = RULES
        self._compiled: list[tuple[IntentRule, list[re.Pattern[str]]]] = []
        self._compile_rules()

    def _compile_rules(self) -> None:
        for rule in self._rules:
            patterns = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in rule.patterns]
            self._compiled.append((rule, patterns))

    def normalize_text(self, text: str) -> str:
        """Clean and normalize input text for better matching."""
        text = text.lower().strip()
        
        # 1. Hard fix for Turkish suffixes to prevent partial regex issues (e.g., 'notepadni')
        text = text.replace("not defterini", "not defteri")
        text = text.replace("not defterine", "not defteri")
        text = text.replace("hesap makinesini", "hesap makinesi")
        text = text.replace("hesap makinesine", "hesap makinesi")
        text = text.replace("chrome'u", "chrome")
        text = text.replace("chrome'a", "chrome")
        text = text.replace("brave'i", "brave")
        text = text.replace("brave'ı", "brave")
        text = text.replace("brave i", "brave")
        text = text.replace("brave ı", "brave")
        text = text.replace("google'ı", "google")
        text = text.replace("premiere'i", "premiere")
        text = text.replace("premiere'ı", "premiere")
        
        # 2. Map all aliases to their internal IDs directly in the text
        # We sort by length descending to match longer aliases first (e.g. 'not defteri' before 'not')
        sorted_aliases = sorted(APP_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            internal = APP_ALIASES[alias]
            # Use word boundaries to avoid partial word replacement
            pattern = rf"\b{re.escape(alias)}\b"
            text = re.sub(pattern, internal, text)
        
        return text

    def normalize_app_name(self, text: str) -> str | None:
        """Map a potential app name/alias to its internal ID."""
        text = text.lower().strip()
        return APP_ALIASES.get(text)

    async def parse(
        self,
        text: str,
        model: str | None = None,
        *,
        model_call_authorized: bool = False,
    ) -> list[IntentResult]:
        """Parse user input into one or more structured IntentResults."""
        # Safety check: should already be clean from the API layer
        if text.startswith("b'") or text.startswith('b"'):
            logger.warning("[PARSER] Byte artifact detected! Attempting emergency clean...")
            from aegis.api.routes_command import clean_text
            text = clean_text(text)
            
        logger.info("[PARSER] Input: %r", text)
        if model:
            logger.info(
                "[PARSER] Ignoring legacy model hint %r; model calls require Model Auto Mode authorization.",
                model,
            )

        if get_settings().features.deterministic_decomposition:
            deterministic = self._parse_deterministic_decomposition(text)
            if deterministic is not None:
                logger.debug("[PARSER] Deterministic decomposition intents: %s", deterministic)
                return deterministic
        
        # 1. Normalize
        normalized = self.normalize_text(text)
        compound = self._parse_compound_app_search(text, normalized)
        if compound:
            for res in compound:
                self._enrich_desktop_metadata(res)
            logger.debug("[PARSER] Intents: %s", compound)
            return compound
        logger.info("[PARSER] Normalized: %r", normalized)

        # 2. Split by connectors: "ve", "sonra", "ardından", "and", "then"
        # Using word boundaries (\b) is critical to avoid splitting words like "venerated"
        connectors = r"\b(?:ve|sonra|ardından|and|then)\b"
        parts = [p.strip() for p in re.split(connectors, normalized, flags=re.IGNORECASE | re.UNICODE) if p.strip()]
        
        if not parts:
            return [self._unknown(text)]
            
        results = []
        for part in parts:
            results.append(self.parse_single(part))
        
        # 3. FORCE INTENT (CRITICAL FIX)
        results = self.force_app_intent(text, results)

        # 4. AI Fallback: ONLY if the entire command is unrecognized
        if all(r.intent == "unknown" for r in results):
            if get_settings().features.agent_loop and model_call_authorized:
                logger.info("[PARSER] Rule-based system could not identify ANY segment. Falling back to AI as last resort...")
                from aegis.intent.ai_parser import get_ai_parser
                ai_results = await get_ai_parser().parse(text, model_call_authorized=True)
                if ai_results:
                    results = ai_results
            else:
                logger.info(
                    "[PARSER] AI fallback disabled or not authorized; returning deterministic unknown intent."
                )
            
        # 5. FINAL SAFETY NET: Force-fix empty open_url or incorrectly routed apps
        # We do this at the very end to catch ANY escape from rule/AI logic
        for res in results:
            # If we have open_url with no params OR an unknown intent
            # AND the text contains a known app keyword, we force it
            is_empty_url = (res.intent == "open_url" and not res.params)
            is_unknown = (res.intent == "unknown")
            
            if is_empty_url or is_unknown:
                segment_text = self.normalize_text(str(res.raw_input or ""))
                if self._looks_like_search_command(segment_text):
                    continue
                for k in ["premiere", "photoshop", "notepad", "calc", "brave"]:
                    if k in segment_text:
                        logger.warning("[PARSER] Final safety override to open_app (%s)", k)
                        res.intent = "open_app"
                        res.params = {"app": k, "_app_known": True}
                        break

        # Tier 4 Enrichment: Inject Verification Metadata for deterministic tracking
        for res in results:
            self._enrich_desktop_metadata(res)

        # Keep mixed known/unknown plans intact. Dropping unknown segments would
        # execute only part of a user request and hide a planning gap.
        if any(r.intent == "unknown" for r in results) and any(r.intent != "unknown" for r in results):
            logger.debug("[PARSER] Intents: %s", results)
            return results

        # Filter out unknown segments if we have some known ones
        known_results = [r for r in results if r.intent != "unknown"]
        if known_results:
            logger.debug("[PARSER] Intents: %s", known_results)
            return known_results
            
        logger.debug("[PARSER] Intents: %s", results)
        return results

    def _parse_deterministic_decomposition(self, text: str) -> list[IntentResult] | None:
        plan = decompose_command(text)
        if plan is None:
            return None

        if plan.status != PlanStatus.READY.value:
            return [self._non_executable_decomposition_result(text, plan)]

        try:
            intents = normalized_plan_to_intents(plan, raw_text=text)
        except ValueError as exc:
            blocked = NormalizedPlan(
                plan_kind=plan.plan_kind,
                language=plan.language,
                source_text=plan.source_text,
                status=PlanStatus.BLOCKED.value,
                risk=plan.risk,
                steps=[],
                ambiguities=[],
                guard_notes=[str(exc)],
            )
            return [self._non_executable_decomposition_result(text, blocked)]

        for result in intents:
            self._enrich_desktop_metadata(result)
        return intents

    def _non_executable_decomposition_result(self, text: str, plan: NormalizedPlan) -> IntentResult:
        risk = RiskLevel.CRITICAL if plan.status == PlanStatus.APPROVAL_REQUIRED.value else RiskLevel.NONE
        return IntentResult(
            intent="unknown",
            confidence=0.0,
            params={},
            risk=risk,
            source=IntentSource.RULE,
            raw_input=text,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "decomposition": "deterministic",
                "plan_kind": plan.plan_kind,
                "plan_status": plan.status,
                "plan_risk": plan.risk,
                "ambiguities": list(plan.ambiguities),
                "guard_notes": list(plan.guard_notes),
            },
        )

    def _enrich_desktop_metadata(self, result: IntentResult) -> None:
        if result.intent not in {"open_app", "focus_app", "close_app"}:
            return
        app_id = result.params.get("app")
        if not app_id:
            return
        meta = VERIFICATION_METADATA.get(app_id)
        if meta:
            result.params["_process_name"] = meta["process_name"]
            result.params["_keywords"] = meta["keywords"]

    def _parse_compound_app_search(self, raw_text: str, normalized: str) -> list[IntentResult] | None:
        """Split common browser-open-and-search commands without relying on an LLM."""
        search_tail = r"(?:araması\s+yap|arama\s+yap|ara|search|bul|find|googlela|google['’]?la)"
        patterns = [
            rf"^(?P<app>[\w .&+\-]{{2,80}}?)(?:['’]?[ıiuüi])?\s+(?:açıp|acip|açip|aç|ac|open|launch|start)\s+(?P<query>.+?)\s+{search_tail}$",
            rf"^(?:aç|ac|open|launch|start)\s+(?P<app>[\w .&+\-]{{2,80}}?)\s+(?:ve|sonra|and|then)\s+(?P<query>.+?)\s+{search_tail}$",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE | re.UNICODE)
            if not match:
                continue
            app_raw = match.group("app").strip(" '’")
            query = match.group("query").strip()
            app_id = self.normalize_app_name(app_raw) or resolve_app_name(app_raw)
            if not app_id or not query:
                continue
            timestamp = datetime.now(timezone.utc)
            return [
                IntentResult(
                    intent="open_app",
                    confidence=1.0,
                    params={"app": app_id, "_app_known": True},
                    risk=RiskLevel.MEDIUM,
                    source=IntentSource.RULE,
                    raw_input=raw_text,
                    timestamp=timestamp,
                    metadata={"decomposition": "compound_app_search", "segment": "open_app"},
                ),
                IntentResult(
                    intent="search_web",
                    confidence=1.0,
                    params={"query": query, "browser": app_id},
                    risk=RiskLevel.LOW,
                    source=IntentSource.RULE,
                    raw_input=raw_text,
                    timestamp=timestamp,
                    metadata={"decomposition": "compound_app_search", "segment": "search_web"},
                ),
            ]
        return None

    def force_app_intent(self, text: str, intents: list[IntentResult]) -> list[IntentResult]:
        """Emergency override to prevent open_url logic for known apps."""
        APP_KEYWORDS = [
            "notepad", "calc", "hesap makinesi", "not defteri",
            "premiere", "photoshop", "adobe", "premier",
            "chrome", "brave", "edge", "firefox", "antigravity"
        ]

        norm_text = self.normalize_text(text)
        if self._looks_like_search_command(norm_text):
            return intents
        has_app_keyword = any(k in norm_text for k in APP_KEYWORDS)
        has_open_verb = any(v in norm_text for v in ["aç", "open", "başlat", "launch"])
        
        if has_app_keyword and has_open_verb:
            # If we only have 'unknown' or 'open_url' results, this is where it usually fails
            if all(i.intent in ["unknown", "open_url"] for i in intents):
                matched_app = next((k for k in APP_KEYWORDS if k in norm_text), "unknown")
                logger.info("[PARSER] FORCE LOCK: Overriding suspect intents with open_app(%s)", matched_app)
                return [IntentResult(
                    intent="open_app",
                    confidence=1.0,
                    params={"app": matched_app, "_app_known": True},
                    source=IntentSource.RULE,
                    raw_input=text
                )]
        return intents

    def _looks_like_search_command(self, text: str) -> bool:
        lowered = text.lower()
        markers = (
            " ara",
            " arat",
            " arama yap",
            " aramasÄ± yap",
            " diye arat",
            " search",
            " find",
            " googlela",
        )
        return any(marker in lowered for marker in markers)

    def parse_single(self, text: str) -> IntentResult:
        """Parse a single command segment into a structured IntentResult."""
        text = text.strip()
        if not text:
            return self._unknown(text)

        for rule, patterns in self._compiled:
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    params = self._extract_params(rule, match)
                    risk = rule.risk
                    if rule.intent == "git_action":
                        git_cmd = str(params.get("git_cmd", "")).lower().strip()
                        risk = RiskLevel.LOW if git_cmd == "status" else RiskLevel.CRITICAL
                    if rule.intent in {"write_file", "create_file", "edit_file"}:
                        write_path = _resolve_write_path(str(params.get("path", "")))
                        if _is_forbidden_write_path(write_path) or not _is_allowed_write_path(write_path):
                            risk = RiskLevel.CRITICAL
                    if rule.intent in {"delete_file", "move_file"}:
                        risk = RiskLevel.CRITICAL
                    if rule.intent == "run_command":
                        command = str(params.get("command", ""))
                        if is_destructive_shell_command(command) or not is_allowlisted_shell_command(command):
                            risk = RiskLevel.CRITICAL
                    result = IntentResult(
                        intent=rule.intent,
                        confidence=1.0,
                        params=params,
                        risk=risk,
                        source=IntentSource.RULE,
                        raw_input=text,
                        timestamp=datetime.now(timezone.utc),
                        metadata={"matched_pattern": pattern.pattern},
                    )
                    logger.info("Sub-intent parsed: %s (params=%s)", rule.intent, params)
                    return result

        logger.info("No rule matched for segment: %r → unknown", text)
        return self._unknown(text)

    def _extract_params(self, rule: IntentRule, match: re.Match[str]) -> dict[str, Any]:
        """Extract structured parameters from regex match groups."""
        params: dict[str, Any] = {}
        groups = match.groupdict()

        # URL
        if "url" in groups and groups["url"]:
            params["url"] = groups["url"]

        # Well-known site → resolve to URL
        if "site" in groups and groups["site"]:
            site = groups["site"].lower()
            params["site"] = site
            params["url"] = KNOWN_SITES.get(site, f"https://www.{site}.com")

        # File path
        if "path" in groups and groups["path"]:
            params["path"] = groups["path"]

        # Search query
        if "query" in groups and groups["query"]:
            params["query"] = groups["query"].strip()

        # Click coordinates
        if "x" in groups and groups["x"]:
            params["x"] = int(groups["x"])
        if "y" in groups and groups["y"]:
            params["y"] = int(groups["y"])

        # Click count
        if "count" in groups and groups["count"]:
            params["count"] = int(groups["count"])
        elif rule.intent == "click":
            params["count"] = 1  # default: single click

        # Text for typing
        if "text" in groups and groups["text"]:
            params["text"] = groups["text"].strip()

        # File content for write_file
        if "content" in groups and groups["content"]:
            params["content"] = groups["content"].strip()
        
        # Target window title
        if "window" in groups and groups["window"]:
            window_raw = groups["window"].strip()
            # Try to normalize window name too (e.g. "not defteri" -> "notepad")
            normalized_win = self.normalize_app_name(window_raw)
            params["window"] = normalized_win if normalized_win else window_raw
            
        # Target application name
        if "app" in groups and groups["app"]:
            app_raw = groups["app"].strip()
            normalized_app = self.normalize_app_name(app_raw)
            params["app"] = normalized_app if normalized_app else app_raw
            params["_app_known"] = bool(normalized_app or resolve_app_name(app_raw))
            logger.info("[PARSER] Detected app: %s -> %s", app_raw, params["app"])

        # Git command
        if "git_cmd" in groups and groups["git_cmd"]:
            params["git_cmd"] = groups["git_cmd"].strip()

        # Shell command
        if "command" in groups and groups["command"]:
            params["command"] = groups["command"].strip()

        # Destination path
        if "destination" in groups and groups["destination"]:
            params["destination"] = groups["destination"].strip()

        # Exact edit target/replacement
        if "target" in groups and groups["target"]:
            params["target"] = groups["target"].strip()
        if "replacement" in groups and groups["replacement"]:
            params["replacement"] = groups["replacement"].strip()

        return params

    def _unknown(self, text: str) -> IntentResult:
        """Unknown intent — no guessing, no random action."""
        return IntentResult(
            intent="unknown",
            confidence=0.0,
            params={},
            risk=RiskLevel.NONE,
            source=IntentSource.RULE,
            raw_input=text,
            timestamp=datetime.now(timezone.utc),
        )


# Singleton
_parser: IntentParser | None = None


def get_parser() -> IntentParser:
    global _parser
    if _parser is None:
        _parser = IntentParser()
    return _parser
