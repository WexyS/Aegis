from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_model_context_profile import (
    LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION,
    LOCAL_MODEL_CONTEXT_PROFILE_VERSION,
    validate_local_model_context_profile_request,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "model-profile:aegis:1",
        "model_id": "qwen3.5-9b-q4-k-m",
        "model_name": "Qwen3.5 9B",
        "model_family_class": "qwen_general",
        "provider_class": "lm_studio_local",
        "intended_role": "fast_general_chat",
        "context_source_allowance_class": "public_docs_allowed",
        "context_budget_class": "small_context",
        "sampling_profile_class": "safe_general",
        "eval_readiness_class": "user_observed_metadata_only",
        "source_refs": [{"ref_id": "synthetic:lm-studio-model-profile", "ref_type": "synthetic_fixture"}],
        "provenance": [{"ref_id": "caller:test", "ref_type": "synthetic_fixture"}],
        "limitations": ["profile metadata only"],
        "unknowns": [],
        "known_risks": ["self_report_untrusted"],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION,
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
        evidence_provided_by_model_profile=False,
        verifier_success=False,
        model_loaded=False,
        model_call_performed=False,
        inference_performed=False,
        provider_probed=False,
        endpoint_probed=False,
        api_key_validated=False,
        secret_read=False,
        live_model_files_inspected=False,
        embedding_generated=False,
        reranking_performed=False,
        multimodal_inference_performed=False,
        benchmark_run=False,
        eval_result_created=False,
        context_retrieval_performed=False,
        memory_retrieval_performed=False,
        web_query_performed=False,
        repo_file_read_performed=False,
        profile_record_created=False,
        data_sent_external=False,
        model_identity_verified=False,
        benchmark_claim_verified=False,
        provider_health_verified=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_model_profile is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.model_loaded is False
    assert decision.model_call_performed is False
    assert decision.inference_performed is False
    assert decision.provider_probed is False
    assert decision.endpoint_probed is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.live_model_files_inspected is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_inference_performed is False
    assert decision.benchmark_run is False
    assert decision.eval_result_created is False
    assert decision.context_retrieval_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.web_query_performed is False
    assert decision.repo_file_read_performed is False
    assert decision.profile_record_created is False
    assert decision.data_sent_external is False
    assert decision.model_identity_verified is False
    assert decision.benchmark_claim_verified is False
    assert decision.provider_health_verified is False
    assert decision.requires_backend_validation is True
    assert decision.requires_policy_check is True
    assert decision.read_only_projection is True


def test_valid_qwen35_fast_general_chat_profile_is_candidate_only() -> None:
    decision = validate_local_model_context_profile_request(_request())

    assert decision.contract_version == LOCAL_MODEL_CONTEXT_PROFILE_VERSION
    assert decision.profile_status == "profile_requires_human_review"
    assert decision.role_suitability_status == "role_candidate_only"
    assert decision.qwen35_retained_candidate is True
    _assert_non_authority(decision)


def test_valid_gemma_general_reasoning_profile_is_candidate_only() -> None:
    decision = validate_local_model_context_profile_request(
        _request(
            model_id="gemma-4-12b",
            model_name="Gemma 4 12B",
            model_family_class="gemma_multimodal_general",
            intended_role="general_reasoning",
            sampling_profile_class="architecture_review",
            context_budget_class="medium_context",
            known_risks=["self_identity_drift", "self_report_untrusted"],
        )
    )

    assert decision.profile_status == "profile_requires_human_review"
    assert decision.gemma_multimodal_candidate is True
    assert decision.self_identity_drift_preserved is True
    _assert_non_authority(decision)


def test_valid_gemma_future_multimodal_profile_remains_future_gated() -> None:
    decision = validate_local_model_context_profile_request(
        _request(
            model_id="gemma-4-12b",
            model_name="Gemma 4 12B",
            model_family_class="gemma_multimodal_general",
            intended_role="future_multimodal_reasoning",
            context_source_allowance_class="image_observation_future_gated",
            sampling_profile_class="multimodal_future_gated",
            eval_readiness_class="multimodal_privacy_required",
            future_privacy_boundary_present=True,
            known_risks=["modality_future_gated", "privacy_boundary_required"],
        )
    )

    assert decision.profile_status == "future_gated"
    assert decision.future_gated is True
    assert decision.multimodal_inference_performed is False


def test_valid_qwen25_coder_coding_profile_is_candidate_only() -> None:
    decision = validate_local_model_context_profile_request(
        _request(
            model_id="qwen2.5-coder-14b",
            model_name="Qwen2.5 Coder 14B",
            model_family_class="qwen_coder",
            intended_role="coding_assistant",
            context_source_allowance_class="repo_code_candidate_local_only",
            context_budget_class="medium_context",
            sampling_profile_class="coding_low_temperature",
            eval_readiness_class="eval_plan_candidate",
            private_repo_context_candidate=True,
        ),
        identity_scope_decision=_related(scope_status="ready"),
    )

    assert decision.profile_status == "profile_candidate_ready"
    assert decision.context_allowance_status == "local_or_metadata_candidate"
    assert decision.repo_file_read_performed is False


def test_valid_deepseek_risk_analysis_profile_is_candidate_only() -> None:
    decision = validate_local_model_context_profile_request(
        _request(
            model_id="deepseek-r1-distill-qwen-14b",
            model_name="DeepSeek R1 Distill Qwen 14B",
            model_family_class="deepseek_reasoning",
            intended_role="risk_analysis",
            sampling_profile_class="architecture_review",
            known_risks=["hallucination_risk"],
        )
    )

    assert decision.role_suitability_status == "role_candidate_only"
    assert decision.model_call_performed is False


def test_embedding_and_reranker_profiles_are_not_chat() -> None:
    embedding = validate_local_model_context_profile_request(
        _request(
            model_id="bge-m3",
            model_name="bge-m3",
            model_family_class="bge_embedding",
            intended_role="embedding",
            context_source_allowance_class="repo_metadata_allowed",
            sampling_profile_class="strict_json",
            eval_readiness_class="eval_plan_candidate",
        )
    )
    reranker = validate_local_model_context_profile_request(
        _request(
            model_id="qwen3-reranker-0.6b",
            model_name="Qwen3 Reranker 0.6B",
            model_family_class="qwen_reranker",
            intended_role="reranking",
            context_source_allowance_class="repo_metadata_allowed",
            sampling_profile_class="strict_json",
            eval_readiness_class="eval_plan_candidate",
        )
    )

    assert embedding.role_suitability_status == "embedding_candidate_not_chat"
    assert reranker.role_suitability_status == "reranker_candidate_not_chat"
    assert embedding.embedding_generated is False
    assert reranker.reranking_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("request_id", "missing_request_id"),
        ("model_id", "missing_model_id"),
        ("model_family_class", "missing_model_family_class"),
        ("provider_class", "missing_provider_class"),
        ("intended_role", "missing_intended_role"),
        ("context_budget_class", "missing_context_budget_class"),
        ("sampling_profile_class", "missing_sampling_profile_class"),
        ("eval_readiness_class", "missing_eval_readiness_class"),
    ],
)
def test_missing_required_fields_block(field: str, reason: str) -> None:
    decision = validate_local_model_context_profile_request(_request(**{field: None}))

    assert decision.profile_status == "blocked_by_missing_required_field"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_source_refs_or_provenance_blocks() -> None:
    decision = validate_local_model_context_profile_request(_request(source_refs=[], provenance=[]))

    assert decision.profile_status == "blocked_by_missing_required_field"
    assert "missing_source_refs_or_provenance" in decision.failure_reasons


