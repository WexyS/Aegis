export interface ModelHubIntegrationRecord {
  integration_id: string;
  aegis_name: string;
  family: string;
  aegis_surface: string;
  source_strategy: string;
  default_execution_status: string;
  current_status: string;
  risk_level: string;
  requires_network: boolean;
  requires_secret: boolean;
  requires_process_spawn: boolean;
  requires_model_gateway: boolean;
  requires_external_api: boolean;
  allowed_modes: string[];
  notes: string[];
  authority: boolean;
  runtime_dispatch_allowed: boolean;
  execution_permission: string;
  execution_enabled_now: boolean;
  model_call_performed: boolean;
  external_api_called: boolean;
}

export interface ModelHubModePolicySummary {
  mode: string;
  display_name: string;
  model_gateway_allowed: boolean;
  external_api_allowed: boolean;
  tool_execution_allowed: boolean;
  agent_execution_allowed: boolean;
  workflow_execution_allowed: boolean;
  computer_control_allowed: boolean;
  mode_allows_execution_now: boolean;
  current_execution_grant: boolean;
}

export interface ModelGatewayStatus {
  status: string;
  provider: string;
  base_url: string;
  host: string;
  model: string | null;
  model_configured: boolean;
  enabled: boolean;
  timeout_seconds: number;
  max_input_chars: number;
  max_output_tokens: number;
  health_result: unknown;
  failure_reasons: string[];
  warnings: string[];
  limitations: string[];
  unknowns: string[];
  duration_ms: number;
  provider_probe_performed: boolean;
  http_request_performed: boolean;
  model_call_performed: boolean;
  generation_performed: boolean;
  prompt_payload_sent: boolean;
  context_payload_sent: boolean;
  memory_write_performed: boolean;
  tool_call_performed: boolean;
  mcp_call_performed: boolean;
  shell_command_performed: boolean;
  file_mutation_performed: boolean;
  data_sent_external: boolean;
  authority: boolean;
  runtime_dispatch_allowed: boolean;
  execution_permission: string;
  evidence: boolean;
  evidence_provided_by_model: boolean;
  verifier_success: boolean;
  approval_granted: boolean;
  permission_granted: boolean;
  capability_lease_granted: boolean;
  model_output_is_truth: boolean;
  model_output_is_evidence: boolean;
  model_output_is_verifier_success: boolean;
}

export interface ModelGatewayCompletionResponse {
  request_id: string;
  status: string;
  provider: string;
  base_url: string;
  model: string | null;
  purpose: string;
  output_text: string;
  usage: Record<string, unknown>;
  started_at: number;
  completed_at: number;
  duration_ms: number;
  warnings: string[];
  limitations: string[];
  failure_reasons: string[];
  raw_error: string | null;
  schema_validation: string;
  safety_validation: string;
  http_request_performed: boolean;
  model_call_performed: boolean;
  generation_performed: boolean;
  prompt_payload_sent: boolean;
  context_payload_sent: boolean;
  memory_write_performed: boolean;
  tool_call_performed: boolean;
  mcp_call_performed: boolean;
  shell_command_performed: boolean;
  file_mutation_performed: boolean;
  data_sent_external: boolean;
  transcript_persisted: boolean;
  journal_mutated: boolean;
  evidence_mutated: boolean;
  runtime_state_mutated: boolean;
  authority: boolean;
  runtime_dispatch_allowed: boolean;
  execution_permission: string;
  evidence: boolean;
  evidence_provided_by_model: boolean;
  verifier_success: boolean;
  approval_granted: boolean;
  permission_granted: boolean;
  capability_lease_granted: boolean;
  model_output_is_truth: boolean;
  model_output_is_evidence: boolean;
  model_output_is_verifier_success: boolean;
}

export interface ModelGatewayCompleteRequest {
  request_id?: string;
  purpose: 'explanation' | 'proposal_draft';
  prompt: string;
  max_output_tokens?: number;
  temperature?: number;
}

export interface LocalModelProfile {
  profile_id: string;
  label: string;
  purpose: string;
  preferred_model_id_hint: string;
  model_id_matchers: string[];
  eligible_for_completion: boolean;
  eligible_for_probe: boolean;
  eligible_for_rerank: boolean;
  default_profile: boolean;
  manual_selection_required: boolean;
  hardware_target: string;
  vram_gb_target: number;
  system_ram_gb_target: number;
  memory_pressure: string;
  recommended_max_input_chars: number;
  recommended_max_output_tokens: number;
  recommended_timeout_seconds: number;
  warnings: string[];
  limitations: string[];
  operator_steps: string[];
  cloud_fallback_allowed: boolean;
  execution_permission: string;
  authority: boolean;
  model_output_is_truth: boolean;
  evidence: boolean;
  verifier_success: boolean;
  approval_granted: boolean;
  capability_lease_granted: boolean;
}

export interface ResourceGuardrails {
  hardware_target: string;
  gpu: string;
  vram_gb_target: number;
  system_ram_gb_target: number;
  local_model_manager: string;
  expected_local_server: string;
  default_profile_id: string;
  recommended_order: string[];
  automatic_model_switching_allowed: boolean;
  ui_env_write_allowed: boolean;
  live_probe_required_for_installation_claim: boolean;
  configured_model_is_not_live_proof: boolean;
  warnings: string[];
  limitations: string[];
}

