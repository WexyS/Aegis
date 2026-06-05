from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.action_attribution import (
    ACTION_ATTRIBUTION_EXECUTION_PERMISSION,
    ACTION_ATTRIBUTION_VERSION,
    validate_action_attribution_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "attribution:aegis:1",
        "attribution_subject": "command_effect",
        "attribution_operation": "propose_causal_link",
        "namespace": "action_attribution",
        "source_class": "command_lifecycle_projection",
        "confidence_class": "direct_source_ref",
        "causality_class": "direct_causality_candidate",
        "completeness_class": "complete_for_supplied_projection",
        "source_refs": [{"ref_id": "command:cmd-1", "ref_type": "synthetic_projection"}],
        "provenance": [{"ref_id": "caller:test", "ref_type": "synthetic_fixture"}],
        "limitations": ["candidate attribution only"],
        "unknowns": [],
        "direct_source_refs_present": True,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": ACTION_ATTRIBUTION_EXECUTION_PERMISSION,
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
        evidence_provided_by_attribution=False,
        verifier_success=False,
        live_observation_performed=False,
        file_scan_performed=False,
        file_read_performed=False,
        process_scan_performed=False,
        raw_journal_read=False,
        raw_evidence_read=False,
        database_queried=False,
        model_call_performed=False,
        tool_call_performed=False,
        mcp_call_performed=False,
        web_query_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        attribution_record_created=False,
        timeline_created=False,
        report_generated=False,
        runtime_state_mutated=False,
        journal_mutated=False,
        evidence_mutated=False,
        replay_mutated=False,
        generated_artifact_created=False,
        data_sent_external=False,
        causality_claim_final=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == ACTION_ATTRIBUTION_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_attribution is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.live_observation_performed is False
    assert decision.file_scan_performed is False
    assert decision.file_read_performed is False
    assert decision.process_scan_performed is False
    assert decision.raw_journal_read is False
    assert decision.raw_evidence_read is False
    assert decision.database_queried is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.web_query_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.attribution_record_created is False
    assert decision.timeline_created is False
    assert decision.report_generated is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.generated_artifact_created is False
    assert decision.data_sent_external is False
    assert decision.causality_claim_final is False
    assert decision.requires_backend_validation is True
    assert decision.read_only_projection is True


def test_valid_command_effect_attribution_with_direct_refs_is_read_only_candidate() -> None:
    decision = validate_action_attribution_request(_request())

    assert decision.contract_version == ACTION_ATTRIBUTION_VERSION
    assert decision.attribution_status == "attribution_candidate_ready"
    assert decision.attribution_truth_status == "direct_source_ref_candidate"
    assert decision.direct_source_ref_preserved is True
    _assert_non_authority(decision)


def test_approval_effect_attribution_remains_candidate_not_approval_grant() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="approval_effect",
            attribution_operation="propose_approval_link",
            source_class="approval_projection",
        )
    )

    assert decision.attribution_status == "attribution_candidate_ready"
    assert decision.approval_grant is False
    _assert_non_authority(decision)


def test_evidence_state_change_uses_refs_only_not_raw_evidence_or_verifier_success() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="evidence_state_change",
            attribution_operation="propose_evidence_ref_link",
            source_class="evidence_ref_projection",
        )
    )

    assert decision.evidence_provided_by_attribution is False
    assert decision.raw_evidence_read is False
    assert decision.verifier_success is False
    _assert_non_authority(decision)


