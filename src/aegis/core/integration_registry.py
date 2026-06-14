from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


INTEGRATION_REGISTRY_CONTRACT = "aegis-integration-registry"
INTEGRATION_EXECUTION_PERMISSION = "not_granted_by_integration_registry"

VALID_INTEGRATION_FAMILIES = frozenset(
    {
        "code_workforce",
        "design_studio",
        "flow_engine",
        "model_hub",
        "memory_os",
        "computer_operator",
        "skill_foundry",
        "agent_board",
    }
)

VALID_SOURCE_STRATEGIES = frozenset(
    {
        "native_aegis",
        "clean_room_reimplementation",
        "external_adapter",
        "vendored_with_notice",
        "research_reference_only",
        "blocked_until_license_review",
    }
)

VALID_EXECUTION_STATUSES = frozenset(
    {
        "disabled",
        "discovery_only",
        "dry_run_only",
        "approval_gated_planned",
        "power_mode_planned",
        "yolo_lab_planned",
        "blocked",
    }
)

VALID_MODES = frozenset({"safe", "balanced", "power", "yolo_lab"})


@dataclass(frozen=True)
class IntegrationRecord:
    integration_id: str
    aegis_name: str
    family: str
    aegis_surface: str
    upstream_reference: str
    upstream_url: str
    license_hint: str
    source_strategy: str
    notice_required: bool
    requires_network: bool
    requires_secret: bool
    requires_process_spawn: bool
    requires_filesystem_read: bool
    requires_filesystem_write: bool
    requires_computer_control: bool
    requires_model_gateway: bool
    requires_external_api: bool
    allowed_modes: tuple[str, ...]
    default_execution_status: str
    risk_level: str
    current_status: str
    user_facing_brand: str
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "integration_id": self.integration_id,
            "aegis_name": self.aegis_name,
            "family": self.family,
            "aegis_surface": self.aegis_surface,
            "upstream_reference": self.upstream_reference,
            "upstream_url": self.upstream_url,
            "license_hint": self.license_hint,
            "source_strategy": self.source_strategy,
            "notice_required": self.notice_required,
            "requires_network": self.requires_network,
            "requires_secret": self.requires_secret,
            "requires_process_spawn": self.requires_process_spawn,
            "requires_filesystem_read": self.requires_filesystem_read,
            "requires_filesystem_write": self.requires_filesystem_write,
            "requires_computer_control": self.requires_computer_control,
            "requires_model_gateway": self.requires_model_gateway,
            "requires_external_api": self.requires_external_api,
            "allowed_modes": list(self.allowed_modes),
            "default_execution_status": self.default_execution_status,
            "risk_level": self.risk_level,
            "current_status": self.current_status,
            "user_facing_brand": self.user_facing_brand,
            "notes": list(self.notes),
            "authority": False,
            "runtime_dispatch_allowed": False,
            "execution_permission": INTEGRATION_EXECUTION_PERMISSION,
            "integration_execution_allowed": False,
            "execution_enabled_now": False,
            "installed_status_claimed": False,
            "external_process_launched": False,
            "network_call_performed": False,
            "external_api_called": False,
            "model_call_performed": False,
            "tool_call_performed": False,
            "agent_execution_performed": False,
            "workflow_execution_performed": False,
            "computer_control_performed": False,
            "memory_write_performed": False,
            "evidence_created": False,
            "verifier_success": False,
            "approval_granted": False,
            "capability_lease_granted": False,
            "frontend_authority": False,
        }


def list_integrations() -> list[dict[str, Any]]:
    return [record.to_dict() for record in INTEGRATION_RECORDS]


def get_integration(integration_id: str) -> dict[str, Any] | None:
    requested = str(integration_id or "").strip()
    for record in INTEGRATION_RECORDS:
        if record.integration_id == requested:
            return record.to_dict()
    return None


def list_integrations_by_family(family: str) -> list[dict[str, Any]]:
    requested = str(family or "").strip()
    return [record.to_dict() for record in INTEGRATION_RECORDS if record.family == requested]


