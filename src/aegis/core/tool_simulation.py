from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, unique
from types import MappingProxyType
from typing import Any, Mapping


TOOL_SIMULATION_VERSION = "policy-tool-simulation-dry-run/1"
TOOL_SIMULATION_EXECUTION_PERMISSION = "not_granted_by_tool_simulation"


@unique
class ToolSimulationStatus(str, Enum):
    SIMULATION_READY = "simulation_ready"
    POLICY_ALLOWS_BUT_REQUIRES_EXECUTION_GATE = "policy_allows_but_requires_execution_gate"
    APPROVAL_REQUIRED = "approval_required"
    LEASE_REQUIRED = "lease_required"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    BLOCKED_BY_UNKNOWN_RISK = "blocked_by_unknown_risk"
    BLOCKED_BY_MISSING_RESOURCE_SCOPE = "blocked_by_missing_resource_scope"
    BLOCKED_BY_MISSING_EVIDENCE_EXPECTATION = "blocked_by_missing_evidence_expectation"
    BLOCKED_BY_MISSING_VERIFIER_EXPECTATION = "blocked_by_missing_verifier_expectation"
    BLOCKED_BY_DESTRUCTIVE_ACTION = "blocked_by_destructive_action"
    BLOCKED_BY_UNAVAILABLE_ROLLBACK = "blocked_by_unavailable_rollback"
    BLOCKED_BY_PROVIDER_INTERSTITIAL_RISK = "blocked_by_provider_interstitial_risk"
    BLOCKED_BY_QUARANTINED_TOOL = "blocked_by_quarantined_tool"
    UNSUPPORTED_TOOL = "unsupported_tool"
    UNSUPPORTED_ACTION = "unsupported_action"
    CLARIFICATION_REQUIRED = "clarification_required"


@unique
class ToolSimulationRiskTier(str, Enum):
    READ_ONLY = "read_only"
    BROWSER_OPEN = "browser_open"
    BROWSER_SEARCH = "browser_search"
    APP_LAUNCH = "app_launch"
    LOCAL_FILE_READ = "local_file_read"
    LOCAL_FILE_WRITE = "local_file_write"
    EXTERNAL_API_READ = "external_api_read"
    EXTERNAL_API_WRITE = "external_api_write"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    PLUGIN_EXECUTION = "plugin_execution"
    CLEANUP_ARCHIVE = "cleanup_archive"
    CLEANUP_COMPACTION = "cleanup_compaction"
    DESTRUCTIVE_SYSTEM_CHANGE = "destructive_system_change"
    UNKNOWN = "unknown"


@unique
class ToolCategory(str, Enum):
    APP_TOOL = "app_tool"
    BROWSER_TOOL = "browser_tool"
    FILE_TOOL = "file_tool"
    SHELL_TOOL = "shell_tool"
    API_TOOL = "api_tool"
    MEMORY_TOOL = "memory_tool"
    PLUGIN_TOOL = "plugin_tool"
    CLEANUP_TOOL = "cleanup_tool"
    MODEL_TOOL = "model_tool"
    UNKNOWN_TOOL = "unknown_tool"


@unique
class ToolSimulationEvidenceExpectation(str, Enum):
    NO_EVIDENCE_EXPECTED = "no_evidence_expected"
    PROCESS_WINDOW_VERIFICATION_EXPECTED = "process_window_verification_expected"
    BROWSER_URL_VERIFICATION_EXPECTED = "browser_url_verification_expected"
    PROVIDER_INTERSTITIAL_CHECK_EXPECTED = "provider_interstitial_check_expected"
    FILE_HASH_OR_DIFF_EXPECTED = "file_hash_or_diff_expected"
    POLICY_DECISION_REF_EXPECTED = "policy_decision_ref_expected"
    TIMEOUT_PROJECTION_EXPECTED = "timeout_projection_expected"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    UNKNOWN_EVIDENCE_EXPECTATION = "unknown_evidence_expectation"


@unique
class ToolSimulationRollbackStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"
    MANUAL_ONLY = "manual_only"
    STAGING_REQUIRED = "staging_required"
    BACKUP_REQUIRED = "backup_required"
    REVERSIBLE_WITH_PLAN = "reversible_with_plan"
    COMPENSATING_ACTION_ONLY = "compensating_action_only"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolSimulationVerifierExpectation:
    verifier_required: bool
    verifier_name: str
    verifier_postcondition: str
    verifier_failure_modes: tuple[str, ...] = ()
    verifier_success_required_for_completion: bool = False


@dataclass(frozen=True)
class SimulationFinding:
    reason: str
    field: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class SimulationAlternative:
    label: str
    reason: str
    proposed_intent: str | None = None


