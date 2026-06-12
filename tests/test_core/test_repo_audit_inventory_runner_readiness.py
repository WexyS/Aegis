from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_inventory_runner_readiness import (
    REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION,
    REPO_AUDIT_INVENTORY_RUNNER_READINESS_VERSION,
    validate_repo_audit_inventory_runner_readiness,
)
from aegis.core.repo_audit_read_plan import (
    REPO_AUDIT_READ_PLAN_EXECUTION_PERMISSION,
    build_repo_audit_future_read_plan,
)


def _read_plan_request(**overrides: object) -> dict[str, object]:
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
            {"path": "docs/repo-audit-pack-read-only-contract.md", "path_type": "docs"},
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


def _read_plan(**overrides: object):
    return build_repo_audit_future_read_plan(_read_plan_request(**overrides))


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "repo-audit-runner-readiness:aegis:1",
        "project_ref": "project:aegis",
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "tenant_scope": "local",
        "namespace": "repo_audit",
        "read_plan_ref": "repo-audit-read-plan:aegis:1",
        "runner_scope": [
            "metadata_only_runner_readiness",
            "path_normalization_runner_readiness",
            "exclusion_enforcement_runner_readiness",
            "budget_enforcement_runner_readiness",
            "read_attempt_evidence_readiness",
            "read_result_envelope_readiness",
            "redaction_boundary_readiness",
            "verifier_postcondition_readiness",
        ],
        "file_access_mode": "future_read_only",
        "path_normalization_policy": "relative_path_only",
        "secret_exclusion_policy": "deny_by_default",
        "generated_artifact_policy": "deny_by_default",
        "runtime_journal_policy": "blocked",
        "log_policy": "blocked",
        "dependency_policy": "blocked",
        "build_artifact_policy": "blocked",
        "model_artifact_policy": "blocked",
        "vector_db_policy": "blocked",
        "hidden_path_policy": "explicit_future_gate_required",
        "symlink_policy": "explicit_future_gate_required",
        "content_logging_policy": "no_raw_content_logging",
        "redaction_policy": "redaction_required",
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "budget_policy": {
            "max_file_count": 100,
            "max_file_size_bytes": 200_000,
            "max_total_bytes": 5_000_000,
            "budget_policy": "human_review_required_above_limits",
        },
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
        "source_refs": [{"ref_id": "commit:f2dfae4", "ref_type": "commit"}],
        "policy_refs": ["policy:repo-audit.runner-readiness.future-only"],
        "limitations": ["runner readiness only; no read performed"],
        "unknowns": ["read-plan targets are caller supplied"],
        "future_runner_requirements": [
            "backend_owned_read_only_runner",
            "negative_evidence_on_failure",
            "postcondition_verifier_required",
            "no_raw_content_logging_without_policy",
        ],
        "authority": False,
        "execution_permission": REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


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
        read_result_created=False,
        read_attempt_evidence_created=False,
        verifier_success=False,
        verified_success=False,
        success=False,
    )
    for key, value in overrides.items():
        setattr(decision, key, value)
    return decision


def _validate(request: dict[str, object], **related_decisions: object):
    return validate_repo_audit_inventory_runner_readiness(request, **related_decisions)


def _tampered_read_plan(**overrides: object) -> SimpleNamespace:
    base = _read_plan()
    data = dict(base.__dict__)
    data.update(overrides)
    return SimpleNamespace(**data)


def _target(category: str, path: str, **overrides: object) -> dict[str, object]:
    target: dict[str, object] = {
        "original_path": path,
        "normalized_relative_path": path,
        "category": category,
        "decision_reason": f"{category}_test",
        "expected_evidence": ["file_read_attempt_evidence_expected"],
        "expected_verifier": ["path_within_repo_root_verifier"],
        "human_review_required": True,
    }
    target.update(overrides)
    return target


