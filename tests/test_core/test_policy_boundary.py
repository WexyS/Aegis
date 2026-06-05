from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.identity_scope import validate_identity_scope_request
from aegis.core.local_model_inventory import validate_local_model_inventory_request
from aegis.core.memory_governance import validate_memory_governance_request
from aegis.core.policy_boundary import (
    POST_FOUNDATION_POLICY_VERSION,
    POLICY_BOUNDARY_VERSION,
    POLICY_DISPATCHABLE_TOOL_NAMES,
    POLICY_EXTENSION_EXECUTION_PERMISSION,
    POLICY_OUTCOMES,
    approval_resolution_can_resume,
    evaluate_capability_policy_contract,
    evaluate_policy_boundary,
    evaluate_policy_extension_request,
    side_effects_missing_dispatch_contract,
)


def _policy_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "subject_kind": "context_operation",
        "action_kind": "metadata_validation",
        "policy_rule_ref": "policy:test",
        "namespace": "policy_extension_test",
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": POLICY_EXTENSION_EXECUTION_PERMISSION,
    }
    request.update(overrides)
    return request


def _identity_scope_ready() -> object:
    return validate_identity_scope_request(
        {
            "request_id": "scope-1",
            "subject_kind": "project",
            "namespace": "aegis",
            "privacy_class": "private",
            "data_boundary": "project_local_only",
            "persistence_scope": "project_scoped",
            "project_ref": "Aegis",
            "session_ref": "session-1",
        }
    )


def _identity_scope_blocked() -> object:
    return validate_identity_scope_request(
        {
            "request_id": "scope-blocked",
            "subject_kind": "unknown",
            "namespace": "aegis",
            "privacy_class": "private",
            "persistence_scope": "session_only",
            "session_ref": "session-1",
        }
    )


def _memory_governance_ready() -> object:
    return validate_memory_governance_request(
        {
            "request_id": "memory-1",
            "memory_category": "task_session_memory",
            "memory_status": "proposed",
            "operation": "propose_write",
            "memory_scope": "session_only",
            "namespace": "aegis",
            "privacy_class": "private",
            "sensitivity_class": "internal",
            "retention_policy": "no_persistence",
            "session_ref": "session-1",
        }
    )


def _local_model_inventory_ready() -> object:
    return validate_local_model_inventory_request(
        {
            "request_id": "model-1",
            "project_ref": "Aegis",
            "tenant_scope": "local-single-user",
            "namespace": "aegis",
            "provider_id": "lm-studio",
            "provider_class": "lm_studio_local",
            "provider_status": "configured_metadata_only",
            "privacy_class": "private",
            "data_sensitivity_allowed": ["private"],
            "context_policy": {
                "max_context_tokens": 4096,
                "recommended_context_budget": 2048,
                "can_receive_private_repo_context": True,
                "can_receive_secret_like_content": False,
                "can_receive_raw_journal": False,
                "requires_redaction": True,
                "requires_source_refs": True,
                "output_requires_validation": True,
            },
            "models": [
                {
                    "model_id": "qwen-coder",
                    "model_name": "Qwen2.5 Coder synthetic",
                    "model_role": "coding",
                    "model_modality": "text_in_text_out",
                    "task_roles": ["repo_audit_candidate_notes"],
                    "terms_status": "local_only",
                    "region_status": "local_only",
                }
            ],
        }
    )


def _assert_policy_extension_non_authority(decision: object) -> None:
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == POLICY_EXTENSION_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_policy is False
    assert decision.verifier_success is False
    assert decision.frontend_authority is False


def test_generic_click_is_not_dispatchable_policy_surface() -> None:
    assert "click" not in POLICY_DISPATCHABLE_TOOL_NAMES


def test_policy_dispatchable_tool_names_do_not_expand_without_guard_update() -> None:
    expected_dispatchable = {
        "read_file",
        "list_directory",
        "search_files",
        "grep_in_files",
        "file_info",
        "write_file",
        "create_file",
        "edit_file",
        "read_page",
        "scroll",
        "search_web",
        "open_url",
        "type",
        "open_app",
        "focus_app",
        "close_app",
        "run_command",
        "git_action",
        "general_chat",
    }

    assert POLICY_DISPATCHABLE_TOOL_NAMES == expected_dispatchable
    assert {
        "click",
        "browser_click",
        "desktop_click",
        "model_call",
        "cloud_model_call",
        "context_retrieve",
        "memory_write",
        "memory_retrieve",
        "vector_index",
        "embedding_generate",
        "rerank",
        "web_query",
        "repo_file_read",
        "plugin_execute",
        "lease_use",
    }.isdisjoint(POLICY_DISPATCHABLE_TOOL_NAMES)


