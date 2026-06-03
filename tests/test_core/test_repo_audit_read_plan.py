from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_read_plan import (
    REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION,
    REPO_AUDIT_READ_PLAN_VERSION,
    build_repo_audit_future_read_plan,
)
from aegis.core.repo_audit_source_inventory import (
    REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION,
    validate_repo_audit_source_inventory_design,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-read-plan:aegis:1",
        "project_ref": "project:aegis",
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "tenant_scope": "local",
        "namespace": "repo_audit",
        "source_inventory_decision_ref": "repo-audit-source-inventory:aegis:1",
        "source_inventory_scope": ["future_read_plan_candidate"],
        "candidate_paths": [
            {"path": "README.md", "path_type": "documentation", "metadata_only": True},
            {"path": "src/aegis/core/repo_audit_pack.py", "path_type": "source"},
            {"path": "tests/test_core/test_repo_audit_pack.py", "path_type": "test"},
            {"path": "docs/repo-audit-pack-read-only-contract-v1.md", "path_type": "docs"},
        ],
        "source_refs": [{"ref_id": "commit:f2dfae4", "ref_type": "commit"}],
        "policy_refs": ["policy:repo-audit.read-plan.future-only"],
        "source_policy_refs": ["source-policy:repo-audit.exclusions"],
        "budget_policy": {
            "max_file_count": 100,
            "max_file_size_bytes": 200_000,
            "max_total_bytes": 5_000_000,
            "budget_policy": "human_review_required_above_limits",
        },
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "secret_exclusion_policy": "deny_by_default",
        "generated_artifact_policy": "deny_by_default",
        "hidden_file_policy": "deny_by_default",
        "symlink_policy": "blocked",
        "evidence_expectation": [
            "file_read_attempt_evidence_expected",
            "path_normalization_evidence_expected",
            "exclusion_policy_evidence_expected",
            "file_hash_evidence_expected_future",
            "no_content_logged_without_policy",
        ],
        "verifier_expectation": [
            "path_within_repo_root_verifier",
            "forbidden_path_exclusion_verifier",
            "budget_enforcement_verifier",
            "secret_exclusion_verifier",
            "content_read_boundary_verifier",
        ],
        "limitations": ["read plan only; no file existence proof"],
        "unknowns": ["candidate paths are caller supplied"],
        "future_runner_requirements": [
            "backend_owned_read_only_runner",
            "evidence_boundary_required",
            "verifier_boundary_required",
        ],
        "authority": False,
        "execution_permission": REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _source_inventory_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "inventory_id": "repo-audit-source-inventory:aegis:1",
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "commit_ref": "f2dfae4",
        "branch_ref": "main",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
        "source_refs": [{"ref_id": "commit:f2dfae4", "ref_type": "commit"}],
        "source_inventory_scope": [
            "source_inventory_design",
            "path_policy_validation",
            "exclusion_policy_validation",
            "source_budget_validation",
            "metadata_only_inventory_candidate",
            "future_read_plan_candidate",
        ],
        "candidate_paths": [
            {"path": "README.md", "path_type": "documentation"},
            {"path": "src/aegis/core/repo_audit_pack.py", "path_type": "source"},
            {"path": "tests/test_core/test_repo_audit_pack.py", "path_type": "test"},
            {"path": "docs/repo-audit-pack-read-only-contract-v1.md", "path_type": "docs"},
        ],
        "path_policy": {
            "allowed_prefixes": ["src/", "tests/", "docs/"],
            "allow_repo_root_files": True,
            "forbidden_paths": [".git/", ".venv/", "logs/", "node_modules/", "dist/", "build/"],
            "forbidden_extensions": [".env", ".key", ".pem", ".p12", ".pfx"],
            "generated_artifact_policy": "deny_by_default",
            "secret_privacy_policy": "deny_by_default",
            "hidden_path_policy": "deny_by_default",
            "symlink_policy": "blocked",
            "external_path_policy": "blocked",
            "path_traversal_policy": "blocked",
            "runtime_log_policy": "blocked",
            "model_vector_policy": "blocked",
            "browser_output_policy": "blocked",
            "dependency_build_policy": "blocked",
        },
        "budget": {
            "max_file_count": 100,
            "max_file_size_bytes": 200_000,
            "max_total_bytes": 5_000_000,
            "budget_policy": "human_review_required_above_limits",
        },
        "output_categories": ["allowed_path_candidate", "future_read_plan_candidate"],
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "limitations": ["metadata-only source inventory design"],
        "unknowns": ["no live file access"],
        "authority": False,
        "execution_permission": REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _source_inventory_decision(**overrides: object):
    return validate_repo_audit_source_inventory_design(_source_inventory_request(**overrides))


def _unsafe_related_decision(**overrides: object) -> SimpleNamespace:
    decision = SimpleNamespace(
        validation_status="review_ready",
        failure_reasons=(),
        authority=False,
        runtime_dispatch_allowed=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        frontend_authority=False,
        evidence_provided_by_pack_output=False,
        evidence_provided_by_readiness=False,
        evidence_provided_by_inventory=False,
        evidence_provided_by_report=False,
        evidence_provided_by_preview=False,
        evidence_provided_by_simulation=False,
        evidence_provided_by_passport=False,
        evidence_provided_by_package=False,
        evidence_provided_by_review=False,
        evidence_provided_by_read_plan=False,
        verifier_success=False,
        verified_success=False,
        success=False,
    )
    for key, value in overrides.items():
        setattr(decision, key, value)
    return decision


def _build(request: dict[str, object], **related_decisions: object):
    return build_repo_audit_future_read_plan(request, **related_decisions)


def test_valid_minimal_future_read_plan_is_non_authoritative() -> None:
    decision = _build(_request(), source_inventory_decision=_source_inventory_decision())

    assert decision.contract_version == REPO_AUDIT_READ_PLAN_VERSION
    assert decision.plan_status == "plan_ready"
    assert decision.failure_reasons == ()
    assert decision.execution_permission == REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_read_plan is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.read_plan_contract.read_plan_only is True
    assert decision.read_plan_contract.repo_scan_performed is False
    assert decision.read_plan_contract.file_read_performed is False
    assert decision.read_plan_contract.filesystem_traversal_performed is False
    assert decision.read_plan_contract.stat_performed is False
    assert decision.read_plan_contract.git_command_performed is False
    assert decision.read_plan_contract.subprocess_performed is False
    assert decision.read_plan_contract.test_execution_performed is False
    assert decision.read_plan_contract.model_call_performed is False
    assert decision.read_plan_contract.tool_call_performed is False
    assert decision.read_plan_contract.api_call_performed is False
    assert decision.read_plan_contract.mcp_call_performed is False
    assert decision.read_plan_contract.memory_access_performed is False
    assert decision.read_plan_contract.report_generated is False
    assert decision.read_plan_contract.export_performed is False
    assert decision.read_plan_contract.certification_claim is False


def test_valid_readme_src_tests_and_docs_candidates_are_planned_without_existence_claim() -> None:
    decision = _build(_request())

    categories = {target.normalized_relative_path: target.category for target in decision.planned_targets}

    assert decision.plan_status == "plan_ready"
    assert categories["README.md"] == "planned_metadata_only_candidate"
    assert categories["src/aegis/core/repo_audit_pack.py"] == "future_read_candidate"
    assert categories["tests/test_core/test_repo_audit_pack.py"] == "future_read_candidate"
    assert categories["docs/repo-audit-pack-read-only-contract-v1.md"] == "future_read_candidate"
    for target in decision.planned_targets:
        assert target.source_existence_proven is False
        assert target.file_content_observed is False
        assert target.file_read_performed is False
        assert target.evidence_provided_by_read_plan is False
        assert target.verifier_success is False
        assert target.expected_evidence
        assert target.expected_verifier


def test_source_inventory_decision_can_supply_metadata_candidates_without_reads() -> None:
    request = _request(candidate_paths=[])

    decision = _build(request, source_inventory_decision=_source_inventory_decision())

    assert decision.plan_status == "plan_ready"
    assert {target.category for target in decision.planned_targets} == {
        "planned_metadata_only_candidate"
    }
    assert decision.read_plan_contract.file_read_performed is False


def test_missing_project_repo_identity_is_blocked() -> None:
    decision = _build(_request(request_id="", project_ref="", repo_id="", repo_name="", repo_root_ref=""))

    assert decision.plan_status == "blocked_by_missing_scope"
    assert "request_identity_required" in decision.failure_reasons
    assert "project_repo_identity_required" in decision.failure_reasons


def test_missing_tenant_or_namespace_is_blocked() -> None:
    decision = _build(_request(tenant_scope="", namespace=""))

    assert decision.plan_status == "blocked_by_missing_scope"
    assert "tenant_scope_required" in decision.failure_reasons
    assert "namespace_required" in decision.failure_reasons


def test_missing_source_inventory_or_candidate_metadata_requires_clarification() -> None:
    decision = _build(_request(candidate_paths=[]))

    assert decision.plan_status == "clarification_required"
    assert "source_inventory_or_candidate_metadata_required" in decision.failure_reasons
    assert decision.planned_targets == ()


def test_missing_budget_policy_is_blocked() -> None:
    decision = _build(_request(budget_policy={}))

    assert decision.plan_status == "blocked_by_missing_budget"
    assert "missing_budget_policy" in decision.failure_reasons
    assert "missing_budget_file_count" in decision.failure_reasons
    assert "missing_budget_file_size" in decision.failure_reasons
    assert "missing_budget_total_bytes" in decision.failure_reasons


def test_missing_privacy_or_data_sensitivity_blocks_plan() -> None:
    decision = _build(_request(privacy_class="", data_sensitivity=""))

    assert decision.plan_status == "blocked_by_privacy_policy"
    assert "privacy_class_required" in decision.failure_reasons
    assert "data_sensitivity_required" in decision.failure_reasons


def test_missing_evidence_expectation_blocks_future_read_plan() -> None:
    decision = _build(_request(evidence_expectation=[]))

    assert decision.plan_status == "blocked_by_missing_evidence_expectation"
    assert "missing_evidence_expectation" in decision.failure_reasons
    assert decision.evidence_provided_by_read_plan is False


def test_missing_verifier_expectation_blocks_future_read_plan() -> None:
    decision = _build(_request(verifier_expectation=[]))

    assert decision.plan_status == "blocked_by_missing_verifier_expectation"
    assert "missing_verifier_expectation" in decision.failure_reasons
    assert decision.verifier_success is False


@pytest.mark.parametrize(
    ("path", "reason", "category"),
    [
        ("C:/Users/nemes/Desktop/Aegis/README.md", "absolute_path_denied", "denied_external_path"),
        ("C:", "drive_root_path_denied", "denied_external_path"),
        ("C:/", "drive_root_path_denied", "denied_external_path"),
        ("//server/share/README.md", "unc_path_denied", "denied_external_path"),
        ("/workspace/Aegis/README.md", "absolute_path_denied", "denied_external_path"),
        ("file:///C:/Users/nemes/Desktop/Aegis/README.md", "external_path_denied", "denied_external_path"),
        ("https://example.test/README.md", "external_path_denied", "denied_external_path"),
        ("~/Aegis/README.md", "home_relative_path_denied", "denied_external_path"),
        ("src/aegis/../secret.py", "path_traversal_denied", "denied_traversal_path"),
        ("src/aegis/core/\x00bad.py", "path_control_character_denied", "denied_unknown"),
    ],
)
def test_external_absolute_home_traversal_and_control_paths_are_denied(
    path: str,
    reason: str,
    category: str,
) -> None:
    decision = _build(_request(candidate_paths=[{"path": path}]))

    assert decision.plan_status == "blocked_by_path_policy"
    assert reason in decision.failure_reasons
    assert decision.denied_targets[0].category == category
    assert decision.denied_targets[0].denial_reason == reason
    assert decision.planned_targets == ()


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "src/aegis/.env.local",
        "config/private.key",
        "config/certificate.pem",
        "secrets/service-token.txt",
        "credentials/api_password.txt",
    ],
)
def test_secret_like_paths_are_denied(path: str) -> None:
    decision = _build(_request(candidate_paths=[{"path": path}]))

    assert decision.plan_status == "blocked_by_secret_policy"
    assert "secret_path_denied" in decision.failure_reasons
    assert decision.denied_targets[0].category == "denied_secret_path"