@dataclass(frozen=True)
class ToolSimulationInput:
    request_id: str | None
    command_id: str | None
    raw_user_request: str | None
    normalized_intent: str | None
    route_kind: str | None
    proposed_action: str | None
    proposed_tool: str | None
    tool_category: str = ToolCategory.UNKNOWN_TOOL.value
    capability_category: str | None = None
    risk_tier: str = ToolSimulationRiskTier.UNKNOWN.value
    target_app: str | None = None
    target_url: str | None = None
    search_provider: str | None = None
    query: str | None = None
    affected_resources: tuple[str, ...] = ()
    data_sensitivity: str | None = None
    policy_rule_refs: tuple[str, ...] = ()
    policy_decision_hint: str | None = None
    approval_hint: Mapping[str, Any] = field(default_factory=dict)
    lease_hint: Mapping[str, Any] = field(default_factory=dict)
    evidence_expectation_hint: tuple[str, ...] = ()
    verifier_expectation_hint: ToolSimulationVerifierExpectation = field(
        default_factory=lambda: ToolSimulationVerifierExpectation(
            verifier_required=False,
            verifier_name="",
            verifier_postcondition="",
        )
    )
    timeout_budget_ref: str | None = None
    rollback_status: str = ToolSimulationRollbackStatus.UNKNOWN.value
    provider_interstitial_risk: Mapping[str, Any] = field(default_factory=dict)
    fallback_expectation: Mapping[str, Any] = field(default_factory=dict)
    source_refs: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_resources", _strings(self.affected_resources))
        object.__setattr__(self, "policy_rule_refs", _strings(self.policy_rule_refs))
        object.__setattr__(self, "evidence_expectation_hint", _strings(self.evidence_expectation_hint))
        object.__setattr__(self, "source_refs", _strings(self.source_refs))
        object.__setattr__(self, "claims", _strings(self.claims))
        object.__setattr__(self, "approval_hint", MappingProxyType(deepcopy(dict(self.approval_hint))))
        object.__setattr__(self, "lease_hint", MappingProxyType(deepcopy(dict(self.lease_hint))))
        object.__setattr__(
            self,
            "provider_interstitial_risk",
            MappingProxyType(deepcopy(dict(self.provider_interstitial_risk))),
        )
        object.__setattr__(self, "fallback_expectation", MappingProxyType(deepcopy(dict(self.fallback_expectation))))


@dataclass(frozen=True)
class ToolSimulationResult:
    simulation_version: str
    simulation_id: str
    request_id: str | None
    command_id: str | None
    raw_user_request: str | None
    normalized_intent: str | None
    route_kind: str | None
    proposed_action: str | None
    proposed_tool: str | None
    tool_category: str
    risk_tier: str
    capability_category: str | None
    target_app: str | None
    target_url: str | None
    search_provider: str | None
    query: str | None
    policy_simulation_status: str
    policy_rule_refs: tuple[str, ...]
    policy_decision_hint: str | None
    approval_required: bool
    approval_reason: str | None
    lease_required: bool
    lease_reason: str | None
    proposed_lease_scope: str | None
    proposed_lease_duration: str | None
    evidence_expected: tuple[str, ...]
    verifier_expected: ToolSimulationVerifierExpectation
    affected_resources: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    unknowns: tuple[str, ...]
    alternatives: tuple[SimulationAlternative, ...]
    operator_attention_required: bool
    rollback_status: str
    timeout_budget_ref: str | None
    fallback_expectation: Mapping[str, Any]
    provider_interstitial_risk: Mapping[str, Any]
    source_refs: tuple[str, ...]
    findings: tuple[SimulationFinding, ...] = ()
    can_execute: bool = False
    would_dispatch: bool = False
    dispatch_performed: bool = False
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = TOOL_SIMULATION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_created: bool = False
    evidence_provided_by_simulation: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    image_generation_used: bool = False
    model_call_used: bool = False
    tool_call_used: bool = False
    mcp_call_used: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_expectation", MappingProxyType(deepcopy(dict(self.fallback_expectation))))
        object.__setattr__(
            self,
            "provider_interstitial_risk",
            MappingProxyType(deepcopy(dict(self.provider_interstitial_risk))),
        )


@dataclass(frozen=True)
class ToolSimulationDecision:
    simulation_version: str
    validation_status: str
    failure_reasons: tuple[str, ...]
    failures: tuple[SimulationFinding, ...]
    simulation_input: ToolSimulationInput | None = None
    result: ToolSimulationResult | None = None
    can_execute: bool = False
    would_dispatch: bool = False
    dispatch_performed: bool = False
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = TOOL_SIMULATION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_created: bool = False
    evidence_provided_by_simulation: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


SUPPORTED_TOOLS = {
    "read_file",
    "list_directory",
    "search_files",
    "grep_in_files",
    "file_info",
    "search_web",
    "open_url",
    "open_app",
    "focus_app",
    "write_file",
    "create_file",
    "edit_file",
    "run_command",
    "external_api_read",
    "external_api_write",
    "memory_read",
    "memory_write",
    "plugin_execution",
    "cleanup_archive",
    "cleanup_compaction",
}

