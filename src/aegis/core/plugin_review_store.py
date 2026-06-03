from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, unique
from types import MappingProxyType
from typing import Any, Mapping


PLUGIN_REVIEW_STORE_VERSION = "plugin-review-store-readiness/1"
PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION = "not_granted_by_plugin_review_store"


@unique
class PluginReviewStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    REVIEW_READY = "review_ready"
    APPROVED_FOR_CATALOG_REVIEW = "approved_for_catalog_review"
    APPROVED_METADATA_ONLY = "approved_metadata_only"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    REQUIRES_SECURITY_REVIEW = "requires_security_review"
    REQUIRES_PRIVACY_REVIEW = "requires_privacy_review"
    REQUIRES_POLICY_REVIEW = "requires_policy_review"
    UNKNOWN = "unknown"


@unique
class PluginReviewScope(str, Enum):
    MANIFEST_METADATA_ONLY = "manifest_metadata_only"
    INTEGRITY_METADATA_ONLY = "integrity_metadata_only"
    LIFECYCLE_METADATA_ONLY = "lifecycle_metadata_only"
    VERTICAL_PACK_METADATA_ONLY = "vertical_pack_metadata_only"
    CATALOG_REVIEW_CANDIDATE = "catalog_review_candidate"
    SECURITY_REVIEW_CANDIDATE = "security_review_candidate"
    PRIVACY_REVIEW_CANDIDATE = "privacy_review_candidate"
    POLICY_REVIEW_CANDIDATE = "policy_review_candidate"
    READ_ONLY_PACK_CANDIDATE = "read_only_pack_candidate"
    EXTERNAL_INTEGRATION_CANDIDATE = "external_integration_candidate"
    EXECUTION_CANDIDATE_FUTURE_ONLY = "execution_candidate_future_only"


@dataclass(frozen=True)
class PluginReviewFinding:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class PluginReviewSourceRef:
    ref_id: str
    ref_type: str = "unspecified"
    description: str | None = None


@dataclass(frozen=True)
class PluginReviewLimitation:
    note: str
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginReviewRequirement:
    requirement_id: str
    requirement_type: str
    reason: str
    required: bool = True


@dataclass(frozen=True)
class PluginReviewProvenance:
    reviewer_ref: str | None
    review_timestamp: str | None
    source_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]


@dataclass(frozen=True)
class PluginReviewRecordInput:
    review_record_id: str | None
    plugin_id: str | None
    plugin_name: str | None
    plugin_version: str | None
    manifest_ref: str | None
    manifest_checksum_ref: str | None
    signature_ref: str | None
    lifecycle_decision_ref: str | None
    vertical_pack_decision_ref: str | None
    policy_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    reviewer_ref: str | None = None
    review_timestamp: str | None = None
    review_status: str = PluginReviewStatus.UNKNOWN.value
    review_scope: tuple[str, ...] = ()
    review_version: str | None = None
    source_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    required_followups: tuple[str, ...] = ()
    required_operator_review: bool = True
    required_security_review: bool = False
    required_privacy_review: bool = False
    required_policy_review: bool = True
    allowed_operations: tuple[str, ...] = ()
    forbidden_operations: tuple[str, ...] = ()
    declared_capabilities: tuple[str, ...] = ()
    declared_risk_tiers: tuple[str, ...] = ()
    requested_permissions: tuple[str, ...] = ()
    hidden_permissions: tuple[str, ...] = ()
    data_sensitivity: str | None = None
    tenant_scope: str | None = None
    project_scope: str | None = None
    namespace: str | None = None
    provenance_refs: tuple[str, ...] = ()
    expiry_or_revalidation_at: str | None = None
    supersedes_review_record_id: str | None = None
    claims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "policy_refs",
            "evidence_refs",
            "review_scope",
            "source_refs",
            "limitations",
            "unknowns",
            "required_followups",
            "allowed_operations",
            "forbidden_operations",
            "declared_capabilities",
            "declared_risk_tiers",
            "requested_permissions",
            "hidden_permissions",
            "provenance_refs",
            "claims",
        ):
            object.__setattr__(self, field_name, _strings(getattr(self, field_name)))


