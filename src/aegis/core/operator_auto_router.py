from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from aegis.core.capability_broker import build_capability_assessment


CONTRACT_NAME = "aegis-operator-auto-router-preview"
ROUTER_MODE = "deterministic_preview"
PREVIEW_STATUS = "preview_only"
EMPTY_STATUS = "blocked_by_empty_request"
PERMISSION_MODE = "safe_preview"

INTENT_ASK_STATUS = "ask_status"
INTENT_SAFE_PLAN = "safe_plan"
INTENT_CODE_PROMPT = "code_prompt"
INTENT_MEMORY_ACTION = "memory_action"
INTENT_MODEL_HUB = "model_hub"
INTENT_VISION_REVIEW = "vision_review"
INTENT_WEB_RESEARCH = "web_research"
INTENT_COMMAND_PREVIEW = "command_preview"
INTENT_APPROVAL_REVIEW = "approval_review"
INTENT_UNKNOWN = "unknown"

NO_ACTION_FLAGS: dict[str, bool] = {
    "command_execution_performed": False,
    "model_call_performed": False,
    "local_model_call_performed": False,
    "cloud_call_performed": False,
    "external_provider_call_performed": False,
    "kimi_moonshot_call_performed": False,
    "image_upload_performed": False,
    "video_upload_performed": False,
    "memory_write_performed": False,
    "tool_call_performed": False,
    "mcp_call_performed": False,
    "browser_action_performed": False,
    "shell_command_performed": False,
    "file_mutation_performed": False,
    "evidence_created": False,
    "verifier_success": False,
    "approval_granted": False,
    "permission_granted": False,
    "capability_lease_granted": False,
    "authority": False,
    "frontend_authority": False,
    "model_output_is_truth": False,
    "data_sent_external": False,
    "prompt_payload_sent_external": False,
    "output_is_evidence": False,
    "output_is_verifier_success": False,
    "output_authority": False,
}

SAFETY_FLAGS: tuple[str, ...] = (
    "no_command_execution",
    "no_model_call",
    "no_cloud_call",
    "no_external_provider_call",
    "no_kimi_moonshot_call",
    "no_image_upload",
    "no_video_upload",
    "no_memory_write",
    "no_tool_call",
    "no_evidence",
    "no_verifier_success",
    "no_approval_or_permission_grant",
)

MODEL_CANDIDATES = {
    "default_proposal": "google/gemma-4-12b",
    "fast_summary": "qwen/qwen3.5-9b",
    "coding_review": "qwen2.5-coder-14b-instruct",
    "reasoning_review": "deepseek-r1-distill-qwen-14b",
    "vision_review": "qwen/qwen3-vl-8b",
    "rerank_only": "qwen3-reranker-0.6b",
    "external_cloud_candidate": "moonshot/kimi-k2.7-code (disabled external metadata only)",
}

TRACE_STEPS: tuple[str, ...] = (
    "request_received",
    "intent_preview_generated",
    "route_selected",
    "model_candidate_selected",
    "permission_boundary_evaluated",
    "cloud_boundary_evaluated",
    "memory_policy_evaluated",
    "artifact_draft_created",
    "blocked_actions_not_performed",
)

