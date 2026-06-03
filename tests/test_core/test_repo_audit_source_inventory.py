from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from aegis.core.repo_audit_source_inventory import (
    REPO_AUDIT_SOURCE_INVENTORY_DESIGN_VERSION,
    REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION,
    validate_repo_audit_source_inventory_design,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "inventory_id": "repo-audit-source-inventory:aegis:1",
        "repo_id": "WexyS/Aegis",
        "repo_name": "Aegis",
        "repo_root_ref": "workspace:aegis",
        "commit_ref": "152e4df",
        "branch_ref": "main",
        "tenant_scope": "local",
        "project_scope": "aegis",
        "namespace": "repo_audit",
        "source_refs": [
            {"ref_id": "commit:152e4df", "ref_type": "commit"},
            {"ref_id": "contract:repo-audit-pack", "ref_type": "contract"},
        ],
        "source_inventory_scope": [
            "source_inventory_design",
            "path_policy_validation",
            "exclusion_policy_validation",
            "source_budget_validation",
            "metadata_only_inventory_candidate",
        ],
        "candidate_paths": [
            {"path": "README.md", "path_type": "documentation"},
            {"path": "pyproject.toml", "path_type": "config"},
            {"path": "src/aegis/core/repo_audit_pack.py", "path_type": "source"},
            {"path": "tests/test_core/test_repo_audit_pack.py", "path_type": "test"},
            {"path": "docs/repo-audit-pack-read-only-contract-v1.md", "path_type": "docs"},
        ],
        "path_policy": {
            "allowed_prefixes": ["src/", "tests/", "docs/"],
            "allow_repo_root_files": True,
            "forbidden_paths": [
                ".git/",
                ".venv/",
                "logs/",
                "node_modules/",
                "dist/",
                "build/",
                "data/",
            ],
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
        "output_categories": [
            "allowed_path_candidate",
            "denied_path_candidate",
            "future_read_plan_candidate",
            "source_inventory_limitation",
        ],
        "privacy_class": "project_internal",
        "data_sensitivity": "source_code",
        "limitations": ["metadata-only design; no file existence claims"],
        "unknowns": ["candidate paths are caller supplied"],
        "authority": False,
        "execution_permission": REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION,
        "runtime_dispatch_allowed": False,
    }
    request.update(overrides)
    return request


def _validate(request: dict[str, object], **related_decisions: object):
    return validate_repo_audit_source_inventory_design(request, **related_decisions)


def _safe_related_decision(**overrides: object) -> SimpleNamespace:
    decision = SimpleNamespace(
        validation_status="review_ready",
        readiness_status="ready",
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
        verifier_success=False,
        verified_success=False,
        success=False,
        execution_permission="not_granted_by_related_contract",
    )
    for key, value in overrides.items():
        setattr(decision, key, value)
    return decision


def test_valid_source_inventory_design_is_metadata_only_and_non_dispatchable() -> None:
    decision = _validate(_request())

    assert decision.contract_version == REPO_AUDIT_SOURCE_INVENTORY_DESIGN_VERSION
    assert decision.validation_status == "design_ready"
    assert decision.failure_reasons == ()
    assert decision.execution_permission == REPO_AUDIT_SOURCE_INVENTORY_EXECUTION_PERMISSION
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False
    assert decision.capability_grant is False
    assert decision.lease_grant is False
    assert decision.source_inventory_contract.design_only is True
    assert decision.source_inventory_contract.actual_source_inventory_performed is False
    assert decision.source_inventory_contract.repo_scan_performed is False
    assert decision.source_inventory_contract.file_read_performed is False
    assert decision.source_inventory_contract.filesystem_traversal_performed is False
    assert decision.source_inventory_contract.file_stat_performed is False
    assert decision.source_inventory_contract.git_command_performed is False
    assert decision.source_inventory_contract.test_execution_performed is False
    assert decision.source_inventory_contract.subprocess_performed is False
    assert decision.source_inventory_contract.model_call_performed is False
    assert decision.source_inventory_contract.tool_call_performed is False
    assert decision.source_inventory_contract.api_call_performed is False
    assert decision.source_inventory_contract.mcp_call_performed is False
    assert decision.source_inventory_contract.memory_access_performed is False
    assert decision.source_inventory_contract.report_generated is False
    assert decision.source_inventory_contract.export_performed is False
    assert decision.source_inventory_contract.evidence_provided_by_inventory is False
    assert decision.source_inventory_contract.verifier_success is False


def test_allowed_path_candidates_do_not_claim_existence_read_or_evidence() -> None:
    decision = _validate(_request(candidate_paths=["README.md", "src/aegis/core/example.py"]))

    assert decision.validation_status == "design_ready"
    assert [candidate.normalized_path for candidate in decision.allowed_path_candidates] == [
        "README.md",
        "src/aegis/core/example.py",
    ]
    assert decision.denied_paths == ()
    for candidate in decision.allowed_path_candidates:
        assert candidate.metadata_only is True
        assert candidate.exists_confirmed is False
        assert candidate.file_read_performed is False
        assert candidate.file_stat_performed is False
        assert candidate.evidence_provided_by_inventory is False
        assert candidate.verifier_success is False


def test_source_inventory_decision_is_immutable_and_does_not_mutate_input() -> None:
    request = _request()
    before = deepcopy(request)

    decision = _validate(request)

    assert request == before
    with pytest.raises(FrozenInstanceError):
        decision.runtime_dispatch_allowed = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decision.source_inventory_contract.file_read_performed = True  # type: ignore[misc]
    replaced = replace(decision, validation_status="copied")
    assert decision.validation_status == "design_ready"
    assert replaced.validation_status == "copied"


def test_missing_identity_namespace_or_scope_is_denied() -> None:
    decision = _validate(
        _request(
            inventory_id="",
            repo_id="",
            repo_name="",
            tenant_scope="",
            namespace="",
            source_inventory_scope=[],
        )
    )

    assert decision.validation_status == "failed_validation"
    assert "inventory_identity_required" in decision.failure_reasons
    assert "repo_identity_required" in decision.failure_reasons
    assert "tenant_scope_required" in decision.failure_reasons
    assert "namespace_required" in decision.failure_reasons
    assert "source_inventory_scope_required" in decision.failure_reasons


def test_candidate_paths_or_explicit_future_read_plan_metadata_is_required() -> None:
    denied = _validate(_request(candidate_paths=[]))
    allowed_future_plan = _validate(
        _request(
            candidate_paths=[],
            source_inventory_scope=["future_read_plan_candidate"],
            future_read_plan={
                "plan_id": "future-read-plan:aegis:1",
                "requires_boundary_approval": True,
                "can_read_now": False,
            },
        )
    )

    assert denied.validation_status == "failed_validation"
    assert "candidate_paths_or_future_read_plan_required" in denied.failure_reasons
    assert allowed_future_plan.validation_status == "design_ready"
    assert allowed_future_plan.future_read_plan.can_read_now is False
    assert allowed_future_plan.future_read_plan.requires_evidence_boundary is True
    assert allowed_future_plan.source_inventory_contract.file_read_performed is False


def test_unknown_or_forbidden_source_inventory_scope_is_blocked() -> None:
    unknown = _validate(_request(source_inventory_scope=["source_inventory_design", "imaginary_scope"]))
    forbidden = _validate(
        _request(
            source_inventory_scope=[
                "source_inventory_design",
                "actual_source_inventory",
                "repo_filesystem_walk",
                "file_content_read",
                "git_ls_files",
                "test_execution",
                "model_assisted_inventory",
                "report_export",
                "proof_repo_state",
            ]
        )
    )

    assert unknown.validation_status == "blocked"
    assert "unknown_source_inventory_scope" in unknown.failure_reasons
    assert forbidden.validation_status == "blocked"
    assert "forbidden_source_inventory_scope_denied" in forbidden.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("repo_scan_performed", "repo_scan_request_denied"),
        ("file_read_performed", "file_read_request_denied"),
        ("filesystem_traversal_performed", "filesystem_traversal_request_denied"),
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
        ("signed_inventory_requested", "signed_inventory_request_denied"),
    ],
)
def test_execution_and_export_requests_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert decision.validation_status == "blocked"
    assert reason in decision.failure_reasons
    assert decision.source_inventory_contract.actual_source_inventory_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority", "authority_must_be_false"),
        ("runtime_dispatch_allowed", "runtime_dispatch_not_allowed"),
        ("approval_grant", "approval_grant_not_allowed"),
        ("capability_grant", "capability_grant_not_allowed"),
        ("lease_grant", "lease_grant_not_allowed"),
        ("frontend_authority", "frontend_authority_not_allowed"),
        ("evidence_provided_by_inventory", "inventory_cannot_provide_evidence"),
        ("verifier_success", "inventory_cannot_mark_verifier_success"),
        ("verified_success", "inventory_cannot_mark_verifier_success"),
        ("success", "success_claim_denied"),
    ],
)
def test_authority_evidence_verifier_and_success_claims_are_rejected(
    field: str, reason: str
) -> None:
    decision = _validate(_request(**{field: True}))

    assert decision.validation_status == "blocked"
    assert reason in decision.failure_reasons
    assert decision.authority is False
    assert decision.runtime_dispatch_allowed is False


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("C:/Users/nemes/Desktop/Aegis/src/aegis/core/x.py", "absolute_path_denied"),
        ("C:", "drive_root_path_denied"),
        ("C:/", "drive_root_path_denied"),
        ("//server/share/file.py", "unc_path_denied"),
        ("/workspace/Aegis/file.py", "absolute_path_denied"),
        ("file:///C:/Users/nemes/Desktop/Aegis/file.py", "external_path_denied"),
        ("https://example.com/file.py", "external_path_denied"),
        ("src/aegis/../secrets.py", "path_traversal_denied"),
        ("~/Aegis/file.py", "home_relative_path_denied"),
        ("", "empty_path_denied"),
        ("src/aegis/core/\x00bad.py", "path_control_character_denied"),
    ],
)
def test_absolute_external_traversal_and_control_paths_are_denied(
    path: str, reason: str
) -> None:
    decision = _validate(_request(candidate_paths=[path]))

    assert decision.validation_status == "blocked"
    assert reason in decision.failure_reasons
    assert decision.allowed_path_candidates == ()


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
def test_secret_and_privacy_sensitive_paths_are_denied(path: str) -> None:
    decision = _validate(_request(candidate_paths=[path]))

    assert decision.validation_status == "blocked"
    assert "secret_path_denied" in decision.failure_reasons
    assert decision.allowed_path_candidates == ()


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("logs/backend.log", "runtime_or_log_path_denied"),
        ("logs/runtime_events.jsonl", "runtime_or_log_path_denied"),
        ("journal/runtime.jsonl", "runtime_or_log_path_denied"),
        ("evidence/smoke.json", "runtime_or_log_path_denied"),
        ("replay/session.jsonl", "runtime_or_log_path_denied"),
        (".git/config", "generated_or_cache_path_denied"),
        (".venv/pyvenv.cfg", "generated_or_cache_path_denied"),
        ("node_modules/pkg/index.js", "generated_or_cache_path_denied"),
        ("dist/app.js", "generated_or_cache_path_denied"),
        ("build/app.js", "generated_or_cache_path_denied"),
        ("coverage/index.html", "generated_or_cache_path_denied"),
        ("data/source.db", "data_path_denied"),
        ("models/local.gguf", "model_vector_dataset_path_denied"),
        ("vector_db/index.bin", "model_vector_dataset_path_denied"),
        ("datasets/source.jsonl", "model_vector_dataset_path_denied"),
        ("screenshots/home.png", "screenshot_browser_output_path_denied"),
        ("browser-output/run.html", "screenshot_browser_output_path_denied"),
        ("playwright-report/index.html", "screenshot_browser_output_path_denied"),
    ],
)
def test_runtime_generated_model_data_and_browser_output_paths_are_denied(
    path: str, reason: str
) -> None:
    decision = _validate(_request(candidate_paths=[path]))

    assert decision.validation_status == "blocked"
    assert reason in decision.failure_reasons
    assert decision.allowed_path_candidates == ()


