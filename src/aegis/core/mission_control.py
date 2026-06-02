from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, unique
from types import MappingProxyType
from typing import Any, Mapping


MISSION_CONTROL_CONTRACT_VERSION = "mission-control-dry-run-preview/1"
MISSION_CONTROL_EXECUTION_PERMISSION = "not_granted_by_mission_control"


@unique
class MissionControlRiskTier(str, Enum):
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
class MissionControlOperatorOption(str, Enum):
    APPROVE_ONCE = "approve_once"
    DENY = "deny"
    ASK_CLARIFICATION = "ask_clarification"
    REQUEST_DRY_RUN_DETAILS = "request_dry_run_details"
    REQUEST_SAFER_ALTERNATIVE = "request_safer_alternative"
    CREATE_SCOPED_LEASE_CANDIDATE = "create_scoped_lease_candidate"
    CANCEL = "cancel"
    BLOCK = "block"


@unique
class MissionControlEvidenceExpectation(str, Enum):
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
class MissionControlRollbackStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"
    MANUAL_ONLY = "manual_only"
    STAGING_REQUIRED = "staging_required"
    BACKUP_REQUIRED = "backup_required"
    REVERSIBLE_WITH_PLAN = "reversible_with_plan"
    COMPENSATING_ACTION_ONLY = "compensating_action_only"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MissionControlVerifierExpectation:
    verifier_required: bool
    verifier_name: str
    verifier_postcondition: str
    verifier_failure_modes: tuple[str, ...] = ()
    verifier_success_required_for_completion: bool = False


@dataclass(frozen=True)
class MissionControlInput:
    request_id: str | None
    command_id: str | None
    raw_user_request: str | None
    normalized_intent: str | None
    route_kind: str | None
    proposed_action: str | None
    proposed_tool: str | None
    target_app: str | None = None
    target_url: str | None = None
    search_provider: str | None = None
    query: str | None = None
    affected_resources: tuple[str, ...] = ()
    risk_tier: str = MissionControlRiskTier.UNKNOWN.value
    capability_category: str | None = None
    policy_decision_ref: str | None = None
    policy_decision_status: str | None = None
    policy_reason: str | None = None
    approval_required: bool = False
    approval_reason: str | None = None
    lease_required: bool = False
    lease_scope: str | None = None
    lease_duration: str | None = None
    evidence_expectation: tuple[str, ...] = ()
    verifier_expectation: MissionControlVerifierExpectation = field(
        default_factory=lambda: MissionControlVerifierExpectation(
            verifier_required=False,
            verifier_name="",
            verifier_postcondition="",
        )
    )
    timeout_budget_ref: str | None = None
    fallback_expectation: Mapping[str, Any] = field(default_factory=dict)
    rollback_status: str = MissionControlRollbackStatus.UNKNOWN.value
    rollback_plan_ref: str | None = None
    provider_interstitial_risk: Mapping[str, Any] = field(default_factory=dict)
    data_sensitivity: str | None = None
    privacy_notes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    operator_options: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_resources", _strings(self.affected_resources))
        object.__setattr__(self, "evidence_expectation", _strings(self.evidence_expectation))
        object.__setattr__(self, "privacy_notes", _strings(self.privacy_notes))
        object.__setattr__(self, "limitations", _strings(self.limitations))
        object.__setattr__(self, "unknowns", _strings(self.unknowns))
        object.__setattr__(self, "alternatives", _strings(self.alternatives))
        object.__setattr__(self, "operator_options", _strings(self.operator_options))
        object.__setattr__(self, "source_refs", _strings(self.source_refs))
        object.__setattr__(self, "fallback_expectation", MappingProxyType(deepcopy(dict(self.fallback_expectation))))
        object.__setattr__(
            self,
            "provider_interstitial_risk",
            MappingProxyType(deepcopy(dict(self.provider_interstitial_risk))),
        )


