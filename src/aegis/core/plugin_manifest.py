from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from aegis.core.policy_boundary import (
    CAPABILITY_ALLOWED_RISK_TIERS,
    POLICY_DISPATCHABLE_TOOL_NAMES,
    POST_FOUNDATION_CAPABILITY_CATEGORIES,
    POST_FOUNDATION_RISK_TIERS,
    SIDE_EFFECTING_RISK_TIERS,
)


PLUGIN_MANIFEST_CONTRACT_VERSION = "plugin-manifest-contract/1"
PLUGIN_MANIFEST_EXECUTION_PERMISSION = "not_granted_by_plugin_manifest"

PACK_TYPES = {
    "plugin",
    "skill",
    "skill_pack",
    "vertical_pack",
    "adapter_pack",
    "integration_pack",
    "evaluation_pack",
    "read_only_pack",
    "proposal_only_pack",
    "approval_gated_action_pack",
}

PACK_LIFECYCLE_STATUSES = {
    "discovered",
    "registered_metadata_only",
    "disabled",
    "policy_review_required",
    "eval_required",
    "approved_for_read_only",
    "approved_for_proposal_only",
    "approval_required_for_actions",
    "lease_required",
    "deprecated",
    "revoked",
    "quarantined",
    "blocked_by_policy",
    "blocked_by_privacy",
    "blocked_by_missing_evidence",
    "failed_validation",
}

PACK_ACTIVATION_STATUSES = {
    "metadata_only",
    "review_ready",
    "blocked",
    "failed_validation",
}

KNOWN_MODEL_PROVIDERS = {
    "lm_studio_local",
    "ollama_local",
    "openai_compatible_local",
    "remote_api_provider",
    "mock_provider_for_tests",
    "offline_disabled_provider",
}

KNOWN_MEMORY_NAMESPACES = {
    "user",
    "project",
    "tenant",
    "aegis_core",
    "skill_plugin",
    "vertical_pack",
    "external_integration",
    "model_provider",
    "temporary_session",
    "quarantined",
    "glossa",
    "learner",
    "document",
    "domain",
    "eval",
}

KNOWN_EXTERNAL_API_SCOPES = {
    "read_status",
    "read_foundation",
    "read_maintenance",
    "read_evidence",
    "read_replay",
    "propose_command",
    "propose_tool_call",
    "propose_memory_write",
    "propose_model_generation",
    "propose_cleanup_archive",
    "tenant_read",
    "project_read",
    "pack_read",
    "pack_propose",
}

MUTATION_RISK_TIERS = SIDE_EFFECTING_RISK_TIERS - {"model_routing"}
UNRESOLVED_REFERENCE_STATUSES = {"unresolved", "blocked"}


@dataclass(frozen=True)
class PackCapabilityDeclaration:
    capability_category: str
    risk_tier: str
    policy_rule: str | None = None
    evidence_expectation_id: str | None = None


@dataclass(frozen=True)
class PackValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class PluginManifest:
    manifest_version: str
    pack_id: str
    pack_name: str
    pack_type: str
    pack_version: str
    capability_categories: tuple[str, ...]
    risk_tiers: tuple[str, ...]
    disabled_by_default: bool
    authority: bool
    execution_permission: str
    lifecycle_status: str


@dataclass(frozen=True)
class PackValidationDecision:
    contract_version: str
    manifest_present: bool
    pack_id: str | None
    pack_type: str | None
    pack_lifecycle_status: str | None
    activation_status: str
    failure_reasons: tuple[str, ...]
    failures: tuple[PackValidationFailure, ...]
    manifest: PluginManifest | None = None
    authority: bool = False
    execution_permission: str = PLUGIN_MANIFEST_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_pack_output: bool = False
    verifier_success: bool = False
    runtime_dispatch_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_approval_if_side_effecting: bool = True


