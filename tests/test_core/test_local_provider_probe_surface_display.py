from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.api.local_provider_probe_projection import (
    build_local_provider_probe_projection_api_response,
)
from aegis.core.local_provider_probe_maintenance_projection import (
    validate_local_provider_probe_maintenance_projection_request,
)
from aegis.core.local_provider_probe_projection import (
    validate_local_provider_probe_projection_request,
)
from aegis.core.local_provider_probe_surface_display import (
    PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION,
    PROVIDER_PROBE_SURFACE_DISPLAY_VERSION,
    validate_provider_probe_surface_display_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "provider-probe-surface-display:aegis:1",
        "surface_display_source_class": "maintenance_probe_projection_api",
        "surface_display_state_class": "no_projection_available",
        "ui_meaning_class": "neutral_no_data",
        "namespace": "provider_probe_surface_display",
        "source_refs": [{"ref_id": "api:/maintenance/local-provider/probe-projection"}],
        "provenance": [{"ref_id": "caller-supplied-display-metadata"}],
        "display_severity_class": "neutral",
        "limitations": ["display readiness only"],
        "unknowns": ["current provider reachability is not observed"],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        projection_status="display_ready",
        api_surface_status_class="metadata_candidate_available",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        frontend_authority=False,
        api_authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_display=False,
        evidence_provided_by_probe_projection=False,
        evidence_provided_by_maintenance_projection=False,
        evidence_provided=False,
        verifier_success=False,
        mutation_performed=False,
        retry_authorized=False,
        retry_control_exposed=False,
        action_control_exposed=False,
        provider_health_verified=False,
        model_availability_verified=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
        runtime_health_mutated=False,
        maintenance_health_mutated=False,
        fake_current_projection_created=False,
        fake_health_created=False,
        fake_success_created=False,
        fake_verification_created=False,
        live_probe_performed=False,
        real_endpoint_probed=False,
        socket_opened=False,
        http_request_performed=False,
        model_call_performed=False,
        generation_performed=False,
        embedding_generated=False,
        reranking_performed=False,
        multimodal_inference_performed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.frontend_authority is False
    assert decision.api_authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PROVIDER_PROBE_SURFACE_DISPLAY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_display is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.retry_authorized is False
    assert decision.retry_control_exposed is False
    assert decision.action_control_exposed is False
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
    assert decision.runtime_health_mutated is False
    assert decision.maintenance_health_mutated is False
    assert decision.fake_current_projection_created is False
    assert decision.fake_health_created is False
    assert decision.fake_success_created is False
    assert decision.fake_verification_created is False
    assert decision.live_probe_performed is False
    assert decision.real_endpoint_probed is False
    assert decision.socket_opened is False
    assert decision.http_request_performed is False
    assert decision.model_call_performed is False
    assert decision.generation_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_inference_performed is False
    assert decision.data_sent_external is False
    assert decision.read_only_projection is True
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True


def _assert_blocked(decision: object, reason: str) -> None:
    assert reason in decision.failure_reasons
    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_no_projection_available_maps_to_neutral_no_data_display() -> None:
    decision = validate_provider_probe_surface_display_request(_request())

    assert decision.contract_version == PROVIDER_PROBE_SURFACE_DISPLAY_VERSION
    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert decision.display_severity_class == "neutral"
    assert decision.recommended_wording == "No current provider probe projection is available."
    assert decision.color_semantics == "neutral_not_failure"
    _assert_non_authority(decision)


def test_not_observed_maps_to_neutral_not_observed_display() -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(surface_display_state_class="not_observed")
    )

    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert decision.recommended_wording == "Provider probe has not been observed."
    assert decision.retry_guidance == "No retry is authorized by provider probe surface display."


