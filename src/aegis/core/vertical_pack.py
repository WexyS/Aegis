from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


VERTICAL_PACK_FRAMEWORK_VERSION = "vertical-pack-framework/1"
VERTICAL_PACK_EXECUTION_PERMISSION = "not_granted_by_vertical_pack_framework"

VERTICAL_PACK_CATEGORIES = {
    "repo_audit",
    "developer_work_passport",
    "skopos_terminology",
    "glossa",
    "compliance_evidence",
    "language_learning",
    "document_analysis",
    "coding_report",
    "security_eval",
    "business_automation",
    "freelance_workflow",
    "browser_workflow",
    "messaging_comms",
    "voice",
    "vision",
    "model_provider",
    "memory_context",
    "custom",
}

VERTICAL_PACK_OPERATING_PROFILES = {
    "read_only",
    "proposal_only",
    "approval_gated_action",
    "evidence_reporting",
    "eval_only",
    "training_candidate_source",
    "external_integration_candidate",
}

TENANT_PROJECT_SCOPED_CATEGORIES = VERTICAL_PACK_CATEGORIES - {
    "repo_audit",
    "security_eval",
    "custom",
}
MODEL_USING_CATEGORIES = {
    "skopos_terminology",
    "glossa",
    "language_learning",
    "document_analysis",
    "coding_report",
    "voice",
    "vision",
    "model_provider",
}
MEMORY_USING_CATEGORIES = {
    "glossa",
    "language_learning",
    "memory_context",
    "business_automation",
    "freelance_workflow",
}
TOOL_USING_CATEGORIES = {
    "repo_audit",
    "coding_report",
    "browser_workflow",
    "messaging_comms",
    "business_automation",
    "freelance_workflow",
}
EXTERNAL_INTEGRATION_CATEGORIES = {
    "business_automation",
    "freelance_workflow",
    "messaging_comms",
}
EVIDENCE_REQUIRED_PROFILES = {"evidence_reporting", "approval_gated_action"}
BLOCKING_LIFECYCLE_STATES = {
    "revoked",
    "quarantined",
    "deprecated",
    "failed_validation",
    "blocked_by_policy",
    "blocked_by_privacy",
    "blocked_by_missing_evidence",
}


@dataclass(frozen=True)
class VerticalPackDescriptor:
    pack_id: str
    pack_category: str
    operating_profile: str
    namespace: str
    tenant_scope: str | None
    project_scope: str | None
    required_capabilities: tuple[str, ...]
    required_tools: tuple[str, ...]
    required_model_roles: tuple[str, ...]
    required_memory_namespaces: tuple[str, ...]
    required_external_api_scopes: tuple[str, ...]
    required_eval_families: tuple[str, ...]
    evidence_expectations: tuple[str, ...]
    verifier_expectations: tuple[str, ...]
    policy_requirements: tuple[str, ...]
    approval_requirements: tuple[str, ...]
    lease_requirements: tuple[str, ...]
    data_sensitivity: str | None
    privacy_class: str | None


@dataclass(frozen=True)
class VerticalPackValidationFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class VerticalPackFrameworkDecision:
    framework_version: str
    descriptor_present: bool
    validation_status: str
    pack_id: str | None
    pack_category: str | None
    operating_profile: str | None
    namespace: str | None
    failure_reasons: tuple[str, ...]
    failures: tuple[VerticalPackValidationFailure, ...]
    descriptor: VerticalPackDescriptor | None = None
    authority: bool = False
    execution_permission: str = VERTICAL_PACK_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_pack_output: bool = False
    verifier_success: bool = False
    runtime_dispatch_allowed: bool = False
    pack_output_is_evidence: bool = False
    pack_output_is_verifier_truth: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_manifest_validation: bool = True
    requires_integrity_check: bool = True
    requires_lifecycle_check: bool = True


