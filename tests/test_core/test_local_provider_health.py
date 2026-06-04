from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from aegis.core.local_provider_health import (
    LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION,
    LOCAL_PROVIDER_HEALTH_VERSION,
    validate_local_provider_health_request,
)


def _model(**overrides: object) -> dict[str, object]:
    model: dict[str, object] = {
        "model_id": "qwen2.5-coder-14b",
        "model_name": "Qwen2.5 Coder 14B Instruct Reason",
        "model_role": "coding",
        "model_modality": "text_in_text_out",
        "model_health_status": "model_metadata_only",
        "task_roles": ["repo_audit_candidate_notes", "code_explanation"],
        "resource_status": "model_resource_unknown",
        "listed_unverified": False,
    }
    model.update(overrides)
    return model


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "provider-health:aegis:1",
        "project_ref": "project:aegis",
        "tenant_scope": "local-user",
        "namespace": "local_provider_health",
        "health_check_phase": "classify_metadata_only",
        "provider_id": "lmstudio:local",
        "provider_class": "lm_studio_local",
        "provider_health_status": "configured_metadata_only",
        "endpoint_ref": "lmstudio-localhost",
        "endpoint_scheme": "http",
        "endpoint_host_class": "localhost",
        "endpoint_port": 1234,
        "api_key_required": False,
        "secret_status": "no_secret_required",
        "dependency_status": "metadata_only",
        "config_source": "backend_config",
        "process_observation_status": "provider_process_unknown",
        "resource_status": "unknown",
        "disk_status": "disk_warning",
        "ram_status": "unknown",
        "vram_status": "unknown",
        "supported_model_roles": ["coding", "reasoning", "chat_general", "embedding", "reranker"],
        "supported_modalities": ["text_in_text_out", "text_embedding", "text_rerank"],
        "models": [_model()],
        "source_refs": [{"ref_id": "synthetic:provider-health", "ref_type": "test_fixture"}],
        "policy_refs": ["policy:local-provider-health.metadata-only"],
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _safe_related(**overrides: object) -> SimpleNamespace:
    related = SimpleNamespace(
        authority=False,
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_related_contract",
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        evidence_provided_by_provider_health=False,
        verifier_success=False,
        provider_selected_for_execution=False,
        model_selected_for_execution=False,
        endpoint_probed=False,
        model_loaded=False,
        model_call_performed=False,
        data_sent_external=False,
    )
    for key, value in overrides.items():
        setattr(related, key, value)
    return related


def _validate(request: dict[str, object], **related: object):
    return validate_local_provider_health_request(request, **related)


def _assert_non_authority(decision: object) -> None:
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_provider_health is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.endpoint_probed is False
    assert decision.provider_process_inspected is False
    assert decision.provider_authenticated is False
    assert decision.api_key_validated is False
    assert decision.secret_read is False
    assert decision.model_list_requested is False
    assert decision.model_loaded is False
    assert decision.model_call_performed is False
    assert decision.minimal_generation_performed is False
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False
    assert decision.multimodal_probe_performed is False
    assert decision.context_retrieval_performed is False
    assert decision.memory_retrieval_performed is False
    assert decision.data_sent_external is False
    assert decision.provider_selected_for_execution is False
    assert decision.model_selected_for_execution is False
    assert decision.health_verified is False
    assert decision.health_check_executed is False
    assert decision.output_is_authority is False


def test_valid_lm_studio_local_metadata_is_non_authoritative() -> None:
    decision = _validate(_request())

    assert decision.contract_version == LOCAL_PROVIDER_HEALTH_VERSION
    assert decision.readiness_status == "metadata_ready"
    assert decision.provider_health_status == "configured_metadata_only"
    assert decision.model_health_status == "model_metadata_only"
    assert decision.endpoint_host_class == "localhost"
    _assert_non_authority(decision)


