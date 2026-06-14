from __future__ import annotations

from aegis.core.integration_registry import (
    VALID_EXECUTION_STATUSES,
    VALID_INTEGRATION_FAMILIES,
    VALID_MODES,
    VALID_SOURCE_STRATEGIES,
    build_integration_landscape,
    get_integration,
    integration_allows_execution,
    list_integrations,
    list_integrations_by_family,
    list_integrations_for_mode,
)


REQUIRED_URLS = {
    "https://github.com/nexu-io/open-design",
    "https://github.com/hesreallyhim/awesome-claude-code",
    "https://github.com/nexu-io/html-anything",
    "https://github.com/anomalyco/opencode",
    "https://github.com/cline/cline",
    "https://github.com/Aider-AI/aider",
    "https://github.com/kilo-org/kilocode",
    "https://github.com/openai/codex",
    "https://github.com/google-gemini/gemini-cli",
    "https://github.com/aaif-goose/goose",
    "https://github.com/n8n-io/n8n",
    "https://github.com/ollama/ollama",
    "https://github.com/langflow-ai/langflow",
    "https://github.com/langgenius/dify",
    "https://github.com/open-webui/open-webui",
    "https://github.com/trycua/cua",
    "https://github.com/mintplex-labs/anything-llm",
    "https://github.com/multica-ai/multica",
    "https://github.com/agentscope-ai/QwenPaw",
    "https://github.com/mem0ai/mem0",
    "https://github.com/getzep/graphiti",
    "https://github.com/topoteretes/cognee",
    "https://github.com/microsoft/graphrag",
    "https://github.com/HKUDS/LightRAG",
    "https://github.com/infiniflow/ragflow",
    "https://github.com/khoj-ai/khoj",
}


PLANNED_TARGET_IDS = {"lm_studio", "openrouter", "deepseek", "cursor_composer"}


def test_integration_ids_are_unique() -> None:
    integrations = list_integrations()
    ids = [record["integration_id"] for record in integrations]

    assert len(ids) == len(set(ids))


def test_records_preserve_aegis_branding_and_upstream_traceability() -> None:
    for record in list_integrations():
        assert str(record["aegis_name"]).startswith("Aegis")
        assert record["user_facing_brand"] == "Aegis"
        assert record["upstream_reference"]
        assert record["upstream_url"]
        assert record["license_hint"] == "unknown_pending_review"
        assert record["notice_required"] is True
        assert record["installed_status_claimed"] is False


def test_records_have_known_taxonomy_values() -> None:
    for record in list_integrations():
        assert record["family"] in VALID_INTEGRATION_FAMILIES
        assert record["source_strategy"] in VALID_SOURCE_STRATEGIES
        assert record["default_execution_status"] in VALID_EXECUTION_STATUSES
        assert record["allowed_modes"]
        assert set(record["allowed_modes"]) <= VALID_MODES


def test_no_integration_allows_execution_now() -> None:
    for record in list_integrations():
        assert integration_allows_execution(record) is False
        assert record["runtime_dispatch_allowed"] is False
        assert record["integration_execution_allowed"] is False
        assert record["execution_enabled_now"] is False
        assert record["external_process_launched"] is False
        assert record["network_call_performed"] is False
        assert record["external_api_called"] is False
        assert record["model_call_performed"] is False
        assert record["tool_call_performed"] is False
        assert record["agent_execution_performed"] is False
        assert record["workflow_execution_performed"] is False
        assert record["computer_control_performed"] is False
        assert record["memory_write_performed"] is False
        assert record["evidence_created"] is False
        assert record["verifier_success"] is False
        assert record["approval_granted"] is False
        assert record["capability_lease_granted"] is False


def test_records_requiring_risky_resources_are_not_executable() -> None:
    risk_fields = {
        "requires_network",
        "requires_secret",
        "requires_process_spawn",
        "requires_filesystem_read",
        "requires_filesystem_write",
        "requires_computer_control",
        "requires_model_gateway",
        "requires_external_api",
    }
    risky = [record for record in list_integrations() if any(record[field] is True for field in risk_fields)]

    assert risky
    for record in risky:
        assert integration_allows_execution(record) is False
        assert record["execution_enabled_now"] is False


def test_required_project_urls_are_represented() -> None:
    urls = {record["upstream_url"] for record in list_integrations()}

    assert REQUIRED_URLS <= urls


def test_non_github_provider_targets_are_represented_without_execution() -> None:
    for integration_id in PLANNED_TARGET_IDS:
        record = get_integration(integration_id)

        assert record is not None
        assert record["family"] in {"model_hub", "code_workforce"}
        assert integration_allows_execution(record) is False
        assert record["installed_status_claimed"] is False


def test_landscape_returns_all_families_and_modes() -> None:
    landscape = build_integration_landscape()

    assert landscape["status"] == "listed_non_executing"
    assert set(landscape["families"]) == VALID_INTEGRATION_FAMILIES
    assert set(landscape["modes"]) == VALID_MODES
    assert set(landscape["family_counts"]) == VALID_INTEGRATION_FAMILIES
    assert all(count > 0 for count in landscape["family_counts"].values())
    assert landscape["integration_count"] == len(list_integrations())
    assert landscape["all_integrations_disabled_from_execution"] is True
    assert landscape["third_party_code_vendored"] is False
    assert landscape["external_repos_cloned"] is False
    assert landscape["runtime_dispatch_allowed"] is False


def test_family_and_mode_helpers_are_bounded_filters() -> None:
    code_records = list_integrations_by_family("code_workforce")
    safe_records = list_integrations_for_mode("safe")

    assert code_records
    assert all(record["family"] == "code_workforce" for record in code_records)
    assert safe_records
    assert all("safe" in record["allowed_modes"] for record in safe_records)
