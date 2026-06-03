from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_model_inventory import (
    LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION,
    LOCAL_MODEL_INVENTORY_VERSION,
    validate_local_model_inventory_request,
)


def _context_policy(**overrides: object) -> dict[str, object]:
    policy: dict[str, object] = {
        "max_context_tokens": 32_768,
        "recommended_context_budget": 12_000,
        "can_receive_private_repo_context": True,
        "can_receive_user_memory_context": False,
        "can_receive_runtime_logs": False,
        "can_receive_evidence_refs": True,
        "can_receive_raw_evidence": False,
        "can_receive_secret_like_content": False,
        "can_receive_raw_journal": False,
        "can_receive_compliance_context": False,
        "can_receive_web_context": False,
        "requires_redaction": True,
        "requires_source_refs": True,
        "output_requires_validation": True,
    }
    policy.update(overrides)
    return policy


def _model(**overrides: object) -> dict[str, object]:
    model: dict[str, object] = {
        "model_id": "qwen2.5-coder-14b-instruct-reason-q4-k-m",
        "model_name": "Qwen2.5 Coder 14B Instruct Reason",
        "model_family": "qwen",
        "publisher": "mradermacher",
        "model_role": "coding",
        "model_modality": "text_in_text_out",
        "quantization": "Q4_K_M",
        "parameter_count": "14B",
        "disk_size_bytes": 8_370_000_000,
        "context_window_tokens": None,
        "max_output_tokens": None,
        "privacy_class": "local_private",
        "data_sensitivity_allowed": ["private_repo_context"],
        "task_roles": ["repo_audit_candidate_notes", "code_explanation"],
        "resource_requirements": {
            "estimated_vram_gb": None,
            "estimated_ram_gb": None,
            "gpu_required": False,
            "cpu_usable": True,
            "latency_class": "unknown",
            "quality_class": "unknown",
            "cost_class": "local_disk_resource",
        },
        "license_ref": "unknown",
        "terms_status": "unknown",
        "region_status": "local_only",
        "source_refs": [{"ref_id": "synthetic:lm-studio-visible-model-list", "ref_type": "synthetic_fixture"}],
        "limitations": ["synthetic metadata only; no model health proof"],
        "unknowns": [],
        "human_review_required": False,
    }
    model.update(overrides)
    return model


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "local-model-inventory:aegis:1",
        "project_ref": "project:aegis",
        "tenant_scope": "local-user",
        "namespace": "model_provider_readiness",
        "provider_id": "lmstudio:local",
        "provider_class": "lm_studio_local",
        "provider_status": "configured_metadata_only",
        "privacy_class": "local_private",
        "data_sensitivity_allowed": ["private_repo_context", "source_code"],
        "context_policy": _context_policy(),
        "models": [_model()],
        "source_refs": [{"ref_id": "docs:model-provider-local-llm-readiness-v1", "ref_type": "doc"}],
        "policy_refs": ["policy:model-provider.local-inventory.metadata-only"],
        "limitations": ["inventory metadata only; no endpoint probing"],
        "unknowns": [],
        "human_review_required": False,
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related_decisions: object):
    return validate_local_model_inventory_request(request, **related_decisions)


def _unsafe_related_decision(**overrides: object) -> SimpleNamespace:
    decision = SimpleNamespace(
        authority=False,
        runtime_dispatch_allowed=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        frontend_authority=False,
        evidence_provided_by_inventory=False,
        verifier_success=False,
        model_call_performed=False,
        api_call_performed=False,
        mcp_call_performed=False,
        tool_call_performed=False,
        memory_access_performed=False,
    )
    for key, value in overrides.items():
        setattr(decision, key, value)
    return decision


def test_valid_minimal_lm_studio_metadata_is_non_authoritative() -> None:
    decision = _validate(_request())

    assert decision.contract_version == LOCAL_MODEL_INVENTORY_VERSION
    assert decision.inventory_status == "inventory_ready"
    assert decision.failure_reasons == ()
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_inventory is False
    assert decision.verifier_success is False
    assert decision.model_call_performed is False
    assert decision.model_loaded is False
    assert decision.endpoint_probed is False
    assert decision.auto_mode_execution_allowed is False
    assert decision.output_is_authority is False

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "coding"
    assert mapping.task_roles == ("repo_audit_candidate_notes", "code_explanation")
    assert mapping.proposal_only is True
    assert mapping.chat_generation_candidate is True
    assert mapping.active_use_allowed is False
    assert mapping.local_only_for_private_context is True
    assert mapping.auto_mode_eligibility == "local_only"


