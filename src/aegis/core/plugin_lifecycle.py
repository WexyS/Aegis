from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from aegis.core.plugin_manifest import PACK_LIFECYCLE_STATUSES
from aegis.core.plugin_manifest_integrity import SIGNATURE_STATUSES


PLUGIN_LIFECYCLE_CONTRACT_VERSION = "plugin-lifecycle-contract/1"
PLUGIN_LIFECYCLE_EXECUTION_PERMISSION = "not_granted_by_plugin_lifecycle"

PLUGIN_LIFECYCLE_STATES = set(PACK_LIFECYCLE_STATUSES) | {
    "active_read_only",
    "active_proposal_only",
    "active_action_gated",
}

ACTIVE_STATES = {
    "active_read_only",
    "active_proposal_only",
    "active_action_gated",
}

APPROVED_STATES = {
    "approved_for_read_only",
    "approved_for_proposal_only",
}

TERMINAL_BLOCKED_STATES = {
    "revoked",
    "quarantined",
    "failed_validation",
    "blocked_by_policy",
    "blocked_by_privacy",
    "blocked_by_missing_evidence",
}

SAFE_METADATA_TRANSITIONS = {
    "discovered": {"registered_metadata_only", "disabled", "failed_validation", "quarantined"},
    "registered_metadata_only": {
        "policy_review_required",
        "eval_required",
        "disabled",
        "approved_for_read_only",
        "approved_for_proposal_only",
    },
    "disabled": {"policy_review_required", "deprecated", "revoked"},
    "policy_review_required": {"approved_for_read_only", "blocked_by_policy", "blocked_by_privacy"},
    "eval_required": {"approved_for_proposal_only", "failed_validation", "blocked_by_policy"},
    "approved_for_read_only": {"active_read_only", "deprecated", "revoked", "quarantined"},
    "approved_for_proposal_only": {
        "active_proposal_only",
        "approval_required_for_actions",
        "deprecated",
        "revoked",
        "quarantined",
    },
    "approval_required_for_actions": {"lease_required", "blocked_by_missing_evidence", "revoked"},
    "lease_required": {"active_action_gated", "blocked_by_policy", "revoked", "quarantined"},
    "active_read_only": {"deprecated", "revoked", "quarantined"},
    "active_proposal_only": {"approval_required_for_actions", "deprecated", "revoked", "quarantined"},
    "active_action_gated": {"deprecated", "revoked", "quarantined"},
    "deprecated": {"revoked", "quarantined"},
}

INVALID_SIGNATURE_STATES = {
    "signature_invalid",
    "signer_untrusted",
    "signature_expired",
    "signature_revoked",
    "algorithm_unsupported",
}

REVIEW_BLOCKING_INTEGRITY_STATES = {
    "changed_requires_review",
    "version_changed_requires_review",
    "checksum_mismatch_requires_quarantine",
    "invalid_manifest_requires_quarantine",
    "unsupported_algorithm",
    "blocked",
}

ACTION_GATED_REQUIRED_GATES = {
    "policy_check",
    "approval",
    "lease",
    "evidence_expectation",
    "verifier_strategy",
    "audit_requirements",
    "eval",
    "rollback",
}


@dataclass(frozen=True)
class PluginLifecycleDecision:
    contract_version: str
    current_state: str
    requested_state: str
    transition_allowed: bool
    activation_allowed: bool
    runtime_dispatch_allowed: bool
    authority: bool
    execution_permission: str
    approval_grant: bool
    capability_grant: bool
    lease_grant: bool
    evidence_provided_by_lifecycle: bool
    verifier_success: bool
    requires_backend_validation: bool
    requires_policy_check: bool
    requires_manifest_validation: bool
    requires_integrity_check: bool
    failure_reasons: tuple[str, ...]
    required_gates: tuple[str, ...]
    audit_notes: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()