@pytest.mark.parametrize(
    ("path", "reason", "category"),
    [
        ("logs/backend.log", "log_path_denied", "denied_log_path"),
        ("runtime_events.jsonl", "runtime_journal_path_denied", "denied_runtime_journal"),
        ("evidence/smoke.json", "runtime_journal_path_denied", "denied_runtime_journal"),
        ("replay/session.jsonl", "runtime_journal_path_denied", "denied_runtime_journal"),
        ("journal/runtime.jsonl", "runtime_journal_path_denied", "denied_runtime_journal"),
        ("archive/runtime.jsonl", "runtime_journal_path_denied", "denied_runtime_journal"),
    ],
)
def test_runtime_journal_evidence_replay_archive_and_log_paths_are_denied(
    path: str,
    reason: str,
    category: str,
) -> None:
    decision = _build(_request(candidate_paths=[{"path": path}]))

    assert decision.plan_status == "blocked_by_runtime_journal_policy"
    assert reason in decision.failure_reasons
    assert decision.denied_targets[0].category == category


@pytest.mark.parametrize(
    ("path", "reason", "category"),
    [
        (".git/config", "dependency_path_denied", "denied_dependency_path"),
        (".venv/pyvenv.cfg", "dependency_path_denied", "denied_dependency_path"),
        ("node_modules/pkg/index.js", "dependency_path_denied", "denied_dependency_path"),
        (".next/server/app.js", "build_cache_path_denied", "denied_build_cache"),
        ("dist/app.js", "build_cache_path_denied", "denied_build_cache"),
        ("build/app.js", "build_cache_path_denied", "denied_build_cache"),
        ("cache/file.bin", "build_cache_path_denied", "denied_build_cache"),
        ("models/local.gguf", "model_artifact_path_denied", "denied_model_artifact"),
        ("datasets/source.jsonl", "model_artifact_path_denied", "denied_model_artifact"),
        ("vector_db/index.bin", "vector_db_path_denied", "denied_vector_db"),
        ("screenshots/home.png", "browser_output_or_screenshot_path_denied", "denied_generated_artifact"),
        ("browser-output/run.html", "browser_output_or_screenshot_path_denied", "denied_generated_artifact"),
    ],
)
def test_dependency_build_model_vector_browser_and_generated_paths_are_denied(
    path: str,
    reason: str,
    category: str,
) -> None:
    decision = _build(_request(candidate_paths=[{"path": path}]))

    assert reason in decision.failure_reasons
    assert decision.denied_targets[0].category == category
    assert decision.planned_targets == ()


