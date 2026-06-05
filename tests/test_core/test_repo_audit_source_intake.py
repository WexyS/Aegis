from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_source_intake import (
    REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION,
    REPO_AUDIT_SOURCE_INTAKE_VERSION,
    validate_repo_audit_source_intake_request,
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


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-source-intake:aegis:1",
        "source_intake_class": "github_source_candidate",
        "source_intake_operation": "classify_source_intake",
        "repo_source_scope_class": "repository_metadata_only",
        "privacy_class": "public_metadata",
        "readiness_status_class": "intake_ready_metadata_only",
        "source_trust_class": "connector_metadata_candidate",
        "freshness_class": "commit_pinned",
        "namespace": "repo_audit_source_intake",
        "source_refs": [{"ref_id": "github:WexyS/Aegis", "kind": "synthetic_source_ref"}],
        "provenance": [{"ref_id": "caller:test", "kind": "synthetic_fixture"}],
        "exclusion_classes": FULL_EXCLUSIONS,
        "limitations": ["metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION,
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
        evidence_provided_by_source_intake=False,
        verifier_success=False,
        github_api_called=False,
        github_url_fetched=False,
        browser_fetch_performed=False,
        raw_file_fetch_performed=False,
        git_clone_performed=False,
        local_repo_read_performed=False,
        repo_scan_performed=False,
        file_read_performed=False,
        directory_scan_performed=False,
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
    assert decision.execution_permission == REPO_AUDIT_SOURCE_INTAKE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_source_intake is False
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
    assert decision.file_read_performed is False
    assert decision.directory_scan_performed is False
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


def test_valid_github_public_repo_source_candidate_is_metadata_only() -> None:
    decision = validate_repo_audit_source_intake_request(_request())

    assert decision.contract_version == REPO_AUDIT_SOURCE_INTAKE_VERSION
    assert decision.intake_status == "source_intake_ready_metadata_only"
    assert decision.source_handoff_status == "source_ref_handoff_metadata_only"
    assert decision.source_scope_status == "metadata_only"
    assert decision.source_trust_status == "source_ref_candidate_not_truth"
    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    _assert_non_authority(decision)


def test_public_readme_candidate_remains_source_ref_only() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(repo_source_scope_class="readme_candidate", source_intake_operation="propose_read_plan_link")
    )

    assert decision.intake_status == "source_intake_ready_metadata_only"
    assert decision.source_scope_status == "future_read_plan_candidate_only"
    assert decision.raw_content_ingestion_allowed is False
    assert decision.file_read_performed is False


def test_dependency_manifest_candidate_is_future_read_plan_candidate_only() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(
            source_intake_class="repo_audit_read_plan_candidate",
            repo_source_scope_class="dependency_manifest_candidate",
            source_trust_class="repo_audit_read_plan_candidate",
        )
    )

    assert decision.source_handoff_status == "read_plan_link_candidate_not_permission"
    assert decision.source_trust_status == "read_plan_candidate_not_read_permission"
    assert decision.repo_scan_performed is False


def test_release_metadata_candidate_preserves_freshness_metadata() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(
            source_intake_class="release_notes_source_candidate",
            repo_source_scope_class="release_metadata_candidate",
            freshness_class="tag_or_release_pinned",
        )
    )

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.evidence_provided_by_source_intake is False