def test_policy_boundary_allows_ready_decision_only_after_policy_classification() -> None:
    decision = classify_intent_risk("open_app", {"app": "notepad"})

    boundary = evaluate_policy_boundary(decision)

    assert decision.decision_status == DecisionStatus.READY
    assert boundary.boundary_version == POLICY_BOUNDARY_VERSION
    assert boundary.dispatch_allowed is True
    assert boundary.not_executed is False
    assert boundary.policy_rule == "open_app.known_app.ready"


def test_policy_boundary_blocks_clarification_even_if_approval_flag_is_present() -> None:
    decision = classify_intent_risk("click", {})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert boundary.dispatch_allowed is False
    assert boundary.requires_clarification is True
    assert boundary.not_executed is True


def test_policy_boundary_blocks_quarantined_click_approval_resume() -> None:
    decision = classify_intent_risk("click", {"x": 10, "y": 20})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert approval_resolution_can_resume(decision) is False
    assert boundary.dispatch_allowed is False
    assert boundary.resume_allowed is False
    assert boundary.not_executed is True


def test_policy_boundary_allows_resumable_approval_only_for_policy_eligible_actions() -> None:
    decision = classify_intent_risk("write_file", {"path": "scratch/a.txt", "content": "ok"})

    without_approval = evaluate_policy_boundary(decision, approval_granted=False)
    with_approval = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert approval_resolution_can_resume(decision) is True
    assert without_approval.dispatch_allowed is False
    assert with_approval.dispatch_allowed is True
    assert with_approval.resume_allowed is True


def test_policy_boundary_never_dispatches_blocked_decision() -> None:
    decision = classify_intent_risk("run_command", {"command": "reg delete HKCU\\Software\\Aegis /f"})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.BLOCKED
    assert boundary.dispatch_allowed is False
    assert boundary.blocked is True
    assert boundary.not_executed is True


def test_side_effect_dispatch_contract_identifies_missing_dispatchable_tool() -> None:
    plan = [SimpleNamespace(intent="open_app"), SimpleNamespace(intent="read_file")]

    missing = side_effects_missing_dispatch_contract(
        plan,
        tool_spec_lookup=lambda name: SimpleNamespace(side_effecting=name == "open_app"),
        dispatchable_tool_names=POLICY_DISPATCHABLE_TOOL_NAMES - {"open_app"},
    )

    assert missing == ["open_app"]


def test_post_foundation_policy_unknown_capability_is_denied() -> None:
    decision = evaluate_capability_policy_contract(
        "unknown_capability",
        "read_only",
        policy_rule="future.unknown",
    )

    assert decision.policy_version == POST_FOUNDATION_POLICY_VERSION
    assert decision.known_capability is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == "not_granted_by_policy_extension"
    assert decision.decision_status == "denied"
    assert "unknown_capability" in decision.blocked_reasons


def test_post_foundation_policy_untrusted_authorities_cannot_grant_permission() -> None:
    for authority in ("context_compiler", "memory", "model_output", "plugin_manifest", "frontend_projection"):
        decision = evaluate_capability_policy_contract(
            "context_compilation",
            "read_only",
            source_authority=authority,
            policy_rule="context.read_only",
        )

        assert decision.contract_ready is False
        assert decision.runtime_dispatch_allowed is False
        assert decision.execution_permission == "not_granted_by_policy_extension"
        assert f"{authority}_cannot_grant_permission" in decision.blocked_reasons
        assert decision.context_may_grant_permission is False
        assert decision.memory_may_grant_permission is False
        assert decision.model_may_grant_permission is False
        assert decision.plugin_manifest_may_grant_permission is False
        assert decision.frontend_may_grant_permission is False


def test_post_foundation_policy_side_effecting_tier_requires_approval_and_evidence() -> None:
    decision = evaluate_capability_policy_contract(
        "local_tool_write",
        "local_file_write",
        policy_rule="local_tool_write.requires_approval_and_evidence",
    )

    assert decision.approval_required is True
    assert decision.evidence_required is True
    assert decision.approval_granted is False
    assert decision.evidence_expectation_present is False
    assert decision.runtime_dispatch_allowed is False
    assert "approval_required" in decision.blocked_reasons
    assert "missing_evidence_expectation" in decision.blocked_reasons