@dataclass(frozen=True)
class PluginReviewRecord:
    review_record_id: str | None
    plugin_id: str | None
    plugin_name: str | None
    plugin_version: str | None
    manifest_ref: str | None
    manifest_checksum_ref: str | None
    signature_ref: str | None
    lifecycle_decision_ref: str | None
    vertical_pack_decision_ref: str | None
    policy_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reviewer_ref: str | None
    review_timestamp: str | None
    review_status: str
    review_scope: tuple[str, ...]
    review_version: str | None
    source_refs: tuple[str, ...]
    limitations: tuple[PluginReviewLimitation, ...]
    unknowns: tuple[str, ...]
    required_followups: tuple[str, ...]
    required_operator_review: bool
    required_security_review: bool
    required_privacy_review: bool
    required_policy_review: bool
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    declared_capabilities: tuple[str, ...]
    declared_risk_tiers: tuple[str, ...]
    requested_permissions: tuple[str, ...]
    data_sensitivity: str | None
    tenant_scope: str | None
    project_scope: str | None
    namespace: str | None
    provenance: PluginReviewProvenance
    provenance_refs: tuple[str, ...]
    expiry_or_revalidation_at: str | None
    supersedes_review_record_id: str | None
    review_blocked: bool
    revalidation_required: bool
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_review: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    plugin_execution_allowed: bool = False
    dynamic_import_allowed: bool = False
    marketplace_publication_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_operator_approval_for_execution: bool = True


@dataclass(frozen=True)
class PluginReviewStoreContract:
    store_version: str = PLUGIN_REVIEW_STORE_VERSION
    real_persistence_added: bool = False
    database_added: bool = False
    file_store_added: bool = False
    runtime_integration_added: bool = False
    plugin_loading_added: bool = False
    marketplace_publication_added: bool = False
    mutation_performed: bool = False


@dataclass(frozen=True)
class PluginReviewDecision:
    contract_version: str
    validation_status: str
    review_record_id: str | None
    plugin_id: str | None
    plugin_version: str | None
    failure_reasons: tuple[str, ...]
    failures: tuple[PluginReviewFinding, ...]
    review_input: PluginReviewRecordInput | None = None
    review_record: PluginReviewRecord | None = None
    store_contract: PluginReviewStoreContract = field(default_factory=PluginReviewStoreContract)
    requires_operator_attention: bool = False
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_review: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    plugin_execution_allowed: bool = False
    dynamic_import_allowed: bool = False
    marketplace_publication_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_operator_approval_for_execution: bool = True


ALLOWED_REVIEW_STATUSES = {item.value for item in PluginReviewStatus}
ALLOWED_REVIEW_SCOPES = {item.value for item in PluginReviewScope}
BLOCKING_STATUSES = {
    PluginReviewStatus.REJECTED.value,
    PluginReviewStatus.BLOCKED.value,
    PluginReviewStatus.QUARANTINED.value,
}
STALE_STATUSES = {
    PluginReviewStatus.EXPIRED.value,
    PluginReviewStatus.SUPERSEDED.value,
    PluginReviewStatus.DEPRECATED.value,
}
HIGH_RISK_TIERS = {
    "local_file_write",
    "external_api_write",
    "memory_write",
    "plugin_execution",
    "cleanup_archive",
    "cleanup_compaction",
    "destructive_system_change",
    "tool_execution",
    "external_network",
}
HIGH_RISK_CAPABILITIES = {
    "local_tool_write",
    "memory_write",
    "mcp_tool_call",
    "plugin_action",
    "vertical_pack_write",
    "cleanup_archive",
    "cleanup_compaction",
    "external_api_write",
    "plugin_execution",
}
WILDCARD_VALUES = {"*", "all", "any"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_review": "review_cannot_provide_evidence",
    "evidence_provided_by_pack_output": "review_cannot_provide_evidence",
    "verifier_success": "review_cannot_mark_verifier_success",
    "verified_success": "review_cannot_mark_verifier_success",
    "mutation_performed": "mutation_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "plugin_execution_allowed": "plugin_execution_not_allowed",
    "dynamic_import_allowed": "dynamic_import_not_allowed",
    "marketplace_publication_allowed": "marketplace_publication_not_allowed",
    "external_api_request": "external_api_request_denied",
    "call_external_api": "external_api_request_denied",
    "tool_execution_requested": "tool_execution_request_denied",
    "mcp_tool_call": "mcp_call_request_denied",
    "model_call_requested": "model_call_request_denied",
    "memory_read_requested": "memory_access_request_denied",
    "memory_write_requested": "memory_access_request_denied",
}

