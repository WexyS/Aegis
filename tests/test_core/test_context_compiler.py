import json
from copy import deepcopy

from aegis.core.context_compiler import (
    CONTEXT_COMPILER_VERSION,
    CONTEXT_PACKAGE_SCHEMA_VERSION,
    CONTEXT_READ_ONLY_CONTRACT_VERSION,
    ContextBudget,
    ContextCompilerInput,
    compile_context_package,
)
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.policy_boundary import evaluate_policy_boundary


def test_context_package_includes_schema_version_and_provenance() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            request={"command_id": "cmd-1", "trace_id": "trace-1", "text": "open notepad"},
            runtime_snapshot={"session_id": "s1", "fsm_state": "IDLE", "version": 3},
            generated_at_ms=12345,
        )
    )

    assert package["schema_version"] == CONTEXT_PACKAGE_SCHEMA_VERSION
    assert package["compiler_version"] == CONTEXT_COMPILER_VERSION
    assert package["context_contract_version"] == CONTEXT_READ_ONLY_CONTRACT_VERSION
    assert package["context_package_id"].startswith("context-package/")
    assert package["generated_at_ms"] == 12345
    assert package["authority"] is False
    assert package["non_executing"] is True
    assert package["capability_grant"] is False
    assert package["approval_grant"] is False
    assert package["lease_grant"] is False
    assert package["execution_permission"] == "not_granted_by_context"
    assert package["requires_backend_validation"] is True
    assert package["requires_policy_recheck"] is True
    assert package["memory_mutation"] is False
    assert package["journal_mutation"] is False
    assert package["evidence_mutation"] is False
    assert package["runtime_mutation"] is False
    assert package["raw_journal_included"] is False
    refs = {ref["source_id"]: ref for ref in package["source_references"]}
    assert refs["runtime_snapshot"]["authority"] == "backend_authoritative"
    assert refs["runtime_snapshot"]["provided"] is True
    assert package["source_refs"] == package["source_references"]
    assert package["source_versions"]["runtime_snapshot"] == 3
    assert package["runtime"]["source_ref"] == "runtime_snapshot"


def test_frontend_projection_is_reference_only_not_authority() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            frontend_projection={"runtimeState": "COMPLETED", "health": "healthy"},
            generated_at_ms=1,
        )
    )

    frontend = package["frontend_projection"]["summary"]
    refs = {ref["source_id"]: ref for ref in package["source_references"]}
    assert frontend["provided"] is True
    assert frontend["used_as_authority"] is False
    assert frontend["status"] == "reference_only"
    assert refs["frontend_projection"]["authority"] == "frontend_reference_non_authoritative"
    assert refs["frontend_projection"]["used_as_authority"] is False
    assert any("frontend projection provided for reference only" in warning for warning in package["safety_warnings"])


def test_unknown_stale_and_missing_inputs_remain_unavailable_or_stale() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            runtime_snapshot={"fsm_state": "IDLE", "stale": True},
            command_lifecycle=None,
            policy_boundary=None,
            evidence_audit=None,
            generated_at_ms=1,
        )
    )

    assert package["runtime"]["summary"]["status"] == "stale"
    assert package["command_lifecycle"]["summary"]["status"] == "unavailable"
    assert package["policy_boundary"]["summary"]["status"] == "unavailable"
    assert package["verifier_evidence"]["summary"]["status"] == "unavailable"
    assert any("runtime snapshot is stale" in warning for warning in package["safety_warnings"])
    assert any("command lifecycle unavailable" in warning for warning in package["safety_warnings"])


def test_blocked_non_executable_quarantined_state_stays_non_executable_in_context() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            non_executable_state={
                "command_status": "waiting_for_approval",
                "executed": False,
                "not_executed": True,
                "terminal_non_executed": True,
                "last_guard_decision": {
                    "policy_rule": "generic_click.quarantined.target_resolution_missing",
                },
            },
            generated_at_ms=1,
        )
    )

    summary = package["non_executable"]["summary"]
    assert summary["non_executable"] is True
    assert summary["blocked"] is True
    assert summary["quarantined"] is True
    assert summary["execution_recommendation"] == "do_not_execute"
    assert any("non-executable or blocked state present" in warning for warning in package["safety_warnings"])