def test_valid_offline_disabled_provider_validates_without_model_entries() -> None:
    decision = _validate(
        _request(
            provider_id="offline:none",
            provider_class="offline_disabled_provider",
            provider_status="disabled_by_policy",
            models=[],
            context_policy=None,
            privacy_class=None,
            data_sensitivity_allowed=[],
        )
    )

    assert decision.inventory_status == "offline_disabled_ready"
    assert decision.failure_reasons == ()
    assert decision.role_mappings == ()
    assert decision.runtime_dispatch_allowed is False


def test_qwen25_coder_maps_to_coding_repo_audit_candidate_notes() -> None:
    decision = _validate(_request(models=[_model()]))

    mapping = decision.role_mappings[0]
    assert mapping.model_name == "Qwen2.5 Coder 14B Instruct Reason"
    assert mapping.model_role == "coding"
    assert "repo_audit_candidate_notes" in mapping.task_roles
    assert "code_explanation" in mapping.task_roles
    assert mapping.proposal_only is True
    assert mapping.auto_mode_eligibility == "local_only"


def test_deepseek_r1_distill_maps_to_reasoning_risk_analysis() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="deepseek-r1-distill-qwen-14b-q4-k-m",
                    model_name="DeepSeek R1 Distill Qwen 14B",
                    model_family="deepseek-r1-distill-qwen",
                    publisher="unsloth",
                    model_role="reasoning",
                    task_roles=["risk_analysis", "architecture_review"],
                    disk_size_bytes=8_370_000_000,
                )
            ]
        )
    )

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "reasoning"
    assert mapping.task_roles == ("risk_analysis", "architecture_review")
    assert mapping.proposal_only is True
    assert mapping.active_use_allowed is False


def test_qwen35_9b_maps_to_fast_general_wording_role() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="qwen3.5-9b-q4-k-m",
                    model_name="Qwen3.5 9B",
                    model_family="qwen",
                    publisher="qwen",
                    model_role="chat_general",
                    task_roles=["mission_control_wording", "documentation_summary"],
                    disk_size_bytes=6_100_000_000,
                    latency_class="fast_candidate",
                )
            ]
        )
    )

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "chat_general"
    assert "mission_control_wording" in mapping.task_roles
    assert mapping.chat_generation_candidate is True
    assert mapping.proposal_only is True


def test_gpt_oss_20b_maps_to_fallback_with_unknown_quality_resource() -> None:
    decision = _validate(
        _request(
            human_review_required=True,
            models=[
                _model(
                    model_id="gpt-oss-20b-q3-k-m",
                    model_name="GPT-OSS 20B",
                    model_family="gpt-oss",
                    publisher="unsloth",
                    model_role="chat_general",
                    task_roles=["documentation_summary"],
                    quantization="Q3_K_M",
                    disk_size_bytes=10_720_000_000,
                    limitations=["general fallback candidate only"],
                    unknowns=["quality, latency, context length, and resource suitability unknown"],
                    human_review_required=True,
                )
            ],
        )
    )

    assert decision.inventory_status == "inventory_ready_requires_human_review"
    mapping = decision.role_mappings[0]
    assert mapping.model_role == "chat_general"
    assert mapping.unknowns == ("quality, latency, context length, and resource suitability unknown",)
    assert mapping.proposal_only is True


def test_bge_m3_maps_to_embedding_context_retrieval_not_chat() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="text-embedding-baai-bge-m3-567m",
                    model_name="text-embedding-baai-bge-m3-567M",
                    model_family="bge-m3",
                    publisher="cPilotGod",
                    model_role="embedding",
                    model_modality="text_embedding",
                    quantization="Q8_0",
                    parameter_count="567M",
                    disk_size_bytes=634_600_000,
                    task_roles=["context_retrieval"],
                )
            ]
        )
    )

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "embedding"
    assert mapping.model_modality == "text_embedding"
    assert mapping.task_roles == ("context_retrieval",)
    assert mapping.chat_generation_candidate is False
    assert mapping.active_use_allowed is False


def test_qwen3_embedding_class_maps_to_context_retrieval_not_chat() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="qwen3-0.6b-embedding-class",
                    model_name="Qwen3 0.6B embedding-class model",
                    model_family="qwen3",
                    publisher="Qwen/DevQuasar",
                    model_role="embedding",
                    model_modality="text_embedding",
                    quantization="Q8_0",
                    parameter_count="0.6B",
                    disk_size_bytes=639_000_000,
                    task_roles=["context_retrieval"],
                )
            ]
        )
    )

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "embedding"
    assert mapping.task_roles == ("context_retrieval",)
    assert mapping.chat_generation_candidate is False


