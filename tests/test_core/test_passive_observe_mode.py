from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.passive_observe_mode import (
    PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION,
    PASSIVE_OBSERVE_MODE_VERSION,
    validate_passive_observe_mode_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "observe:aegis:1",
        "observe_scope": "runtime_status_summary",
        "namespace": "passive_observe_mode",
        "supplied_state_classification": "available_from_backend_state",
        "risk_level": "info",
        "state_source": "backend_state",
        "source_refs": [{"ref_id": "backend:runtime-snapshot", "ref_type": "synthetic_fixture"}],
        "provenance": [{"ref_id": "caller:supplied", "ref_type": "test_fixture"}],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        readiness_status="metadata_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_observe_mode=False,
        verifier_success=False,
        tool_call_performed=False,
        model_call_performed=False,
        provider_probe_performed=False,
        endpoint_probed=False,
        repo_scan_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        web_query_performed=False,
        mutation_performed=False,
        fake_health_created=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _validate(request: dict[str, object], **related: object):
    return validate_passive_observe_mode_request(request, **related)


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == PASSIVE_OBSERVE_MODE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_observe_mode is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.tool_call_performed is False
    assert decision.model_call_performed is False
    assert decision.provider_probe_performed is False
    assert decision.endpoint_probed is False
    assert decision.repo_scan_performed is False
    assert decision.file_watch_started is False
    assert decision.process_watch_started is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.web_query_performed is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.data_sent_external is False
    assert decision.generated_artifact_created is False
    assert decision.fake_health_created is False
    assert decision.fake_evidence_created is False
    assert decision.fake_verifier_success_created is False
    assert decision.read_only_projection is True


def test_valid_runtime_status_summary_from_backend_state_is_read_only_projection() -> None:
    decision = _validate(_request())

    assert decision.contract_version == PASSIVE_OBSERVE_MODE_VERSION
    assert decision.display_state == "available_from_backend_state"
    assert decision.source_truth_status == "backend_state_reference"
    assert decision.read_only_projection is True
    _assert_non_authority(decision)


def test_maintenance_projection_preserves_current_blocker_vs_historical_debt() -> None:
    current = _validate(
        _request(
            observe_scope="maintenance_projection_summary",
            supplied_state_classification="current_blocker",
            current_blocker=True,
            risk_level=None,
        )
    )
    historical = _validate(
        _request(
            observe_scope="maintenance_projection_summary",
            supplied_state_classification="historical_debt",
            historical_debt=True,
            risk_level=None,
        )
    )

    assert current.display_state == "current_blocker"
    assert current.current_state_preserved is True
    assert current.risk_level == "high"
    assert historical.display_state == "historical_debt"
    assert historical.historical_debt_preserved is True
    assert historical.risk_level == "medium"


def test_model_inventory_summary_is_metadata_not_usable_models() -> None:
    decision = _validate(
        _request(
            observe_scope="model_inventory_summary",
            supplied_state_classification="read_only_projection",
        ),
        local_model_inventory_decision=_related(inventory_status="inventory_ready"),
    )

    assert decision.display_state == "read_only_projection"
    assert decision.related_observations[0].label == "local_model_inventory"
    assert decision.related_observations[0].implementation_claim is False
    assert decision.model_call_performed is False


def test_provider_readiness_summary_is_not_health_proof() -> None:
    decision = _validate(
        _request(
            observe_scope="provider_readiness_summary",
            supplied_state_classification="future_gated",
            future_gated=True,
            local_provider_health_decision=_related(readiness_status="future_gated"),
        )
    )

    assert decision.display_state == "future_gated"
    assert decision.future_gated_preserved is True
    assert decision.endpoint_probed is False
    assert decision.fake_health_created is False


def test_lease_readiness_summary_is_candidate_only() -> None:
    decision = _validate(
        _request(
            observe_scope="lease_readiness_summary",
            supplied_state_classification="read_only_projection",
            capability_lease_decision=_related(lifecycle_state="ready_for_operator_review"),
        )
    )

    assert decision.display_state == "read_only_projection"
    assert decision.lease_grant is False
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("observe_scope", "missing_observe_scope"),
        ("namespace", "missing_namespace"),
        ("supplied_state_classification", "missing_supplied_state_classification"),
    ],
)
def test_missing_required_fields_block_display(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: None}))

    assert decision.display_state == "unavailable"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks_displayed_status() -> None:
    decision = _validate(_request(source_refs=[], provenance=[]))

    assert decision.display_state == "unavailable"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("classification", "flag", "expected"),
    [
        ("unknown", "unknown_state", "unknown"),
        ("unavailable", "unavailable", "unavailable"),
        ("stale", "stale", "stale"),
        ("historical_debt", "historical_debt", "historical_debt"),
        ("current_blocker", "current_blocker", "current_blocker"),
        ("future_gated", "future_gated", "future_gated"),
        ("not_implemented", "not_implemented", "not_implemented"),
        ("not_configured", "not_configured", "not_configured"),
    ],
)
def test_truthfulness_states_are_preserved(classification: str, flag: str, expected: str) -> None:
    decision = _validate(_request(supplied_state_classification=classification, **{flag: True}))

    assert decision.display_state == expected
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("unknown_state", "unknown_state_cannot_be_available"),
        ("historical_debt", "historical_debt_cannot_be_current_success"),
        ("future_gated", "future_gated_cannot_be_implemented"),
        ("stale", "stale_state_cannot_be_live_truth"),
    ],
)
def test_truthfulness_flags_cannot_be_marked_available_backend_success(flag: str, reason: str) -> None:
    decision = _validate(_request(supplied_state_classification="available_from_backend_state", **{flag: True}))

    assert reason in decision.failure_reasons
    assert decision.display_state in {"blocked_by_policy", "unknown", "historical_debt", "future_gated", "stale"}


