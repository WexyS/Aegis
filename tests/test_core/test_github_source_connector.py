from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.github_source_connector import (
    GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION,
    GITHUB_SOURCE_CONNECTOR_VERSION,
    validate_github_source_connector_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "github-source:aegis:1",
        "github_object_class": "github_repository",
        "repository_visibility_class": "public_repository",
        "source_intent_class": "repo_overview",
        "access_method_class": "url_classification_only",
        "privacy_class": "public_metadata",
        "source_trust_class": "public_metadata_candidate",
        "freshness_class": "commit_pinned",
        "cache_policy_class": "source_ref_only",
        "namespace": "github_source_connector",
        "source_refs": [{"ref_id": "github:WexyS/Aegis", "url": "https://github.com/WexyS/Aegis"}],
        "provenance": [{"ref_id": "caller:test", "kind": "synthetic_fixture"}],
        "allowed_future_source_scopes": ["repository_metadata_only", "no_raw_content"],
        "blocked_source_scopes": [],
        "limitations": ["synthetic metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION,
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
        evidence_provided_by_github_source=False,
        verifier_success=False,
        github_api_called=False,
        github_url_fetched=False,
        browser_fetch_performed=False,
        raw_file_fetch_performed=False,
        git_clone_performed=False,
        local_repo_read_performed=False,
        repo_scan_performed=False,
        file_read_performed=False,
        mcp_call_performed=False,
        tool_call_performed=False,
        model_call_performed=False,
        web_query_performed=False,
        http_request_performed=False,
        external_api_called=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
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
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_github_source is False
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
    assert decision.mcp_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.model_call_performed is False
    assert decision.web_query_performed is False
    assert decision.http_request_performed is False
    assert decision.external_api_called is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
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
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def test_valid_public_repository_url_classification_is_proposal_only() -> None:
    decision = validate_github_source_connector_request(_request())

    assert decision.contract_version == GITHUB_SOURCE_CONNECTOR_VERSION
    assert decision.connector_status == "source_candidate_ready"
    assert decision.source_readiness_status == "url_classification_metadata_only"
    assert decision.source_trust_status == "source_ref_candidate_not_truth"
    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    _assert_non_authority(decision)


def test_public_readme_source_candidate_is_source_ref_only() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_file",
            source_intent_class="readme_review",
            source_trust_class="repository_content_candidate",
            allowed_future_source_scopes=["readme_candidate", "no_raw_content"],
            cache_policy_class="source_ref_only",
        )
    )

    assert decision.connector_status == "source_candidate_ready"
    assert decision.raw_content_status == "raw_content_prohibited"
    assert decision.file_read_performed is False
    assert decision.source_truth_claimed is False


def test_public_issue_metadata_candidate_remains_low_trust_user_generated() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_issue",
            source_intent_class="issue_triage",
            source_trust_class="issue_or_pr_discussion_low_trust",
            freshness_class="branch_floating",
            allowed_future_source_scopes=["issue_metadata_candidate", "no_raw_content"],
        )
    )

    assert decision.connector_status == "source_candidate_requires_human_review"
    assert decision.lower_trust_source is True
    assert decision.source_trust_status == "low_trust_user_generated_candidate"
    assert decision.freshness_status == "floating_branch_not_pinned"


def test_release_notes_candidate_preserves_freshness_metadata() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_release",
            source_intent_class="release_notes_review",
            freshness_class="release_pinned",
            source_trust_class="official_github_metadata_candidate",
            allowed_future_source_scopes=["release_metadata_candidate", "no_raw_content"],
        )
    )

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.source_trust_status == "official_metadata_candidate_not_evidence"
    assert decision.verifier_success is False