def test_qwen3_reranker_maps_to_context_reranking_not_chat() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="qwen3-reranker-0.6b",
                    model_name="Qwen Qwen3 Reranker 0.6B",
                    model_family="qwen3",
                    publisher="DevQuasar",
                    model_role="reranker",
                    model_modality="text_rerank",
                    quantization="Q8_0",
                    parameter_count="0.6B",
                    disk_size_bytes=609_540_000,
                    task_roles=["context_reranking"],
                )
            ]
        )
    )

    mapping = decision.role_mappings[0]
    assert mapping.model_role == "reranker"
    assert mapping.model_modality == "text_rerank"
    assert mapping.task_roles == ("context_reranking",)
    assert mapping.chat_generation_candidate is False


def test_qwen3_vl_is_future_gated_for_vision_not_active_by_default() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="qwen3-vl-8b-q4-k-m",
                    model_name="Qwen3 VL 8B",
                    model_family="qwen3-vl",
                    publisher="qwen",
                    model_role="vision",
                    model_modality="image_text",
                    disk_size_bytes=5_760_000_000,
                    task_roles=["visual_analysis_future_gated"],
                    human_review_required=True,
                )
            ]
        )
    )

    assert decision.inventory_status == "inventory_ready_requires_human_review"
    mapping = decision.role_mappings[0]
    assert mapping.future_gated is True
    assert mapping.active_use_allowed is False
    assert mapping.auto_mode_eligibility == "future_gated"


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        ("provider_id", None, "missing_provider_identity"),
        ("provider_class", "remote_api_provider", "unsupported_provider_class"),
        ("provider_status", "ready_for_generation", "unsupported_provider_status"),
    ],
)
def test_provider_identity_and_class_fail_safely(
    field: str,
    value: object,
    expected_reason: str,
) -> None:
    decision = _validate(_request(**{field: value}))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize("field", ["model_role", "model_modality"])
def test_missing_model_role_or_modality_is_denied(field: str) -> None:
    model = _model()
    model.pop(field)

    decision = _validate(_request(models=[model]))

    assert f"missing_{field}" in decision.failure_reasons
    assert decision.inventory_status == "blocked_by_missing_model_metadata"


def test_unknown_model_role_requires_human_review_or_blocks() -> None:
    review_ready = _validate(
        _request(
            human_review_required=True,
            models=[
                _model(
                    model_role="unknown",
                    model_modality="unknown",
                    task_roles=["unknown"],
                    human_review_required=True,
                )
            ],
        )
    )
    blocked = _validate(
        _request(
            models=[
                _model(
                    model_role="unknown",
                    model_modality="unknown",
                    task_roles=["unknown"],
                    human_review_required=False,
                )
            ]
        )
    )

    assert review_ready.inventory_status == "inventory_ready_requires_human_review"
    assert review_ready.failure_reasons == ()
    assert review_ready.role_mappings[0].auto_mode_eligibility == "blocked_by_unknown_metadata"
    assert "unknown_model_role_requires_human_review" in blocked.failure_reasons
    assert blocked.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    "model",
    [
        _model(
            model_role="embedding",
            model_modality="text_embedding",
            task_roles=["code_explanation"],
        ),
        _model(
            model_role="reranker",
            model_modality="text_rerank",
            task_roles=["mission_control_wording"],
        ),
    ],
)
def test_embedding_and_reranker_cannot_be_mapped_to_chat_generation(
    model: dict[str, object],
) -> None:
    decision = _validate(_request(models=[model]))

    assert "retrieval_model_mapped_to_chat" in decision.failure_reasons
    assert decision.role_mappings[0].chat_generation_candidate is False
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    "model",
    [
        _model(
            model_role="vision",
            model_modality="image_text",
            task_roles=["code_explanation"],
        ),
        _model(
            model_role="audio_stt",
            model_modality="audio_text",
            task_roles=["voice_interaction_future_gated"],
            active_use_requested=True,
        ),
    ],
)
def test_vision_and_audio_active_use_is_rejected_unless_future_gated(
    model: dict[str, object],
) -> None:
    decision = _validate(_request(models=[model]))

    assert "future_gated_model_active_use_denied" in decision.failure_reasons
    assert decision.role_mappings[0].active_use_allowed is False
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("context_override", "expected_reason"),
    [
        ({"can_receive_secret_like_content": True}, "raw_secret_context_denied"),
        ({"can_receive_raw_journal": True}, "raw_journal_context_denied"),
        ({"can_receive_raw_evidence": True}, "raw_evidence_context_denied"),
    ],
)
def test_raw_secret_journal_and_evidence_context_are_rejected(
    context_override: dict[str, object],
    expected_reason: str,
) -> None:
    decision = _validate(_request(context_policy=_context_policy(**context_override)))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        ("privacy_class", None, "missing_privacy_class"),
        ("data_sensitivity_allowed", [], "missing_data_sensitivity_allowed"),
        ("context_policy", None, "missing_context_policy"),
    ],
)
def test_privacy_data_sensitivity_and_context_policy_are_required(
    field: str,
    value: object,
    expected_reason: str,
) -> None:
    decision = _validate(_request(**{field: value}))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_private_repo_context_maps_local_only_by_default() -> None:
    decision = _validate(_request())

    mapping = decision.role_mappings[0]
    assert mapping.can_receive_private_repo_context is True
    assert mapping.local_only_for_private_context is True
    assert mapping.auto_mode_eligibility == "local_only"


