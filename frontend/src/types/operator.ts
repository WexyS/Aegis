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
}

export interface OperatorTraceItem {
  id: string;
  step: OperatorTraceStep;
  status: OperatorTraceStatus;
}

export interface OperatorArtifact {
  id: string;
  type: OperatorArtifactType;
  status: 'draft' | 'preview-only';
  request: string;
  safetyFlags: string[];
}

export interface OperatorDecisionPreview {
  id: string;
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
