from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Mapping


EXTERNAL_PROVIDER_EXECUTION_PERMISSION = "not_granted_by_external_provider_readiness"


@dataclass(frozen=True)
class ExternalProviderDefinition:
    provider_id: str
    label: str
    provider_family: str
    intended_use: str
    api_key_env_var: str
    model_env_var: str
    base_url_env_var: str | None = None
    default_base_url_guidance: str | None = None
    suggested_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExternalProviderReadiness:
    provider_id: str
    label: str
    provider_family: str
    status: str
    intended_use: str
    expected_env_vars: tuple[str, ...]
    default_base_url_guidance: str | None
    suggested_models: tuple[str, ...]
    api_key_present: bool
    api_key_value_exposed: bool
    cloud_completion_enabled: bool
    automatic_fallback_allowed: bool
    manual_operator_opt_in_required: bool
    prompt_preview_required: bool
    cost_warning_required: bool
    privacy_warning_required: bool
    secrets_allowed_in_prompt: bool
    raw_logs_allowed_in_prompt: bool
    raw_journals_allowed_in_prompt: bool
    raw_evidence_allowed_in_prompt: bool
    repo_dump_allowed_in_prompt: bool
    output_authority: bool
    output_is_evidence: bool
    output_is_verifier_success: bool
    authority: bool
    evidence_created: bool
    verifier_success: bool
    approval_granted: bool
    permission_granted: bool
    lease_grant: bool
    capability_lease_granted: bool
    memory_write_allowed: bool
    tool_execution_allowed: bool
    model_call_allowed: bool
    external_api_call_allowed: bool
    data_sent_external: bool
    execution_permission: str
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    future_requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROVIDER_DEFINITIONS: tuple[ExternalProviderDefinition, ...] = (
    ExternalProviderDefinition(
        provider_id="openrouter",
        label="OpenRouter",
        provider_family="external_model_gateway",
        intended_use="Future operator-selected external model broker.",
        api_key_env_var="AEGIS_OPENROUTER_API_KEY",
        model_env_var="AEGIS_OPENROUTER_MODEL",
    ),
    ExternalProviderDefinition(
        provider_id="deepseek",
        label="DeepSeek API",
        provider_family="external_model_gateway",
        intended_use="Future operator-selected reasoning provider.",
        api_key_env_var="AEGIS_DEEPSEEK_API_KEY",
        model_env_var="AEGIS_DEEPSEEK_MODEL",
    ),
    ExternalProviderDefinition(
        provider_id="openai",
        label="OpenAI",
        provider_family="external_model_gateway",
        intended_use="Future operator-selected external model provider.",
        api_key_env_var="AEGIS_OPENAI_API_KEY",
        model_env_var="AEGIS_OPENAI_MODEL",
    ),
    ExternalProviderDefinition(
        provider_id="anthropic",
        label="Anthropic",
        provider_family="external_model_gateway",
        intended_use="Future operator-selected external model provider.",
        api_key_env_var="AEGIS_ANTHROPIC_API_KEY",
        model_env_var="AEGIS_ANTHROPIC_MODEL",
    ),
    ExternalProviderDefinition(
        provider_id="gemini",
        label="Gemini",
        provider_family="external_model_gateway",
        intended_use="Future operator-selected external model provider.",
        api_key_env_var="AEGIS_GEMINI_API_KEY",
        model_env_var="AEGIS_GEMINI_MODEL",
    ),
    ExternalProviderDefinition(
        provider_id="moonshot_kimi",
        label="Moonshot / Kimi",
        provider_family="external_cloud_provider",
        intended_use=(
            "Future operator-selected external coding, long-context code review, "
            "agentic coding plan, and multimodal/code review candidate."
        ),
        api_key_env_var="AEGIS_MOONSHOT_API_KEY",
        model_env_var="AEGIS_MOONSHOT_MODEL",
        base_url_env_var="AEGIS_MOONSHOT_BASE_URL",
        default_base_url_guidance="https://api.moonshot.ai/v1",
        suggested_models=("kimi-k2.7-code", "kimi-k2.7-code-highspeed"),
    ),
)