def test_offline_disabled_provider_validates_without_model_entries() -> None:
    decision = _validate(
        _request(
            provider_id="offline:disabled",
            provider_class="offline_disabled_provider",
            provider_health_status="offline_disabled",
            endpoint_host_class=None,
            models=[],
        )
    )

    assert decision.readiness_status == "offline_disabled_ready"
    assert decision.provider_health_status == "offline_disabled"
    assert decision.model_health_status == "model_load_not_attempted"
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    ("provider_class", "expected_gate"),
    [
        ("llama_cpp_local_future", "llama_cpp_local_future_requires_future_provider_boundary"),
        ("mlx_local_future", "mlx_local_future_requires_future_provider_boundary"),
    ],
)
def test_future_provider_classes_are_future_gated(provider_class: str, expected_gate: str) -> None:
    decision = _validate(_request(provider_class=provider_class))

    assert decision.readiness_status == "future_gated"
    assert expected_gate in decision.required_future_gates
    _assert_non_authority(decision)


@pytest.mark.parametrize(
    "phase",
    [
        "propose_endpoint_probe_future",
        "propose_model_list_future",
        "propose_model_load_future",
        "propose_minimal_generation_future",
        "propose_embedding_probe_future",
        "propose_reranker_probe_future",
    ],
)
def test_future_probe_phases_are_future_gated_not_executed(phase: str) -> None:
    decision = _validate(_request(health_check_phase=phase))

    assert decision.readiness_status == "future_gated"
    assert f"{phase}_requires_future_probe_boundary" in decision.required_future_gates
    _assert_non_authority(decision)


@pytest.mark.parametrize("field", ["provider_id", "provider_class", "request_id", "project_ref", "tenant_scope", "namespace"])
def test_missing_required_identity_fields_block(field: str) -> None:
    decision = _validate(_request(**{field: None}))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert f"missing_{field}" in decision.failure_reasons
    _assert_non_authority(decision)


def test_missing_model_metadata_blocks_non_metadata_phase() -> None:
    decision = _validate(_request(health_check_phase="validate_config_shape", models=[]))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert "missing_model_metadata" in decision.failure_reasons


def test_unsupported_provider_class_denied() -> None:
    decision = _validate(_request(provider_class="remote_cloud_api"))

    assert decision.readiness_status == "blocked_by_missing_required_field"
    assert "unsupported_provider_class" in decision.failure_reasons


@pytest.mark.parametrize("endpoint_host_class", ["lan", "remote", "cloud"])
def test_non_local_endpoint_hosts_are_blocked(endpoint_host_class: str) -> None:
    decision = _validate(_request(endpoint_host_class=endpoint_host_class))

    assert decision.readiness_status == "blocked_by_endpoint_policy"
    assert "non_local_endpoint_host_blocked" in decision.failure_reasons
    assert "non_local_endpoint_requires_future_boundary" in decision.required_future_gates
    _assert_non_authority(decision)


def test_unknown_endpoint_host_requires_human_review() -> None:
    blocked = _validate(_request(endpoint_host_class="unknown"))
    reviewed = _validate(_request(endpoint_host_class="unknown", human_review_required=True))

    assert blocked.readiness_status == "blocked_by_endpoint_policy"
    assert "unknown_endpoint_requires_human_review" in blocked.failure_reasons
    assert reviewed.readiness_status == "metadata_ready_requires_human_review"
    _assert_non_authority(reviewed)


def test_endpoint_reachable_unverified_future_is_not_health_verification() -> None:
    decision = _validate(_request(provider_health_status="endpoint_reachable_unverified_future"))

    assert decision.provider_health_status == "endpoint_reachable_unverified_future"
    assert decision.health_verified is False
    assert decision.endpoint_probed is False


def test_process_observed_metadata_only_is_not_process_inspection() -> None:
    decision = _validate(_request(process_observation_status="provider_process_observed_metadata_only"))

    assert decision.provider_config.process_observation_status == "provider_process_observed_metadata_only"
    assert decision.provider_process_inspected is False
    assert decision.health_verified is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("api_key_required", "api_key_requirement_out_of_scope"),
        ("secret_status", "secret_status_out_of_scope"),
    ],
)
def test_api_key_and_secret_metadata_do_not_validate_secrets(field: str, reason: str) -> None:
    value: object = True if field == "api_key_required" else "secret_present_unverified"
    decision = _validate(_request(**{field: value}))

    assert decision.readiness_status == "blocked_by_secret_policy"
    assert reason in decision.failure_reasons
    assert decision.secret_read is False
    assert decision.api_key_validated is False