@dataclass(frozen=True)
class MissionControlValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class MissionControlPreviewContract:
    request_id: str | None
    command_id: str | None
    raw_user_request: str | None
    normalized_intent: str | None
    route_kind: str | None
    proposed_action: str | None
    proposed_tool: str | None
    target_app: str | None
    target_url: str | None
    search_provider: str | None
    query: str | None
    affected_resources: tuple[str, ...]
    risk_tier: str
    capability_category: str | None
    policy_decision_ref: str | None
    policy_decision_status: str | None
    policy_reason: str | None
    approval_required: bool
    approval_reason: str | None
    lease_required: bool
    lease_scope: str | None
    lease_duration: str | None
    evidence_expectation: tuple[str, ...]
    verifier_expectation: MissionControlVerifierExpectation
    timeout_budget_ref: str | None
    fallback_expectation: Mapping[str, Any]
    rollback_status: str
    rollback_plan_ref: str | None
    provider_interstitial_risk: Mapping[str, Any]
    data_sensitivity: str | None
    privacy_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    alternatives: tuple[str, ...]
    operator_options: tuple[str, ...]
    source_refs: tuple[str, ...]
    actions_performed: tuple[str, ...] = ()
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = MISSION_CONTROL_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_preview: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_operator_decision_when_required: bool = True
    fallback_is_success: bool = False
    provider_interstitial_bypass_allowed: bool = False
    compliance_certification_claim_allowed: bool = False
    image_generation_used: bool = False
    model_call_used: bool = False
    tool_call_used: bool = False
    screenshot_created: bool = False
    visual_asset_created: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_expectation", MappingProxyType(deepcopy(dict(self.fallback_expectation))))
        object.__setattr__(
            self,
            "provider_interstitial_risk",
            MappingProxyType(deepcopy(dict(self.provider_interstitial_risk))),
        )


@dataclass(frozen=True)
class MissionControlDecision:
    contract_version: str
    validation_status: str
    failure_reasons: tuple[str, ...]
    failures: tuple[MissionControlValidationFailure, ...]
    mission_input: MissionControlInput | None = None
    preview_contract: MissionControlPreviewContract | None = None
    requires_operator_attention: bool = False
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = MISSION_CONTROL_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_preview: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_operator_decision_when_required: bool = True


HIGH_RISK_TIERS = {
    MissionControlRiskTier.LOCAL_FILE_WRITE.value,
    MissionControlRiskTier.EXTERNAL_API_WRITE.value,
    MissionControlRiskTier.MEMORY_WRITE.value,
    MissionControlRiskTier.PLUGIN_EXECUTION.value,
    MissionControlRiskTier.CLEANUP_ARCHIVE.value,
    MissionControlRiskTier.CLEANUP_COMPACTION.value,
    MissionControlRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value,
}

DESTRUCTIVE_TIERS = {
    MissionControlRiskTier.CLEANUP_ARCHIVE.value,
    MissionControlRiskTier.CLEANUP_COMPACTION.value,
    MissionControlRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value,
}

CAPABILITY_ALLOWED_RISK_TIERS = {
    "read_only": {MissionControlRiskTier.READ_ONLY.value},
    "browser_open": {MissionControlRiskTier.BROWSER_OPEN.value},
    "browser_search": {MissionControlRiskTier.BROWSER_SEARCH.value},
    "app_launch": {MissionControlRiskTier.APP_LAUNCH.value},
    "local_file_read": {MissionControlRiskTier.LOCAL_FILE_READ.value, MissionControlRiskTier.READ_ONLY.value},
    "local_file_write": {MissionControlRiskTier.LOCAL_FILE_WRITE.value},
    "external_api_read": {MissionControlRiskTier.EXTERNAL_API_READ.value},
    "external_api_write": {MissionControlRiskTier.EXTERNAL_API_WRITE.value},
    "memory_read": {MissionControlRiskTier.MEMORY_READ.value},
    "memory_write": {MissionControlRiskTier.MEMORY_WRITE.value},
    "plugin_execution": {MissionControlRiskTier.PLUGIN_EXECUTION.value},
    "cleanup_archive": {MissionControlRiskTier.CLEANUP_ARCHIVE.value},
    "cleanup_compaction": {MissionControlRiskTier.CLEANUP_COMPACTION.value},
    "destructive_system_change": {MissionControlRiskTier.DESTRUCTIVE_SYSTEM_CHANGE.value},
    "unknown": {MissionControlRiskTier.UNKNOWN.value},
}

ALLOWED_OPERATOR_OPTIONS = {item.value for item in MissionControlOperatorOption}
ALLOWED_EVIDENCE_EXPECTATIONS = {item.value for item in MissionControlEvidenceExpectation}
ALLOWED_ROLLBACK_STATUSES = {item.value for item in MissionControlRollbackStatus}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_preview": "preview_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "preview_cannot_provide_evidence",
    "verifier_success": "preview_cannot_mark_verifier_success",
    "verified_success": "preview_cannot_mark_verifier_success",
    "frontend_authority": "frontend_authority_not_allowed",
    "success": "success_claim_denied",
}

