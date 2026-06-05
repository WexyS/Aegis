from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_dry_run_source_plan import (
    REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION,
    REPO_AUDIT_DRY_RUN_SOURCE_PLAN_VERSION,
    validate_repo_audit_dry_run_source_plan_request,
)


FULL_EXCLUSIONS = [
    "secrets_excluded",
    "credentials_excluded",
    "env_files_excluded",
    "private_keys_excluded",
    "generated_artifacts_excluded",
    "build_outputs_excluded",
    "dependency_vendor_dirs_excluded",
    "model_files_excluded",
    "vector_db_files_excluded",
    "runtime_journals_excluded",
    "raw_evidence_files_excluded",
]


def _candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "ref_id": "github:WexyS/Aegis",
        "source_kind": "github_repository",
        "disposition": "include_candidate_metadata_only",
        "privacy_class": "public_metadata",
        "trust_class": "github_connector_candidate",
        "freshness_class": "commit_pinned",
        "scope_class": "repository_metadata_only",
        "reason": "synthetic metadata candidate",
    }
    candidate.update(overrides)
    return candidate


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-dry-run-source-plan:aegis:1",
        "dry_run_plan_class": "github_repo_source_plan",
        "plan_operation": "classify_dry_run_plan",
        "plan_status_class": "dry_run_ready",
        "projection_completeness_class": "complete_for_supplied_metadata",
        "privacy_class": "public_metadata",
        "trust_class": "github_connector_candidate",
        "freshness_class": "commit_pinned",
        "namespace": "repo_audit_dry_run_source_plan",
        "source_refs": [{"ref_id": "github:WexyS/Aegis", "kind": "synthetic_source_ref"}],
        "provenance": [{"ref_id": "caller:test", "kind": "synthetic_fixture"}],
        "candidate_sources": [_candidate()],
        "exclusion_classes": FULL_EXCLUSIONS,
        "limitations": ["dry-run metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION,
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
        evidence_provided_by_dry_run_plan=False,
        verifier_success=False,
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
        report_generated=False,
        generated_artifact_created=False,
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
    assert decision.execution_permission == REPO_AUDIT_DRY_RUN_SOURCE_PLAN_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_dry_run_plan is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
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
    assert decision.report_generated is False
    assert decision.generated_artifact_created is False
    assert decision.data_sent_external is False
    assert decision.private_repo_access_allowed is False
    assert decision.raw_content_ingestion_allowed is False
    assert decision.source_truth_claimed is False
    assert decision.repo_audit_proof_claimed is False
    assert decision.compliance_proof_claimed is False
    assert decision.passport_proof_claimed is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def test_valid_github_public_repo_dry_run_source_plan_is_metadata_only() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request())

    assert decision.contract_version == REPO_AUDIT_DRY_RUN_SOURCE_PLAN_VERSION
    assert decision.dry_run_status == "dry_run_ready"
    assert decision.plan_projection_status == "dry_run_projection_only"
    assert decision.candidate_projection_status == "candidate_dispositions_preserved"
    assert decision.included_candidate_count == 1
    assert decision.trust_status == "source_candidate_not_truth"
    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    _assert_non_authority(decision)


def test_valid_readme_candidate_is_included_as_metadata_only_candidate() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(
            dry_run_plan_class="github_file_source_plan",
            candidate_sources=[_candidate(source_kind="github_file", scope_class="readme_candidate")],
        )
    )

    assert decision.included_candidate_count == 1
    assert decision.file_read_performed is False
    assert decision.raw_content_ingestion_allowed is False


def test_dependency_manifest_candidate_remains_future_read_plan_candidate_only() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(
            dry_run_plan_class="package_dependency_plan",
            trust_class="repo_audit_read_plan_candidate",
            candidate_sources=[_candidate(scope_class="dependency_manifest_candidate", trust_class="repo_audit_read_plan_candidate")],
        )
    )

    assert decision.trust_status == "read_plan_candidate_not_read_permission"
    assert decision.repo_scan_performed is False


def test_selected_file_candidate_remains_not_read_dry_run_candidate() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(
            dry_run_plan_class="github_file_source_plan",
            candidate_sources=[_candidate(source_kind="github_file", scope_class="selected_path_candidate")],
        )
    )

    assert decision.local_repo_read_performed is False
    assert decision.file_list_performed is False
    assert decision.file_read_performed is False


