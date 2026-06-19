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
