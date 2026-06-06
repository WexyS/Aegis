from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api.repo_audit_dry_run_projection import (
    REPO_AUDIT_DRY_RUN_API_SURFACE_EXECUTION_PERMISSION,
    build_repo_audit_dry_run_projection_api_response,
)
from aegis.main import app


API_PATH = "/maintenance/repo-audit/dry-run-projection"


def _assert_read_only_invariants(data: dict[str, object]) -> None:
    assert data["read_only"] is True
    assert data["mutation_performed"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == REPO_AUDIT_DRY_RUN_API_SURFACE_EXECUTION_PERMISSION
    assert data["approval_grant"] is False
    assert data["capability_grant"] is False
    assert data["lease_grant"] is False
    assert data["evidence_provided"] is False
    assert data["verifier_success"] is False
    assert data["frontend_authority"] is False
    assert data["api_authority"] is False
    assert data["repo_read_performed"] is False
    assert data["repo_scan_performed"] is False
    assert data["directory_scan_performed"] is False
    assert data["file_list_performed"] is False
    assert data["file_stat_performed"] is False
    assert data["file_hash_performed"] is False
    assert data["file_read_performed"] is False
    assert data["github_api_called"] is False
    assert data["github_url_fetched"] is False
    assert data["browser_fetch_performed"] is False
    assert data["raw_file_fetch_performed"] is False
    assert data["git_clone_performed"] is False
    assert data["http_request_performed"] is False
    assert data["external_api_called"] is False
    assert data["mcp_call_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["model_call_performed"] is False
    assert data["web_query_performed"] is False
    assert data["memory_retrieval_performed"] is False
    assert data["context_retrieval_performed"] is False
    assert data["context_package_created"] is False
    assert data["cache_written"] is False
    assert data["source_record_created"] is False
    assert data["citation_record_created"] is False
    assert data["report_generated"] is False
    assert data["generated_artifact_created"] is False
    assert data["data_sent_external"] is False
    assert data["source_truth_claimed"] is False
    assert data["repo_audit_proof_claimed"] is False
    assert data["compliance_proof_claimed"] is False
    assert data["passport_proof_claimed"] is False
    assert data["runtime_state_mutated"] is False
    assert data["journal_mutated"] is False
    assert data["evidence_mutated"] is False
    assert data["replay_mutated"] is False
    assert data["api_route_added"] is False
    assert data["runtime_command_added"] is False
    assert data["scheduler_added"] is False
    assert data["action_endpoint_added"] is False
    assert data["run_authorized"] is False
    assert data["retry_authorized"] is False
    assert data["repo_read_authorized"] is False
    assert data["github_fetch_authorized"] is False
    assert data["raw_content_ingestion_allowed"] is False
    assert data["private_repo_access_allowed"] is False
    assert data["fake_current_projection_created"] is False


def _fixture(**overrides: object) -> dict[str, object]:
    fixture: dict[str, object] = {
        "request_id": "repo-audit-dry-run-api-surface:test",
        "dry_run_plan_class": "github_repo_source_plan",
        "plan_operation": "project_candidate_sources",
        "plan_status_class": "metadata_only_projection",
        "projection_completeness_class": "bounded_metadata_only",
        "privacy_class": "public_metadata",
        "trust_class": "backend_supplied_metadata",
        "freshness_class": "commit_pinned",
        "namespace": "repo_audit_dry_run_api_surface",
        "source_refs": [{"ref_id": "synthetic:repo"}],
        "provenance": [{"ref_id": "synthetic:dry-run"}],
    }
    fixture.update(overrides)
    return fixture


@pytest.mark.asyncio
async def test_endpoint_returns_honest_no_current_projection_without_source_access() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_PATH)

    assert response.status_code == 200
    data = response.json()
    assert data["projection_result_class"] == "no_projection_available"
    assert data["api_surface_status_class"] == "no_current_dry_run_result"
    assert data["projection_available"] is False
    assert data["current_projection_available"] is False
    assert data["source_current"] is False
    assert data["dry_run_status"] == "repo_audit_dry_run_not_observed"
    assert data["blocked"] is False
    assert "Prior design examples are not replayed as current runtime state." in data["limitations"]
    assert "unreachable" not in str(data).lower()
    assert "source_truth" in data["truthfulness_classification"]
    _assert_read_only_invariants(data)


@pytest.mark.asyncio
async def test_endpoint_has_no_action_run_or_retry_post_surface() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_PATH)

    assert response.status_code == 405