def test_approval_and_clarification_lifecycle_are_not_execution_permission() -> None:
    lifecycle = {
        "records": [
            {
                "command_id": "cmd-approved-nonexec",
                "status": "blocked",
                "active": False,
                "verification_state": "unverified",
                "metadata": {
                    "approval_resolution_status": "approval_granted",
                    "resume_allowed": False,
                    "not_executed": True,
                    "completed_without_execution": True,
                    "mutation_performed": False,
                },
            },
            {
                "command_id": "cmd-clarified",
                "status": "blocked",
                "active": False,
                "verification_state": "unverified",
                "metadata": {
                    "clarification_resolution_status": "clarification_resolved",
                    "not_executed": True,
                    "completed_without_execution": True,
                    "mutation_performed": False,
                },
            },
        ],
        "pending_approvals": [],
        "pending_clarifications": [],
    }

    package = compile_context_package(ContextCompilerInput(command_lifecycle=lifecycle, generated_at_ms=1))
    summary = package["command_lifecycle"]["summary"]

    assert summary["resolution_is_execution_permission"] is False
    assert summary["recent_records"][0]["approval_resolution_status"] == "approval_granted"
    assert summary["recent_records"][0]["not_executed"] is True
    assert summary["recent_records"][1]["clarification_resolution_status"] == "clarification_resolved"
    assert summary["recent_records"][1]["completed_without_execution"] is True
    assert package["execution_permission"] == "not_granted_by_context"


def test_policy_boundary_summary_cannot_be_interpreted_as_context_permission() -> None:
    decision = classify_intent_risk("open_app", {"app": "notepad"})
    boundary = evaluate_policy_boundary(decision)

    package = compile_context_package(ContextCompilerInput(policy_boundary=boundary, generated_at_ms=1))
    summary = package["policy_boundary"]["summary"]

    assert summary["dispatch_allowed_by_policy"] is True
    assert summary["context_grants_permission"] is False
    assert summary["execution_permission"] == "not_granted_by_context"
    assert summary["requires_policy_recheck_before_dispatch"] is True
    assert "execute_allowed" not in json.dumps(package)


def test_verifier_evidence_summary_distinguishes_dispatch_from_verified_evidence() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            evidence_audit={
                "scan_version": "evidence-audit/2",
                "read_only": True,
                "status": "warning",
                "success_count": 1,
                "verified_action_count": 0,
                "missing_evidence_count": 1,
                "failed_evidence_count": 0,
                "verification_counts": {"missing": 1},
            },
            generated_at_ms=1,
        )
    )

    summary = package["verifier_evidence"]["summary"]
    assert summary["status"] == "warning"
    assert summary["success_count"] == 1
    assert summary["verified_action_count"] == 0
    assert summary["missing_evidence_count"] == 1
    assert summary["dispatch_success_is_not_verification"] is True
    assert any("evidence audit status is warning" in warning for warning in package["safety_warnings"])


def test_evidence_classification_counts_are_preserved_without_verification_claims() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            evidence_audit={
                "scan_version": "evidence-audit/2",
                "read_only": True,
                "status": "fail",
                "success_count": 2,
                "verified_action_count": 0,
                "missing_evidence_count": 16,
                "failed_evidence_count": 2,
                "current_evidence_failure_count": 0,
                "historical_evidence_debt_count": 18,
                "unknown_era_evidence_issue_count": 10,
                "current_missing_evidence_count": 0,
                "historical_missing_evidence_count": 16,
                "unknown_era_missing_evidence_count": 0,
                "verification_counts": {"missing": 16, "failed": 2},
            },
            generated_at_ms=1,
        )
    )

    summary = package["verifier_evidence"]["summary"]
    assert summary["status"] == "fail"
    assert summary["current_evidence_failure_count"] == 0
    assert summary["historical_evidence_debt_count"] == 18
    assert summary["unknown_era_evidence_issue_count"] == 10
    assert summary["current_missing_evidence_count"] == 0
    assert summary["historical_missing_evidence_count"] == 16
    assert summary["unknown_era_missing_evidence_count"] == 0
    assert summary["verified_action_count"] == 0
    assert summary["dispatch_success_is_not_verification"] is True
    assert package["known_debt_visible"] is True
    assert package["unknown_era_preserved"] is True
    assert package["execution_permission"] == "not_granted_by_context"