def validate_vertical_pack_descriptor(
    descriptor: Mapping[str, Any] | None,
    *,
    manifest_decision: Any | None = None,
    integrity_decision: Any | None = None,
    lifecycle_decision: Any | None = None,
) -> VerticalPackFrameworkDecision:
    """Validate a future vertical pack descriptor as non-authoritative metadata.

    The helper is intentionally pure. It never loads pack code, creates a
    registry, executes tools, calls models, mutates runtime state, or grants
    runtime dispatch permission.
    """

    failures: list[VerticalPackValidationFailure] = []
    if not isinstance(descriptor, Mapping):
        failure = VerticalPackValidationFailure(
            reason="missing_descriptor",
            field="descriptor",
            message="vertical pack descriptor must be a mapping",
        )
        return _decision(
            descriptor_present=False,
            pack_id=None,
            pack_category=None,
            operating_profile=None,
            namespace=None,
            failures=(failure,),
            validation_status="failed_validation",
        )

    pack_id = _text(descriptor.get("pack_id")) or None
    category = _text(descriptor.get("pack_category")) or None
    profile = _text(descriptor.get("operating_profile")) or None
    namespace = _text(descriptor.get("namespace")) or None

    for field_name in ("pack_id", "pack_category", "operating_profile", "namespace"):
        if not _text(descriptor.get(field_name)):
            _add_failure(
                failures,
                "missing_required_field",
                field_name,
                f"{field_name} is required for vertical pack review",
            )

    if category and category not in VERTICAL_PACK_CATEGORIES:
        _add_failure(failures, "unknown_pack_category", "pack_category", category)
    if category == "custom" and not _text(descriptor.get("custom_category_namespace")):
        _add_failure(
            failures,
            "custom_category_requires_explicit_namespace",
            "custom_category_namespace",
            "custom vertical packs require an explicit category namespace",
        )
    if profile and profile not in VERTICAL_PACK_OPERATING_PROFILES:
        _add_failure(failures, "unknown_operating_profile", "operating_profile", profile)

    _validate_non_authority_fields(descriptor, failures)
    _validate_scopes(descriptor, category, profile, failures)
    _validate_profile_requirements(descriptor, profile, failures)
    _validate_pack_specific_requirements(descriptor, category, profile, failures)
    _validate_manifest_relationship(manifest_decision, failures)
    _validate_integrity_relationship(integrity_decision, failures)
    _validate_lifecycle_relationship(lifecycle_decision, failures)

    parsed = None
    if pack_id and category and profile and namespace:
        parsed = VerticalPackDescriptor(
            pack_id=pack_id,
            pack_category=category,
            operating_profile=profile,
            namespace=namespace,
            tenant_scope=_text(descriptor.get("tenant_scope")) or None,
            project_scope=_text(descriptor.get("project_scope")) or None,
            required_capabilities=_strings(descriptor.get("required_capabilities")),
            required_tools=_strings(descriptor.get("required_tools")),
            required_model_roles=_strings(descriptor.get("required_model_roles")),
            required_memory_namespaces=_strings(descriptor.get("required_memory_namespaces")),
            required_external_api_scopes=_strings(descriptor.get("required_external_api_scopes")),
            required_eval_families=_strings(descriptor.get("required_eval_families")),
            evidence_expectations=_strings(descriptor.get("evidence_expectations")),
            verifier_expectations=_strings(descriptor.get("verifier_expectations")),
            policy_requirements=_strings(descriptor.get("policy_requirements")),
            approval_requirements=_strings(descriptor.get("approval_requirements")),
            lease_requirements=_strings(descriptor.get("lease_requirements")),
            data_sensitivity=_text(descriptor.get("data_sensitivity")) or None,
            privacy_class=_text(descriptor.get("privacy_class")) or None,
        )

    validation_status = "review_ready"
    if any(failure.reason in {"missing_descriptor", "missing_required_field"} for failure in failures):
        validation_status = "failed_validation"
    elif failures:
        validation_status = "blocked"

    return _decision(
        descriptor_present=True,
        pack_id=pack_id,
        pack_category=category,
        operating_profile=profile,
        namespace=namespace,
        failures=tuple(failures),
        validation_status=validation_status,
        parsed_descriptor=parsed,
    )