def test_security_advisory_source_plan_preserves_trust_and_freshness_metadata() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(
            dry_run_plan_class="security_advisory_plan",
            trust_class="web_gateway_candidate",
            freshness_class="current_required",
            candidate_sources=[_candidate(source_kind="github_security_advisory", trust_class="web_gateway_candidate", freshness_class="current_required")],
        )
    )

    assert decision.dry_run_status == "dry_run_ready"
    assert decision.freshness_status == "freshness_requirement_preserved"
    assert decision.evidence_provided_by_dry_run_plan is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("dry_run_plan_class", "missing_dry_run_plan_class"),
        ("plan_operation", "missing_plan_operation"),
        ("plan_status_class", "missing_plan_status_class"),
        ("projection_completeness_class", "missing_projection_completeness_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(**{field: None}))

    assert decision.dry_run_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(source_refs=[], provenance=[]))

    assert decision.dry_run_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


def test_missing_candidate_source_metadata_blocks() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(candidate_sources=[]))

    assert decision.dry_run_status == "blocked_by_missing_required_field"
    assert "missing_candidate_source_metadata" in decision.failure_reasons


def test_missing_exclusion_policy_metadata_blocks() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(exclusion_classes=[]))

    assert decision.dry_run_status == "blocked_by_missing_required_field"
    assert "missing_exclusion_policy" in decision.failure_reasons


def test_private_repo_metadata_requires_identity_scope() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(privacy_class="private_repo_metadata"))

    assert "missing_identity_scope" in decision.failure_reasons
    assert decision.private_repo_access_allowed is False


def test_private_repo_content_blocks_dry_run_handoff_without_future_policy() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(privacy_class="private_repo_content"),
        identity_scope_decision=_related(scope_status="scope_ready"),
    )

    assert decision.dry_run_status == "blocked_by_privacy_or_exclusion"
    assert "private_repo_content_projection_blocked" in decision.failure_reasons


@pytest.mark.parametrize("privacy_class", ["secret_like", "credential_like"])
def test_secret_and_credential_candidates_block(privacy_class: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(privacy_class=privacy_class))

    assert decision.dry_run_status == "blocked_by_privacy_or_exclusion"
    assert "secret_or_credential_candidate_blocked" in decision.failure_reasons


@pytest.mark.parametrize(
    ("disposition", "reason"),
    [
        ("exclude_secret_like", "candidate_exclude_secret_like_blocked"),
        ("exclude_credential_like", "candidate_exclude_credential_like_blocked"),
    ],
)
def test_env_private_key_secret_candidate_scopes_block_through_disposition(disposition: str, reason: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(candidate_sources=[_candidate(disposition=disposition)]))

    assert decision.dry_run_status == "blocked_by_privacy_or_exclusion"
    assert reason in decision.failure_reasons


def test_unknown_privacy_blocks_source_plan_readiness() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(privacy_class="unknown"))

    assert "unknown_privacy_blocks_dry_run_plan" in decision.failure_reasons
    assert decision.data_sent_external is False


def test_internal_repo_future_remains_future_gated() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(
            dry_run_plan_class="local_clone_future_plan",
            plan_operation="project_future_execution_gates",
            plan_status_class="future_gated",
            privacy_class="internal_repo_future",
            candidate_sources=[_candidate(disposition="future_gated", privacy_class="internal_repo_future")],
        ),
        identity_scope_decision=_related(scope_status="scope_ready"),
    )

    assert decision.dry_run_status == "dry_run_future_gated"
    assert decision.future_gated is True
    assert decision.future_gated_candidate_count == 1


def test_public_source_candidate_does_not_allow_raw_content_ingestion() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(raw_content_requested=True))

    assert "raw_content_request_blocked" in decision.failure_reasons
    assert decision.raw_content_ingestion_allowed is False


@pytest.mark.parametrize(
    ("disposition", "expected_count_field"),
    [
        ("exclude_generated", "excluded_candidate_count"),
        ("exclude_build_output", "excluded_candidate_count"),
        ("exclude_vendor_dependency", "excluded_candidate_count"),
        ("exclude_model_or_vector_artifact", "excluded_candidate_count"),
        ("exclude_runtime_journal", "excluded_candidate_count"),
        ("exclude_raw_evidence", "excluded_candidate_count"),
    ],
)
def test_excluded_candidate_dispositions_are_preserved(disposition: str, expected_count_field: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(candidate_sources=[_candidate(disposition=disposition)]))

    assert decision.dry_run_status == "dry_run_ready"
    assert getattr(decision, expected_count_field) == 1
    assert decision.file_read_performed is False


def test_dependency_manifest_candidate_is_metadata_only() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(candidate_sources=[_candidate(scope_class="dependency_manifest_candidate")])
    )

    assert decision.included_candidate_count == 1
    assert decision.context_package_created is False


def test_selected_path_candidate_is_not_read_now() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(candidate_sources=[_candidate(scope_class="selected_path_candidate")])
    )

    assert decision.file_list_performed is False
    assert decision.file_stat_performed is False
    assert decision.file_hash_performed is False
    assert decision.file_read_performed is False


