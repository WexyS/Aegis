from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_source_plan_display import (
    REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION,
    REPO_AUDIT_SOURCE_PLAN_DISPLAY_VERSION,
    validate_repo_audit_source_plan_display_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-source-plan-display:aegis:1",
        "display_surface_class": "ui_panel_future",
        "display_intent_class": "summarize_dry_run_plan",
        "display_status_class": "display_ready_metadata_only",
        "display_truth_label": "metadata_only",
        "display_risk_label": "info",
        "namespace": "repo_audit_source_plan_display",
        "source_refs": [{"ref_id": "dry-run:source-plan:1", "kind": "synthetic_source_ref"}],
        "provenance": [{"ref_id": "caller:test", "kind": "synthetic_fixture"}],
        "dry_run_source_plan_refs": [{"ref_id": "dry-run-plan:1", "kind": "synthetic_plan_ref"}],
        "limitations": ["display metadata only"],
        "unknowns": [],
        "human_review_required": False,
        "memory_derived_context": False,
        "project_or_repository_scoped": False,
        "private_display_metadata": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION,
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
        evidence_provided_by_display=False,
        verifier_success=False,
        mutation_performed=False,
        frontend_authority=False,
        cli_authority=False,
        ui_render_performed=False,
        cli_output_performed=False,
        report_generated=False,
        generated_artifact_created=False,
        github_api_called=False,
        github_url_fetched=False,
        browser_fetch_performed=False,
        raw_file_fetch_performed=False,
        git_clone_performed=False,
        local_repo_read_performed=False,
        repo_scan_performed=False,
        directory_scan_performed=False,
        file_list_performed=False,
        file_stat_performed=False,
        file_hash_performed=False,
        file_read_performed=False,
        http_request_performed=False,
        external_api_called=False,
        mcp_call_performed=False,
        tool_call_performed=False,
        model_call_performed=False,
        web_query_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        context_package_created=False,
        cache_written=False,
        source_record_created=False,
        citation_record_created=False,
        data_sent_external=False,
        private_repo_access_allowed=False,
        raw_content_ingestion_allowed=False,
        source_truth_claimed=False,
        repo_audit_proof_claimed=False,
        compliance_proof_claimed=False,
        passport_proof_claimed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == REPO_AUDIT_SOURCE_PLAN_DISPLAY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_display is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.cli_authority is False
    assert decision.ui_render_performed is False
    assert decision.cli_output_performed is False
    assert decision.report_generated is False
    assert decision.generated_artifact_created is False
    assert decision.github_api_called is False
    assert decision.github_url_fetched is False
    assert decision.browser_fetch_performed is False
    assert decision.raw_file_fetch_performed is False
    assert decision.git_clone_performed is False
    assert decision.local_repo_read_performed is False
    assert decision.repo_scan_performed is False
    assert decision.directory_scan_performed is False
    assert decision.file_list_performed is False
    assert decision.file_stat_performed is False
    assert decision.file_hash_performed is False
    assert decision.file_read_performed is False
    assert decision.http_request_performed is False
    assert decision.external_api_called is False
    assert decision.mcp_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.model_call_performed is False
    assert decision.web_query_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.context_package_created is False
    assert decision.cache_written is False
    assert decision.source_record_created is False
    assert decision.citation_record_created is False
    assert decision.data_sent_external is False
    assert decision.private_repo_access_allowed is False
    assert decision.raw_content_ingestion_allowed is False
    assert decision.source_truth_claimed is False
    assert decision.repo_audit_proof_claimed is False
    assert decision.compliance_proof_claimed is False
    assert decision.passport_proof_claimed is False
    assert decision.display_overclaims_authority is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def _assert_blocked(decision: object, reason: str) -> None:
    assert reason in decision.failure_reasons
    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_valid_ui_panel_display_projection_is_metadata_only_and_non_authoritative() -> None:
    decision = validate_repo_audit_source_plan_display_request(_request())

    assert decision.contract_version == REPO_AUDIT_SOURCE_PLAN_DISPLAY_VERSION
    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert decision.display_projection_status == "display_metadata_projection_only"
    assert decision.truth_label_status == "truth_label_metadata_only"
    assert decision.non_authority_notice_status == "non_authority_required"
    assert decision.source_ref_display_status == "source_refs_preserved"
    assert decision.future_gated is False
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("display_surface_class", "display_intent_class"),
    [
        ("cli_summary_future", "summarize_dry_run_plan"),
        ("mission_control_card_future", "show_candidate_sources"),
        ("audit_query_projection_future", "show_exclusions"),
        ("report_preview_future", "show_blockers"),
        ("operator_review_queue_future", "show_operator_review_items"),
    ],
)
def test_display_surfaces_remain_projection_only_not_render_or_cli_output(
    display_surface_class: str,
    display_intent_class: str,
) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_surface_class=display_surface_class, display_intent_class=display_intent_class)
    )

    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert decision.ui_render_performed is False
    assert decision.cli_output_performed is False
    assert decision.report_generated is False