KEYWORDS: dict[str, tuple[str, ...]] = {
    INTENT_VISION_REVIEW: (
        "screenshot",
        "image",
        "visual",
        "vision",
        "gorsel",
        "ekran goruntusu",
        "ui bozuk",
        "ui sorunu",
        "ui issue",
        "arayuz",
    ),
    INTENT_CODE_PROMPT: (
        "codex prompt",
        "kod",
        "code",
        "diff",
        "test",
        "pr",
        "repo",
        "patch",
    ),
    INTENT_MEMORY_ACTION: (
        "hatirla",
        "unut",
        "hafiza",
        "memory",
        "remember",
        "forget",
    ),
    INTENT_WEB_RESEARCH: (
        "web",
        "arastir",
        "internet",
        "kaynak",
        "source",
        "research",
    ),
    INTENT_MODEL_HUB: (
        "model",
        "lm studio",
        "qwen",
        "gemma",
        "deepseek",
        "openrouter",
        "moonshot",
        "kimi",
        "model hub",
    ),
    INTENT_COMMAND_PREVIEW: (
        "komut",
        "calistir",
        "execute",
        "shell",
        "terminal",
        "run ",
    ),
    INTENT_APPROVAL_REVIEW: (
        "onay",
        "approval",
        "approve",
        "permission",
        "izin",
    ),
    INTENT_SAFE_PLAN: (
        "plan",
        "sprint",
        "next step",
        "sonraki",
        "safe",
        "guvenli",
    ),
    INTENT_ASK_STATUS: (
        "status",
        "durum",
        "health",
        "nedir",
        "explain",
        "acikla",
    ),
}


def build_operator_route_preview(request: str) -> dict[str, Any]:
    """Build a deterministic preview-only operator routing envelope."""
    raw_request = request if isinstance(request, str) else ""
    display_request = redact_sensitive_markers(raw_request.strip())
    normalized = normalize_request(raw_request)
    status = PREVIEW_STATUS if normalized else EMPTY_STATUS
    intents = classify_operator_intents(normalized)
    primary_intent = choose_primary_intent(intents)
    route_id = choose_route_id(intents, primary_intent)
    preview_id = stable_preview_id(f"{route_id}:{normalized or 'empty'}")
    model_candidates = choose_model_candidates(intents, primary_intent, normalized)
    approval_needed = primary_intent in {INTENT_COMMAND_PREVIEW, INTENT_APPROVAL_REVIEW}
    memory_action_proposed = INTENT_MEMORY_ACTION in intents
    vision_boundary_required = INTENT_VISION_REVIEW in intents
    research_boundary_required = INTENT_WEB_RESEARCH in intents
    artifact = build_artifact(
        preview_id=preview_id,
        route_id=route_id,
        request=display_request,
        status=status,
    )

    preview = {
        "contract": CONTRACT_NAME,
        "status": status,
        "router_mode": ROUTER_MODE,
        "request": display_request,
        "preview_id": preview_id,
        "request_id": preview_id,
        "intents": intents,
        "primary_intent": primary_intent,
        "route_id": route_id,
        "model_candidates": model_candidates,
        "permission_mode": PERMISSION_MODE,
        "cloud_needed": False,
        "approval_needed": approval_needed,
        "memory_action_proposed": memory_action_proposed,
        "vision_boundary_required": vision_boundary_required,
        "research_boundary_required": research_boundary_required,
        "artifact": artifact,
        "trace_items": build_trace_items(
            preview_id=preview_id,
            status=status,
            route_id=route_id,
            model_candidates=model_candidates,
            approval_needed=approval_needed,
            memory_action_proposed=memory_action_proposed,
            research_boundary_required=research_boundary_required,
        ),
        "proposal_only": True,
        "requires_backend_owned_policy_before_execution": True,
        "process_trace_is_summary_not_hidden_reasoning": True,
        "cloud_fallback_allowed": False,
        "external_cloud_candidate_disabled": includes_external_provider_reference(normalized),
        **NO_ACTION_FLAGS,
    }
    return {
        **preview,
        "capability_assessment": build_capability_assessment(display_request, preview),
    }


def classify_operator_intents(normalized_request: str) -> list[str]:
    if not normalized_request:
        return [INTENT_UNKNOWN]
    intents: list[str] = []
    for intent, keywords in KEYWORDS.items():
        if matches_intent(normalized_request, intent, keywords):
            intents.append(intent)
    return intents or [INTENT_ASK_STATUS]