FORBIDDEN_CLAIMS = {
    "legal certification": "legal_certification_claim_denied",
    "security certification": "security_certification_claim_denied",
    "compliance certification": "compliance_certification_claim_denied",
    "official audit result": "official_audit_result_claim_denied",
    "court-admissible": "court_admissible_claim_denied",
    "court admissible": "court_admissible_claim_denied",
    "proof of compliance": "proof_of_compliance_claim_denied",
    "controls are effective": "proof_control_effective_claim_denied",
    "control effectiveness": "proof_control_effective_claim_denied",
}


def validate_plugin_review_record(
    request: Mapping[str, Any] | None,
    *,
    manifest_decision: Any | None = None,
    integrity_decision: Any | None = None,
    lifecycle_decision: Any | None = None,
    vertical_pack_decision: Any | None = None,
    policy_decision: Any | None = None,
) -> PluginReviewDecision:
    """Validate caller-supplied plugin review-store metadata.

    The helper is pure. It does not create persistence, write files, create a
    database, load plugins, dynamically import code, execute plugins, verify
    real signatures, publish marketplace listings, call APIs/MCP/models/memory,
    or grant runtime permission.
    """

    failures: list[PluginReviewFinding] = []
    if not isinstance(request, Mapping):
        failure = PluginReviewFinding(
            reason="missing_review_record",
            field="request",
            message="plugin review record must be a mapping",
        )
        return _decision(
            validation_status="failed_validation",
            review_record_id=None,
            plugin_id=None,
            plugin_version=None,
            failures=(failure,),
        )

    request_copy = deepcopy(dict(request))
    _validate_non_authority_fields(request_copy, failures)
    _validate_forbidden_claims(request_copy, failures)
    review_input = _review_input(request_copy)
    _validate_identity(review_input, failures)
    _validate_status_and_scope(review_input, failures)
    _validate_required_refs_and_scopes(review_input, failures)
    _validate_permissions_and_review_requirements(review_input, request_copy, failures)
    _validate_related_decision("manifest", manifest_decision, failures)
    _validate_related_decision("integrity", integrity_decision, failures)
    _validate_related_decision("lifecycle", lifecycle_decision, failures)
    _validate_related_decision("vertical_pack", vertical_pack_decision, failures)
    _validate_related_decision("policy", policy_decision, failures)

    review_record = _record_from_input(review_input)
    validation_status = _validation_status(review_input, failures)
    return _decision(
        validation_status=validation_status,
        review_record_id=review_input.review_record_id,
        plugin_id=review_input.plugin_id,
        plugin_version=review_input.plugin_version,
        failures=tuple(failures),
        review_input=review_input,
        review_record=review_record,
        requires_operator_attention=_requires_operator_attention(review_input, failures),
    )


