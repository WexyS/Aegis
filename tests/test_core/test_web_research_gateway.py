from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.web_research_gateway import (
    WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION,
    WEB_RESEARCH_GATEWAY_VERSION,
    validate_web_research_gateway_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "web-research:aegis:1",
        "research_subject": "official_docs_research",
        "research_operation": "propose_query_plan",
        "namespace": "web_research_gateway",
        "privacy_class": "public_query",
        "freshness_class": "stable_reference",
        "source_provider_class": "no_provider",
        "source_type_class": "official_primary_source",
        "source_quality_class": "high_authority",
        "cache_policy_class": "no_cache",
        "result_authority_class": "source_candidate_only",
        "research_risk_class": "info",
        "source_metadata_claimed": True,
        "source_refs": [{"ref_id": "source:official-docs", "ref_type": "synthetic_projection"}],
        "provenance": [{"ref_id": "caller:test", "ref_type": "synthetic_fixture"}],
        "limitations": ["planning metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION,
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
        evidence_provided_by_web_research=False,
        verifier_success=False,
        web_query_performed=False,
        browser_fetch_performed=False,
        search_api_called=False,
        http_request_performed=False,
        external_api_called=False,
        github_api_called=False,
        page_extract_performed=False,
        scraping_performed=False,
        model_call_performed=False,
        tool_call_performed=False,
        mcp_call_performed=False,
        memory_retrieval_performed=False,
        context_retrieval_performed=False,
        cache_written=False,
        source_record_created=False,
        citation_record_created=False,
        report_generated=False,
        generated_artifact_created=False,
        data_sent_external=False,
        private_query_leak_allowed=False,
        source_truth_claimed=False,
        synthesis_truth_claimed=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_web_research is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.web_query_performed is False
    assert decision.browser_fetch_performed is False
    assert decision.search_api_called is False
    assert decision.http_request_performed is False
    assert decision.external_api_called is False
    assert decision.github_api_called is False
    assert decision.page_extract_performed is False
    assert decision.scraping_performed is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.cache_written is False
    assert decision.source_record_created is False
    assert decision.citation_record_created is False
    assert decision.report_generated is False
    assert decision.generated_artifact_created is False
    assert decision.data_sent_external is False
    assert decision.private_query_leak_allowed is False
    assert decision.source_truth_claimed is False
    assert decision.synthesis_truth_claimed is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def test_valid_official_docs_query_plan_is_proposal_only_and_non_authoritative() -> None:
    decision = validate_web_research_gateway_request(_request())

    assert decision.contract_version == WEB_RESEARCH_GATEWAY_VERSION
    assert decision.readiness_status == "research_plan_ready"
    assert decision.source_quality_status == "high_authority_candidate"
    assert decision.result_authority_status == "source_candidate_only"
    _assert_non_authority(decision)


def test_security_advisory_research_requires_high_quality_and_freshness_metadata() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            research_subject="security_advisory_research",
            source_type_class="security_advisory",
            source_quality_class="high_authority",
            freshness_class="current_required",
            research_risk_class="high",
        )
    )

    assert decision.readiness_status == "research_plan_ready"
    assert decision.freshness_status == "freshness_requirement_preserved"
    assert decision.research_risk_class == "high"
    _assert_non_authority(decision)


def test_source_verification_preserves_citation_candidate_status() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            research_subject="source_verification_research",
            research_operation="propose_citation_plan",
            result_authority_class="citation_candidate_only",
            citation_required=True,
        )
    )

    assert decision.citation_status == "citation_candidate_only"
    assert decision.citation_record_created is False
    assert decision.verifier_success is False


def test_contradiction_check_preserves_contradiction_candidate_status() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            research_subject="contradiction_check_research",
            research_operation="propose_contradiction_check",
            source_quality_class="conflicting",
            result_authority_class="contradiction_candidate_only",
            contradiction_present=True,
        )
    )

    assert decision.readiness_status == "proposal_requires_human_review"
    assert decision.contradiction_handling_required is True
    assert decision.result_authority_status == "contradiction_candidate_only"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("research_subject", "missing_research_subject"),
        ("research_operation", "missing_research_operation"),
        ("namespace", "missing_namespace"),
        ("privacy_class", "missing_privacy_class"),
        ("freshness_class", "missing_freshness_class"),
        ("source_provider_class", "missing_source_provider_class"),
        ("cache_policy_class", "missing_cache_policy_class"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_web_research_gateway_request(_request(**{field: None}))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_claimed_source_metadata_without_source_refs_or_provenance_blocks() -> None:
    decision = validate_web_research_gateway_request(_request(source_refs=[], provenance=[]))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("research_subject", "not_research", "unsupported_research_subject"),
        ("research_operation", "search_now", "unsupported_research_operation"),
        ("privacy_class", "privateish", "unsupported_privacy_class"),
        ("freshness_class", "live", "unsupported_freshness_class"),
        ("source_provider_class", "google_now", "unsupported_source_provider_class"),
        ("source_type_class", "random", "unsupported_source_type_class"),
        ("source_quality_class", "certain", "unsupported_source_quality_class"),
        ("cache_policy_class", "write_cache", "unsupported_cache_policy_class"),
        ("result_authority_class", "truth", "unsupported_result_authority_class"),
    ],
)
def test_unsupported_taxonomy_values_block(field: str, value: str, reason: str) -> None:
    decision = validate_web_research_gateway_request(_request(**{field: value}))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize("privacy_class", ["private_user_context", "private_repo_context"])