def matches_intent(normalized_request: str, intent: str, keywords: tuple[str, ...]) -> bool:
    if intent == INTENT_CODE_PROMPT:
        regular_keywords = tuple(keyword for keyword in keywords if keyword != "pr")
        return (
            any(keyword in normalized_request for keyword in regular_keywords)
            or re.search(r"(^|\s)pr($|\s)", normalized_request) is not None
        )
    return any(keyword in normalized_request for keyword in keywords)


def choose_primary_intent(intents: list[str]) -> str:
    priority = (
        INTENT_COMMAND_PREVIEW,
        INTENT_VISION_REVIEW,
        INTENT_MEMORY_ACTION,
        INTENT_WEB_RESEARCH,
        INTENT_MODEL_HUB,
        INTENT_CODE_PROMPT,
        INTENT_APPROVAL_REVIEW,
        INTENT_SAFE_PLAN,
        INTENT_ASK_STATUS,
        INTENT_UNKNOWN,
    )
    return next((intent for intent in priority if intent in intents), INTENT_UNKNOWN)


def choose_route_id(intents: list[str], primary_intent: str) -> str:
    if INTENT_VISION_REVIEW in intents and INTENT_CODE_PROMPT in intents:
        return "vision_to_code_prompt"
    if primary_intent == INTENT_VISION_REVIEW:
        return "vision_review_plan"
    if primary_intent == INTENT_MEMORY_ACTION:
        return "memory_policy_preview"
    if primary_intent == INTENT_WEB_RESEARCH:
        return "research_plan"
    if primary_intent == INTENT_MODEL_HUB:
        return "model_hub_review"
    if primary_intent == INTENT_CODE_PROMPT:
        return "code_prompt_builder"
    if primary_intent == INTENT_COMMAND_PREVIEW:
        return "command_approval_preview"
    if primary_intent == INTENT_APPROVAL_REVIEW:
        return "approval_review"
    if primary_intent == INTENT_SAFE_PLAN:
        return "safe_plan_builder"
    return "status_explainer"


def choose_model_candidates(
    intents: list[str],
    primary_intent: str,
    normalized_request: str,
) -> list[dict[str, str]]:
    candidate_ids: list[str] = []
    if INTENT_VISION_REVIEW in intents:
        candidate_ids.append("vision_review")
    if INTENT_CODE_PROMPT in intents:
        candidate_ids.append("coding_review")
    if INTENT_WEB_RESEARCH in intents:
        candidate_ids.append("rerank_only")
    if primary_intent in {INTENT_SAFE_PLAN, INTENT_APPROVAL_REVIEW, INTENT_COMMAND_PREVIEW}:
        candidate_ids.append("reasoning_review")
    if primary_intent == INTENT_ASK_STATUS:
        candidate_ids.append("fast_summary")
    if includes_external_provider_reference(normalized_request):
        candidate_ids.append("external_cloud_candidate")
    if not candidate_ids:
        candidate_ids.append("default_proposal")

    unique_ids = list(dict.fromkeys(candidate_ids))
    return [
        {
            "profile_id": profile_id,
            "model_hint": MODEL_CANDIDATES[profile_id],
            "selected_for_call": False,
            "proposal_only": True,
        }
        for profile_id in unique_ids
    ]


