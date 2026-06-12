from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


SKILL_REGISTRY_RC1_VERSION = "skill-registry-rc1/1"
SKILL_REGISTRY_EXECUTION_PERMISSION = "not_granted_by_skill_registry"

VALID_SKILL_STATUSES = frozenset({"available", "disabled", "future_gated", "candidate", "blocked"})
VALID_RISK_CLASSES = frozenset(
    {
        "local_read_only",
        "local_model_required",
        "external_network_required",
        "mcp_required",
        "credential_required",
        "mutation_capable",
        "high_risk_external",
        "unknown_risk",
    }
)
VALID_EXECUTION_MODES = frozenset(
    {
        "metadata_only",
        "read_only_planned",
        "model_assisted_planned",
        "external_candidate",
        "future_policy_gated",
    }
)

REQUIRED_MANIFEST_FIELDS = (
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
)

BOOLEAN_FIELDS = (
    "requires_model",
    "requires_network",
    "requires_mcp",
    "requires_shell",
    "requires_credentials",
    "can_mutate_files",
    "can_write_memory",
)

SIDE_EFFECT_REQUIREMENT_FIELDS = (
    "requires_network",
    "requires_mcp",
    "requires_shell",
    "requires_credentials",
    "can_mutate_files",
    "can_write_memory",
)

NON_AUTHORITY_FALSE_FIELDS = (
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
)

WILDCARD_VALUES = {"*", "all", "any", "unbounded", "wildcard"}


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    name: str
    version: str
    description: str
    category: str
    status: str
    risk_class: str
    execution_mode: str
    input_contract: Mapping[str, Any]
    output_contract: Mapping[str, Any]
    required_capabilities: tuple[str, ...]
    allowed_scopes: tuple[str, ...]
    requires_model: bool = False
    requires_network: bool = False
    requires_mcp: bool = False
    requires_shell: bool = False
    requires_credentials: bool = False
    can_mutate_files: bool = False
    can_write_memory: bool = False
    external_source: str = "aegis_builtin"
    limitations: tuple[str, ...] = ()
    non_authority_flags: Mapping[str, bool] = field(default_factory=lambda: _non_authority_flags())

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "risk_class": self.risk_class,
            "execution_mode": self.execution_mode,
            "input_contract": dict(self.input_contract),
            "output_contract": dict(self.output_contract),
            "required_capabilities": list(self.required_capabilities),
            "allowed_scopes": list(self.allowed_scopes),
            "requires_model": self.requires_model,
            "requires_network": self.requires_network,
            "requires_mcp": self.requires_mcp,
            "requires_shell": self.requires_shell,
            "requires_credentials": self.requires_credentials,
            "can_mutate_files": self.can_mutate_files,
            "can_write_memory": self.can_write_memory,
            "external_source": self.external_source,
            "limitations": list(self.limitations),
            "non_authority_flags": dict(self.non_authority_flags),
        }


def list_skill_manifests() -> list[dict[str, Any]]:
    return [manifest.to_dict() for manifest in BUILTIN_SKILL_MANIFESTS]


def get_skill_manifest(skill_id: str) -> dict[str, Any] | None:
    requested = str(skill_id or "").strip()
    for manifest in BUILTIN_SKILL_MANIFESTS:
        if manifest.skill_id == requested:
            return manifest.to_dict()
    return None


def build_skill_catalog() -> dict[str, Any]:
    skills = list_skill_manifests()
    categories = sorted({skill["category"] for skill in skills})
    return {
        "skill_registry_version": SKILL_REGISTRY_RC1_VERSION,
        "status": "listed",
        "skill_count": len(skills),
        "skills": skills,
        "categories": categories,
        "risk_classes": sorted(VALID_RISK_CLASSES),
        "execution_modes": sorted(VALID_EXECUTION_MODES),
        "catalog_source": "aegis_static_catalog_with_external_candidates",
        "catalog_persistence": "code_defined_static_catalog",
        "catalog_mutation_allowed": False,
        "skill_execution_allowed": False,
        "no_execution_endpoint": True,
        **_registry_non_execution_flags(),
    }


