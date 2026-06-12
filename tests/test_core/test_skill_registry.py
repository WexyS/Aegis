from __future__ import annotations

import pytest

from aegis.core.skill_registry import (
    SKILL_REGISTRY_EXECUTION_PERMISSION,
    VALID_EXECUTION_MODES,
    VALID_RISK_CLASSES,
    build_skill_catalog,
    get_skill_manifest,
    list_skill_manifests,
    validate_skill_manifest,
)


EXPECTED_SKILLS = {
    "repo_structure_audit",
    "memory_candidate_review",
    "society_review",
    "report_summarization",
    "context_package_review",
    "model_assisted_explanation",
    "higgsfield_mcp_media_generation",
    "ecc_repo_scan_review",
    "ecc_article_writing_reference",
    "ecc_security_config_review",
    "ecc_github_ops_reference",
}

EXTERNAL_CANDIDATES = {
    "higgsfield_mcp_media_generation",
    "ecc_repo_scan_review",
    "ecc_article_writing_reference",
    "ecc_security_config_review",
    "ecc_github_ops_reference",
}

REQUIRED_FIELDS = {
    "skill_id",
    "name",
    "version",
    "description",
    "category",
    "status",
    "risk_class",
    "execution_mode",
    "input_contract",
    "output_contract",
    "required_capabilities",
    "allowed_scopes",
    "requires_model",
    "requires_network",
    "requires_mcp",
    "requires_shell",
    "requires_credentials",
    "can_mutate_files",
    "can_write_memory",
    "external_source",
    "limitations",
    "non_authority_flags",
}

NON_AUTHORITY_FALSE_FIELDS = {
    "authority",
    "permission_granted",
    "approval_granted",
    "capability_lease_granted",
    "evidence_created",
    "verifier_success",
    "runtime_dispatch_allowed",
    "memory_write_performed",
    "model_call_performed",
    "mcp_call_performed",
    "tool_call_performed",
    "shell_command_performed",
    "file_mutation_performed",
}