def test_self_report_user_observation_and_provider_health_cannot_be_verified_truth() -> None:
    identity = validate_local_model_context_profile_request(_request(model_identity_verified=True))
    benchmark = validate_local_model_context_profile_request(_request(benchmark_claim_verified=True))
    health = validate_local_model_context_profile_request(_request(provider_health_verified=True))

    assert "model_identity_verification_denied" in identity.failure_reasons
    assert "benchmark_verification_denied" in benchmark.failure_reasons
    assert "provider_health_verification_denied" in health.failure_reasons
    assert identity.model_identity_verified is False
    assert benchmark.benchmark_claim_verified is False
    assert health.provider_health_verified is False


def test_inventory_auto_mode_web_gateway_and_lease_do_not_authorize_execution() -> None:
    decision = validate_local_model_context_profile_request(
        _request(),
        local_model_inventory_decision=_related(inventory_status="inventory_ready"),
        model_auto_mode_decision=_related(selection_mode="local_model_candidate"),
        web_research_gateway_decision=_related(readiness_status="research_plan_ready"),
        capability_lease_decision=_related(lifecycle_state="proposed"),
    )

    assert len(decision.related_references) == 4
    assert decision.model_call_performed is False
    assert decision.web_query_performed is False
    assert decision.lease_grant is False


