export interface AskSourceRef {
  source_id: string;
  label: string;
  authority: boolean;
  evidence: boolean;
}

export interface AskRequest {
  question: string;
  intent?: string;
  include_memory?: boolean;
  include_model_polish?: boolean;
  include_autopilot?: boolean;
  include_agent_proposal?: boolean;
  scope?: string;
  max_sources?: number;
}

export interface AskResponse {
  answer: string;
  intent: string;
  source_refs: AskSourceRef[];
  known: string[];
  unknown: string[];
  limitations: string[];
  recommended_next_steps: string[];
  non_authority_flags: Record<string, boolean>;
  runtime_health_summary: Record<string, unknown>;
  model_used: string | null;
  memory_written: boolean;
  execution_performed: boolean;
  evidence_created: boolean;
  verifier_success: boolean;
  approval_granted: boolean;
  capability_lease_granted: boolean;
  tool_execution_performed: boolean;
  plugin_execution_performed: boolean;
  agent_execution_performed: boolean;
  runtime_dispatch_allowed: boolean;
  execution_permission: string;
}
