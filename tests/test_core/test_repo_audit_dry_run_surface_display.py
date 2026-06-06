from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.api.repo_audit_dry_run_projection import (
    build_repo_audit_dry_run_projection_api_response,
)
from aegis.core.repo_audit_dry_run_surface_display import (
    REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION,
    REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_VERSION,
    validate_repo_audit_dry_run_surface_display_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-dry-run-surface-display:aegis:1",
        "surface_display_source_class": "repo_audit_dry_run_projection_api",
        "surface_display_state_class": "no_projection_available",
        "ui_meaning_class": "neutral_no_data",
        "namespace": "repo_audit_dry_run_surface_display",
        "source_refs": [{"ref_id": "api:/maintenance/repo-audit/dry-run-projection"}],
        "provenance": [{"ref_id": "caller-supplied-display-metadata"}],
        "display_severity_class": "neutral",
        "limitations": ["display readiness only"],
        "unknowns": ["current dry-run projection is not observed"],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        display_readiness_status="display_ready_metadata_only",
        api_surface_status_class="metadata_candidate_available",
        dry_run_status="dry_run_ready",
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        authority=False,
        frontend_authority=False,
        api_authority=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_display=False,
        evidence_provided=False,
        verifier_success=False,
        mutation_performed=False,
        run_authorized=False,
        retry_authorized=False,
        run_control_exposed=False,
        retry_control_exposed=False,
        action_control_exposed=False,
        repo_read_performed=False,
        repo_scan_performed=False,
        directory_scan_performed=False,
        file_list_performed=False,
        file_stat_performed=False,
        file_hash_performed=False,
        file_read_performed=False,
        github_api_called=False,
        github_url_fetched=False,
        browser_fetch_performed=False,
        raw_file_fetch_performed=False,
        git_clone_performed=False,
        http_request_performed=False,
        external_api_called=False,
        model_call_performed=False,
        tool_call_performed=False,
        mcp_call_performed=False,
        web_query_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        context_package_created=False,
        cache_written=False,
        source_record_created=False,
        citation_record_created=False,
        report_generated=False,
        generated_artifact_created=False,
        source_truth_claimed=False,
        repo_audit_proof_claimed=False,
        compliance_proof_claimed=False,
        passport_proof_claimed=False,
        cleanup_performed=False,
        deletion_performed=False,
        fake_current_projection_created=False,
        fake_source_truth_created=False,
        fake_success_created=False,
        fake_verification_created=False,
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
    assert decision.execution_permission == REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_display is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.run_authorized is False
    assert decision.retry_authorized is False
    assert decision.run_control_exposed is False
    assert decision.retry_control_exposed is False
    assert decision.action_control_exposed is False
    assert decision.repo_read_performed is False
    assert decision.repo_scan_performed is False
    assert decision.directory_scan_performed is False
    assert decision.file_list_performed is False
    assert decision.file_stat_performed is False
    assert decision.file_hash_performed is False
    assert decision.file_read_performed is False
    assert decision.github_api_called is False
    assert decision.github_url_fetched is False
    assert decision.browser_fetch_performed is False
    assert decision.raw_file_fetch_performed is False
    assert decision.git_clone_performed is False
    assert decision.http_request_performed is False
    assert decision.external_api_called is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.web_query_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.context_package_created is False
    assert decision.cache_written is False
    assert decision.source_record_created is False
    assert decision.citation_record_created is False
    assert decision.report_generated is False
    assert decision.generated_artifact_created is False
    assert decision.source_truth_claimed is False
    assert decision.repo_audit_proof_claimed is False
    assert decision.compliance_proof_claimed is False
    assert decision.passport_proof_claimed is False
    assert decision.cleanup_performed is False
    assert decision.deletion_performed is False
    assert decision.fake_current_projection_created is False
    assert decision.fake_source_truth_created is False
    assert decision.fake_success_created is False
    assert decision.fake_verification_created is False
    assert decision.data_sent_external is False
    assert decision.read_only_projection is True
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True


def _assert_blocked(decision: object, reason: str) -> None:
    assert reason in decision.failure_reasons
    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)


def test_no_projection_available_maps_to_neutral_no_data_display() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(_request())

    assert decision.contract_version == REPO_AUDIT_DRY_RUN_SURFACE_DISPLAY_VERSION
    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert decision.display_severity_class == "neutral"
    assert decision.recommended_wording == "No current repo-audit dry-run projection is available."
    assert decision.color_semantics == "neutral_not_failure"
    assert decision.truthfulness_classification.startswith("display_not_repo_read")
    _assert_non_authority(decision)