@pytest.mark.parametrize(
    ("display_intent_class", "expected_status"),
    [
        ("show_provenance_refs", "source_refs_only_not_evidence"),
        ("show_non_authority_notice", "source_refs_preserved"),
    ],
)
def test_provenance_and_non_authority_intents_are_metadata_only(display_intent_class: str, expected_status: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_intent_class=display_intent_class)
    )

    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert decision.source_ref_display_status == expected_status
    assert decision.evidence_provided_by_display is False
    assert decision.verifier_success is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("display_surface_class", "missing_display_surface_class"),
        ("display_intent_class", "missing_display_intent_class"),
        ("display_status_class", "missing_display_status_class"),
        ("display_truth_label", "missing_display_truth_label"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(source_refs=[], provenance=[]))

    _assert_blocked(decision, "missing_source_refs_or_provenance")


def test_missing_dry_run_source_plan_ref_blocks() -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(dry_run_source_plan_refs=[]))

    _assert_blocked(decision, "missing_dry_run_source_plan_reference")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("display_surface_class", "browser_window_now", "unsupported_display_surface_class"),
        ("display_intent_class", "render_live_ui", "unsupported_display_intent_class"),
        ("display_status_class", "rendered", "unsupported_display_status_class"),
        ("display_truth_label", "verified_truth", "unsupported_display_truth_label"),
        ("display_risk_label", "safe", "unsupported_display_risk_label"),
    ],
)
def test_unknown_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: value}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("display_truth_label", "expected_status"),
    [
        ("candidate_only", "truth_label_metadata_only"),
        ("excluded_by_policy", "blocked_or_excluded_label_preserved"),
        ("blocked", "blocked_or_excluded_label_preserved"),
        ("operator_review_required", "review_or_gate_label_preserved"),
        ("bounded_projection", "truth_label_metadata_only"),
        ("stale_or_unverified", "low_trust_or_stale_label_preserved"),
        ("low_trust", "low_trust_or_stale_label_preserved"),
        ("unavailable", "blocked_or_excluded_label_preserved"),
    ],
)
def test_truth_labels_are_preserved_without_becoming_proof(display_truth_label: str, expected_status: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_truth_label=display_truth_label)
    )

    assert decision.truth_label_status == expected_status
    assert decision.source_truth_claimed is False
    assert decision.repo_audit_proof_claimed is False


def test_future_gated_truth_label_requires_operator_review_but_not_execution() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_status_class="future_gated", display_truth_label="future_gated")
    )

    assert decision.display_readiness_status == "display_future_gated"
    assert decision.future_gated is True
    assert decision.operator_review_status == "operator_review_required"
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize("display_risk_label", ["high", "critical"])
def test_high_risk_label_preserved_and_requires_operator_review(display_risk_label: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_risk_label=display_risk_label)
    )

    assert decision.display_readiness_status == "display_requires_operator_review"
    assert decision.risk_label_status == "high_risk_label_preserved"
    assert decision.human_review_required is True


def test_operator_review_status_class_preserves_review_requirement() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(
            display_status_class="requires_operator_review",
            display_truth_label="operator_review_required",
            identity_scope_decision="metadata",
        ),
        identity_scope_decision=_related(scope_status="identity_scope_ready"),
    )

    assert decision.display_readiness_status == "display_requires_operator_review"
    assert decision.operator_review_status == "operator_review_required"