def test_hidden_paths_are_denied_unless_explicitly_future_gated() -> None:
    denied = _validate(_request(candidate_paths=["src/aegis/.internal/design.md"]))
    allowed = _validate(
        _request(
            candidate_paths=[
                {
                    "path": "src/aegis/.internal/design.md",
                    "path_type": "future_metadata",
                    "future_gate_ref": "approval:future-hidden-path-review",
                }
            ],
            source_inventory_scope=[
                "source_inventory_design",
                "future_read_plan_candidate",
            ],
            path_policy={
                **dict(_request()["path_policy"]),  # type: ignore[arg-type]
                "hidden_path_policy": "explicit_future_gate_required",
            },
        )
    )

    assert denied.validation_status == "blocked"
    assert "hidden_path_denied" in denied.failure_reasons
    assert allowed.validation_status == "design_ready"
    assert allowed.allowed_path_candidates[0].metadata_only is True
    assert allowed.allowed_path_candidates[0].exists_confirmed is False


def test_symlink_paths_are_denied_unless_explicitly_future_gated() -> None:
    denied = _validate(
        _request(candidate_paths=[{"path": "docs/link.md", "is_symlink": True}])
    )
    allowed = _validate(
        _request(
            candidate_paths=[
                {
                    "path": "docs/link.md",
                    "is_symlink": True,
                    "future_gate_ref": "approval:future-symlink-review",
                }
            ],
            source_inventory_scope=[
                "source_inventory_design",
                "future_read_plan_candidate",
            ],
            path_policy={
                **dict(_request()["path_policy"]),  # type: ignore[arg-type]
                "symlink_policy": "explicit_future_gate_required",
            },
        )
    )

    assert denied.validation_status == "blocked"
    assert "symlink_candidate_denied" in denied.failure_reasons
    assert allowed.validation_status == "design_ready"
    assert allowed.allowed_path_candidates[0].metadata_only is True
    assert allowed.source_inventory_contract.filesystem_traversal_performed is False