def _review_input(request: Mapping[str, Any]) -> PluginReviewRecordInput:
    return PluginReviewRecordInput(
        review_record_id=_text(request.get("review_record_id")) or None,
        plugin_id=_text(request.get("plugin_id")) or None,
        plugin_name=_text(request.get("plugin_name")) or None,
        plugin_version=_text(request.get("plugin_version")) or None,
        manifest_ref=_text(request.get("manifest_ref")) or None,
        manifest_checksum_ref=_text(request.get("manifest_checksum_ref")) or None,
        signature_ref=_text(request.get("signature_ref")) or None,
        lifecycle_decision_ref=_text(request.get("lifecycle_decision_ref")) or None,
        vertical_pack_decision_ref=_text(request.get("vertical_pack_decision_ref")) or None,
        policy_refs=_strings(request.get("policy_refs")),
        evidence_refs=_strings(request.get("evidence_refs")),
        reviewer_ref=_text(request.get("reviewer_ref")) or None,
        review_timestamp=_text(request.get("review_timestamp")) or None,
        review_status=_text(request.get("review_status")) or PluginReviewStatus.UNKNOWN.value,
        review_scope=_strings(request.get("review_scope")),
        review_version=_text(request.get("review_version")) or None,
        source_refs=_source_ref_ids(request.get("source_refs")),
        limitations=_strings(request.get("limitations")),
        unknowns=_strings(request.get("unknowns")),
        required_followups=_strings(request.get("required_followups")),
        required_operator_review=request.get("required_operator_review") is not False,
        required_security_review=request.get("required_security_review") is True,
        required_privacy_review=request.get("required_privacy_review") is True,
        required_policy_review=request.get("required_policy_review") is not False,
        allowed_operations=_strings(request.get("allowed_operations")),
        forbidden_operations=_strings(request.get("forbidden_operations")),
        declared_capabilities=_strings(request.get("declared_capabilities")),
        declared_risk_tiers=_strings(request.get("declared_risk_tiers")),
        requested_permissions=_permission_ids(request.get("requested_permissions")),
        hidden_permissions=_strings(request.get("hidden_permissions")),
        data_sensitivity=_text(request.get("data_sensitivity")) or None,
        tenant_scope=_text(request.get("tenant_scope")) or None,
        project_scope=_text(request.get("project_scope")) or None,
        namespace=_text(request.get("namespace")) or None,
        provenance_refs=_strings(request.get("provenance_refs")),
        expiry_or_revalidation_at=_text(request.get("expiry_or_revalidation_at")) or None,
        supersedes_review_record_id=_text(request.get("supersedes_review_record_id")) or None,
        claims=_strings(request.get("claims")),
    )


def _validate_non_authority_fields(
    request: Mapping[str, Any],
    failures: list[PluginReviewFinding],
) -> None:
    for field_name, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if request.get(field_name) is True or (
            field_name in {
                "external_api_request",
                "call_external_api",
                "mcp_tool_call",
            }
            and _text(request.get(field_name))
        ):
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} is outside the Plugin Review Store readiness contract",
            )
    if request.get("execution_permission") not in (None, "", PLUGIN_REVIEW_STORE_EXECUTION_PERMISSION):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_plugin_review_store_required",
            "execution_permission",
            "plugin review store cannot grant execution permission",
        )


def _validate_forbidden_claims(
    request: Mapping[str, Any],
    failures: list[PluginReviewFinding],
) -> None:
    claims = " ".join(_strings(request.get("claims"))).lower()
    for phrase, reason in FORBIDDEN_CLAIMS.items():
        if phrase in claims:
            _add_failure(failures, reason, "claims", f"review record cannot claim {phrase}")


def _validate_identity(
    review_input: PluginReviewRecordInput,
    failures: list[PluginReviewFinding],
) -> None:
    has_record_id = bool(review_input.review_record_id)
    has_plugin_identity = bool(review_input.plugin_id and review_input.plugin_version)
    if not (has_record_id or has_plugin_identity):
        _add_failure(
            failures,
            "review_identity_required",
            "review_record_id",
            "review_record_id or plugin_id plus plugin_version is required",
        )


def _validate_status_and_scope(
    review_input: PluginReviewRecordInput,
    failures: list[PluginReviewFinding],
) -> None:
    if review_input.review_status not in ALLOWED_REVIEW_STATUSES:
        _add_failure(failures, "unknown_review_status", "review_status", review_input.review_status)
    if review_input.review_status == PluginReviewStatus.UNKNOWN.value:
        _add_failure(
            failures,
            "unknown_review_status_requires_attention",
            "review_status",
            "unknown review status requires operator/security attention",
        )
    for scope in review_input.review_scope:
        if scope not in ALLOWED_REVIEW_SCOPES:
            _add_failure(failures, "unknown_review_scope", "review_scope", scope)
    if not review_input.review_scope and review_input.review_status != PluginReviewStatus.DRAFT.value:
        _add_failure(
            failures,
            "review_scope_required_for_non_draft",
            "review_scope",
            "non-draft review records require review scope",
        )
    if review_input.review_status in STALE_STATUSES:
        if not (review_input.expiry_or_revalidation_at or review_input.supersedes_review_record_id):
            _add_failure(
                failures,
                "revalidation_metadata_required_for_stale_review",
                "expiry_or_revalidation_at",
                "expired, superseded, or deprecated records require revalidation metadata",
            )


