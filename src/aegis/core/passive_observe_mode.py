from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


PASSIVE_OBSERVE_MODE_VERSION = "passive-observe-only-product-mode-readiness/1"
PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION = "not_granted_by_passive_observe_mode"

OBSERVE_SCOPES = {
    "runtime_status_summary",
    "maintenance_projection_summary",
    "pending_decision_summary",
    "app_registry_summary",
    "tool_registry_summary",
    "provider_readiness_summary",
    "model_inventory_summary",
    "policy_boundary_summary",
    "context_policy_summary",
    "memory_governance_summary",
    "identity_scope_summary",
    "lease_readiness_summary",
    "probe_design_summary",
    "repo_audit_readiness_summary",
    "evidence_debt_summary",
    "replay_debt_summary",
    "system_resource_summary",
    "product_onboarding_summary",
    "unknown",
}

DISPLAY_STATES = {
    "available_from_backend_state",
    "unavailable",
    "unknown",
    "stale",
    "historical_debt",
    "current_blocker",
    "future_gated",
    "blocked_by_policy",
    "needs_operator_attention",
    "not_implemented",
    "not_configured",
    "no_mutation_performed",
    "read_only_projection",
}

RISK_LEVELS = {"info", "low", "medium", "high", "critical", "unknown"}

LOWER_TRUST_SOURCES = {"frontend", "frontend_supplied", "frontend_projection", "user_supplied_untrusted"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_observe_mode": "observe_mode_cannot_provide_evidence",
    "evidence_created": "observe_mode_cannot_provide_evidence",
    "verifier_success": "observe_mode_cannot_mark_verifier_success",
    "verified_success": "observe_mode_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "fake_health_created": "fake_health_denied",
    "fake_evidence_created": "fake_evidence_denied",
    "fake_verifier_success_created": "fake_verifier_success_denied",
    "runtime_health_greenwashed": "runtime_health_greenwash_denied",
    "unknown_converted_to_healthy": "unknown_to_healthy_denied",
    "historical_debt_converted_to_success": "historical_debt_success_denied",
    "readiness_metadata_is_implementation": "readiness_metadata_implementation_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "tool_call_performed": "tool_call_request_denied",
    "model_call_performed": "model_call_request_denied",
    "provider_probe_performed": "provider_probe_request_denied",
    "endpoint_probed": "endpoint_probe_request_denied",
    "repo_scan_performed": "repo_scan_request_denied",
    "file_watch_started": "file_watch_request_denied",
    "process_watch_started": "process_watch_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "context_retrieval_performed": "context_retrieval_request_denied",
    "web_query_performed": "web_query_request_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "data_sent_external": "external_data_transfer_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
}


@dataclass(frozen=True)
class PassiveObserveModeFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedDecisionObservation:
    label: str
    observed_status: str | None
    display_state: str
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class PassiveObserveModeInput:
    request_id: str | None
    observe_scope: str | None
    namespace: str | None
    supplied_state_classification: str | None
    risk_level: str | None
    state_source: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    current_blocker: bool
    historical_debt: bool
    stale: bool
    future_gated: bool
    blocked: bool
    unavailable: bool
    not_implemented: bool
    not_configured: bool
    unknown_state: bool