def test_security_advisory_candidate_requires_high_source_quality_and_freshness() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_security_advisory",
            source_intent_class="security_static_notes",
            source_trust_class="official_github_metadata_candidate",
            freshness_class="current_required",
            allowed_future_source_scopes=["repository_metadata_only", "no_raw_content"],
        )
    )

    assert decision.connector_status == "source_candidate_ready"
    assert decision.freshness_status == "freshness_requirement_preserved"
    assert decision.source_trust_status == "official_metadata_candidate_not_evidence"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("github_object_class", "missing_github_object_class"),
        ("repository_visibility_class", "missing_repository_visibility_class"),
        ("source_intent_class", "missing_source_intent_class"),
        ("access_method_class", "missing_access_method_class"),
        ("privacy_class", "missing_privacy_class"),
        ("source_trust_class", "missing_source_trust_class"),
        ("freshness_class", "missing_freshness_class"),
        ("cache_policy_class", "missing_cache_policy_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_github_source_connector_request(_request(**{field: None}))

    assert decision.connector_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_github_source_connector_request(_request(source_refs=[], provenance=[]))

    assert decision.connector_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize("access_method", ["github_api_future", "browser_fetch_future", "raw_file_fetch_future", "git_clone_future", "mcp_github_future"])
def test_private_repository_blocks_fetch_api_clone_candidates(access_method: str) -> None:
    decision = validate_github_source_connector_request(
        _request(
            repository_visibility_class="private_repository",
            privacy_class="private_repo_content",
            access_method_class=access_method,
            cache_policy_class="raw_content_cache_prohibited" if access_method == "raw_file_fetch_future" else "no_cache",
        ),
        identity_scope_decision=_related(scope_status="scope_ready"),
    )

    assert decision.connector_status == "blocked_by_privacy_or_source_scope"
    assert "private_repository_access_blocked" in decision.failure_reasons
    _assert_non_authority(decision)


def test_private_repo_content_requires_future_policy_and_identity_scope() -> None:
    decision = validate_github_source_connector_request(
        _request(repository_visibility_class="private_repository", privacy_class="private_repo_content")
    )

    assert "missing_identity_scope" in decision.failure_reasons
    assert decision.private_repo_access_allowed is False


@pytest.mark.parametrize(
    ("privacy_class", "reason"),
    [
        ("secret_like", "secret_or_credential_source_blocked"),
        ("credential_like", "secret_or_credential_source_blocked"),
    ],
)
def test_secret_and_credential_privacy_block(privacy_class: str, reason: str) -> None:
    decision = validate_github_source_connector_request(_request(privacy_class=privacy_class))

    assert decision.connector_status == "blocked_by_privacy_or_source_scope"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize("blocked_scope", ["env_files", "private_keys", "secrets", "credentials"])
def test_env_private_key_secret_scopes_block(blocked_scope: str) -> None:
    decision = validate_github_source_connector_request(_request(blocked_source_scopes=[blocked_scope]))

    assert f"blocked_source_scope_{blocked_scope}" in decision.failure_reasons
    assert decision.connector_status == "blocked_by_privacy_or_source_scope"


def test_unknown_privacy_blocks_external_access() -> None:
    decision = validate_github_source_connector_request(
        _request(privacy_class="unknown", access_method_class="github_api_future")
    )

    assert "unknown_privacy_external_access_blocked" in decision.failure_reasons
    assert decision.github_api_called is False


def test_public_url_does_not_automatically_allow_raw_content_ingestion() -> None:
    decision = validate_github_source_connector_request(_request(raw_content_requested=True))

    assert "raw_content_request_blocked" in decision.failure_reasons
    assert decision.raw_content_ingestion_allowed is False


def test_archived_repository_is_marked_stale_or_archived() -> None:
    decision = validate_github_source_connector_request(
        _request(
            repository_visibility_class="archived_repository",
            source_trust_class="archived_or_stale",
            freshness_class="stale",
        )
    )

    assert decision.source_trust_status == "archived_or_stale_candidate"
    assert decision.freshness_status == "stale_metadata_preserved"


def test_deleted_unavailable_repository_blocks() -> None:
    decision = validate_github_source_connector_request(
        _request(repository_visibility_class="deleted_or_unavailable", source_trust_class="unavailable")
    )

    assert decision.connector_status == "blocked_by_privacy_or_source_scope"
    assert "source_unavailable" in decision.failure_reasons


@pytest.mark.parametrize(
    "blocked_scope",
    [
        "generated_artifacts",
        "build_outputs",
        "node_modules",
        "vendor_dependencies",
        "model_files",
        "vector_db_files",
        "runtime_journals",
        "raw_evidence_files",
    ],
)
def test_blocked_source_scopes_remain_blocked(blocked_scope: str) -> None:
    decision = validate_github_source_connector_request(_request(blocked_source_scopes=[blocked_scope]))

    assert f"blocked_source_scope_{blocked_scope}" in decision.failure_reasons
    assert decision.source_readiness_status == "blocked"


def test_dependency_manifests_are_candidate_metadata_only() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_file",
            source_intent_class="dependency_review",
            allowed_future_source_scopes=["dependency_manifest_candidate", "no_raw_content"],
        )
    )

    assert decision.connector_status == "source_candidate_ready"
    assert decision.file_read_performed is False
    assert decision.raw_content_ingestion_allowed is False


def test_selected_files_are_candidate_only_and_not_read_now() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_file",
            source_intent_class="architecture_review",
            allowed_future_source_scopes=["selected_file_candidate", "no_raw_content"],
        )
    )

    assert decision.source_readiness_status == "url_classification_metadata_only"
    assert decision.file_read_performed is False