def _validate_required_refs_and_scopes(
    review_input: PluginReviewRecordInput,
    failures: list[PluginReviewFinding],
) -> None:
    if review_input.review_status == PluginReviewStatus.DRAFT.value:
        return
    if not (review_input.manifest_ref or review_input.source_refs):
        _add_failure(
            failures,
            "manifest_or_source_ref_required_for_non_draft",
            "manifest_ref",
            "non-draft review records require manifest_ref or source_refs",
        )
    if not review_input.tenant_scope:
        _add_failure(
            failures,
            "tenant_scope_required_for_non_draft",
            "tenant_scope",
            "non-draft review records require tenant scope",
        )
    if not review_input.namespace:
        _add_failure(
            failures,
            "namespace_required_for_non_draft",
            "namespace",
            "non-draft review records require namespace",
        )
    if not review_input.project_scope:
        _add_failure(
            failures,
            "project_scope_required_for_non_draft",
            "project_scope",
            "non-draft review records require project scope",
        )
    if not review_input.limitations:
        _add_failure(
            failures,
            "limitations_required_for_review_record",
            "limitations",
            "review records must preserve limitations",
        )
    if not review_input.unknowns:
        _add_failure(
            failures,
            "unknowns_required_for_review_record",
            "unknowns",
            "review records must preserve unknowns",
        )


def _validate_permissions_and_review_requirements(
    review_input: PluginReviewRecordInput,
    request: Mapping[str, Any],
    failures: list[PluginReviewFinding],
) -> None:
    for permission in review_input.requested_permissions:
        if permission.lower() in WILDCARD_VALUES:
            _add_failure(
                failures,
                "wildcard_permission_denied",
                "requested_permissions",
                "wildcard requested permissions are denied",
            )
    for operation in review_input.allowed_operations:
        if operation.lower() in WILDCARD_VALUES:
            _add_failure(
                failures,
                "wildcard_operation_denied",
                "allowed_operations",
                "wildcard allowed operations are denied",
            )
    if review_input.hidden_permissions or request.get("hidden_permissions"):
        _add_failure(
            failures,
            "hidden_permissions_denied",
            "hidden_permissions",
            "review records cannot hide permissions",
        )
    high_risk = bool(
        set(review_input.declared_risk_tiers) & HIGH_RISK_TIERS
        or set(review_input.declared_capabilities) & HIGH_RISK_CAPABILITIES
        or set(review_input.requested_permissions) - {"metadata_review", "read_metadata"}
    )
    if high_risk:
        if not review_input.required_security_review:
            _add_failure(
                failures,
                "security_review_required_for_high_risk_review",
                "required_security_review",
                "high-risk plugin reviews require security review",
            )
        if not review_input.required_privacy_review:
            _add_failure(
                failures,
                "privacy_review_required_for_high_risk_review",
                "required_privacy_review",
                "high-risk plugin reviews require privacy review",
            )
        if not review_input.required_policy_review:
            _add_failure(
                failures,
                "policy_review_required_for_high_risk_review",
                "required_policy_review",
                "high-risk plugin reviews require policy review",
            )
        if not review_input.unknowns:
            _add_failure(
                failures,
                "high_risk_review_requires_unknowns",
                "unknowns",
                "high-risk review records must preserve unknowns",
            )


