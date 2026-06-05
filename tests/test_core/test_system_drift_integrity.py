from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.system_drift_integrity import (
    SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION,
    SYSTEM_DRIFT_INTEGRITY_VERSION,
    validate_system_drift_integrity_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "drift:aegis:1",
        "drift_subject": "config_drift",
        "integrity_subject": "critical_config_integrity",
        "drift_operation": "compare_supplied_baseline_metadata",
        "namespace": "system_drift_integrity",
        "baseline_source_class": "caller_supplied_baseline",
        "current_source_class": "caller_supplied_current_metadata",
        "drift_status": "drift_candidate",
        "integrity_status": "integrity_not_claimed",
        "attribution_relationship": "not_attributed",
        "severity_class": "medium",
        "completeness_class": "complete_for_supplied_metadata",
        "source_refs": [{"ref_id": "baseline:config", "ref_type": "synthetic_projection"}],
        "provenance": [{"ref_id": "caller:test", "ref_type": "synthetic_fixture"}],
        "limitations": ["metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION,
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
        evidence_provided_by_drift_monitor=False,
        verifier_success=False,
        live_monitoring_started=False,
        file_watch_started=False,
        process_watch_started=False,
        file_scan_performed=False,
        process_scan_performed=False,
        file_read_performed=False,
        hash_computation_performed=False,
        raw_journal_read=False,
        raw_evidence_read=False,
        database_queried=False,
        model_call_performed=False,
        tool_call_performed=False,
        mcp_call_performed=False,
        web_query_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        drift_record_created=False,
        integrity_record_created=False,
        report_generated=False,
        runtime_state_mutated=False,
        journal_mutated=False,
        evidence_mutated=False,
        replay_mutated=False,
        generated_artifact_created=False,
        data_sent_external=False,
        drift_proof_claimed=False,
        integrity_proof_claimed=False,
        causality_claim_final=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_drift_monitor is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.live_monitoring_started is False
    assert decision.file_watch_started is False
    assert decision.process_watch_started is False
    assert decision.file_scan_performed is False
    assert decision.process_scan_performed is False
    assert decision.file_read_performed is False
    assert decision.hash_computation_performed is False
    assert decision.raw_journal_read is False
    assert decision.raw_evidence_read is False
    assert decision.database_queried is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.web_query_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.drift_record_created is False
    assert decision.integrity_record_created is False
    assert decision.report_generated is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.generated_artifact_created is False
    assert decision.data_sent_external is False
    assert decision.drift_proof_claimed is False
    assert decision.integrity_proof_claimed is False
    assert decision.causality_claim_final is False
    assert decision.requires_backend_validation is True
    assert decision.read_only_projection is True


def test_valid_config_drift_candidate_is_read_only_metadata_candidate() -> None:
    decision = validate_system_drift_integrity_request(_request())

    assert decision.contract_version == SYSTEM_DRIFT_INTEGRITY_VERSION
    assert decision.readiness_status == "drift_integrity_candidate_ready"
    assert decision.drift_truth_status == "candidate_only"
    assert decision.integrity_truth_status == "integrity_not_claimed"
    _assert_non_authority(decision)


def test_frontend_generated_drift_candidate_preserves_generated_drift_status() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_subject="frontend_generated_drift",
            integrity_subject="frontend_generated_artifact_integrity",
            drift_status="unexpected_change_candidate",
            integrity_status="integrity_warning_candidate",
            severity_class="low",
            completeness_class="bounded_metadata_only",
            human_review_required=True,
        )
    )

    assert decision.unexpected_change_preserved is True
    assert decision.human_review_required is True
    assert decision.generated_artifact_created is False
    _assert_non_authority(decision)


def test_dispatch_surface_drift_remains_candidate_not_policy_change() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_subject="dispatch_surface_drift",
            integrity_subject="dispatch_policy_integrity",
            drift_status="drift_candidate",
            integrity_status="integrity_warning_candidate",
            severity_class="high",
        )
    )

    assert decision.readiness_status == "drift_integrity_candidate_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.capability_grant is False