@dataclass(frozen=True)
class PassiveObserveModeDecision:
    contract_version: str
    observe_scope: str | None
    display_state: str
    risk_level: str
    request_id: str | None
    namespace: str | None
    supplied_state_classification: str | None
    state_source: str | None
    lower_trust_source: bool
    source_truth_status: str
    current_state_preserved: bool
    historical_debt_preserved: bool
    stale_state_preserved: bool
    future_gated_preserved: bool
    blocked_state_preserved: bool
    unknown_state_preserved: bool
    unavailable_state_preserved: bool
    related_observations: tuple[RelatedDecisionObservation, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[PassiveObserveModeFailure, ...]
    observe_input: PassiveObserveModeInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_observe_mode: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    tool_call_performed: bool = False
    model_call_performed: bool = False
    provider_probe_performed: bool = False
    endpoint_probed: bool = False
    repo_scan_performed: bool = False
    file_watch_started: bool = False
    process_watch_started: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    web_query_performed: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    data_sent_external: bool = False
    generated_artifact_created: bool = False
    fake_health_created: bool = False
    fake_evidence_created: bool = False
    fake_verifier_success_created: bool = False
    requires_backend_validation: bool = True
    read_only_projection: bool = True


def validate_passive_observe_mode_request(
    request: Mapping[str, Any] | None,
    *,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> PassiveObserveModeDecision:
    """Classify supplied state for observe-only display without observing live systems."""

    if not isinstance(request, Mapping):
        failure = PassiveObserveModeFailure(
            reason="missing_request",
            field="request",
            message="passive observe mode request must be caller-supplied metadata",
        )
        return _decision(
            observe_scope=None,
            display_state="unknown",
            risk_level="unknown",
            request_id=None,
            namespace=None,
            supplied_state_classification=None,
            state_source=None,
            lower_trust_source=False,
            source_truth_status="missing_request",
            related_observations=(),
            failures=(failure,),
            observe_input=None,
        )

    data = deepcopy(dict(request))
    failures: list[PassiveObserveModeFailure] = []
    related_observations: list[RelatedDecisionObservation] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_provider_health": local_provider_health_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "capability_lease": capability_lease_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_observations)

    observe_input = PassiveObserveModeInput(
        request_id=_text(data.get("request_id")),
        observe_scope=_text(data.get("observe_scope")),
        namespace=_text(data.get("namespace")),
        supplied_state_classification=_text(data.get("supplied_state_classification")),
        risk_level=_text(data.get("risk_level")),
        state_source=_text(data.get("state_source")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        current_blocker=_truthy(data.get("current_blocker")),
        historical_debt=_truthy(data.get("historical_debt")),
        stale=_truthy(data.get("stale")),
        future_gated=_truthy(data.get("future_gated")),
        blocked=_truthy(data.get("blocked")),
        unavailable=_truthy(data.get("unavailable")),
        not_implemented=_truthy(data.get("not_implemented")),
        not_configured=_truthy(data.get("not_configured")),
        unknown_state=_truthy(data.get("unknown_state")),
    )

    _validate_required_fields(observe_input, failures)
    _validate_truthfulness(observe_input, failures)

    display_state = _display_state(observe_input, failures)
    risk_level = _risk_level(observe_input, display_state, failures)
    lower_trust = observe_input.state_source in LOWER_TRUST_SOURCES
    return _decision(
        observe_scope=observe_input.observe_scope,
        display_state=display_state,
        risk_level=risk_level,
        request_id=observe_input.request_id,
        namespace=observe_input.namespace,
        supplied_state_classification=observe_input.supplied_state_classification,
        state_source=observe_input.state_source,
        lower_trust_source=lower_trust,
        source_truth_status=_source_truth_status(observe_input, lower_trust),
        related_observations=tuple(related_observations),
        failures=tuple(failures),
        observe_input=observe_input,
    )


def _decision(
    *,
    observe_scope: str | None,
    display_state: str,
    risk_level: str,
    request_id: str | None,
    namespace: str | None,
    supplied_state_classification: str | None,
    state_source: str | None,
    lower_trust_source: bool,
    source_truth_status: str,
    related_observations: tuple[RelatedDecisionObservation, ...],
    failures: tuple[PassiveObserveModeFailure, ...],
    observe_input: PassiveObserveModeInput | None,
) -> PassiveObserveModeDecision:
    return PassiveObserveModeDecision(
        contract_version=PASSIVE_OBSERVE_MODE_VERSION,
        observe_scope=observe_scope,
        display_state=display_state,
        risk_level=risk_level,
        request_id=request_id,
        namespace=namespace,
        supplied_state_classification=supplied_state_classification,
        state_source=state_source,
        lower_trust_source=lower_trust_source,
        source_truth_status=source_truth_status,
        current_state_preserved=bool(observe_input and observe_input.current_blocker),
        historical_debt_preserved=bool(observe_input and observe_input.historical_debt),
        stale_state_preserved=bool(observe_input and observe_input.stale),
        future_gated_preserved=bool(observe_input and observe_input.future_gated),
        blocked_state_preserved=bool(observe_input and observe_input.blocked),
        unknown_state_preserved=bool(observe_input and (observe_input.unknown_state or observe_input.supplied_state_classification == "unknown")),
        unavailable_state_preserved=bool(observe_input and observe_input.unavailable),
        related_observations=related_observations,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        observe_input=observe_input,
    )


def _validate_required_fields(
    observe_input: PassiveObserveModeInput,
    failures: list[PassiveObserveModeFailure],
) -> None:
    required = {
        "request_id": observe_input.request_id,
        "observe_scope": observe_input.observe_scope,
        "namespace": observe_input.namespace,
        "supplied_state_classification": observe_input.supplied_state_classification,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if observe_input.observe_scope and observe_input.observe_scope not in OBSERVE_SCOPES:
        _add_failure(failures, "unsupported_observe_scope", "observe_scope", "observe scope is not recognized")
    if observe_input.supplied_state_classification and observe_input.supplied_state_classification not in DISPLAY_STATES:
        _add_failure(failures, "unsupported_state_classification", "supplied_state_classification", "state classification is not recognized")
    if observe_input.risk_level and observe_input.risk_level not in RISK_LEVELS:
        _add_failure(failures, "unsupported_risk_level", "risk_level", "risk level is not recognized")
    if not (observe_input.source_refs or observe_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "displayed state requires source refs or provenance")


def _validate_truthfulness(
    observe_input: PassiveObserveModeInput,
    failures: list[PassiveObserveModeFailure],
) -> None:
    if observe_input.state_source in LOWER_TRUST_SOURCES and observe_input.supplied_state_classification == "available_from_backend_state":
        _add_failure(failures, "frontend_state_cannot_claim_backend_truth", "state_source", "frontend-supplied state cannot become backend truth")
    if observe_input.unknown_state and observe_input.supplied_state_classification == "available_from_backend_state":
        _add_failure(failures, "unknown_state_cannot_be_available", "supplied_state_classification", "unknown state cannot be marked available")
    if observe_input.historical_debt and observe_input.supplied_state_classification == "available_from_backend_state":
        _add_failure(failures, "historical_debt_cannot_be_current_success", "supplied_state_classification", "historical debt cannot become current success")
    if observe_input.future_gated and observe_input.supplied_state_classification == "available_from_backend_state":
        _add_failure(failures, "future_gated_cannot_be_implemented", "supplied_state_classification", "future-gated readiness cannot become implementation")
    if observe_input.stale and observe_input.supplied_state_classification == "available_from_backend_state":
        _add_failure(failures, "stale_state_cannot_be_live_truth", "supplied_state_classification", "stale metadata cannot become live runtime truth")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[PassiveObserveModeFailure],
    related_observations: list[RelatedDecisionObservation],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot grant observe mode authority, dispatch, grants, evidence, verifier success, execution, mutation, or fake state",
        )
    related_observations.append(
        RelatedDecisionObservation(
            label=label,
            observed_status=_related_status(decision),
            display_state=_related_display_state(decision),
            reference_only=True,
            authority=False,
            implementation_claim=False,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[PassiveObserveModeFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "observe mode cannot claim authority, grants, evidence, verifier success, fake state, proof, or implementation")
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "observe mode cannot perform tools, models, provider probes, scans, watchers, retrieval, web, mutation, external transfer, or artifact creation")
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "observe mode cannot grant execution permission")


def _display_state(
    observe_input: PassiveObserveModeInput,
    failures: list[PassiveObserveModeFailure],
) -> str:
    reasons = {failure.reason for failure in failures}
    if any("fake" in reason or "authority" in reason or "dispatch" in reason for reason in reasons):
        return "blocked_by_policy"
    if any(
        "request_denied" in reason
        or "mutation" in reason
        or "external" in reason
        or "artifact" in reason
        for reason in reasons
    ):
        return "blocked_by_policy"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "unavailable"
    if observe_input.blocked:
        return "blocked_by_policy"
    if observe_input.current_blocker:
        return "current_blocker"
    if observe_input.historical_debt:
        return "historical_debt"
    if observe_input.stale:
        return "stale"
    if observe_input.future_gated:
        return "future_gated"
    if observe_input.unavailable:
        return "unavailable"
    if observe_input.not_implemented:
        return "not_implemented"
    if observe_input.not_configured:
        return "not_configured"
    if observe_input.unknown_state:
        return "unknown"
    return observe_input.supplied_state_classification or "unknown"


def _risk_level(
    observe_input: PassiveObserveModeInput,
    display_state: str,
    failures: list[PassiveObserveModeFailure],
) -> str:
    if failures:
        return "high"
    if observe_input.risk_level:
        return observe_input.risk_level
    if display_state == "current_blocker":
        return "high"
    if display_state in {"historical_debt", "stale", "needs_operator_attention"}:
        return "medium"
    if display_state in {"unknown", "unavailable"}:
        return "unknown"
    if display_state in {"future_gated", "not_implemented", "not_configured"}:
        return "low"
    return "info"


def _source_truth_status(observe_input: PassiveObserveModeInput, lower_trust: bool) -> str:
    if lower_trust:
        return "lower_trust_reference_only"
    if observe_input.supplied_state_classification == "available_from_backend_state":
        return "backend_state_reference"
    return "caller_supplied_projection"


def _related_status(decision: Any) -> str | None:
    for field in (
        "probe_result_status",
        "selection_mode",
        "lifecycle_state",
        "readiness_status",
        "policy_status",
        "policy_outcome",
        "inventory_status",
        "governance_status",
        "scope_status",
        "decision_status",
    ):
        value = _field_value(decision, field)
        if value:
            return str(value)
    return None


def _related_display_state(decision: Any) -> str:
    status = str(_related_status(decision) or "")
    if status.startswith("blocked"):
        return "blocked_by_policy"
    if "future" in status or _field_bool(decision, "future_gated"):
        return "future_gated"
    if status in {"not_configured", "offline_disabled"}:
        return "not_configured"
    if status in {"unknown", "clarification_required"}:
        return "unknown"
    if status:
        return "read_only_projection"
    return "unknown"


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(deepcopy(item) for item in value if isinstance(item, Mapping))


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "allowed", "grant"}
    return bool(value)


def _add_failure(
    failures: list[PassiveObserveModeFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(PassiveObserveModeFailure(reason=reason, field=field, message=message))