def test_security_advisory_source_requires_trust_and_freshness_metadata() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(
            source_intake_class="security_advisory_source_candidate",
            repo_source_scope_class="advisory_metadata_candidate",
            source_trust_class="web_gateway_candidate",
            freshness_class="current_required",
        )
    )

    assert decision.intake_status == "source_intake_ready_metadata_only"
    assert decision.freshness_status == "freshness_requirement_preserved"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("source_intake_class", "missing_source_intake_class"),
        ("source_intake_operation", "missing_source_intake_operation"),
        ("repo_source_scope_class", "missing_repo_source_scope_class"),
        ("privacy_class", "missing_privacy_class"),
        ("readiness_status_class", "missing_readiness_status_class"),
        ("source_trust_class", "missing_source_trust_class"),
        ("freshness_class", "missing_freshness_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_intake_request(_request(**{field: None}))

    assert decision.intake_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_repo_audit_source_intake_request(_request(source_refs=[], provenance=[]))

    assert decision.intake_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


def test_missing_exclusions_for_future_read_candidate_blocks() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(repo_source_scope_class="source_file_candidate", exclusion_classes=[])
    )

    assert decision.intake_status == "blocked_by_missing_required_field"
    assert "missing_exclusion_policy" in decision.failure_reasons


def test_private_repo_metadata_requires_identity_scope() -> None:
    decision = validate_repo_audit_source_intake_request(_request(privacy_class="private_repo_metadata"))

    assert "missing_identity_scope" in decision.failure_reasons
    assert decision.private_repo_access_allowed is False


def test_private_repo_content_blocks_handoff_without_future_policy() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(privacy_class="private_repo_content"),
        identity_scope_decision=_related(scope_status="scope_ready"),
    )

    assert decision.intake_status == "blocked_by_privacy_or_source_scope"
    assert "private_repo_content_handoff_blocked" in decision.failure_reasons


@pytest.mark.parametrize("privacy_class", ["secret_like", "credential_like"])
def test_secret_and_credential_privacy_block(privacy_class: str) -> None:
    decision = validate_repo_audit_source_intake_request(_request(privacy_class=privacy_class))

    assert decision.intake_status == "blocked_by_privacy_or_source_scope"
    assert "secret_or_credential_source_blocked" in decision.failure_reasons


@pytest.mark.parametrize("scope_status", ["blocked_by_secret_scope", "blocked_by_unknown_scope"])
def test_blocked_readiness_statuses_remain_blocked(scope_status: str) -> None:
    decision = validate_repo_audit_source_intake_request(_request(readiness_status_class=scope_status))

    assert decision.intake_status == "blocked_by_privacy_or_source_scope"


def test_unknown_privacy_blocks_source_access() -> None:
    decision = validate_repo_audit_source_intake_request(_request(privacy_class="unknown"))

    assert "unknown_privacy_blocks_source_access" in decision.failure_reasons
    assert decision.data_sent_external is False


def test_public_source_does_not_allow_raw_content_ingestion() -> None:
    decision = validate_repo_audit_source_intake_request(_request(raw_content_requested=True))

    assert "raw_content_request_blocked" in decision.failure_reasons
    assert decision.raw_content_ingestion_allowed is False


def test_internal_repo_future_remains_future_gated() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(
            source_intake_class="local_clone_reference_future",
            source_intake_operation="propose_future_local_read_gate",
            privacy_class="internal_repo_future",
            readiness_status_class="future_gated",
        ),
        identity_scope_decision=_related(scope_status="scope_ready"),
    )

    assert decision.intake_status == "source_intake_future_gated"
    assert decision.future_gated is True


@pytest.mark.parametrize(
    "missing_exclusion",
    [
        "generated_artifacts_excluded",
        "build_outputs_excluded",
        "dependency_vendor_dirs_excluded",
        "model_files_excluded",
        "vector_db_files_excluded",
        "runtime_journals_excluded",
        "raw_evidence_files_excluded",
        "env_files_excluded",
        "private_keys_excluded",
    ],
)
def test_required_exclusions_must_be_present_for_future_read_candidates(missing_exclusion: str) -> None:
    exclusions = [item for item in FULL_EXCLUSIONS if item != missing_exclusion]
    decision = validate_repo_audit_source_intake_request(
        _request(repo_source_scope_class="selected_path_candidate", exclusion_classes=exclusions)
    )

    assert decision.intake_status == "blocked_by_privacy_or_source_scope"
    assert "incomplete_exclusion_policy" in decision.failure_reasons