def _validate_related_decision(
    prefix: str,
    decision: Any | None,
    failures: list[PluginReviewFinding],
) -> None:
    if decision is None:
        return
    if _bool_field(decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            f"{prefix}_runtime_dispatch_attempt_denied",
            f"{prefix}_decision.runtime_dispatch_allowed",
            f"{prefix} decision cannot grant runtime dispatch to review store",
        )
    permission_fields = (
        "approval_grant",
        "capability_grant",
        "lease_grant",
        "plugin_execution_allowed",
        "dynamic_import_allowed",
        "marketplace_publication_allowed",
    )
    if any(_bool_field(decision, field_name) for field_name in permission_fields):
        _add_failure(
            failures,
            f"{prefix}_permission_claim_denied",
            f"{prefix}_decision",
            f"{prefix} decision cannot grant permission to review store",
        )
    if prefix == "vertical_pack":
        if _bool_field(decision, "evidence_provided_by_pack_output") or _bool_field(decision, "pack_output_is_evidence"):
            _add_failure(
                failures,
                "vertical_pack_evidence_claim_denied",
                "vertical_pack_decision.evidence_provided_by_pack_output",
                "vertical pack output cannot become review evidence by itself",
            )
        if _bool_field(decision, "verifier_success") or _bool_field(decision, "pack_output_is_verifier_truth"):
            _add_failure(
                failures,
                "vertical_pack_verifier_success_claim_denied",
                "vertical_pack_decision.verifier_success",
                "vertical pack output cannot become verifier success",
            )
    if prefix in {"manifest", "integrity", "lifecycle"}:
        evidence_fields = (
            "evidence_provided_by_pack_output",
            "evidence_provided_by_lifecycle",
            "evidence_provided_by_review",
        )
        if any(_bool_field(decision, field_name) for field_name in evidence_fields):
            _add_failure(
                failures,
                f"{prefix}_evidence_claim_denied",
                f"{prefix}_decision",
                f"{prefix} decision cannot create review evidence",
            )
        if _bool_field(decision, "verifier_success"):
            _add_failure(
                failures,
                f"{prefix}_verifier_success_claim_denied",
                f"{prefix}_decision.verifier_success",
                f"{prefix} decision cannot create verifier success",
            )
    if _tuple_field(decision, "failure_reasons"):
        _add_failure(
            failures,
            f"{prefix}_decision_has_failures",
            f"{prefix}_decision.failure_reasons",
            f"{prefix} decision failures require review revalidation",
        )
    if prefix == "integrity":
        if _bool_field(decision, "review_required") or _bool_field(decision, "quarantine_required"):
            _add_failure(
                failures,
                "integrity_requires_revalidation",
                "integrity_decision.review_required",
                "manifest drift or quarantine requires review revalidation",
            )
        if _field(decision, "decision_state") not in {"", "unchanged"}:
            _add_failure(
                failures,
                "integrity_state_requires_revalidation",
                "integrity_decision.decision_state",
                "non-unchanged integrity state requires review revalidation",
            )
    if prefix == "lifecycle":
        current = _field(decision, "current_state")
        requested = _field(decision, "requested_state")
        if current in {"revoked", "quarantined", "deprecated", "failed_validation"} or requested in {
            "revoked",
            "quarantined",
            "deprecated",
            "failed_validation",
        }:
            _add_failure(
                failures,
                "lifecycle_state_requires_revalidation",
                "lifecycle_decision.current_state",
                "quarantined, deprecated, revoked, or failed lifecycle state blocks review readiness",
            )