def validate_plugin_manifest(manifest: Mapping[str, Any] | None) -> PackValidationDecision:
    """Validate a future plugin/skill/pack manifest as non-authoritative metadata.

    This helper is intentionally pure and non-dispatching. It validates manifest
    shape and future policy readiness, but it never loads plugin code, starts a
    registry, grants permission, or connects to runtime execution.
    """

    failures: list[PackValidationFailure] = []
    if not isinstance(manifest, Mapping):
        failure = PackValidationFailure(
            reason="missing_manifest",
            field="manifest",
            message="manifest must be a mapping and cannot grant permission",
        )
        return _decision(
            manifest_present=False,
            pack_id=None,
            pack_type=None,
            lifecycle_status=None,
            failures=(failure,),
            activation_status="failed_validation",
        )

    required_fields = (
        "manifest_version",
        "pack_id",
        "pack_name",
        "pack_type",
        "pack_version",
        "capabilities",
        "capability_categories",
        "risk_tiers",
        "disabled_by_default",
        "authority",
        "execution_permission",
    )
    for field_name in required_fields:
        if field_name not in manifest or manifest[field_name] in (None, "", []):
            _add_failure(
                failures,
                "missing_required_field",
                field_name,
                f"{field_name} is required for metadata review",
            )

    pack_id = _text(manifest.get("pack_id")) or None
    pack_type = _text(manifest.get("pack_type")) or None
    lifecycle_status = _text(manifest.get("lifecycle_status") or "registered_metadata_only")
    capability_categories = _strings(manifest.get("capability_categories"))
    risk_tiers = _strings(manifest.get("risk_tiers"))

    if pack_type and pack_type not in PACK_TYPES:
        _add_failure(failures, "unknown_pack_type", "pack_type", "pack type is not recognized")
    if lifecycle_status not in PACK_LIFECYCLE_STATUSES:
        _add_failure(
            failures,
            "unknown_lifecycle_status",
            "lifecycle_status",
            "lifecycle status is not recognized",
        )

    _validate_non_authority_fields(manifest, failures)
    _validate_capability_and_risk(capability_categories, risk_tiers, failures)
    _validate_reference_list(
        manifest,
        failures,
        field_name="allowed_tools",
        known_values=POLICY_DISPATCHABLE_TOOL_NAMES,
        id_keys=("tool_id", "name"),
        unknown_reason="unknown_tool",
    )
    _validate_reference_list(
        manifest,
        failures,
        field_name="required_tools",
        known_values=POLICY_DISPATCHABLE_TOOL_NAMES,
        id_keys=("tool_id", "name"),
        unknown_reason="unknown_tool",
    )
    _validate_reference_list(
        manifest,
        failures,
        field_name="model_requirements",
        known_values=KNOWN_MODEL_PROVIDERS,
        id_keys=("provider_id", "model_provider", "name"),
        unknown_reason="unknown_model_provider",
    )
    _validate_reference_list(
        manifest,
        failures,
        field_name="memory_namespaces",
        known_values=KNOWN_MEMORY_NAMESPACES,
        id_keys=("namespace", "namespace_id", "name"),
        unknown_reason="unknown_memory_namespace",
    )
    _validate_reference_list(
        manifest,
        failures,
        field_name="external_api_scopes",
        known_values=KNOWN_EXTERNAL_API_SCOPES,
        id_keys=("scope", "scope_id", "name"),
        unknown_reason="unknown_external_api_scope",
    )
    _validate_side_effect_requirements(manifest, risk_tiers, failures)
    _validate_vertical_pack_requirements(manifest, capability_categories, pack_type, failures)

    parsed_manifest = None
    if _required_metadata_present(manifest):
        parsed_manifest = PluginManifest(
            manifest_version=_text(manifest.get("manifest_version")),
            pack_id=_text(manifest.get("pack_id")),
            pack_name=_text(manifest.get("pack_name")),
            pack_type=_text(manifest.get("pack_type")),
            pack_version=_text(manifest.get("pack_version")),
            capability_categories=capability_categories,
            risk_tiers=risk_tiers,
            disabled_by_default=manifest.get("disabled_by_default") is True,
            authority=manifest.get("authority") is True,
            execution_permission=_text(manifest.get("execution_permission")),
            lifecycle_status=lifecycle_status,
        )

    activation_status = "review_ready"
    if any(failure.reason in {"missing_manifest", "missing_required_field"} for failure in failures):
        activation_status = "failed_validation"
    elif failures:
        activation_status = "blocked"
    elif lifecycle_status in {"registered_metadata_only", "disabled", "discovered"}:
        activation_status = "metadata_only"

    return _decision(
        manifest_present=True,
        pack_id=pack_id,
        pack_type=pack_type,
        lifecycle_status=lifecycle_status,
        failures=tuple(failures),
        activation_status=activation_status,
        parsed_manifest=parsed_manifest,
    )