def test_private_context_blocks_web_query_candidate(privacy_class: str) -> None:
    decision = validate_web_research_gateway_request(
        _request(
            privacy_class=privacy_class,
            source_provider_class="browser_search_future",
        ),
        identity_scope_decision=_related(scope_status="ready"),
    )

    assert decision.readiness_status == "blocked_by_privacy_policy"
    assert "private_context_external_query_blocked" in decision.failure_reasons
    assert decision.data_sent_external is False


def test_personal_private_requires_redaction_and_human_review() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            privacy_class="personal_private",
            source_provider_class="no_provider",
        ),
        identity_scope_decision=_related(scope_status="ready"),
    )

    assert decision.readiness_status == "proposal_requires_human_review"
    assert decision.redaction_required is True
    assert decision.human_review_required is True


def test_sensitive_context_requires_identity_and_context_policy() -> None:
    missing = validate_web_research_gateway_request(
        _request(privacy_class="sensitive", source_provider_class="no_provider")
    )
    ready = validate_web_research_gateway_request(
        _request(privacy_class="sensitive", source_provider_class="no_provider"),
        identity_scope_decision=_related(scope_status="ready"),
        context_policy_decision=_related(policy_status="proposal_ready"),
    )

    assert "missing_identity_scope" in missing.failure_reasons
    assert ready.readiness_status == "proposal_requires_human_review"
    assert ready.redaction_required is True


@pytest.mark.parametrize("privacy_class", ["secret_like", "credential_like"])
def test_secret_and_credential_context_blocks(privacy_class: str) -> None:
    decision = validate_web_research_gateway_request(_request(privacy_class=privacy_class))

    assert decision.readiness_status == "blocked_by_privacy_policy"
    assert "secret_or_credential_query_blocked" in decision.failure_reasons
    assert decision.private_query_leak_allowed is False


def test_unknown_privacy_blocks_external_query() -> None:
    decision = validate_web_research_gateway_request(
        _request(privacy_class="unknown", source_provider_class="general_search_api_future")
    )

    assert decision.readiness_status == "blocked_by_privacy_policy"
    assert "unknown_privacy_external_query_blocked" in decision.failure_reasons


def test_memory_derived_context_requires_memory_governance() -> None:
    missing = validate_web_research_gateway_request(
        _request(memory_derived_context=True, source_provider_class="no_provider")
    )
    ready = validate_web_research_gateway_request(
        _request(memory_derived_context=True, source_provider_class="no_provider"),
        memory_governance_decision=_related(governance_status="ready"),
    )

    assert "missing_memory_governance" in missing.failure_reasons
    assert ready.readiness_status == "research_plan_ready"


def test_project_or_user_scoped_research_requires_identity_scope() -> None:
    missing = validate_web_research_gateway_request(
        _request(project_or_user_scoped_context=True, source_provider_class="no_provider")
    )
    ready = validate_web_research_gateway_request(
        _request(project_or_user_scoped_context=True, source_provider_class="no_provider"),
        identity_scope_decision=_related(scope_status="ready"),
    )

    assert "missing_identity_scope" in missing.failure_reasons
    assert ready.readiness_status == "research_plan_ready"


def test_context_policy_cannot_be_contradicted() -> None:
    decision = validate_web_research_gateway_request(
        _request(source_provider_class="no_provider"),
        context_policy_decision=_related(data_sent_external=True),
    )

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons


def test_search_snippet_is_low_trust_and_not_evidence() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            source_type_class="search_snippet",
            source_quality_class="snippet_only_low_trust",
            result_authority_class="citation_candidate_only",
        )
    )

    assert decision.source_quality_status == "low_trust_candidate"
    assert decision.evidence_provided_by_web_research is False
    assert decision.verifier_success is False


def test_search_snippet_cannot_be_high_authority() -> None:
    decision = validate_web_research_gateway_request(
        _request(source_type_class="search_snippet", source_quality_class="high_authority")
    )

    assert decision.readiness_status == "blocked_by_truth_claim"
    assert "search_snippet_cannot_be_high_authority" in decision.failure_reasons


def test_community_forum_is_low_trust_unless_labeled() -> None:
    low = validate_web_research_gateway_request(
        _request(source_type_class="community_forum", source_quality_class="community_low_trust")
    )
    blocked = validate_web_research_gateway_request(
        _request(source_type_class="community_forum", source_quality_class="high_authority")
    )

    assert low.source_quality_status == "low_trust_candidate"
    assert blocked.readiness_status == "blocked_by_truth_claim"


def test_official_primary_source_is_high_authority_candidate_not_truth() -> None:
    decision = validate_web_research_gateway_request(
        _request(source_type_class="official_primary_source", source_quality_class="high_authority")
    )

    assert decision.source_quality_status == "high_authority_candidate"
    assert decision.source_truth_claimed is False
    assert decision.result_authority_status == "source_candidate_only"