def test_unknown_resource_and_provider_health_remain_unknown() -> None:
    decision = validate_local_model_context_profile_request(
        _request(known_risks=["resource_unknown", "provider_health_unknown"])
    )

    assert decision.unknown_resource_or_provider_health_preserved is True
    assert decision.human_review_required is True


def test_qwen35_is_not_replaced_by_gemma_profile() -> None:
    qwen = validate_local_model_context_profile_request(_request())
    gemma = validate_local_model_context_profile_request(
        _request(
            model_id="gemma-4-12b",
            model_name="Gemma 4 12B",
            model_family_class="gemma_multimodal_general",
            intended_role="general_reasoning",
        )
    )

    assert qwen.qwen35_retained_candidate is True
    assert gemma.qwen35_retained_candidate is False
    assert gemma.gemma_multimodal_candidate is True


@pytest.mark.parametrize(
    ("family", "role", "reason"),
    [
        ("bge_embedding", "fast_general_chat", "embedding_model_cannot_be_chat_role"),
        ("qwen_embedding", "general_reasoning", "embedding_model_cannot_be_chat_role"),
        ("qwen_reranker", "fast_general_chat", "reranker_model_cannot_be_chat_role"),
        ("qwen_coder", "future_vision", "coding_model_cannot_default_multimodal"),
    ],
)
def test_role_mismatch_blocks(family: str, role: str, reason: str) -> None:
    decision = validate_local_model_context_profile_request(
        _request(model_family_class=family, intended_role=role)
    )

    assert reason in decision.failure_reasons
    assert decision.profile_status in {"blocked_by_role_mismatch", "blocked_by_context_policy"}


@pytest.mark.parametrize("role", ["future_vision", "future_audio", "future_video_frame", "future_screen_observation"])
def test_multimodal_roles_require_future_privacy_boundary(role: str) -> None:
    decision = validate_local_model_context_profile_request(_request(intended_role=role))

    assert "multimodal_role_requires_future_privacy_boundary" in decision.failure_reasons
    assert decision.multimodal_inference_performed is False


@pytest.mark.parametrize(
    "context_source",
    ["raw_journal_blocked", "raw_evidence_blocked", "unknown_blocked", "user_memory_blocked_by_default"],
)
def test_blocked_context_sources_are_rejected(context_source: str) -> None:
    decision = validate_local_model_context_profile_request(
        _request(context_source_allowance_class=context_source)
    )

    assert decision.profile_status == "blocked_by_context_policy"
    assert decision.context_retrieval_performed is False


def test_project_memory_requires_governance_and_private_repo_remains_local_only() -> None:
    missing_memory = validate_local_model_context_profile_request(
        _request(context_source_allowance_class="project_memory_requires_governance")
    )
    contradiction = validate_local_model_context_profile_request(
        _request(private_repo_context_candidate=True, cloud_context_candidate=True),
        identity_scope_decision=_related(scope_status="ready"),
    )

    assert "missing_memory_governance" in missing_memory.failure_reasons
    assert "private_repo_cloud_context_contradiction" in contradiction.failure_reasons
    assert contradiction.data_sent_external is False