def _decision(
    *,
    manifest_present: bool,
    pack_id: str | None,
    pack_type: str | None,
    lifecycle_status: str | None,
    failures: tuple[PackValidationFailure, ...],
    activation_status: str,
    parsed_manifest: PluginManifest | None = None,
) -> PackValidationDecision:
    return PackValidationDecision(
        contract_version=PLUGIN_MANIFEST_CONTRACT_VERSION,
        manifest_present=manifest_present,
        pack_id=pack_id,
        pack_type=pack_type,
        pack_lifecycle_status=lifecycle_status,
        activation_status=activation_status,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        manifest=parsed_manifest,
    )


def _validate_non_authority_fields(
    manifest: Mapping[str, Any],
    failures: list[PackValidationFailure],
) -> None:
    if manifest.get("disabled_by_default") is not True:
        _add_failure(
            failures,
            "disabled_by_default_required",
            "disabled_by_default",
            "manifest must be disabled by default",
        )
    if manifest.get("authority") is not False:
        _add_failure(failures, "authority_must_be_false", "authority", "manifest is not authority")
    if manifest.get("execution_permission") != PLUGIN_MANIFEST_EXECUTION_PERMISSION:
        _add_failure(
            failures,
            "execution_permission_not_granted_by_manifest_required",
            "execution_permission",
            "manifest cannot grant execution permission",
        )

    forbidden_truthy_flags = {
        "approval_grant": "approval_grant_not_allowed",
        "capability_grant": "capability_grant_not_allowed",
        "lease_grant": "lease_grant_not_allowed",
        "evidence_provided_by_pack_output": "pack_output_cannot_provide_evidence",
        "verifier_success": "pack_output_cannot_mark_verifier_success",
        "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
        "enabled": "enabled_state_cannot_grant_permission",
        "installed": "installed_state_cannot_grant_permission",
        "context_derived_permission": "context_derived_permission_denied",
        "memory_derived_permission": "memory_derived_permission_denied",
        "model_derived_permission": "model_derived_permission_denied",
        "plugin_derived_permission": "plugin_derived_permission_denied",
        "skill_derived_permission": "skill_derived_permission_denied",
        "api_derived_permission": "api_derived_permission_denied",
        "tool_derived_permission": "tool_derived_permission_denied",
        "frontend_derived_permission": "frontend_derived_permission_denied",
        "defines_aegis_platform_identity": "pack_cannot_define_aegis_platform_identity",
        "redefines_aegis_platform_identity": "pack_cannot_define_aegis_platform_identity",
    }
    for field_name, reason in forbidden_truthy_flags.items():
        if manifest.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority or permission",
            )

    permission_source = _text(manifest.get("permission_source"))
    if permission_source in {
        "context",
        "context_compiler",
        "memory",
        "model",
        "model_output",
        "plugin",
        "plugin_manifest",
        "skill",
        "skill_manifest",
        "api",
        "sdk",
        "tool",
        "frontend",
        "frontend_projection",
    }:
        _add_failure(
            failures,
            f"{permission_source}_permission_source_denied",
            "permission_source",
            "untrusted sources cannot grant permission",
        )


def _validate_capability_and_risk(
    capability_categories: tuple[str, ...],
    risk_tiers: tuple[str, ...],
    failures: list[PackValidationFailure],
) -> None:
    for capability in capability_categories:
        if capability not in POST_FOUNDATION_CAPABILITY_CATEGORIES:
            _add_failure(failures, "unknown_capability", "capability_categories", capability)
    for risk_tier in risk_tiers:
        if risk_tier not in POST_FOUNDATION_RISK_TIERS:
            _add_failure(failures, "unknown_risk_tier", "risk_tiers", risk_tier)

    known_risks = {risk for risk in risk_tiers if risk in POST_FOUNDATION_RISK_TIERS}
    for capability in capability_categories:
        if capability not in POST_FOUNDATION_CAPABILITY_CATEGORIES:
            continue
        allowed = CAPABILITY_ALLOWED_RISK_TIERS.get(capability, set())
        if known_risks and not (known_risks & allowed):
            _add_failure(
                failures,
                "risk_tier_not_allowed_for_capability",
                "risk_tiers",
                f"{capability} does not allow {sorted(known_risks)}",
            )


