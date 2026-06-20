export type StatusTone = 'success' | 'info' | 'warning' | 'danger' | 'unknown';

export type RcRecord = Record<string, unknown>;

export interface MemoryItem {
  id: string;
  type: string;
  content: string;
  content_summary?: string;
  scope: string;
  status: string;
  sensitivity: string;
  source_refs?: RcRecord[];
  project_ref?: string | null;
  repository_ref?: string | null;
  session_ref?: string | null;
  created_at?: number;
  updated_at?: number;
  deleted_at?: number | null;
  metadata?: RcRecord;
  candidate_only?: boolean;
  execution_permission?: string;
  retrieved_memory_is_truth?: boolean;
  memory_output_is_authority?: boolean;
}

export interface MemoryOperationResponse {
  ok: boolean;
  operation: string;
  status: string;
  memory_id?: string | null;
  memory?: MemoryItem | null;
  memories?: MemoryItem[];
  result_count?: number;
  validation_result?: RcRecord;
  governance_result?: RcRecord;
  warnings?: string[];
  limitations?: string[];
  failure_reasons?: string[];
  runtime_dispatch_allowed?: boolean;
  evidence_provided_by_memory?: boolean;
  verifier_success?: boolean;
  retrieved_memory_is_truth?: boolean;
  memory_retrieval_is_authority?: boolean;
}

export interface AutoPilotReport {
  report_id: string;
  task_id?: string;
  task_name?: string;
  status: string;
  root_path?: string;
  context_preflight?: RcRecord;
  policy_gate?: RcRecord;
  source_inventory?: {
    root_path?: string;
    total_files?: number;
    total_dirs?: number;
    included_file_count?: number;
    key_files?: string[];
    package_config_files?: string[];
    docs_paths?: string[];
    tests_paths?: string[];
    frontend_indicators?: string[];
    backend_indicators?: string[];
    excluded_dirs?: RcRecord[];
    excluded_files?: RcRecord[];
    warnings?: string[];
    limitations?: string[];
  };
  findings?: RcRecord[];
  risk_markers?: Array<{ id?: string; severity?: string; message?: string }>;
  memory_candidate_proposals?: MemoryCandidateProposal[];
  verifier_lite?: {
    state?: string;
    checks?: RcRecord;
    limitations?: string[];
  };
  warnings?: string[];
  limitations?: string[];
  degraded_state?: boolean;
  runtime_dispatch_allowed?: boolean;
  shell_command_performed?: boolean;
  network_call_performed?: boolean;
  model_call_performed?: boolean;
  mcp_call_performed?: boolean;
  report_is_evidence?: boolean;
  report_is_verifier?: boolean;
}

export interface AutoPilotReportListResponse {
  status: string;
  report_count: number;
  reports: AutoPilotReport[];
  report_persistence?: string;
}

export interface MemoryCandidateProposal {
  type?: string;
  content?: string;
  scope_suggestion?: string;
  sensitivity_suggestion?: string;
  source_ref?: string;
  rationale?: string;
  status?: string;
  persisted?: boolean;
  active_memory?: boolean;
}

export interface SocietyProposal {
  role: string;
  proposal_type: string;
  title: string;
  summary: string;
  inputs_used?: string[];
  claims?: RcRecord;
  limitations?: string[];
  authority?: boolean;
  can_execute_tools?: boolean;
  verifier_success?: boolean;
  evidence_provided?: boolean;
}

export interface SocietyTimelineEvent {
  sequence: number;
  event: string;
  role: string;
  summary: string;
  backend_owned?: boolean;
  authority?: boolean;
  runtime_dispatch_allowed?: boolean;
}

export interface SocietySession {
  session_id: string;
  status: string;
  mode: string;
  society_name?: string;
  input_report_id?: string | null;
  input_report_summary?: RcRecord;
  memory_refs?: RcRecord[];
  roles?: Array<{ name: string; status: string; mode?: string }>;
  proposals?: SocietyProposal[];
  timeline?: SocietyTimelineEvent[];
  final_summary?: string;
  warnings?: string[];
  limitations?: string[];
  degraded_state?: boolean;
  runtime_dispatch_allowed?: boolean;
  model_call_performed?: boolean;
  mcp_call_performed?: boolean;
  tool_call_performed?: boolean;
  shell_command_performed?: boolean;
  network_call_performed?: boolean;
  memory_write_performed?: boolean;
}

export interface SocietySessionListResponse {
  status: string;
  session_count: number;
  sessions: SocietySession[];
  session_persistence?: string;
}