def test_valid_minimal_runner_readiness_is_non_authoritative() -> None:
    decision = _validate(_request(), read_plan_decision=_read_plan())

    assert decision.contract_version == REPO_AUDIT_INVENTORY_RUNNER_READINESS_VERSION
    assert decision.readiness_status == "readiness_ready"
    assert decision.failure_reasons == ()
    assert decision.execution_permission == REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.evidence_provided_by_readiness is False
    assert decision.verifier_success is False
    assert decision.mutation_performed is False
    assert decision.frontend_authority is False
    assert decision.readiness_contract.read_only_runner_readiness_only is True
    assert decision.readiness_contract.runner_executed is False
    assert decision.readiness_contract.repo_scan_performed is False
    assert decision.readiness_contract.file_read_performed is False
    assert decision.readiness_contract.filesystem_traversal_performed is False
    assert decision.readiness_contract.stat_performed is False
    assert decision.readiness_contract.git_command_performed is False
    assert decision.readiness_contract.subprocess_performed is False
    assert decision.readiness_contract.test_execution_performed is False
    assert decision.readiness_contract.model_call_performed is False
    assert decision.readiness_contract.tool_call_performed is False
    assert decision.readiness_contract.api_call_performed is False
    assert decision.readiness_contract.mcp_call_performed is False
    assert decision.readiness_contract.memory_access_performed is False
    assert decision.readiness_contract.report_generated is False
    assert decision.readiness_contract.export_performed is False
    assert decision.readiness_contract.read_result_created is False
    assert decision.readiness_contract.read_attempt_evidence_created is False


def test_read_plan_targets_become_non_executing_future_attempt_envelopes() -> None:
    decision = _validate(_request(), read_plan_decision=_read_plan())

    paths = {target.normalized_relative_path for target in decision.planned_targets}
    assert "README.md" in paths
    assert "src/aegis/core/repo_audit_pack.py" in paths
    assert len(decision.future_read_attempt_envelopes) == len(decision.planned_targets)
    for envelope in decision.future_read_attempt_envelopes:
        assert envelope.read_performed is False
        assert envelope.content_observed is False
        assert envelope.evidence_created is False
        assert envelope.verifier_success is False
        assert envelope.content_logging_allowed is False
        assert envelope.redaction_required is True
        assert envelope.expected_evidence_type
        assert envelope.expected_verifier
        assert envelope.failure_classification == "future_runner_must_emit_negative_evidence_on_failure"


def test_future_read_candidate_does_not_prove_file_exists_or_content_was_read() -> None:
    decision = _validate(_request(), read_plan_decision=_read_plan())

    for target in decision.planned_targets:
        assert target.source_existence_proven is False
        assert target.file_content_observed is False
        assert target.file_read_performed is False
        assert target.evidence_provided_by_readiness is False
        assert target.verifier_success is False
    assert decision.source_existence_proven is False
    assert decision.file_content_observed is False
    assert decision.file_read_performed is False


def test_missing_project_repo_identity_is_blocked() -> None:
    decision = _validate(
        _request(request_id="", project_ref="", repo_id="", repo_name="", repo_root_ref=""),
        read_plan_decision=_read_plan(),
    )

    assert decision.readiness_status == "blocked_by_missing_scope"
    assert "request_identity_required" in decision.failure_reasons
    assert "project_repo_identity_required" in decision.failure_reasons


def test_missing_tenant_or_namespace_is_blocked() -> None:
    decision = _validate(_request(tenant_scope="", namespace=""), read_plan_decision=_read_plan())

    assert decision.readiness_status == "blocked_by_missing_scope"
    assert "tenant_scope_required" in decision.failure_reasons
    assert "namespace_required" in decision.failure_reasons


def test_missing_read_plan_or_target_metadata_is_blocked() -> None:
    decision = _validate(_request(read_plan_ref=""))

    assert decision.readiness_status == "blocked_by_missing_read_plan"
    assert "read_plan_or_target_metadata_required" in decision.failure_reasons
    assert "read_plan_ref_required" in decision.failure_reasons


def test_missing_budget_policy_is_blocked() -> None:
    decision = _validate(_request(budget_policy={}), read_plan_decision=_read_plan())

    assert decision.readiness_status == "blocked_by_missing_budget"
    assert "missing_budget_policy" in decision.failure_reasons
    assert "missing_budget_file_count" in decision.failure_reasons
    assert "missing_budget_file_size" in decision.failure_reasons
    assert "missing_budget_total_bytes" in decision.failure_reasons