def test_not_observed_maps_to_neutral_not_observed_display() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(surface_display_state_class="repo_audit_dry_run_not_observed")
    )

    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert decision.recommended_wording == "Repo-audit dry-run has not been observed."
    assert decision.run_guidance == (
        "No run, retry, fetch, clone, or read is authorized by Repo Audit dry-run surface display."
    )


def test_not_configured_maps_to_neutral_not_failure_display() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(surface_display_state_class="repo_audit_dry_run_not_configured")
    )

    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert decision.color_semantics == "neutral_not_failure"


@pytest.mark.parametrize(
    ("state", "expected_wording"),
    [
        ("dry_run_plan_metadata_candidate", "Metadata candidate only; not evidence or verifier success."),
        ("source_intake_metadata_candidate", "Metadata candidate only; not evidence or verifier success."),
        ("source_plan_display_candidate", "Metadata candidate only; not evidence or verifier success."),
        ("candidate_sources_available", "Candidate sources only; not source truth or repo read."),
    ],
)
def test_metadata_and_candidate_states_are_informational_not_source_truth(
    state: str,
    expected_wording: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class="informational_candidate",
            display_severity_class="info",
        )
    )

    assert decision.display_readiness_status == "display_ready_informational_candidate"
    assert decision.recommended_wording == expected_wording
    assert decision.color_semantics == "info_not_verified_source"
    assert decision.source_truth_claimed is False
    assert decision.repo_read_performed is False
    _assert_non_authority(decision)


def test_exclusion_metadata_is_not_cleanup_or_deletion() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class="exclusions_available",
            ui_meaning_class="exclusion_metadata",
            display_severity_class="info",
        )
    )

    assert decision.display_readiness_status == "display_ready_exclusion_metadata"
    assert decision.recommended_wording == "Exclusion metadata only; no cleanup or deletion performed."
    assert decision.color_semantics == "info_not_cleanup_success"
    assert decision.cleanup_performed is False
    assert decision.deletion_performed is False


@pytest.mark.parametrize("state", ["blockers_available", "blocked_by_policy"])
def test_blocker_states_are_blocked_notice_not_permission(state: str) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class="blocked_notice",
            display_severity_class="warning",
        )
    )

    assert decision.display_readiness_status == "display_ready_blocked_notice"
    assert decision.color_semantics == "warning_not_permission"
    assert decision.runtime_dispatch_allowed is False
    assert decision.run_authorized is False


def test_future_gated_state_is_not_execution_ready() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class="future_gated",
            ui_meaning_class="future_gated_notice",
            display_severity_class="future",
        )
    )

    assert decision.display_readiness_status == "display_ready_future_gated"
    assert decision.recommended_wording == "Future-gated; not execution-ready."
    assert decision.color_semantics == "future_not_execution_ready"
    assert "operator_review_recommended" in decision.required_operator_actions


def test_operator_review_state_is_not_run_authorization() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class="operator_review_required_candidate",
            ui_meaning_class="operator_review_required",
            display_severity_class="attention",
        )
    )

    assert decision.display_readiness_status == "display_ready_operator_review"
    assert decision.recommended_wording == "Operator review required; run is not authorized."
    assert decision.run_guidance == "Operator review required; run is not authorized."
    assert "run_requires_separate_authorization" in decision.required_operator_actions
    assert decision.run_authorized is False


def test_safe_api_surface_response_can_be_mapped_without_frontend_authority() -> None:
    response = build_repo_audit_dry_run_projection_api_response()
    decision = validate_repo_audit_dry_run_surface_display_request(
        {
            "request_id": "repo-audit-dry-run-surface-display:api-response",
            "surface_display_source_class": "repo_audit_dry_run_projection_api",
            "projection_result_class": response["projection_result_class"],
            "ui_meaning_class": "neutral_no_data",
            "namespace": "repo_audit_dry_run_surface_display",
            "source_refs": [{"ref_id": "api:/maintenance/repo-audit/dry-run-projection"}],
            "provenance": response["provenance"],
            "display_severity_class": "neutral",
        },
        repo_audit_dry_run_api_surface_decision=response,
    )

    assert decision.surface_display_state_class == "no_projection_available"
    assert decision.display_readiness_status == "display_ready_neutral_no_data"
    assert [ref.label for ref in decision.related_references] == ["repo_audit_dry_run_api_surface"]
    _assert_non_authority(decision)


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
    decision = validate_repo_audit_dry_run_surface_display_request(_request(**{field: None}))

    _assert_blocked(decision, reason)


def test_missing_source_refs_and_provenance_blocks() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
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
    decision = validate_repo_audit_dry_run_surface_display_request(_request(**{field: value}))

    _assert_blocked(decision, reason)


