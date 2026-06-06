from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


PROVIDER_PROBE_SURFACE_DISPLAY_VERSION = "provider-probe-maintenance-surface-display/1"
PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION = (
    "not_granted_by_provider_probe_surface_display"
)

SURFACE_DISPLAY_SOURCE_CLASSES = {
    "maintenance_probe_projection_api",
    "local_provider_probe_projection",
    "manual_smoke_projection_fixture",
    "synthetic_fixture",
    "mission_control_future",
    "maintenance_scan_future",
    "unknown",
}

SURFACE_DISPLAY_STATE_CLASSES = {
    "no_projection_available",
    "not_observed",
    "not_configured",
    "metadata_candidate",
    "model_list_candidate",
    "empty_model_list_candidate",
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
    "blocked_by_policy",
    "future_gated",
    "unknown",
}

UI_MEANING_CLASSES = {
    "neutral_no_data",
    "informational_candidate",
    "warning_negative_candidate",
    "operator_review_recommended",
    "retry_requires_operator_approval",
    "blocked",
    "future_gated",
    "unknown",
}

FORBIDDEN_UI_MEANINGS = {
    "runtime_failure",
    "provider_health_verified",
    "model_availability_verified",
    "model_unavailable_proof",
    "verifier_success",
    "evidence_available",
    "retry_authorized",
    "execution_ready",
    "auto_mode_selected",
    "frontend_authority",
}

DISPLAY_SEVERITY_CLASSES = {
    "neutral",
    "info",
    "attention",
    "warning",
    "blocked",
    "future",
    "unknown",
}

NEGATIVE_DISPLAY_STATES = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
}

RETRY_REQUIRES_OPERATOR_APPROVAL_STATES = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
}

METADATA_DISPLAY_STATES = {
    "metadata_candidate",
    "model_list_candidate",
    "empty_model_list_candidate",
}

RECOMMENDED_WORDING_BY_STATE = {
    "no_projection_available": "No current provider probe projection is available.",
    "not_observed": "Provider probe has not been observed.",
    "unreachable_negative_candidate": (
        "Provider endpoint was unreachable during the observed probe; this is a "
        "negative candidate, not a runtime failure."
    ),
    "metadata_candidate": "Metadata candidate only; not provider health proof.",
    "model_list_candidate": (
        "Model-list metadata candidate only; not model availability proof."
    ),
    "empty_model_list_candidate": "Empty model-list candidate; not runtime failure.",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "frontend_authority": "frontend_authority_not_allowed",
    "api_authority": "api_authority_not_allowed",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_display": "display_cannot_provide_evidence",
    "evidence_provided_by_probe_projection": "display_cannot_provide_evidence",
    "evidence_provided_by_maintenance_projection": "display_cannot_provide_evidence",
    "evidence_provided": "display_cannot_provide_evidence",
    "evidence_created": "display_cannot_provide_evidence",
    "verifier_success": "display_cannot_mark_verifier_success",
    "verified_success": "display_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "retry_authorized": "retry_authorization_denied",
    "retry_control_exposed": "retry_control_exposure_denied",
    "action_control_exposed": "action_control_exposure_denied",
    "provider_health_verified": "provider_health_verification_denied",
    "health_verified": "provider_health_verification_denied",
    "model_availability_verified": "model_availability_verification_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "runtime_health_mutated": "runtime_health_mutation_denied",
    "maintenance_health_mutated": "maintenance_health_mutation_denied",
    "fake_current_projection_created": "fake_current_projection_denied",
    "fake_health_created": "fake_health_denied",
    "fake_success_created": "fake_success_denied",
    "fake_verification_created": "fake_verification_denied",
    "display_severity_is_runtime_health": "display_runtime_health_claim_denied",
    "negative_candidate_is_runtime_failure": "negative_runtime_failure_claim_denied",
    "metadata_candidate_is_provider_health_proof": "metadata_health_proof_denied",
    "model_list_candidate_is_model_availability_proof": "model_list_availability_proof_denied",
    "empty_model_list_is_runtime_failure": "empty_model_list_runtime_failure_claim_denied",
    "model_unavailable_proof": "model_unavailable_proof_denied",
    "execution_ready": "execution_ready_claim_denied",
    "auto_mode_selected": "auto_mode_selection_claim_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "live_probe_performed": "live_probe_execution_denied",
    "real_endpoint_probed": "real_endpoint_probe_denied",
    "provider_probed": "provider_probe_execution_denied",
    "endpoint_probed": "endpoint_probe_execution_denied",
    "probe_executed": "probe_execution_denied",
    "socket_opened": "socket_open_denied",
    "http_request_performed": "http_request_denied",
    "api_call_performed": "api_call_denied",
    "model_loaded": "model_load_denied",
    "model_call_performed": "model_call_denied",
    "generation_performed": "generation_denied",
    "minimal_generation_performed": "generation_denied",
    "embedding_generated": "embedding_generation_denied",
    "reranking_performed": "reranking_denied",
    "multimodal_inference_performed": "multimodal_inference_denied",
    "multimodal_probe_performed": "multimodal_inference_denied",
    "prompt_payload_sent": "prompt_payload_denied",
    "context_payload_sent": "context_payload_denied",
    "memory_payload_sent": "memory_payload_denied",
    "repo_payload_sent": "repo_payload_denied",
    "raw_journal_payload_sent": "raw_journal_payload_denied",
    "raw_evidence_payload_sent": "raw_evidence_payload_denied",
    "api_key_validated": "api_key_validation_denied",
    "secret_read": "secret_read_denied",
    "authorization_header_sent": "authorization_header_denied",
    "response_body_logged": "response_body_logging_denied",
    "secret_logged": "secret_logging_denied",
    "cloud_provider_called": "cloud_provider_call_denied",
    "lan_or_remote_endpoint_called": "lan_or_remote_endpoint_call_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "repo_file_read_performed": "repo_file_read_denied",
    "web_query_performed": "web_query_denied",
}