def test_branch_floating_is_not_pinned() -> None:
    decision = validate_github_source_connector_request(_request(freshness_class="branch_floating"))

    assert decision.connector_status == "source_candidate_requires_human_review"
    assert decision.freshness_status == "floating_branch_not_pinned"


def test_commit_pinned_is_stronger_metadata_but_not_proof() -> None:
    decision = validate_github_source_connector_request(_request(freshness_class="commit_pinned"))

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.repo_audit_proof_claimed is False


@pytest.mark.parametrize("freshness_class", ["tag_pinned", "release_pinned"])
def test_tag_and_release_pinned_remain_candidates(freshness_class: str) -> None:
    decision = validate_github_source_connector_request(_request(freshness_class=freshness_class))

    assert decision.freshness_status == "pinned_metadata_candidate_not_proof"
    assert decision.evidence_provided_by_github_source is False


def test_issue_pr_discussion_remains_low_trust() -> None:
    decision = validate_github_source_connector_request(
        _request(github_object_class="github_pull_request", source_trust_class="user_generated_low_trust")
    )

    assert decision.lower_trust_source is True
    assert decision.source_trust_status == "low_trust_user_generated_candidate"


def test_github_metadata_is_candidate_not_evidence_or_verifier_success() -> None:
    decision = validate_github_source_connector_request(
        _request(source_trust_class="official_github_metadata_candidate")
    )

    assert decision.source_trust_status == "official_metadata_candidate_not_evidence"
    assert decision.evidence_provided_by_github_source is False
    assert decision.verifier_success is False


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
        ("file_read_performed", "file_read_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("model_call_performed", "model_call_denied"),
        ("web_query_performed", "web_query_denied"),
        ("http_request_performed", "http_request_denied"),
        ("external_api_called", "external_api_call_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("cache_written", "cache_write_denied"),
        ("source_record_created", "source_record_creation_denied"),
        ("citation_record_created", "citation_record_creation_denied"),
        ("report_generated", "report_generation_denied"),
        ("generated_artifact_created", "generated_artifact_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_network_fetch_clone_read_call_cache_record_and_transfer_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_github_source_connector_request(_request(**{field: True}))

    assert decision.connector_status == "blocked_by_execution_claim"
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
        ("evidence_provided_by_github_source", "github_source_cannot_provide_evidence"),
        ("verifier_success", "github_source_cannot_mark_verifier_success"),
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
    decision = validate_github_source_connector_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_github_source_connector_request(_request(execution_permission="granted_by_source_connector"))

    assert decision.connector_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("web_research_gateway_decision", _related(github_api_called=True)),
        ("context_policy_decision", _related(data_sent_external=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _related(runtime_dispatch_allowed=True)),
        ("local_model_context_profile_decision", _related(model_call_performed=True)),
        ("repo_audit_decision", _related(local_repo_read_performed=True)),
        ("capability_lease_decision", _related(private_repo_access_allowed=True)),
        ("compliance_evidence_decision", _related(proof=True)),
        ("developer_work_passport_decision", _related(repo_audit_proof_claimed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(mcp_call_performed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_github_source_connector_request(_request(), **{related_name: related_value})

    assert decision.connector_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_github_source_connector_request(
        _request(),
        web_research_gateway_decision=_related(readiness_status="research_plan_ready"),
        local_model_context_profile_decision=_related(profile_status="profile_candidate_ready"),
        context_policy_decision=_related(policy_status="context_policy_ready"),
        repo_audit_decision=_related(audit_status="candidate_ready"),
    )

    assert len(decision.related_references) == 4
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.github_api_called is False


def test_memory_derived_github_context_requires_memory_governance() -> None:
    decision = validate_github_source_connector_request(_request(memory_derived_context=True))

    assert "missing_memory_governance" in decision.failure_reasons
    assert decision.memory_retrieval_performed is False


def test_private_project_scoped_metadata_requires_identity_scope() -> None:
    decision = validate_github_source_connector_request(_request(project_or_repository_scoped=True))

    assert "missing_identity_scope" in decision.failure_reasons


def test_raw_file_future_is_future_gated_and_cache_prohibited_without_fetching() -> None:
    decision = validate_github_source_connector_request(
        _request(
            github_object_class="github_file",
            access_method_class="raw_file_fetch_future",
            cache_policy_class="raw_content_cache_prohibited",
            allowed_future_source_scopes=["selected_file_candidate", "no_raw_content"],
        )
    )

    assert decision.connector_status == "source_candidate_future_gated"
    assert decision.raw_content_status == "raw_fetch_future_gated_no_ingestion"
    assert decision.raw_file_fetch_performed is False


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "github:repo", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_github_source_connector_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.source_input.request_id = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection() -> None:
    decision = validate_github_source_connector_request(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