def test_private_display_metadata_requires_identity_scope() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(private_display_metadata=True)
    )

    _assert_blocked(decision, "missing_identity_scope")


def test_repository_scoped_display_metadata_requires_identity_scope() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(project_or_repository_scoped=True)
    )

    _assert_blocked(decision, "missing_identity_scope")


def test_identity_scope_reference_allows_repository_scoped_metadata_without_authority() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(project_or_repository_scoped=True),
        identity_scope_decision=_related(scope_status="identity_scope_ready"),
    )

    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert decision.related_references[0].reference_only is True
    _assert_non_authority(decision)


def test_memory_derived_context_requires_memory_governance() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(memory_derived_context=True)
    )

    _assert_blocked(decision, "missing_memory_governance")


def test_memory_governance_reference_allows_memory_metadata_without_retrieval() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(memory_derived_context=True),
        memory_governance_decision=_related(governance_status="memory_governance_ready"),
    )

    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert decision.memory_retrieval_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("display_claims_source_truth", "display_source_truth_claim_denied"),
        ("display_claims_repo_read", "display_repo_read_claim_denied"),
        ("display_claims_evidence", "display_evidence_claim_denied"),
        ("display_claims_verifier_success", "display_verifier_claim_denied"),
        ("display_claims_permission", "display_permission_claim_denied"),
        ("display_claims_deleted_or_cleaned", "display_cleanup_claim_denied"),
        ("display_claims_available", "display_availability_claim_denied"),
        ("display_claims_permitted", "display_permission_claim_denied"),
        ("display_claims_complete_repo_plan", "bounded_projection_complete_claim_denied"),
        ("low_trust_shown_as_authority", "low_trust_authority_claim_denied"),
    ],
)
def test_display_overclaim_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("display_truth_label", "flag", "reason"),
    [
        ("metadata_only", "display_claims_source_truth", "display_source_truth_claim_denied"),
        ("candidate_only", "display_claims_repo_read", "display_repo_read_claim_denied"),
        ("excluded_by_policy", "display_claims_cleaned", "display_cleanup_claim_denied"),
        ("future_gated", "display_claims_available", "display_availability_claim_denied"),
        ("blocked", "display_claims_permitted", "display_permission_claim_denied"),
        ("low_trust", "low_trust_shown_as_authority", "low_trust_authority_claim_denied"),
        ("bounded_projection", "bounded_projection_claims_complete", "bounded_projection_complete_claim_denied"),
    ],
)
def test_truth_specific_overclaims_are_rejected(display_truth_label: str, flag: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(display_truth_label=display_truth_label, **{flag: True})
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_display", "display_cannot_provide_evidence"),
        ("verifier_success", "display_cannot_mark_verifier_success"),
        ("mutation_performed", "mutation_performed_denied"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("cli_authority", "cli_authority_not_allowed"),
        ("source_truth_claimed", "source_truth_claim_denied"),
        ("repo_audit_proof_claimed", "repo_audit_proof_claim_denied"),
        ("compliance_proof_claimed", "compliance_proof_claim_denied"),
        ("passport_proof_claimed", "passport_proof_claim_denied"),
        ("private_repo_access_allowed", "private_repo_access_permission_denied"),
        ("raw_content_ingestion_allowed", "raw_content_ingestion_denied"),
    ],
)
def test_authority_grant_truth_and_proof_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("ui_render_performed", "ui_render_denied"),
        ("cli_output_performed", "cli_output_denied"),
        ("report_generated", "report_generation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("github_api_called", "github_api_call_denied"),
        ("github_url_fetched", "github_url_fetch_denied"),
        ("browser_fetch_performed", "browser_fetch_denied"),
        ("raw_file_fetch_performed", "raw_file_fetch_denied"),
        ("git_clone_performed", "git_clone_denied"),
        ("local_repo_read_performed", "local_repo_read_denied"),
        ("repo_scan_performed", "repo_scan_denied"),
        ("directory_scan_performed", "directory_scan_denied"),
        ("file_list_performed", "file_list_denied"),
        ("file_stat_performed", "file_stat_denied"),
        ("file_hash_performed", "file_hash_denied"),
        ("file_read_performed", "file_read_denied"),
        ("http_request_performed", "http_request_denied"),
        ("external_api_called", "external_api_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("model_call_performed", "model_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("context_package_created", "context_package_creation_denied"),
        ("cache_written", "cache_write_denied"),
        ("source_record_created", "source_record_creation_denied"),
        ("citation_record_created", "citation_record_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_execution_render_network_read_context_and_artifact_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    "field",
    [
        "frontend_result_is_authority",
        "cli_result_is_authority",
        "model_output_is_authority",
        "mcp_output_is_authority",
        "tool_output_is_authority",
        "frontend_output_is_truth",
        "cli_output_is_truth",
        "model_output_is_truth",
        "mcp_output_is_truth",
        "tool_output_is_truth",
    ],
)
def test_frontend_cli_model_mcp_tool_output_cannot_be_authority_or_truth(field: str) -> None:
    decision = validate_repo_audit_source_plan_display_request(_request(**{field: True}))

    assert decision.display_readiness_status in {"blocked_by_display_overclaim", "blocked_by_truth_claim"}
    _assert_non_authority(decision)


def test_execution_permission_grant_is_rejected() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(execution_permission="granted_by_display")
    )

    _assert_blocked(decision, "execution_permission_claim_denied")


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("repo_audit_dry_run_source_plan_decision", {"local_repo_read_performed": True}),
        ("repo_audit_source_intake_decision", {"source_truth_claimed": True}),
        ("github_source_connector_decision", {"github_url_fetched": True}),
        ("web_research_gateway_decision", {"web_query_performed": True}),
        ("local_model_context_profile_decision", {"model_call_performed": True}),
        ("context_policy_decision", {"context_package_created": True}),
        ("identity_scope_decision", {"runtime_dispatch_allowed": True}),
        ("memory_governance_decision", {"memory_retrieval_performed": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("capability_lease_decision", {"lease_grant": True}),
        ("repo_audit_decision", {"repo_scan_performed": True}),
        ("audit_query_layer_decision", {"report_generated": True}),
        ("action_attribution_decision", {"mutation_performed": True}),
        ("system_drift_integrity_decision", {"verifier_success": True}),
        ("passive_observe_decision", {"authority": True}),
        ("compliance_evidence_decision", {"compliance_proof_claimed": True}),
        ("developer_work_passport_decision", {"passport_proof_claimed": True}),
        ("plugin_review_decision", {"tool_call_performed": True}),
        ("mission_control_decision", {"frontend_authority": True}),
        ("tool_simulation_decision", {"tool_output_is_truth": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, kwargs: dict[str, object]) -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(),
        repo_audit_dry_run_source_plan_decision=_related(dry_run_status="dry_run_ready"),
        github_source_connector_decision=_related(connector_status="metadata_only"),
        context_policy_decision=_related(policy_status="context_policy_ready"),
    )

    assert decision.display_readiness_status == "display_ready_metadata_only"
    assert [ref.label for ref in decision.related_references] == [
        "repo_audit_dry_run_source_plan",
        "github_source_connector",
        "context_policy",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


def test_context_policy_external_transfer_is_rejected() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(),
        context_policy_decision=_related(data_sent_external=True),
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "dry-run:source-plan:1", "tags": ["a"]}])
    original_request = deepcopy(request)
    related = _related(readiness_status="metadata_ready")
    original_status = related.readiness_status

    decision = validate_repo_audit_source_plan_display_request(
        request,
        repo_audit_dry_run_source_plan_decision=related,
    )

    assert request == original_request
    assert related.readiness_status == original_status
    assert decision.display_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.display_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_repo_audit_source_plan_display_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.display_input is None


def test_output_never_sets_execution_or_render_flags_even_when_blocked() -> None:
    decision = validate_repo_audit_source_plan_display_request(
        _request(ui_render_performed=True, github_api_called=True, source_truth_claimed=True)
    )

    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)