@dataclass(frozen=True)
class ProviderProbeSurfaceDisplayFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ProviderProbeSurfaceDisplayInput:
    request_id: str | None
    surface_display_source_class: str | None
    surface_display_state_class: str | None
    ui_meaning_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    display_wording_candidate: str | None
    display_severity_class: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RelatedProviderProbeSurfaceDisplayReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class ProviderProbeSurfaceDisplayDecision:
    contract_version: str
    display_readiness_status: str
    request_id: str | None
    surface_display_source_class: str | None
    surface_display_state_class: str | None
    ui_meaning_class: str | None
    namespace: str | None
    display_severity_class: str
    recommended_wording: str
    retry_guidance: str
    truthfulness_classification: str
    color_semantics: str
    related_references: tuple[RelatedProviderProbeSurfaceDisplayReference, ...]
    required_operator_actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...]
    display_input: ProviderProbeSurfaceDisplayInput | None
    authority: bool = False
    frontend_authority: bool = False
    api_authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_display: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    retry_authorized: bool = False
    retry_control_exposed: bool = False
    action_control_exposed: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    runtime_health_mutated: bool = False
    maintenance_health_mutated: bool = False
    fake_current_projection_created: bool = False
    fake_health_created: bool = False
    fake_success_created: bool = False
    fake_verification_created: bool = False
    live_probe_performed: bool = False
    real_endpoint_probed: bool = False
    socket_opened: bool = False
    http_request_performed: bool = False
    model_call_performed: bool = False
    generation_performed: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    multimodal_inference_performed: bool = False
    data_sent_external: bool = False
    read_only_projection: bool = True
    requires_backend_validation: bool = True
    requires_policy_check: bool = True


