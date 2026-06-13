from __future__ import annotations

import unicodedata
from copy import deepcopy
from typing import Any, Mapping


ASK_EXECUTION_PERMISSION = "not_granted_by_aegis_ask"

ASK_INTENTS = {
    "system_status",
    "runtime_health_explanation",
    "capability_summary",
    "skill_registry_question",
    "tool_registry_question",
    "plugin_question",
    "model_gateway_question",
    "memory_question",
    "autopilot_question",
    "policy_or_safety_question",
    "next_step_planning",
    "unsupported_or_risky",
}

NON_AUTHORITY_FALSE_FIELDS = {
    "memory_written",
    "execution_performed",
    "evidence_created",
    "verifier_success",
    "approval_granted",
    "capability_lease_granted",
    "tool_execution_performed",
    "plugin_execution_performed",
    "agent_execution_performed",
}


def route_ask_intent(question: str, requested_intent: str | None = None) -> str:
    """Classify an Ask question with a deterministic, local-only router."""

    if requested_intent:
        normalized_intent = str(requested_intent).strip()
        if normalized_intent in ASK_INTENTS:
            return normalized_intent

    text = _normalize_text(question)
    words = set(text.split())

    if _looks_like_execution_request(text, words):
        return "unsupported_or_risky"
    if _has_any(text, ("siradaki", "next step", "safe next", "guvenli adim", "ne yapmaliyim")):
        return "next_step_planning"
    if _has_any(text, ("skill", "registry", "calistirilabilir", "yetenek")):
        return "skill_registry_question"
    if _has_any(text, ("tool", "arac", "tools", "registry")):
        return "tool_registry_question"
    if _has_any(text, ("plugin", "manifest", "mcp", "connector")):
        return "plugin_question"
    if _has_any(text, ("model gateway", "lm studio", "local model", "model acik", "model aktif")):
        return "model_gateway_question"
    if _has_any(text, ("memory", "hafiza", "bellek")):
        return "memory_question"
    if _has_any(text, ("autopilot", "repo scan", "repo audit", "read only scan")):
        return "autopilot_question"
    if _has_any(text, ("policy", "safety", "guvenlik", "approval", "evidence", "verifier", "lease")):
        return "policy_or_safety_question"
    if _has_any(text, ("warning", "uyari", "blocker", "historical debt", "active blocker", "raw fail")):
        return "runtime_health_explanation"
    if _has_any(text, ("ne durumda", "su an", "durum", "status", "health", "ne yapabilir", "ne yapamaz")):
        return "system_status"
    return "capability_summary"