@pytest.mark.parametrize(
    ("provider_status_field", "value", "reason"),
    [
        ("resource_status", "resource_blocked", "provider_resource_blocked"),
        ("provider_health_status", "disk_pressure_blocked", "provider_resource_blocked"),
        ("disk_status", "disk_pressure_blocked", "provider_disk_pressure_blocked"),
    ],
)
def test_resource_and_disk_pressure_block(provider_status_field: str, value: str, reason: str) -> None:
    decision = _validate(_request(**{provider_status_field: value}))

    assert decision.readiness_status == "blocked_by_resource"
    assert reason in decision.failure_reasons


def test_lower_trust_frontend_config_is_metadata_only_not_authority() -> None:
    decision = _validate(_request(config_source="frontend_projection"))

    assert decision.readiness_status == "metadata_ready"
    assert decision.lower_trust_config_source is True
    assert decision.config_trust_level == "lower_trust_metadata_only"
    assert decision.frontend_authority is False


def test_qwen_coder_like_model_maps_as_metadata_only_coding_candidate() -> None:
    decision = _validate(_request(models=[_model()]))

    model = decision.model_metadata[0]
    assert model.model_id == "qwen2.5-coder-14b"
    assert model.model_role == "coding"
    assert model.task_roles == ("repo_audit_candidate_notes", "code_explanation")
    assert decision.model_selected_for_execution is False


def test_deepseek_reasoning_like_model_maps_as_risk_analysis_metadata() -> None:
    decision = _validate(
        _request(
            models=[
                _model(
                    model_id="deepseek-r1-distill-qwen-14b",
                    model_name="DeepSeek R1 Distill Qwen 14B",
                    model_role="reasoning",
                    task_roles=["risk_analysis", "architecture_review"],
                )
            ]
        )
    )

    assert decision.readiness_status == "metadata_ready"
    assert decision.model_metadata[0].model_role == "reasoning"
    assert decision.model_call_performed is False


def test_gemma_and_qwen_vl_like_multimodal_models_are_future_gated() -> None:
    decision = _validate(
        _request(
            health_check_phase="propose_multimodal_probe_future",
            models=[
                _model(
                    model_id="gemma-4-12b",
                    model_name="Gemma 4 12B",
                    model_role="multimodal",
                    model_modality="multimodal",
                    task_roles=["visual_analysis_future_gated"],
                ),
                _model(
                    model_id="qwen3-vl-8b",
                    model_name="Qwen3 VL 8B",
                    model_role="vision",
                    model_modality="image_text",
                    task_roles=["visual_analysis_future_gated"],
                ),
            ],
        )
    )

    assert decision.readiness_status == "future_gated"
    assert decision.model_health_status == "model_modality_future_gated"
    assert "multimodal_or_voice_model_requires_future_privacy_boundary" in decision.required_future_gates
    assert decision.multimodal_probe_performed is False


@pytest.mark.parametrize(
    "model",
    [
        _model(model_role="embedding", model_modality="text_embedding", task_roles=["repo_audit_candidate_notes"]),
        _model(model_role="reranker", model_modality="text_rerank", task_roles=["code_explanation"]),
    ],
)
def test_embedding_and_reranker_cannot_be_mapped_to_chat_tasks(model: dict[str, object]) -> None:
    decision = _validate(_request(models=[model]))

    assert decision.readiness_status == "blocked_by_model_policy"
    assert "retrieval_model_mapped_to_chat" in decision.failure_reasons
    assert decision.model_call_performed is False