@pytest.mark.parametrize(
    ("field", "expected_reason"),
    [
        ("model_call_performed", "model_call_request_denied"),
        ("endpoint_probed", "endpoint_probe_request_denied"),
        ("model_loaded", "model_load_request_denied"),
        ("model_downloaded", "model_download_request_denied"),
        ("model_file_read", "model_file_read_request_denied"),
        ("model_file_moved", "model_file_move_request_denied"),
        ("model_file_deleted", "model_file_delete_request_denied"),
        ("inference_performed", "inference_request_denied"),
        ("embedding_generated", "embedding_generation_request_denied"),
        ("reranking_performed", "reranking_request_denied"),
        ("api_call_performed", "api_call_request_denied"),
        ("mcp_call_performed", "mcp_call_request_denied"),
        ("tool_call_performed", "tool_call_request_denied"),
        ("memory_access_performed", "memory_access_request_denied"),
    ],
)
def test_model_provider_api_tool_memory_behavior_flags_are_rejected(
    field: str,
    expected_reason: str,
) -> None:
    decision = _validate(_request(**{field: True}))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.model_call_performed is False
    assert decision.inference_performed is False


@pytest.mark.parametrize(
    ("field", "expected_reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("evidence_provided_by_inventory", "inventory_cannot_provide_evidence"),
        ("verifier_success", "inventory_cannot_mark_verifier_success"),
        ("auto_mode_execution_allowed", "auto_mode_execution_not_allowed"),
        ("output_is_authority", "model_inventory_output_cannot_be_authority"),
    ],
)
def test_authority_grant_evidence_and_verifier_claims_are_rejected(
    field: str,
    expected_reason: str,
) -> None:
    decision = _validate(_request(**{field: True}))

    assert expected_reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.auto_mode_execution_allowed is False


@pytest.mark.parametrize(
    ("field", "expected_reason"),
    [
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("model_output_as_evidence", "model_output_evidence_claim_denied"),
        ("model_output_as_policy", "model_output_policy_claim_denied"),
        ("model_output_as_compliance_proof", "model_output_compliance_claim_denied"),
        ("proof_model_quality", "model_quality_proof_claim_denied"),
        ("security_certification", "security_certification_claim_denied"),
    ],
)
def test_model_output_as_truth_proof_or_certification_is_rejected(
    field: str,
    expected_reason: str,
) -> None:
    decision = _validate(_request(**{field: True}))

    assert expected_reason in decision.failure_reasons
    assert decision.verifier_success is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("terms_status", "accepted"),
        ("region_status", "verified"),
        ("cloud_region_status", "eu-west-1"),
    ],
)
def test_cloud_region_and_terms_claims_are_rejected_in_local_inventory(
    field: str,
    value: str,
) -> None:
    decision = _validate(_request(**{field: value}))

    assert "cloud_terms_or_region_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_nested_model_behavior_and_truth_claims_are_rejected() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_call_performed=True,
                    model_output_is_truth=True,
                    terms_status="accepted",
                )
            ]
        )
    )

    assert "model_call_request_denied" in decision.failure_reasons
    assert "model_output_truth_claim_denied" in decision.failure_reasons
    assert "cloud_terms_or_region_claim_denied" in decision.failure_reasons
    assert decision.model_call_performed is False


def test_unsafe_related_decision_is_rejected() -> None:
    decision = _validate(
        _request(),
        model_provider_readiness=_unsafe_related_decision(model_call_performed=True),
    )

    assert "model_call_request_denied" in decision.failure_reasons
    assert "unsafe_related_decision" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_execution_permission_claim_is_rejected() -> None:
    decision = _validate(_request(execution_permission="granted_by_model_inventory"))

    assert "execution_permission_claim_denied" in decision.failure_reasons
    assert decision.execution_permission == LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION


def test_input_and_supplied_decisions_are_not_mutated() -> None:
    request = _request()
    related = _unsafe_related_decision()
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _validate(request, provider_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.provider_id = "changed"  # type: ignore[misc]


def test_output_never_allows_runtime_dispatch_or_auto_mode_execution() -> None:
    decision = _validate(_request())

    assert decision.runtime_dispatch_allowed is False
    assert decision.auto_mode_execution_allowed is False
    assert decision.inventory_contract.runtime_dispatch_allowed is False
    assert decision.inventory_contract.auto_mode_execution_allowed is False
    assert all(mapping.active_use_allowed is False for mapping in decision.role_mappings)