@pytest.mark.parametrize(
    ("state", "expected_wording"),
    [
        ("metadata_candidate", "Metadata candidate only; not provider health proof."),
        (
            "model_list_candidate",
            "Model-list metadata candidate only; not model availability proof.",
        ),
        ("empty_model_list_candidate", "Empty model-list candidate; not runtime failure."),
    ],
)
def test_metadata_states_map_to_informational_candidate_not_proof(
    state: str,
    expected_wording: str,
) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class="informational_candidate",
            display_severity_class="info",
        )
    )

    assert decision.display_readiness_status == "display_ready_informational_candidate"
    assert decision.recommended_wording == expected_wording
    assert decision.color_semantics == "info_not_verified_success"
    assert decision.provider_health_verified is False
    assert decision.model_availability_verified is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("state", "expected_wording"),
    [
        (
            "unreachable_negative_candidate",
            "Provider endpoint was unreachable during the observed probe; this is a negative candidate, not a runtime failure.",
        ),
        (
            "timeout_negative_candidate",
            "timeout_negative_candidate observed as a negative candidate; not a runtime failure.",
        ),
        (
            "connection_refused_negative_candidate",
            "connection_refused_negative_candidate observed as a negative candidate; not a runtime failure.",
        ),
        (
            "invalid_response_negative_candidate",
            "invalid_response_negative_candidate observed as a negative candidate; not a runtime failure.",
        ),
    ],
)
def test_retryable_negative_states_preserve_operator_approval_without_retry(
    state: str,
    expected_wording: str,
) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class="retry_requires_operator_approval",
            display_severity_class="warning",
        )
    )

    assert decision.display_readiness_status == "display_ready_negative_candidate"
    assert decision.recommended_wording == expected_wording
    assert decision.retry_guidance == "Retry requires explicit operator approval."
    assert "operator_approval_required_before_retry" in decision.required_operator_actions
    assert decision.retry_authorized is False
    assert decision.runtime_health_mutated is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    "state",
    [
        "unauthorized_negative_candidate",
        "unsupported_endpoint_negative_candidate",
        "cancelled_negative_candidate",
    ],
)
def test_non_retry_negative_states_remain_distinct_warning_candidates(state: str) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class="warning_negative_candidate",
            display_severity_class="attention",
        )
    )

    assert decision.display_readiness_status == "display_ready_negative_candidate"
    assert decision.retry_guidance == "No retry is authorized by provider probe surface display."
    assert "operator_review_recommended" in decision.required_operator_actions
    assert decision.provider_health_verified is False


def test_blocked_and_future_gated_display_states_remain_non_executable() -> None:
    blocked = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class="blocked_by_policy",
            ui_meaning_class="blocked",
            display_severity_class="blocked",
        )
    )
    future = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class="future_gated",
            ui_meaning_class="future_gated",
            display_severity_class="future",
        )
    )

    assert blocked.display_readiness_status == "display_ready_blocked_by_policy"
    assert future.display_readiness_status == "display_ready_future_gated"
    assert blocked.retry_authorized is False
    assert future.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("surface_display_source_class", "missing_surface_display_source_class"),
        ("surface_display_state_class", "missing_surface_display_state_class"),
        ("ui_meaning_class", "missing_ui_meaning_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_provider_probe_surface_display_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(source_refs=[], provenance=[])
    )

    _assert_blocked(decision, "missing_source_refs_or_provenance")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("surface_display_source_class", "unsupported", "unsupported_surface_display_source_class"),
        ("surface_display_state_class", "unsupported", "unsupported_surface_display_state_class"),
        ("ui_meaning_class", "unsupported", "unsupported_ui_meaning_class"),
        ("display_severity_class", "critical", "unsupported_display_severity_class"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_provider_probe_surface_display_request(_request(**{field: value}))

    _assert_blocked(decision, reason)


def test_unknown_taxonomy_values_block() -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_source_class="unknown",
            surface_display_state_class="unknown",
            ui_meaning_class="unknown",
        )
    )

    assert "unknown_surface_display_source_blocked" in decision.failure_reasons
    assert "unknown_surface_display_state_blocked" in decision.failure_reasons
    assert "unknown_ui_meaning_blocked" in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("state", "meaning", "reason"),
    [
        ("no_projection_available", "warning_negative_candidate", "no_data_state_requires_neutral_meaning"),
        ("metadata_candidate", "retry_requires_operator_approval", "metadata_state_requires_informational_meaning"),
        ("unreachable_negative_candidate", "informational_candidate", "negative_state_requires_warning_or_review_meaning"),
        ("timeout_negative_candidate", "operator_review_recommended", "retryable_state_requires_operator_approval_meaning"),
        ("blocked_by_policy", "informational_candidate", "blocked_policy_state_requires_blocked_meaning"),
        ("future_gated", "informational_candidate", "future_gated_state_requires_future_meaning"),
    ],
)
def test_state_meaning_mismatches_block_truthfulness(
    state: str,
    meaning: str,
    reason: str,
) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class=meaning,
            display_severity_class="neutral",
        )
    )

    _assert_blocked(decision, reason)


