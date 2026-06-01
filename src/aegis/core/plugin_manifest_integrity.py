from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from aegis.core.plugin_manifest import PLUGIN_MANIFEST_EXECUTION_PERMISSION


MANIFEST_INTEGRITY_CONTRACT_VERSION = "plugin-manifest-integrity/1"
MANIFEST_INTEGRITY_EXECUTION_PERMISSION = "not_granted_by_manifest_integrity"

SUPPORTED_CHECKSUM_ALGORITHMS = {"sha256"}

CHECKSUM_EXCLUDED_FIELDS = {
    "checksum_algorithm",
    "manifest_checksum",
    "review_status",
    "reviewed_at",
    "reviewed_manifest_checksum",
    "signature",
    "signature_status",
    "signed_by",
}

SIGNATURE_STATUSES = {
    "unsigned",
    "signature_missing",
    "signature_present_unverified",
    "signature_verified",
    "signature_invalid",
    "signer_untrusted",
    "signature_expired",
    "signature_revoked",
    "algorithm_unsupported",
}

QUARANTINE_SIGNATURE_STATUSES = {
    "signature_invalid": "signature_invalid",
    "signer_untrusted": "signer_untrusted",
    "signature_expired": "signature_expired",
    "signature_revoked": "signature_revoked",
    "algorithm_unsupported": "algorithm_unsupported",
}


@dataclass(frozen=True)
class ManifestScopeExpansionDecision:
    expansion_detected: bool
    expansion_reasons: tuple[str, ...]
    added_capabilities: tuple[str, ...] = ()
    added_risk_tiers: tuple[str, ...] = ()
    added_tools: tuple[str, ...] = ()
    added_model_providers: tuple[str, ...] = ()
    added_memory_namespaces: tuple[str, ...] = ()
    added_external_api_scopes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManifestDriftDecision:
    contract_version: str
    decision_state: str
    checksum_algorithm: str
    current_checksum: str | None
    reviewed_checksum: str | None
    current_pack_version: str | None
    reviewed_pack_version: str | None
    signature_status: str
    signature_trusted: bool
    review_required: bool
    quarantine_required: bool
    quarantine_reasons: tuple[str, ...]
    expansion_reasons: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    authority: bool = False
    execution_permission: str = MANIFEST_INTEGRITY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_pack_output: bool = False
    verifier_success: bool = False
    runtime_dispatch_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


def normalize_manifest_for_checksum(manifest: Mapping[str, Any]) -> str:
    """Return deterministic JSON for manifest content hashing.

    Review and signature/checksum bookkeeping fields are excluded so the stored
    checksum can be compared against the manifest content it represents. The
    helper is pure and does not mutate the supplied mapping.
    """

    if not isinstance(manifest, Mapping):
        raise TypeError("manifest must be a mapping")
    normalized = _normalize_mapping(manifest)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def calculate_manifest_checksum(
    manifest: Mapping[str, Any],
    *,
    algorithm: str = "sha256",
) -> str:
    """Calculate a deterministic manifest checksum for supported algorithms."""

    normalized_algorithm = str(algorithm or "").lower()
    if normalized_algorithm not in SUPPORTED_CHECKSUM_ALGORITHMS:
        raise ValueError(f"unsupported checksum algorithm: {algorithm}")
    payload = normalize_manifest_for_checksum(manifest).encode("utf-8")
    return hashlib.new(normalized_algorithm, payload).hexdigest()