export interface ActiveModelProfileMatch {
  status: string;
  configured_model: string | null;
  matched_profile_id: string | null;
  matched_profile_label: string | null;
  match_type: string;
  completion_safe: boolean;
  rerank_only: boolean;
  automatic_model_switch_performed: boolean;
  live_installation_claimed: boolean;
  warnings: string[];
  limitations: string[];
  authority: boolean;
  evidence: boolean;
  verifier_success: boolean;
}

export interface ExternalProviderReadiness {
  provider_id: string;
  label: string;
  provider_family: string;
  status: string;
  intended_use: string;
  expected_env_vars: string[];
  api_key_present: boolean;
  api_key_value_exposed: boolean;
  cloud_completion_enabled: boolean;
  automatic_fallback_allowed: boolean;
  manual_operator_opt_in_required: boolean;
  prompt_preview_required: boolean;
  cost_warning_required: boolean;
  privacy_warning_required: boolean;
  secrets_allowed_in_prompt: boolean;
  raw_logs_allowed_in_prompt: boolean;
  raw_journals_allowed_in_prompt: boolean;
  raw_evidence_allowed_in_prompt: boolean;
  repo_dump_allowed_in_prompt: boolean;
  output_authority: boolean;
  output_is_evidence: boolean;
  output_is_verifier_success: boolean;
  approval_granted: boolean;
  capability_lease_granted: boolean;
  memory_write_allowed: boolean;
  tool_execution_allowed: boolean;
  execution_permission: string;
  warnings: string[];
  limitations: string[];
  future_requirements: string[];
}

export interface CloudFallbackPolicy {
  automatic_cloud_fallback_allowed: boolean;
  cloud_calls_enabled_now: boolean;
  external_provider_broker_required: boolean;
  operator_opt_in_required: boolean;
  prompt_preview_required: boolean;
  cost_warning_required: boolean;
  privacy_warning_required: boolean;
  secrets_redaction_required: boolean;
  proposal_only_output_required: boolean;
  provider_key_presence_is_authorization: boolean;
  local_failure_triggers_cloud: boolean;
  provider_routing_added: boolean;
  warnings: string[];
  limitations: string[];
}

export interface ModelHubStatus {
  contract: string;
  status: string;
  model_gateway: ModelGatewayStatus;
  orchestrator_readiness: {
    integration_landscape_count?: number;
    family_counts?: Record<string, number>;
    families_represented?: string[];
    mode_execution_allowed_now?: Record<string, boolean>;
    provider_probe_performed: boolean;
    http_request_performed: boolean;
    model_call_performed: boolean;
    lm_studio_called: boolean;
  };
  model_hub_integrations: ModelHubIntegrationRecord[];
  mode_policy_summary: {
    modes: ModelHubModePolicySummary[];
    mode_count: number;
    execution_allowed_now: boolean;
    external_api_allowed_now: boolean;
    cloud_routing_allowed: boolean;
  };
  lm_studio: {
    provider: string;
    base_url: string;
    host: string;
    enabled: boolean;
    model: string | null;
    model_configured: boolean;
    status: string;
    failure_reasons: string[];
    warnings: string[];
    probe_required_for_live_health: boolean;
    local_only_boundary: boolean;
    openai_compatible_local_endpoint: boolean;
    config_mutation_allowed: boolean;
    env_file_written: boolean;
    cloud_fallback_available: boolean;
    status_source: string;
  };
  local_model_profiles: LocalModelProfile[];
  resource_guardrails: ResourceGuardrails;
  recommended_default_profile_id: string;
  active_model_profile_match: ActiveModelProfileMatch;
  external_provider_readiness: ExternalProviderReadiness[];
  cloud_fallback_policy: CloudFallbackPolicy;
  non_authority_flags: Record<string, boolean>;
  authority: boolean;
  runtime_dispatch_allowed: boolean;
  execution_permission: string;
  approval_grant: boolean;
  approval_granted: boolean;
  capability_grant: boolean;
  capability_lease_granted: boolean;
  lease_grant: boolean;
  evidence_created: boolean;
  evidence_provided_by_model_hub: boolean;
  verifier_success: boolean;
  mutation_performed: boolean;
  frontend_authority: boolean;
  provider_probe_performed: boolean;
  http_request_performed: boolean;
  model_call_performed: boolean;
  generation_performed: boolean;
  prompt_payload_sent: boolean;
  context_payload_sent: boolean;
  memory_write_performed: boolean;
  tool_call_performed: boolean;
  mcp_call_performed: boolean;
  plugin_execution_performed: boolean;
  agent_execution_performed: boolean;
  workflow_execution_performed: boolean;
  computer_control_performed: boolean;
  shell_command_performed: boolean;
  file_mutation_performed: boolean;
  external_api_called: boolean;
  cloud_routing_allowed: boolean;
  data_sent_external: boolean;
  config_mutation_allowed: boolean;
  env_file_written: boolean;
  requires_backend_validation: boolean;
  requires_policy_check: boolean;
  limitations: string[];
}