def evaluate_plugin_lifecycle_transition(
    current_state: str,
    requested_state: str,
    *,
    manifest_validation: Any | None = None,
    integrity_decision: Any | None = None,
    signature_state: str | None = None,
    requested_capability: str | None = None,
    risk_tier: str | None = None,
    approval_present: bool = False,
    lease_present: bool = False,
    evidence_expectation_present: bool = False,
    verifier_strategy_present: bool = False,
    audit_requirements_present: bool = False,
    eval_present: bool = False,
    rollback_present: bool = False,
    namespace_scope_present: bool = False,
    tenant_scope_present: bool = False,
    enabled: bool = False,
    installed: bool = False,
) -> PluginLifecycleDecision:
    """Evaluate a future plugin/skill/pack lifecycle transition.

    This helper is a pure type-contract validator. It does not load plugins,
    persist records, inspect runtime state, or grant runtime dispatch.
    """

    current = _text(current_state)
    requested = _text(requested_state)
    failures: list[str] = []
    required_gates: set[str] = {"manifest_validation", "integrity_check"}
    audit_notes: list[str] = []

    if current not in PLUGIN_LIFECYCLE_STATES:
        failures.append("unknown_current_state")
    if requested not in PLUGIN_LIFECYCLE_STATES:
        failures.append("unknown_requested_state")

    manifest_ok, manifest_failures = _manifest_validation_ok(manifest_validation)
    if not manifest_ok:
        failures.extend(manifest_failures)

    integrity_ok, integrity_failures = _integrity_decision_ok(
        integrity_decision,
        target_state=requested,
    )
    if not integrity_ok:
        failures.extend(integrity_failures)

    if current in {"revoked", "quarantined", "failed_validation"} and requested in ACTIVE_STATES:
        failures.append(f"{current}_cannot_activate")
    if current == "deprecated" and requested == "active_action_gated":
        failures.append("deprecated_cannot_become_action_gated")
    if current in TERMINAL_BLOCKED_STATES and requested in ACTIVE_STATES:
        failures.append("blocked_state_cannot_activate")
    if current == "disabled" and requested in ACTIVE_STATES:
        failures.append("disabled_requires_review_before_activation")
    if current == "policy_review_required" and requested in ACTIVE_STATES:
        failures.append("policy_review_required_cannot_activate_directly")
    if current == "eval_required" and requested in ACTIVE_STATES and not eval_present:
        failures.append("eval_required_before_activation")

    if current in PLUGIN_LIFECYCLE_STATES and requested in PLUGIN_LIFECYCLE_STATES:
        allowed_targets = SAFE_METADATA_TRANSITIONS.get(current, set())
        if requested not in allowed_targets:
            failures.append("transition_not_allowed")

    signature = _text(signature_state) or _field(integrity_decision, "signature_status") or "unsigned"
    if signature not in SIGNATURE_STATUSES:
        failures.append("unknown_signature_state")
    if signature in INVALID_SIGNATURE_STATES and requested in (ACTIVE_STATES | APPROVED_STATES):
        failures.append(f"{signature}_blocks_activation")
    if requested == "active_action_gated" and signature != "signature_verified":
        failures.append("trusted_signature_required_for_action_gated_activation")

    if requested in APPROVED_STATES | ACTIVE_STATES:
        if _field(integrity_decision, "decision_state") != "unchanged":
            failures.append("integrity_review_required_before_activation")
        if _bool_field(integrity_decision, "review_required"):
            failures.append("manifest_review_required")
        if _bool_field(integrity_decision, "quarantine_required"):
            failures.append("manifest_quarantine_blocks_activation")

    if requested in {"approved_for_proposal_only", "active_proposal_only"} and not eval_present:
        required_gates.add("eval")
        failures.append("eval_required_for_proposal_lifecycle")

    if requested == "active_action_gated":
        required_gates.update(ACTION_GATED_REQUIRED_GATES)
        if not approval_present:
            failures.append("approval_required_for_action_gated_lifecycle")
        if not lease_present:
            failures.append("lease_required_for_action_gated_lifecycle")
        if not evidence_expectation_present:
            failures.append("evidence_expectation_required_for_action_gated_lifecycle")
        if not verifier_strategy_present:
            failures.append("verifier_strategy_required_for_action_gated_lifecycle")
        if not audit_requirements_present:
            failures.append("audit_requirements_required_for_action_gated_lifecycle")
        if not eval_present:
            failures.append("eval_required_for_action_gated_lifecycle")
        if _mutation_possible(risk_tier) and not rollback_present:
            failures.append("rollback_required_for_mutating_action_gated_lifecycle")
        if _vertical_capability(requested_capability) and not namespace_scope_present:
            failures.append("namespace_scope_required_for_vertical_pack_lifecycle")
        if _vertical_capability(requested_capability) and not tenant_scope_present:
            failures.append("tenant_scope_required_for_vertical_pack_lifecycle")

    if enabled:
        audit_notes.append("enabled_flag_is_metadata_only")
    if installed:
        audit_notes.append("installed_flag_is_metadata_only")
    if approval_present:
        audit_notes.append("approval_presence_is_not_dispatch_permission")
    if lease_present:
        audit_notes.append("lease_presence_is_not_dispatch_permission")

    unique_failures = tuple(_unique(failures))
    transition_allowed = not unique_failures
    activation_allowed = transition_allowed and requested in ACTIVE_STATES

    return PluginLifecycleDecision(
        contract_version=PLUGIN_LIFECYCLE_CONTRACT_VERSION,
        current_state=current,
        requested_state=requested,
        transition_allowed=transition_allowed,
        activation_allowed=activation_allowed,
        runtime_dispatch_allowed=False,
        authority=False,
        execution_permission=PLUGIN_LIFECYCLE_EXECUTION_PERMISSION,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_lifecycle=False,
        verifier_success=False,
        requires_backend_validation=True,
        requires_policy_check=True,
        requires_manifest_validation=True,
        requires_integrity_check=True,
        failure_reasons=unique_failures,
        required_gates=tuple(sorted(required_gates)),
        audit_notes=tuple(audit_notes),
    )