def test_post_foundation_policy_approval_alone_is_not_execution_permission() -> None:
    decision = evaluate_capability_policy_contract(
        "app_launch",
        "app_launch",
        policy_rule="app_launch.requires_evidence",
        approval_granted=True,
        evidence_expectation={"verifier": "desktop-process-window"},
    )

    assert decision.contract_ready is True
    assert decision.approval_granted is True
    assert decision.evidence_expectation_present is True
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == "not_granted_by_policy_extension"
    assert decision.decision_status == "denied"


def test_post_foundation_policy_cleanup_archive_and_compaction_require_operator_boundary() -> None:
    archive = evaluate_capability_policy_contract(
        "cleanup_archive",
        "cleanup_archive",
        policy_rule="cleanup.archive.requires_boundary",
        approval_granted=True,
        evidence_expectation={"checks": ["backup", "restore", "replay", "hash-chain"]},
    )
    compaction = evaluate_capability_policy_contract(
        "cleanup_compaction",
        "cleanup_compaction",
        policy_rule="cleanup.compaction.requires_boundary",
        approval_granted=True,
        evidence_expectation={"checks": ["backup", "restore", "replay", "hash-chain"]},
    )

    assert archive.runtime_dispatch_allowed is False
    assert compaction.runtime_dispatch_allowed is False
    assert "operator_boundary_required" in archive.blocked_reasons
    assert "operator_boundary_required" in compaction.blocked_reasons


def test_post_foundation_policy_read_only_contract_can_be_review_ready_not_dispatchable() -> None:
    decision = evaluate_capability_policy_contract(
        "context_compilation",
        "read_only",
        policy_rule="context_compilation.read_only",
    )

    assert decision.contract_ready is True
    assert decision.decision_status == "review_ready"
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == "not_granted_by_policy_extension"
    assert decision.approval_required is False
    assert decision.evidence_required is False