def test_generated_candidate_flag_is_denied() -> None:
    decision = _build(_request(candidate_paths=[{"path": "src/generated/client.py", "is_generated": True}]))

    assert decision.plan_status == "blocked_by_generated_artifact_policy"
    assert "generated_artifact_path_denied" in decision.failure_reasons
    assert decision.denied_targets[0].category == "denied_generated_artifact"


def test_hidden_paths_are_future_gated_only_when_policy_allows() -> None:
    denied = _build(_request(candidate_paths=[{"path": "src/aegis/.internal/design.md"}]))
    gated = _build(
        _request(
            candidate_paths=[
                {
                    "path": "src/aegis/.internal/design.md",
                    "future_gate_ref": "approval:future-hidden-path-review",
                }
            ],
            hidden_file_policy="explicit_future_gate_required",
        )
    )

    assert denied.plan_status == "blocked_by_hidden_path_policy"
    assert "hidden_path_denied" in denied.failure_reasons
    assert denied.denied_targets[0].category == "denied_hidden_path"
    assert gated.plan_status == "plan_ready_requires_human_review"
    assert gated.future_gated_targets[0].category == "future_gated_hidden_path"
    assert gated.future_gated_targets[0].future_gate_reason == "hidden_path_requires_future_gate"
    assert gated.future_gated_targets[0].human_review_required is True