def validate_provider_probe_surface_display_request(
    request: Mapping[str, Any] | None,
    *,
    local_provider_probe_api_surface_decision: Any | None = None,
    local_provider_probe_maintenance_projection_decision: Any | None = None,
    local_provider_probe_projection_decision: Any | None = None,
    local_provider_probe_runner_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
) -> ProviderProbeSurfaceDisplayDecision:
    """Validate provider-probe display metadata without UI authority or probing."""

    if not isinstance(request, Mapping):
        failure = ProviderProbeSurfaceDisplayFailure(
            reason="missing_request",
            field="request",
            message="provider probe surface display requires caller-supplied metadata",
        )
        return _decision(display_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[ProviderProbeSurfaceDisplayFailure] = []
    related_references: list[RelatedProviderProbeSurfaceDisplayReference] = []

    _validate_forbidden_claims("request", data, failures)
    _validate_forbidden_ui_meaning(data, failures)
    related_decisions = {
        "local_provider_probe_api_surface": local_provider_probe_api_surface_decision,
        "local_provider_probe_maintenance_projection": local_provider_probe_maintenance_projection_decision,
        "local_provider_probe_projection": local_provider_probe_projection_decision,
        "local_provider_probe_runner": local_provider_probe_runner_decision,
        "local_provider_health": local_provider_health_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_model_inventory": local_model_inventory_decision,
        "local_model_context_profile": local_model_context_profile_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "capability_lease": capability_lease_decision,
        "mission_control": mission_control_decision,
        "passive_observe": passive_observe_decision,
    }
    for label, decision in related_decisions.items():
        _validate_related_decision(label, decision, failures, related_references)

    display_input = ProviderProbeSurfaceDisplayInput(
        request_id=_text(data.get("request_id")),
        surface_display_source_class=_text(data.get("surface_display_source_class")),
        surface_display_state_class=_normalized_state(data),
        ui_meaning_class=_text(data.get("ui_meaning_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        display_wording_candidate=_text(data.get("display_wording_candidate")),
        display_severity_class=_text(data.get("display_severity_class")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(display_input, failures)
    _validate_display_semantics(display_input, failures)
    _validate_wording(display_input, failures)

    return _decision(
        display_input=display_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    display_input: ProviderProbeSurfaceDisplayInput | None,
    related_references: tuple[RelatedProviderProbeSurfaceDisplayReference, ...],
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> ProviderProbeSurfaceDisplayDecision:
    return ProviderProbeSurfaceDisplayDecision(
        contract_version=PROVIDER_PROBE_SURFACE_DISPLAY_VERSION,
        display_readiness_status=_display_readiness_status(display_input, failures),
        request_id=display_input.request_id if display_input else None,
        surface_display_source_class=display_input.surface_display_source_class if display_input else None,
        surface_display_state_class=display_input.surface_display_state_class if display_input else None,
        ui_meaning_class=display_input.ui_meaning_class if display_input else None,
        namespace=display_input.namespace if display_input else None,
        display_severity_class=_display_severity(display_input, failures),
        recommended_wording=_recommended_wording(display_input, failures),
        retry_guidance=_retry_guidance(display_input, failures),
        truthfulness_classification=_truthfulness_classification(display_input, failures),
        color_semantics=_color_semantics(display_input, failures),
        related_references=related_references,
        required_operator_actions=_required_operator_actions(display_input, failures),
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        display_input=display_input,
    )


def _validate_required(
    display_input: ProviderProbeSurfaceDisplayInput,
    failures: list[ProviderProbeSurfaceDisplayFailure],
) -> None:
    required = {
        "request_id": display_input.request_id,
        "surface_display_source_class": display_input.surface_display_source_class,
        "surface_display_state_class": display_input.surface_display_state_class,
        "ui_meaning_class": display_input.ui_meaning_class,
        "namespace": display_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (display_input.source_refs or display_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "source refs or provenance are required",
        )
    if (
        display_input.surface_display_source_class
        and display_input.surface_display_source_class not in SURFACE_DISPLAY_SOURCE_CLASSES
    ):
        _add_failure(
            failures,
            "unsupported_surface_display_source_class",
            "surface_display_source_class",
            "surface display source class is not recognized",
        )
    if (
        display_input.surface_display_state_class
        and display_input.surface_display_state_class not in SURFACE_DISPLAY_STATE_CLASSES
    ):
        _add_failure(
            failures,
            "unsupported_surface_display_state_class",
            "surface_display_state_class",
            "surface display state class is not recognized",
        )
    if display_input.ui_meaning_class and display_input.ui_meaning_class not in UI_MEANING_CLASSES:
        _add_failure(
            failures,
            "unsupported_ui_meaning_class",
            "ui_meaning_class",
            "UI meaning class is not recognized or is forbidden",
        )
    if (
        display_input.display_severity_class
        and display_input.display_severity_class not in DISPLAY_SEVERITY_CLASSES
    ):
        _add_failure(
            failures,
            "unsupported_display_severity_class",
            "display_severity_class",
            "display severity class is not recognized",
        )


def _validate_display_semantics(
    display_input: ProviderProbeSurfaceDisplayInput,
    failures: list[ProviderProbeSurfaceDisplayFailure],
) -> None:
    source = display_input.surface_display_source_class
    state = display_input.surface_display_state_class
    meaning = display_input.ui_meaning_class
    severity = display_input.display_severity_class

    if source == "unknown":
        _add_failure(
            failures,
            "unknown_surface_display_source_blocked",
            "surface_display_source_class",
            "unknown display source requires clarification",
        )
    if state == "unknown":
        _add_failure(
            failures,
            "unknown_surface_display_state_blocked",
            "surface_display_state_class",
            "unknown display state requires clarification",
        )
    if meaning == "unknown":
        _add_failure(
            failures,
            "unknown_ui_meaning_blocked",
            "ui_meaning_class",
            "unknown UI meaning requires clarification",
        )

    if state in {"no_projection_available", "not_observed", "not_configured"}:
        if meaning != "neutral_no_data":
            _add_failure(
                failures,
                "no_data_state_requires_neutral_meaning",
                "ui_meaning_class",
                "no projection, not observed, and not configured states must be neutral no-data displays",
            )
        if severity and severity not in {"neutral", "info"}:
            _add_failure(
                failures,
                "no_data_state_severity_overstated",
                "display_severity_class",
                "no-data provider probe display must not be warning, blocked, or failure severity",
            )
    if state in METADATA_DISPLAY_STATES:
        if meaning != "informational_candidate":
            _add_failure(
                failures,
                "metadata_state_requires_informational_meaning",
                "ui_meaning_class",
                "metadata and model-list candidates must be informational candidates only",
            )
        if severity and severity not in {"neutral", "info"}:
            _add_failure(
                failures,
                "metadata_state_severity_overstated",
                "display_severity_class",
                "metadata candidates must not be displayed as verified success or failure",
            )
    if state in NEGATIVE_DISPLAY_STATES:
        allowed_meanings = {
            "warning_negative_candidate",
            "operator_review_recommended",
            "retry_requires_operator_approval",
        }
        if meaning not in allowed_meanings:
            _add_failure(
                failures,
                "negative_state_requires_warning_or_review_meaning",
                "ui_meaning_class",
                "negative candidates must remain warning/review candidates, not runtime failures",
            )
        if severity and severity not in {"attention", "warning"}:
            _add_failure(
                failures,
                "negative_state_severity_must_not_be_runtime_failure",
                "display_severity_class",
                "negative candidates may be attention or warning, not runtime failure",
            )
    if state in RETRY_REQUIRES_OPERATOR_APPROVAL_STATES:
        if meaning != "retry_requires_operator_approval":
            _add_failure(
                failures,
                "retryable_state_requires_operator_approval_meaning",
                "ui_meaning_class",
                "retryable negative candidates must preserve explicit operator approval wording",
            )
    if state == "blocked_by_policy":
        if meaning != "blocked":
            _add_failure(
                failures,
                "blocked_policy_state_requires_blocked_meaning",
                "ui_meaning_class",
                "blocked-by-policy display must stay blocked and must not become retry/action ready",
            )
    if state == "future_gated":
        if meaning != "future_gated":
            _add_failure(
                failures,
                "future_gated_state_requires_future_meaning",
                "ui_meaning_class",
                "future-gated display must stay future-gated",
            )


def _validate_wording(
    display_input: ProviderProbeSurfaceDisplayInput,
    failures: list[ProviderProbeSurfaceDisplayFailure],
) -> None:
    wording = display_input.display_wording_candidate
    if not wording:
        return
    lowered = wording.lower()
    forbidden_fragments = {
        "runtime failure": "display_wording_runtime_failure_claim_denied",
        "provider health verified": "display_wording_provider_health_claim_denied",
        "model availability verified": "display_wording_model_availability_claim_denied",
        "model available": "display_wording_model_availability_claim_denied",
        "verifier success": "display_wording_verifier_claim_denied",
        "evidence available": "display_wording_evidence_claim_denied",
        "retry authorized": "display_wording_retry_authorization_denied",
        "execution ready": "display_wording_execution_ready_claim_denied",
        "auto mode selected": "display_wording_auto_mode_claim_denied",
    }
    for fragment, reason in forbidden_fragments.items():
        if fragment in lowered:
            _add_failure(
                failures,
                reason,
                "display_wording_candidate",
                "display wording cannot claim runtime failure, verified health, model availability, evidence, verifier success, retry authorization, execution readiness, or Auto Mode selection",
            )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[ProviderProbeSurfaceDisplayFailure],
    related_references: list[RelatedProviderProbeSurfaceDisplayReference],
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
            f"{label} cannot authorize probing, retry controls, provider proof, model proof, health mutation, evidence, verifier success, authority, or grants",
        )
    related_references.append(
        RelatedProviderProbeSurfaceDisplayReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[ProviderProbeSurfaceDisplayFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, retry authorization, health proof, model proof, fake status, or health mutation",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot probe providers, open sockets, perform HTTP, call models, send payloads, validate secrets, call external endpoints, or mutate runtime state",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (
        None,
        "",
        PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION,
    ):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "provider probe surface display cannot grant execution permission",
            )


def _validate_forbidden_ui_meaning(
    data: Mapping[str, Any],
    failures: list[ProviderProbeSurfaceDisplayFailure],
) -> None:
    meaning = _text(data.get("ui_meaning_class"))
    if meaning in FORBIDDEN_UI_MEANINGS:
        _add_failure(
            failures,
            "forbidden_ui_meaning_denied",
            "ui_meaning_class",
            "UI meaning cannot claim runtime failure, verified provider health, model availability, evidence, retry authorization, execution readiness, Auto Mode selection, or frontend authority",
        )


def _display_readiness_status(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        state = display_input.surface_display_state_class
        if state in {"no_projection_available", "not_observed", "not_configured"}:
            return "display_ready_neutral_no_data"
        if state in METADATA_DISPLAY_STATES:
            return "display_ready_informational_candidate"
        if state in NEGATIVE_DISPLAY_STATES:
            return "display_ready_negative_candidate"
        if state == "blocked_by_policy":
            return "display_ready_blocked_by_policy"
        if state == "future_gated":
            return "display_ready_future_gated"
        return "display_ready"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_unsafe_related_decision"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_missing_required_field"
    if any("wording" in reason or "runtime_failure" in reason or "health" in reason or "availability" in reason or "proof" in reason or "verifier" in reason or "evidence" in reason for reason in reasons):
        return "blocked_by_truthfulness_claim"
    if any("retry" in reason or "control" in reason or "execution_ready" in reason for reason in reasons):
        return "blocked_by_retry_or_action_claim"
    if any("probe" in reason or "socket" in reason or "http" in reason or "call" in reason or "payload" in reason or "external" in reason for reason in reasons):
        return "blocked_by_execution_claim"
    if any("grant" in reason or "authority" in reason or "dispatch" in reason for reason in reasons):
        return "blocked_by_authority_claim"
    return "blocked_by_display_policy"


def _display_severity(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.display_severity_class:
        return display_input.display_severity_class
    state = display_input.surface_display_state_class
    if state in {"no_projection_available", "not_observed", "not_configured"}:
        return "neutral"
    if state in METADATA_DISPLAY_STATES:
        return "info"
    if state in NEGATIVE_DISPLAY_STATES:
        return "warning"
    if state == "blocked_by_policy":
        return "blocked"
    if state == "future_gated":
        return "future"
    return "unknown"


def _recommended_wording(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "Display is blocked until required metadata and truthfulness constraints are satisfied."
    state = display_input.surface_display_state_class or "unknown"
    if state in RECOMMENDED_WORDING_BY_STATE:
        return RECOMMENDED_WORDING_BY_STATE[state]
    if state in NEGATIVE_DISPLAY_STATES:
        return f"{state} observed as a negative candidate; not a runtime failure."
    if state == "blocked_by_policy":
        return "Provider probe display is blocked by policy."
    if state == "future_gated":
        return "Provider probe display is future-gated."
    return "Provider probe display state is unknown and requires review."


def _retry_guidance(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    if display_input.surface_display_state_class in RETRY_REQUIRES_OPERATOR_APPROVAL_STATES:
        return "Retry requires explicit operator approval."
    return "No retry is authorized by provider probe surface display."


def _truthfulness_classification(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked"
    return (
        "display_not_runtime_health_not_provider_health_not_model_availability_"
        "not_evidence_not_verifier_success_not_retry_authorization"
    )


def _color_semantics(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> str:
    if display_input is None or failures:
        return "blocked_display_not_runtime_health"
    state = display_input.surface_display_state_class
    if state in {"no_projection_available", "not_observed", "not_configured"}:
        return "neutral_not_failure"
    if state in METADATA_DISPLAY_STATES:
        return "info_not_verified_success"
    if state in NEGATIVE_DISPLAY_STATES:
        return "warning_not_runtime_failure"
    if state == "blocked_by_policy":
        return "blocked_not_retry_ready"
    if state == "future_gated":
        return "future_not_enabled"
    return "unknown_requires_review"


def _required_operator_actions(
    display_input: ProviderProbeSurfaceDisplayInput | None,
    failures: tuple[ProviderProbeSurfaceDisplayFailure, ...],
) -> tuple[str, ...]:
    if display_input is None or failures:
        return ()
    actions: list[str] = []
    state = display_input.surface_display_state_class
    if state in RETRY_REQUIRES_OPERATOR_APPROVAL_STATES:
        actions.append("operator_approval_required_before_retry")
    if state in NEGATIVE_DISPLAY_STATES:
        actions.append("operator_review_recommended")
    if state in {"blocked_by_policy", "future_gated", "unknown"}:
        actions.append("operator_review_recommended")
    return tuple(dict.fromkeys(actions))


def _normalized_state(data: Mapping[str, Any]) -> str | None:
    explicit = _text(data.get("surface_display_state_class"))
    if explicit:
        return explicit
    api_result = _text(data.get("projection_result_class"))
    probe_result = _text(data.get("probe_result_class"))
    aliases = {
        "provider_probe_unreachable_candidate": "unreachable_negative_candidate",
        "provider_probe_timeout_candidate": "timeout_negative_candidate",
        "provider_probe_connection_refused_candidate": "connection_refused_negative_candidate",
        "provider_probe_invalid_response_candidate": "invalid_response_negative_candidate",
        "provider_probe_unauthorized_candidate": "unauthorized_negative_candidate",
        "provider_probe_unsupported_endpoint_candidate": "unsupported_endpoint_negative_candidate",
        "provider_probe_metadata_candidate": "metadata_candidate",
        "provider_probe_model_list_candidate": "model_list_candidate",
        "provider_probe_empty_model_list_candidate": "empty_model_list_candidate",
        "provider_probe_not_observed": "not_observed",
        "provider_probe_not_configured": "not_configured",
    }
    if api_result:
        return aliases.get(api_result, api_result)
    if probe_result:
        return aliases.get(probe_result, probe_result)
    return None


def _related_status(decision: Any) -> str | None:
    for field in (
        "display_readiness_status",
        "api_surface_status_class",
        "projection_status",
        "runner_status",
        "probe_result_status",
        "readiness_status",
        "selection_status",
        "inventory_status",
        "profile_status",
        "policy_status",
        "governance_status",
        "scope_status",
        "lifecycle_state",
        "policy_outcome",
    ):
        value = _field_value(decision, field)
        if value is not None:
            return str(value)
    return None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if source is None:
        return None
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "allowed", "grant"}
    return bool(value)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (deepcopy(dict(value)),)
    if isinstance(value, (list, tuple)):
        return tuple(deepcopy(dict(item)) for item in value if isinstance(item, Mapping))
    return ()


def _add_failure(
    failures: list[ProviderProbeSurfaceDisplayFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(ProviderProbeSurfaceDisplayFailure(reason=reason, field=field, message=message))