def _validate_side_effect_requirements(
    manifest: Mapping[str, Any],
    risk_tiers: tuple[str, ...],
    failures: list[PackValidationFailure],
) -> None:
    side_effecting = any(risk in SIDE_EFFECTING_RISK_TIERS for risk in risk_tiers)
    mutation_possible = any(risk in MUTATION_RISK_TIERS for risk in risk_tiers)
    if not side_effecting:
        return

    if manifest.get("approval_required") is not True and not manifest.get("approval_requirements"):
        _add_failure(
            failures,
            "approval_required_for_side_effecting_pack",
            "approval_requirements",
            "side-effecting pack capabilities require approval requirements",
        )
    if manifest.get("lease_required") is not True and not manifest.get("lease_requirements"):
        _add_failure(
            failures,
            "lease_required_for_side_effecting_pack",
            "lease_requirements",
            "side-effecting pack capabilities require lease requirements",
        )
    if not manifest.get("evidence_expectations"):
        _add_failure(
            failures,
            "missing_evidence_expectation",
            "evidence_expectations",
            "side-effecting pack capabilities require evidence expectations",
        )
    if not manifest.get("verifier_strategy"):
        _add_failure(
            failures,
            "missing_verifier_strategy",
            "verifier_strategy",
            "side-effecting pack capabilities require verifier strategy",
        )
    if not manifest.get("audit_requirements"):
        _add_failure(
            failures,
            "missing_audit_requirements",
            "audit_requirements",
            "side-effecting pack capabilities require audit requirements",
        )
    if mutation_possible and not manifest.get("rollback_strategy"):
        _add_failure(
            failures,
            "missing_rollback_strategy",
            "rollback_strategy",
            "mutation-capable pack capabilities require rollback strategy",
        )
    if not manifest.get("eval_requirements"):
        _add_failure(
            failures,
            "missing_eval_requirements",
            "eval_requirements",
            "side-effecting pack capabilities require eval requirements",
        )


def _validate_vertical_pack_requirements(
    manifest: Mapping[str, Any],
    capability_categories: tuple[str, ...],
    pack_type: str | None,
    failures: list[PackValidationFailure],
) -> None:
    vertical_related = (
        pack_type == "vertical_pack"
        or "vertical_pack_read" in capability_categories
        or "vertical_pack_write" in capability_categories
    )
    if not vertical_related:
        return

    if not manifest.get("namespace_scope") or not manifest.get("tenant_scope"):
        _add_failure(
            failures,
            "vertical_pack_requires_namespace_and_tenant_scope",
            "namespace_scope",
            "vertical packs require namespace and tenant scope",
        )

    training_policy = manifest.get("training_data_policy")
    namespace_specific = (
        isinstance(training_policy, Mapping)
        and training_policy.get("namespace_specific") is True
    )
    if not namespace_specific:
        _add_failure(
            failures,
            "vertical_pack_requires_namespace_specific_training_policy",
            "training_data_policy",
            "vertical pack training data policy must be namespace-specific",
        )


def _validate_reference_list(
    manifest: Mapping[str, Any],
    failures: list[PackValidationFailure],
    *,
    field_name: str,
    known_values: set[str],
    id_keys: tuple[str, ...],
    unknown_reason: str,
) -> None:
    for item in _items(manifest.get(field_name)):
        item_id, status = _reference_identity(item, id_keys)
        if not item_id:
            _add_failure(failures, f"{unknown_reason}_missing_id", field_name, "missing id")
            continue
        if item_id in {"*", "all", "any"}:
            _add_failure(failures, "wildcard_scope_denied", field_name, "wildcard scope is denied")
            continue
        if item_id not in known_values and status not in UNRESOLVED_REFERENCE_STATUSES:
            _add_failure(failures, unknown_reason, field_name, item_id)


def _reference_identity(item: Any, id_keys: tuple[str, ...]) -> tuple[str, str]:
    if isinstance(item, Mapping):
        item_id = ""
        for key in id_keys:
            item_id = _text(item.get(key))
            if item_id:
                break
        return item_id, _text(item.get("status"))
    return _text(item), ""


def _items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


def _strings(value: Any) -> tuple[str, ...]:
    strings: list[str] = []
    for item in _items(value):
        text = _text(item)
        if text:
            strings.append(text)
    return tuple(strings)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _required_metadata_present(manifest: Mapping[str, Any]) -> bool:
    return all(
        field_name in manifest and manifest[field_name] not in (None, "", [])
        for field_name in (
            "manifest_version",
            "pack_id",
            "pack_name",
            "pack_type",
            "pack_version",
            "capability_categories",
            "risk_tiers",
        )
    )


def _add_failure(
    failures: list[PackValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(PackValidationFailure(reason=reason, field=field, message=message))
