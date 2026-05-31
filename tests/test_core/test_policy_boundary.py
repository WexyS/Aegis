from __future__ import annotations

from types import SimpleNamespace

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.policy_boundary import (
    POST_FOUNDATION_POLICY_VERSION,
    POLICY_BOUNDARY_VERSION,
    POLICY_DISPATCHABLE_TOOL_NAMES,
    approval_resolution_can_resume,
    evaluate_capability_policy_contract,
    evaluate_policy_boundary,
    side_effects_missing_dispatch_contract,
)


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