FORBIDDEN_CLAIMS = {
    "legal certification": "legal_certification_claim_denied",
    "compliance certification": "compliance_certification_claim_denied",
    "security certification": "security_certification_claim_denied",
    "court-admissible": "court_admissible_claim_denied",
    "court admissible": "court_admissible_claim_denied",
    "official audit result": "official_audit_result_claim_denied",
    "proof of compliance": "proof_of_compliance_claim_denied",
    "controls are effective": "proof_control_effective_claim_denied",
    "control effectiveness": "proof_control_effective_claim_denied",
    "certified compliant": "compliance_certification_claim_denied",
}


def build_mission_control_preview(request: Mapping[str, Any] | None) -> MissionControlDecision:
    """Validate caller-supplied Mission Control dry-run preview metadata.

    This helper is pure. It does not execute tools, call models, call APIs,
    approve actions, create leases, create evidence, update verifier state,
    mutate runtime state, append journal events, render UI, create screenshots,
    or generate image/design assets.
    """

    failures: list[MissionControlValidationFailure] = []
    if not isinstance(request, Mapping):
        failure = MissionControlValidationFailure(
            reason="missing_request",
            field="request",
            message="Mission Control preview request must be a mapping",
        )
        return _decision(validation_status="failed_validation", failures=(failure,))

    request_copy = deepcopy(dict(request))
    _validate_non_authority_fields(request_copy, failures)
    _validate_no_generation_requests(request_copy, failures)
    _validate_claims(request_copy, failures)

    mission_input = _mission_input(request_copy)
    _validate_required_identity(mission_input, failures)
    _validate_risk_and_capability(mission_input, failures)
    _validate_policy_relationship(mission_input, failures)
    _validate_evidence_and_verifier(mission_input, failures)
    _validate_rollback(mission_input, failures)
    _validate_operator_options(mission_input, failures)

    fallback_expectation = _safe_fallback_expectation(mission_input.fallback_expectation, failures)
    provider_interstitial_risk = _safe_provider_interstitial_risk(
        mission_input,
        failures,
    )
    preview_contract = MissionControlPreviewContract(
        request_id=mission_input.request_id,
        command_id=mission_input.command_id,
        raw_user_request=mission_input.raw_user_request,
        normalized_intent=mission_input.normalized_intent,
        route_kind=mission_input.route_kind,
        proposed_action=mission_input.proposed_action,
        proposed_tool=mission_input.proposed_tool,
        target_app=mission_input.target_app,
        target_url=mission_input.target_url,
        search_provider=mission_input.search_provider,
        query=mission_input.query,
        affected_resources=mission_input.affected_resources,
        risk_tier=mission_input.risk_tier,
        capability_category=mission_input.capability_category,
        policy_decision_ref=mission_input.policy_decision_ref,
        policy_decision_status=mission_input.policy_decision_status,
        policy_reason=mission_input.policy_reason,
        approval_required=mission_input.approval_required,
        approval_reason=mission_input.approval_reason,
        lease_required=mission_input.lease_required,
        lease_scope=mission_input.lease_scope,
        lease_duration=mission_input.lease_duration,
        evidence_expectation=mission_input.evidence_expectation,
        verifier_expectation=mission_input.verifier_expectation,
        timeout_budget_ref=mission_input.timeout_budget_ref,
        fallback_expectation=fallback_expectation,
        rollback_status=mission_input.rollback_status,
        rollback_plan_ref=mission_input.rollback_plan_ref,
        provider_interstitial_risk=provider_interstitial_risk,
        data_sensitivity=mission_input.data_sensitivity,
        privacy_notes=mission_input.privacy_notes,
        limitations=mission_input.limitations,
        unknowns=mission_input.unknowns,
        alternatives=mission_input.alternatives,
        operator_options=mission_input.operator_options,
        source_refs=mission_input.source_refs,
    )

    validation_status = _validation_status(mission_input, failures)
    return _decision(
        validation_status=validation_status,
        failures=tuple(failures),
        mission_input=mission_input,
        preview_contract=preview_contract,
        requires_operator_attention=mission_input.risk_tier == MissionControlRiskTier.UNKNOWN.value,
    )