def test_unknown_era_counts_are_preserved_without_collapsing_to_historical() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            evidence_audit={
                "scan_version": "evidence-audit/2",
                "read_only": True,
                "status": "fail",
                "historical_evidence_debt_count": 18,
                "historical_missing_evidence_count": 16,
                "unknown_era_evidence_issue_count": 10,
                "unknown_era_missing_evidence_count": 0,
                "verified_action_count": 0,
                "missing_evidence_count": 16,
                "failed_evidence_count": 0,
            },
            generated_at_ms=1,
        )
    )

    summary = package["verifier_evidence"]["summary"]
    assert summary["historical_evidence_debt_count"] == 18
    assert summary["historical_missing_evidence_count"] == 16
    assert summary["unknown_era_evidence_issue_count"] == 10
    assert summary["unknown_era_missing_evidence_count"] == 0
    assert package["unknown_era_preserved"] is True
    assert "unknown_era_as_historical" not in json.dumps(package)


def test_maintenance_diagnostics_are_marked_read_only() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            maintenance_scan={
                "status": "warning",
                "read_only": True,
                "action_proposals": [{"id": "proposal-1", "requires_approval": True}],
                "checks": {
                    "app_discovery": {
                        "read_only": True,
                        "actions_performed": [],
                    }
                },
            },
            generated_at_ms=1,
        )
    )

    summary = package["maintenance_diagnostics"]["summary"]
    assert summary["read_only"] is True
    assert summary["diagnostics_only"] is True
    assert summary["action_proposal_count"] == 1
    assert summary["app_discovery"]["read_only"] is True
    assert summary["app_discovery"]["actions_performed"] == []
    assert summary["mutation_performed"] is False


def test_maintenance_debt_and_runtime_health_projection_are_preserved_read_only() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            maintenance_scan={
                "scan_version": "maintenance-scan/1",
                "status": "fail",
                "read_only": True,
                "summary": {
                    "scan_version": "runtime-health/1",
                    "read_only": True,
                    "status": "fail",
                    "reasons": ["evidence_audit", "replay_diagnostics", "system_resources"],
                    "finding_severity_counts": {"fail": 1, "warning": 2},
                },
                "action_proposals": [],
                "mutation_performed": False,
                "checks": {
                    "foundation_closure_readiness": {
                        "read_only": True,
                        "mutation_performed": False,
                        "status": "warning",
                        "closure_readiness_status": "needs_operator_attention",
                        "current_blocker_count": 0,
                        "current_evidence_failure_count": 0,
                        "current_missing_evidence_count": 0,
                        "pending_decision_blocker_count": 0,
                        "restored_pending_count": 0,
                        "historical_evidence_debt_count": 18,
                        "historical_missing_evidence_count": 16,
                        "unknown_era_evidence_issue_count": 10,
                        "unknown_era_missing_evidence_count": 0,
                        "replay_diagnostics_status": "fail",
                        "replay_boundary_classification": "historical_mixed_sequence_eras_or_reset_boundaries",
                        "system_resource_warning_count": 1,
                    },
                    "pending_decision_hygiene": {
                        "status": "ok",
                        "pending_count": 0,
                        "restored_unresolved_count": 0,
                    },
                    "replay_diagnostics": {
                        "status": "fail",
                        "cleanup_execution_blocked": True,
                        "replay_boundary": {
                            "classification": "historical_mixed_sequence_eras_or_reset_boundaries",
                        },
                    },
                    "system_resources": {
                        "status": "warning",
                        "disk": {"percent": 92.3},
                    },
                    "app_discovery": {
                        "read_only": True,
                        "actions_performed": [],
                    },
                },
            },
            generated_at_ms=1,
        )
    )

    summary = package["maintenance_diagnostics"]["summary"]
    closure = summary["foundation_closure_readiness"]
    assert summary["runtime_health_status"] == "fail"
    assert summary["runtime_health_reasons"] == ["evidence_audit", "replay_diagnostics", "system_resources"]
    assert closure["read_only"] is True
    assert closure["mutation_performed"] is False
    assert closure["closure_readiness_status"] == "needs_operator_attention"
    assert closure["current_blocker_count"] == 0
    assert closure["current_evidence_failure_count"] == 0
    assert closure["historical_evidence_debt_count"] == 18
    assert closure["historical_missing_evidence_count"] == 16
    assert closure["unknown_era_evidence_issue_count"] == 10
    assert closure["unknown_era_missing_evidence_count"] == 0
    assert closure["replay_diagnostics_status"] == "fail"
    assert closure["replay_cleanup_execution_blocked"] is True
    assert closure["system_resource_warning_count"] == 1
    assert summary["replay_diagnostics"]["boundary_classification"] == (
        "historical_mixed_sequence_eras_or_reset_boundaries"
    )
    assert summary["system_resources"]["disk_percent"] == 92.3
    assert package["known_debt_visible"] is True
    assert package["unknown_era_preserved"] is True
    assert package["runtime_mutation"] is False