QUARANTINED_TOOLS = {"click", "browser_click", "desktop_click"}
RAW_CONTROL_COMMANDS = {"/force_idle", "/reset_memory", "force_idle", "reset_memory"}
VISION_LIVE_TOOLS = {"vision", "ocr", "live_feed", "vision_live_feed", "screen_live_feed"}

SIDE_EFFECTING_RISK_TIERS = {
    ToolSimulationRiskTier.APP_LAUNCH.value,
    ToolSimulationRiskTier.LOCAL_FILE_WRITE.value,
    ToolSimulationRiskTier.EXTERNAL_API_WRITE.value,
    ToolSimulationRiskTier.MEMORY_WRITE.value,
    ToolSimulationRiskTier.PLUGIN_EXECUTION.value,
    ToolSimulationRiskTier.CLEANUP_ARCHIVE.value,
    ToolSimulationRiskTier.CLEANUP_COMPACTION.value,
    ToolSimulationRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value,
}

HIGH_RISK_TIERS = {
    ToolSimulationRiskTier.LOCAL_FILE_WRITE.value,
    ToolSimulationRiskTier.EXTERNAL_API_WRITE.value,
    ToolSimulationRiskTier.MEMORY_WRITE.value,
    ToolSimulationRiskTier.PLUGIN_EXECUTION.value,
    ToolSimulationRiskTier.CLEANUP_ARCHIVE.value,
    ToolSimulationRiskTier.CLEANUP_COMPACTION.value,
    ToolSimulationRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value,
}

DESTRUCTIVE_TIERS = {
    ToolSimulationRiskTier.CLEANUP_ARCHIVE.value,
    ToolSimulationRiskTier.CLEANUP_COMPACTION.value,
    ToolSimulationRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value,
}

ALLOWED_EVIDENCE_EXPECTATIONS = {item.value for item in ToolSimulationEvidenceExpectation}
ALLOWED_ROLLBACK_STATUSES = {item.value for item in ToolSimulationRollbackStatus}
ALLOWED_TOOL_CATEGORIES = {item.value for item in ToolCategory}
ALLOWED_RISK_TIERS = {item.value for item in ToolSimulationRiskTier}

CAPABILITY_ALLOWED_RISK_TIERS = {
    "read_only": {ToolSimulationRiskTier.READ_ONLY.value},
    "browser_open": {ToolSimulationRiskTier.BROWSER_OPEN.value},
    "browser_search": {ToolSimulationRiskTier.BROWSER_SEARCH.value},
    "app_launch": {ToolSimulationRiskTier.APP_LAUNCH.value},
    "local_file_read": {ToolSimulationRiskTier.LOCAL_FILE_READ.value, ToolSimulationRiskTier.READ_ONLY.value},
    "local_file_write": {ToolSimulationRiskTier.LOCAL_FILE_WRITE.value},
    "external_api_read": {ToolSimulationRiskTier.EXTERNAL_API_READ.value},
    "external_api_write": {ToolSimulationRiskTier.EXTERNAL_API_WRITE.value},
    "memory_read": {ToolSimulationRiskTier.MEMORY_READ.value},
    "memory_write": {ToolSimulationRiskTier.MEMORY_WRITE.value},
    "plugin_execution": {ToolSimulationRiskTier.PLUGIN_EXECUTION.value},
    "cleanup_archive": {ToolSimulationRiskTier.CLEANUP_ARCHIVE.value},
    "cleanup_compaction": {ToolSimulationRiskTier.CLEANUP_COMPACTION.value},
    "destructive_system_change": {ToolSimulationRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value},
    "unknown": {ToolSimulationRiskTier.UNKNOWN.value},
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "can_execute": "can_execute_not_allowed",
    "would_dispatch": "would_dispatch_not_allowed",
    "dispatch_performed": "dispatch_performed_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_created": "simulation_cannot_create_evidence",
    "evidence_provided_by_simulation": "simulation_cannot_create_evidence",
    "verifier_success": "simulation_cannot_mark_verifier_success",
    "verified_success": "simulation_cannot_mark_verifier_success",
    "frontend_authority": "frontend_authority_not_allowed",
    "success": "success_claim_denied",
}

FORBIDDEN_CLAIMS = {
    "legal certification": "legal_certification_claim_denied",
    "compliance certification": "compliance_certification_claim_denied",
    "security certification": "security_certification_claim_denied",
    "official audit result": "official_audit_result_claim_denied",
    "court-admissible": "court_admissible_claim_denied",
    "court admissible": "court_admissible_claim_denied",
    "proof of compliance": "proof_of_compliance_claim_denied",
    "controls are effective": "proof_control_effective_claim_denied",
    "control effectiveness": "proof_control_effective_claim_denied",
    "organization is safe": "proof_organization_safe_claim_denied",
    "organization-safe": "proof_organization_safe_claim_denied",
}