def test_passive_observe_state_change_remains_projection_only() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="passive_observe_state_change",
            attribution_operation="propose_source_link",
            source_class="passive_observe_projection",
        ),
        passive_observe_decision=_related(display_state="read_only_projection"),
    )

    assert decision.related_references[0].reference_only is True
    assert decision.live_observation_performed is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("attribution_subject", "missing_attribution_subject"),
        ("attribution_operation", "missing_attribution_operation"),
        ("namespace", "missing_namespace"),
        ("source_class", "missing_source_class"),
        ("confidence_class", "missing_confidence_class"),
        ("causality_class", "missing_causality_class"),
        ("completeness_class", "missing_completeness_class"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_action_attribution_request(_request(**{field: None}))

    assert decision.attribution_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_action_attribution_request(_request(source_refs=[], provenance=[]))

    assert decision.attribution_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("attribution_subject", "not_a_subject", "unsupported_attribution_subject"),
        ("attribution_operation", "execute_attribution", "unsupported_attribution_operation"),
        ("source_class", "live_file_scan", "unsupported_source_class"),
        ("confidence_class", "certain", "unsupported_confidence_class"),
        ("causality_class", "final", "unsupported_causality_class"),
        ("completeness_class", "full_history", "unsupported_completeness_class"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_action_attribution_request(_request(**{field: value}))

    assert decision.attribution_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons


def test_direct_causality_requires_direct_source_refs() -> None:
    decision = validate_action_attribution_request(
        _request(confidence_class="strong_candidate", direct_source_refs_present=False)
    )

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "direct_causality_requires_direct_source_ref" in decision.failure_reasons
    assert decision.causality_claim_final is False


@pytest.mark.parametrize(
    ("confidence", "causality", "truth_field"),
    [
        ("weak_candidate", "temporal_correlation_only", "temporal_correlation_preserved"),
        ("inferred_low_trust", "indirect_causality_candidate", "inferred_low_trust_preserved"),
        ("conflicting", "conflicting_causality", "conflicting_attribution_preserved"),
        ("insufficient_evidence", "impossible_to_determine", "insufficient_evidence_preserved"),
        ("unknown", "unknown", "unknown_attribution_preserved"),
    ],
)
def test_non_direct_attribution_states_are_preserved(confidence: str, causality: str, truth_field: str) -> None:
    decision = validate_action_attribution_request(
        _request(
            confidence_class=confidence,
            causality_class=causality,
            completeness_class="partial",
            direct_source_refs_present=False,
        )
    )

    assert getattr(decision, truth_field) is True
    assert decision.human_review_required is True
    assert decision.causality_claim_final is False
    _assert_non_authority(decision)


def test_external_or_unknown_attribution_is_preserved() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="external_change_future",
            attribution_operation="propose_unknown_external_change",
            source_class="future_integrity_monitor_projection",
            confidence_class="unknown",
            causality_class="external_or_unknown",
            completeness_class="unknown",
            direct_source_refs_present=False,
        )
    )

    assert decision.attribution_status == "future_gated"
    assert decision.external_or_unknown_preserved is True
    assert decision.future_gated_preserved is True
    _assert_non_authority(decision)


def test_bounded_projection_cannot_claim_complete_attribution() -> None:
    decision = validate_action_attribution_request(
        _request(completeness_class="bounded_projection_only", full_attribution_claimed=True)
    )

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "full_attribution_requires_complete_supplied_projection" in decision.failure_reasons
    assert decision.bounded_projection_preserved is True


def test_stale_projection_cannot_claim_current_causality() -> None:
    decision = validate_action_attribution_request(_request(completeness_class="stale", current_claim=True))

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "stale_projection_cannot_claim_current_causality" in decision.failure_reasons
    assert decision.stale_projection_preserved is True


@pytest.mark.parametrize(
    "source_class",
    ["frontend_supplied_low_trust", "model_output_low_trust", "mcp_output_low_trust", "tool_output_low_trust"],
)
def test_low_trust_sources_cannot_be_authoritative_attribution(source_class: str) -> None:
    decision = validate_action_attribution_request(_request(source_class=source_class))

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "low_trust_source_cannot_claim_direct_source_ref" in decision.failure_reasons
    assert decision.lower_trust_source is True
    assert decision.causality_claim_final is False
    _assert_non_authority(decision)


def test_model_provider_readiness_is_not_proof_of_change() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="provider_state_change",
            source_class="caller_supplied_metadata",
            confidence_class="weak_candidate",
            causality_class="temporal_correlation_only",
            completeness_class="bounded_projection_only",
            direct_source_refs_present=False,
        ),
        local_provider_health_decision=_related(readiness_status="metadata_ready"),
    )

    assert decision.attribution_truth_status == "temporal_correlation_only"
    assert decision.verifier_success is False
    assert decision.model_call_performed is False