def compare_manifest_scope_expansion(
    reviewed_manifest: Mapping[str, Any] | None,
    current_manifest: Mapping[str, Any] | None,
) -> ManifestScopeExpansionDecision:
    """Compare reviewed/current manifests for scope or authority expansion."""

    if not isinstance(reviewed_manifest, Mapping) or not isinstance(current_manifest, Mapping):
        return ManifestScopeExpansionDecision(
            expansion_detected=False,
            expansion_reasons=(),
        )

    reasons: list[str] = []
    added_capabilities = _added_values(reviewed_manifest, current_manifest, "capability_categories")
    added_risk_tiers = _added_values(reviewed_manifest, current_manifest, "risk_tiers")
    added_tools = _added_values(reviewed_manifest, current_manifest, "allowed_tools", "required_tools")
    added_model_providers = _added_values(reviewed_manifest, current_manifest, "model_requirements")
    added_memory_namespaces = _added_values(reviewed_manifest, current_manifest, "memory_namespaces")
    added_external_api_scopes = _added_values(reviewed_manifest, current_manifest, "external_api_scopes")

    if added_capabilities:
        reasons.append("capability_expansion")
    if added_risk_tiers:
        reasons.append("risk_tier_expansion")
    if added_tools:
        reasons.append("new_tool_reference")
    if added_model_providers:
        reasons.append("new_model_reference")
    if added_memory_namespaces:
        reasons.append("new_memory_namespace")
    if added_external_api_scopes:
        reasons.append("new_external_api_scope")
    if _scope_expanded(reviewed_manifest, current_manifest, "tenant_scope"):
        reasons.append("tenant_scope_expansion")
    if _scope_expanded(reviewed_manifest, current_manifest, "project_scope"):
        reasons.append("scope_expansion")
    if reviewed_manifest.get("disabled_by_default") is True and current_manifest.get("disabled_by_default") is False:
        reasons.append("disabled_by_default_changed_to_false")
    if current_manifest.get("authority") is True:
        reasons.append("authority_changed_to_true")
    if current_manifest.get("execution_permission") != PLUGIN_MANIFEST_EXECUTION_PERMISSION:
        reasons.append("execution_permission_changed")
    if (
        current_manifest.get("defines_aegis_platform_identity") is True
        or current_manifest.get("redefines_aegis_platform_identity") is True
    ):
        reasons.append("platform_identity_override_attempt")

    return ManifestScopeExpansionDecision(
        expansion_detected=bool(reasons),
        expansion_reasons=tuple(reasons),
        added_capabilities=tuple(sorted(added_capabilities)),
        added_risk_tiers=tuple(sorted(added_risk_tiers)),
        added_tools=tuple(sorted(added_tools)),
        added_model_providers=tuple(sorted(added_model_providers)),
        added_memory_namespaces=tuple(sorted(added_memory_namespaces)),
        added_external_api_scopes=tuple(sorted(added_external_api_scopes)),
    )


def evaluate_manifest_drift(
    current_manifest: Mapping[str, Any] | None,
    *,
    reviewed_checksum: str | None = None,
    reviewed_version: str | None = None,
    reviewed_manifest: Mapping[str, Any] | None = None,
    checksum_algorithm: str = "sha256",
    signature_status: str = "unsigned",
) -> ManifestDriftDecision:
    """Evaluate manifest drift/signature readiness without granting permission."""

    algorithm = str(checksum_algorithm or "").lower()
    normalized_signature_status = str(signature_status or "unsigned")
    failure_reasons: list[str] = []
    quarantine_reasons: list[str] = []
    current_checksum: str | None = None
    current_pack_version: str | None = None
    expansion = compare_manifest_scope_expansion(reviewed_manifest, current_manifest)

    if algorithm not in SUPPORTED_CHECKSUM_ALGORITHMS:
        return _drift_decision(
            decision_state="unsupported_algorithm",
            checksum_algorithm=algorithm,
            current_checksum=None,
            reviewed_checksum=reviewed_checksum,
            current_pack_version=None,
            reviewed_pack_version=reviewed_version,
            signature_status=normalized_signature_status,
            review_required=True,
            quarantine_required=True,
            quarantine_reasons=("algorithm_unsupported",),
            expansion_reasons=(),
            failure_reasons=("unsupported_algorithm",),
        )

    if normalized_signature_status not in SIGNATURE_STATUSES:
        normalized_signature_status = "algorithm_unsupported"

    if not isinstance(current_manifest, Mapping):
        return _drift_decision(
            decision_state="invalid_manifest_requires_quarantine",
            checksum_algorithm=algorithm,
            current_checksum=None,
            reviewed_checksum=reviewed_checksum,
            current_pack_version=None,
            reviewed_pack_version=reviewed_version,
            signature_status=normalized_signature_status,
            review_required=True,
            quarantine_required=True,
            quarantine_reasons=("invalid_manifest",),
            expansion_reasons=(),
            failure_reasons=("invalid_manifest",),
        )

    current_pack_version = _text(current_manifest.get("pack_version")) or None
    try:
        current_checksum = calculate_manifest_checksum(current_manifest, algorithm=algorithm)
    except (TypeError, ValueError):
        return _drift_decision(
            decision_state="invalid_manifest_requires_quarantine",
            checksum_algorithm=algorithm,
            current_checksum=None,
            reviewed_checksum=reviewed_checksum,
            current_pack_version=current_pack_version,
            reviewed_pack_version=reviewed_version,
            signature_status=normalized_signature_status,
            review_required=True,
            quarantine_required=True,
            quarantine_reasons=("invalid_manifest",),
            expansion_reasons=(),
            failure_reasons=("invalid_manifest",),
        )

    signature_reason = QUARANTINE_SIGNATURE_STATUSES.get(normalized_signature_status)
    if signature_reason:
        quarantine_reasons.append(signature_reason)
        failure_reasons.append(signature_reason)

    if expansion.expansion_reasons:
        quarantine_reasons.extend(expansion.expansion_reasons)

    version_changed = bool(
        reviewed_version
        and current_pack_version
        and str(reviewed_version) != current_pack_version
    )
    checksum_changed = bool(reviewed_checksum and current_checksum != reviewed_checksum)

    if version_changed:
        quarantine_reasons.append("version_drift")
    if checksum_changed:
        quarantine_reasons.append("checksum_mismatch")

    review_required = (
        not reviewed_checksum
        or checksum_changed
        or version_changed
        or bool(expansion.expansion_reasons)
        or bool(signature_reason)
    )
    quarantine_required = bool(
        checksum_changed
        or signature_reason
        or expansion.expansion_reasons
        or version_changed
    )

    if signature_reason:
        decision_state = "blocked"
    elif version_changed:
        decision_state = "version_changed_requires_review"
    elif checksum_changed:
        decision_state = "checksum_mismatch_requires_quarantine"
    elif expansion.expansion_reasons:
        decision_state = "changed_requires_review"
    elif not reviewed_checksum:
        decision_state = "no_review_record"
    else:
        decision_state = "unchanged"

    return _drift_decision(
        decision_state=decision_state,
        checksum_algorithm=algorithm,
        current_checksum=current_checksum,
        reviewed_checksum=reviewed_checksum,
        current_pack_version=current_pack_version,
        reviewed_pack_version=reviewed_version,
        signature_status=normalized_signature_status,
        review_required=review_required,
        quarantine_required=quarantine_required,
        quarantine_reasons=tuple(_unique(quarantine_reasons)),
        expansion_reasons=expansion.expansion_reasons,
        failure_reasons=tuple(_unique(failure_reasons)),
    )