@pytest.mark.parametrize(
    ("model", "expected_role"),
    [
        (
            _model(
                model_id="text-embedding-baai-bge-m3-567m",
                model_name="text-embedding-baai-bge-m3-567M",
                model_role="embedding",
                model_modality="text_embedding",
                task_roles=["context_retrieval"],
            ),
            "embedding",
        ),
        (
            _model(
                model_id="qwen3-reranker-0.6b",
                model_name="Qwen3 Reranker 0.6B",
                model_role="reranker",
                model_modality="text_rerank",
                task_roles=["context_reranking"],
            ),
            "reranker",
        ),
    ],
)
def test_embedding_and_reranker_metadata_is_not_execution(model: dict[str, object], expected_role: str) -> None:
    decision = _validate(_request(models=[model]))

    assert decision.readiness_status == "metadata_ready"
    assert decision.model_metadata[0].model_role == expected_role
    assert decision.embedding_generated is False
    assert decision.reranking_performed is False


def test_model_listed_unverified_future_is_not_loaded_or_verified() -> None:
    decision = _validate(_request(models=[_model(listed_unverified=True, model_health_status="model_listed_unverified_future")]))

    assert decision.readiness_status == "future_gated"
    assert decision.model_health_status == "model_listed_unverified_future"
    assert "model_list_status_requires_future_probe_evidence" in decision.required_future_gates
    assert decision.model_loaded is False
    assert decision.health_verified is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_id", "missing_model_id"),
        ("model_name", "missing_model_name"),
        ("model_role", "missing_model_role"),
        ("model_modality", "missing_model_modality"),
    ],
)
def test_missing_model_fields_block(field: str, reason: str) -> None:
    decision = _validate(_request(models=[_model(**{field: None})]))

    assert reason in decision.failure_reasons
    assert decision.readiness_status in {"blocked_by_missing_required_field", "blocked_by_model_policy"}


def test_unknown_model_role_requires_human_review_or_blocks() -> None:
    blocked = _validate(_request(models=[_model(model_role="unknown", model_modality="unknown", task_roles=["unknown"])]))
    reviewed = _validate(
        _request(
            human_review_required=True,
            models=[_model(model_role="unknown", model_modality="unknown", task_roles=["unknown"])],
        )
    )

    assert "unknown_model_role_requires_human_review" in blocked.failure_reasons
    assert blocked.readiness_status == "blocked_by_model_policy"
    assert reviewed.readiness_status == "metadata_ready_requires_human_review"


def test_model_loaded_unverified_future_status_is_out_of_scope() -> None:
    decision = _validate(_request(models=[_model(model_health_status="model_loaded_unverified_future")]))

    assert decision.readiness_status == "blocked_by_execution_claim"
    assert "model_loaded_status_out_of_scope" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("endpoint_probed", "endpoint_probe_request_denied"),
        ("provider_process_inspected", "provider_process_inspection_denied"),
        ("provider_authenticated", "provider_authentication_denied"),
        ("api_key_validated", "api_key_validation_denied"),
        ("secret_read", "secret_read_denied"),
        ("model_list_requested", "model_list_request_denied"),
        ("model_loaded", "model_load_request_denied"),
        ("model_call_performed", "model_call_request_denied"),
        ("minimal_generation_performed", "minimal_generation_request_denied"),
        ("embedding_generated", "embedding_generation_request_denied"),
        ("reranking_performed", "reranking_request_denied"),
        ("multimodal_probe_performed", "multimodal_probe_request_denied"),
        ("context_retrieval_performed", "context_retrieval_request_denied"),
        ("memory_retrieval_performed", "memory_retrieval_request_denied"),
        ("data_sent_external", "external_data_transfer_denied"),
        ("api_call_performed", "api_call_request_denied"),
        ("mcp_call_performed", "mcp_call_request_denied"),
        ("tool_call_performed", "tool_call_request_denied"),
        ("health_check_executed", "health_check_execution_denied"),
    ],
)
def test_behavior_flags_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

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
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("evidence_provided_by_provider_health", "provider_health_cannot_provide_evidence"),
        ("verifier_success", "provider_health_cannot_mark_verifier_success"),
        ("health_verified", "provider_health_cannot_verify_health"),
        ("provider_selected_for_execution", "provider_execution_selection_not_allowed"),
        ("model_selected_for_execution", "model_execution_selection_not_allowed"),
        ("model_output_is_truth", "model_output_truth_claim_denied"),
        ("proof_model_health", "model_health_proof_denied"),
        ("certification_claim", "certification_claim_denied"),
    ],
)
def test_authority_grant_evidence_verifier_and_proof_claims_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert reason in decision.failure_reasons
    _assert_non_authority(decision)