def test_frontend_supplied_state_cannot_become_backend_truth() -> None:
    decision = _validate(_request(state_source="frontend_supplied"))

    assert decision.lower_trust_source is True
    assert decision.source_truth_status == "lower_trust_reference_only"
    assert "frontend_state_cannot_claim_backend_truth" in decision.failure_reasons
    assert decision.frontend_authority is False


def test_config_metadata_does_not_become_live_runtime_truth() -> None:
    decision = _validate(
        _request(
            observe_scope="provider_readiness_summary",
            supplied_state_classification="stale",
            stale=True,
            state_source="metadata_only",
        )
    )

    assert decision.display_state == "stale"
    assert decision.stale_state_preserved is True
    assert decision.source_truth_status == "caller_supplied_projection"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("tool_call_performed", "tool_call_request_denied"),
        ("model_call_performed", "model_call_request_denied"),
        ("provider_probe_performed", "provider_probe_request_denied"),
        ("endpoint_probed", "endpoint_probe_request_denied"),
        ("repo_scan_performed", "repo_scan_request_denied"),
        ("file_watch_started", "file_watch_request_denied"),
        ("process_watch_started", "process_watch_request_denied"),
        ("memory_retrieval_performed", "memory_retrieval_request_denied"),
        ("context_retrieval_performed", "context_retrieval_request_denied"),
        ("web_query_performed", "web_query_request_denied"),
        ("runtime_state_mutated", "runtime_state_mutation_denied"),
        ("journal_mutated", "journal_mutation_denied"),
        ("evidence_mutated", "evidence_mutation_denied"),
        ("replay_mutated", "replay_mutation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
    ],
)
def test_non_execution_and_no_mutation_flags_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert decision.display_state == "blocked_by_policy"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("fake_health_created", "fake_health_denied"),
        ("fake_evidence_created", "fake_evidence_denied"),
        ("fake_verifier_success_created", "fake_verifier_success_denied"),
        ("evidence_provided_by_observe_mode", "observe_mode_cannot_provide_evidence"),
        ("verifier_success", "observe_mode_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("unknown_converted_to_healthy", "unknown_to_healthy_denied"),
        ("historical_debt_converted_to_success", "historical_debt_success_denied"),
        ("readiness_metadata_is_implementation", "readiness_metadata_implementation_denied"),
    ],
)
def test_authority_grant_fake_state_evidence_and_verifier_claims_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = _validate(_request(execution_permission="granted_by_observe_mode"))

    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("identity_scope_decision", _related(runtime_dispatch_allowed=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(verifier_success=True)),
        ("context_policy_decision", _related(context_retrieval_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("local_provider_health_decision", _related(endpoint_probed=True)),
        ("local_provider_probe_design_decision", _related(provider_probe_performed=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("local_model_inventory_decision", _related(fake_health_created=True)),
        ("repo_audit_decision", _related(repo_scan_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = _validate(_request(), **{related_name: related_value})

    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only_readiness_observations() -> None:
    decision = _validate(
        _request(observe_scope="product_onboarding_summary", supplied_state_classification="read_only_projection"),
        model_auto_mode_decision=_related(selection_mode="local_model_candidate"),
        local_provider_health_decision=_related(readiness_status="metadata_ready"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        capability_lease_decision=_related(lifecycle_state="ready_for_operator_review"),
        memory_governance_decision=_related(governance_status="governance_ready"),
        context_policy_decision=_related(policy_status="proposal_ready"),
    )

    assert len(decision.related_observations) == 6
    for observation in decision.related_observations:
        assert observation.reference_only is True
        assert observation.authority is False
        assert observation.implementation_claim is False


def test_model_auto_mode_provider_probe_and_lease_related_decisions_remain_candidates() -> None:
    decision = _validate(
        _request(observe_scope="product_onboarding_summary", supplied_state_classification="read_only_projection"),
        model_auto_mode_decision=_related(selection_mode="local_model_candidate"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        capability_lease_decision=_related(lifecycle_state="ready_for_operator_review"),
    )

    states = {observation.label: observation.display_state for observation in decision.related_observations}
    assert states["model_auto_mode"] == "read_only_projection"
    assert states["local_provider_probe_design"] == "future_gated"
    assert states["capability_lease"] == "read_only_projection"
    assert decision.model_call_performed is False
    assert decision.provider_probe_performed is False
    assert decision.lease_grant is False


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _validate(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.observe_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection_and_never_fake_success() -> None:
    decision = _validate(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