def test_display_severity_cannot_be_treated_as_runtime_health() -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class="unreachable_negative_candidate",
            ui_meaning_class="retry_requires_operator_approval",
            display_severity_class="blocked",
        )
    )

    _assert_blocked(decision, "negative_state_severity_must_not_be_runtime_failure")


@pytest.mark.parametrize(
    "forbidden_meaning",
    [
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
    ],
)
def test_forbidden_ui_meanings_are_rejected(forbidden_meaning: str) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(ui_meaning_class=forbidden_meaning)
    )

    _assert_blocked(decision, "forbidden_ui_meaning_denied")


@pytest.mark.parametrize(
    ("wording", "reason"),
    [
        ("Runtime failure detected.", "display_wording_runtime_failure_claim_denied"),
        ("Provider health verified.", "display_wording_provider_health_claim_denied"),
        ("Model available.", "display_wording_model_availability_claim_denied"),
        ("Evidence available.", "display_wording_evidence_claim_denied"),
        ("Verifier success.", "display_wording_verifier_claim_denied"),
        ("Retry authorized.", "display_wording_retry_authorization_denied"),
        ("Execution ready.", "display_wording_execution_ready_claim_denied"),
        ("Auto Mode selected.", "display_wording_auto_mode_claim_denied"),
    ],
)
def test_display_wording_cannot_overclaim_truth_or_authority(
    wording: str,
    reason: str,
) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(display_wording_candidate=wording)
    )

    _assert_blocked(decision, reason)


def test_safe_api_surface_response_can_be_mapped_without_frontend_authority() -> None:
    response = build_local_provider_probe_projection_api_response()
    decision = validate_provider_probe_surface_display_request(
        {
            "request_id": "provider-probe-surface-display:api-response",
            "surface_display_source_class": "maintenance_probe_projection_api",
            "projection_result_class": response["projection_result_class"],
            "ui_meaning_class": "neutral_no_data",
            "namespace": "provider_probe_surface_display",
            "source_refs": [{"ref_id": "api:/maintenance/local-provider/probe-projection"}],
            "provenance": response["provenance"],
            "display_severity_class": "neutral",
        },
        local_provider_probe_api_surface_decision=response,
    )

    assert decision.surface_display_state_class == "no_projection_available"
    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert [ref.label for ref in decision.related_references] == ["local_provider_probe_api_surface"]
    _assert_non_authority(decision)