def test_missing_privacy_or_data_sensitivity_blocks_readiness() -> None:
    decision = _validate(
        _request(privacy_class="", data_sensitivity=""),
        read_plan_decision=_read_plan(),
    )

    assert decision.readiness_status == "blocked_by_missing_privacy_class"
    assert "privacy_class_required" in decision.failure_reasons
    assert "data_sensitivity_required" in decision.failure_reasons


def test_missing_evidence_expectation_blocks_runner_readiness() -> None:
    decision = _validate(_request(evidence_expectation=[]), read_plan_decision=_read_plan())

    assert decision.readiness_status == "blocked_by_missing_evidence_expectation"
    assert "missing_evidence_expectation" in decision.failure_reasons
    assert decision.evidence_provided_by_readiness is False


def test_missing_verifier_expectation_blocks_runner_readiness() -> None:
    decision = _validate(_request(verifier_expectation=[]), read_plan_decision=_read_plan())

    assert decision.readiness_status == "blocked_by_missing_verifier_expectation"
    assert "missing_verifier_expectation" in decision.failure_reasons
    assert decision.verifier_success is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("secret_exclusion_policy", "secret_exclusion_policy_required"),
        ("generated_artifact_policy", "generated_artifact_policy_required"),
        ("runtime_journal_policy", "runtime_journal_policy_required"),
        ("log_policy", "log_policy_required"),
        ("dependency_policy", "dependency_policy_required"),
        ("build_artifact_policy", "build_artifact_policy_required"),
        ("model_artifact_policy", "model_artifact_policy_required"),
        ("vector_db_policy", "vector_db_policy_required"),
        ("hidden_path_policy", "hidden_path_policy_required"),
        ("symlink_policy", "symlink_policy_required"),
    ],
)
def test_required_exclusion_policies_are_required(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: ""}), read_plan_decision=_read_plan())

    assert reason in decision.failure_reasons


def test_missing_content_logging_or_redaction_policy_blocks_readiness() -> None:
    missing_content = _validate(
        _request(content_logging_policy=""),
        read_plan_decision=_read_plan(),
    )
    missing_redaction = _validate(
        _request(redaction_policy=""),
        read_plan_decision=_read_plan(),
    )

    assert missing_content.readiness_status == "blocked_by_content_logging_policy"
    assert "content_logging_policy_required" in missing_content.failure_reasons
    assert missing_redaction.readiness_status == "blocked_by_redaction_policy"
    assert "redaction_policy_required" in missing_redaction.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("raw_content_logging_default", "raw_content_logging_default_denied"),
        ("binary_content_logged", "binary_content_logging_denied"),
        ("generated_artifact_content_logged", "generated_artifact_content_logging_denied"),
        ("runtime_journal_content_logged", "runtime_journal_content_logging_denied"),
        ("model_vector_content_logged", "model_vector_content_logging_denied"),
    ],
)
def test_content_logging_escape_hatches_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}), read_plan_decision=_read_plan())

    assert decision.readiness_status == "blocked_by_content_logging_policy"
    assert reason in decision.failure_reasons


def test_denied_targets_preserve_reason_and_cannot_become_read_attempts() -> None:
    decision = _validate(
        _request(
            planned_targets=[],
            denied_targets=[
                {
                    "original_path": ".env",
                    "normalized_relative_path": ".env",
                    "category": "denied_secret_path",
                    "denial_reason": "secret_path_denied",
                }
            ],
        )
    )

    assert decision.readiness_status == "blocked_by_secret_policy"
    assert "denied_secret_path_preserved" in decision.failure_reasons
    assert "secret_path_denied" in decision.failure_reasons
    assert decision.denied_targets[0].denial_reason == "secret_path_denied"
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


def test_denied_target_in_planned_targets_is_rejected() -> None:
    decision = _validate(
        _request(
            planned_targets=[
                {
                    "original_path": ".env",
                    "normalized_relative_path": ".env",
                    "category": "denied_secret_path",
                    "denial_reason": "secret_path_denied",
                }
            ]
        )
    )

    assert decision.readiness_status == "blocked_by_secret_policy"
    assert "planned_target_category_denied_denied_secret_path" in decision.failure_reasons
    assert "planned_target_path_denied_denied_secret_path" in decision.failure_reasons
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