def build_ask_response(
    request: Mapping[str, Any],
    *,
    maintenance_scan: Mapping[str, Any] | None = None,
    skill_catalog: Mapping[str, Any] | None = None,
    tool_registry_snapshot: Mapping[str, Any] | None = None,
    model_gateway_status: Mapping[str, Any] | None = None,
    memory_search_result: Mapping[str, Any] | None = None,
    autopilot_report: Mapping[str, Any] | None = None,
    agent_profile_catalog: Mapping[str, Any] | None = None,
    plugin_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only Aegis Ask response envelope.

    The helper is deterministic and non-dispatching. It does not execute
    commands, run tools, call models, write memory, create evidence, or grant
    approval/capability/lease permission.
    """

    question = _required_question(request)
    max_sources = _safe_max_sources(request.get("max_sources"))
    intent = route_ask_intent(question, _optional_text(request.get("intent")))
    include_memory = request.get("include_memory") is True
    include_model_polish = request.get("include_model_polish") is True
    include_autopilot = request.get("include_autopilot") is True
    include_agent_proposal = request.get("include_agent_proposal") is True

    maintenance = deepcopy(dict(maintenance_scan or {}))
    skills = deepcopy(dict(skill_catalog or {}))
    tools = deepcopy(dict(tool_registry_snapshot or {}))
    model_status = deepcopy(dict(model_gateway_status or {}))
    memory_result = deepcopy(dict(memory_search_result or {}))
    autopilot = deepcopy(dict(autopilot_report or {}))
    agents = deepcopy(dict(agent_profile_catalog or {}))
    plugins = deepcopy(dict(plugin_summary or {}))

    runtime_summary = _runtime_health_summary(maintenance)
    sources = _source_refs(
        max_sources=max_sources,
        maintenance=maintenance,
        skills=skills,
        tools=tools,
        model_status=model_status,
        memory_result=memory_result if include_memory else {},
        autopilot=autopilot if include_autopilot else {},
        agents=agents if include_agent_proposal else {},
        plugins=plugins,
    )
    known: list[str] = []
    unknown: list[str] = []
    limitations: list[str] = [
        "Ask is read-only and explanation-only in this product slice.",
        "Ask does not execute commands, tools, plugins, agents, or MCP connectors.",
        "Ask does not create evidence, verifier success, approvals, capabilities, or leases.",
    ]

    if not maintenance:
        unknown.append("No maintenance scan projection was supplied to Ask.")
    if include_model_polish:
        limitations.append("Model polish was requested but not performed in this first Ask slice.")
    if include_memory:
        if memory_result:
            known.append(_memory_known(memory_result))
            limitations.append("Memory retrieval is context only and not authority.")
        else:
            limitations.append("Memory was requested, but Ask did not perform a MemoryStore read without a supplied safe read-only result.")
            unknown.append("Memory search result was not supplied.")
    if include_autopilot:
        if autopilot:
            known.append(_autopilot_known(autopilot))
            limitations.append("AutoPilot reports are read-only candidate reports, not evidence.")
        else:
            limitations.append("AutoPilot was requested, but Ask did not run a repo scan in this slice.")
            unknown.append("AutoPilot report was not supplied.")
    if include_agent_proposal:
        if agents:
            known.append(_agent_known(agents))
            limitations.append("Agent Runtime metadata is proposal-only and not the Ask engine.")
        else:
            limitations.append("Agent proposal metadata was requested but no catalog was supplied.")

    answer, intent_known, intent_unknown, next_steps = _answer_for_intent(
        intent,
        runtime_summary=runtime_summary,
        skills=skills,
        tools=tools,
        model_status=model_status,
        plugins=plugins,
        agents=agents,
    )
    known.extend(intent_known)
    unknown.extend(intent_unknown)

    return {
        "answer": answer,
        "intent": intent,
        "source_refs": sources,
        "known": _unique(known),
        "unknown": _unique(unknown),
        "limitations": _unique(limitations),
        "recommended_next_steps": next_steps,
        "non_authority_flags": _non_authority_flags(),
        "runtime_health_summary": runtime_summary,
        "model_used": None,
        "memory_written": False,
        "execution_performed": False,
        "evidence_created": False,
        "verifier_success": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "tool_execution_performed": False,
        "plugin_execution_performed": False,
        "agent_execution_performed": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": ASK_EXECUTION_PERMISSION,
    }


def _answer_for_intent(
    intent: str,
    *,
    runtime_summary: Mapping[str, Any],
    skills: Mapping[str, Any],
    tools: Mapping[str, Any],
    model_status: Mapping[str, Any],
    plugins: Mapping[str, Any],
    agents: Mapping[str, Any],
) -> tuple[str, list[str], list[str], list[str]]:
    known: list[str] = []
    unknown: list[str] = []
    next_steps = [
        "Use Ask for read-only explanation and next-step planning.",
        "Use the command/runtime flow only for explicitly approved execution tasks.",
    ]

    if intent == "unsupported_or_risky":
        return (
            "Ask cannot execute or mutate anything. This request looks like an action, so it was kept in a safe explanation-only path.",
            known,
            ["No execution path was selected."],
            [
                "Ask a read-only question, or use the explicit runtime command flow for approval-gated actions.",
                "Do not treat this Ask response as approval or execution permission.",
            ],
        )

    if intent in {"system_status", "runtime_health_explanation"}:
        status = runtime_summary.get("status") or "unknown"
        blockers = runtime_summary.get("current_blocker_count", "unknown")
        active_failures = runtime_summary.get("active_failure_components") or []
        raw = runtime_summary.get("raw_component_statuses") or {}
        known.append(f"Runtime health projection status is {status}.")
        known.append(f"Current operational blocker count is {blockers}.")
        if active_failures:
            known.append(f"Active failure components: {', '.join(map(str, active_failures))}.")
        else:
            known.append("No active failure components are reported by the current projection.")
        known.append("Raw evidence/replay failures remain visible separately from active projection status.")
        return (
            "Aegis is not fully green: the current projection is warning-level, with current blockers clear, while raw historical evidence/replay debt remains visible.",
            known,
            unknown,
            [
                "Keep raw historical debt visible; do not reclassify it as success.",
                "Continue with controlled product slices that preserve read-only/proposal-only boundaries.",
            ],
        )

    if intent == "skill_registry_question":
        skill_count = skills.get("skill_count", "unknown")
        names = _named_items(skills.get("skills"), "skill_id", limit=8)
        known.append(f"Skill Registry lists {skill_count} skills.")
        if names:
            known.append(f"Known skill ids include: {', '.join(names)}.")
        known.append("Skill Registry metadata does not grant skill execution permission.")
        return (
            "The Skill Registry is a catalog/introspection surface. It can explain known skills, but it cannot run them or grant permission.",
            known,
            unknown,
            ["Use Ask to inspect skill status; add a separate approval-gated execution sprint before any skill can run."],
        )

    if intent == "tool_registry_question":
        registered = tools.get("registered_count", "unknown")
        configured = tools.get("configured_count", "unknown")
        known.append(f"Tool Registry reports {registered} registered tools and {configured} configured tools.")
        known.append("Ask reads registry metadata only and does not call tools.")
        return (
            "The Tool Registry can be summarized, but Ask does not execute tools or convert availability into permission.",
            known,
            unknown,
            ["Inspect tool metadata first; use the runtime approval path for any future tool execution."],
        )

    if intent == "plugin_question":
        known.append("Plugin manifest/lifecycle/review contracts exist as metadata and readiness checks.")
        known.append("No plugin load, dynamic import, marketplace action, MCP call, or plugin execution is performed by Ask.")
        if plugins:
            known.append(f"Plugin metadata summary status: {plugins.get('status', 'metadata_only')}.")
        return (
            "Plugin information is readiness metadata only. It is not a runtime plugin system or execution permission.",
            known,
            unknown,
            ["Keep plugin work behind manifest, integrity, lifecycle, policy, approval, and lease gates."],
        )

    if intent == "model_gateway_question":
        status = model_status.get("status", "unknown")
        enabled = model_status.get("enabled")
        provider = model_status.get("provider", "unknown")
        known.append(f"Model Gateway provider metadata: {provider}.")
        known.append(f"Model Gateway status: {status}; enabled={enabled}.")
        known.append("Ask did not call a model and did not send context to a provider.")
        return (
            f"Model Gateway metadata is visible as {status}. Ask remains deterministic here and did not call the model gateway.",
            known,
            unknown,
            ["Use a separate local-provider validation flow before enabling model-assisted polish."],
        )

    if intent == "memory_question":
        known.append("Memory writes are not performed by Ask.")
        known.append("Memory retrieval, when explicitly supplied, is context only and not authority.")
        return (
            "Ask does not write memory. Memory can only be considered later through explicit, consent-aware read/search paths.",
            known,
            unknown,
            ["Use Memory Inbox/consent flows for persistence; do not silently store Ask content."],
        )

    if intent == "autopilot_question":
        known.append("AutoPilot is a read-only scanner/report source, not evidence or execution.")
        return (
            "AutoPilot can produce read-only candidate reports in its own flow, but Ask does not run hidden scans by default.",
            known,
            unknown,
            ["Use explicit AutoPilot report refs or scoped read-only scans in a separate operator-approved flow."],
        )

    if intent == "policy_or_safety_question":
        known.append("Policy allow is not execution success.")
        known.append("Model, memory, frontend, plugin, manifest, lease, and agent metadata are not authority.")
        return (
            "Aegis safety is strict by design: backend verifier logic owns success, and Ask only explains state and safe next steps.",
            known,
            unknown,
            ["Keep safety boundaries visible in UI and docs while adding real read-only product slices."],
        )

    if intent == "next_step_planning":
        known.append("Current safe product direction is controlled, read-only/productized slices before execution expansion.")
        return (
            "The safest next step is to improve useful read-only product surfaces first, then add narrow approval-gated execution only when evidence and verifier contracts are ready.",
            known,
            unknown,
            [
                "Validate Ask with real UI/API usage.",
                "Then add source-specific read-only summaries or a controlled capability broker.",
            ],
        )

    known.append("Aegis can explain runtime state, capabilities, skills, tools, model gateway metadata, and safe next steps.")
    known.append("Aegis Ask cannot execute actions, write memory, call plugins/tools/agents, or create evidence.")
    return (
        "Aegis Ask is a read-only explanation layer over backend-owned status and metadata. It is useful for status, capability, registry, and safety questions.",
        known,
        unknown,
        ["Ask a concrete status, capability, skill, tool, model, memory, or safety question."],
    )


def _runtime_health_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    summary = _mapping(report.get("summary"))
    checks = _mapping(report.get("checks"))
    closure = _mapping(checks.get("foundation_closure_readiness"))
    pending = _mapping(checks.get("pending_decision_hygiene"))
    evidence = _mapping(checks.get("evidence_audit"))
    replay = _mapping(checks.get("replay_diagnostics"))

    active_projections = _mapping(summary.get("active_runtime_projections"))
    evidence_projection = _mapping(active_projections.get("evidence_audit"))
    replay_projection = _mapping(active_projections.get("replay_diagnostics"))

    return {
        "status": summary.get("status") or closure.get("status") or "unknown",
        "source_of_truth": summary.get("source_of_truth") or "backend_projection_unavailable",
        "component_statuses": deepcopy(summary.get("component_statuses") or {}),
        "raw_component_statuses": deepcopy(summary.get("raw_component_statuses") or {}),
        "active_failure_components": list(summary.get("active_failure_components") or []),
        "attention": list(summary.get("attention") or []),
        "current_blocker_count": _number_or_unknown(closure.get("current_blocker_count")),
        "current_evidence_failure_count": _number_or_unknown(
            closure.get("current_evidence_failure_count")
            if "current_evidence_failure_count" in closure
            else evidence.get("current_evidence_failure_count")
        ),
        "current_missing_evidence_count": _number_or_unknown(
            closure.get("current_missing_evidence_count")
            if "current_missing_evidence_count" in closure
            else evidence.get("current_missing_evidence_count")
        ),
        "pending_decision_count": _number_or_unknown(pending.get("pending_count")),
        "restored_pending_count": _number_or_unknown(closure.get("restored_pending_count")),
        "current_session_pending_count": _number_or_unknown(closure.get("current_session_pending_count")),
        "historical_evidence_debt_count": _number_or_unknown(
            closure.get("historical_evidence_debt_count")
            if "historical_evidence_debt_count" in closure
            else evidence.get("historical_evidence_debt_count")
        ),
        "historical_missing_evidence_count": _number_or_unknown(
            closure.get("historical_missing_evidence_count")
            if "historical_missing_evidence_count" in closure
            else evidence.get("historical_missing_evidence_count")
        ),
        "raw_evidence_status": evidence.get("status") or _mapping(summary.get("raw_component_statuses")).get("evidence_audit") or "unknown",
        "active_evidence_status": evidence_projection.get("status") or "unknown",
        "raw_replay_status": replay.get("status") or _mapping(summary.get("raw_component_statuses")).get("replay_diagnostics") or "unknown",
        "active_replay_status": replay_projection.get("status") or "unknown",
        "replay_boundary_classification": closure.get("replay_boundary_classification")
        or replay_projection.get("replay_boundary_classification")
        or "unknown",
        "mutation_performed": False,
    }


def _source_refs(
    *,
    max_sources: int,
    maintenance: Mapping[str, Any],
    skills: Mapping[str, Any],
    tools: Mapping[str, Any],
    model_status: Mapping[str, Any],
    memory_result: Mapping[str, Any],
    autopilot: Mapping[str, Any],
    agents: Mapping[str, Any],
    plugins: Mapping[str, Any],
) -> list[dict[str, Any]]:
    candidates = [
        ("maintenance_scan", "Current read-only maintenance scan projection", bool(maintenance)),
        ("skill_registry", "Skill Registry metadata", bool(skills)),
        ("tool_registry", "Tool Registry metadata", bool(tools)),
        ("model_gateway_status", "Model Gateway status metadata", bool(model_status)),
        ("memory_search_result", "Explicitly supplied read-only memory search result", bool(memory_result)),
        ("autopilot_report", "Explicitly supplied AutoPilot read-only report", bool(autopilot)),
        ("agent_profile_catalog", "Agent Runtime profile catalog metadata", bool(agents)),
        ("plugin_metadata", "Plugin manifest/lifecycle metadata summary", bool(plugins)),
    ]
    return [
        {"source_id": source_id, "label": label, "authority": False, "evidence": False}
        for source_id, label, present in candidates
        if present
    ][:max_sources]


def _non_authority_flags() -> dict[str, bool]:
    return {
        "frontend_authority": False,
        "model_output_is_truth": False,
        "memory_retrieval_is_authority": False,
        "skill_registry_grants_permission": False,
        "tool_registry_grants_permission": False,
        "plugin_metadata_grants_permission": False,
        "agent_runtime_is_ask_engine": False,
        "autopilot_report_is_evidence": False,
        "context_package_is_permission": False,
        "policy_allow_is_execution_success": False,
    }


def _required_question(request: Mapping[str, Any]) -> str:
    question = _optional_text(request.get("question"))
    if not question:
        raise ValueError("question is required")
    return question


def _looks_like_execution_request(text: str, words: set[str]) -> bool:
    if _has_any(text, ("memory'ye yaz", "memory ye yaz", "memoryye yaz", "memory yaz", "write memory", "dosya olustur", "create file")):
        return True
    if _has_any(text, ("notepad ac", "open notepad", "shell calistir", "run command", "execute command")):
        return True
    return bool(words & {"delete", "sil", "mutate", "execute", "exec", "run", "launch", "baslat"})


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _named_items(value: Any, key: str, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            name = _optional_text(item.get(key))
            if name:
                names.append(name)
        if len(names) >= limit:
            break
    return names


def _memory_known(result: Mapping[str, Any]) -> str:
    return f"Memory search result count is {result.get('result_count', 'unknown')}."


def _autopilot_known(report: Mapping[str, Any]) -> str:
    return f"AutoPilot report status is {report.get('status', 'unknown')}."


def _agent_known(catalog: Mapping[str, Any]) -> str:
    return f"Agent profile catalog count is {catalog.get('profile_count', 'unknown')}."


def _safe_max_sources(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 8
    return max(1, min(parsed, 20))


def _optional_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number_or_unknown(value: Any) -> int | str:
    if isinstance(value, bool):
        return "unknown"
    if isinstance(value, int):
        return value
    return "unknown"


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