def _mission_input(request: Mapping[str, Any]) -> MissionControlInput:
    return MissionControlInput(
        request_id=_text(request.get("request_id")) or None,
        command_id=_text(request.get("command_id")) or None,
        raw_user_request=_text(request.get("raw_user_request")) or None,
        normalized_intent=_text(request.get("normalized_intent")) or None,
        route_kind=_text(request.get("route_kind")) or None,
        proposed_action=_text(request.get("proposed_action")) or None,
        proposed_tool=_text(request.get("proposed_tool")) or None,
        target_app=_text(request.get("target_app")) or None,
        target_url=_text(request.get("target_url")) or None,
        search_provider=_text(request.get("search_provider")) or None,
        query=_text(request.get("query")) or None,
        affected_resources=_strings(request.get("affected_resources")),
        risk_tier=_text(request.get("risk_tier")) or MissionControlRiskTier.UNKNOWN.value,
        capability_category=_text(request.get("capability_category")) or None,
        policy_decision_ref=_text(request.get("policy_decision_ref")) or None,
        policy_decision_status=_text(request.get("policy_decision_status")) or None,
        policy_reason=_text(request.get("policy_reason")) or None,
        approval_required=request.get("approval_required") is True,
        approval_reason=_text(request.get("approval_reason")) or None,
        lease_required=request.get("lease_required") is True,
        lease_scope=_text(request.get("lease_scope")) or None,
        lease_duration=_text(request.get("lease_duration")) or None,
        evidence_expectation=_strings(request.get("evidence_expectation")),
        verifier_expectation=_verifier_expectation(request.get("verifier_expectation")),
        timeout_budget_ref=_text(request.get("timeout_budget_ref")) or None,
        fallback_expectation=_mapping(request.get("fallback_expectation")),
        rollback_status=_text(request.get("rollback_status")) or MissionControlRollbackStatus.UNKNOWN.value,
        rollback_plan_ref=_text(request.get("rollback_plan_ref")) or None,
        provider_interstitial_risk=_mapping(request.get("provider_interstitial_risk")),
        data_sensitivity=_text(request.get("data_sensitivity")) or None,
        privacy_notes=_strings(request.get("privacy_notes")),
        limitations=_strings(request.get("limitations")),
        unknowns=_strings(request.get("unknowns")),
        alternatives=_strings(request.get("alternatives")),
        operator_options=_strings(request.get("operator_options")),
        source_refs=_strings(request.get("source_refs")),
    )


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[MissionControlValidationFailure],
) -> None:
    for field_name, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority, evidence, verification, or success",
            )
    if request.get("execution_permission") not in (
        None,
        "",
        MISSION_CONTROL_EXECUTION_PERMISSION,
    ):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_mission_control_required",
            "execution_permission",
            "Mission Control cannot grant execution permission",
        )
    if request.get("requires_policy_check") is False:
        _add_failure(
            failures,
            "policy_check_required_for_preview",
            "requires_policy_check",
            "Mission Control previews require backend policy validation",
        )
    if request.get("requires_backend_validation") is False:
        _add_failure(
            failures,
            "backend_validation_required_for_preview",
            "requires_backend_validation",
            "Mission Control previews require backend validation",
        )


def _validate_no_generation_requests(
    request: Mapping[str, Any],
    failures: list[MissionControlValidationFailure],
) -> None:
    denied_flags = {
        "image_generation_requested": "image_generation_request_denied",
        "screenshot_requested": "screenshot_request_denied",
        "visual_asset_requested": "visual_asset_request_denied",
        "model_call_requested": "model_call_request_denied",
        "tool_call_requested": "tool_call_request_denied",
    }
    for field_name, reason in denied_flags.items():
        if request.get(field_name) is True:
            _add_failure(failures, reason, field_name, "Mission Control preview is text/code/docs only")
    if _strings(request.get("model_calls_requested")):
        _add_failure(
            failures,
            "model_call_request_denied",
            "model_calls_requested",
            "Mission Control preview does not request model calls",
        )
    if _strings(request.get("requested_tools")):
        _add_failure(
            failures,
            "tool_call_request_denied",
            "requested_tools",
            "Mission Control preview does not request tool calls",
        )