def test_future_gated_hidden_and_symlink_targets_remain_gated_without_attempts() -> None:
    read_plan = _read_plan(
        candidate_paths=[
            {
                "path": "docs/.config.md",
                "future_gate_ref": "approval:hidden-path",
            },
            {
                "path": "docs/link.md",
                "is_symlink": True,
                "future_gate_ref": "approval:symlink",
            },
        ],
        hidden_file_policy="explicit_future_gate_required",
        symlink_policy="explicit_future_gate_required",
    )

    decision = _validate(_request(), read_plan_decision=read_plan)

    assert decision.readiness_status == "readiness_ready_requires_human_review"
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()
    assert {target.category for target in decision.future_gated_targets} == {
        "future_gated_hidden_path",
        "future_gated_symlink",
    }
    for target in decision.future_gated_targets:
        assert target.human_review_required is True
        assert target.future_gate_reason
        assert target.file_read_performed is False


def test_budget_excess_requires_human_review_without_counting_files_or_bytes() -> None:
    decision = _validate(
        _request(
            budget_policy={
                "max_file_count": 10_000,
                "max_file_size_bytes": 200_000,
                "max_total_bytes": 5_000_000,
                "budget_policy": "human_review_required_above_limits",
            }
        ),
        read_plan_decision=_read_plan(),
    )

    assert decision.readiness_status == "readiness_ready_requires_human_review"
    assert "budget_excess_requires_human_review" in decision.failure_reasons
    assert decision.budget.actual_files_counted is False
    assert decision.budget.actual_bytes_counted is False


def test_unsafe_read_plan_decision_is_rejected() -> None:
    base = _read_plan()
    unsafe = replace(
        base,
        runtime_dispatch_allowed=True,
        read_plan_contract=replace(base.read_plan_contract, verifier_success=True),
    )

    decision = _validate(_request(), read_plan_decision=unsafe)

    assert decision.readiness_status == "blocked_by_missing_read_plan"
    assert "read_plan_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert "read_plan_unsafe_contract_claim_denied" in decision.failure_reasons


def test_tampered_read_plan_execution_permission_claim_is_rejected() -> None:
    read_plan = _tampered_read_plan(execution_permission="granted_by_tampered_read_plan")

    decision = _validate(_request(), read_plan_decision=read_plan)

    assert decision.readiness_status == "blocked_by_missing_read_plan"
    assert "read_plan_execution_permission_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.execution_permission == REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_dispatch_allowed", "read_plan_runtime_dispatch_attempt_denied"),
        ("file_read_performed", "read_plan_unsafe_behavior_claim_denied"),
        ("filesystem_traversal_performed", "read_plan_unsafe_behavior_claim_denied"),
        ("stat_performed", "read_plan_unsafe_behavior_claim_denied"),
        ("report_generated", "read_plan_unsafe_behavior_claim_denied"),
        ("export_performed", "read_plan_unsafe_behavior_claim_denied"),
        ("source_existence_proven", "read_plan_evidence_claim_denied"),
        ("file_content_observed", "read_plan_evidence_claim_denied"),
        ("evidence_provided_by_read_plan", "read_plan_evidence_claim_denied"),
        ("verifier_success", "read_plan_verifier_success_claim_denied"),
        ("proof_file_content", "read_plan_proof_or_certification_claim_denied"),
        ("certification_claim", "read_plan_proof_or_certification_claim_denied"),
        ("official_audit_result", "read_plan_proof_or_certification_claim_denied"),
    ],
)
def test_tampered_read_plan_behavior_proof_evidence_and_verifier_claims_block(
    field: str,
    reason: str,
) -> None:
    decision = _validate(_request(), read_plan_decision=_tampered_read_plan(**{field: True}))

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.file_read_performed is False
    assert decision.evidence_provided_by_readiness is False
    assert decision.verifier_success is False


