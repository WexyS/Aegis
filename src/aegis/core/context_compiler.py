from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


CONTEXT_COMPILER_VERSION = "context-compiler/1"
CONTEXT_PACKAGE_SCHEMA_VERSION = "context-package/1"

AUTHORITY_BACKEND = "backend_authoritative"
AUTHORITY_DERIVED = "backend_derived_summary"
AUTHORITY_FRONTEND_REFERENCE = "frontend_reference_non_authoritative"


@dataclass(frozen=True)
class ContextBudget:
    max_items_per_section: int = 5
    include_raw_runtime_events: bool = False


@dataclass(frozen=True)
class ContextCompilerInput:
    request: Mapping[str, Any] | None = None
    runtime_snapshot: Mapping[str, Any] | None = None
    command_lifecycle: Mapping[str, Any] | None = None
    policy_boundary: Any | None = None
    non_executable_state: Mapping[str, Any] | None = None
    evidence_audit: Mapping[str, Any] | None = None
    maintenance_scan: Mapping[str, Any] | None = None
    frontend_projection: Mapping[str, Any] | None = None
    runtime_events: Iterable[Mapping[str, Any]] | None = None
    generated_at_ms: int | None = None
    budget: ContextBudget | None = None


def compile_context_package(inputs: ContextCompilerInput) -> dict[str, Any]:
    """Build a bounded, non-executing context package from trusted inputs.

    The compiler is deliberately pure: it reads only caller-supplied data, does
    not inspect global runtime state, does not call tools, and grants no
    execution permission.
    """

    budget = inputs.budget or ContextBudget()
    source_references = _source_references(inputs)
    omitted_sections: list[dict[str, Any]] = []
    safety_warnings: list[str] = []
    omitted_item_counts: dict[str, int] = {}

    runtime_events_seen = _count_iterable(inputs.runtime_events)
    if runtime_events_seen:
        omitted_sections.append({
            "section": "runtime_events",
            "reason": "raw_runtime_journal_excluded_by_default",
            "omitted_count": runtime_events_seen,
        })
        omitted_item_counts["runtime_events"] = runtime_events_seen
        safety_warnings.append("raw runtime events were omitted; context contains bounded summaries only")

    request_summary = _compile_request(inputs.request, safety_warnings)
    runtime_summary = _compile_runtime_snapshot(inputs.runtime_snapshot, safety_warnings)
    lifecycle_summary, lifecycle_omissions = _compile_command_lifecycle(
        inputs.command_lifecycle,
        budget=budget,
        safety_warnings=safety_warnings,
    )
    omitted_item_counts.update(lifecycle_omissions)
    policy_summary = _compile_policy_boundary(inputs.policy_boundary, safety_warnings)
    non_executable_summary = _compile_non_executable_state(inputs.non_executable_state, safety_warnings)
    evidence_summary = _compile_evidence_audit(inputs.evidence_audit, safety_warnings)
    maintenance_summary = _compile_maintenance_scan(inputs.maintenance_scan, safety_warnings)
    frontend_summary = _compile_frontend_projection(inputs.frontend_projection, safety_warnings)

    if lifecycle_omissions:
        for section, count in lifecycle_omissions.items():
            omitted_sections.append({
                "section": section,
                "reason": "context_budget_limit",
                "omitted_count": count,
            })

    return {
        "schema_version": CONTEXT_PACKAGE_SCHEMA_VERSION,
        "compiler_version": CONTEXT_COMPILER_VERSION,
        "generated_at_ms": int(inputs.generated_at_ms if inputs.generated_at_ms is not None else time.time() * 1000),
        "non_executing": True,
        "capability_grant": False,
        "execution_permission": "not_granted_by_context",
        "request": _section("request", request_summary),
        "runtime": _section("runtime_snapshot", runtime_summary),
        "command_lifecycle": _section("command_lifecycle", lifecycle_summary),
        "policy_boundary": _section("policy_boundary", policy_summary),
        "non_executable": _section("non_executable_state", non_executable_summary),
        "verifier_evidence": _section("evidence_audit", evidence_summary),
        "maintenance_diagnostics": _section("maintenance_scan", maintenance_summary),
        "frontend_projection": _section("frontend_projection", frontend_summary),
        "source_references": source_references,
        "omitted_sections": omitted_sections,
        "safety_warnings": safety_warnings,
        "budget": {
            "max_items_per_section": _safe_limit(budget.max_items_per_section),
            "raw_runtime_journal_included": False,
            "requested_raw_runtime_events": bool(budget.include_raw_runtime_events),
            "omitted_item_counts": omitted_item_counts,
        },
    }