def _manifest_validation_ok(manifest_validation: Any | None) -> tuple[bool, list[str]]:
    if manifest_validation is None:
        return False, ["missing_manifest_validation"]
    activation_status = _field(manifest_validation, "activation_status")
    failure_reasons = _tuple_field(manifest_validation, "failure_reasons")
    if activation_status in {"blocked", "failed_validation"} or failure_reasons:
        return False, ["failed_manifest_validation"]
    if _bool_field(manifest_validation, "runtime_dispatch_allowed"):
        return False, ["manifest_validation_attempted_runtime_dispatch"]
    return True, []


def _integrity_decision_ok(
    integrity_decision: Any | None,
    *,
    target_state: str,
) -> tuple[bool, list[str]]:
    if integrity_decision is None:
        return False, ["missing_integrity_check"]
    if _bool_field(integrity_decision, "runtime_dispatch_allowed"):
        return False, ["integrity_decision_attempted_runtime_dispatch"]
    if _bool_field(integrity_decision, "quarantine_required"):
        return False, ["integrity_quarantine_required"]
    state = _field(integrity_decision, "decision_state")
    if state in REVIEW_BLOCKING_INTEGRITY_STATES:
        return False, ["integrity_blocks_lifecycle"]
    if target_state in (ACTIVE_STATES | APPROVED_STATES) and state != "unchanged":
        return False, ["integrity_review_required"]
    return True, []


def _mutation_possible(risk_tier: str | None) -> bool:
    return _text(risk_tier) in {
        "local_file_write",
        "app_launch",
        "app_focus",
        "ui_click",
        "external_network",
        "tool_execution",
        "memory_write",
        "plugin_execution",
        "cleanup_archive",
        "cleanup_compaction",
        "destructive_system_change",
    }


def _vertical_capability(requested_capability: str | None) -> bool:
    return _text(requested_capability) in {"vertical_pack_read", "vertical_pack_write"}


def _field(value: Any, field_name: str) -> str:
    if isinstance(value, Mapping):
        return _text(value.get(field_name))
    return _text(getattr(value, field_name, None))


def _bool_field(value: Any, field_name: str) -> bool:
    if isinstance(value, Mapping):
        return value.get(field_name) is True
    return getattr(value, field_name, None) is True


def _tuple_field(value: Any, field_name: str) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        raw = value.get(field_name)
    else:
        raw = getattr(value, field_name, None)
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