def test_tampered_read_plan_cannot_launder_denied_path_into_planned_targets() -> None:
    read_plan = _tampered_read_plan(
        planned_targets=(
            SimpleNamespace(
                original_path=".env",
                normalized_relative_path=".env",
                category="future_read_candidate",
                decision_reason="tampered_future_read_candidate",
                expected_evidence=("file_read_attempt_evidence_expected",),
                expected_verifier=("path_within_repo_root_verifier",),
                source_existence_proven=False,
                file_content_observed=False,
                file_read_performed=False,
                evidence_provided_by_read_plan=False,
                verifier_success=False,
            ),
        ),
        denied_targets=(),
        future_gated_targets=(),
    )

    decision = _validate(_request(), read_plan_decision=read_plan)

    assert decision.readiness_status == "blocked_by_secret_policy"
    assert "planned_target_path_denied_denied_secret_path" in decision.failure_reasons
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


@pytest.mark.parametrize(
    ("category", "status"),
    [
        ("denied_secret_path", "blocked_by_secret_policy"),
        ("denied_runtime_journal", "blocked_by_runtime_journal_policy"),
        ("denied_log_path", "blocked_by_log_policy"),
        ("denied_dependency_path", "blocked_by_dependency_policy"),
        ("denied_build_cache", "blocked_by_build_artifact_policy"),
        ("denied_model_artifact", "blocked_by_model_artifact_policy"),
        ("denied_vector_db", "blocked_by_vector_db_policy"),
        ("denied_external_path", "blocked_by_unsafe_read_plan"),
        ("denied_traversal_path", "blocked_by_unsafe_read_plan"),
        ("denied_hidden_path", "blocked_by_hidden_path_policy"),
        ("denied_symlink", "blocked_by_symlink_policy"),
    ],
)
def test_denied_read_plan_target_categories_remain_denied(category: str, status: str) -> None:
    decision = _validate(
        _request(denied_targets=[_target(category, "blocked/path.txt")])
    )

    assert decision.readiness_status == status
    assert f"{category}_preserved" in decision.failure_reasons
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


@pytest.mark.parametrize(
    ("path", "reason", "status"),
    [
        (".env", "planned_target_path_denied_denied_secret_path", "blocked_by_secret_policy"),
        ("credentials/token.txt", "planned_target_path_denied_denied_secret_path", "blocked_by_secret_policy"),
        ("logs/runtime_events.jsonl", "planned_target_path_denied_denied_log_path", "blocked_by_log_policy"),
        ("journal/runtime.jsonl", "planned_target_path_denied_denied_runtime_journal", "blocked_by_runtime_journal_policy"),
        ("evidence/action.json", "planned_target_path_denied_denied_runtime_journal", "blocked_by_runtime_journal_policy"),
        ("replay/session.jsonl", "planned_target_path_denied_denied_runtime_journal", "blocked_by_runtime_journal_policy"),
        (".git/config", "planned_target_path_denied_denied_dependency_path", "blocked_by_dependency_policy"),
        (".venv/pyvenv.cfg", "planned_target_path_denied_denied_dependency_path", "blocked_by_dependency_policy"),
        ("node_modules/pkg/index.js", "planned_target_path_denied_denied_dependency_path", "blocked_by_dependency_policy"),
        (".next/server/app.js", "planned_target_path_denied_denied_build_cache", "blocked_by_build_artifact_policy"),
        ("dist/app.js", "planned_target_path_denied_denied_build_cache", "blocked_by_build_artifact_policy"),
        ("models/local.gguf", "planned_target_path_denied_denied_model_artifact", "blocked_by_model_artifact_policy"),
        ("vector_db/index.sqlite", "planned_target_path_denied_denied_vector_db", "blocked_by_vector_db_policy"),
        ("screenshots/home.png", "planned_target_path_denied_denied_generated_artifact", "blocked_by_generated_artifact_policy"),
        ("C:/Users/nemes/Desktop/Aegis/README.md", "planned_target_path_denied_denied_external_path", "blocked_by_unsafe_read_plan"),
        ("//server/share/README.md", "planned_target_path_denied_denied_external_path", "blocked_by_unsafe_read_plan"),
        ("~/Aegis/README.md", "planned_target_path_denied_denied_external_path", "blocked_by_unsafe_read_plan"),
        ("src/../secret.py", "planned_target_path_denied_denied_traversal_path", "blocked_by_unsafe_read_plan"),
        ("src/aegis/core/\x00bad.py", "planned_target_path_denied_denied_unknown", "blocked_by_unsafe_read_plan"),
    ],
)
def test_path_policy_chain_blocks_forbidden_planned_target_paths(
    path: str,
    reason: str,
    status: str,
) -> None:
    decision = _validate(
        _request(planned_targets=[_target("future_read_candidate", path)])
    )

    assert decision.readiness_status == status
    assert reason in decision.failure_reasons
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