def validate_skill_manifest(manifest: SkillManifest | Mapping[str, Any]) -> dict[str, Any]:
    data = manifest.to_dict() if isinstance(manifest, SkillManifest) else dict(manifest)
    failures: list[str] = []

    for field_name in REQUIRED_MANIFEST_FIELDS:
        if field_name not in data:
            failures.append(f"missing_{field_name}")

    for field_name in ("skill_id", "name", "version", "description", "category", "external_source"):
        if field_name in data and not _nonempty_text(data.get(field_name)):
            failures.append(f"empty_{field_name}")

    status = str(data.get("status") or "")
    risk_class = str(data.get("risk_class") or "")
    execution_mode = str(data.get("execution_mode") or "")
    if status and status not in VALID_SKILL_STATUSES:
        failures.append("invalid_status")
    if risk_class and risk_class not in VALID_RISK_CLASSES:
        failures.append("invalid_risk_class")
    if execution_mode and execution_mode not in VALID_EXECUTION_MODES:
        failures.append("invalid_execution_mode")

    if "input_contract" in data and not isinstance(data.get("input_contract"), Mapping):
        failures.append("invalid_input_contract")
    if "output_contract" in data and not isinstance(data.get("output_contract"), Mapping):
        failures.append("invalid_output_contract")

    for field_name in ("required_capabilities", "allowed_scopes", "limitations"):
        if field_name in data and not _string_sequence(data.get(field_name)):
            failures.append(f"invalid_{field_name}")

    for field_name in BOOLEAN_FIELDS:
        if field_name in data and not isinstance(data.get(field_name), bool):
            failures.append(f"invalid_{field_name}")

    capabilities = set(_sequence_values(data.get("required_capabilities")))
    scopes = set(_sequence_values(data.get("allowed_scopes")))
    if capabilities & WILDCARD_VALUES:
        failures.append("wildcard_capability_denied")
    if scopes & WILDCARD_VALUES:
        failures.append("wildcard_scope_denied")

    non_authority = data.get("non_authority_flags")
    if not isinstance(non_authority, Mapping):
        failures.append("invalid_non_authority_flags")
    else:
        for field_name in NON_AUTHORITY_FALSE_FIELDS:
            if field_name not in non_authority:
                failures.append(f"missing_non_authority_{field_name}")
            elif non_authority.get(field_name) is not False:
                failures.append(f"non_authority_{field_name}_must_be_false")

    side_effect_requirements = [field_name for field_name in SIDE_EFFECT_REQUIREMENT_FIELDS if data.get(field_name) is True]
    if side_effect_requirements:
        explicitly_future_gated = status in {"candidate", "future_gated", "blocked"} and execution_mode in {
            "external_candidate",
            "future_policy_gated",
        }
        if not explicitly_future_gated:
            failures.append("side_effect_requirements_must_be_future_gated")

    if data.get("requires_model") is True and risk_class not in {"local_model_required", "unknown_risk"}:
        failures.append("model_requirement_requires_model_risk_class")
    if data.get("requires_mcp") is True and risk_class not in {"mcp_required", "high_risk_external", "unknown_risk"}:
        failures.append("mcp_requirement_requires_mcp_risk_class")
    if data.get("requires_network") is True and risk_class not in {
        "external_network_required",
        "high_risk_external",
        "unknown_risk",
    }:
        failures.append("network_requirement_requires_external_risk_class")
    if data.get("requires_credentials") is True and risk_class not in {
        "credential_required",
        "high_risk_external",
        "unknown_risk",
    }:
        failures.append("credential_requirement_requires_credential_risk_class")
    if (data.get("can_mutate_files") is True or data.get("can_write_memory") is True) and risk_class != "mutation_capable":
        failures.append("mutation_requirement_requires_mutation_risk_class")

    status_result = "valid" if not failures else "blocked"
    return {
        "skill_registry_version": SKILL_REGISTRY_RC1_VERSION,
        "status": status_result,
        "skill_id": str(data.get("skill_id") or ""),
        "failure_reasons": tuple(dict.fromkeys(failures)),
        "manifest": data if status_result == "valid" else None,
        "validation_scope": "metadata_only_manifest_validation",
        **_registry_non_execution_flags(),
    }


def _non_authority_flags() -> dict[str, bool]:
    return {field_name: False for field_name in NON_AUTHORITY_FALSE_FIELDS}