def test_safe_maintenance_and_probe_projection_decisions_can_be_referenced() -> None:
    probe_decision = validate_local_provider_probe_projection_request(
        {
            "request_id": "probe-projection:1",
            "projection_source_class": "manual_smoke_result",
            "probe_result_class": "unreachable_negative_candidate",
            "maintenance_surface_status_class": "provider_probe_unreachable_candidate",
            "truth_label_class": "retry_requires_operator_approval",
            "display_severity_class": "warning",
            "freshness_class": "current_manual_smoke",
            "namespace": "local_provider_probe_projection",
            "source_refs": [{"ref_id": "manual-smoke"}],
        }
    )
    maintenance_decision = validate_local_provider_probe_maintenance_projection_request(
        {
            "request_id": "maintenance-projection:1",
            "projection_api_source_class": "local_provider_probe_projection",
            "api_exposure_readiness_class": "requires_operator_review_for_retry",
            "maintenance_category_class": "local_provider_retry_guidance",
            "consumer_surface_class": "maintenance_scan_future",
            "display_contract_class": "retry_requires_operator_approval_notice",
            "namespace": "local_provider_probe_maintenance_projection",
            "source_refs": [{"ref_id": "manual-smoke"}],
            "local_provider_probe_projection_ref": {
                "probe_result_class": "unreachable_negative_candidate",
            },
            "probe_result_class": "unreachable_negative_candidate",
            "display_severity_class": "warning",
        },
        local_provider_probe_projection_decision=probe_decision,
    )

    decision = validate_provider_probe_surface_display_request(
        _request(
            surface_display_state_class="unreachable_negative_candidate",
            ui_meaning_class="retry_requires_operator_approval",
            display_severity_class="warning",
        ),
        local_provider_probe_maintenance_projection_decision=maintenance_decision,
        local_provider_probe_projection_decision=probe_decision,
    )

    assert decision.display_readiness_status == "display_ready_negative_candidate"
    assert [ref.label for ref in decision.related_references] == [
        "local_provider_probe_maintenance_projection",
        "local_provider_probe_projection",
    ]
    assert all(ref.reference_only for ref in decision.related_references)


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("local_provider_probe_api_surface_decision", {"provider_health_verified": True}),
        ("local_provider_probe_maintenance_projection_decision", {"retry_authorized": True}),
        ("local_provider_probe_projection_decision", {"model_availability_verified": True}),
        ("local_provider_probe_runner_decision", {"live_probe_performed": True}),
        ("local_provider_health_decision", {"provider_health_verified": True}),
        ("model_auto_mode_decision", {"auto_mode_selected": True}),
        ("local_model_inventory_decision", {"model_availability_verified": True}),
        ("local_model_context_profile_decision", {"benchmark_claim_verified": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("context_policy_decision", {"context_payload_sent": True}),
        ("identity_scope_decision", {"authority": True}),
        ("memory_governance_decision", {"memory_payload_sent": True}),
        ("capability_lease_decision", {"lease_grant": True}),
        ("mission_control_decision", {"frontend_authority": True}),
        ("passive_observe_decision", {"runtime_state_mutated": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(
    related_name: str,
    kwargs: dict[str, object],
) -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("api_authority", "api_authority_not_allowed"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("retry_authorized", "retry_authorization_denied"),
        ("retry_control_exposed", "retry_control_exposure_denied"),
        ("action_control_exposed", "action_control_exposure_denied"),
        ("provider_health_verified", "provider_health_verification_denied"),
        ("model_availability_verified", "model_availability_verification_denied"),
        ("model_identity_verified", "model_identity_verification_denied"),
        ("benchmark_claim_verified", "benchmark_verification_denied"),
        ("runtime_health_mutated", "runtime_health_mutation_denied"),
        ("maintenance_health_mutated", "maintenance_health_mutation_denied"),
        ("fake_current_projection_created", "fake_current_projection_denied"),
        ("fake_health_created", "fake_health_denied"),
        ("fake_success_created", "fake_success_denied"),
        ("fake_verification_created", "fake_verification_denied"),
        ("live_probe_performed", "live_probe_execution_denied"),
        ("real_endpoint_probed", "real_endpoint_probe_denied"),
        ("socket_opened", "socket_open_denied"),
        ("http_request_performed", "http_request_denied"),
        ("model_call_performed", "model_call_denied"),
        ("generation_performed", "generation_denied"),
        ("embedding_generated", "embedding_generation_denied"),
        ("reranking_performed", "reranking_denied"),
        ("multimodal_inference_performed", "multimodal_inference_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("evidence_provided_by_display", "display_cannot_provide_evidence"),
        ("verifier_success", "display_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_execution_authority_probe_health_retry_and_proof_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_provider_probe_surface_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_provider_probe_surface_display_request(
        request,
        local_provider_health_decision=related,
    )

    assert request == request_before
    assert related.__dict__ == related_before
    assert decision.display_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.display_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_provider_probe_surface_display_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.display_input is None


def test_output_never_sets_probe_model_health_or_retry_flags_even_when_blocked() -> None:
    decision = validate_provider_probe_surface_display_request(
        _request(
            model_call_performed=True,
            http_request_performed=True,
            provider_health_verified=True,
            retry_authorized=True,
        )
    )

    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)