def _section(source_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_ref": source_id,
        "summary": summary,
    }


def _source_references(inputs: ContextCompilerInput) -> list[dict[str, Any]]:
    refs = [
        _source_ref("request", "explicit_context_compiler_input", AUTHORITY_BACKEND, inputs.request is not None),
        _source_ref("runtime_snapshot", "runtime_authority_snapshot", AUTHORITY_BACKEND, inputs.runtime_snapshot is not None),
        _source_ref("command_lifecycle", "command_lifecycle_snapshot", AUTHORITY_BACKEND, inputs.command_lifecycle is not None),
        _source_ref("policy_boundary", "policy_boundary_decision", AUTHORITY_BACKEND, inputs.policy_boundary is not None),
        _source_ref("non_executable_state", "guard_non_executable_projection", AUTHORITY_DERIVED, inputs.non_executable_state is not None),
        _source_ref("evidence_audit", "evidence_audit_summary", AUTHORITY_DERIVED, inputs.evidence_audit is not None),
        _source_ref("maintenance_scan", "read_only_maintenance_scan", AUTHORITY_DERIVED, inputs.maintenance_scan is not None),
        _source_ref(
            "frontend_projection",
            "frontend_projection_reference",
            AUTHORITY_FRONTEND_REFERENCE,
            inputs.frontend_projection is not None,
            used_as_authority=False,
        ),
    ]
    return refs


def _source_ref(
    source_id: str,
    source_type: str,
    authority: str,
    provided: bool,
    *,
    used_as_authority: bool | None = None,
) -> dict[str, Any]:
    ref = {
        "source_id": source_id,
        "source_type": source_type,
        "authority": authority,
        "provided": provided,
    }
    if used_as_authority is not None:
        ref["used_as_authority"] = used_as_authority
    return ref