def test_missing_or_excessive_budget_is_denied_or_requires_review() -> None:
    missing = _validate(_request(budget={}))
    excessive = _validate(
        _request(
            budget={
                "max_file_count": 25_000,
                "max_file_size_bytes": 25_000_000,
                "max_total_bytes": 1_000_000_000,
                "budget_policy": "human_review_required_above_limits",
            }
        )
    )

    assert missing.validation_status == "failed_validation"
    assert "budget_policy_required" in missing.failure_reasons
    assert "budget_file_count_required" in missing.failure_reasons
    assert "budget_file_size_required" in missing.failure_reasons
    assert "budget_total_bytes_required" in missing.failure_reasons
    assert excessive.validation_status == "requires_human_review"
    assert "budget_file_count_exceeds_review_limit" in excessive.failure_reasons
    assert "budget_file_size_exceeds_review_limit" in excessive.failure_reasons
    assert "budget_total_bytes_exceeds_review_limit" in excessive.failure_reasons
    assert excessive.budget_decision.requires_human_review is True
    assert excessive.budget_decision.actual_bytes_counted is False


def test_high_risk_inventory_scope_requires_privacy_and_data_sensitivity() -> None:
    decision = _validate(
        _request(
            source_inventory_scope=[
                "source_inventory_design",
                "secret_exclusion_design",
                "generated_artifact_exclusion_design",
            ],
            privacy_class="",
            data_sensitivity="",
        )
    )

    assert decision.validation_status == "failed_validation"
    assert "high_risk_inventory_requires_privacy_class" in decision.failure_reasons
    assert "high_risk_inventory_requires_data_sensitivity" in decision.failure_reasons


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("proof_repo_state", "proof_repo_state_claim_denied"),
        ("proof_file_exists", "proof_file_exists_claim_denied"),
        ("proof_tests_passed", "test_success_claim_denied"),
        ("proof_code_safe", "code_safety_claim_denied"),
        ("proof_secure", "security_proof_claim_denied"),
        ("proof_compliant", "compliance_proof_claim_denied"),
    ],
)
def test_proof_claim_fields_are_rejected(field: str, reason: str) -> None:
    decision = _validate(_request(**{field: True}))

    assert decision.validation_status == "blocked"
    assert reason in decision.failure_reasons