def test_unknown_taxonomy_values_block() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
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
        ("no_projection_available", "warning_attention", "no_data_state_requires_neutral_meaning"),
        ("candidate_sources_available", "operator_review_required", "candidate_state_requires_informational_meaning"),
        ("exclusions_available", "informational_candidate", "exclusion_state_requires_exclusion_metadata"),
        ("blockers_available", "informational_candidate", "blocked_state_requires_blocked_notice"),
        ("future_gated", "informational_candidate", "future_gated_state_requires_future_notice"),
        ("operator_review_required_candidate", "warning_attention", "operator_review_state_requires_review_meaning"),
    ],
)
def test_state_meaning_mismatches_block_truthfulness(
    state: str,
    meaning: str,
    reason: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class=meaning,
            display_severity_class="neutral",
        )
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("state", "meaning", "severity", "reason"),
    [
        ("no_projection_available", "neutral_no_data", "warning", "no_data_state_severity_overstated"),
        ("candidate_sources_available", "informational_candidate", "warning", "candidate_state_severity_overstated"),
        ("exclusions_available", "exclusion_metadata", "blocked", "exclusion_state_severity_overstated"),
        ("future_gated", "future_gated_notice", "warning", "future_gated_state_severity_overstated"),
    ],
)
def test_display_severity_cannot_be_treated_as_backend_truth(
    state: str,
    meaning: str,
    severity: str,
    reason: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class=state,
            ui_meaning_class=meaning,
            display_severity_class=severity,
        )
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    "forbidden_meaning",
    [
        "repo_read_performed",
        "source_truth_verified",
        "source_available_verified",
        "evidence_available",
        "verifier_success",
        "report_generated",
        "compliance_proof",
        "passport_proof",
        "run_authorized",
        "execution_ready",
        "cleanup_performed",
        "deletion_performed",
        "frontend_authority",
    ],
)
def test_forbidden_ui_meanings_are_rejected(forbidden_meaning: str) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(ui_meaning_class=forbidden_meaning)
    )

    _assert_blocked(decision, "forbidden_ui_meaning_denied")