def build_tool_simulation(request: Mapping[str, Any] | None) -> ToolSimulationDecision:
    """Build a pure policy/tool simulation result from caller-supplied metadata.

    This helper does not execute tools, dispatch commands, inspect live
    systems, call browser/app/file/shell/API/model/memory/plugin/MCP systems,
    create approvals, create leases, create evidence, set verifier success,
    mutate runtime state, append journals, create UI, take screenshots, or
    generate images.
    """

    findings: list[SimulationFinding] = []
    if not isinstance(request, Mapping):
        finding = SimulationFinding(
            reason="missing_request",
            field="request",
            message="tool simulation request must be a mapping",
            severity="fail",
        )
        return _decision(validation_status=ToolSimulationStatus.UNSUPPORTED_ACTION.value, findings=(finding,))

    request_copy = deepcopy(dict(request))
    _validate_non_authority_fields(request_copy, findings)
    _validate_no_runtime_generation_requests(request_copy, findings)
    _validate_claims(request_copy, findings)

    simulation_input = _simulation_input(request_copy)
    _validate_required_identity(simulation_input, findings)
    _validate_tool_surface(simulation_input, findings)
    _validate_risk_capability_and_policy(simulation_input, findings)
    _validate_evidence_and_verifier(simulation_input, findings)
    _validate_rollback(simulation_input, findings)

    fallback_expectation = _safe_fallback_expectation(simulation_input.fallback_expectation, findings)
    provider_interstitial_risk = _safe_provider_interstitial_risk(simulation_input, findings)
    status = _simulation_status(simulation_input, findings)
    approval_required = _hint_required(simulation_input.approval_hint)
    lease_required = _hint_required(simulation_input.lease_hint)
    result = ToolSimulationResult(
        simulation_version=TOOL_SIMULATION_VERSION,
        simulation_id=_simulation_id(simulation_input),
        request_id=simulation_input.request_id,
        command_id=simulation_input.command_id,
        raw_user_request=simulation_input.raw_user_request,
        normalized_intent=simulation_input.normalized_intent,
        route_kind=simulation_input.route_kind,
        proposed_action=simulation_input.proposed_action,
        proposed_tool=simulation_input.proposed_tool,
        tool_category=simulation_input.tool_category,
        risk_tier=simulation_input.risk_tier,
        capability_category=simulation_input.capability_category,
        target_app=simulation_input.target_app,
        target_url=simulation_input.target_url,
        search_provider=simulation_input.search_provider,
        query=simulation_input.query,
        policy_simulation_status=status,
        policy_rule_refs=simulation_input.policy_rule_refs,
        policy_decision_hint=simulation_input.policy_decision_hint,
        approval_required=approval_required,
        approval_reason=_text(simulation_input.approval_hint.get("reason")) or None,
        lease_required=lease_required,
        lease_reason=_text(simulation_input.lease_hint.get("reason")) or None,
        proposed_lease_scope=_text(simulation_input.lease_hint.get("scope")) or None,
        proposed_lease_duration=_text(simulation_input.lease_hint.get("duration")) or None,
        evidence_expected=simulation_input.evidence_expectation_hint,
        verifier_expected=simulation_input.verifier_expectation_hint,
        affected_resources=simulation_input.affected_resources,
        blocked_reasons=tuple(finding.reason for finding in findings if finding.severity == "fail"),
        warnings=tuple(finding.reason for finding in findings if finding.severity == "warning"),
        unknowns=_unknowns(simulation_input, findings),
        alternatives=_alternatives(simulation_input),
        operator_attention_required=_operator_attention_required(simulation_input, findings),
        rollback_status=simulation_input.rollback_status,
        timeout_budget_ref=simulation_input.timeout_budget_ref,
        fallback_expectation=fallback_expectation,
        provider_interstitial_risk=provider_interstitial_risk,
        source_refs=simulation_input.source_refs,
        findings=tuple(findings),
    )
    return _decision(
        validation_status=status,
        findings=tuple(findings),
        simulation_input=simulation_input,
        result=result,
    )


def mission_control_input_from_simulation(result: ToolSimulationResult | None) -> dict[str, object]:
    if result is None:
        return {}
    return {
        "request_id": result.request_id,
        "command_id": result.command_id,
        "raw_user_request": result.raw_user_request,
        "normalized_intent": result.normalized_intent,
        "route_kind": result.route_kind,
        "proposed_action": result.proposed_action,
        "proposed_tool": result.proposed_tool,
        "target_app": result.target_app,
        "target_url": result.target_url,
        "search_provider": result.search_provider,
        "query": result.query,
        "affected_resources": result.affected_resources,
        "risk_tier": result.risk_tier,
        "capability_category": result.capability_category,
        "policy_decision_ref": result.policy_rule_refs[0] if result.policy_rule_refs else None,
        "policy_decision_status": result.policy_simulation_status,
        "policy_reason": result.policy_decision_hint,
        "approval_required": result.approval_required,
        "approval_reason": result.approval_reason,
        "lease_required": result.lease_required,
        "lease_scope": result.proposed_lease_scope,
        "lease_duration": result.proposed_lease_duration,
        "evidence_expectation": result.evidence_expected,
        "verifier_expectation": {
            "verifier_required": result.verifier_expected.verifier_required,
            "verifier_name": result.verifier_expected.verifier_name,
            "verifier_postcondition": result.verifier_expected.verifier_postcondition,
            "verifier_failure_modes": result.verifier_expected.verifier_failure_modes,
            "verifier_success_required_for_completion": (
                result.verifier_expected.verifier_success_required_for_completion
            ),
        },
        "timeout_budget_ref": result.timeout_budget_ref,
        "fallback_expectation": dict(result.fallback_expectation),
        "rollback_status": result.rollback_status,
        "provider_interstitial_risk": dict(result.provider_interstitial_risk),
        "limitations": ("simulation_result_is_not_execution",),
        "unknowns": result.unknowns,
        "alternatives": tuple(alternative.label for alternative in result.alternatives),
        "operator_options": _mission_control_options(result),
        "source_refs": result.source_refs,
    }