def list_integrations_for_mode(mode: str) -> list[dict[str, Any]]:
    requested = str(mode or "").strip()
    return [record.to_dict() for record in INTEGRATION_RECORDS if requested in record.allowed_modes]


def build_integration_landscape() -> dict[str, Any]:
    records = list_integrations()
    family_counts = {family: 0 for family in sorted(VALID_INTEGRATION_FAMILIES)}
    mode_counts = {mode: 0 for mode in sorted(VALID_MODES)}
    for record in INTEGRATION_RECORDS:
        family_counts[record.family] += 1
        for mode in record.allowed_modes:
            mode_counts[mode] += 1
    return {
        "contract": INTEGRATION_REGISTRY_CONTRACT,
        "status": "listed_non_executing",
        "integration_count": len(records),
        "families": sorted(VALID_INTEGRATION_FAMILIES),
        "family_counts": family_counts,
        "modes": sorted(VALID_MODES),
        "mode_counts": mode_counts,
        "source_strategies": sorted(VALID_SOURCE_STRATEGIES),
        "execution_statuses": sorted(VALID_EXECUTION_STATUSES),
        "records": records,
        "execution_enabled_now": False,
        "all_integrations_disabled_from_execution": True,
        "third_party_code_vendored": False,
        "external_repos_cloned": False,
        "license_review_required_before_vendoring": True,
        "user_facing_brand_policy": "Aegis",
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": INTEGRATION_EXECUTION_PERMISSION,
        "evidence_created": False,
        "verifier_success": False,
        "approval_granted": False,
        "capability_lease_granted": False,
    }


def integration_allows_execution(record: IntegrationRecord | Mapping[str, Any]) -> bool:
    data = record.to_dict() if isinstance(record, IntegrationRecord) else dict(record)
    if data.get("runtime_dispatch_allowed") is True:
        return True
    if data.get("integration_execution_allowed") is True or data.get("execution_enabled_now") is True:
        return True
    if data.get("default_execution_status") not in VALID_EXECUTION_STATUSES:
        return False
    return False


def _record(
    *,
    integration_id: str,
    aegis_name: str,
    family: str,
    aegis_surface: str,
    upstream_reference: str,
    upstream_url: str,
    source_strategy: str,
    default_execution_status: str,
    allowed_modes: tuple[str, ...],
    risk_level: str,
    requires_network: bool = False,
    requires_secret: bool = False,
    requires_process_spawn: bool = False,
    requires_filesystem_read: bool = False,
    requires_filesystem_write: bool = False,
    requires_computer_control: bool = False,
    requires_model_gateway: bool = False,
    requires_external_api: bool = False,
    notice_required: bool = True,
    notes: tuple[str, ...] = (),
) -> IntegrationRecord:
    return IntegrationRecord(
        integration_id=integration_id,
        aegis_name=aegis_name,
        family=family,
        aegis_surface=aegis_surface,
        upstream_reference=upstream_reference,
        upstream_url=upstream_url,
        license_hint="unknown_pending_review",
        source_strategy=source_strategy,
        notice_required=notice_required,
        requires_network=requires_network,
        requires_secret=requires_secret,
        requires_process_spawn=requires_process_spawn,
        requires_filesystem_read=requires_filesystem_read,
        requires_filesystem_write=requires_filesystem_write,
        requires_computer_control=requires_computer_control,
        requires_model_gateway=requires_model_gateway,
        requires_external_api=requires_external_api,
        allowed_modes=allowed_modes,
        default_execution_status=default_execution_status,
        risk_level=risk_level,
        current_status="planned_disabled_non_executing",
        user_facing_brand="Aegis",
        notes=(
            "architecture_record_only",
            "not_installed_or_executable_by_registry",
            "upstream_traceability_preserved",
            *notes,
        ),
    )