def build_trace_items(
    *,
    preview_id: str,
    status: str,
    route_id: str,
    model_candidates: list[dict[str, str]],
    approval_needed: bool,
    memory_action_proposed: bool,
    research_boundary_required: bool,
) -> list[dict[str, str]]:
    details = {
        "request_received": "Request text was received for deterministic preview only.",
        "intent_preview_generated": "Keyword classifier produced non-authoritative intent metadata.",
        "route_selected": f"Preview route selected: {route_id}.",
        "model_candidate_selected": "Model candidates listed as proposal metadata; no model was called.",
        "permission_boundary_evaluated": (
            "Execution-like request remains blocked until backend policy and approval gates."
            if approval_needed else
            "Safe preview grants no execution permission."
        ),
        "cloud_boundary_evaluated": (
            "External research or cloud candidate remains future-gated and no data was sent."
            if research_boundary_required else
            "No cloud provider was selected or called."
        ),
        "memory_policy_evaluated": (
            "Memory action is a lifecycle proposal only; no write occurred."
            if memory_action_proposed else
            "No memory write was requested or performed."
        ),
        "artifact_draft_created": "Preview artifact metadata was created for UI display only.",
        "blocked_actions_not_performed": (
            "No command, model, provider, memory, tool, browser, evidence, verifier, approval, or permission action occurred."
        ),
    }
    statuses = {
        "request_received": "done" if status == PREVIEW_STATUS else "blocked",
        "intent_preview_generated": "done" if status == PREVIEW_STATUS else "blocked",
        "route_selected": "done" if status == PREVIEW_STATUS else "blocked",
        "model_candidate_selected": "info" if model_candidates else "waiting",
        "permission_boundary_evaluated": "blocked" if approval_needed else "done",
        "cloud_boundary_evaluated": "blocked" if research_boundary_required else "done",
        "memory_policy_evaluated": "blocked" if memory_action_proposed else "done",
        "artifact_draft_created": "done" if status == PREVIEW_STATUS else "blocked",
        "blocked_actions_not_performed": "blocked",
    }
    return [
        {
            "id": f"{preview_id}-{step}",
            "step": step,
            "status": statuses[step],
            "detail": details[step],
        }
        for step in TRACE_STEPS
    ]


def build_artifact(*, preview_id: str, route_id: str, request: str, status: str) -> dict[str, Any]:
    artifact_type_by_route = {
        "status_explainer": "safe_plan_draft",
        "safe_plan_builder": "safe_plan_draft",
        "code_prompt_builder": "codex_prompt_draft",
        "memory_policy_preview": "memory_action_preview",
        "model_hub_review": "model_routing_summary",
        "vision_review_plan": "ui_review_plan",
        "vision_to_code_prompt": "codex_prompt_draft",
        "research_plan": "research_plan",
        "command_approval_preview": "command_approval_preview",
        "approval_review": "command_approval_preview",
    }
    artifact_type = artifact_type_by_route[route_id]
    return {
        "id": f"{preview_id}-artifact",
        "type": artifact_type,
        "status": "preview_only" if status == PREVIEW_STATUS else "blocked_preview",
        "title": title_for_artifact(artifact_type),
        "request": request,
        "summary": summary_for_artifact(artifact_type),
        "safety_flags": SAFETY_FLAGS,
    }


def title_for_artifact(artifact_type: str) -> str:
    return artifact_type.replace("_", " ").title()


def summary_for_artifact(artifact_type: str) -> str:
    summaries = {
        "safe_plan_draft": "Bounded plan preview with explicit validation and no execution.",
        "codex_prompt_draft": "Draft handoff prompt metadata; not a patch or execution result.",
        "ui_review_plan": "UI review preview that requires a future vision boundary for images.",
        "research_plan": "Research plan preview that requires a future external research boundary.",
        "memory_action_preview": "Memory lifecycle preview requiring explicit consent before any write.",
        "model_routing_summary": "Model routing metadata only; no local or external model was called.",
        "command_approval_preview": "Command safety preview blocked before backend policy and approval gates.",
    }
    return summaries[artifact_type]


def includes_external_provider_reference(normalized_request: str) -> bool:
    return any(keyword in normalized_request for keyword in ("kimi", "moonshot", "openrouter", "cloud"))


def normalize_request(request: str) -> str:
    lowered = request.casefold().replace("ı", "i")
    normalized = unicodedata.normalize("NFKD", lowered)
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", without_marks).strip()


def redact_sensitive_markers(value: str) -> str:
    return re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[redacted-secret-like-token]", value)


def stable_preview_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"operator-preview-{digest}"