def _simulation_input(request: Mapping[str, Any]) -> ToolSimulationInput:
    return ToolSimulationInput(
        request_id=_text(request.get("request_id")) or None,
        command_id=_text(request.get("command_id")) or None,
        raw_user_request=_text(request.get("raw_user_request")) or None,
        normalized_intent=_text(request.get("normalized_intent")) or None,
        route_kind=_text(request.get("route_kind")) or None,
        proposed_action=_text(request.get("proposed_action")) or None,
        proposed_tool=_text(request.get("proposed_tool")) or None,
        tool_category=_text(request.get("tool_category")) or ToolCategory.UNKNOWN_TOOL.value,
        capability_category=_text(request.get("capability_category")) or None,
        risk_tier=_text(request.get("risk_tier")) or ToolSimulationRiskTier.UNKNOWN.value,
        target_app=_text(request.get("target_app")) or None,
        target_url=_text(request.get("target_url")) or None,
        search_provider=_text(request.get("search_provider")) or None,
        query=_text(request.get("query")) or None,
        affected_resources=_strings(request.get("affected_resources")),
        data_sensitivity=_text(request.get("data_sensitivity")) or None,
        policy_rule_refs=_strings(request.get("policy_rule_refs")),
        policy_decision_hint=_text(request.get("policy_decision_hint")) or None,
        approval_hint=_mapping(request.get("approval_hint")),
        lease_hint=_mapping(request.get("lease_hint")),
        evidence_expectation_hint=_strings(request.get("evidence_expectation_hint")),
        verifier_expectation_hint=_verifier_expectation(request.get("verifier_expectation_hint")),
        timeout_budget_ref=_text(request.get("timeout_budget_ref")) or None,
        rollback_status=_text(request.get("rollback_status")) or ToolSimulationRollbackStatus.UNKNOWN.value,
        provider_interstitial_risk=_mapping(request.get("provider_interstitial_risk")),
        fallback_expectation=_mapping(request.get("fallback_expectation")),
        source_refs=_strings(request.get("source_refs")),
        claims=_strings(request.get("claims")),
    )


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    findings: list[SimulationFinding],
) -> None:
    for field_name, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field_name) is True:
            _add_finding(
                findings,
                reason,
                field_name,
                f"{field_name} cannot grant authority, dispatch, evidence, verification, or success",
                severity="fail",
            )
    if request.get("execution_permission") not in (None, "", TOOL_SIMULATION_EXECUTION_PERMISSION):
        _add_finding(
            findings,
            "execution_permission_not_granted_by_tool_simulation_required",
            "execution_permission",
            "tool simulation cannot grant execution permission",
            severity="fail",
        )


def _validate_no_runtime_generation_requests(
    request: Mapping[str, Any],
    findings: list[SimulationFinding],
) -> None:
    denied_flags = {
        "image_generation_requested": "image_generation_request_denied",
        "screenshot_requested": "screenshot_request_denied",
        "visual_asset_requested": "visual_asset_request_denied",
        "model_call_requested": "model_call_request_denied",
        "tool_call_requested": "tool_call_request_denied",
        "mcp_call_requested": "mcp_call_request_denied",
        "api_call_requested": "api_call_request_denied",
        "memory_access_requested": "memory_access_request_denied",
    }
    for field_name, reason in denied_flags.items():
        if request.get(field_name) is True:
            _add_finding(
                findings,
                reason,
                field_name,
                "tool simulation is code/text/docs only and non-executing",
                severity="fail",
            )