@pytest.mark.parametrize(
    "category",
    [
        "future_gated_hidden_path",
        "future_gated_symlink",
        "future_gated_large_file",
        "future_gated_sensitive_path",
    ],
)
def test_future_gated_target_categories_remain_gated_and_do_not_create_attempts(
    category: str,
) -> None:
    decision = _validate(
        _request(
            future_gated_targets=[
                _target(
                    category,
                    "src/aegis/core/repo_audit_pack.py",
                    future_gate_reason=f"{category}_requires_future_gate",
                )
            ]
        )
    )

    assert decision.readiness_status == "readiness_ready_requires_human_review"
    assert decision.future_gated_targets[0].category == category
    assert decision.future_gated_targets[0].human_review_required is True
    assert decision.planned_targets == ()
    assert decision.future_read_attempt_envelopes == ()


def test_future_gated_target_without_human_review_is_flagged() -> None:
    decision = _validate(
        _request(
            future_gated_targets=[
                _target(
                    "future_gated_sensitive_path",
                    "src/aegis/core/repo_audit_pack.py",
                    human_review_required=False,
                )
            ]
        )
    )

    assert decision.readiness_status == "readiness_ready_requires_human_review"
    assert "future_gated_target_human_review_required" in decision.failure_reasons
    assert decision.future_read_attempt_envelopes == ()


def test_secret_logging_must_remain_disabled() -> None:
    decision = _validate(
        _request(secrets_never_logged=False),
        read_plan_decision=_read_plan(),
    )

    assert decision.readiness_status == "blocked_by_content_logging_policy"
    assert "secret_logging_denied" in decision.failure_reasons
    assert decision.content_policy.secrets_never_logged is False


@pytest.mark.parametrize(
    "field",
    [
        "actual_source_inventory_performed",
        "file_read_performed",
        "filesystem_traversal_performed",
        "file_stat_performed",
        "git_command_performed",
        "test_execution_performed",
        "model_call_performed",
        "tool_call_performed",
        "api_call_performed",
        "mcp_call_performed",
        "memory_access_performed",
    ],
)
def test_source_inventory_behavior_claims_are_rejected(field: str) -> None:
    source_inventory = _unsafe_related_decision(**{field: True})

    decision = _validate(
        _request(),
        read_plan_decision=_read_plan(),
        source_inventory_decision=source_inventory,
    )

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "source_inventory_behavior_claim_denied" in decision.failure_reasons
    assert decision.file_read_performed is False