@pytest.mark.parametrize(
    ("wording", "reason"),
    [
        ("Repo read performed.", "display_wording_repo_read_claim_denied"),
        ("Source truth verified.", "display_wording_source_truth_claim_denied"),
        ("Source available verified.", "display_wording_source_availability_claim_denied"),
        ("Evidence available.", "display_wording_evidence_claim_denied"),
        ("Verifier success.", "display_wording_verifier_claim_denied"),
        ("Report generated.", "display_wording_report_claim_denied"),
        ("Compliance proof.", "display_wording_compliance_claim_denied"),
        ("Passport proof.", "display_wording_passport_claim_denied"),
        ("Run authorized.", "display_wording_run_authorization_denied"),
        ("Execution ready.", "display_wording_execution_ready_claim_denied"),
        ("Cleanup performed.", "display_wording_cleanup_claim_denied"),
        ("Deletion performed.", "display_wording_deletion_claim_denied"),
    ],
)
def test_display_wording_cannot_overclaim_truth_or_authority(
    wording: str,
    reason: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(display_wording_candidate=wording)
    )

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("related_name", "kwargs"),
    [
        ("repo_audit_dry_run_api_surface_decision", {"source_truth_claimed": True}),
        ("repo_audit_dry_run_source_plan_decision", {"repo_read_performed": True}),
        ("repo_audit_source_intake_decision", {"source_truth_claimed": True}),
        ("repo_audit_source_plan_display_decision", {"report_generated": True}),
        ("github_source_connector_decision", {"github_url_fetched": True}),
        ("web_research_gateway_decision", {"web_query_performed": True}),
        ("context_policy_decision", {"context_package_created": True}),
        ("identity_scope_decision", {"runtime_dispatch_allowed": True}),
        ("memory_governance_decision", {"memory_retrieval_performed": True}),
        ("policy_extension_decision", {"approval_grant": True}),
        ("capability_lease_decision", {"lease_grant": True}),
        ("compliance_evidence_decision", {"compliance_proof_claimed": True}),
        ("developer_work_passport_decision", {"passport_proof_claimed": True}),
        ("mission_control_decision", {"frontend_authority": True}),
        ("passive_observe_decision", {"runtime_state_mutated": True}),
    ],
)
def test_unsafe_related_decisions_are_rejected(
    related_name: str,
    kwargs: dict[str, object],
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(),
        **{related_name: _related(**kwargs)},
    )

    _assert_blocked(decision, "unsafe_related_decision")


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            surface_display_state_class="candidate_sources_available",
            ui_meaning_class="informational_candidate",
            display_severity_class="info",
        ),
        repo_audit_dry_run_source_plan_decision=_related(dry_run_status="dry_run_ready"),
        repo_audit_source_intake_decision=_related(intake_status="metadata_only"),
        repo_audit_source_plan_display_decision=_related(display_readiness_status="display_ready_metadata_only"),
    )

    assert decision.display_readiness_status == "display_ready_informational_candidate"
    assert [ref.label for ref in decision.related_references] == [
        "repo_audit_dry_run_source_plan",
        "repo_audit_source_intake",
        "repo_audit_source_plan_display",
    ]
    assert all(ref.reference_only for ref in decision.related_references)
    assert all(ref.authority is False for ref in decision.related_references)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("api_authority", "api_authority_not_allowed"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("run_authorized", "run_authorization_denied"),
        ("retry_authorized", "retry_authorization_denied"),
        ("run_control_exposed", "run_control_exposure_denied"),
        ("retry_control_exposed", "retry_control_exposure_denied"),
        ("action_control_exposed", "action_control_exposure_denied"),
        ("source_truth_claimed", "source_truth_claim_denied"),
        ("source_available_verified", "source_availability_verification_denied"),
        ("repo_audit_proof_claimed", "repo_audit_proof_claim_denied"),
        ("compliance_proof_claimed", "compliance_proof_claim_denied"),
        ("passport_proof_claimed", "passport_proof_claim_denied"),
        ("cleanup_performed", "cleanup_claim_denied"),
        ("deletion_performed", "deletion_claim_denied"),
        ("fake_current_projection_created", "fake_current_projection_denied"),
        ("fake_source_truth_created", "fake_source_truth_denied"),
        ("fake_success_created", "fake_success_denied"),
        ("fake_verification_created", "fake_verification_denied"),
        ("evidence_provided_by_display", "display_cannot_provide_evidence"),
        ("verifier_success", "display_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
    ],
)
def test_authority_proof_run_cleanup_and_fake_success_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("repo_read_performed", "repo_read_denied"),
        ("repo_scan_performed", "repo_scan_denied"),
        ("directory_scan_performed", "directory_scan_denied"),
        ("file_list_performed", "file_list_denied"),
        ("file_stat_performed", "file_stat_denied"),
        ("file_hash_performed", "file_hash_denied"),
        ("file_read_performed", "file_read_denied"),
        ("github_api_called", "github_api_call_denied"),
        ("github_url_fetched", "github_url_fetch_denied"),
        ("browser_fetch_performed", "browser_fetch_denied"),
        ("raw_file_fetch_performed", "raw_file_fetch_denied"),
        ("git_clone_performed", "git_clone_denied"),
        ("http_request_performed", "http_request_denied"),
        ("external_api_called", "external_api_call_denied"),
        ("model_call_performed", "model_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("context_package_created", "context_package_creation_denied"),
        ("cache_written", "cache_write_denied"),
        ("source_record_created", "source_record_creation_denied"),
        ("citation_record_created", "citation_record_creation_denied"),
        ("report_generated", "report_generation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("runtime_state_mutated", "runtime_state_mutation_denied"),
        ("journal_mutated", "journal_mutation_denied"),
        ("evidence_mutated", "evidence_mutation_denied"),
        ("replay_mutated", "replay_mutation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_execution_source_access_context_report_and_mutation_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("display_severity_is_backend_truth", "display_backend_truth_claim_denied"),
        ("candidate_source_is_verified", "candidate_source_verification_claim_denied"),
        ("exclusion_is_cleanup_or_deletion", "exclusion_cleanup_claim_denied"),
        ("blocker_is_permission", "blocker_permission_claim_denied"),
        ("future_gated_is_execution_ready", "future_gated_execution_ready_claim_denied"),
        ("operator_review_is_run_authorization", "operator_review_run_authorization_denied"),
    ],
)
def test_specific_truthfulness_overclaims_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(_request(**{field: True}))

    _assert_blocked(decision, reason)


def test_execution_permission_grant_is_rejected() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(execution_permission="granted_by_display")
    )

    _assert_blocked(decision, "execution_permission_claim_denied")


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_repo_audit_dry_run_surface_display_request(
        request,
        repo_audit_dry_run_source_plan_decision=related,
    )

    assert request == request_before
    assert related.__dict__ == related_before
    assert decision.display_input is not None
    with pytest.raises(FrozenInstanceError):
        decision.display_input.limitations = ("mutated",)  # type: ignore[misc]


def test_non_mapping_request_blocks_without_side_effects() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(None)

    _assert_blocked(decision, "missing_request")
    assert decision.display_input is None


def test_output_never_sets_source_run_report_or_authority_flags_even_when_blocked() -> None:
    decision = validate_repo_audit_dry_run_surface_display_request(
        _request(
            repo_read_performed=True,
            github_api_called=True,
            report_generated=True,
            source_truth_claimed=True,
            run_authorized=True,
        )
    )

    assert decision.display_readiness_status.startswith("blocked_by_")
    _assert_non_authority(decision)