def test_raw_runtime_journal_is_excluded_by_default_and_budget_records_omissions() -> None:
    raw_events = [
        {
            "type": "ACTION_COMPLETED",
            "payload": {
                "success": True,
                "execution_evidence": {"verification_state": "verified"},
            },
        }
    ]
    lifecycle = {
        "records": [
            {"command_id": f"cmd-{index}", "status": "completed", "metadata": {}}
            for index in range(4)
        ],
        "pending_approvals": [],
        "pending_clarifications": [],
    }

    package = compile_context_package(
        ContextCompilerInput(
            command_lifecycle=lifecycle,
            runtime_events=raw_events,
            budget=ContextBudget(max_items_per_section=2),
            generated_at_ms=1,
        )
    )
    encoded = json.dumps(package)

    assert "ACTION_COMPLETED" not in encoded
    assert "execution_evidence" not in encoded
    assert package["budget"]["raw_runtime_journal_included"] is False
    assert package["budget"]["omitted_item_counts"]["runtime_events"] == 1
    assert package["budget"]["omitted_item_counts"]["command_lifecycle.records"] == 2
    assert any(section["section"] == "runtime_events" for section in package["omitted_sections"])
    assert any(section["section"] == "command_lifecycle.records" for section in package["omitted_sections"])


def test_requested_raw_runtime_events_remain_omitted_without_boundary_approval() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            runtime_events=[
                {
                    "type": "ACTION_COMPLETED",
                    "payload": {"execution_evidence": {"verification_state": "verified"}},
                }
            ],
            budget=ContextBudget(include_raw_runtime_events=True),
            generated_at_ms=1,
        )
    )

    encoded = json.dumps(package)
    assert package["raw_journal_included"] is False
    assert package["budget"]["raw_runtime_journal_included"] is False
    assert package["budget"]["requested_raw_runtime_events"] is True
    assert package["budget"]["omitted_item_counts"]["runtime_events"] == 1
    assert "ACTION_COMPLETED" not in encoded
    assert "execution_evidence" not in encoded


def test_context_compiler_introduces_no_execution_capability() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            request={"text": "click something"},
            policy_boundary={"dispatch_allowed": True, "decision_status": "ready"},
            frontend_projection={"execute_allowed": True},
            generated_at_ms=1,
        )
    )

    assert package["non_executing"] is True
    assert package["capability_grant"] is False
    assert package["approval_grant"] is False
    assert package["lease_grant"] is False
    assert package["execution_permission"] == "not_granted_by_context"
    assert package["raw_journal_included"] is False
    assert package["policy_boundary"]["summary"]["context_grants_permission"] is False
    assert package["frontend_projection"]["summary"]["used_as_authority"] is False
    assert "execute_allowed" not in json.dumps(package["policy_boundary"])
    assert "execute_allowed" not in json.dumps(package["request"])