def list_external_provider_readiness(
    env: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    source = os.environ if env is None else env
    return [_readiness_for(definition, source).to_dict() for definition in PROVIDER_DEFINITIONS]


def build_cloud_fallback_policy() -> dict[str, Any]:
    return {
        "automatic_cloud_fallback_allowed": False,
        "cloud_calls_enabled_now": False,
        "external_provider_broker_required": True,
        "operator_opt_in_required": True,
        "prompt_preview_required": True,
        "cost_warning_required": True,
        "privacy_warning_required": True,
        "secrets_redaction_required": True,
        "proposal_only_output_required": True,
        "provider_key_presence_is_authorization": False,
        "local_failure_triggers_cloud": False,
        "provider_routing_added": False,
        "warnings": (
            "local_failure_must_not_silently_trigger_cloud",
            "api_key_presence_is_readiness_metadata_only",
            "future_broker_must_require_explicit_operator_opt_in",
        ),
        "limitations": (
            "no_external_provider_calls_in_current_model_hub_readiness",
            "no_cloud_completion_endpoint_added",
        ),
    }


def expected_provider_env_placeholders() -> list[dict[str, str]]:
    return [
        {
            "provider_id": definition.provider_id,
            "api_key_env_var": definition.api_key_env_var,
            "model_env_var": definition.model_env_var,
            "base_url_env_var": definition.base_url_env_var or "",
            "default_base_url_guidance": definition.default_base_url_guidance or "",
            "suggested_models": definition.suggested_models,
            "api_key_placeholder": f'$env:{definition.api_key_env_var}="<paste-key-in-your-own-shell>"',
            "model_placeholder": f'$env:{definition.model_env_var}="{_model_placeholder_value(definition)}"',
            "base_url_placeholder": (
                f'$env:{definition.base_url_env_var}="{definition.default_base_url_guidance}"'
                if definition.base_url_env_var and definition.default_base_url_guidance
                else ""
            ),
        }
        for definition in PROVIDER_DEFINITIONS
    ]


def _readiness_for(
    definition: ExternalProviderDefinition,
    env: Mapping[str, str],
) -> ExternalProviderReadiness:
    key_present = bool(str(env.get(definition.api_key_env_var, "")).strip())
    status = "key_present_calls_disabled" if key_present else "missing_key_disabled"
    expected_env_vars = [definition.api_key_env_var, definition.model_env_var]
    if definition.base_url_env_var:
        expected_env_vars.append(definition.base_url_env_var)
    return ExternalProviderReadiness(
        provider_id=definition.provider_id,
        label=definition.label,
        provider_family=definition.provider_family,
        status=status,
        intended_use=definition.intended_use,
        expected_env_vars=tuple(expected_env_vars),
        default_base_url_guidance=definition.default_base_url_guidance,
        suggested_models=definition.suggested_models,
        api_key_present=key_present,
        api_key_value_exposed=False,
        cloud_completion_enabled=False,
        automatic_fallback_allowed=False,
        manual_operator_opt_in_required=True,
        prompt_preview_required=True,
        cost_warning_required=True,
        privacy_warning_required=True,
        secrets_allowed_in_prompt=False,
        raw_logs_allowed_in_prompt=False,
        raw_journals_allowed_in_prompt=False,
        raw_evidence_allowed_in_prompt=False,
        repo_dump_allowed_in_prompt=False,
        output_authority=False,
        output_is_evidence=False,
        output_is_verifier_success=False,
        authority=False,
        evidence_created=False,
        verifier_success=False,
        approval_granted=False,
        permission_granted=False,
        lease_grant=False,
        capability_lease_granted=False,
        memory_write_allowed=False,
        tool_execution_allowed=False,
        model_call_allowed=False,
        external_api_call_allowed=False,
        data_sent_external=False,
        execution_permission=EXTERNAL_PROVIDER_EXECUTION_PERMISSION,
        warnings=(
            "key_presence_is_not_authorization",
            "cloud_completion_disabled_until_external_provider_broker_exists",
            "manual_operator_opt_in_required_before_future_use",
        ),
        limitations=(
            "readiness_metadata_only",
            "api_key_value_never_returned",
            "no_external_api_call_performed",
            "no_cloud_fallback",
        ),
        future_requirements=(
            "external_provider_broker",
            "explicit_provider_enablement",
            "exact_model_selection",
            "prompt_preview",
            "cost_warning",
            "privacy_warning",
            "secret_redaction",
            "proposal_only_output_envelope",
        ),
    )


def _model_placeholder_value(definition: ExternalProviderDefinition) -> str:
    if definition.suggested_models:
        return definition.suggested_models[0]
    return "<future-model-id>"
