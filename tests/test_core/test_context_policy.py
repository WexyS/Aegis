from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.context_policy import (
    CONTEXT_POLICY_EXECUTION_PERMISSION,
    CONTEXT_POLICY_VERSION,
    validate_context_policy_request,
)
from aegis.core.identity_scope import validate_identity_scope_request
from aegis.core.memory_governance import validate_memory_governance_request


def _budget(**overrides: object) -> dict[str, object]:
    budget: dict[str, object] = {
        "max_context_tokens": 8192,
        "recommended_context_tokens": 2048,
        "reserved_system_tokens": 512,
        "reserved_instruction_tokens": 512,
        "reserved_response_tokens": 1024,
        "max_source_count": 8,
        "max_chunk_count": 32,
        "max_chunk_tokens": 512,
        "max_memory_items": 4,
        "max_evidence_refs": 8,
        "allow_raw_content": False,
        "allow_summaries": True,
        "allow_source_refs_only": True,
        "requires_redaction": False,
        "requires_citation": True,
        "requires_freshness_check": True,
        "requires_provenance": True,
        "requires_human_review": False,
    }
    budget.update(overrides)
    return budget


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "context-policy:aegis:1",
        "context_source_category": "public_docs",
        "context_operation": "classify_context",
        "privacy_class": "public",
        "provider_target_class": "passive_backend_only",
        "namespace": "context_policy",
        "project_ref": "project:aegis",
        "repository_ref": "repo:WexyS/Aegis",
        "source_refs": [{"ref_id": "docs:readme", "ref_type": "doc"}],
        "provenance": [{"ref_id": "caller:supplied", "ref_type": "synthetic_fixture"}],
        "budget_policy": _budget(),
        "limitations": ["synthetic metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": CONTEXT_POLICY_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _identity_scope_ready() -> object:
    return validate_identity_scope_request(
        {
            "request_id": "identity:context:test",
            "subject_kind": "repository",
            "namespace": "context_policy",
            "privacy_class": "private_repo",
            "data_boundary": "private_repo_local_only",
            "persistence_scope": "project_scoped",
            "project_ref": "project:aegis",
            "repository_ref": "repo:WexyS/Aegis",
            "session_ref": "session:test",
        }
    )


def _memory_governance_ready() -> object:
    return validate_memory_governance_request(
        {
            "request_id": "memory:context:test",
            "memory_category": "repo_memory",
            "memory_status": "proposed",
            "memory_scope": "repository_scoped",
            "operation": "propose_retrieve",
            "namespace": "context_policy",
            "project_ref": "project:aegis",
            "repository_ref": "repo:WexyS/Aegis",
            "session_ref": "session:test",
            "privacy_class": "private",
            "sensitivity_class": "private",
            "retention_policy": "project_ttl",
            "source_refs": [{"ref_id": "memory:source", "ref_type": "synthetic_fixture"}],
        },
        identity_scope_decision=_identity_scope_ready(),
    )


def _safe_related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        authority=False,
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_context_policy=False,
        verifier_success=False,
        provider_selected=False,
        context_retrieval_performed=False,
        model_call_performed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == CONTEXT_POLICY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_context_policy is False
    assert decision.verifier_success is False
    assert decision.frontend_authority is False
    assert decision.context_retrieval_performed is False
    assert decision.context_package_created is False
    assert decision.memory_retrieval_performed is False
    assert decision.repo_file_read_performed is False
    assert decision.web_query_performed is False
    assert decision.document_parse_performed is False
    assert decision.vector_index_touched is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.model_call_performed is False
    assert decision.cloud_sync_performed is False
    assert decision.data_sent_external is False
    assert decision.provider_selected is False
    assert decision.cloud_routing_allowed is False
    assert decision.local_model_routing_allowed is False
    assert decision.memory_context_allowed is False
    assert decision.raw_journal_allowed is False
    assert decision.raw_evidence_allowed is False
    assert decision.secret_context_allowed is False


def test_valid_public_docs_context_classification_is_metadata_only() -> None:
    decision = validate_context_policy_request(_request())

    assert decision.contract_version == CONTEXT_POLICY_VERSION
    assert decision.policy_status == "metadata_ready"
    assert decision.provider_target_status == "metadata_only"
    assert decision.budget_status == "metadata_ready"
    assert decision.source_delivery_mode == "summary_candidate"
    assert decision.failure_reasons == ()
    _assert_non_authority(decision)


def test_private_repo_context_requires_identity_scope() -> None:
    blocked = validate_context_policy_request(
        _request(
            context_source_category="private_repo_code",
            context_operation="propose_context_package",
            privacy_class="private_repo",
            provider_target_class="local_model_candidate",
        )
    )
    ready = validate_context_policy_request(
        _request(
            context_source_category="private_repo_code",
            context_operation="propose_context_package",
            privacy_class="private_repo",
            provider_target_class="local_model_candidate",
            budget_policy=_budget(requires_redaction=True),
        ),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert blocked.policy_status == "blocked_by_missing_identity_scope"
    assert "missing_identity_scope" in blocked.failure_reasons
    assert ready.policy_status == "proposal_ready"
    assert ready.provider_target_status == "proposal_only"
    assert ready.redaction_required is True
    assert ready.provider_selected is False
    _assert_non_authority(ready)


def test_memory_refs_context_requires_memory_governance_and_identity_scope() -> None:
    missing_memory = validate_context_policy_request(
        _request(
            context_source_category="memory_refs",
            context_operation="propose_memory_retrieval_future",
            privacy_class="private",
            provider_target_class="passive_backend_only",
        ),
        identity_scope_decision=_identity_scope_ready(),
    )
    ready = validate_context_policy_request(
        _request(
            context_source_category="memory_refs",
            context_operation="propose_memory_retrieval_future",
            privacy_class="private",
            provider_target_class="passive_backend_only",
            human_review_required=True,
        ),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
    )

    assert missing_memory.policy_status == "blocked_by_missing_memory_governance"
    assert "missing_memory_governance" in missing_memory.failure_reasons
    assert ready.policy_status == "future_gated"
    assert ready.memory_context_allowed is False
    assert ready.memory_retrieval_performed is False
    _assert_non_authority(ready)


@pytest.mark.parametrize(
    ("field", "expected_reason"),
    [
        ("context_source_category", "missing_context_source_category"),
        ("context_operation", "missing_context_operation"),
        ("privacy_class", "missing_privacy_class"),
        ("namespace", "missing_namespace"),
    ],
)
def test_missing_required_context_fields_block(field: str, expected_reason: str) -> None:
    decision = validate_context_policy_request(_request(**{field: None}))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_durable_reference_context_without_source_refs_or_provenance_blocks() -> None:
    decision = validate_context_policy_request(_request(source_refs=[], provenance=[]))

    assert decision.policy_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("source", "privacy", "expected_reason"),
    [
        ("secrets_or_tokens", "private", "secret_context_blocked"),
        ("public_docs", "credential_like", "secret_context_blocked"),
        ("public_docs", "secret_like", "secret_context_blocked"),
    ],
)
def test_secret_and_credential_context_is_blocked(
    source: str,
    privacy: str,
    expected_reason: str,
) -> None:
    decision = validate_context_policy_request(
        _request(context_source_category=source, privacy_class=privacy)
    )

    assert decision.policy_status == "blocked_by_secret_policy"
    assert expected_reason in decision.failure_reasons
    assert decision.secret_context_allowed is False


def test_unknown_sensitivity_blocks_cloud_provider_routing() -> None:
    decision = validate_context_policy_request(
        _request(
            privacy_class="unknown",
            provider_target_class="cloud_model_candidate_later",
            human_review_required=True,
        )
    )

    assert "unknown_sensitivity_blocks_provider_routing" in decision.failure_reasons
    assert decision.provider_selected is False
    assert decision.data_sent_external is False


def test_raw_journal_is_blocked_by_default() -> None:
    decision = validate_context_policy_request(
        _request(context_source_category="raw_journal", privacy_class="private")
    )

    assert decision.policy_status == "blocked_by_raw_journal_policy"
    assert "raw_journal_blocked_by_default" in decision.failure_reasons
    assert decision.raw_journal_allowed is False


def test_raw_evidence_is_blocked_unless_refs_only_policy_is_used() -> None:
    blocked = validate_context_policy_request(
        _request(
            context_source_category="raw_evidence",
            privacy_class="internal",
            budget_policy=_budget(allow_raw_content=True, allow_source_refs_only=False),
        )
    )
    refs_only = validate_context_policy_request(
        _request(context_source_category="raw_evidence", privacy_class="internal")
    )

    assert blocked.policy_status == "blocked_by_raw_evidence_policy"
    assert "raw_evidence_blocked_by_default" in blocked.failure_reasons
    assert refs_only.policy_status == "metadata_ready"
    assert refs_only.source_delivery_mode == "refs_only"
    assert refs_only.raw_evidence_allowed is False


def test_evidence_refs_are_refs_only_metadata_not_evidence() -> None:
    decision = validate_context_policy_request(
        _request(context_source_category="evidence_refs", privacy_class="internal")
    )

    assert decision.policy_status == "metadata_ready"
    assert decision.source_delivery_mode == "refs_only"
    assert decision.evidence_provided_by_context_policy is False
    assert decision.verifier_success is False


def test_private_repo_code_cannot_target_cloud_model_candidate() -> None:
    decision = validate_context_policy_request(
        _request(
            context_source_category="private_repo_code",
            context_operation="propose_context_package",
            privacy_class="private_repo",
            provider_target_class="cloud_model_candidate_later",
        ),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert "private_repo_context_to_cloud_denied" in decision.failure_reasons
    assert decision.data_sent_external is False
    assert decision.cloud_routing_allowed is False


@pytest.mark.parametrize("target", ["passive_backend_only", "local_model_candidate"])
def test_private_repo_code_can_be_proposed_passive_or_local_only_not_routed(target: str) -> None:
    decision = validate_context_policy_request(
        _request(
            context_source_category="private_repo_code",
            context_operation="propose_context_package",
            privacy_class="private_repo",
            provider_target_class=target,
            budget_policy=_budget(requires_redaction=True),
        ),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.policy_status == "proposal_ready"
    assert decision.provider_selected is False
    assert decision.local_model_routing_allowed is False
    assert decision.redaction_required is True
    _assert_non_authority(decision)


@pytest.mark.parametrize("source", ["user_memory", "project_memory", "repo_memory"])
def test_memory_context_sources_require_memory_governance(source: str) -> None:
    decision = validate_context_policy_request(
        _request(context_source_category=source, privacy_class="private"),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.policy_status == "blocked_by_missing_memory_governance"
    assert "missing_memory_governance" in decision.failure_reasons


def test_frontend_supplied_context_is_lower_trust_and_cannot_be_authority() -> None:
    decision = validate_context_policy_request(
        _request(
            context_source_category="frontend_supplied_context",
            authority=True,
        )
    )

    assert decision.lower_trust_source is True
    assert decision.policy_status == "blocked_by_authority_claim"
    assert "authority_must_be_false" in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("source", "claim", "reason"),
    [
        ("mcp_output", "mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output", "tool_output_is_truth", "tool_output_truth_claim_denied"),
        ("web_search_result_future", "web_output_is_truth", "web_output_truth_claim_denied"),
        ("external_agent_output_future", "external_agent_output_is_truth", "external_agent_output_truth_claim_denied"),
        ("public_docs", "model_output_is_truth", "model_output_truth_claim_denied"),
    ],
)
def test_lower_trust_outputs_cannot_be_truth(source: str, claim: str, reason: str) -> None:
    decision = validate_context_policy_request(
        _request(context_source_category=source, **{claim: True})
    )

    assert reason in decision.failure_reasons
    assert decision.verifier_success is False


def test_budget_metadata_does_not_authorize_model_retrieval_or_cloud_routing() -> None:
    decision = validate_context_policy_request(
        _request(
            context_operation="propose_context_budget",
            provider_target_class="local_model_candidate",
            budget_policy=_budget(max_context_tokens=128_000, recommended_context_tokens=16_000),
        )
    )

    assert decision.policy_status == "proposal_ready"
    assert decision.model_call_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.cloud_routing_allowed is False
    assert decision.provider_selected is False


def test_budget_excess_blocks() -> None:
    decision = validate_context_policy_request(
        _request(
            budget_policy=_budget(
                max_context_tokens=4096,
                recommended_context_tokens=4096,
                reserved_response_tokens=1024,
            )
        )
    )

    assert decision.policy_status == "blocked_by_budget_policy"
    assert "budget_constraints_exceeded" in decision.failure_reasons
    assert decision.budget_status == "blocked"


def test_private_context_sets_redaction_and_preserves_citation_provenance_requirements() -> None:
    decision = validate_context_policy_request(
        _request(
            context_source_category="project_config",
            privacy_class="private",
            budget_policy=_budget(requires_citation=True, requires_provenance=True),
        ),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.redaction_required is True
    assert decision.citation_required is True
    assert decision.provenance_required is True


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("identity_scope_decision", _safe_related(authority=True)),
        ("memory_governance_decision", _safe_related(memory_retrieval_performed=True)),
        ("policy_extension_decision", _safe_related(runtime_dispatch_allowed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_context_policy_request(_request(), **{related_name: related_value})

    assert decision.policy_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_blocked_policy_extension_decision_is_not_contradicted() -> None:
    decision = validate_context_policy_request(
        _request(),
        policy_extension_decision=SimpleNamespace(
            policy_outcome="blocked_by_policy",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_policy_extension",
        ),
    )

    assert decision.policy_status == "blocked_by_policy_extension"
    assert "policy_extension_not_ready" in decision.failure_reasons


def test_local_model_inventory_metadata_alone_does_not_authorize_context_delivery() -> None:
    decision = validate_context_policy_request(
        _request(
            context_operation="propose_provider_target",
            provider_target_class="local_model_candidate",
        ),
        local_model_inventory_decision=_safe_related(execution_permission="not_granted_by_local_model_inventory"),
    )

    assert decision.policy_status == "proposal_ready"
    assert decision.provider_target_status == "proposal_only"
    assert decision.provider_selected is False
    assert decision.local_model_routing_allowed is False


def test_absent_model_auto_mode_means_no_provider_selection() -> None:
    decision = validate_context_policy_request(
        _request(context_operation="propose_provider_target", provider_target_class="local_model_candidate")
    )

    assert decision.provider_selected is False
    assert decision.provider_target_status == "proposal_only"


def test_repo_audit_metadata_does_not_authorize_repo_file_reads() -> None:
    decision = validate_context_policy_request(
        _request(
            context_source_category="private_repo_code",
            context_operation="propose_repo_read_future",
            privacy_class="private_repo",
            provider_target_class="passive_backend_only",
        ),
        identity_scope_decision=_identity_scope_ready(),
        repo_audit_decision=_safe_related(execution_permission="not_granted_by_repo_audit_readiness"),
    )

    assert decision.policy_status == "future_gated"
    assert decision.repo_file_read_performed is False
    assert decision.context_retrieval_performed is False


def test_compliance_and_developer_passport_metadata_is_not_proof() -> None:
    decision = validate_context_policy_request(
        _request(),
        compliance_evidence_decision=_safe_related(proof=True),
        developer_work_passport_decision=_safe_related(certification_claim=True),
    )

    assert decision.policy_status == "blocked_by_unsafe_related_decision"
    assert "proof_claim_denied" in decision.failure_reasons
    assert "certification_claim_denied" in decision.failure_reasons
    assert decision.evidence_provided_by_context_policy is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("evidence_provided_by_context_policy", "context_policy_cannot_provide_evidence"),
        ("verifier_success", "context_policy_cannot_mark_verifier_success"),
        ("provider_selected", "provider_selection_not_allowed"),
        ("cloud_routing_allowed", "cloud_routing_not_allowed"),
        ("local_model_routing_allowed", "local_model_routing_not_allowed"),
        ("memory_context_allowed", "memory_context_permission_not_allowed"),
        ("raw_journal_allowed", "raw_journal_not_allowed"),
        ("raw_evidence_allowed", "raw_evidence_not_allowed"),
        ("secret_context_allowed", "secret_context_not_allowed"),
    ],
)
def test_context_policy_rejects_authority_permission_and_routing_claims(field: str, reason: str) -> None:
    decision = validate_context_policy_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("context_retrieval_performed", "context_retrieval_request_denied"),
        ("context_package_created", "context_package_creation_denied"),
        ("memory_retrieval_performed", "memory_retrieval_request_denied"),
        ("repo_file_read_performed", "repo_file_read_request_denied"),
        ("web_query_performed", "web_query_request_denied"),
        ("document_parse_performed", "document_parse_request_denied"),
        ("vector_index_touched", "vector_index_request_denied"),
        ("embedding_generated", "embedding_generation_request_denied"),
        ("reranking_performed", "reranking_request_denied"),
        ("model_call_performed", "model_call_request_denied"),
        ("cloud_sync_performed", "cloud_sync_request_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("api_call_performed", "api_call_request_denied"),
        ("mcp_call_performed", "mcp_call_request_denied"),
        ("tool_call_performed", "tool_call_request_denied"),
    ],
)
def test_context_policy_rejects_behavior_flags(field: str, reason: str) -> None:
    decision = validate_context_policy_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _safe_related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_context_policy_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.context_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_never_sets_dispatch_provider_external_or_retrieval_flags() -> None:
    decision = validate_context_policy_request(_request())

    _assert_non_authority(decision)