def test_policy_approval_grant_is_reported_but_not_context_permission() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            policy_boundary={
                "boundary_version": "policy-boundary/1",
                "dispatch_allowed": True,
                "decision_status": "approval_required",
                "policy_rule": "medium_risk.requires_approval",
                "approval_granted": True,
                "resume_allowed": True,
            },
            generated_at_ms=1,
        )
    )

    summary = package["policy_boundary"]["summary"]
    assert summary["approval_granted"] is True
    assert summary["resume_allowed_by_policy"] is True
    assert summary["context_grants_permission"] is False
    assert summary["execution_permission"] == "not_granted_by_context"
    assert summary["requires_policy_recheck_before_dispatch"] is True
    assert package["non_executing"] is True
    assert package["capability_grant"] is False
    assert package["execution_permission"] == "not_granted_by_context"


def test_untrusted_permission_fields_are_not_promoted_from_sources() -> None:
    package = compile_context_package(
        ContextCompilerInput(
            request={
                "text": "open notepad",
                "capability_grant": True,
                "approval_grant": True,
                "execution_permission": "granted",
            },
            maintenance_scan={
                "status": "ok",
                "read_only": True,
                "capability_grant": True,
                "approval_grant": True,
                "lease_grant": True,
                "execution_permission": "granted",
                "authority": True,
                "memory_mutation": True,
                "journal_mutation": True,
                "evidence_mutation": True,
                "runtime_mutation": True,
                "raw_journal_included": True,
                "checks": {"app_discovery": {"read_only": True, "actions_performed": []}},
            },
            frontend_projection={
                "capability_grant": True,
                "approval_grant": True,
                "lease_grant": True,
                "execution_permission": "granted",
                "authority": True,
            },
            generated_at_ms=1,
        )
    )

    assert package["authority"] is False
    assert package["non_executing"] is True
    assert package["capability_grant"] is False
    assert package["approval_grant"] is False
    assert package["lease_grant"] is False
    assert package["execution_permission"] == "not_granted_by_context"
    assert package["memory_mutation"] is False
    assert package["journal_mutation"] is False
    assert package["evidence_mutation"] is False
    assert package["runtime_mutation"] is False
    assert package["raw_journal_included"] is False
    assert "granted" not in json.dumps(package["request"])
    assert "granted" not in json.dumps(package["maintenance_diagnostics"])
    assert package["frontend_projection"]["summary"]["used_as_authority"] is False


def test_context_compiler_does_not_mutate_supplied_inputs() -> None:
    request = {"text": "summarize runtime", "metadata": {"operator": "local"}}
    lifecycle = {
        "records": [{"command_id": "cmd-1", "status": "executed", "metadata": {}}],
        "pending_approvals": [],
        "pending_clarifications": [],
    }
    evidence = {
        "status": "warning",
        "read_only": True,
        "success_count": 0,
        "verified_action_count": 0,
        "missing_evidence_count": 1,
        "failed_evidence_count": 0,
        "verification_counts": {"missing": 1},
    }
    maintenance = {
        "status": "warning",
        "read_only": True,
        "action_proposals": [],
        "checks": {"app_discovery": {"read_only": True, "actions_performed": []}},
    }
    before = deepcopy({
        "request": request,
        "lifecycle": lifecycle,
        "evidence": evidence,
        "maintenance": maintenance,
    })

    package = compile_context_package(
        ContextCompilerInput(
            request=request,
            command_lifecycle=lifecycle,
            evidence_audit=evidence,
            maintenance_scan=maintenance,
            generated_at_ms=1,
        )
    )

    assert {
        "request": request,
        "lifecycle": lifecycle,
        "evidence": evidence,
        "maintenance": maintenance,
    } == before
    assert package["non_executing"] is True