def _validate_non_authority_fields(
    descriptor: Mapping[str, Any],
    failures: list[VerticalPackValidationFailure],
) -> None:
    forbidden_truthy_flags = {
        "authority": "authority_must_be_false",
        "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
        "approval_grant": "approval_grant_not_allowed",
        "capability_grant": "capability_grant_not_allowed",
        "lease_grant": "lease_grant_not_allowed",
        "evidence_provided_by_pack_output": "pack_output_cannot_provide_evidence",
        "pack_output_is_evidence": "pack_output_cannot_provide_evidence",
        "verifier_success": "pack_output_cannot_mark_verifier_success",
        "pack_output_is_verifier_truth": "pack_output_cannot_mark_verifier_success",
        "context_derived_permission": "context_derived_permission_denied",
        "memory_derived_permission": "memory_derived_permission_denied",
        "model_derived_permission": "model_derived_permission_denied",
        "plugin_derived_permission": "plugin_derived_permission_denied",
        "tool_derived_permission": "tool_derived_permission_denied",
        "api_derived_permission": "api_derived_permission_denied",
        "frontend_derived_permission": "frontend_derived_permission_denied",
        "defines_aegis_platform_identity": "pack_cannot_define_aegis_platform_identity",
        "redefines_aegis_platform_identity": "pack_cannot_define_aegis_platform_identity",
    }
    for field_name, reason in forbidden_truthy_flags.items():
        if descriptor.get(field_name) is True:
            _add_failure(
                failures,
                reason,
                field_name,
                f"{field_name} cannot grant authority or permission",
            )

    if descriptor.get("execution_permission") not in (None, "", VERTICAL_PACK_EXECUTION_PERMISSION):
        _add_failure(
            failures,
            "execution_permission_not_granted_by_vertical_pack_required",
            "execution_permission",
            "vertical pack descriptors cannot grant execution permission",
        )