def test_policy_extension_unknown_subject_and_action_are_unsupported_not_dispatchable() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="unrecognized", action_kind="unrecognized")
    )

    assert decision.policy_version == POST_FOUNDATION_POLICY_VERSION
    assert decision.policy_outcome == "unsupported"
    assert decision.policy_outcome in POLICY_OUTCOMES
    assert "unknown_subject_kind" in decision.blocked_reasons
    assert "unknown_action_kind" in decision.blocked_reasons
    assert "requires_human_review" in decision.required_gates
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_metadata_validation_is_metadata_only_not_execution() -> None:
    decision = evaluate_policy_extension_request(_policy_request())

    assert decision.policy_outcome == "allowed_metadata_only"
    assert decision.blocked_reasons == ()
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_proposal_only_is_proposal_not_grant_or_evidence() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="tool_action", action_kind="proposal_only")
    )

    assert decision.policy_outcome == "allowed_proposal_only"
    assert decision.blocked_reasons == ()
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_rejects_policy_success_evidence_and_verifier_claims() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(
            evidence_created=True,
            verifier_success=True,
            success=True,
            model_output_as_evidence=True,
        )
    )

    assert decision.policy_outcome == "blocked_by_policy"
    assert "policy_cannot_provide_evidence" in decision.blocked_reasons
    assert "policy_cannot_mark_verifier_success" in decision.blocked_reasons
    assert "success_claim_denied" in decision.blocked_reasons
    assert "model_output_evidence_claim_denied" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_does_not_mutate_request_or_related_decisions() -> None:
    request = _policy_request(action_kind="memory_write")
    related = {"governance_status": "proposal_ready", "runtime_dispatch_allowed": False}
    request_before = deepcopy(request)
    related_before = deepcopy(related)

    decision = evaluate_policy_extension_request(
        request,
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=related,
    )

    assert request == request_before
    assert related == related_before
    assert decision.policy_outcome == "allowed_proposal_only"
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_memory_write_requires_memory_governance() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="memory_operation", action_kind="memory_write"),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.policy_outcome == "blocked_by_missing_governance"
    assert "missing_memory_governance" in decision.blocked_reasons
    assert "requires_memory_governance" in decision.required_gates
    assert decision.memory_write_allowed is False
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_memory_retrieve_requires_memory_governance() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="memory_operation", action_kind="memory_retrieve"),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.policy_outcome == "blocked_by_missing_governance"
    assert "missing_memory_governance" in decision.blocked_reasons
    assert decision.memory_retrieval_allowed is False
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_valid_memory_governance_remains_proposal_only() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="memory_operation", action_kind="memory_write"),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
    )

    assert decision.policy_outcome == "allowed_proposal_only"
    assert decision.blocked_reasons == ()
    assert decision.memory_write_allowed is False
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_secret_like_memory_operation_is_blocked() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(
            subject_kind="memory_operation",
            action_kind="memory_write",
            sensitivity_class="secret_like",
        ),
        identity_scope_decision=_identity_scope_ready(),
        memory_governance_decision=_memory_governance_ready(),
    )

    assert decision.policy_outcome == "blocked_by_sensitive_data"
    assert "sensitive_data_blocked_by_default" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_unknown_identity_blocks_persistent_memory_policy() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="memory_operation", action_kind="memory_write"),
        identity_scope_decision=_identity_scope_blocked(),
        memory_governance_decision=_memory_governance_ready(),
    )

    assert decision.policy_outcome == "blocked_by_unknown_scope"
    assert "identity_scope_not_ready" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_model_call_requires_future_auto_mode_and_provider_health() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="model_operation", action_kind="model_call")
    )

    assert decision.policy_outcome == "blocked_by_unimplemented_feature"
    assert "model_execution_unimplemented" in decision.blocked_reasons
    assert "requires_model_auto_mode" in decision.required_gates
    assert "requires_provider_health_check" in decision.required_gates
    assert decision.model_call_allowed is False
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_cloud_model_call_requires_future_region_terms_and_secret_policy() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="model_operation", action_kind="cloud_model_call"),
        identity_scope_decision=_identity_scope_ready(),
    )

    assert decision.policy_outcome == "blocked_by_unimplemented_feature"
    assert "cloud_model_policy_missing" in decision.blocked_reasons
    assert "requires_region_policy" in decision.required_gates
    assert "requires_terms_policy" in decision.required_gates
    assert "requires_secret_policy" in decision.required_gates
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_local_model_inventory_metadata_alone_is_not_model_permission() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="model_operation", action_kind="model_call"),
        local_model_inventory_decision=_local_model_inventory_ready(),
    )

    assert decision.policy_outcome == "blocked_by_unimplemented_feature"
    assert "local_model_inventory_metadata_is_not_model_permission" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_legacy_router_hint_does_not_allow_model_call() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(
            subject_kind="model_operation",
            action_kind="model_call",
            legacy_router_model_hint="qwen-coder",
        )
    )

    assert decision.policy_outcome == "blocked_by_unimplemented_feature"
    assert "legacy_router_hint_not_model_permission" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_context_package_is_metadata_not_permission() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="context_operation", action_kind="context_package"),
        identity_scope_decision=_identity_scope_ready(),
        context_compiler_decision=SimpleNamespace(
            runtime_dispatch_allowed=False,
            execution_permission="not_granted_by_context",
            capability_grant=False,
        ),
    )

    assert decision.policy_outcome == "allowed_proposal_only"
    assert decision.context_retrieval_allowed is False
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_context_retrieve_vector_embedding_and_rerank_are_blocked() -> None:
    cases = [
        ("context_operation", "context_retrieve", "requires_context_policy"),
        ("vector_operation", "vector_index", "requires_vector_policy"),
        ("vector_operation", "embedding_generate", "requires_vector_policy"),
        ("vector_operation", "rerank", "requires_vector_policy"),
    ]

    for subject, action, gate in cases:
        decision = evaluate_policy_extension_request(
            _policy_request(subject_kind=subject, action_kind=action),
            identity_scope_decision=_identity_scope_ready(),
        )

        assert decision.policy_outcome == "blocked_by_unimplemented_feature"
        assert gate in decision.required_gates
        assert decision.vector_index_allowed is False
        assert decision.context_retrieval_allowed is False
        _assert_policy_extension_non_authority(decision)


def test_policy_extension_web_and_repo_reads_are_blocked_until_future_gates() -> None:
    web = evaluate_policy_extension_request(
        _policy_request(subject_kind="web_research_operation", action_kind="web_query")
    )
    repo = evaluate_policy_extension_request(
        _policy_request(subject_kind="repo_audit_operation", action_kind="repo_file_read"),
        identity_scope_decision=_identity_scope_ready(),
        repo_audit_decision=SimpleNamespace(runtime_dispatch_allowed=False, authority=False),
    )

    assert web.policy_outcome == "blocked_by_unimplemented_feature"
    assert "requires_web_research_gateway_policy" in web.required_gates
    assert web.web_query_allowed is False
    assert repo.policy_outcome == "blocked_by_unimplemented_feature"
    assert "repo_file_read_unimplemented" in repo.blocked_reasons
    assert "requires_source_read_plan" in repo.required_gates
    assert repo.repo_file_read_allowed is False
    _assert_policy_extension_non_authority(web)
    _assert_policy_extension_non_authority(repo)