def test_supplied_dry_run_metadata_fixture_remains_metadata_only_candidate() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture()
    )

    assert data["projection_result_class"] == "candidate_sources_available"
    assert data["api_surface_status_class"] == "metadata_candidate_available"
    assert data["candidate_counts"]["included"] == 1
    assert "candidate_only" in data["dry_run_truth_labels"]
    assert data["source_truth_claimed"] is False
    assert data["repo_audit_proof_claimed"] is False
    _assert_read_only_invariants(data)


def test_candidate_source_fixture_is_not_source_truth_or_repo_read() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(
            candidate_sources=[
                {
                    "ref_id": "github:WexyS/Aegis:README",
                    "source_kind": "readme_candidate",
                    "disposition": "include_candidate_metadata_only",
                    "privacy_class": "public_metadata",
                    "trust_class": "github_connector_candidate",
                    "freshness_class": "commit_pinned",
                }
            ]
        )
    )

    assert data["projection_result_class"] == "candidate_sources_available"
    assert data["repo_read_performed"] is False
    assert data["file_read_performed"] is False
    assert data["source_truth_claimed"] is False
    assert data["repo_audit_proof_claimed"] is False


def test_exclusion_fixture_remains_exclusion_metadata_not_cleanup_or_deletion() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(
            candidate_sources=[
                {
                    "ref_id": "candidate:generated-output",
                    "source_kind": "generated_artifact",
                    "disposition": "exclude_generated",
                    "privacy_class": "public_metadata",
                    "trust_class": "backend_supplied_metadata",
                    "freshness_class": "commit_pinned",
                }
            ]
        )
    )

    assert data["projection_result_class"] == "exclusions_available"
    assert data["candidate_counts"]["excluded"] == 1
    assert data["generated_artifact_created"] is False
    assert data["mutation_performed"] is False
    assert data["report_generated"] is False
    _assert_read_only_invariants(data)


def test_blocked_fixture_remains_blocked_without_permission() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(
            privacy_class="secret_like",
            candidate_sources=[
                {
                    "ref_id": "candidate:env",
                    "source_kind": "env_file",
                    "disposition": "exclude_secret_like",
                    "privacy_class": "secret_like",
                    "trust_class": "backend_supplied_metadata",
                    "freshness_class": "commit_pinned",
                }
            ],
        )
    )

    assert data["projection_result_class"] == "blocked_by_policy"
    assert data["api_surface_status_class"] == "blocked_by_policy"
    assert data["blocked"] is True
    assert data["repo_read_authorized"] is False
    assert data["github_fetch_authorized"] is False
    assert "secret_or_credential_candidate_blocked" in data["failure_reasons"]
    _assert_read_only_invariants(data)


def test_future_gated_fixture_remains_future_gated_without_execution() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(
            dry_run_plan_class="local_clone_future_plan",
            plan_status_class="future_gated",
            plan_operation="project_future_execution_gates",
            candidate_sources=[
                {
                    "ref_id": "candidate:local-clone",
                    "source_kind": "local_clone_future",
                    "disposition": "future_gated",
                    "privacy_class": "public_metadata",
                    "trust_class": "backend_supplied_metadata",
                    "freshness_class": "local_snapshot_metadata",
                }
            ],
        )
    )

    assert data["projection_result_class"] == "future_gated"
    assert data["api_surface_status_class"] == "future_gated"
    assert data["future_gated"] is True
    assert data["git_clone_performed"] is False
    assert data["repo_read_authorized"] is False
    _assert_read_only_invariants(data)