def test_selected_path_candidate_is_not_read_now() -> None:
    decision = validate_repo_audit_source_intake_request(_request(repo_source_scope_class="selected_path_candidate"))

    assert decision.source_scope_status == "future_read_plan_candidate_only"
    assert decision.local_repo_read_performed is False
    assert decision.file_read_performed is False


def test_branch_floating_is_not_pinned() -> None:
    decision = validate_repo_audit_source_intake_request(_request(freshness_class="branch_floating"))

    assert decision.intake_status == "source_intake_requires_human_review"
    assert decision.freshness_status == "floating_branch_not_pinned"


def test_commit_pinned_is_stronger_metadata_but_not_proof() -> None:
    decision = validate_repo_audit_source_intake_request(_request(freshness_class="commit_pinned"))

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.repo_audit_proof_claimed is False


def test_source_ref_is_not_evidence_or_verifier_success() -> None:
    decision = validate_repo_audit_source_intake_request(_request())

    assert decision.evidence_provided_by_source_intake is False
    assert decision.verifier_success is False
    assert decision.source_truth_claimed is False


@pytest.mark.parametrize(
    "source_trust_class",
    [
        "user_supplied_low_trust",
        "frontend_supplied_low_trust",
        "model_output_low_trust",
        "mcp_output_low_trust",
        "tool_output_low_trust",
    ],
)
def test_user_frontend_model_mcp_tool_metadata_is_low_trust(source_trust_class: str) -> None:
    decision = validate_repo_audit_source_intake_request(_request(source_trust_class=source_trust_class))

    assert decision.intake_status == "source_intake_requires_human_review"
    assert decision.lower_trust_source is True
    assert decision.source_trust_status == "low_trust_metadata_candidate"


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
def test_fetch_read_context_model_report_and_transfer_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_repo_audit_source_intake_request(_request(**{field: True}))

    assert decision.intake_status == "blocked_by_execution_claim"
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
        ("evidence_provided_by_source_intake", "source_intake_cannot_provide_evidence"),
        ("verifier_success", "source_intake_cannot_mark_verifier_success"),
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
    decision = validate_repo_audit_source_intake_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_repo_audit_source_intake_request(_request(execution_permission="granted_by_source_intake"))

    assert decision.intake_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("github_source_connector_decision", _related(github_api_called=True)),
        ("web_research_gateway_decision", _related(web_query_performed=True)),
        ("context_policy_decision", _related(data_sent_external=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(runtime_dispatch_allowed=True)),
        ("local_model_context_profile_decision", _related(model_call_performed=True)),
        ("repo_audit_decision", _related(local_repo_read_performed=True)),
        ("capability_lease_decision", _related(private_repo_access_allowed=True)),
        ("compliance_evidence_decision", _related(compliance_proof_claimed=True)),
        ("developer_work_passport_decision", _related(passport_proof_claimed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(mcp_call_performed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_repo_audit_source_intake_request(_request(), **{related_name: related_value})

    assert decision.intake_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_repo_audit_source_intake_request(
        _request(),
        github_source_connector_decision=_related(connector_status="source_candidate_ready"),
        web_research_gateway_decision=_related(readiness_status="research_plan_ready"),
        context_policy_decision=_related(policy_status="context_policy_ready"),
        repo_audit_decision=_related(read_plan_status="plan_ready"),
    )

    assert len(decision.related_references) == 4
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False


def test_memory_derived_source_requires_memory_governance() -> None:
    decision = validate_repo_audit_source_intake_request(_request(memory_derived_context=True))

    assert "missing_memory_governance" in decision.failure_reasons
    assert decision.memory_retrieval_performed is False


def test_project_repository_scoped_source_requires_identity_scope() -> None:
    decision = validate_repo_audit_source_intake_request(_request(project_or_repository_scoped=True))

    assert "missing_identity_scope" in decision.failure_reasons


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_repo_audit_source_intake_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.source_input.request_id = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection() -> None:
    decision = validate_repo_audit_source_intake_request(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