def _compile_request(request: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        warnings.append("request metadata unavailable")
        return {"status": "unavailable"}
    return {
        "status": _state_status(request),
        "command_id": request.get("command_id"),
        "trace_id": request.get("trace_id"),
        "text_present": bool(request.get("text")),
        "text_length": len(str(request.get("text") or "")),
    }


def _compile_runtime_snapshot(snapshot: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(snapshot, Mapping):
        warnings.append("runtime snapshot unavailable")
        return {"status": "unavailable", "authority": AUTHORITY_BACKEND}
    status = _state_status(snapshot)
    if status in {"stale", "unknown"}:
        warnings.append(f"runtime snapshot is {status}")
    return {
        "status": status,
        "authority": AUTHORITY_BACKEND,
        "fsm_state": snapshot.get("fsm_state") or "unknown",
        "active_command_present": _present_or_unknown(snapshot, "active_command"),
        "active_tool": snapshot.get("active_tool") or "unknown",
        "queue_depth": snapshot["queue_depth"] if "queue_depth" in snapshot else "unavailable",
        "version": snapshot.get("version") if "version" in snapshot else "unavailable",
    }


def _compile_command_lifecycle(
    lifecycle: Mapping[str, Any] | None,
    *,
    budget: ContextBudget,
    safety_warnings: list[str],
) -> tuple[dict[str, Any], dict[str, int]]:
    if not isinstance(lifecycle, Mapping):
        safety_warnings.append("command lifecycle unavailable")
        return {"status": "unavailable", "authority": AUTHORITY_BACKEND}, {}

    limit = _safe_limit(budget.max_items_per_section)
    pending_approvals = _list_from(lifecycle.get("pending_approvals"))
    pending_clarifications = _list_from(lifecycle.get("pending_clarifications"))
    records = _list_from(lifecycle.get("records"))
    approvals, omitted_approvals = _bounded_decisions(pending_approvals, limit)
    clarifications, omitted_clarifications = _bounded_decisions(pending_clarifications, limit)
    recent_records, omitted_records = _bounded_records(records, limit)
    omitted = {
        key: value
        for key, value in {
            "command_lifecycle.pending_approvals": omitted_approvals,
            "command_lifecycle.pending_clarifications": omitted_clarifications,
            "command_lifecycle.records": omitted_records,
        }.items()
        if value
    }

    lifecycle_states = [str(record.get("status") or "unknown") for record in records if isinstance(record, Mapping)]
    unresolved = len(pending_approvals) + len(pending_clarifications)
    summary = {
        "status": _state_status(lifecycle),
        "authority": AUTHORITY_BACKEND,
        "pending_approval_count": len(pending_approvals),
        "pending_clarification_count": len(pending_clarifications),
        "unresolved_decision_count": unresolved,
        "pending_approvals": approvals,
        "pending_clarifications": clarifications,
        "recent_records": recent_records,
        "lifecycle_states": sorted(set(lifecycle_states)),
        "resolution_is_execution_permission": False,
    }
    if unresolved:
        safety_warnings.append("unresolved approval or clarification state present")
    if any(_is_stale(record) for record in records):
        safety_warnings.append("stale command lifecycle record present")
        summary["status"] = "stale"
    return summary, omitted


def _compile_policy_boundary(policy_boundary: Any, warnings: list[str]) -> dict[str, Any]:
    if policy_boundary is None:
        warnings.append("policy boundary decision unavailable")
        return {
            "status": "unavailable",
            "context_grants_permission": False,
            "execution_permission": "not_granted_by_context",
        }
    dispatch_allowed = _get_field(policy_boundary, "dispatch_allowed", "unknown")
    summary = {
        "status": _state_status(policy_boundary),
        "boundary_version": _get_field(policy_boundary, "boundary_version", "unknown"),
        "decision_status": _get_field(policy_boundary, "decision_status", "unknown"),
        "policy_rule": _get_field(policy_boundary, "policy_rule", "unknown"),
        "dispatch_allowed_by_policy": dispatch_allowed,
        "resume_allowed_by_policy": _get_field(policy_boundary, "resume_allowed", False),
        "approval_granted": _get_field(policy_boundary, "approval_granted", False),
        "context_grants_permission": False,
        "execution_permission": "not_granted_by_context",
        "requires_policy_recheck_before_dispatch": True,
    }
    if dispatch_allowed is not True:
        warnings.append("policy boundary does not report dispatchable state")
    return summary


def _compile_non_executable_state(state: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        return {"status": "unavailable", "non_executable": "unknown"}

    guard = state.get("last_guard_decision") if isinstance(state.get("last_guard_decision"), Mapping) else {}
    policy_rule = str((guard or {}).get("policy_rule") or state.get("policy_rule") or "")
    blocked = bool(state.get("last_blocked_action") or state.get("blocked") or state.get("terminal_non_executed"))
    non_executed = state.get("not_executed") is True or state.get("executed") is False
    quarantined = "quarantine" in policy_rule or "quarantined" in policy_rule
    if blocked or non_executed or quarantined:
        warnings.append("non-executable or blocked state present")
    return {
        "status": _state_status(state),
        "command_status": state.get("command_status") or "unknown",
        "non_executable": non_executed or blocked or quarantined,
        "blocked": blocked,
        "quarantined": quarantined,
        "policy_rule": policy_rule or "unknown",
        "execution_recommendation": "do_not_execute" if (non_executed or blocked or quarantined) else "unknown",
    }


def _compile_evidence_audit(evidence: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(evidence, Mapping):
        warnings.append("evidence audit unavailable")
        return {"status": "unavailable", "dispatch_success_is_not_verification": True}
    status = str(evidence.get("status") or "unknown")
    if status != "ok":
        warnings.append(f"evidence audit status is {status}")
    return {
        "status": status,
        "read_only": evidence.get("read_only") if "read_only" in evidence else "unavailable",
        "success_count": evidence["success_count"] if "success_count" in evidence else "unavailable",
        "verified_action_count": evidence["verified_action_count"] if "verified_action_count" in evidence else "unavailable",
        "missing_evidence_count": evidence["missing_evidence_count"] if "missing_evidence_count" in evidence else "unavailable",
        "failed_evidence_count": evidence["failed_evidence_count"] if "failed_evidence_count" in evidence else "unavailable",
        "verification_counts": evidence.get("verification_counts") if "verification_counts" in evidence else "unavailable",
        "dispatch_success_is_not_verification": True,
    }


def _compile_maintenance_scan(scan: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(scan, Mapping):
        return {"status": "unavailable", "read_only": "unknown", "diagnostics_only": True}
    checks = scan.get("checks") if isinstance(scan.get("checks"), Mapping) else {}
    app_discovery = checks.get("app_discovery") if isinstance(checks.get("app_discovery"), Mapping) else {}
    read_only = scan.get("read_only") if "read_only" in scan else "unavailable"
    app_read_only = app_discovery.get("read_only") if "read_only" in app_discovery else "unavailable"
    if read_only is not True or app_read_only is False:
        warnings.append("maintenance diagnostics read-only status is not explicitly safe")
    return {
        "status": _state_status(scan),
        "read_only": read_only,
        "diagnostics_only": True,
        "action_proposal_count": len(_list_from(scan.get("action_proposals"))),
        "app_discovery": {
            "present": bool(app_discovery),
            "read_only": app_read_only,
            "actions_performed": app_discovery.get("actions_performed") if "actions_performed" in app_discovery else "unavailable",
        },
        "mutation_performed": scan.get("mutation_performed", False) is True,
    }


def _compile_frontend_projection(projection: Mapping[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    if projection is not None:
        warnings.append("frontend projection provided for reference only; backend truth remains authoritative")
    return {
        "provided": isinstance(projection, Mapping),
        "used_as_authority": False,
        "status": "reference_only" if isinstance(projection, Mapping) else "unavailable",
        "reason": "frontend projection/cache cannot grant authority or execution permission",
    }


def _bounded_decisions(items: list[Any], limit: int) -> tuple[list[dict[str, Any]], int]:
    bounded: list[dict[str, Any]] = []
    for item in items[:limit]:
        if not isinstance(item, Mapping):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
        bounded.append({
            "command_id": item.get("command_id"),
            "status": item.get("status") or "unknown",
            "risk_level": item.get("risk_level") or "unknown",
            "approval_required": item.get("approval_required") if "approval_required" in item else "unknown",
            "clarification_required": item.get("clarification_required") if "clarification_required" in item else "unknown",
            "verification_state": item.get("verification_state") or "unknown",
            "resolution_status": (
                metadata.get("approval_resolution_status")
                or metadata.get("clarification_resolution_status")
                or "unknown"
            ),
            "resume_allowed": metadata.get("resume_allowed") if "resume_allowed" in metadata else "unknown",
            "mutation_performed": metadata.get("mutation_performed") is True,
            "not_executed": metadata.get("not_executed") is True,
            "completed_without_execution": metadata.get("completed_without_execution") is True,
        })
    return bounded, max(len(items) - limit, 0)


def _bounded_records(items: list[Any], limit: int) -> tuple[list[dict[str, Any]], int]:
    bounded: list[dict[str, Any]] = []
    for item in items[-limit:]:
        if not isinstance(item, Mapping):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
        bounded.append({
            "command_id": item.get("command_id"),
            "status": item.get("status") or "unknown",
            "active": item.get("active") if "active" in item else "unknown",
            "verification_state": item.get("verification_state") or "unknown",
            "approval_resolution_status": metadata.get("approval_resolution_status") or "unknown",
            "clarification_resolution_status": metadata.get("clarification_resolution_status") or "unknown",
            "mutation_performed": metadata.get("mutation_performed") is True,
            "not_executed": metadata.get("not_executed") is True,
            "completed_without_execution": metadata.get("completed_without_execution") is True,
        })
    return bounded, max(len(items) - limit, 0)


def _state_status(value: Any) -> str:
    if value is None:
        return "unavailable"
    if _is_stale(value):
        return "stale"
    if isinstance(value, Mapping):
        raw = value.get("status")
        if raw:
            return str(raw)
        if value.get("unknown") is True:
            return "unknown"
        return "available"
    return "available"


def _is_stale(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value.get("stale") or value.get("is_stale"))
    return bool(getattr(value, "stale", False) or getattr(value, "is_stale", False))


def _present_or_unknown(mapping: Mapping[str, Any], key: str) -> bool | str:
    if key not in mapping:
        return "unknown"
    return mapping.get(key) is not None


def _get_field(value: Any, key: str, default: Any) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _list_from(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_limit(value: int) -> int:
    return max(int(value), 0)


def _count_iterable(value: Iterable[Any] | None) -> int:
    if value is None:
        return 0
    if isinstance(value, list | tuple):
        return len(value)
    return sum(1 for _ in value)