def test_capability_lease_candidate_is_not_proof_of_permission_or_use() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="capability_lease_candidate_change",
            source_class="caller_supplied_metadata",
            confidence_class="strong_candidate",
            causality_class="indirect_causality_candidate",
            completeness_class="bounded_projection_only",
            direct_source_refs_present=False,
        ),
        capability_lease_decision=_related(lifecycle_state="proposed"),
    )

    assert decision.lease_grant is False
    assert decision.runtime_dispatch_allowed is False


def test_audit_query_projection_is_not_full_history_unless_complete_for_supplied_projection() -> None:
    decision = validate_action_attribution_request(
        _request(
            source_class="audit_query_projection",
            completeness_class="bounded_projection_only",
            full_attribution_claimed=True,
        ),
        audit_query_layer_decision=_related(query_status="query_plan_ready_bounded_projection"),
    )

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "full_attribution_requires_complete_supplied_projection" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_observation_performed", "live_observation_denied"),
        ("file_scan_performed", "file_scan_denied"),
        ("file_read_performed", "file_read_denied"),
        ("process_scan_performed", "process_scan_denied"),
        ("raw_journal_read", "raw_journal_read_denied"),
        ("raw_evidence_read", "raw_evidence_read_denied"),
        ("database_queried", "database_query_denied"),
        ("model_call_performed", "model_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("attribution_record_created", "attribution_record_creation_denied"),
        ("timeline_created", "timeline_creation_denied"),
        ("report_generated", "report_generation_denied"),
        ("runtime_state_mutated", "runtime_state_mutation_denied"),
        ("journal_mutated", "journal_mutation_denied"),
        ("evidence_mutated", "evidence_mutation_denied"),
        ("replay_mutated", "replay_mutation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_observation_scans_reads_calls_records_reports_and_mutations_are_rejected(field: str, reason: str) -> None:
    decision = validate_action_attribution_request(_request(**{field: True}))

    assert decision.attribution_status == "blocked_by_execution_claim"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_attribution", "attribution_cannot_provide_evidence"),
        ("verifier_success", "attribution_cannot_mark_verifier_success"),
        ("success", "success_claim_denied"),
        ("proof", "proof_claim_denied"),
        ("certification_claim", "certification_claim_denied"),
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_authority_grants_evidence_verifier_truth_and_proof_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_action_attribution_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_final_causality_claim_is_rejected_even_with_direct_candidate_metadata() -> None:
    decision = validate_action_attribution_request(_request(causality_claim_final=True))

    assert decision.attribution_status == "blocked_by_truthfulness_claim"
    assert "final_causality_claim_denied" in decision.failure_reasons
    assert decision.causality_claim_final is False


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_action_attribution_request(_request(execution_permission="granted_by_attribution"))

    assert decision.attribution_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("audit_query_layer_decision", _related(runtime_dispatch_allowed=True)),
        ("passive_observe_decision", _related(verifier_success=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(capability_grant=True)),
        ("context_policy_decision", _related(context_retrieval_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("local_provider_health_decision", _related(model_call_performed=True)),
        ("local_provider_probe_design_decision", _related(live_observation_performed=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("local_model_inventory_decision", _related(model_call_performed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("repo_audit_decision", _related(file_read_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_action_attribution_request(_request(), **{related_name: related_value})

    assert decision.attribution_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_action_attribution_request(
        _request(
            attribution_subject="maintenance_finding_change",
            source_class="maintenance_projection",
            confidence_class="strong_candidate",
            causality_class="indirect_causality_candidate",
            completeness_class="bounded_projection_only",
            direct_source_refs_present=False,
        ),
        audit_query_layer_decision=_related(query_status="query_plan_ready_bounded_projection"),
        passive_observe_decision=_related(display_state="read_only_projection"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        memory_governance_decision=_related(governance_status="governance_ready"),
        context_policy_decision=_related(policy_status="proposal_ready"),
        repo_audit_decision=_related(readiness_status="readiness_ready"),
    )

    assert len(decision.related_references) == 7
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.file_read_performed is False


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_action_attribution_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.attribution_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection_and_never_final_causality() -> None:
    decision = validate_action_attribution_request(_request())

    assert decision.read_only_projection is True
    assert decision.causality_claim_final is False
    _assert_non_authority(decision)