def _drift_decision(
    *,
    decision_state: str,
    checksum_algorithm: str,
    current_checksum: str | None,
    reviewed_checksum: str | None,
    current_pack_version: str | None,
    reviewed_pack_version: str | None,
    signature_status: str,
    review_required: bool,
    quarantine_required: bool,
    quarantine_reasons: tuple[str, ...],
    expansion_reasons: tuple[str, ...],
    failure_reasons: tuple[str, ...],
) -> ManifestDriftDecision:
    return ManifestDriftDecision(
        contract_version=MANIFEST_INTEGRITY_CONTRACT_VERSION,
        decision_state=decision_state,
        checksum_algorithm=checksum_algorithm,
        current_checksum=current_checksum,
        reviewed_checksum=reviewed_checksum,
        current_pack_version=current_pack_version,
        reviewed_pack_version=reviewed_pack_version,
        signature_status=signature_status,
        signature_trusted=signature_status == "signature_verified",
        review_required=review_required,
        quarantine_required=quarantine_required,
        quarantine_reasons=quarantine_reasons,
        expansion_reasons=expansion_reasons,
        failure_reasons=failure_reasons,
    )


def _normalize_mapping(manifest: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in manifest.items():
        text_key = _text(key)
        if text_key in CHECKSUM_EXCLUDED_FIELDS:
            continue
        normalized[text_key] = _normalize_value(value)
    return normalized


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    if isinstance(value, set):
        normalized_items = [_normalize_value(item) for item in value]
        return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"manifest value is not JSON-serializable: {type(value).__name__}")


def _added_values(
    reviewed_manifest: Mapping[str, Any],
    current_manifest: Mapping[str, Any],
    *field_names: str,
) -> set[str]:
    reviewed: set[str] = set()
    current: set[str] = set()
    for field_name in field_names:
        reviewed.update(_reference_values(reviewed_manifest.get(field_name)))
        current.update(_reference_values(current_manifest.get(field_name)))
    return current - reviewed


def _reference_values(value: Any) -> set[str]:
    values: set[str] = set()
    for item in _items(value):
        if isinstance(item, Mapping):
            item_id = (
                _text(item.get("tool_id"))
                or _text(item.get("provider_id"))
                or _text(item.get("model_provider"))
                or _text(item.get("namespace"))
                or _text(item.get("namespace_id"))
                or _text(item.get("scope"))
                or _text(item.get("scope_id"))
                or _text(item.get("name"))
            )
            if item_id:
                values.add(item_id)
        else:
            item_id = _text(item)
            if item_id:
                values.add(item_id)
    return values


def _scope_expanded(
    reviewed_manifest: Mapping[str, Any],
    current_manifest: Mapping[str, Any],
    field_name: str,
) -> bool:
    reviewed = _reference_values(reviewed_manifest.get(field_name))
    current = _reference_values(current_manifest.get(field_name))
    if current & {"*", "all", "any"}:
        return True
    return bool(current - reviewed)


def _items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


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
