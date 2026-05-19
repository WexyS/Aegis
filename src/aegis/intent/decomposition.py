"""Normalized command decomposition contracts.

This module defines the plan shape and guard validation only. It is not wired to
the production parser or executor yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from aegis.core.constants import IntentSource, RiskLevel
from aegis.core.schemas import IntentResult
from aegis.intent.rules import APP_ALIASES


class PlanStatus(str, Enum):
    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


RiskName = Literal["none", "low", "medium", "high", "critical"]


VALID_RISKS = {"none", "low", "medium", "high", "critical"}

RISK_LEVEL_BY_NAME: dict[str, RiskLevel] = {
    "none": RiskLevel.NONE,
    "low": RiskLevel.LOW,
    "medium": RiskLevel.MEDIUM,
    "high": RiskLevel.HIGH,
    "critical": RiskLevel.CRITICAL,
}

ALLOWED_EXECUTABLE_INTENTS = {
    "open_app",
    "focus_app",
    "type",
    "open_url",
    "search_web",
}

BLOCKED_FUTURE_INTENTS = {
    "browser_click",
    "desktop_click",
}

REQUIRED_PARAMS: dict[str, set[str]] = {
    "open_app": {"app"},
    "focus_app": {"app"},
    "type": {"text"},
    "open_url": {"url"},
    "search_web": {"query"},
}


@dataclass(frozen=True)
class PrimitiveStep:
    intent: str
    params: dict[str, Any] = field(default_factory=dict)
    source_span: str = ""
    risk: str = "none"


@dataclass(frozen=True)
class NormalizedPlan:
    plan_kind: str
    language: str
    source_text: str
    status: str
    risk: str
    steps: list[PrimitiveStep] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    guard_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlanValidationResult:
    valid: bool
    status: PlanStatus | None
    plan: NormalizedPlan
    errors: list[str] = field(default_factory=list)
    guard_notes: list[str] = field(default_factory=list)


def _parse_status(value: str, errors: list[str]) -> PlanStatus | None:
    try:
        return PlanStatus(value)
    except ValueError:
        errors.append(f"invalid status: {value}")
        return None


def _validate_risk(value: str, errors: list[str], *, field_name: str) -> None:
    if value not in VALID_RISKS:
        errors.append(f"invalid risk for {field_name}: {value}")


def _validate_step(step: PrimitiveStep, errors: list[str]) -> None:
    _validate_risk(step.risk, errors, field_name=f"step {step.intent}")

    if step.intent == "click":
        errors.append("raw generic click intent is not executable; use target resolution first")
        return

    if step.intent in BLOCKED_FUTURE_INTENTS:
        errors.append(f"{step.intent} is blocked: target resolution is not implemented")
        return

    if step.intent not in ALLOWED_EXECUTABLE_INTENTS:
        errors.append(f"unknown intent: {step.intent}")
        return

    required = REQUIRED_PARAMS.get(step.intent, set())
    missing = sorted(name for name in required if not step.params.get(name))
    if missing:
        errors.append(f"missing required params for {step.intent}: {', '.join(missing)}")


def validate_normalized_plan(plan: NormalizedPlan, *, source: str = "rule") -> PlanValidationResult:
    """Validate a normalized decomposition plan without executing it."""

    errors: list[str] = []
    guard_notes = list(plan.guard_notes)

    if plan.plan_kind != "deterministic_decomposition":
        errors.append(f"invalid plan_kind: {plan.plan_kind}")

    status = _parse_status(plan.status, errors)
    _validate_risk(plan.risk, errors, field_name="plan")

    if status == PlanStatus.READY:
        if not plan.steps:
            errors.append("ready plan must contain at least one step")
        if plan.ambiguities:
            errors.append("ready plan cannot contain ambiguities")
    elif status in {PlanStatus.CLARIFICATION_REQUIRED, PlanStatus.APPROVAL_REQUIRED}:
        if not plan.ambiguities and not guard_notes:
            errors.append(f"{status.value} plan must explain why it cannot execute")

    for step in plan.steps:
        _validate_step(step, errors)

    if source == "llm" and errors:
        guard_notes.append("llm proposal rejected by normalized plan guard")

    return PlanValidationResult(
        valid=not errors,
        status=status,
        plan=plan,
        errors=errors,
        guard_notes=guard_notes,
    )


_TURKISH_OPEN_TYPE_PATTERNS = (
    re.compile(r"^\s*(?P<app>.+?)\s+açıp\s*(?P<text>.*?)\s+yaz\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?P<app>.+?)\s+aç\s+(?:ve|sonra)\s*(?P<text>.*?)\s+yaz\s*$", re.IGNORECASE),
)

_ENGLISH_OPEN_TYPE_PATTERNS = (
    re.compile(r"^\s*open\s+(?P<app>.+?)\s+(?:and|then)\s+type\s*(?P<text>.*?)\s*$", re.IGNORECASE),
)

_TURKISH_OPEN_SEARCH_PATTERNS = (
    re.compile(r"^\s*(?P<app>.+?)\s+açıp\s*(?P<query>.*?)\s+ara\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?P<app>.+?)\s+aç\s+(?:ve|sonra)\s*(?P<query>.*?)\s+ara\s*$", re.IGNORECASE),
)

_ENGLISH_OPEN_SEARCH_PATTERNS = (
    re.compile(r"^\s*open\s+(?P<app>.+?)\s+(?:and|then)\s+search\s*(?P<query>.*?)\s*$", re.IGNORECASE),
)


def _normalize_app_alias(value: str) -> str:
    text = value.strip().lower()
    replacements = {
        "not defterini": "not defteri",
        "not defterine": "not defteri",
        "not defteri'ni": "not defteri",
        "not defteri'ne": "not defteri",
        "notepad'i": "notepad",
        "notepad'ı": "notepad",
        "notepad e": "notepad",
        "notepad a": "notepad",
        "chrome'u": "chrome",
        "chrome'a": "chrome",
        "brave'i": "brave",
        "brave'ı": "brave",
        "brave i": "brave",
        "brave ı": "brave",
    }
    return replacements.get(text, text)


def _canonical_app(value: str) -> str | None:
    return APP_ALIASES.get(_normalize_app_alias(value))


def _clarification_plan(source_text: str, language: str, ambiguity: str) -> NormalizedPlan:
    return NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language=language,
        source_text=source_text,
        status=PlanStatus.CLARIFICATION_REQUIRED.value,
        risk="none",
        steps=[],
        ambiguities=[ambiguity],
        guard_notes=[],
    )


def _ready_open_type_plan(
    *,
    source_text: str,
    language: str,
    app: str,
    app_span: str,
    typed_text: str,
) -> NormalizedPlan:
    plan = NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language=language,
        source_text=source_text,
        status=PlanStatus.READY.value,
        risk="medium",
        steps=[
            PrimitiveStep(
                intent="open_app",
                params={"app": app},
                source_span=app_span,
                risk="medium",
            ),
            PrimitiveStep(
                intent="type",
                params={"text": typed_text, "_require_focus": app},
                source_span=typed_text,
                risk="medium",
            ),
        ],
        ambiguities=[],
        guard_notes=[],
    )
    validation = validate_normalized_plan(plan)
    if validation.valid:
        return plan
    return NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language=language,
        source_text=source_text,
        status=PlanStatus.BLOCKED.value,
        risk="medium",
        steps=[],
        ambiguities=[],
        guard_notes=validation.errors,
    )


def _ready_open_search_plan(
    *,
    source_text: str,
    language: str,
    app: str,
    app_span: str,
    query: str,
) -> NormalizedPlan:
    plan = NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language=language,
        source_text=source_text,
        status=PlanStatus.READY.value,
        risk="medium",
        steps=[
            PrimitiveStep(
                intent="open_app",
                params={"app": app},
                source_span=app_span,
                risk="medium",
            ),
            PrimitiveStep(
                intent="search_web",
                params={"query": query, "browser": app},
                source_span=query,
                risk="low",
            ),
        ],
        ambiguities=[],
        guard_notes=[],
    )
    validation = validate_normalized_plan(plan)
    if validation.valid:
        return plan
    return NormalizedPlan(
        plan_kind="deterministic_decomposition",
        language=language,
        source_text=source_text,
        status=PlanStatus.BLOCKED.value,
        risk="medium",
        steps=[],
        ambiguities=[],
        guard_notes=validation.errors,
    )


def decompose_open_type(text: str) -> NormalizedPlan | None:
    """Decompose high-confidence open-app + type commands without executing them."""

    source_text = text
    for pattern in _TURKISH_OPEN_TYPE_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        app_span = match.group("app").strip()
        typed_text = match.group("text").strip()
        app = _canonical_app(app_span)
        if not app:
            return _clarification_plan(source_text, "tr", f"unknown app for open+type: {app_span}")
        if not typed_text:
            return _clarification_plan(source_text, "tr", "missing text for type step")
        return _ready_open_type_plan(
            source_text=source_text,
            language="tr",
            app=app,
            app_span=app_span,
            typed_text=typed_text,
        )

    for pattern in _ENGLISH_OPEN_TYPE_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        app_span = match.group("app").strip()
        typed_text = match.group("text").strip()
        app = _canonical_app(app_span)
        if not app:
            return _clarification_plan(source_text, "en", f"unknown app for open+type: {app_span}")
        if not typed_text:
            return _clarification_plan(source_text, "en", "missing text for type step")
        return _ready_open_type_plan(
            source_text=source_text,
            language="en",
            app=app,
            app_span=app_span,
            typed_text=typed_text,
        )

    return None


def decompose_open_search(text: str) -> NormalizedPlan | None:
    """Decompose high-confidence open-app + search commands without executing them."""

    source_text = text
    for pattern in _TURKISH_OPEN_SEARCH_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        app_span = match.group("app").strip()
        query = match.group("query").strip()
        app = _canonical_app(app_span)
        if not app:
            return _clarification_plan(source_text, "tr", f"unknown app for open+search: {app_span}")
        if not query:
            return _clarification_plan(source_text, "tr", "missing query for search_web step")
        return _ready_open_search_plan(
            source_text=source_text,
            language="tr",
            app=app,
            app_span=app_span,
            query=query,
        )

    for pattern in _ENGLISH_OPEN_SEARCH_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        app_span = match.group("app").strip()
        query = match.group("query").strip()
        app = _canonical_app(app_span)
        if not app:
            return _clarification_plan(source_text, "en", f"unknown app for open+search: {app_span}")
        if not query:
            return _clarification_plan(source_text, "en", "missing query for search_web step")
        return _ready_open_search_plan(
            source_text=source_text,
            language="en",
            app=app,
            app_span=app_span,
            query=query,
        )

    return None


def decompose_command(text: str) -> NormalizedPlan | None:
    """Try deterministic decomposers in a stable safe order."""

    lowered = text.strip().lower()
    click_tokens = ("click", "tıkla", "tikla", "tÄ±kla")
    unresolved_targets = ("that", "button", "buton", "ilk", "sonuca", "bu ", "şu ", "su ")
    if any(token in lowered for token in click_tokens) and any(target in lowered for target in unresolved_targets):
        return _clarification_plan(text, "unknown", "click target resolution is not implemented")

    for decomposer in (decompose_open_type, decompose_open_search):
        plan = decomposer(text)
        if plan is None:
            continue

        validation = validate_normalized_plan(plan)
        if validation.valid:
            return plan

        return NormalizedPlan(
            plan_kind="deterministic_decomposition",
            language=plan.language,
            source_text=plan.source_text,
            status=PlanStatus.BLOCKED.value,
            risk=plan.risk,
            steps=[],
            ambiguities=[],
            guard_notes=validation.errors,
        )

    return None


def normalized_plan_to_intents(plan: NormalizedPlan, *, raw_text: str) -> list[IntentResult]:
    """Adapt a validated ready normalized plan to existing parser output."""

    validation = validate_normalized_plan(plan)
    if not validation.valid:
        raise ValueError(f"invalid normalized plan: {'; '.join(validation.errors)}")

    if validation.status != PlanStatus.READY:
        raise ValueError(f"cannot adapt non-ready normalized plan: {plan.status}")

    intents: list[IntentResult] = []
    step_count = len(plan.steps)
    for index, step in enumerate(plan.steps):
        risk = RISK_LEVEL_BY_NAME.get(step.risk)
        if risk is None:
            raise ValueError(f"invalid normalized plan risk: {step.risk}")

        intents.append(
            IntentResult(
                intent=step.intent,
                confidence=1.0,
                params=dict(step.params),
                risk=risk,
                source=IntentSource.RULE,
                raw_input=raw_text,
                metadata={
                    "decomposition": "deterministic",
                    "plan_kind": plan.plan_kind,
                    "plan_status": plan.status,
                    "plan_risk": plan.risk,
                    "step_index": index,
                    "step_count": step_count,
                    "source_span": step.source_span,
                    "guard_notes": list(plan.guard_notes),
                    "ambiguities": list(plan.ambiguities),
                },
            )
        )

    return intents