def _validate_claims(
    request: Mapping[str, Any],
    findings: list[SimulationFinding],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    for phrase, reason in FORBIDDEN_CLAIMS.items():
        if phrase in claims:
            _add_finding(
                findings,
                reason,
                "claims",
                f"tool simulation cannot claim {phrase}",
                severity="fail",
            )


def _validate_required_identity(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> None:
    if not simulation_input.request_id:
        _add_finding(findings, "request_id_required", "request_id", "request_id is required", severity="fail")
    if not simulation_input.command_id:
        _add_finding(findings, "command_id_required", "command_id", "command_id is required", severity="fail")
    if not simulation_input.normalized_intent:
        _add_finding(
            findings,
            "normalized_intent_required_for_simulation",
            "normalized_intent",
            "tool simulation requires normalized_intent",
            severity="fail",
        )


def _validate_tool_surface(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> None:
    tool = (simulation_input.proposed_tool or "").lower()
    intent = (simulation_input.normalized_intent or "").lower()
    raw = (simulation_input.raw_user_request or "").strip().lower()
    if raw in RAW_CONTROL_COMMANDS or tool in RAW_CONTROL_COMMANDS or intent in RAW_CONTROL_COMMANDS:
        _add_finding(
            findings,
            "raw_control_command_not_simulatable_as_direct_execution",
            "proposed_tool",
            "raw control commands must remain lifecycle records, not direct tool simulation",
            severity="fail",
        )
    if tool in QUARANTINED_TOOLS or intent in QUARANTINED_TOOLS:
        _add_finding(
            findings,
            "quarantined_tool_not_simulatable_as_executable",
            "proposed_tool",
            "click/browser_click/desktop_click remain quarantined",
            severity="fail",
        )
    if tool in VISION_LIVE_TOOLS or intent in VISION_LIVE_TOOLS:
        _add_finding(
            findings,
            "vision_live_feed_not_simulatable_without_future_privacy_gate",
            "proposed_tool",
            "vision/live feed is unavailable without a future explicit privacy gate",
            severity="fail",
        )
    if simulation_input.tool_category not in ALLOWED_TOOL_CATEGORIES:
        _add_finding(
            findings,
            "unknown_tool_category",
            "tool_category",
            simulation_input.tool_category,
            severity="fail",
        )
    if simulation_input.tool_category == ToolCategory.UNKNOWN_TOOL.value or tool not in SUPPORTED_TOOLS:
        _add_finding(
            findings,
            "unsupported_tool",
            "proposed_tool",
            "tool is not supported by the pure simulation contract",
            severity="fail",
        )


def _validate_risk_capability_and_policy(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> None:
    risk = simulation_input.risk_tier
    capability = simulation_input.capability_category or ""
    if risk not in ALLOWED_RISK_TIERS:
        _add_finding(findings, "unknown_risk_tier", "risk_tier", risk, severity="fail")
    if risk == ToolSimulationRiskTier.UNKNOWN.value:
        _add_finding(
            findings,
            "unknown_risk_tier",
            "risk_tier",
            "unknown risk blocks tool simulation",
            severity="fail",
        )
    allowed = CAPABILITY_ALLOWED_RISK_TIERS.get(capability)
    if allowed is not None and risk not in allowed:
        _add_finding(
            findings,
            "capability_risk_tier_mismatch",
            "capability_category",
            f"{capability} cannot use risk tier {risk}",
            severity="fail",
        )
    for capability_name, reason in {
        "external_api_write": "external_api_write_cannot_be_read_only",
        "plugin_execution": "plugin_execution_cannot_be_read_only",
        "memory_write": "memory_write_cannot_be_read_only",
    }.items():
        if capability == capability_name and risk == ToolSimulationRiskTier.READ_ONLY.value:
            _add_finding(
                findings,
                reason,
                "risk_tier",
                f"{capability_name} cannot be simulated as read_only",
                severity="fail",
            )
    hint = (simulation_input.policy_decision_hint or "").lower()
    refs = " ".join(simulation_input.policy_rule_refs).lower()
    if hint in {"blocked", "denied", "policy_denied"} or ".blocked" in refs:
        _add_finding(
            findings,
            "policy_denied_cannot_be_overridden_by_simulation",
            "policy_decision_hint",
            "policy denied remains denied in tool simulation",
            severity="fail",
        )


def _validate_evidence_and_verifier(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> None:
    for item in simulation_input.evidence_expectation_hint:
        if item not in ALLOWED_EVIDENCE_EXPECTATIONS:
            _add_finding(findings, "unknown_evidence_expectation", "evidence_expectation_hint", item, severity="fail")
    if simulation_input.risk_tier in SIDE_EFFECTING_RISK_TIERS and not simulation_input.affected_resources:
        _add_finding(
            findings,
            "affected_resources_required_for_side_effecting_simulation",
            "affected_resources",
            "side-effecting simulation requires affected resources",
            severity="fail",
        )
    if simulation_input.risk_tier in SIDE_EFFECTING_RISK_TIERS and not simulation_input.evidence_expectation_hint:
        _add_finding(
            findings,
            "evidence_expectation_required_for_side_effecting_simulation",
            "evidence_expectation_hint",
            "side-effecting simulation requires evidence expectation",
            severity="fail",
        )
    if simulation_input.risk_tier in HIGH_RISK_TIERS:
        verifier = simulation_input.verifier_expectation_hint
        if not verifier.verifier_required or not verifier.verifier_name:
            _add_finding(
                findings,
                "verifier_expectation_required_for_high_risk_simulation",
                "verifier_expectation_hint",
                "high-risk simulation requires verifier expectation",
                severity="fail",
            )


def _validate_rollback(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> None:
    if simulation_input.rollback_status not in ALLOWED_ROLLBACK_STATUSES:
        _add_finding(findings, "unknown_rollback_status", "rollback_status", simulation_input.rollback_status)
    if simulation_input.risk_tier in DESTRUCTIVE_TIERS:
        if simulation_input.rollback_status in {
            ToolSimulationRollbackStatus.UNKNOWN.value,
            ToolSimulationRollbackStatus.UNAVAILABLE.value,
        }:
            _add_finding(
                findings,
                "destructive_action_requires_known_rollback_or_blocked_policy",
                "rollback_status",
                "destructive simulation requires known rollback/staging or blocked policy",
                severity="fail",
            )


def _safe_fallback_expectation(
    fallback: Mapping[str, Any],
    findings: list[SimulationFinding],
) -> Mapping[str, Any]:
    safe = deepcopy(dict(fallback))
    if safe.get("fallback_is_success") is True:
        _add_finding(
            findings,
            "fallback_cannot_be_success",
            "fallback_expectation.fallback_is_success",
            "timeout, fallback, and retry cannot be success in simulation",
            severity="fail",
        )
    safe["fallback_is_success"] = False
    return MappingProxyType(safe)


def _safe_provider_interstitial_risk(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> Mapping[str, Any]:
    safe = deepcopy(dict(simulation_input.provider_interstitial_risk))
    provider = (simulation_input.search_provider or _text(safe.get("provider"))).lower()
    if provider == "google":
        safe["provider"] = "google"
        if not _text(safe.get("known_risk")) or safe.get("known_risk") == "not_applicable":
            safe["known_risk"] = "google_sorry_bot_challenge"
        safe.setdefault("known_path", "/sorry")
        safe.setdefault("verification_blocker", "search_verification_blocked_by_provider")
        safe.setdefault("fallback_allowed", False)
        safe.setdefault("fallback_attempted", False)
    if safe.get("bypass_allowed") is True or safe.get("challenge_bypass_allowed") is True:
        _add_finding(
            findings,
            "provider_interstitial_bypass_not_allowed",
            "provider_interstitial_risk.bypass_allowed",
            "provider interstitial risk cannot bypass provider challenge",
            severity="fail",
        )
    safe["bypass_allowed"] = False
    safe["challenge_bypass_allowed"] = False
    return MappingProxyType(safe)


def _simulation_status(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> str:
    reasons = {finding.reason for finding in findings if finding.severity == "fail"}
    if "raw_control_command_not_simulatable_as_direct_execution" in reasons:
        return ToolSimulationStatus.UNSUPPORTED_ACTION.value
    if "quarantined_tool_not_simulatable_as_executable" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_QUARANTINED_TOOL.value
    if "vision_live_feed_not_simulatable_without_future_privacy_gate" in reasons:
        return ToolSimulationStatus.UNSUPPORTED_TOOL.value
    if "unsupported_tool" in reasons or "unknown_tool_category" in reasons:
        return ToolSimulationStatus.UNSUPPORTED_TOOL.value
    if "unknown_risk_tier" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_UNKNOWN_RISK.value
    if "affected_resources_required_for_side_effecting_simulation" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_MISSING_RESOURCE_SCOPE.value
    if "evidence_expectation_required_for_side_effecting_simulation" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_MISSING_EVIDENCE_EXPECTATION.value
    if "verifier_expectation_required_for_high_risk_simulation" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_MISSING_VERIFIER_EXPECTATION.value
    if "destructive_action_requires_known_rollback_or_blocked_policy" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_UNAVAILABLE_ROLLBACK.value
    if "provider_interstitial_bypass_not_allowed" in reasons:
        return ToolSimulationStatus.BLOCKED_BY_PROVIDER_INTERSTITIAL_RISK.value
    policy_reasons = {
        "policy_denied_cannot_be_overridden_by_simulation",
        "capability_risk_tier_mismatch",
        "external_api_write_cannot_be_read_only",
        "plugin_execution_cannot_be_read_only",
        "memory_write_cannot_be_read_only",
        "authority_must_be_false",
        "runtime_dispatch_not_allowed",
        "can_execute_not_allowed",
        "would_dispatch_not_allowed",
        "dispatch_performed_not_allowed",
        "approval_grant_not_allowed",
        "capability_grant_not_allowed",
        "lease_grant_not_allowed",
        "simulation_cannot_create_evidence",
        "simulation_cannot_mark_verifier_success",
        "frontend_authority_not_allowed",
        "success_claim_denied",
        "fallback_cannot_be_success",
    }
    compliance_reasons = set(FORBIDDEN_CLAIMS.values())
    if reasons & (policy_reasons | compliance_reasons):
        return ToolSimulationStatus.BLOCKED_BY_POLICY.value
    if _hint_required(simulation_input.approval_hint):
        return ToolSimulationStatus.APPROVAL_REQUIRED.value
    if _hint_required(simulation_input.lease_hint):
        return ToolSimulationStatus.LEASE_REQUIRED.value
    if simulation_input.risk_tier in SIDE_EFFECTING_RISK_TIERS - {ToolSimulationRiskTier.APP_LAUNCH.value}:
        return ToolSimulationStatus.POLICY_ALLOWS_BUT_REQUIRES_EXECUTION_GATE.value
    return ToolSimulationStatus.SIMULATION_READY.value


def _unknowns(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> tuple[str, ...]:
    unknowns: list[str] = []
    if simulation_input.risk_tier == ToolSimulationRiskTier.UNKNOWN.value:
        unknowns.append("risk_tier")
    if not simulation_input.policy_rule_refs:
        unknowns.append("policy_rule_refs")
    unknowns.extend(finding.reason for finding in findings if "unknown" in finding.reason)
    return tuple(dict.fromkeys(unknowns))


def _alternatives(simulation_input: ToolSimulationInput) -> tuple[SimulationAlternative, ...]:
    tool = (simulation_input.proposed_tool or "").lower()
    if tool in QUARANTINED_TOOLS:
        return (
            SimulationAlternative(
                label="Resolve target before click",
                reason="Click actions require a future explicit target-resolution policy.",
                proposed_intent="ask_clarification",
            ),
        )
    if simulation_input.risk_tier in DESTRUCTIVE_TIERS:
        return (
            SimulationAlternative(
                label="Request read-only diagnostic first",
                reason="Read-only diagnostics preserve evidence boundaries before destructive action.",
                proposed_intent="read_only_diagnostic",
            ),
        )
    return (
        SimulationAlternative(
            label="Request dry-run details",
            reason="Operator can inspect policy, evidence, verifier, and resource expectations before execution.",
            proposed_intent="request_dry_run_details",
        ),
    )


def _operator_attention_required(
    simulation_input: ToolSimulationInput,
    findings: list[SimulationFinding],
) -> bool:
    if simulation_input.risk_tier == ToolSimulationRiskTier.UNKNOWN.value:
        return True
    if _hint_required(simulation_input.approval_hint) or _hint_required(simulation_input.lease_hint):
        return True
    return any(finding.severity == "fail" for finding in findings)


def _mission_control_options(result: ToolSimulationResult) -> tuple[str, ...]:
    if result.policy_simulation_status.startswith("blocked") or result.policy_simulation_status.startswith("unsupported"):
        return ("request_dry_run_details", "request_safer_alternative", "cancel", "block")
    if result.approval_required:
        return ("approve_once", "deny", "request_dry_run_details", "request_safer_alternative", "cancel")
    if result.lease_required:
        return (
            "create_scoped_lease_candidate",
            "approve_once",
            "deny",
            "request_dry_run_details",
            "cancel",
        )
    return ("request_dry_run_details", "request_safer_alternative", "cancel")


def _decision(
    *,
    validation_status: str,
    findings: tuple[SimulationFinding, ...],
    simulation_input: ToolSimulationInput | None = None,
    result: ToolSimulationResult | None = None,
) -> ToolSimulationDecision:
    return ToolSimulationDecision(
        simulation_version=TOOL_SIMULATION_VERSION,
        validation_status=validation_status,
        failure_reasons=tuple(finding.reason for finding in findings),
        failures=findings,
        simulation_input=simulation_input,
        result=result,
    )


def _simulation_id(simulation_input: ToolSimulationInput) -> str:
    command_id = simulation_input.command_id or "unknown-command"
    proposed_tool = simulation_input.proposed_tool or "unknown-tool"
    return f"tool-simulation:{command_id}:{proposed_tool}"


def _hint_required(value: Mapping[str, Any]) -> bool:
    return value.get("required") is True


def _verifier_expectation(value: Any) -> ToolSimulationVerifierExpectation:
    if not isinstance(value, Mapping):
        return ToolSimulationVerifierExpectation(
            verifier_required=False,
            verifier_name="",
            verifier_postcondition="",
        )
    return ToolSimulationVerifierExpectation(
        verifier_required=value.get("verifier_required") is True,
        verifier_name=_text(value.get("verifier_name")),
        verifier_postcondition=_text(value.get("verifier_postcondition")),
        verifier_failure_modes=_strings(value.get("verifier_failure_modes")),
        verifier_success_required_for_completion=value.get("verifier_success_required_for_completion") is True,
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return MappingProxyType({})
    return MappingProxyType(deepcopy(dict(value)))


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = (value,)
    elif isinstance(value, (list, tuple, set)):
        items = tuple(value)
    else:
        items = (value,)
    strings: list[str] = []
    for item in items:
        text = _text(item)
        if text:
            strings.append(text)
    return tuple(strings)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _add_finding(
    findings: list[SimulationFinding],
    reason: str,
    field: str,
    message: str,
    *,
    severity: str = "warning",
) -> None:
    findings.append(SimulationFinding(reason=reason, field=field, message=message, severity=severity))