def test_resource_pressure_drift_preserves_warning_and_resource_debt() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_subject="resource_pressure_drift",
            integrity_subject=None,
            drift_status="unexpected_change_candidate",
            integrity_status="integrity_not_claimed",
            severity_class="high",
            resource_debt=True,
            completeness_class="bounded_metadata_only",
        )
    )

    assert decision.unexpected_change_preserved is True
    assert decision.resource_debt_preserved is True
    assert decision.human_review_required is True


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("drift_operation", "missing_drift_operation"),
        ("namespace", "missing_namespace"),
        ("baseline_source_class", "missing_baseline_source_class"),
        ("current_source_class", "missing_current_source_class"),
        ("drift_status", "missing_drift_status"),
        ("integrity_status", "missing_integrity_status"),
        ("attribution_relationship", "missing_attribution_relationship"),
        ("severity_class", "missing_severity_class"),
        ("completeness_class", "missing_completeness_class"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_system_drift_integrity_request(_request(**{field: None}))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_subject_blocks() -> None:
    decision = validate_system_drift_integrity_request(_request(drift_subject=None, integrity_subject=None))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert "missing_subject" in decision.failure_reasons


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_system_drift_integrity_request(_request(source_refs=[], provenance=[]))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("drift_subject", "not_a_drift", "unsupported_drift_subject"),
        ("integrity_subject", "not_integrity", "unsupported_integrity_subject"),
        ("drift_operation", "start_monitor", "unsupported_drift_operation"),
        ("baseline_source_class", "live_hash", "unsupported_baseline_source_class"),
        ("current_source_class", "live_process", "unsupported_current_source_class"),
        ("drift_status", "verified_drift", "unsupported_drift_status"),
        ("integrity_status", "verified_integrity", "unsupported_integrity_status"),
        ("attribution_relationship", "final", "unsupported_attribution_relationship"),
        ("severity_class", "severe", "unsupported_severity_class"),
        ("completeness_class", "full", "unsupported_completeness_class"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_system_drift_integrity_request(_request(**{field: value}))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize(
    ("drift_status", "preserved_field", "truth_status"),
    [
        ("missing_baseline", "missing_baseline_preserved", "missing_baseline"),
        ("stale_baseline", "stale_baseline_preserved", "stale_baseline"),
        ("missing_current_state", "missing_current_state_preserved", "missing_current_state"),
        ("insufficient_metadata", "insufficient_metadata_preserved", "insufficient_metadata"),
        ("external_or_unknown_change", "external_unknown_preserved", "external_or_unknown"),
        ("conflicting_change", "conflicting_change_preserved", "conflicting"),
    ],
)
def test_missing_stale_conflicting_and_external_states_are_preserved(
    drift_status: str,
    preserved_field: str,
    truth_status: str,
) -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_status=drift_status,
            completeness_class="partial",
            attribution_relationship="unknown_external" if drift_status == "external_or_unknown_change" else "not_attributed",
        )
    )

    assert getattr(decision, preserved_field) is True
    assert decision.drift_truth_status == truth_status
    assert decision.human_review_required is True
    _assert_non_authority(decision)


def test_expected_change_does_not_become_integrity_success() -> None:
    decision = validate_system_drift_integrity_request(
        _request(drift_status="expected_change_candidate", integrity_status="integrity_candidate")
    )

    assert decision.readiness_status == "blocked_by_truthfulness_claim"
    assert "expected_change_cannot_claim_integrity_success" in decision.failure_reasons
    assert decision.verifier_success is False


def test_unexpected_change_does_not_become_proof() -> None:
    decision = validate_system_drift_integrity_request(
        _request(drift_status="unexpected_change_candidate", integrity_status="integrity_candidate")
    )

    assert decision.readiness_status == "blocked_by_truthfulness_claim"
    assert "unexpected_change_cannot_claim_integrity_success" in decision.failure_reasons
    assert decision.integrity_proof_claimed is False


def test_temporal_correlation_cannot_become_expected_attributed_change() -> None:
    decision = validate_system_drift_integrity_request(
        _request(drift_status="expected_change_candidate", attribution_relationship="temporal_correlation_only")
    )

    assert decision.readiness_status == "blocked_by_truthfulness_claim"
    assert "temporal_correlation_cannot_be_expected_change" in decision.failure_reasons
    assert decision.causality_claim_final is False


def test_action_attribution_candidate_cannot_become_final_causality() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            baseline_source_class="action_attribution_projection_baseline",
            current_source_class="action_attribution_projection_current",
            causality_claim_final=True,
        ),
        action_attribution_decision=_related(attribution_status="attribution_candidate_ready"),
    )

    assert decision.readiness_status == "blocked_by_truthfulness_claim"
    assert "final_causality_claim_denied" in decision.failure_reasons
    assert decision.causality_claim_final is False