def test_symlink_paths_are_future_gated_only_when_policy_allows() -> None:
    denied = _build(_request(candidate_paths=[{"path": "docs/link.md", "is_symlink": True}]))
    gated = _build(
        _request(
            candidate_paths=[
                {
                    "path": "docs/link.md",
                    "is_symlink": True,
                    "future_gate_ref": "approval:future-symlink-review",
                }
            ],
            symlink_policy="explicit_future_gate_required",
        )
    )

    assert denied.plan_status == "blocked_by_symlink_policy"
    assert "symlink_path_denied" in denied.failure_reasons
    assert denied.denied_targets[0].category == "denied_symlink"
    assert gated.plan_status == "plan_ready_requires_human_review"
    assert gated.future_gated_targets[0].category == "future_gated_symlink"
    assert gated.future_gated_targets[0].future_gate_reason == "symlink_requires_future_gate"


def test_large_file_budget_excess_requires_review_or_blocks() -> None:
    review = _build(
        _request(
            candidate_paths=[{"path": "src/aegis/core/large.py", "size_bytes": 300_000}],
            budget_policy={
                "max_file_count": 100,
                "max_file_size_bytes": 200_000,
                "max_total_bytes": 5_000_000,
                "budget_policy": "human_review_required_above_limits",
            },
        )
    )
    blocked = _build(
        _request(
            budget_policy={
                "max_file_count": 25_000,
                "max_file_size_bytes": 25_000_000,
                "max_total_bytes": 1_000_000_000,
                "budget_policy": "block_above_limits",
            }
        )
    )

    assert review.plan_status == "plan_ready_requires_human_review"
    assert review.future_gated_targets[0].category == "future_gated_large_file"
    assert review.future_gated_targets[0].future_gate_reason == "large_file_requires_future_gate"
    assert review.budget.actual_bytes_counted is False
    assert blocked.plan_status == "blocked_by_budget_excess"
    assert blocked.planned_targets == ()