def test_execution_permission_claim_is_rejected() -> None:
    decision = _validate(_request(execution_permission="granted_by_provider_health"))

    assert decision.readiness_status == "blocked_by_execution_claim"
    assert "execution_permission_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("related_name", "related_value"),
    [
        ("local_model_inventory_decision", _safe_related(model_loaded=True)),
        ("model_auto_mode_decision", _safe_related(provider_selected_for_execution=True)),
        ("context_policy_decision", _safe_related(data_sent_external=True)),
        ("policy_extension_decision", _safe_related(runtime_dispatch_allowed=True)),
        ("identity_scope_decision", _safe_related(authority=True)),
        ("memory_governance_decision", _safe_related(memory_retrieval_performed=True)),
        ("mission_control_decision", _safe_related(model_call_performed=True)),
        ("tool_simulation_decision", _safe_related(tool_call_performed=True)),
    ],
)
def test_unsafe_related_decisions_are_rejected(related_name: str, related_value: object) -> None:
    decision = _validate(_request(), **{related_name: related_value})

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "unsafe_related_decision" in decision.failure_reasons
    _assert_non_authority(decision)


def test_local_model_inventory_metadata_alone_does_not_authorize_health_probe() -> None:
    decision = _validate(
        _request(health_check_phase="propose_endpoint_probe_future"),
        local_model_inventory_decision=SimpleNamespace(
            inventory_status="inventory_ready",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_local_model_inventory",
            endpoint_probed=False,
            model_call_performed=False,
        ),
    )

    assert decision.readiness_status == "future_gated"
    assert decision.endpoint_probed is False
    assert decision.health_check_executed is False


def test_auto_mode_candidate_does_not_authorize_provider_selection_or_probe() -> None:
    decision = _validate(
        _request(),
        model_auto_mode_decision=SimpleNamespace(
            selection_mode="local_model_candidate",
            provider_selected=False,
            provider_selected_for_execution=False,
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_model_auto_mode",
        ),
    )

    assert decision.readiness_status == "metadata_ready"
    assert decision.provider_selected_for_execution is False
    assert decision.endpoint_probed is False


def test_blocked_context_policy_blocks_provider_health_readiness() -> None:
    decision = _validate(
        _request(),
        context_policy_decision=SimpleNamespace(
            policy_status="blocked_by_secret_policy",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_context_policy",
        ),
    )

    assert decision.readiness_status == "blocked_by_context_policy"
    assert "context_policy_not_ready" in decision.failure_reasons


def test_blocked_policy_extension_blocks_provider_health_readiness() -> None:
    decision = _validate(
        _request(),
        policy_extension_decision=SimpleNamespace(
            policy_outcome="blocked_by_policy",
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_policy_extension",
        ),
    )

    assert decision.readiness_status == "blocked_by_policy_extension"
    assert "policy_extension_not_ready" in decision.failure_reasons


def test_input_and_related_decisions_are_not_mutated() -> None:
    request = _request(source_refs=[{"ref_id": "source", "nested": {"value": 1}}])
    related = _safe_related(nested={"value": 1})
    request_before = deepcopy(request)
    related_before = deepcopy(related.__dict__)

    decision = _validate(request, mission_control_decision=related)

    assert request == request_before
    assert related.__dict__ == related_before
    with pytest.raises(FrozenInstanceError):
        decision.health_input.namespace = "mutated"  # type: ignore[union-attr,misc]


def test_output_never_sets_execution_or_health_verification_flags() -> None:
    decision = _validate(_request())

    _assert_non_authority(decision)
