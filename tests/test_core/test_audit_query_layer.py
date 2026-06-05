from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.audit_query_layer import (
    AUDIT_QUERY_LAYER_EXECUTION_PERMISSION,
    AUDIT_QUERY_LAYER_VERSION,
    validate_audit_query_layer_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "audit-query:aegis:1",
        "query_category": "command_lifecycle_query",
        "query_operation": "propose_projection_query",
        "namespace": "audit_query_layer",
        "projection_source_class": "caller_supplied_projection",
        "result_completeness_class": "bounded_projection_only",
        "freshness_class": "current_supplied",
        "result_trust_level": "backend_projection",
        "risk_level": "info",
        "source_refs": [{"ref_id": "runtime:command-lifecycle", "ref_type": "synthetic_projection"}],
        "provenance": [{"ref_id": "caller:test", "ref_type": "synthetic_fixture"}],
        "limitations": ["bounded projection only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": AUDIT_QUERY_LAYER_EXECUTION_PERMISSION,
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
        evidence_provided_by_audit_query=False,
        verifier_success=False,
        live_query_executed=False,
        raw_journal_read=False,
        raw_evidence_read=False,
        database_queried=False,
        repo_scan_performed=False,
        file_read_performed=False,
        model_call_performed=False,
        tool_call_performed=False,
        mcp_call_performed=False,
        web_query_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        export_performed=False,
        runtime_state_mutated=False,
        journal_mutated=False,
        evidence_mutated=False,
        replay_mutated=False,
        generated_artifact_created=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == AUDIT_QUERY_LAYER_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_audit_query is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.live_query_executed is False
    assert decision.raw_journal_read is False
    assert decision.raw_evidence_read is False
    assert decision.database_queried is False
    assert decision.repo_scan_performed is False
    assert decision.file_read_performed is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.web_query_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.export_performed is False
    assert decision.runtime_state_mutated is False
    assert decision.journal_mutated is False
    assert decision.evidence_mutated is False
    assert decision.replay_mutated is False
    assert decision.generated_artifact_created is False
    assert decision.data_sent_external is False
    assert decision.requires_backend_validation is True
    assert decision.read_only_projection is True


def test_valid_command_lifecycle_query_is_read_only_bounded_projection() -> None:
    decision = validate_audit_query_layer_request(_request())

    assert decision.contract_version == AUDIT_QUERY_LAYER_VERSION
    assert decision.query_status == "query_plan_ready_bounded_projection"
    assert decision.required_projection_kinds == ("command_lifecycle_projection",)
    assert decision.projection_truth_status == "bounded_projection_only"
    assert decision.bounded_projection_preserved is True
    _assert_non_authority(decision)


def test_complete_supplied_projection_can_claim_full_history_only_for_supplied_projection() -> None:
    decision = validate_audit_query_layer_request(
        _request(
            result_completeness_class="complete_for_supplied_projection",
            full_history_claimed=True,
            full_history_requested=True,
        )
    )

    assert decision.query_status == "query_plan_ready"
    assert decision.full_history_valid_for_supplied_projection is True
    assert decision.full_history_claimed is True
    assert decision.projection_truth_status == "complete_for_supplied_projection_only"
    _assert_non_authority(decision)


def test_bounded_projection_cannot_claim_full_history() -> None:
    decision = validate_audit_query_layer_request(_request(full_history_claimed=True))

    assert decision.query_status == "blocked_by_full_history_claim"
    assert "full_history_claim_requires_complete_supplied_projection" in decision.failure_reasons
    assert decision.full_history_claimed is False
    _assert_non_authority(decision)


def test_approval_and_clarification_queries_require_lifecycle_projection_refs() -> None:
    approval = validate_audit_query_layer_request(_request(query_category="approval_query"))
    clarification = validate_audit_query_layer_request(_request(query_category="clarification_query"))

    assert approval.required_projection_kinds == ("approval_projection", "command_lifecycle_projection")
    assert clarification.required_projection_kinds == ("approval_projection", "command_lifecycle_projection")
    _assert_non_authority(approval)
    _assert_non_authority(clarification)


def test_evidence_and_verifier_queries_are_refs_not_evidence_or_verifier_success() -> None:
    evidence = validate_audit_query_layer_request(_request(query_category="evidence_query"))
    verifier = validate_audit_query_layer_request(_request(query_category="verifier_query"))

    assert evidence.required_projection_kinds == ("evidence_audit_projection",)
    assert verifier.required_projection_kinds == ("evidence_audit_projection",)
    assert evidence.evidence_provided_by_audit_query is False
    assert verifier.verifier_success is False
    _assert_non_authority(evidence)
    _assert_non_authority(verifier)


def test_maintenance_projection_preserves_current_blocker_and_historical_debt_flags() -> None:
    current = validate_audit_query_layer_request(
        _request(
            query_category="maintenance_projection_query",
            projection_source_class="maintenance_scan_projection",
            current_blocker=True,
            risk_level=None,
        )
    )
    historical = validate_audit_query_layer_request(
        _request(
            query_category="maintenance_projection_query",
            projection_source_class="maintenance_scan_projection",
            freshness_class="historical",
            historical_debt=True,
            risk_level=None,
        )
    )

    assert current.current_blocker_preserved is True
    assert current.risk_level == "high"
    assert historical.historical_debt_preserved is True
    assert historical.freshness_class == "historical"
    assert historical.risk_level == "medium"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("query_category", "missing_query_category"),
        ("query_operation", "missing_query_operation"),
        ("namespace", "missing_namespace"),
        ("projection_source_class", "missing_projection_source_class"),
        ("result_completeness_class", "missing_result_completeness_class"),
        ("freshness_class", "missing_freshness_class"),
        ("result_trust_level", "missing_result_trust_level"),
    ],
)
def test_missing_required_fields_block_query_plan(field: str, reason: str) -> None:
    decision = validate_audit_query_layer_request(_request(**{field: None}))

    assert decision.query_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks_query_plan() -> None:
    decision = validate_audit_query_layer_request(_request(source_refs=[], provenance=[]))

    assert decision.query_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("query_category", "not_a_category", "unsupported_query_category"),
        ("query_operation", "execute_live_query", "unsupported_query_operation"),
        ("projection_source_class", "raw_database", "unsupported_projection_source_class"),
        ("result_completeness_class", "complete_history", "unsupported_result_completeness_class"),
        ("freshness_class", "live", "unsupported_freshness_class"),
        ("result_trust_level", "trusted_frontend", "unsupported_result_trust_level"),
        ("risk_level", "safe", "unsupported_risk_level"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_audit_query_layer_request(_request(**{field: value}))

    assert decision.query_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize(
    ("completeness", "freshness", "flag", "preserved_field"),
    [
        ("stale_projection", "stale", "stale", "stale_projection_preserved"),
        ("unknown_completeness", "unknown", "unknown_state", "unknown_projection_preserved"),
        ("unavailable", "unknown", "unavailable", "unavailable_projection_preserved"),
        ("bounded_projection_only", "current_supplied", "future_gated", "future_gated_preserved"),
    ],
)
def test_stale_unknown_unavailable_and_future_gated_states_are_preserved(
    completeness: str,
    freshness: str,
    flag: str,
    preserved_field: str,
) -> None:
    decision = validate_audit_query_layer_request(
        _request(
            result_completeness_class=completeness,
            freshness_class=freshness,
            **{flag: True},
        )
    )

    assert getattr(decision, preserved_field) is True
    _assert_non_authority(decision)


def test_lower_trust_frontend_projection_cannot_claim_complete_history_or_authority() -> None:
    decision = validate_audit_query_layer_request(
        _request(
            result_trust_level="frontend_supplied_low_trust",
            result_completeness_class="complete_for_supplied_projection",
        )
    )

    assert decision.query_status == "blocked_by_policy"
    assert "lower_trust_result_cannot_claim_complete_history" in decision.failure_reasons
    assert decision.lower_trust_result is True
    assert decision.frontend_authority is False


@pytest.mark.parametrize(
    ("category", "projection"),
    [
        ("future_action_attribution_query", "future_action_attribution_projection"),
        ("future_system_drift_query", "future_system_drift_projection"),
        ("future_integrity_monitor_query", "future_system_drift_projection"),
    ],
)
def test_future_query_categories_remain_future_gated(category: str, projection: str) -> None:
    decision = validate_audit_query_layer_request(
        _request(query_category=category, projection_source_class=projection)
    )

    assert decision.query_status == "future_gated"
    assert decision.future_gated_preserved is True
    _assert_non_authority(decision)


def test_export_operation_is_future_gated_without_exporting() -> None:
    decision = validate_audit_query_layer_request(_request(query_operation="propose_export_future"))

    assert decision.query_status == "future_gated"
    assert decision.export_performed is False
    assert decision.generated_artifact_created is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_query_executed", "live_query_execution_denied"),
        ("raw_journal_read", "raw_journal_read_denied"),
        ("raw_evidence_read", "raw_evidence_read_denied"),
        ("database_queried", "database_query_denied"),
        ("repo_scan_performed", "repo_scan_denied"),
        ("file_read_performed", "file_read_denied"),
        ("model_call_performed", "model_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("export_performed", "export_denied"),
        ("runtime_state_mutated", "runtime_state_mutation_denied"),
        ("journal_mutated", "journal_mutation_denied"),
        ("evidence_mutated", "evidence_mutation_denied"),
        ("replay_mutated", "replay_mutation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_live_query_reads_calls_exports_and_mutations_are_rejected(field: str, reason: str) -> None:
    decision = validate_audit_query_layer_request(_request(**{field: True}))

    assert decision.query_status == "blocked_by_execution_claim"
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
        ("evidence_provided_by_audit_query", "audit_query_cannot_provide_evidence"),
        ("verifier_success", "audit_query_cannot_mark_verifier_success"),
        ("success", "success_claim_denied"),
        ("proof", "proof_claim_denied"),
        ("certification_claim", "certification_claim_denied"),
        ("query_output_is_evidence", "query_output_evidence_claim_denied"),
        ("query_output_is_verifier_success", "query_output_verifier_claim_denied"),
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_authority_grants_evidence_verifier_truth_and_proof_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_audit_query_layer_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_audit_query_layer_request(_request(execution_permission="granted_by_audit_query"))

    assert decision.query_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("passive_observe_decision", _related(runtime_dispatch_allowed=True)),
        ("maintenance_decision", _related(live_query_executed=True)),
        ("command_lifecycle_decision", _related(raw_journal_read=True)),
        ("evidence_audit_decision", _related(raw_evidence_read=True)),
        ("policy_extension_decision", _related(verifier_success=True)),
        ("context_policy_decision", _related(context_retrieval_performed=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("local_model_inventory_decision", _related(model_call_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("repo_audit_decision", _related(repo_scan_performed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_audit_query_layer_request(_request(), **{related_name: related_value})

    assert decision.query_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_audit_query_layer_request(
        _request(query_category="passive_observe_query", projection_source_class="passive_observe_projection"),
        passive_observe_decision=_related(display_state="read_only_projection"),
        context_policy_decision=_related(policy_status="proposal_ready"),
        memory_governance_decision=_related(governance_status="governance_ready"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
        repo_audit_decision=_related(readiness_status="readiness_ready"),
    )

    assert len(decision.related_references) == 5
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.repo_scan_performed is False


def test_model_provider_and_local_inventory_metadata_do_not_become_model_health_or_calls() -> None:
    decision = validate_audit_query_layer_request(
        _request(
            query_category="model_provider_readiness_query",
            projection_source_class="model_readiness_projection",
        ),
        model_provider_readiness_decision=_related(readiness_status="metadata_ready"),
        local_model_inventory_decision=_related(inventory_status="metadata_ready"),
    )

    assert decision.required_projection_kinds == ("model_readiness_projection",)
    assert decision.model_call_performed is False
    assert decision.verifier_success is False
    _assert_non_authority(decision)


def test_capability_lease_query_is_candidate_only_not_permission() -> None:
    decision = validate_audit_query_layer_request(
        _request(query_category="capability_lease_query", projection_source_class="policy_projection"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
    )

    assert decision.required_projection_kinds == ("policy_projection",)
    assert decision.lease_grant is False
    assert decision.runtime_dispatch_allowed is False


def test_repo_audit_readiness_query_does_not_read_files_or_scan_repo() -> None:
    decision = validate_audit_query_layer_request(
        _request(
            query_category="repo_audit_readiness_query",
            projection_source_class="repo_audit_readiness_projection",
        ),
        repo_audit_decision=_related(readiness_status="readiness_ready"),
    )

    assert decision.required_projection_kinds == ("repo_audit_readiness_projection",)
    assert decision.repo_scan_performed is False
    assert decision.file_read_performed is False


def test_compliance_and_developer_passport_queries_are_not_proof() -> None:
    compliance = validate_audit_query_layer_request(
        _request(query_category="compliance_evidence_query"),
        compliance_evidence_decision=_related(decision_status="candidate_refs_only"),
    )
    passport = validate_audit_query_layer_request(
        _request(query_category="developer_work_passport_query"),
        developer_work_passport_decision=_related(decision_status="candidate_refs_only"),
    )

    assert compliance.evidence_provided_by_audit_query is False
    assert compliance.verifier_success is False
    assert passport.evidence_provided_by_audit_query is False
    assert passport.verifier_success is False


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_audit_query_layer_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.query_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection_and_never_runtime_dispatch() -> None:
    decision = validate_audit_query_layer_request(_request())

    assert decision.read_only_projection is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.full_history_claimed is False
    _assert_non_authority(decision)