def test_branch_floating_is_not_pinned() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(freshness_class="branch_floating"))

    assert decision.dry_run_status == "dry_run_requires_operator_review"
    assert decision.freshness_status == "floating_branch_not_pinned"


def test_commit_pinned_is_stronger_metadata_but_not_proof() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(freshness_class="commit_pinned"))

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.repo_audit_proof_claimed is False


def test_bounded_metadata_cannot_claim_complete_repo_source_plan() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(projection_completeness_class="bounded_metadata_only", complete_repo_plan_claimed=True)
    )

    assert decision.dry_run_status == "blocked_by_policy"
    assert "bounded_metadata_cannot_claim_complete_repo_plan" in decision.failure_reasons


def test_stale_source_remains_stale() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(projection_completeness_class="stale", freshness_class="stale")
    )

    assert decision.completeness_status == "stale_projection_preserved"
    assert decision.freshness_status == "stale_metadata_preserved"


def test_source_ref_is_not_evidence_or_verifier_success() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request())

    assert decision.evidence_provided_by_dry_run_plan is False
    assert decision.verifier_success is False
    assert decision.source_truth_claimed is False


def test_repo_audit_read_plan_candidate_is_not_repo_read_permission() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(trust_class="repo_audit_read_plan_candidate")
    )

    assert decision.trust_status == "read_plan_candidate_not_read_permission"
    assert decision.local_repo_read_performed is False


@pytest.mark.parametrize(
    "trust_class",
    [
        "user_supplied_low_trust",
        "frontend_supplied_low_trust",
        "model_output_low_trust",
        "mcp_output_low_trust",
        "tool_output_low_trust",
    ],
)
def test_user_frontend_model_mcp_tool_metadata_is_low_trust(trust_class: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(trust_class=trust_class))

    assert decision.dry_run_status == "dry_run_requires_operator_review"
    assert decision.lower_trust_source is True
    assert decision.trust_status == "low_trust_metadata_candidate"


def test_source_candidate_is_not_compliance_or_passport_proof() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request())

    assert decision.compliance_proof_claimed is False
    assert decision.passport_proof_claimed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
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
        ("report_generated", "report_generation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_fetch_read_list_stat_hash_context_model_report_and_transfer_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(**{field: True}))

    assert decision.dry_run_status == "blocked_by_execution_claim"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("private_repo_access_allowed", "private_repo_access_permission_denied"),
        ("raw_content_ingestion_allowed", "raw_content_ingestion_denied"),
        ("source_truth_claimed", "source_truth_claim_denied"),
        ("repo_audit_proof_claimed", "repo_audit_proof_claim_denied"),
        ("compliance_proof_claimed", "compliance_proof_claim_denied"),
        ("passport_proof_claimed", "passport_proof_claim_denied"),
        ("evidence_provided_by_dry_run_plan", "dry_run_plan_cannot_provide_evidence"),
        ("verifier_success", "dry_run_plan_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_authority_permission_truth_proof_evidence_and_grant_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(execution_permission="granted_by_dry_run_plan"))

    assert decision.dry_run_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("repo_audit_source_intake_decision", _related(local_repo_read_performed=True)),
        ("github_source_connector_decision", _related(github_api_called=True)),
        ("web_research_gateway_decision", _related(web_query_performed=True)),
        ("context_policy_decision", _related(data_sent_external=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(runtime_dispatch_allowed=True)),
        ("local_model_context_profile_decision", _related(model_call_performed=True)),
        ("repo_audit_decision", _related(file_read_performed=True)),
        ("capability_lease_decision", _related(private_repo_access_allowed=True)),
        ("compliance_evidence_decision", _related(compliance_proof_claimed=True)),
        ("developer_work_passport_decision", _related(passport_proof_claimed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(mcp_call_performed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(), **{related_name: related_value})

    assert decision.dry_run_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(
        _request(),
        repo_audit_source_intake_decision=_related(intake_status="source_intake_ready_metadata_only"),
        github_source_connector_decision=_related(connector_status="source_candidate_ready"),
        context_policy_decision=_related(policy_status="context_policy_ready"),
        repo_audit_decision=_related(read_plan_status="plan_ready"),
    )

    assert len(decision.related_references) == 4
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False


def test_memory_derived_source_plan_requires_memory_governance() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(memory_derived_context=True))

    assert "missing_memory_governance" in decision.failure_reasons
    assert decision.memory_retrieval_performed is False


def test_project_repository_scoped_plan_requires_identity_scope() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request(project_or_repository_scoped=True))

    assert "missing_identity_scope" in decision.failure_reasons


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(candidate_sources=[_candidate(ref_id="source", reason="before")])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_repo_audit_dry_run_source_plan_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.plan_input.request_id = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection() -> None:
    decision = validate_repo_audit_dry_run_source_plan_request(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