def test_denied_and_future_gated_targets_preserve_reasons_and_policy_refs() -> None:
    denied = _build(
        _request(
            candidate_paths=[
                {
                    "path": "credentials/api_token.txt",
                    "source_policy_refs": ["policy:secret-deny"],
                }
            ]
        )
    )
    gated = _build(
        _request(
            candidate_paths=[
                {
                    "path": "docs/link.md",
                    "is_symlink": True,
                    "future_gate_ref": "approval:symlink",
                    "source_policy_refs": ["policy:symlink-gate"],
                }
            ],
            symlink_policy="explicit_future_gate_required",
        )
    )

    assert denied.denied_targets[0].denial_reason == "secret_path_denied"
    assert "policy:secret-deny" in denied.denied_targets[0].source_policy_refs
    assert gated.future_gated_targets[0].future_gate_reason == "symlink_requires_future_gate"
    assert "policy:symlink-gate" in gated.future_gated_targets[0].source_policy_refs


def test_unsafe_source_inventory_decision_is_rejected() -> None:
    base = _source_inventory_decision()
    unsafe = replace(
        base,
        runtime_dispatch_allowed=True,
        source_inventory_contract=replace(base.source_inventory_contract, verifier_success=True),
    )

    decision = _build(_request(candidate_paths=[]), source_inventory_decision=unsafe)

    assert decision.plan_status == "blocked_by_source_inventory"
    assert "source_inventory_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "source_inventory_unsafe_behavior_claim_denied" in decision.failure_reasons