def test_bounded_metadata_cannot_claim_complete_drift_analysis() -> None:
    decision = validate_system_drift_integrity_request(
        _request(completeness_class="bounded_metadata_only", full_drift_analysis_claimed=True)
    )

    assert decision.readiness_status == "blocked_by_truthfulness_claim"
    assert "full_drift_analysis_requires_complete_supplied_metadata" in decision.failure_reasons
    assert decision.bounded_metadata_preserved is True


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_frontend_model_mcp_and_tool_output_cannot_be_authoritative(field: str, reason: str) -> None:
    decision = validate_system_drift_integrity_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_future_file_hash_and_process_snapshot_remain_future_gated() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_subject="file_hash_drift_future",
            integrity_subject="repo_source_integrity_future",
            baseline_source_class="future_file_hash_baseline",
            current_source_class="future_file_hash_current",
            drift_status="future_gated",
            integrity_status="future_gated",
        )
    )

    assert decision.readiness_status == "future_gated"
    assert decision.future_gated_preserved is True
    assert decision.hash_computation_performed is False
    assert decision.file_read_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_monitoring_started", "live_monitoring_denied"),
        ("file_watch_started", "file_watch_denied"),
        ("process_watch_started", "process_watch_denied"),
        ("file_scan_performed", "file_scan_denied"),
        ("process_scan_performed", "process_scan_denied"),
        ("file_read_performed", "file_read_denied"),
        ("hash_computation_performed", "hash_computation_denied"),
        ("raw_journal_read", "raw_journal_read_denied"),
        ("raw_evidence_read", "raw_evidence_read_denied"),
        ("database_queried", "database_query_denied"),
        ("model_call_performed", "model_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("drift_record_created", "drift_record_creation_denied"),
        ("integrity_record_created", "integrity_record_creation_denied"),
        ("report_generated", "report_generation_denied"),
        ("runtime_state_mutated", "runtime_state_mutation_denied"),
        ("journal_mutated", "journal_mutation_denied"),
        ("evidence_mutated", "evidence_mutation_denied"),
        ("replay_mutated", "replay_mutation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_monitoring_watchers_scans_hashes_calls_records_reports_and_mutations_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_system_drift_integrity_request(_request(**{field: True}))

    assert decision.readiness_status == "blocked_by_execution_claim"
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
        ("evidence_provided_by_drift_monitor", "drift_monitor_cannot_provide_evidence"),
        ("verifier_success", "drift_monitor_cannot_mark_verifier_success"),
        ("success", "success_claim_denied"),
        ("proof", "proof_claim_denied"),
        ("certification_claim", "certification_claim_denied"),
        ("drift_proof_claimed", "drift_proof_claim_denied"),
        ("integrity_proof_claimed", "integrity_proof_claim_denied"),
        ("causality_claim_final", "final_causality_claim_denied"),
    ],
)
def test_authority_grants_evidence_verifier_proof_and_final_causality_claims_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_system_drift_integrity_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_system_drift_integrity_request(_request(execution_permission="granted_by_drift_monitor"))

    assert decision.readiness_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("action_attribution_decision", _related(causality_claim_final=True)),
        ("audit_query_layer_decision", _related(runtime_dispatch_allowed=True)),
        ("passive_observe_decision", _related(verifier_success=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(capability_grant=True)),
        ("context_policy_decision", _related(context_retrieval_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("local_provider_health_decision", _related(model_call_performed=True)),
        ("local_provider_probe_design_decision", _related(live_monitoring_started=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("local_model_inventory_decision", _related(model_call_performed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("repo_audit_decision", _related(file_read_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_system_drift_integrity_request(_request(), **{related_name: related_value})

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_system_drift_integrity_request(
        _request(
            drift_subject="maintenance_projection_drift",
            baseline_source_class="maintenance_projection_baseline",
            current_source_class="maintenance_projection_current",
            drift_status="drift_candidate",
            completeness_class="bounded_metadata_only",
        ),
        action_attribution_decision=_related(attribution_status="attribution_candidate_ready"),
        audit_query_layer_decision=_related(query_status="query_plan_ready_bounded_projection"),
        passive_observe_decision=_related(display_state="read_only_projection"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        memory_governance_decision=_related(governance_status="governance_ready"),
        context_policy_decision=_related(policy_status="proposal_ready"),
        repo_audit_decision=_related(readiness_status="readiness_ready"),
    )

    assert len(decision.related_references) == 8
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.file_read_performed is False


def test_current_blocker_historical_debt_and_resource_debt_remain_distinct() -> None:
    decision = validate_system_drift_integrity_request(
        _request(current_blocker=True, historical_debt=True, resource_debt=True)
    )

    assert decision.current_blocker_preserved is True
    assert decision.historical_debt_preserved is True
    assert decision.resource_debt_preserved is True


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_system_drift_integrity_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.drift_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection_and_never_proof() -> None:
    decision = validate_system_drift_integrity_request(_request())

    assert decision.read_only_projection is True
    assert decision.drift_proof_claimed is False
    assert decision.integrity_proof_claimed is False
    assert decision.causality_claim_final is False
    _assert_non_authority(decision)