def _assert_registry_non_execution(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["permission_granted"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["evidence_created"] is False
    assert data["verifier_success"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == SKILL_REGISTRY_EXECUTION_PERMISSION
    assert data["skill_execution_performed"] is False
    assert data["memory_write_performed"] is False
    assert data["model_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["network_call_performed"] is False
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False


def test_registry_lists_built_in_skills() -> None:
    catalog = build_skill_catalog()

    assert catalog["status"] == "listed"
    assert catalog["skill_count"] == 11
    assert {skill["skill_id"] for skill in catalog["skills"]} == EXPECTED_SKILLS
    assert catalog["skill_execution_allowed"] is False
    assert catalog["no_execution_endpoint"] is True
    _assert_registry_non_execution(catalog)


def test_each_built_in_skill_has_required_fields_and_valid_taxonomy() -> None:
    for manifest in list_skill_manifests():
        assert REQUIRED_FIELDS <= set(manifest)
        assert manifest["risk_class"] in VALID_RISK_CLASSES
        assert manifest["execution_mode"] in VALID_EXECUTION_MODES
        assert manifest["execution_mode"] != "executable"
        assert manifest["status"] in {"available", "disabled", "future_gated", "candidate", "blocked"}
        assert manifest["external_source"]
        assert manifest["required_capabilities"]
        assert manifest["allowed_scopes"]

        non_authority = manifest["non_authority_flags"]
        assert NON_AUTHORITY_FALSE_FIELDS <= set(non_authority)
        for field_name in NON_AUTHORITY_FALSE_FIELDS:
            assert non_authority[field_name] is False


def test_all_built_in_manifests_validate_as_metadata_only() -> None:
    for manifest in list_skill_manifests():
        result = validate_skill_manifest(manifest)

        assert result["status"] == "valid"
        assert result["failure_reasons"] == ()
        assert result["manifest"] == manifest
        _assert_registry_non_execution(result)


def test_repo_structure_audit_exists_but_is_not_executed_by_registry() -> None:
    manifest = get_skill_manifest("repo_structure_audit")

    assert manifest is not None
    assert manifest["skill_id"] == "repo_structure_audit"
    assert manifest["risk_class"] == "local_read_only"
    assert manifest["execution_mode"] == "read_only_planned"
    assert manifest["input_contract"]["registry_execution"] == "not_supported"
    assert "registry_does_not_run_autopilot" in manifest["limitations"]


@pytest.mark.parametrize("skill_id", ["report_summarization", "model_assisted_explanation"])
def test_model_required_skills_do_not_call_model_gateway(skill_id: str) -> None:
    manifest = get_skill_manifest(skill_id)

    assert manifest is not None
    assert manifest["requires_model"] is True
    assert manifest["risk_class"] == "local_model_required"
    assert manifest["execution_mode"] == "model_assisted_planned"
    assert manifest["non_authority_flags"]["model_call_performed"] is False
    assert "registry_does_not_call_model_gateway" in manifest["limitations"]


def test_external_network_mcp_shell_and_mutation_flags_are_false_for_builtins() -> None:
    for manifest in [item for item in list_skill_manifests() if item["external_source"] == "aegis_builtin"]:
        assert manifest["requires_network"] is False
        assert manifest["requires_mcp"] is False
        assert manifest["requires_shell"] is False
        assert manifest["requires_credentials"] is False
        assert manifest["can_mutate_files"] is False
        assert manifest["can_write_memory"] is False


def test_invalid_manifest_blocks() -> None:
    manifest = dict(get_skill_manifest("repo_structure_audit") or {})
    manifest["risk_class"] = "unknown_future_risk"

    result = validate_skill_manifest(manifest)

    assert result["status"] == "blocked"
    assert "invalid_risk_class" in result["failure_reasons"]
    assert result["manifest"] is None
    _assert_registry_non_execution(result)


def test_manifest_permission_claim_blocks() -> None:
    manifest = dict(get_skill_manifest("repo_structure_audit") or {})
    non_authority = dict(manifest["non_authority_flags"])
    non_authority["permission_granted"] = True
    manifest["non_authority_flags"] = non_authority

    result = validate_skill_manifest(manifest)

    assert result["status"] == "blocked"
    assert "non_authority_permission_granted_must_be_false" in result["failure_reasons"]
    _assert_registry_non_execution(result)


def test_side_effect_requirements_must_be_future_gated() -> None:
    manifest = dict(get_skill_manifest("repo_structure_audit") or {})
    manifest["requires_shell"] = True

    result = validate_skill_manifest(manifest)

    assert result["status"] == "blocked"
    assert "side_effect_requirements_must_be_future_gated" in result["failure_reasons"]
    assert "shell_requirement" not in " ".join(result["failure_reasons"])


def test_candidate_external_schema_can_be_represented_without_execution() -> None:
    manifest = dict(get_skill_manifest("repo_structure_audit") or {})
    manifest.update(
        {
            "skill_id": "ecc_candidate_reference",
            "name": "ECC Candidate Reference",
            "status": "candidate",
            "risk_class": "mcp_required",
            "execution_mode": "external_candidate",
            "requires_mcp": True,
            "external_source": "external_candidate_reference_only",
        }
    )

    result = validate_skill_manifest(manifest)

    assert result["status"] == "valid"
    assert result["manifest"]["requires_mcp"] is True
    assert result["model_call_performed"] is False
    assert result["mcp_call_performed"] is False
    assert result["tool_call_performed"] is False


def test_higgsfield_candidate_exists_and_is_future_gated_non_executable() -> None:
    manifest = get_skill_manifest("higgsfield_mcp_media_generation")

    assert manifest is not None
    assert manifest["category"] == "external_mcp"
    assert manifest["status"] == "future_gated"
    assert manifest["risk_class"] == "high_risk_external"
    assert manifest["execution_mode"] == "external_candidate"
    assert manifest["requires_network"] is True
    assert manifest["requires_mcp"] is True
    assert manifest["requires_credentials"] is True
    assert manifest["can_mutate_files"] is False
    assert manifest["can_write_memory"] is False
    assert manifest["input_contract"]["candidate_source_url"] == "https://mcp.higgsfield.ai/mcp"
    assert "no_media_generation" in manifest["limitations"]
    assert "no_credit_or_quota_spending" in manifest["limitations"]
    for field_name in NON_AUTHORITY_FALSE_FIELDS:
        assert manifest["non_authority_flags"][field_name] is False


def test_ecc_candidate_entries_exist_and_are_not_executable() -> None:
    for skill_id in EXTERNAL_CANDIDATES - {"higgsfield_mcp_media_generation"}:
        manifest = get_skill_manifest(skill_id)

        assert manifest is not None
        assert manifest["category"] == "external_skill_reference"
        assert manifest["status"] in {"candidate", "future_gated"}
        assert manifest["execution_mode"] in {"external_candidate", "future_policy_gated"}
        assert manifest["external_source"] == "ecc_candidate_reference"
        assert manifest["input_contract"]["candidate_source_url"] == "https://github.com/affaan-m/ecc"
        assert manifest["requires_shell"] is False
        assert manifest["requires_mcp"] is False
        assert manifest["can_write_memory"] is False
        assert manifest["non_authority_flags"]["runtime_dispatch_allowed"] is False
        assert manifest["non_authority_flags"]["evidence_created"] is False
        assert manifest["non_authority_flags"]["verifier_success"] is False


def test_ecc_github_ops_candidate_is_network_credential_and_future_gated() -> None:
    manifest = get_skill_manifest("ecc_github_ops_reference")

    assert manifest is not None
    assert manifest["status"] == "future_gated"
    assert manifest["risk_class"] == "high_risk_external"
    assert manifest["execution_mode"] == "future_policy_gated"
    assert manifest["requires_network"] is True
    assert manifest["requires_credentials"] is True
    assert manifest["can_mutate_files"] is False
    assert "mutation_policy_gate" in manifest["required_capabilities"]
    assert "capability_lease_required_future" in manifest["required_capabilities"]
    assert "no_github_api_call" in manifest["limitations"]
    assert "no_github_mutation" in manifest["limitations"]


def test_ecc_repo_scan_candidate_is_not_a_repo_scan() -> None:
    manifest = get_skill_manifest("ecc_repo_scan_review")

    assert manifest is not None
    assert manifest["execution_mode"] == "external_candidate"
    assert manifest["requires_network"] is False
    assert manifest["requires_shell"] is False
    assert manifest["can_mutate_files"] is False
    assert "repo_read_only_context" in manifest["required_capabilities"]
    assert "no_repo_scan_performed_by_skill_registry" in manifest["limitations"]


def test_external_candidates_validate_without_performing_side_effects() -> None:
    for skill_id in EXTERNAL_CANDIDATES:
        manifest = get_skill_manifest(skill_id)
        assert manifest is not None

        result = validate_skill_manifest(manifest)

        assert result["status"] == "valid"
        assert result["failure_reasons"] == ()
        _assert_registry_non_execution(result)
