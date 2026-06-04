from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.context_policy import validate_context_policy_request
from aegis.core.identity_scope import validate_identity_scope_request
from aegis.core.local_model_inventory import validate_local_model_inventory_request
from aegis.core.memory_governance import validate_memory_governance_request
from aegis.core.model_auto_mode import (
    MODEL_AUTO_MODE_EXECUTION_PERMISSION,
    MODEL_AUTO_MODE_VERSION,
    select_model_auto_mode_candidate,
)
from aegis.core.policy_boundary import evaluate_policy_extension_request


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "auto-mode:aegis:1",
        "task_type": "repo_audit_candidate_notes",
        "user_preference_mode": "auto",
        "namespace": "model_auto_mode",
        "privacy_class": "private_repo",
        "provider_class": "lm_studio_local",
        "provider_status": "configured_metadata_only",
        "cloud_provider_status": "not_configured",
        "provider_secret_status": "no_secret_required",
        "resource_status": "disk_warning",
        "source_refs": [{"ref_id": "synthetic:auto-mode-test", "ref_type": "test_fixture"}],
        "limitations": ["synthetic metadata only"],
        "unknowns": [],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": MODEL_AUTO_MODE_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _identity_scope_ready() -> object:
    return validate_identity_scope_request(
        {
            "request_id": "identity:auto-mode:test",
            "subject_kind": "repository",
            "namespace": "model_auto_mode",
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
            "request_id": "memory:auto-mode:test",
            "memory_category": "repo_memory",
            "memory_status": "proposed",
            "memory_scope": "repository_scoped",
            "operation": "propose_retrieve",
            "namespace": "model_auto_mode",
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


def _context_policy(**overrides: object) -> object:
    request: dict[str, object] = {
        "request_id": "context:auto-mode:test",
        "context_source_category": "private_repo_code",
        "context_operation": "propose_context_package",
        "privacy_class": "private_repo",
        "provider_target_class": "local_model_candidate",
        "namespace": "model_auto_mode",
        "project_ref": "project:aegis",
        "repository_ref": "repo:WexyS/Aegis",
        "source_refs": [{"ref_id": "repo:metadata", "ref_type": "synthetic_fixture"}],
        "provenance": [{"ref_id": "caller:supplied", "ref_type": "synthetic_fixture"}],
        "budget_policy": {
            "max_context_tokens": 8192,
            "recommended_context_tokens": 2048,
            "reserved_system_tokens": 512,
            "reserved_instruction_tokens": 512,
            "reserved_response_tokens": 1024,
            "max_source_count": 8,
            "max_chunk_count": 32,
            "max_chunk_tokens": 512,
            "allow_raw_content": False,
            "allow_summaries": True,
            "allow_source_refs_only": True,
            "requires_redaction": True,
            "requires_citation": True,
            "requires_provenance": True,
        },
    }
    request.update(overrides)
    return validate_context_policy_request(request, identity_scope_decision=_identity_scope_ready())


def _context_policy_public(**overrides: object) -> object:
    request: dict[str, object] = {
        "request_id": "context:auto-mode:public",
        "context_source_category": "public_docs",
        "context_operation": "classify_context",
        "privacy_class": "public",
        "provider_target_class": "passive_backend_only",
        "namespace": "model_auto_mode",
        "source_refs": [{"ref_id": "docs:public", "ref_type": "synthetic_fixture"}],
        "provenance": [{"ref_id": "caller:supplied", "ref_type": "synthetic_fixture"}],
        "budget_policy": {
            "max_context_tokens": 8192,
            "recommended_context_tokens": 2048,
            "reserved_system_tokens": 512,
            "reserved_instruction_tokens": 512,
            "reserved_response_tokens": 1024,
            "max_source_count": 8,
            "max_chunk_count": 32,
            "max_chunk_tokens": 512,
            "allow_raw_content": False,
            "allow_summaries": True,
            "allow_source_refs_only": True,
            "requires_citation": True,
            "requires_provenance": True,
        },
    }
    request.update(overrides)
    return validate_context_policy_request(request)


def _model(**overrides: object) -> dict[str, object]:
    model: dict[str, object] = {
        "model_id": "qwen2.5-coder-14b",
        "model_name": "Qwen2.5 Coder 14B Instruct Reason",
        "model_role": "coding",
        "model_modality": "text_in_text_out",
        "task_roles": ["repo_audit_candidate_notes", "code_explanation"],
        "privacy_class": "local_private",
        "terms_status": "local_only",
        "region_status": "local_only",
    }
    model.update(overrides)
    return model


def _local_inventory(*models: dict[str, object]) -> object:
    return validate_local_model_inventory_request(
        {
            "request_id": "inventory:auto-mode:test",
            "project_ref": "project:aegis",
            "tenant_scope": "local-user",
            "namespace": "model_auto_mode",
            "provider_id": "lmstudio:local",
            "provider_class": "lm_studio_local",
            "provider_status": "configured_metadata_only",
            "privacy_class": "local_private",
            "data_sensitivity_allowed": ["private_repo_context", "source_code"],
            "context_policy": {
                "max_context_tokens": 32768,
                "recommended_context_budget": 12000,
                "can_receive_private_repo_context": True,
                "can_receive_user_memory_context": False,
                "can_receive_runtime_logs": False,
                "can_receive_evidence_refs": True,
                "can_receive_raw_evidence": False,
                "can_receive_secret_like_content": False,
                "can_receive_raw_journal": False,
                "requires_redaction": True,
                "requires_source_refs": True,
                "output_requires_validation": True,
            },
            "models": list(models) if models else [_model()],
            "source_refs": [{"ref_id": "synthetic:inventory", "ref_type": "test_fixture"}],
            "policy_refs": ["policy:model-auto-mode.local-inventory"],
        }
    )


def _policy_extension_ready(task_action: str = "proposal_only") -> object:
    return evaluate_policy_extension_request(
        {
            "subject_kind": "model_operation",
            "action_kind": task_action,
            "namespace": "model_auto_mode",
            "runtime_dispatch_allowed": False,
            "execution_permission": "not_granted_by_policy_extension",
        }
    )


def _safe_related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        authority=False,
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_auto_mode=False,
        verifier_success=False,
        provider_selected=False,
        model_call_performed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _select(request: dict[str, object], **related: object):
    return select_model_auto_mode_candidate(request, **related)


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == MODEL_AUTO_MODE_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_auto_mode is False
    assert decision.verifier_success is False
    assert decision.frontend_authority is False
    assert decision.model_call_performed is False
    assert decision.model_loaded is False
    assert decision.endpoint_probed is False
    assert decision.provider_authenticated is False
    assert decision.cloud_api_called is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.context_retrieval_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.repo_file_read_performed is False
    assert decision.web_query_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.inference_performed is False
    assert decision.vector_index_touched is False
    assert decision.provider_selected is False
    assert decision.data_sent_external is False
    assert decision.auto_mode_execution_allowed is False
    assert decision.cloud_routing_allowed is False
    assert decision.local_model_routing_allowed is False
    assert decision.output_is_authority is False


@pytest.mark.parametrize("task", ["maintenance_scan", "evidence_audit", "policy_validation", "repo_audit_readiness"])
def test_deterministic_backend_tasks_select_passive_no_model(task: str) -> None:
    decision = _select(_request(task_type=task, privacy_class=None))

    assert decision.contract_version == MODEL_AUTO_MODE_VERSION
    assert decision.selection_mode == "passive_no_model"
    assert decision.selected_provider_candidate == "passive_backend"
    assert decision.selected_model_candidate is None
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("preference", "expected"),
    [("disabled", "blocked_by_policy"), ("passive_only", "passive_no_model")],
)
def test_disabled_and_passive_only_preferences_block_model_candidates(preference: str, expected: str) -> None:
    decision = _select(
        _request(user_preference_mode=preference),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(),
    )

    assert decision.selection_mode == expected
    assert decision.selected_model_candidate is None
    _assert_non_authority(decision)


def test_repo_audit_candidate_notes_selects_qwen_coder_local_candidate_only() -> None:
    decision = _select(
        _request(task_type="repo_audit_candidate_notes"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(_model()),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.selected_provider_candidate == "lm_studio_local"
    assert decision.selected_model_candidate == "qwen2.5-coder-14b"
    assert "no provider selected" in " ".join(decision.why_this_mode)
    _assert_non_authority(decision)


def test_risk_analysis_selects_deepseek_like_local_candidate_only() -> None:
    decision = _select(
        _request(task_type="risk_analysis"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(
            _model(
                model_id="deepseek-r1-distill-qwen-14b",
                model_name="DeepSeek R1 Distill Qwen 14B",
                model_role="reasoning",
                task_roles=["risk_analysis", "architecture_review"],
            )
        ),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.selected_model_candidate == "deepseek-r1-distill-qwen-14b"
    _assert_non_authority(decision)


def test_mission_control_wording_selects_qwen35_like_local_candidate_only() -> None:
    decision = _select(
        _request(task_type="mission_control_wording", privacy_class="internal"),
        local_model_inventory_decision=_local_inventory(
            _model(
                model_id="qwen3.5-9b",
                model_name="Qwen3.5 9B",
                model_role="chat_general",
                task_roles=["mission_control_wording", "documentation_summary"],
            )
        ),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.selected_model_candidate == "qwen3.5-9b"
    _assert_non_authority(decision)


def test_local_inventory_metadata_alone_does_not_authorize_model_call() -> None:
    decision = _select(
        _request(task_type="code_explanation"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(_model(task_roles=["code_explanation"])),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.provider_selected is False
    assert decision.model_call_performed is False
    assert decision.auto_mode_execution_allowed is False


def test_provider_health_absent_keeps_candidate_unselected() -> None:
    decision = _select(
        _request(task_type="code_explanation", provider_status="endpoint_available_unverified"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(_model(task_roles=["code_explanation"])),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.provider_selected is False
    assert "provider_status=endpoint_available_unverified" in decision.why_not_local


def test_context_retrieval_selects_embedding_candidate_only() -> None:
    decision = _select(
        _request(task_type="context_retrieval"),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
        context_policy_decision=_context_policy(context_operation="propose_retrieval_future"),
        local_model_inventory_decision=_local_inventory(
            _model(
                model_id="bge-m3-567m",
                model_name="text-embedding-baai-bge-m3-567M",
                model_role="embedding",
                model_modality="text_embedding",
                task_roles=["context_retrieval"],
            )
        ),
    )

    assert decision.selection_mode == "local_embedding_candidate"
    assert decision.selected_model_candidate == "bge-m3-567m"
    assert decision.embedding_generated is False


def test_context_reranking_selects_reranker_candidate_only() -> None:
    decision = _select(
        _request(task_type="context_reranking"),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
        context_policy_decision=_context_policy(context_operation="propose_reranking_future"),
        local_model_inventory_decision=_local_inventory(
            _model(
                model_id="qwen3-reranker-0.6b",
                model_name="Qwen3 Reranker 0.6B",
                model_role="reranker",
                model_modality="text_rerank",
                task_roles=["context_reranking"],
            )
        ),
    )

    assert decision.selection_mode == "local_reranker_candidate"
    assert decision.selected_model_candidate == "qwen3-reranker-0.6b"
    assert decision.reranking_performed is False


@pytest.mark.parametrize(
    "model",
    [
        _model(model_role="embedding", model_modality="text_embedding", task_roles=["repo_audit_candidate_notes"]),
        _model(model_role="reranker", model_modality="text_rerank", task_roles=["repo_audit_candidate_notes"]),
    ],
)
def test_embedding_and_reranker_models_cannot_be_chat_candidates(model: dict[str, object]) -> None:
    decision = _select(
        _request(task_type="repo_audit_candidate_notes"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(model),
    )

    assert decision.selection_mode == "blocked_by_provider_status"
    assert decision.selected_model_candidate is None


@pytest.mark.parametrize("preference", ["cloud_allowed", "local_first_cloud_fallback"])
def test_cloud_preferences_do_not_permit_private_repo_cloud_routing(preference: str) -> None:
    decision = _select(
        _request(user_preference_mode=preference, cloud_provider_status="api_key_present_unverified"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(provider_target_class="local_model_candidate"),
        local_model_inventory_decision=_local_inventory(_model()),
    )

    assert "privacy/context policy blocks cloud" in decision.why_not_cloud
    assert decision.cloud_routing_allowed is False
    assert decision.data_sent_external is False


def test_cloud_allowed_blocks_for_private_repo_code() -> None:
    decision = _select(
        _request(user_preference_mode="cloud_allowed"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
    )

    assert decision.selection_mode == "blocked_by_privacy"
    assert decision.cloud_routing_allowed is False


def test_local_only_blocks_cloud_selection() -> None:
    decision = _select(
        _request(user_preference_mode="local_only"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(_model()),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert "local_only preference blocks cloud" in decision.why_not_cloud
    assert decision.cloud_routing_allowed is False


def test_unknown_sensitivity_asks_operator_and_blocks_cloud() -> None:
    decision = _select(
        _request(privacy_class="unknown", user_preference_mode="cloud_allowed"),
        context_policy_decision=_context_policy_public(privacy_class="unknown"),
    )

    assert decision.selection_mode == "ask_operator"
    assert decision.cloud_routing_allowed is False


def test_raw_journal_context_blocks_provider_routing() -> None:
    context = _context_policy(
        context_source_category="raw_journal",
        privacy_class="private",
        provider_target_class="passive_backend_only",
    )
    decision = _select(
        _request(task_type="repo_audit_candidate_notes"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=context,
        local_model_inventory_decision=_local_inventory(_model()),
    )

    assert decision.selection_mode == "blocked_by_context_policy"


def test_raw_evidence_refs_only_does_not_authorize_raw_routing() -> None:
    context = _context_policy_public(context_source_category="raw_evidence", privacy_class="internal")
    decision = _select(
        _request(task_type="documentation_summary", privacy_class="internal"),
        context_policy_decision=context,
        local_model_inventory_decision=_local_inventory(_model(model_role="chat_general", task_roles=["documentation_summary"])),
    )

    assert decision.selection_mode == "local_model_candidate"
    assert decision.data_sent_external is False
    assert decision.provider_selected is False


@pytest.mark.parametrize("privacy", ["secret_like", "credential_like"])
def test_secret_and_credential_context_blocks(privacy: str) -> None:
    decision = _select(_request(privacy_class=privacy))

    assert decision.selection_mode == "blocked_by_secret_boundary"
    assert decision.secret_read is False


@pytest.mark.parametrize(
    ("cloud_status", "expected"),
    [
        ("api_key_present_unverified", "blocked_by_provider_status"),
        ("unsupported_region", "blocked_by_region_or_terms"),
        ("region_blocked", "blocked_by_region_or_terms"),
        ("terms_unverified", "blocked_by_region_or_terms"),
    ],
)
def test_cloud_secret_region_and_terms_statuses_block_cloud(cloud_status: str, expected: str) -> None:
    decision = _select(
        _request(
            task_type="documentation_summary",
            user_preference_mode="cloud_allowed",
            privacy_class="public",
            cloud_provider_status=cloud_status,
        ),
        context_policy_decision=_context_policy_public(),
    )

    assert decision.selection_mode == expected
    assert decision.cloud_routing_allowed is False


@pytest.mark.parametrize(
    "task",
    [
        "visual_analysis_future_gated",
        "audio_analysis_future_gated",
        "multimodal_analysis_future_gated",
        "voice_interaction_future_gated",
        "web_research_future",
        "document_analysis_future",
        "external_agent_oversight_future",
    ],
)
def test_future_gated_tasks_remain_future_gated(task: str) -> None:
    decision = _select(
        _request(task_type=task, privacy_class="internal"),
        context_policy_decision=_context_policy_public(),
        policy_extension_decision=_policy_extension_ready(),
    )

    assert decision.selection_mode == "future_gated"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    "model",
    [
        _model(
            model_id="gemma-4-12b",
            model_name="Gemma 4 12B",
            model_role="multimodal",
            model_modality="multimodal",
            task_roles=["visual_analysis_future_gated"],
            human_review_required=True,
        ),
        _model(
            model_id="qwen3-vl-8b",
            model_name="Qwen3-VL 8B",
            model_role="vision",
            model_modality="image_text",
            task_roles=["visual_analysis_future_gated"],
            human_review_required=True,
        ),
    ],
)
def test_multimodal_models_remain_future_gated(model: dict[str, object]) -> None:
    decision = _select(
        _request(task_type="visual_analysis_future_gated", privacy_class="internal"),
        context_policy_decision=_context_policy_public(),
        policy_extension_decision=_policy_extension_ready(),
        local_model_inventory_decision=_local_inventory(model),
    )

    assert decision.selection_mode == "future_gated"
    assert decision.selected_model_candidate is None
    assert decision.model_call_performed is False


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("identity_scope_decision", _safe_related(authority=True)),
        ("memory_governance_decision", _safe_related(memory_retrieval_performed=True)),
        ("context_policy_decision", _safe_related(provider_selected=True)),
        ("policy_extension_decision", _safe_related(runtime_dispatch_allowed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = _select(_request(), **{related_name: related_value})

    assert decision.selection_mode == "blocked_by_policy"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_absent_context_policy_blocks_context_bearing_model_mode() -> None:
    decision = _select(
        _request(task_type="repo_audit_candidate_notes"),
        identity_scope_decision=_identity_scope_ready(),
        local_model_inventory_decision=_local_inventory(_model()),
    )

    assert decision.selection_mode == "blocked_by_context_policy"
    assert "missing_context_policy" in decision.failure_reasons


def test_absent_local_model_inventory_blocks_local_candidate() -> None:
    decision = _select(
        _request(task_type="repo_audit_candidate_notes"),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
    )

    assert decision.selection_mode == "blocked_by_provider_status"
    assert "missing local model inventory" in decision.why_not_local


def test_blocked_policy_decision_remains_blocked() -> None:
    decision = _select(
        _request(),
        identity_scope_decision=_identity_scope_ready(),
        context_policy_decision=_context_policy(),
        local_model_inventory_decision=_local_inventory(_model()),
        policy_extension_decision=SimpleNamespace(
            policy_outcome="blocked_by_policy",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_policy_extension",
        ),
    )

    assert decision.selection_mode == "blocked_by_policy"
    assert "policy_extension_not_ready" in decision.failure_reasons


def test_memory_governance_and_context_budget_do_not_authorize_model_routing() -> None:
    decision = _select(
        _request(task_type="context_retrieval"),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
        context_policy_decision=_context_policy(context_operation="propose_context_budget"),
        local_model_inventory_decision=_local_inventory(
            _model(model_id="bge-m3-567m", model_role="embedding", model_modality="text_embedding", task_roles=["context_retrieval"])
        ),
    )

    assert decision.selection_mode == "local_embedding_candidate"
    assert decision.local_model_routing_allowed is False
    assert decision.provider_selected is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_call_performed", "model_call_request_denied"),
        ("model_loaded", "model_load_request_denied"),
        ("endpoint_probed", "endpoint_probe_request_denied"),
        ("cloud_api_called", "cloud_api_call_request_denied"),
        ("api_key_validated", "api_key_validation_request_denied"),
        ("secret_read", "secret_read_request_denied"),
        ("provider_authenticated", "provider_auth_request_denied"),
        ("provider_selected", "provider_selection_not_allowed"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("context_retrieval_performed", "context_retrieval_request_denied"),
        ("memory_retrieval_performed", "memory_retrieval_request_denied"),
        ("repo_file_read_performed", "repo_file_read_request_denied"),
        ("web_query_performed", "web_query_request_denied"),
        ("embedding_generated", "embedding_generation_request_denied"),
        ("reranking_performed", "reranking_request_denied"),
        ("inference_performed", "inference_request_denied"),
        ("vector_index_touched", "vector_index_request_denied"),
    ],
)
def test_behavior_flags_are_rejected(field: str, reason: str) -> None:
    decision = _select(_request(**{field: True}))

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
        ("evidence_provided_by_auto_mode", "auto_mode_cannot_provide_evidence"),
        ("verifier_success", "auto_mode_cannot_mark_verifier_success"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("mcp_authority", "mcp_authority_not_allowed"),
        ("mcp_output_is_truth", "mcp_output_truth_claim_denied"),
    ],
)
def test_authority_grant_evidence_verifier_and_mcp_claims_are_rejected(field: str, reason: str) -> None:
    decision = _select(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _safe_related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _select(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.auto_mode_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_never_sets_execution_provider_or_external_flags() -> None:
    decision = _select(_request(task_type="maintenance_scan", privacy_class=None))

    _assert_non_authority(decision)