def test_stale_source_remains_stale_and_unknown_freshness_blocks_current_research() -> None:
    stale = validate_web_research_gateway_request(_request(freshness_class="stale"))
    unknown = validate_web_research_gateway_request(
        _request(research_subject="security_advisory_research", freshness_class="unknown")
    )

    assert stale.freshness_status == "stale_preserved"
    assert stale.readiness_status == "proposal_requires_human_review"
    assert "unknown_freshness_blocks_current_research" in unknown.failure_reasons


def test_cache_policies_do_not_write_cache_or_records() -> None:
    no_cache = validate_web_research_gateway_request(_request(cache_policy_class="no_cache"))
    session = validate_web_research_gateway_request(_request(cache_policy_class="session_cache_only"))
    source_ref = validate_web_research_gateway_request(_request(cache_policy_class="source_ref_cache_only"))

    assert no_cache.cache_status == "no_cache"
    assert session.cache_status == "session_cache_candidate_only"
    assert source_ref.cache_status == "source_ref_cache_candidate_only"
    assert no_cache.cache_written is False
    assert session.cache_written is False
    assert source_ref.cache_written is False


def test_prohibited_cache_blocks_cache_provider_and_durable_cache_is_future_only() -> None:
    prohibited = validate_web_research_gateway_request(
        _request(cache_policy_class="prohibited_cache", source_provider_class="local_cache_future")
    )
    durable = validate_web_research_gateway_request(
        _request(cache_policy_class="durable_cache_future", source_provider_class="no_provider")
    )

    assert prohibited.readiness_status == "blocked_by_cache_policy"
    assert "cache_policy_blocks_cache_provider" in prohibited.failure_reasons
    assert durable.readiness_status == "future_gated"
    assert durable.cache_written is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("web_query_performed", "web_query_denied"),
        ("browser_fetch_performed", "browser_fetch_denied"),
        ("search_api_called", "search_api_call_denied"),
        ("http_request_performed", "http_request_denied"),
        ("external_api_called", "external_api_call_denied"),
        ("github_api_called", "github_api_call_denied"),
        ("page_extract_performed", "page_extract_denied"),
        ("scraping_performed", "scraping_denied"),
        ("model_call_performed", "model_call_denied"),
        ("tool_call_performed", "tool_call_denied"),
        ("mcp_call_performed", "mcp_call_denied"),
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
def test_network_fetch_api_scrape_cache_report_and_external_behavior_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_web_research_gateway_request(_request(**{field: True}))

    assert decision.readiness_status == "blocked_by_execution_claim"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("private_query_leak_allowed", "private_query_leak_denied"),
        ("source_truth_claimed", "source_truth_claim_denied"),
        ("synthesis_truth_claimed", "synthesis_truth_claim_denied"),
        ("evidence_provided_by_web_research", "web_research_cannot_provide_evidence"),
        ("verifier_success", "web_research_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_authority_grants_evidence_verifier_truth_and_private_leak_claims_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = validate_web_research_gateway_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_web_research_gateway_request(_request(execution_permission="granted_by_web_research"))

    assert decision.readiness_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("policy_extension_decision", _related(runtime_dispatch_allowed=True)),
        ("context_policy_decision", _related(evidence_created=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("audit_query_layer_decision", _related(source_truth_claimed=True)),
        ("action_attribution_decision", _related(verifier_success=True)),
        ("system_drift_integrity_decision", _related(proof=True)),
        ("repo_audit_decision", _related(github_api_called=True)),
        ("local_model_inventory_decision", _related(model_call_performed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_web_research_gateway_request(_request(), **{related_name: related_value})

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only_candidates() -> None:
    decision = validate_web_research_gateway_request(
        _request(research_subject="source_verification_research"),
        system_drift_integrity_decision=_related(readiness_status="drift_integrity_candidate_ready"),
        action_attribution_decision=_related(attribution_status="attribution_candidate_ready"),
        audit_query_layer_decision=_related(query_status="query_plan_ready_bounded_projection"),
        passive_observe_decision=_related(display_state="read_only_projection"),
        model_auto_mode_decision=_related(selection_mode="local_preferred"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
        repo_audit_decision=_related(readiness_status="readiness_ready"),
        local_model_inventory_decision=_related(inventory_status="metadata_ready"),
    )

    assert len(decision.related_references) == 8
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.web_query_performed is False
    assert decision.model_call_performed is False
    assert decision.github_api_called is False


def test_future_provider_and_github_source_work_remain_future_gated() -> None:
    decision = validate_web_research_gateway_request(
        _request(
            research_subject="github_public_repo_research_future",
            research_operation="propose_search_api_future",
            source_provider_class="github_api_future",
            source_type_class="github_repository",
            cache_policy_class="source_ref_cache_only",
        )
    )

    assert decision.readiness_status == "future_gated"
    assert decision.future_gated is True
    assert decision.github_api_called is False


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_web_research_gateway_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.research_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection() -> None:
    decision = validate_web_research_gateway_request(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