def _registry_non_execution_flags() -> dict[str, Any]:
    return {
        "authority": False,
        "permission_granted": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_created": False,
        "verifier_success": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": SKILL_REGISTRY_EXECUTION_PERMISSION,
        "skill_execution_performed": False,
        "memory_write_performed": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "network_call_performed": False,
        "external_api_called": False,
        "data_sent_external": False,
    }


def _manifest(
    *,
    skill_id: str,
    name: str,
    description: str,
    category: str,
    risk_class: str,
    execution_mode: str,
    input_contract: Mapping[str, Any],
    output_contract: Mapping[str, Any],
    required_capabilities: Sequence[str],
    allowed_scopes: Sequence[str],
    requires_model: bool = False,
    requires_network: bool = False,
    requires_mcp: bool = False,
    requires_shell: bool = False,
    requires_credentials: bool = False,
    can_mutate_files: bool = False,
    can_write_memory: bool = False,
    external_source: str = "aegis_builtin",
    status: str = "available",
    limitations: Sequence[str] = (),
) -> SkillManifest:
    return SkillManifest(
        skill_id=skill_id,
        name=name,
        version="rc1",
        description=description,
        category=category,
        status=status,
        risk_class=risk_class,
        execution_mode=execution_mode,
        input_contract=input_contract,
        output_contract=output_contract,
        required_capabilities=tuple(required_capabilities),
        allowed_scopes=tuple(allowed_scopes),
        requires_model=requires_model,
        requires_network=requires_network,
        requires_mcp=requires_mcp,
        requires_shell=requires_shell,
        requires_credentials=requires_credentials,
        can_mutate_files=can_mutate_files,
        can_write_memory=can_write_memory,
        external_source=external_source,
        limitations=tuple(limitations),
    )


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_sequence(value: Any) -> bool:
    if isinstance(value, str) or not isinstance(value, Sequence):
        return False
    return all(isinstance(item, str) and bool(item.strip()) for item in value)


def _sequence_values(value: Any) -> tuple[str, ...]:
    if not _string_sequence(value):
        return ()
    return tuple(str(item).strip().lower() for item in value)