def test_policy_extension_external_agent_mcp_and_frontend_authority_claims_are_blocked() -> None:
    external = evaluate_policy_extension_request(
        _policy_request(subject_kind="external_agent_operation", action_kind="external_agent_track"),
        identity_scope_decision=_identity_scope_ready(),
    )
    mcp = evaluate_policy_extension_request(
        _policy_request(subject_kind="mcp_output", action_kind="mcp_authority_claim")
    )
    frontend = evaluate_policy_extension_request(
        _policy_request(subject_kind="frontend_request", action_kind="frontend_authority_claim")
    )

    assert external.policy_outcome == "blocked_by_unimplemented_feature"
    assert external.external_agent_tracking_allowed is False
    assert mcp.policy_outcome == "blocked_by_mcp_authority"
    assert frontend.policy_outcome == "blocked_by_frontend_authority"
    _assert_policy_extension_non_authority(external)
    _assert_policy_extension_non_authority(mcp)
    _assert_policy_extension_non_authority(frontend)


def test_policy_extension_plugin_review_and_vertical_metadata_do_not_allow_execution() -> None:
    plugin = evaluate_policy_extension_request(
        _policy_request(subject_kind="plugin_operation", action_kind="plugin_execute"),
        plugin_review_decision=SimpleNamespace(runtime_dispatch_allowed=False, authority=False),
    )
    vertical = evaluate_policy_extension_request(
        _policy_request(subject_kind="vertical_pack_operation", action_kind="proposal_only")
    )

    assert plugin.policy_outcome == "blocked_by_unimplemented_feature"
    assert plugin.plugin_execution_allowed is False
    assert "requires_plugin_policy" in plugin.required_gates
    assert vertical.policy_outcome == "allowed_proposal_only"
    _assert_policy_extension_non_authority(plugin)
    _assert_policy_extension_non_authority(vertical)


def test_policy_extension_lease_playbook_and_rollback_execution_are_blocked() -> None:
    cases = [
        ("capability_lease_operation", "lease_create", "requires_capability_lease_policy"),
        ("capability_lease_operation", "lease_use", "requires_capability_lease_policy"),
        ("playbook_operation", "playbook_replay", "requires_playbook_policy"),
        ("rollback_operation", "rollback_execute", "requires_rollback_contract"),
        ("rollback_operation", "rollback_snapshot", "requires_rollback_contract"),
    ]

    for subject, action, gate in cases:
        decision = evaluate_policy_extension_request(
            _policy_request(subject_kind=subject, action_kind=action),
            identity_scope_decision=_identity_scope_ready(),
        )

        assert decision.policy_outcome == "blocked_by_unimplemented_feature"
        assert gate in decision.required_gates
        assert decision.playbook_execution_allowed is False
        assert decision.rollback_execution_allowed is False
        _assert_policy_extension_non_authority(decision)


def test_policy_extension_unsafe_related_decisions_are_rejected() -> None:
    decision = evaluate_policy_extension_request(
        _policy_request(subject_kind="context_operation", action_kind="context_package"),
        identity_scope_decision=_identity_scope_ready(),
        context_compiler_decision=SimpleNamespace(
            runtime_dispatch_allowed=True,
            evidence_provided_by_inventory=True,
            verifier_success=True,
        ),
    )

    assert decision.policy_outcome == "blocked_by_policy"
    assert "unsafe_related_decision" in decision.blocked_reasons
    assert "runtime_dispatch_not_allowed" in decision.blocked_reasons
    assert "policy_cannot_provide_evidence" in decision.blocked_reasons
    assert "policy_cannot_mark_verifier_success" in decision.blocked_reasons
    _assert_policy_extension_non_authority(decision)


def test_policy_extension_does_not_expand_existing_dispatchable_tool_names() -> None:
    future_actions = {
        "memory_write",
        "model_call",
        "cloud_model_call",
        "context_retrieve",
        "vector_index",
        "embedding_generate",
        "rerank",
        "web_query",
        "repo_file_read",
        "external_agent_track",
        "plugin_execute",
        "lease_use",
        "playbook_replay",
        "rollback_execute",
    }

    assert future_actions.isdisjoint(POLICY_DISPATCHABLE_TOOL_NAMES)