def test_source_inventory_allowed_forbidden_path_blocks_plan() -> None:
    safe_contract = SimpleNamespace(
        repo_scan_performed=False,
        file_read_performed=False,
        filesystem_traversal_performed=False,
        file_stat_performed=False,
        git_command_performed=False,
        test_execution_performed=False,
        subprocess_performed=False,
        model_call_performed=False,
        tool_call_performed=False,
        api_call_performed=False,
        mcp_call_performed=False,
        memory_access_performed=False,
        report_generated=False,
        export_performed=False,
        evidence_provided_by_inventory=False,
        verifier_success=False,
    )
    unsafe_inventory = SimpleNamespace(
        validation_status="design_ready",
        inventory_id="repo-audit-source-inventory:aegis:bad",
        failure_reasons=(),
        authority=False,
        runtime_dispatch_allowed=False,
        approval_grant=False,
        capability_grant=False,
        lease_grant=False,
        source_inventory_contract=safe_contract,
        allowed_path_candidates=(
            SimpleNamespace(path=".env", normalized_path=".env", path_type="secret", metadata_only=True),
        ),
    )

    decision = _build(_request(candidate_paths=[]), source_inventory_decision=unsafe_inventory)

    assert decision.plan_status == "blocked_by_source_inventory"
    assert "source_inventory_allowed_forbidden_path_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("argument_name", "expected_prefix"),
    [
        ("implementation_readiness_decision", "implementation_readiness"),
        ("repo_audit_decision", "repo_audit"),
        ("mission_control_decision", "mission_control"),
        ("tool_simulation_decision", "tool_simulation"),
        ("developer_work_passport_decision", "developer_work_passport"),
        ("compliance_evidence_decision", "compliance_evidence"),
        ("plugin_review_decision", "plugin_review"),
    ],
)
def test_unsafe_related_decisions_are_rejected(argument_name: str, expected_prefix: str) -> None:
    unsafe = _unsafe_related_decision(
        runtime_dispatch_allowed=True,
        evidence_provided_by_pack_output=True,
        verifier_success=True,
        success=True,
    )

    decision = _build(_request(), **{argument_name: unsafe})

    assert decision.plan_status == "blocked_by_unsafe_related_decision"
    assert f"{expected_prefix}_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert f"{expected_prefix}_evidence_claim_denied" in decision.failure_reasons
    assert f"{expected_prefix}_verifier_success_claim_denied" in decision.failure_reasons
    assert f"{expected_prefix}_success_claim_denied" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_authority", "frontend_authority_not_allowed"),
    ],
)
def test_authority_runtime_dispatch_and_grant_fields_are_rejected(field: str, reason: str) -> None:
    decision = _build(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("evidence_provided_by_read_plan", "read_plan_cannot_provide_evidence"),
        ("evidence_provided_by_inventory", "read_plan_cannot_provide_evidence"),
        ("verifier_success", "read_plan_cannot_mark_verifier_success"),
        ("verified_success", "read_plan_cannot_mark_verifier_success"),
        ("proof_repo_state", "proof_repo_state_claim_denied"),
        ("proof_file_exists", "proof_file_exists_claim_denied"),
        ("certification_claim", "certification_claim_denied"),
    ],
)
def test_evidence_verifier_proof_and_certification_claims_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = _build(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.evidence_provided_by_read_plan is False
    assert decision.verifier_success is False
    assert decision.certification_claim is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("repo_scan_performed", "repo_scan_request_denied"),
        ("file_read_performed", "file_read_request_denied"),
        ("filesystem_traversal_performed", "filesystem_traversal_request_denied"),
        ("stat_performed", "stat_request_denied"),
        ("file_stat_performed", "stat_request_denied"),
        ("git_command_performed", "git_command_request_denied"),
        ("test_execution_performed", "test_execution_request_denied"),
        ("subprocess_performed", "subprocess_request_denied"),
        ("model_call_performed", "model_call_request_denied"),
        ("tool_call_performed", "tool_call_request_denied"),
        ("api_call_performed", "api_call_request_denied"),
        ("mcp_call_performed", "mcp_call_request_denied"),
        ("memory_access_performed", "memory_access_request_denied"),
        ("report_generated", "report_generation_request_denied"),
        ("export_performed", "export_request_denied"),
        ("signing_requested", "report_signing_request_denied"),
    ],
)
def test_execution_tool_model_api_mcp_memory_report_and_export_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = _build(_request(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.repo_scan_performed is False
    assert decision.file_read_performed is False
    assert decision.filesystem_traversal_performed is False
    assert decision.stat_performed is False
    assert decision.git_command_performed is False
    assert decision.test_execution_performed is False
    assert decision.subprocess_performed is False
    assert decision.model_call_performed is False
    assert decision.tool_call_performed is False
    assert decision.api_call_performed is False
    assert decision.mcp_call_performed is False
    assert decision.memory_access_performed is False
    assert decision.report_generated is False
    assert decision.export_performed is False


def test_requested_tools_models_apis_mcp_and_claims_are_rejected() -> None:
    decision = _build(
        _request(
            requested_tools=["read_file"],
            requested_models=["local-llm"],
            requested_mcp_tools=["filesystem.read"],
            api_call_requested=True,
            claims=["proof file exists", "tests passed", "code is safe"],
        )
    )

    assert "tool_call_request_denied" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons
    assert "mcp_call_request_denied" in decision.failure_reasons
    assert "api_call_request_denied" in decision.failure_reasons
    assert "proof_file_exists_claim_denied" in decision.failure_reasons
    assert "test_success_claim_denied" in decision.failure_reasons
    assert "code_safety_claim_denied" in decision.failure_reasons


def test_output_never_sets_execution_or_observation_invariants_true() -> None:
    decision = _build(_request())

    assert decision.repo_scan_performed is False
    assert decision.file_read_performed is False
    assert decision.filesystem_traversal_performed is False
    assert decision.stat_performed is False
    assert decision.git_command_performed is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.lease_grant is False
    assert decision.capability_grant is False
    assert decision.source_existence_proven is False
    assert decision.file_content_observed is False
    for target in decision.planned_targets:
        assert target.source_existence_proven is False
        assert target.file_content_observed is False


def test_validation_does_not_mutate_input_or_supplied_decisions() -> None:
    request = _request()
    before = deepcopy(request)
    source_inventory = _source_inventory_decision()
    related = _unsafe_related_decision()

    decision = _build(
        request,
        source_inventory_decision=source_inventory,
        implementation_readiness_decision=related,
    )

    assert request == before
    assert source_inventory.runtime_dispatch_allowed is False
    assert related.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
    with pytest.raises(FrozenInstanceError):
        decision.runtime_dispatch_allowed = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decision.read_plan_contract.file_read_performed = True  # type: ignore[misc]