@pytest.mark.parametrize(
    ("argument_name", "expected_prefix", "claims"),
    [
        (
            "repo_audit_decision",
            "repo_audit",
            {"proof_file_content": True, "certification_claim": True},
        ),
        (
            "mission_control_decision",
            "mission_control",
            {"approval_grant": True, "lease_grant": True},
        ),
        (
            "tool_simulation_decision",
            "tool_simulation",
            {"dispatch_performed": True, "tool_call_performed": True},
        ),
        (
            "developer_work_passport_decision",
            "developer_work_passport",
            {"developer_work_passport_certification": True, "hidden_monitoring": True},
        ),
        (
            "compliance_evidence_decision",
            "compliance_evidence",
            {"legal_certification": True, "court_admissible": True},
        ),
        (
            "plugin_review_decision",
            "plugin_review",
            {"plugin_execution_allowed": True, "dynamic_import_allowed": True},
        ),
    ],
)
def test_related_decision_domain_specific_bypass_claims_are_rejected(
    argument_name: str,
    expected_prefix: str,
    claims: dict[str, object],
) -> None:
    decision = _validate(
        _request(),
        read_plan_decision=_read_plan(),
        **{argument_name: _unsafe_related_decision(**claims)},
    )

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert (
        f"{expected_prefix}_permission_claim_denied" in decision.failure_reasons
        or f"{expected_prefix}_behavior_claim_denied" in decision.failure_reasons
        or f"{expected_prefix}_proof_or_certification_claim_denied" in decision.failure_reasons
    )
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("argument_name", "expected_prefix"),
    [
        ("source_inventory_decision", "source_inventory"),
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

    decision = _validate(
        _request(),
        read_plan_decision=_read_plan(),
        **{argument_name: unsafe},
    )

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
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
    decision = _validate(_request(**{field: True}), read_plan_decision=_read_plan())

    assert reason in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("evidence_provided_by_readiness", "readiness_cannot_provide_evidence"),
        ("evidence_provided_by_read_plan", "readiness_cannot_provide_evidence"),
        ("verifier_success", "readiness_cannot_mark_verifier_success"),
        ("verified_success", "readiness_cannot_mark_verifier_success"),
        ("proof_repo_state", "proof_repo_state_claim_denied"),
        ("proof_file_exists", "proof_file_exists_claim_denied"),
        ("proof_file_content", "proof_file_content_claim_denied"),
        ("certification_claim", "certification_claim_denied"),
        ("official_audit_result", "official_audit_result_claim_denied"),
    ],
)
def test_evidence_verifier_proof_and_certification_claims_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = _validate(_request(**{field: True}), read_plan_decision=_read_plan())

    assert reason in decision.failure_reasons
    assert decision.evidence_provided_by_readiness is False
    assert decision.verifier_success is False
    assert decision.certification_claim is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runner_executed", "runner_execution_request_denied"),
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
        ("read_result_created", "read_result_creation_denied"),
        ("read_attempt_evidence_created", "read_attempt_evidence_creation_denied"),
    ],
)
def test_execution_tool_model_api_mcp_memory_report_and_export_flags_are_rejected(
    field: str,
    reason: str,
) -> None:
    decision = _validate(_request(**{field: True}), read_plan_decision=_read_plan())

    assert reason in decision.failure_reasons
    assert decision.runner_executed is False
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
    assert decision.read_result_created is False
    assert decision.read_attempt_evidence_created is False


def test_requested_tools_models_mcp_and_claims_are_rejected() -> None:
    decision = _validate(
        _request(
            requested_tools=["read_file"],
            requested_models=["local-llm"],
            requested_mcp_tools=["filesystem.read"],
            api_call_requested=True,
            claims=["proof file content", "tests passed", "official audit result"],
        ),
        read_plan_decision=_read_plan(),
    )

    assert "tool_call_request_denied" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons
    assert "mcp_call_request_denied" in decision.failure_reasons
    assert "api_call_request_denied" in decision.failure_reasons
    assert "proof_file_content_claim_denied" in decision.failure_reasons
    assert "test_success_claim_denied" in decision.failure_reasons
    assert "official_audit_result_claim_denied" in decision.failure_reasons


def test_forbidden_runner_scope_is_rejected_without_dispatch() -> None:
    decision = _validate(
        _request(runner_scope=["metadata_only_runner_readiness", "actual_file_read"]),
        read_plan_decision=_read_plan(),
    )

    assert decision.readiness_status == "blocked_by_missing_scope"
    assert "forbidden_runner_scope_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False


def test_output_never_sets_execution_or_observation_invariants_true() -> None:
    decision = _validate(_request(), read_plan_decision=_read_plan())

    assert decision.runner_executed is False
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
    assert decision.read_result_created is False
    assert decision.read_attempt_evidence_created is False
    for target in decision.planned_targets:
        assert target.source_existence_proven is False
        assert target.file_content_observed is False
    for envelope in decision.future_read_attempt_envelopes:
        assert envelope.read_performed is False
        assert envelope.content_observed is False
        assert envelope.evidence_created is False


def test_validation_does_not_mutate_input_or_supplied_decisions() -> None:
    request = _request()
    before = deepcopy(request)
    read_plan = _read_plan()
    related = _unsafe_related_decision()

    decision = _validate(
        request,
        read_plan_decision=read_plan,
        implementation_readiness_decision=related,
    )

    assert request == before
    assert read_plan.runtime_dispatch_allowed is False
    assert related.runtime_dispatch_allowed is False
    assert decision.runtime_dispatch_allowed is False
    with pytest.raises(FrozenInstanceError):
        decision.runtime_dispatch_allowed = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decision.readiness_contract.file_read_performed = True  # type: ignore[misc]