@pytest.mark.parametrize(
    ("argument_name", "expected_prefix"),
    [
        ("implementation_readiness_decision", "implementation_readiness"),
        ("repo_audit_decision", "repo_audit"),
        ("developer_work_passport_decision", "developer_work_passport"),
        ("compliance_evidence_decision", "compliance_evidence"),
        ("mission_control_decision", "mission_control"),
        ("tool_simulation_decision", "tool_simulation"),
        ("plugin_review_decision", "plugin_review"),
        ("context_compiler_decision", "context_compiler"),
        ("policy_decision", "policy"),
    ],
)
def test_unsafe_related_decisions_are_rejected(argument_name: str, expected_prefix: str) -> None:
    unsafe = _safe_related_decision(
        runtime_dispatch_allowed=True,
        evidence_provided_by_pack_output=True,
        verifier_success=True,
        success=True,
    )

    decision = _validate(_request(), **{argument_name: unsafe})

    assert decision.validation_status == "blocked"
    assert f"{expected_prefix}_runtime_dispatch_attempt_denied" in decision.failure_reasons
    assert f"{expected_prefix}_evidence_claim_denied" in decision.failure_reasons
    assert f"{expected_prefix}_verifier_success_claim_denied" in decision.failure_reasons
    assert f"{expected_prefix}_success_claim_denied" in decision.failure_reasons