def _validate_claims(
    request: Mapping[str, Any],
    failures: list[MissionControlValidationFailure],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    for phrase, reason in FORBIDDEN_CLAIMS.items():
        if phrase in claims:
            _add_failure(
                failures,
                reason,
                "claims",
                f"Mission Control preview cannot claim {phrase}",
            )


def _validate_required_identity(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    if not mission_input.request_id:
        _add_failure(failures, "request_id_required", "request_id", "request_id is required")
    if not mission_input.command_id:
        _add_failure(failures, "command_id_required", "command_id", "command_id is required")
    if not mission_input.normalized_intent and mission_input.proposed_tool:
        _add_failure(
            failures,
            "normalized_intent_required_for_executable_preview",
            "normalized_intent",
            "executable proposals require normalized_intent",
        )
    if not mission_input.policy_decision_ref and mission_input.risk_tier not in {
        MissionControlRiskTier.READ_ONLY.value,
        MissionControlRiskTier.UNKNOWN.value,
    }:
        _add_failure(
            failures,
            "policy_decision_ref_required_for_risky_preview",
            "policy_decision_ref",
            "risky previews require a policy decision reference",
        )


def _validate_risk_and_capability(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    risk = mission_input.risk_tier
    capability = mission_input.capability_category or ""
    known_risk = risk in {item.value for item in MissionControlRiskTier}
    if not known_risk:
        _add_failure(failures, "unknown_risk_tier", "risk_tier", risk)
    if risk == MissionControlRiskTier.UNKNOWN.value:
        _add_failure(
            failures,
            "unknown_risk_requires_operator_attention",
            "risk_tier",
            "unknown risk previews require operator attention",
        )
    allowed = CAPABILITY_ALLOWED_RISK_TIERS.get(capability)
    if allowed is not None and risk not in allowed:
        _add_failure(
            failures,
            "capability_risk_tier_mismatch",
            "capability_category",
            f"{capability} cannot use risk tier {risk}",
        )
    if risk in HIGH_RISK_TIERS and not mission_input.affected_resources:
        _add_failure(
            failures,
            "affected_resources_required_for_high_risk_preview",
            "affected_resources",
            "high-risk previews require affected resources",
        )
    for capability_name, reason in {
        "external_api_write": "external_api_write_cannot_be_read_only",
        "plugin_execution": "plugin_execution_cannot_be_read_only",
        "memory_write": "memory_write_cannot_be_read_only",
    }.items():
        if capability == capability_name and risk == MissionControlRiskTier.READ_ONLY.value:
            _add_failure(
                failures,
                reason,
                "risk_tier",
                f"{capability_name} cannot be represented as read_only",
            )


def _validate_policy_relationship(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    denied_statuses = {"blocked", "denied", "policy_denied"}
    status = (mission_input.policy_decision_status or "").lower()
    ref = (mission_input.policy_decision_ref or "").lower()
    if status in denied_statuses or ref.endswith(".blocked") or ".blocked" in ref:
        _add_failure(
            failures,
            "policy_denied_cannot_be_overridden_by_preview",
            "policy_decision_ref",
            "policy-denied actions remain denied in Mission Control preview",
        )


def _validate_evidence_and_verifier(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    for item in mission_input.evidence_expectation:
        if item not in ALLOWED_EVIDENCE_EXPECTATIONS:
            _add_failure(
                failures,
                "unknown_evidence_expectation",
                "evidence_expectation",
                item,
            )
    if mission_input.risk_tier in HIGH_RISK_TIERS and not mission_input.evidence_expectation:
        _add_failure(
            failures,
            "evidence_expectation_required_for_high_risk_preview",
            "evidence_expectation",
            "high-risk previews require evidence expectations",
        )
    verifier = mission_input.verifier_expectation
    if verifier.verifier_required and not verifier.verifier_name:
        _add_failure(
            failures,
            "verifier_name_required",
            "verifier_expectation.verifier_name",
            "required verifier expectations need verifier_name",
        )


def _validate_rollback(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    if mission_input.rollback_status not in ALLOWED_ROLLBACK_STATUSES:
        _add_failure(failures, "unknown_rollback_status", "rollback_status", mission_input.rollback_status)
    if mission_input.risk_tier in DESTRUCTIVE_TIERS and mission_input.rollback_status in {
        MissionControlRollbackStatus.UNKNOWN.value,
        MissionControlRollbackStatus.UNAVAILABLE.value,
    }:
        _add_failure(
            failures,
            "destructive_action_requires_known_rollback_or_blocked_policy",
            "rollback_status",
            "destructive previews require known rollback/staging or blocked policy",
        )


def _validate_operator_options(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> None:
    for option in mission_input.operator_options:
        if option not in ALLOWED_OPERATOR_OPTIONS:
            _add_failure(failures, "unknown_operator_option", "operator_options", option)


def _safe_fallback_expectation(
    fallback: Mapping[str, Any],
    failures: list[MissionControlValidationFailure],
) -> Mapping[str, Any]:
    safe = deepcopy(dict(fallback))
    if safe.get("fallback_is_success") is True:
        _add_failure(
            failures,
            "fallback_cannot_be_success",
            "fallback_expectation.fallback_is_success",
            "fallback and timeout projection cannot claim success",
        )
    safe["fallback_is_success"] = False
    return MappingProxyType(safe)


def _safe_provider_interstitial_risk(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> Mapping[str, Any]:
    safe = deepcopy(dict(mission_input.provider_interstitial_risk))
    provider = (mission_input.search_provider or _text(safe.get("provider"))).lower()
    if provider == "google":
        safe.setdefault("provider", "google")
        safe.setdefault("known_risk", "google_sorry_bot_challenge")
        safe.setdefault("known_path", "/sorry")
        safe.setdefault("fallback_allowed", False)
        safe.setdefault("fallback_attempted", False)
        safe.setdefault("verification_blocker", "search_verification_blocked_by_provider")
    if safe.get("bypass_allowed") is True or safe.get("challenge_bypass_allowed") is True:
        _add_failure(
            failures,
            "provider_interstitial_bypass_not_allowed",
            "provider_interstitial_risk.bypass_allowed",
            "provider interstitial warning cannot bypass provider challenge",
        )
    safe["bypass_allowed"] = False
    safe["challenge_bypass_allowed"] = False
    return MappingProxyType(safe)


def _validation_status(
    mission_input: MissionControlInput,
    failures: list[MissionControlValidationFailure],
) -> str:
    reasons = {failure.reason for failure in failures}
    failed_validation_reasons = {
        "missing_request",
        "request_id_required",
        "command_id_required",
        "normalized_intent_required_for_executable_preview",
        "affected_resources_required_for_high_risk_preview",
        "evidence_expectation_required_for_high_risk_preview",
        "unknown_risk_tier",
        "unknown_evidence_expectation",
        "unknown_rollback_status",
        "unknown_operator_option",
        "capability_risk_tier_mismatch",
        "external_api_write_cannot_be_read_only",
        "plugin_execution_cannot_be_read_only",
        "memory_write_cannot_be_read_only",
    }
    blocked_reasons = {
        "policy_denied_cannot_be_overridden_by_preview",
        "destructive_action_requires_known_rollback_or_blocked_policy",
        "provider_interstitial_bypass_not_allowed",
        "fallback_cannot_be_success",
        "proof_of_compliance_claim_denied",
        "official_audit_result_claim_denied",
        "court_admissible_claim_denied",
        "compliance_certification_claim_denied",
        "legal_certification_claim_denied",
        "security_certification_claim_denied",
        "success_claim_denied",
        "preview_cannot_provide_evidence",
        "preview_cannot_mark_verifier_success",
        "authority_must_be_false",
        "runtime_dispatch_not_allowed",
        "approval_grant_not_allowed",
        "capability_grant_not_allowed",
        "lease_grant_not_allowed",
        "frontend_authority_not_allowed",
    }
    if reasons & failed_validation_reasons:
        return "failed_validation"
    if reasons & blocked_reasons:
        return "blocked"
    if mission_input.risk_tier == MissionControlRiskTier.UNKNOWN.value:
        return "operator_attention_required"
    if failures:
        return "blocked"
    return "review_ready"


def _decision(
    *,
    validation_status: str,
    failures: tuple[MissionControlValidationFailure, ...],
    mission_input: MissionControlInput | None = None,
    preview_contract: MissionControlPreviewContract | None = None,
    requires_operator_attention: bool = False,
) -> MissionControlDecision:
    return MissionControlDecision(
        contract_version=MISSION_CONTROL_CONTRACT_VERSION,
        validation_status=validation_status,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        mission_input=mission_input,
        preview_contract=preview_contract,
        requires_operator_attention=requires_operator_attention,
    )


def _verifier_expectation(value: Any) -> MissionControlVerifierExpectation:
    if not isinstance(value, Mapping):
        return MissionControlVerifierExpectation(
            verifier_required=False,
            verifier_name="",
            verifier_postcondition="",
        )
    return MissionControlVerifierExpectation(
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


def _add_failure(
    failures: list[MissionControlValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(MissionControlValidationFailure(reason=reason, field=field, message=message))