BUILTIN_SKILL_MANIFESTS: tuple[SkillManifest, ...] = (
    _manifest(
        skill_id="repo_structure_audit",
        name="Repo Structure Audit",
        description="Catalog metadata for the existing read-only AutoPilot repo structure audit.",
        category="autopilot",
        risk_class="local_read_only",
        execution_mode="read_only_planned",
        input_contract={
            "expected_inputs": ["root_path", "include_dirs", "exclude_dirs"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["metadata_report_candidate"],
            "evidence": "not_created_by_skill_registry",
        },
        required_capabilities=("repo_metadata_review",),
        allowed_scopes=("local_workspace_metadata", "read_only_repo_structure"),
        limitations=(
            "registry_does_not_run_autopilot",
            "report_output_is_not_evidence",
            "future_execution_requires_autopilot_api_and_policy_gates",
        ),
    ),
    _manifest(
        skill_id="memory_candidate_review",
        name="Memory Candidate Review",
        description="Catalog metadata for future review of proposed Memory OS candidates.",
        category="memory",
        risk_class="local_read_only",
        execution_mode="metadata_only",
        input_contract={
            "expected_inputs": ["candidate_memory_metadata", "source_refs"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["review_notes_candidate"],
            "memory_write": "not_performed_by_skill_registry",
        },
        required_capabilities=("memory_candidate_metadata_review",),
        allowed_scopes=("memory_candidate_refs", "project_namespace_metadata"),
        limitations=(
            "registry_does_not_write_memory",
            "memory_candidate_is_not_approved_by_registry",
        ),
    ),
    _manifest(
        skill_id="society_review",
        name="Society Review",
        description="Catalog metadata for deterministic Society Session review output.",
        category="society",
        risk_class="local_read_only",
        execution_mode="metadata_only",
        input_contract={
            "expected_inputs": ["society_session_ref", "proposal_refs"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["proposal_review_metadata"],
            "proposal_authority": "none",
        },
        required_capabilities=("proposal_review",),
        allowed_scopes=("society_session_metadata", "proposal_metadata"),
        limitations=(
            "registry_does_not_run_society",
            "society_output_is_proposal_only",
        ),
    ),
    _manifest(
        skill_id="report_summarization",
        name="Report Summarization",
        description="Catalog metadata for future model-assisted report summarization.",
        category="reporting",
        risk_class="local_model_required",
        execution_mode="model_assisted_planned",
        input_contract={
            "expected_inputs": ["report_metadata", "source_refs"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["summary_proposal"],
            "model_output_authority": "none",
        },
        required_capabilities=("model_gateway_proposal_generation", "report_metadata_review"),
        allowed_scopes=("report_metadata", "source_refs_only"),
        requires_model=True,
        limitations=(
            "registry_does_not_call_model_gateway",
            "model_output_is_proposal_only",
        ),
    ),
    _manifest(
        skill_id="context_package_review",
        name="Context Package Review",
        description="Catalog metadata for future review of context package metadata.",
        category="context",
        risk_class="local_read_only",
        execution_mode="metadata_only",
        input_contract={
            "expected_inputs": ["context_package_metadata", "privacy_labels"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["context_review_candidate"],
            "permission": "not_granted_by_context_package",
        },
        required_capabilities=("context_metadata_review", "privacy_boundary_review"),
        allowed_scopes=("context_metadata", "source_refs_only"),
        limitations=(
            "context_package_is_not_permission",
            "registry_does_not_retrieve_context",
        ),
    ),
    _manifest(
        skill_id="model_assisted_explanation",
        name="Model Assisted Explanation",
        description="Catalog metadata for future Model Gateway assisted explanations.",
        category="model_gateway",
        risk_class="local_model_required",
        execution_mode="model_assisted_planned",
        input_contract={
            "expected_inputs": ["prompt", "purpose", "source_refs"],
            "registry_execution": "not_supported",
        },
        output_contract={
            "expected_outputs": ["explanation_proposal"],
            "model_output_authority": "none",
        },
        required_capabilities=("model_gateway_proposal_generation",),
        allowed_scopes=("operator_supplied_prompt", "source_refs_only"),
        requires_model=True,
        limitations=(
            "registry_does_not_call_model_gateway",
            "model_output_is_not_truth_or_evidence",
        ),
    ),
    _manifest(
        skill_id="higgsfield_mcp_media_generation",
        name="Higgsfield MCP Media Generation Candidate",
        description=(
            "Aegis-native future-gated metadata for the Higgsfield MCP media generation connector candidate."
        ),
        category="external_mcp",
        status="future_gated",
        risk_class="high_risk_external",
        execution_mode="external_candidate",
        input_contract={
            "candidate_source_url": "https://mcp.higgsfield.ai/mcp",
            "expected_inputs_future": ["media_generation_prompt", "explicit_user_authorization"],
            "registry_execution": "not_supported",
            "source_review_status": "not_connected_or_authenticated",
        },
        output_contract={
            "expected_outputs_future": ["media_asset_candidate"],
            "media_generation": "not_performed_by_skill_registry",
            "credit_or_quota_spend": "not_performed_by_skill_registry",
        },
        required_capabilities=(
            "external_mcp_connect",
            "media_generation",
            "explicit_user_authorization",
            "credential_boundary",
            "quota_or_credit_acknowledgement",
        ),
        allowed_scopes=("future_explicit_media_generation_scope",),
        requires_network=True,
        requires_mcp=True,
        requires_credentials=True,
        external_source="higgsfield_mcp_candidate_reference",
        limitations=(
            "not_connected",
            "not_authenticated",
            "no_media_generation",
            "no_credit_or_quota_spending",
            "not_available_in_rc1_execution",
            "cataloged_as_future_external_mcp_candidate_only",
        ),
    ),
    _manifest(
        skill_id="ecc_repo_scan_review",
        name="ECC Repo Scan Review Candidate",
        description="Aegis-native metadata for an ECC-inspired repo scan review candidate.",
        category="external_skill_reference",
        status="candidate",
        risk_class="unknown_risk",
        execution_mode="external_candidate",
        input_contract={
            "candidate_source_url": "https://github.com/affaan-m/ecc",
            "expected_inputs_future": ["repo_read_only_context", "operator_review"],
            "registry_execution": "not_supported",
            "source_review_status": "placeholder_from_user_supplied_reference",
        },
        output_contract={
            "expected_outputs_future": ["repo_review_notes_candidate"],
            "repo_scan": "not_performed_by_skill_registry",
        },
        required_capabilities=("repo_read_only_context", "operator_review"),
        allowed_scopes=("future_repo_read_only_context", "source_refs_only"),
        external_source="ecc_candidate_reference",
        limitations=(
            "ecc_not_installed",
            "ecc_not_bulk_imported",
            "external_content_not_trusted_as_authority",
            "no_repo_scan_performed_by_skill_registry",
        ),
    ),
    _manifest(
        skill_id="ecc_article_writing_reference",
        name="ECC Article Writing Reference Candidate",
        description="Aegis-native metadata for an ECC-inspired article writing candidate.",
        category="external_skill_reference",
        status="candidate",
        risk_class="local_model_required",
        execution_mode="external_candidate",
        input_contract={
            "candidate_source_url": "https://github.com/affaan-m/ecc",
            "expected_inputs_future": ["topic", "source_refs", "operator_review"],
            "registry_execution": "not_supported",
            "source_review_status": "placeholder_from_user_supplied_reference",
        },
        output_contract={
            "expected_outputs_future": ["article_draft_candidate"],
            "model_output_authority": "none",
        },
        required_capabilities=("model_gateway_proposal_generation", "operator_review", "source_refs_only"),
        allowed_scopes=("draft_content_metadata", "source_refs_only"),
        requires_model=True,
        external_source="ecc_candidate_reference",
        limitations=(
            "ecc_not_installed",
            "registry_does_not_call_model_gateway",
            "draft_is_proposal_only",
            "no_external_skill_execution",
        ),
    ),
    _manifest(
        skill_id="ecc_security_config_review",
        name="ECC Security Config Review Candidate",
        description="Aegis-native metadata for an ECC-inspired security configuration review candidate.",
        category="external_skill_reference",
        status="candidate",
        risk_class="unknown_risk",
        execution_mode="external_candidate",
        input_contract={
            "candidate_source_url": "https://github.com/affaan-m/ecc",
            "expected_inputs_future": ["config_metadata", "source_refs", "operator_review"],
            "registry_execution": "not_supported",
            "source_review_status": "placeholder_from_user_supplied_reference",
        },
        output_contract={
            "expected_outputs_future": ["security_config_review_candidate"],
            "security_claim": "not_created_by_skill_registry",
        },
        required_capabilities=("security_config_metadata_review", "operator_review", "source_refs_only"),
        allowed_scopes=("config_metadata", "source_refs_only"),
        external_source="ecc_candidate_reference",
        limitations=(
            "ecc_not_installed",
            "no_secret_or_credential_access",
            "security_review_is_not_verifier_success",
            "no_shell_execution",
        ),
    ),
    _manifest(
        skill_id="ecc_github_ops_reference",
        name="ECC GitHub Ops Reference Candidate",
        description="Aegis-native future-gated metadata for an ECC-inspired GitHub operations candidate.",
        category="external_skill_reference",
        status="future_gated",
        risk_class="high_risk_external",
        execution_mode="future_policy_gated",
        input_contract={
            "candidate_source_url": "https://github.com/affaan-m/ecc",
            "expected_inputs_future": ["github_operation_plan", "explicit_user_approval"],
            "registry_execution": "not_supported",
            "source_review_status": "placeholder_from_user_supplied_reference",
        },
        output_contract={
            "expected_outputs_future": ["github_operation_plan_candidate"],
            "github_mutation": "not_performed_by_skill_registry",
        },
        required_capabilities=(
            "github_auth",
            "network_access",
            "explicit_user_approval",
            "mutation_policy_gate",
            "capability_lease_required_future",
        ),
        allowed_scopes=("future_explicit_github_ops_scope",),
        requires_network=True,
        requires_credentials=True,
        external_source="ecc_candidate_reference",
        limitations=(
            "ecc_not_installed",
            "no_github_api_call",
            "no_github_mutation",
            "credential_boundary_required_before_future_use",
            "capability_lease_required_before_future_mutation",
        ),
    ),
)