def test_sampling_and_context_budget_are_metadata_only() -> None:
    strict = validate_local_model_context_profile_request(
        _request(sampling_profile_class="strict_json", context_budget_class="tiny_context")
    )
    creative = validate_local_model_context_profile_request(
        _request(sampling_profile_class="creative_ui_copy", context_budget_class="small_context")
    )
    large = validate_local_model_context_profile_request(
        _request(context_budget_class="large_context_candidate"),
        context_policy_decision=_related(policy_status="proposal_ready"),
    )

    assert strict.sampling_profile_status == "sampling_metadata_only"
    assert creative.sampling_profile_status == "sampling_metadata_only"
    assert large.context_budget_status == "large_context_candidate_only"
    assert large.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_loaded", "model_load_denied"),
        ("model_call_performed", "model_call_denied"),
        ("inference_performed", "inference_denied"),
        ("provider_probed", "provider_probe_denied"),
        ("endpoint_probed", "endpoint_probe_denied"),
        ("api_key_validated", "api_key_validation_denied"),
        ("secret_read", "secret_read_denied"),
        ("live_model_files_inspected", "live_model_file_inspection_denied"),
        ("embedding_generated", "embedding_generation_denied"),
        ("reranking_performed", "reranking_denied"),
        ("multimodal_inference_performed", "multimodal_inference_denied"),
        ("benchmark_run", "benchmark_run_denied"),
        ("eval_result_created", "eval_result_creation_denied"),
        ("context_retrieval_performed", "context_retrieval_denied"),
        ("memory_retrieval_performed", "memory_retrieval_denied"),
        ("web_query_performed", "web_query_denied"),
        ("repo_file_read_performed", "repo_file_read_denied"),
        ("profile_record_created", "profile_record_creation_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
    ],
)
def test_execution_probe_eval_retrieval_and_record_flags_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_model_context_profile_request(_request(**{field: True}))

    assert decision.profile_status == "blocked_by_execution_claim"
    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("mutation_performed", "mutation_performed_denied"),
        ("evidence_provided_by_model_profile", "model_profile_cannot_provide_evidence"),
        ("verifier_success", "model_profile_cannot_mark_verifier_success"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_result_is_authority", "frontend_authority_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
        ("tool_output_is_truth", "tool_output_truth_claim_denied"),
    ],
)
def test_authority_grants_evidence_verifier_and_truth_claims_are_rejected(field: str, reason: str) -> None:
    decision = validate_local_model_context_profile_request(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = validate_local_model_context_profile_request(_request(execution_permission="granted_by_profile"))

    assert decision.profile_status == "blocked_by_authority_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("policy_extension_decision", _related(runtime_dispatch_allowed=True)),
        ("context_policy_decision", _related(context_retrieval_performed=True)),
        ("local_model_inventory_decision", _related(model_call_performed=True)),
        ("model_auto_mode_decision", _related(model_call_performed=True)),
        ("local_provider_health_decision", _related(provider_health_verified=True)),
        ("local_provider_probe_design_decision", _related(provider_probed=True)),
        ("memory_governance_decision", _related(memory_retrieval_performed=True)),
        ("identity_scope_decision", _related(authority=True)),
        ("capability_lease_decision", _related(lease_grant=True)),
        ("web_research_gateway_decision", _related(web_query_performed=True)),
        ("repo_audit_decision", _related(repo_file_read_performed=True)),
        ("tool_simulation_decision", _related(tool_call_performed=True)),
        ("plugin_review_decision", _related(authority=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = validate_local_model_context_profile_request(_request(), **{related_name: related_value})

    assert decision.profile_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_safe_related_decisions_are_reference_only() -> None:
    decision = validate_local_model_context_profile_request(
        _request(),
        local_model_inventory_decision=_related(inventory_status="inventory_ready"),
        model_auto_mode_decision=_related(selection_mode="local_model_candidate"),
        local_provider_health_decision=_related(readiness_status="metadata_ready"),
        local_provider_probe_design_decision=_related(probe_result_status="future_probe_candidate"),
        context_policy_decision=_related(policy_status="proposal_ready"),
        web_research_gateway_decision=_related(readiness_status="research_plan_ready"),
    )

    assert len(decision.related_references) == 6
    for reference in decision.related_references:
        assert reference.reference_only is True
        assert reference.authority is False
        assert reference.implementation_claim is False
    assert decision.model_call_performed is False
    assert decision.provider_health_verified is False


def test_input_and_related_decisions_are_not_mutated_and_output_is_frozen() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = validate_local_model_context_profile_request(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.profile_input.model_id = "mutated"  # type: ignore[union-attr,misc]


def test_output_always_read_only_projection() -> None:
    decision = validate_local_model_context_profile_request(_request())

    assert decision.read_only_projection is True
    _assert_non_authority(decision)