def _record_from_input(review_input: PluginReviewRecordInput) -> PluginReviewRecord:
    limitations = tuple(PluginReviewLimitation(note=note) for note in review_input.limitations)
    provenance = PluginReviewProvenance(
        reviewer_ref=review_input.reviewer_ref,
        review_timestamp=review_input.review_timestamp,
        source_refs=review_input.source_refs,
        provenance_refs=review_input.provenance_refs,
    )
    status = review_input.review_status
    return PluginReviewRecord(
        review_record_id=review_input.review_record_id,
        plugin_id=review_input.plugin_id,
        plugin_name=review_input.plugin_name,
        plugin_version=review_input.plugin_version,
        manifest_ref=review_input.manifest_ref,
        manifest_checksum_ref=review_input.manifest_checksum_ref,
        signature_ref=review_input.signature_ref,
        lifecycle_decision_ref=review_input.lifecycle_decision_ref,
        vertical_pack_decision_ref=review_input.vertical_pack_decision_ref,
        policy_refs=review_input.policy_refs,
        evidence_refs=review_input.evidence_refs,
        reviewer_ref=review_input.reviewer_ref,
        review_timestamp=review_input.review_timestamp,
        review_status=status,
        review_scope=review_input.review_scope,
        review_version=review_input.review_version,
        source_refs=review_input.source_refs,
        limitations=limitations,
        unknowns=review_input.unknowns,
        required_followups=review_input.required_followups,
        required_operator_review=review_input.required_operator_review,
        required_security_review=review_input.required_security_review,
        required_privacy_review=review_input.required_privacy_review,
        required_policy_review=review_input.required_policy_review,
        allowed_operations=review_input.allowed_operations,
        forbidden_operations=review_input.forbidden_operations,
        declared_capabilities=review_input.declared_capabilities,
        declared_risk_tiers=review_input.declared_risk_tiers,
        requested_permissions=review_input.requested_permissions,
        data_sensitivity=review_input.data_sensitivity,
        tenant_scope=review_input.tenant_scope,
        project_scope=review_input.project_scope,
        namespace=review_input.namespace,
        provenance=provenance,
        provenance_refs=review_input.provenance_refs,
        expiry_or_revalidation_at=review_input.expiry_or_revalidation_at,
        supersedes_review_record_id=review_input.supersedes_review_record_id,
        review_blocked=status in BLOCKING_STATUSES,
        revalidation_required=status in STALE_STATUSES,
    )


def _validation_status(
    review_input: PluginReviewRecordInput,
    failures: list[PluginReviewFinding],
) -> str:
    reasons = {failure.reason for failure in failures}
    failed_validation_reasons = {
        "missing_review_record",
        "review_identity_required",
        "manifest_or_source_ref_required_for_non_draft",
        "tenant_scope_required_for_non_draft",
        "namespace_required_for_non_draft",
        "project_scope_required_for_non_draft",
        "unknown_review_scope",
        "unknown_review_status",
    }
    if reasons & failed_validation_reasons:
        return "failed_validation"
    if review_input.review_status == PluginReviewStatus.UNKNOWN.value:
        return "requires_operator_attention"
    if failures:
        return "blocked"
    return review_input.review_status


def _requires_operator_attention(
    review_input: PluginReviewRecordInput,
    failures: list[PluginReviewFinding],
) -> bool:
    if review_input.review_status == PluginReviewStatus.UNKNOWN.value:
        return True
    if review_input.review_status in STALE_STATUSES | BLOCKING_STATUSES:
        return True
    return bool(failures)


def _decision(
    *,
    validation_status: str,
    review_record_id: str | None,
    plugin_id: str | None,
    plugin_version: str | None,
    failures: tuple[PluginReviewFinding, ...],
    review_input: PluginReviewRecordInput | None = None,
    review_record: PluginReviewRecord | None = None,
    requires_operator_attention: bool = False,
) -> PluginReviewDecision:
    return PluginReviewDecision(
        contract_version=PLUGIN_REVIEW_STORE_VERSION,
        validation_status=validation_status,
        review_record_id=review_record_id,
        plugin_id=plugin_id,
        plugin_version=plugin_version,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        review_input=review_input,
        review_record=review_record,
        requires_operator_attention=requires_operator_attention,
    )


def _permission_ids(value: Any) -> tuple[str, ...]:
    ids: list[str] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            text = _text(item.get("scope")) or _text(item.get("permission")) or _text(item.get("name"))
        else:
            text = _text(item)
        if text:
            ids.append(text)
    return tuple(ids)


def _source_ref_ids(value: Any) -> tuple[str, ...]:
    ids: list[str] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            text = _text(item.get("ref_id")) or _text(item.get("id")) or _text(item.get("path"))
        else:
            text = _text(item)
        if text:
            ids.append(text)
    return tuple(ids)


def _tuple_field(value: Any, field_name: str) -> tuple[Any, ...]:
    if value is None:
        return ()
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


def _field(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get(field_name))
    return _text(getattr(value, field_name, None))


def _bool_field(value: Any, field_name: str) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return value.get(field_name) is True
    return getattr(value, field_name, None) is True


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


def _add_failure(
    failures: list[PluginReviewFinding],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(PluginReviewFinding(reason=reason, field=field, message=message))