def test_operator_review_fixture_requires_review_but_does_not_authorize_run() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(
            plan_status_class="requires_operator_review",
            human_review_required=True,
            candidate_sources=[
                {
                    "ref_id": "candidate:review",
                    "source_kind": "selected_file_candidate",
                    "disposition": "require_operator_review",
                    "privacy_class": "public_metadata",
                    "trust_class": "user_supplied_low_trust",
                    "freshness_class": "branch_floating",
                }
            ],
        )
    )

    assert data["projection_result_class"] == "operator_review_required_candidate"
    assert data["human_review_required"] is True
    assert "operator_review_required" in data["dry_run_truth_labels"]
    assert data["run_authorized"] is False
    assert data["runtime_dispatch_allowed"] is False
    _assert_read_only_invariants(data)


@pytest.mark.parametrize(
    "flag",
    [
        "repo_scan_performed",
        "directory_scan_performed",
        "file_list_performed",
        "file_stat_performed",
        "file_hash_performed",
        "file_read_performed",
        "repo_read_performed",
        "github_api_called",
        "github_url_fetched",
        "browser_fetch_performed",
        "raw_file_fetch_performed",
        "git_clone_performed",
        "http_request_performed",
        "external_api_called",
        "mcp_call_performed",
        "tool_call_performed",
        "model_call_performed",
        "web_query_performed",
        "memory_retrieval_performed",
        "context_retrieval_performed",
        "context_package_created",
        "cache_written",
        "source_record_created",
        "citation_record_created",
        "report_generated",
        "generated_artifact_created",
        "data_sent_external",
        "source_truth_claimed",
        "repo_audit_proof_claimed",
        "compliance_proof_claimed",
        "passport_proof_claimed",
        "runtime_state_mutated",
        "journal_mutated",
        "evidence_mutated",
        "replay_mutated",
        "api_authority",
        "frontend_authority",
        "runtime_dispatch_allowed",
        "approval_grant",
        "capability_grant",
        "lease_grant",
        "verifier_success",
    ],
)
def test_unsafe_fixture_flags_are_blocked_or_absent_and_never_reflected(flag: str) -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata={**_fixture(), flag: True}
    )

    assert data[flag] is False
    if flag not in {"repo_read_performed", "api_authority"}:
        assert data["blocked"] is True
        assert data["api_surface_status_class"] == "blocked_by_policy"
    _assert_read_only_invariants(data)


def test_source_plan_display_candidate_is_not_report_evidence_or_frontend_authority() -> None:
    data = build_repo_audit_dry_run_projection_api_response(
        projection_metadata=_fixture(),
        source_plan_display_decision={
            "display_readiness_status": "display_ready_metadata_only",
            "failure_reasons": (),
            "frontend_authority": False,
            "report_generated": False,
            "evidence_provided_by_display": False,
            "verifier_success": False,
            "execution_permission": "not_granted_by_repo_audit_source_plan_display",
        },
    )

    assert data["projection_result_class"] == "source_plan_display_candidate"
    assert data["report_generated"] is False
    assert data["evidence_provided"] is False
    assert data["frontend_authority"] is False
    _assert_read_only_invariants(data)


def test_api_module_does_not_import_source_access_or_network_clients() -> None:
    source = Path("src/aegis/api/repo_audit_dry_run_projection.py").read_text(encoding="utf-8")

    forbidden_fragments = (
        "httpx",
        "requests",
        "socket.",
        "urllib",
        "subprocess",
        "git clone",
        "os.walk",
        "rglob",
        "glob",
        "open(",
        "Path(",
        "read_text",
        "read_bytes",
        "Authorization",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