INTEGRATION_RECORDS: tuple[IntegrationRecord, ...] = (
    _record(
        integration_id="open_design",
        aegis_name="Aegis Design Studio",
        family="design_studio",
        aegis_surface="Aegis Design Studio",
        upstream_reference="Open Design",
        upstream_url="https://github.com/nexu-io/open-design",
        source_strategy="clean_room_reimplementation",
        default_execution_status="discovery_only",
        allowed_modes=("safe", "balanced", "power"),
        risk_level="medium",
        notes=("design_patterns_require_license_review_before_reuse",),
    ),
    _record(
        integration_id="awesome_claude_code",
        aegis_name="Aegis Skill Foundry",
        family="skill_foundry",
        aegis_surface="Aegis Skill Foundry",
        upstream_reference="awesome-claude-code",
        upstream_url="https://github.com/hesreallyhim/awesome-claude-code",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("safe", "balanced"),
        risk_level="low",
        notes=("curated_reference_only_not_imported",),
    ),
    _record(
        integration_id="html_anything",
        aegis_name="Aegis Design Studio",
        family="design_studio",
        aegis_surface="Aegis Design Studio",
        upstream_reference="html-anything",
        upstream_url="https://github.com/nexu-io/html-anything",
        source_strategy="clean_room_reimplementation",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="opencode",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="OpenCode",
        upstream_url="https://github.com/anomalyco/opencode",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="cline",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Cline",
        upstream_url="https://github.com/cline/cline",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
        requires_external_api=True,
    ),
    _record(
        integration_id="aider",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Aider",
        upstream_url="https://github.com/Aider-AI/aider",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="kilo_code",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Kilo Code",
        upstream_url="https://github.com/kilo-org/kilocode",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="codex_cli",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Codex CLI",
        upstream_url="https://github.com/openai/codex",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_external_api=True,
        requires_secret=True,
    ),
    _record(
        integration_id="gemini_cli",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Gemini CLI",
        upstream_url="https://github.com/google-gemini/gemini-cli",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_external_api=True,
        requires_secret=True,
    ),
    _record(
        integration_id="goose",
        aegis_name="Aegis Agent Board",
        family="agent_board",
        aegis_surface="Aegis Agent Board",
        upstream_reference="Goose",
        upstream_url="https://github.com/aaif-goose/goose",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="n8n",
        aegis_name="Aegis Flow Engine",
        family="flow_engine",
        aegis_surface="Aegis Flow Engine",
        upstream_reference="n8n",
        upstream_url="https://github.com/n8n-io/n8n",
        source_strategy="external_adapter",
        default_execution_status="approval_gated_planned",
        allowed_modes=("balanced", "power", "yolo_lab"),
        risk_level="high",
        requires_network=True,
        requires_secret=True,
        requires_process_spawn=True,
        requires_external_api=True,
    ),
    _record(
        integration_id="ollama",
        aegis_name="Aegis Model Hub",
        family="model_hub",
        aegis_surface="Aegis Model Hub",
        upstream_reference="Ollama",
        upstream_url="https://github.com/ollama/ollama",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("safe", "balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="langflow",
        aegis_name="Aegis Flow Engine",
        family="flow_engine",
        aegis_surface="Aegis Flow Engine",
        upstream_reference="Langflow",
        upstream_url="https://github.com/langflow-ai/langflow",
        source_strategy="external_adapter",
        default_execution_status="dry_run_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_network=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="dify",
        aegis_name="Aegis Flow Engine",
        family="flow_engine",
        aegis_surface="Aegis Flow Engine",
        upstream_reference="Dify",
        upstream_url="https://github.com/langgenius/dify",
        source_strategy="external_adapter",
        default_execution_status="dry_run_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_network=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="open_webui",
        aegis_name="Aegis Model Hub",
        family="model_hub",
        aegis_surface="Aegis Model Hub",
        upstream_reference="Open WebUI",
        upstream_url="https://github.com/open-webui/open-webui",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="cua",
        aegis_name="Aegis Computer Operator",
        family="computer_operator",
        aegis_surface="Aegis Computer Operator",
        upstream_reference="CUA",
        upstream_url="https://github.com/trycua/cua",
        source_strategy="external_adapter",
        default_execution_status="yolo_lab_planned",
        allowed_modes=("yolo_lab",),
        risk_level="critical_future",
        requires_process_spawn=True,
        requires_computer_control=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="anything_llm",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="AnythingLLM",
        upstream_url="https://github.com/mintplex-labs/anything-llm",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="multica",
        aegis_name="Aegis Design Studio",
        family="design_studio",
        aegis_surface="Aegis Design Studio",
        upstream_reference="Multica",
        upstream_url="https://github.com/multica-ai/multica",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
    ),
    _record(
        integration_id="qwenpaw",
        aegis_name="Aegis Agent Board",
        family="agent_board",
        aegis_surface="Aegis Agent Board",
        upstream_reference="QwenPaw",
        upstream_url="https://github.com/agentscope-ai/QwenPaw",
        source_strategy="external_adapter",
        default_execution_status="dry_run_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="mem0",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="Mem0",
        upstream_url="https://github.com/mem0ai/mem0",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="graphiti",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="Graphiti",
        upstream_url="https://github.com/getzep/graphiti",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="cognee",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="Cognee",
        upstream_url="https://github.com/topoteretes/cognee",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="graphrag",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="GraphRAG",
        upstream_url="https://github.com/microsoft/graphrag",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="lightrag",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="LightRAG",
        upstream_url="https://github.com/HKUDS/LightRAG",
        source_strategy="research_reference_only",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
    ),
    _record(
        integration_id="ragflow",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="RAGFlow",
        upstream_url="https://github.com/infiniflow/ragflow",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="khoj",
        aegis_name="Aegis Memory OS",
        family="memory_os",
        aegis_surface="Aegis Memory OS",
        upstream_reference="Khoj",
        upstream_url="https://github.com/khoj-ai/khoj",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("balanced", "power"),
        risk_level="medium",
        requires_process_spawn=True,
        requires_model_gateway=True,
    ),
    _record(
        integration_id="lm_studio",
        aegis_name="Aegis Model Hub",
        family="model_hub",
        aegis_surface="Aegis Model Hub",
        upstream_reference="LM Studio local OpenAI-compatible endpoint",
        upstream_url="https://lmstudio.ai",
        source_strategy="external_adapter",
        default_execution_status="discovery_only",
        allowed_modes=("safe", "balanced", "power"),
        risk_level="medium",
        requires_model_gateway=True,
        notes=("existing_model_gateway_is_the_only_allowed_future_call_boundary",),
    ),
    _record(
        integration_id="openrouter",
        aegis_name="Aegis Model Hub",
        family="model_hub",
        aegis_surface="Aegis Model Hub",
        upstream_reference="OpenRouter",
        upstream_url="https://openrouter.ai",
        source_strategy="external_adapter",
        default_execution_status="blocked",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_network=True,
        requires_secret=True,
        requires_external_api=True,
        notes=("cloud_or_external_model_routing_not_allowed_by_current_readiness",),
    ),
    _record(
        integration_id="deepseek",
        aegis_name="Aegis Model Hub",
        family="model_hub",
        aegis_surface="Aegis Model Hub",
        upstream_reference="DeepSeek",
        upstream_url="https://www.deepseek.com",
        source_strategy="external_adapter",
        default_execution_status="blocked",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_network=True,
        requires_secret=True,
        requires_external_api=True,
        notes=("cloud_or_external_model_routing_not_allowed_by_current_readiness",),
    ),
    _record(
        integration_id="cursor_composer",
        aegis_name="Aegis Code Workforce",
        family="code_workforce",
        aegis_surface="Aegis Code Workforce",
        upstream_reference="Cursor Composer",
        upstream_url="https://cursor.com",
        source_strategy="external_adapter",
        default_execution_status="blocked",
        allowed_modes=("power", "yolo_lab"),
        risk_level="high",
        requires_process_spawn=True,
        requires_filesystem_read=True,
        requires_filesystem_write=True,
        requires_network=True,
        requires_secret=True,
        requires_external_api=True,
    ),
)