def _validate_scopes(
    descriptor: Mapping[str, Any],
    category: str | None,
    profile: str | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if category in TENANT_PROJECT_SCOPED_CATEGORIES:
        if not _text(descriptor.get("tenant_scope")):
            _add_failure(
                failures,
                "tenant_scope_required_for_pack",
                "tenant_scope",
                f"{category} requires tenant scope",
            )
        if not _text(descriptor.get("project_scope")):
            _add_failure(
                failures,
                "project_scope_required_for_pack",
                "project_scope",
                f"{category} requires project scope",
            )

    uses_memory = descriptor.get("uses_memory") is True or category in MEMORY_USING_CATEGORIES
    if uses_memory and not _strings(descriptor.get("required_memory_namespaces")):
        _add_failure(
            failures,
            "memory_namespace_required",
            "required_memory_namespaces",
            "memory-using packs require explicit memory namespaces",
        )

    uses_tools = descriptor.get("uses_tools") is True or bool(_strings(descriptor.get("required_tools")))
    if uses_tools and not _strings(descriptor.get("tool_scopes")):
        _add_failure(
            failures,
            "tool_scope_required",
            "tool_scopes",
            "tool-using packs require explicit tool scopes",
        )

    uses_model = descriptor.get("uses_model") is True or category in MODEL_USING_CATEGORIES
    if uses_model:
        if not _strings(descriptor.get("required_model_roles")):
            _add_failure(
                failures,
                "model_role_required",
                "required_model_roles",
                "model-using packs require explicit model roles",
            )
        if not _strings(descriptor.get("model_provider_scopes")):
            _add_failure(
                failures,
                "model_provider_scope_required",
                "model_provider_scopes",
                "model-using packs require explicit provider scopes",
            )

    external = (
        descriptor.get("uses_external_api") is True
        or profile == "external_integration_candidate"
        or category in EXTERNAL_INTEGRATION_CATEGORIES
    )
    if external and not _strings(descriptor.get("required_external_api_scopes")):
        _add_failure(
            failures,
            "external_api_scope_required",
            "required_external_api_scopes",
            "external integration packs require explicit API scopes",
        )

    if category and category != "custom" and not _strings(descriptor.get("required_eval_families")):
        _add_failure(
            failures,
            "eval_family_required",
            "required_eval_families",
            "vertical pack descriptors require eval family coverage",
        )


def _validate_profile_requirements(
    descriptor: Mapping[str, Any],
    profile: str | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if profile in EVIDENCE_REQUIRED_PROFILES:
        if not _strings(descriptor.get("evidence_expectations")):
            _add_failure(
                failures,
                "evidence_expectation_required",
                "evidence_expectations",
                f"{profile} requires evidence expectations",
            )
        if not _strings(descriptor.get("verifier_expectations")):
            _add_failure(
                failures,
                "verifier_expectation_required",
                "verifier_expectations",
                f"{profile} requires verifier expectations",
            )
    if profile == "approval_gated_action":
        if not _strings(descriptor.get("approval_requirements")):
            _add_failure(
                failures,
                "approval_requirements_required",
                "approval_requirements",
                "action-gated packs require approval requirements",
            )
        if not _strings(descriptor.get("lease_requirements")):
            _add_failure(
                failures,
                "lease_requirements_required",
                "lease_requirements",
                "action-gated packs require lease requirements",
            )
        if not _strings(descriptor.get("policy_requirements")):
            _add_failure(
                failures,
                "policy_requirements_required",
                "policy_requirements",
                "action-gated packs require policy requirements",
            )


def _validate_pack_specific_requirements(
    descriptor: Mapping[str, Any],
    category: str | None,
    profile: str | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if category == "repo_audit":
        if profile not in {"read_only", "proposal_only"}:
            _add_failure(
                failures,
                "repo_audit_profile_must_be_read_or_proposal_only",
                "operating_profile",
                "repo audit packs are read-only or proposal-only by default",
            )
        capabilities = set(_strings(descriptor.get("required_capabilities")))
        if not ({"local_tool_read", "repo_read"} & capabilities):
            _add_failure(
                failures,
                "repo_audit_requires_repo_read_capability",
                "required_capabilities",
                "repo audit packs require repo/code read capability metadata",
            )
        provenance = set(_strings(descriptor.get("provenance_requirements")))
        if not {"source_ref", "commit_ref", "path_ref"} <= provenance:
            _add_failure(
                failures,
                "repo_audit_requires_source_commit_path_provenance",
                "provenance_requirements",
                "repo audit packs require source, commit, and path provenance",
            )
        forbidden = {"write_file", "create_file", "edit_file", "git_action"}
        if forbidden & set(_strings(descriptor.get("required_tools"))):
            _add_failure(
                failures,
                "repo_audit_mutation_tool_denied",
                "required_tools",
                "repo audit read-only contract cannot require mutation tools",
            )
        if _strings(descriptor.get("required_external_api_scopes")):
            _add_failure(
                failures,
                "repo_audit_external_api_denied_by_default",
                "required_external_api_scopes",
                "repo audit packs do not use external APIs by default",
            )

    if category == "developer_work_passport":
        if profile != "evidence_reporting":
            _add_failure(
                failures,
                "developer_work_passport_requires_evidence_reporting",
                "operating_profile",
                "developer work passport packs produce evidence reports",
            )
        if descriptor.get("surveillance_mode") is True or descriptor.get("hidden_monitoring") is True:
            _add_failure(
                failures,
                "developer_work_passport_surveillance_denied",
                "surveillance_mode",
                "developer work passport cannot become hidden monitoring",
            )
        if descriptor.get("external_sharing") is True and not _strings(descriptor.get("approval_requirements")):
            _add_failure(
                failures,
                "developer_work_passport_external_sharing_requires_approval",
                "approval_requirements",
                "external sharing requires explicit approval metadata",
            )
        if _text(descriptor.get("trust_positioning")) != "transparency_report":
            _add_failure(
                failures,
                "developer_work_passport_is_transparency_report",
                "trust_positioning",
                "developer work passport is a transparency report, not certification",
            )

    if category == "skopos_terminology":
        if profile not in {"proposal_only", "evidence_reporting"}:
            _add_failure(
                failures,
                "skopos_requires_proposal_or_evidence_profile",
                "operating_profile",
                "terminology packs are proposal-only or evidence-reporting",
            )
        for field_name in ("source_language", "target_language", "domain_refs", "reviewer_refs"):
            if not descriptor.get(field_name):
                _add_failure(
                    failures,
                    "skopos_metadata_required",
                    field_name,
                    f"{field_name} is required for terminology review",
                )

    if category == "glossa":
        for field_name in ("translation_scope", "user_scope", "project_scope"):
            if not _text(descriptor.get(field_name)):
                _add_failure(
                    failures,
                    "glossa_scope_required",
                    field_name,
                    f"{field_name} is required for Glossa scope isolation",
                )

    if category == "compliance_evidence":
        if profile != "evidence_reporting":
            _add_failure(
                failures,
                "compliance_evidence_requires_evidence_reporting",
                "operating_profile",
                "compliance evidence packs produce evidence reports",
            )
        positioning = _text(descriptor.get("trust_positioning")).lower()
        if positioning != "forensic_readiness":
            _add_failure(
                failures,
                "compliance_evidence_requires_forensic_readiness_positioning",
                "trust_positioning",
                "compliance evidence is forensic-readiness support, not legal certification",
            )
        claims = " ".join(_strings(descriptor.get("claims"))).lower()
        if "legal certification" in claims or "court-admissible" in claims:
            _add_failure(
                failures,
                "compliance_evidence_cannot_claim_legal_certification",
                "claims",
                "compliance evidence cannot claim legal certification or court admissibility by default",
            )

    if category == "language_learning":
        if not _text(descriptor.get("learner_namespace")):
            _add_failure(
                failures,
                "language_learning_requires_learner_namespace",
                "learner_namespace",
                "language learning packs require learner namespace isolation",
            )
        if descriptor.get("cross_learner_sharing") is True:
            _add_failure(
                failures,
                "language_learning_cross_learner_leakage_denied",
                "cross_learner_sharing",
                "language learning packs cannot leak across learners",
            )

    if category == "document_analysis":
        if not _strings(descriptor.get("document_provenance_requirements")):
            _add_failure(
                failures,
                "document_analysis_requires_document_provenance",
                "document_provenance_requirements",
                "document analysis requires document provenance metadata",
            )
        if not _text(descriptor.get("privacy_class")):
            _add_failure(
                failures,
                "document_analysis_requires_privacy_class",
                "privacy_class",
                "document analysis requires privacy classification",
            )

    if category == "coding_report":
        provenance = set(_strings(descriptor.get("provenance_requirements")))
        if not {"repo_ref", "path_ref", "test_ref"} <= provenance:
            _add_failure(
                failures,
                "coding_report_requires_repo_path_test_provenance",
                "provenance_requirements",
                "coding reports require repo, path, and test provenance",
            )
        forbidden = {"write_file", "create_file", "edit_file", "git_action"}
        if forbidden & set(_strings(descriptor.get("required_tools"))):
            _add_failure(
                failures,
                "coding_report_mutation_tool_denied",
                "required_tools",
                "coding report packs cannot mutate code by default",
            )

    if category == "security_eval":
        if profile != "eval_only":
            _add_failure(
                failures,
                "security_eval_requires_eval_only_profile",
                "operating_profile",
                "security eval packs are eval-only by default",
            )
        if descriptor.get("exploit_execution") is True:
            _add_failure(
                failures,
                "security_eval_exploit_execution_denied",
                "exploit_execution",
                "security eval packs cannot execute exploits in this framework",
            )


def _validate_manifest_relationship(
    manifest_decision: Any | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if manifest_decision is None:
        _add_failure(
            failures,
            "missing_manifest_validation",
            "manifest_decision",
            "vertical pack validation requires manifest validation",
        )
        return
    if _bool_field(manifest_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "manifest_runtime_dispatch_attempt_denied",
            "manifest_decision.runtime_dispatch_allowed",
            "manifest validation cannot grant runtime dispatch",
        )
    if _tuple_field(manifest_decision, "failure_reasons"):
        _add_failure(
            failures,
            "manifest_validation_failed",
            "manifest_decision.failure_reasons",
            "failed manifest validation blocks vertical pack review",
        )
    if _field(manifest_decision, "activation_status") in {"blocked", "failed_validation"}:
        _add_failure(
            failures,
            "manifest_activation_status_blocks_pack",
            "manifest_decision.activation_status",
            "blocked manifest activation status blocks vertical pack review",
        )


def _validate_integrity_relationship(
    integrity_decision: Any | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if integrity_decision is None:
        _add_failure(
            failures,
            "missing_integrity_check",
            "integrity_decision",
            "vertical pack validation requires integrity review",
        )
        return
    if _bool_field(integrity_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "integrity_runtime_dispatch_attempt_denied",
            "integrity_decision.runtime_dispatch_allowed",
            "integrity validation cannot grant runtime dispatch",
        )
    if _bool_field(integrity_decision, "quarantine_required"):
        _add_failure(
            failures,
            "integrity_quarantine_blocks_pack",
            "integrity_decision.quarantine_required",
            "integrity quarantine blocks vertical pack review",
        )
    if _bool_field(integrity_decision, "review_required"):
        _add_failure(
            failures,
            "integrity_review_required_blocks_pack",
            "integrity_decision.review_required",
            "integrity review-required state blocks active pack review",
        )
    if _field(integrity_decision, "decision_state") != "unchanged":
        _add_failure(
            failures,
            "integrity_must_be_unchanged_for_pack_review",
            "integrity_decision.decision_state",
            "vertical pack review requires unchanged reviewed manifest integrity",
        )


def _validate_lifecycle_relationship(
    lifecycle_decision: Any | None,
    failures: list[VerticalPackValidationFailure],
) -> None:
    if lifecycle_decision is None:
        _add_failure(
            failures,
            "missing_lifecycle_check",
            "lifecycle_decision",
            "vertical pack validation requires lifecycle review",
        )
        return
    if _bool_field(lifecycle_decision, "runtime_dispatch_allowed"):
        _add_failure(
            failures,
            "lifecycle_runtime_dispatch_attempt_denied",
            "lifecycle_decision.runtime_dispatch_allowed",
            "lifecycle validation cannot grant runtime dispatch",
        )
    if _tuple_field(lifecycle_decision, "failure_reasons"):
        _add_failure(
            failures,
            "lifecycle_validation_failed",
            "lifecycle_decision.failure_reasons",
            "failed lifecycle validation blocks vertical pack review",
        )
    if not _bool_field(lifecycle_decision, "transition_allowed"):
        _add_failure(
            failures,
            "lifecycle_transition_not_allowed",
            "lifecycle_decision.transition_allowed",
            "vertical pack lifecycle transition must be allowed for review",
        )
    current = _field(lifecycle_decision, "current_state")
    requested = _field(lifecycle_decision, "requested_state")
    if current in BLOCKING_LIFECYCLE_STATES or requested in BLOCKING_LIFECYCLE_STATES:
        _add_failure(
            failures,
            "lifecycle_state_blocks_pack",
            "lifecycle_decision.current_state",
            "revoked, quarantined, deprecated, failed, or blocked lifecycle states block vertical pack review",
        )


def _decision(
    *,
    descriptor_present: bool,
    pack_id: str | None,
    pack_category: str | None,
    operating_profile: str | None,
    namespace: str | None,
    failures: tuple[VerticalPackValidationFailure, ...],
    validation_status: str,
    parsed_descriptor: VerticalPackDescriptor | None = None,
) -> VerticalPackFrameworkDecision:
    return VerticalPackFrameworkDecision(
        framework_version=VERTICAL_PACK_FRAMEWORK_VERSION,
        descriptor_present=descriptor_present,
        validation_status=validation_status,
        pack_id=pack_id,
        pack_category=pack_category,
        operating_profile=operating_profile,
        namespace=namespace,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        descriptor=parsed_descriptor,
    )


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


def _field(value: Any, field_name: str) -> str:
    if isinstance(value, Mapping):
        return _text(value.get(field_name))
    return _text(getattr(value, field_name, None))


def _bool_field(value: Any, field_name: str) -> bool:
    if isinstance(value, Mapping):
        return value.get(field_name) is True
    return getattr(value, field_name, None) is True


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _add_failure(
    failures: list[VerticalPackValidationFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(VerticalPackValidationFailure(reason=reason, field=field, message=message))
