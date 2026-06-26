export type OperatorIntent =
  | 'ask_status'
  | 'safe_plan'
  | 'code_prompt'
  | 'memory_action'
  | 'model_hub'
  | 'vision_review'
  | 'web_research'
  | 'command_preview'
  | 'approval_review'
  | 'unknown';

export type OperatorRouteId =
  | 'status_explainer'
  | 'safe_plan_builder'
  | 'code_prompt_builder'
  | 'memory_policy_preview'
  | 'model_hub_review'
  | 'vision_review_plan'
  | 'vision_to_code_prompt'
  | 'research_plan'
  | 'command_approval_preview'
  | 'approval_review';

export type OperatorTraceStatus = 'done' | 'waiting' | 'blocked' | 'info';

export type OperatorTraceStep =
  | 'request_received'
  | 'intent_preview_generated'
  | 'route_selected'
  | 'model_candidate_selected'
  | 'permission_boundary_evaluated'
  | 'cloud_boundary_evaluated'
  | 'memory_policy_evaluated'
  | 'artifact_draft_created'
  | 'blocked_actions_not_performed';

export type OperatorArtifactType =
  | 'safe_plan_draft'
  | 'codex_prompt_draft'
  | 'ui_review_plan'
  | 'research_plan'
  | 'memory_action_preview'
  | 'model_routing_summary'
  | 'command_approval_preview';

export type OperatorPermissionMode = 'safe_preview';

export type OperatorModelPreference =
  | 'auto'
  | 'fast_summary'
  | 'balanced_draft'
  | 'code_review'
  | 'reasoning_plan'
  | 'vision_review'
  | 'external_provider';

export type OperatorPlanningDetail = 'concise' | 'balanced' | 'deep';

export type LocalProposalStatus = 'idle' | 'loading' | 'completed' | 'failed';

export interface LocalProposalResult {
  outputText: string;
  backendStatus: string;
  model: string | null;
  purpose: string;
  durationMs: number;
  warnings: string[];
  limitations: string[];
  modelCallPerformed: boolean;
}

export interface OperatorSessionHistoryItem {
  id: string;
  request: string;
  artifactId: string;
  artifactTitle: string;
  previewSource: OperatorPreviewSource;
  createdAt: string;
}

export interface OperatorModelCandidate {
  profileId: string;
  modelHint: string;
  selectedForCall?: boolean;
  proposalOnly?: boolean;
}

export interface OperatorTraceItem {
  id: string;
  step: OperatorTraceStep;
  status: OperatorTraceStatus;
  detail?: string;
}

export interface OperatorArtifact {
  id: string;
  type: OperatorArtifactType;
  status: 'draft' | 'preview-only';
  title?: string;
  request: string;
  summary?: string;
  body?: string;
  safetyFlags: string[];
}

export type OperatorPreviewSource = 'backend_contract' | 'frontend_fallback';

export type OperatorCapabilityClassification =
  | 'observe_only'
  | 'explain_only'
  | 'proposal_only'
  | 'approval_required'
  | 'execution_unavailable'
  | 'provider_unavailable'
  | 'unsupported_or_ambiguous';

export interface OperatorCapabilityAssessment {
  contract: 'aegis-read-only-capability-broker-preview';
  classification: OperatorCapabilityClassification;
  rationale: string;
  boundary: string;
  source: 'backend_route_preview';
  readOnly: true;
  previewOnly: true;
  deterministic: true;
  nonAuthoritative: true;
  nonExecuting: true;
  nonApproving: true;
  nonVerifying: true;
  actionPerformed: false;
  modelCallPerformed: false;
  providerCallPerformed: false;
  commandExecuted: false;
  toolExecuted: false;
  browserActionPerformed: false;
  filesystemMutationPerformed: false;
  memoryWritten: false;
  approvalGranted: false;
  evidenceCreated: false;
  verifierRun: false;
  executionAuthorized: false;
}

export interface OperatorDecisionPreview {
  id: string;
  contract?: string;
  status?: string;
  routerMode?: string;
  previewSource: OperatorPreviewSource;
  backendPreviewAvailable: boolean;
  backendPreviewError: string | null;
  request: string;
  intents: OperatorIntent[];
  primaryIntent: OperatorIntent;
  routeId: OperatorRouteId;
  modelCandidates: OperatorModelCandidate[];
  cloudNeeded: boolean;
  approvalNeeded: boolean;
  memoryActionProposed: boolean;
  visionBoundaryRequired: boolean;
  researchBoundaryRequired: boolean;
  artifactId: string;
  capabilityAssessment: OperatorCapabilityAssessment | null;
  permissionMode: OperatorPermissionMode;
  safety: {
    commandExecutionPerformed: false;
    modelCallPerformed: false;
    cloudCallPerformed: false;
    imageUploadPerformed: false;
    memoryWritePerformed: false;
    evidenceCreated: false;
    verifierSuccessCreated: false;
    approvalGranted: false;
    permissionGranted: false;
    backendAuthority: false;
  };
}

export interface OperatorBackendRoutePreview {
  contract: string;
  status: string;
  router_mode: string;
  request: string;
  preview_id: string;
  request_id: string;
  intents: OperatorIntent[];
  primary_intent: OperatorIntent;
  route_id: OperatorRouteId;
  model_candidates: Array<{
    profile_id: string;
    model_hint: string;
    selected_for_call: boolean;
    proposal_only: boolean;
  }>;
  permission_mode: OperatorPermissionMode;
  cloud_needed: boolean;
  approval_needed: boolean;
  memory_action_proposed: boolean;
  vision_boundary_required: boolean;
  research_boundary_required: boolean;
  artifact: {
    id: string;
    type: OperatorArtifactType;
    status: 'preview_only' | 'blocked_preview';
    title: string;
    request: string;
    summary: string;
    body?: string;
    safety_flags: string[];
  };
  trace_items: Array<{
    id: string;
    step: OperatorTraceStep;
    status: OperatorTraceStatus;
    detail: string;
  }>;
  capability_assessment: {
    contract: 'aegis-read-only-capability-broker-preview';
    classification: OperatorCapabilityClassification;
    rationale: string;
    boundary: string;
    source: 'backend_route_preview';
    read_only: true;
    preview_only: true;
    deterministic: true;
    non_authoritative: true;
    non_executing: true;
    non_approving: true;
    non_verifying: true;
    action_performed: false;
    model_call_performed: false;
    provider_call_performed: false;
    command_executed: false;
    tool_executed: false;
    browser_action_performed: false;
    filesystem_mutation_performed: false;
    memory_written: false;
    approval_granted: false;
    evidence_created: false;
    verifier_run: false;
    execution_authorized: false;
  };
  command_execution_performed: false;
  model_call_performed: false;
  cloud_call_performed: false;
  image_upload_performed: false;
  memory_write_performed: false;
  evidence_created: false;
  verifier_success: false;
  approval_granted: false;
  permission_granted: false;
  authority: false;
}