def test_safe_related_decisions_keep_source_inventory_design_ready() -> None:
    decision = _validate(
        _request(),
        implementation_readiness_decision=_safe_related_decision(),
        repo_audit_decision=_safe_related_decision(),
        developer_work_passport_decision=_safe_related_decision(),
        compliance_evidence_decision=_safe_related_decision(),
        mission_control_decision=_safe_related_decision(),
        tool_simulation_decision=_safe_related_decision(),
        plugin_review_decision=_safe_related_decision(),
        context_compiler_decision=_safe_related_decision(),
        policy_decision=_safe_related_decision(),
    )

    assert decision.validation_status == "design_ready"
    assert decision.failure_reasons == ()
    assert decision.source_inventory_contract.actual_source_inventory_performed is False


def test_related_decision_failures_block_readiness_claims() -> None:
    related = _safe_related_decision(failure_reasons=("related_failure",))

    decision = _validate(_request(), implementation_readiness_decision=related)

    assert decision.validation_status == "blocked"
    assert "implementation_readiness_decision_has_failures" in decision.failure_reasons


def test_finding_output_is_a_limitation_not_verification_or_evidence() -> None:
    decision = _validate(_request())

    assert decision.findings
    assert all(finding.finding_type == "source_inventory_limitation" for finding in decision.findings)
    assert all(finding.evidence_provided is False for finding in decision.findings)
    assert all(finding.verifier_success is False for finding in decision.findings)
    assert all(finding.requires_human_review is True for finding in decision.findings)
