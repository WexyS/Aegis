import { create } from 'zustand';

import type {
  OperatorArtifact,
  OperatorArtifactType,
  OperatorDecisionPreview,
  OperatorIntent,
  OperatorModelCandidate,
  OperatorPermissionMode,
  OperatorRouteId,
  OperatorTraceItem,
} from '@/types/operator';

type OperatorStoreState = {
  composerText: string;
  lastDecision: OperatorDecisionPreview | null;
  traceItems: OperatorTraceItem[];
  artifacts: OperatorArtifact[];
  selectedArtifactId: string | null;
  permissionModePreview: OperatorPermissionMode;
  setComposerText: (value: string) => void;
  clearOperatorSession: () => void;
  selectArtifact: (artifactId: string) => void;
  submitPreviewRequest: (request?: string) => OperatorDecisionPreview | null;
};

const FALSE_SAFETY_FLAGS = {
  commandExecutionPerformed: false,
  modelCallPerformed: false,
  cloudCallPerformed: false,
  imageUploadPerformed: false,
  memoryWritePerformed: false,
  evidenceCreated: false,
  verifierSuccessCreated: false,
  approvalGranted: false,
  permissionGranted: false,
  backendAuthority: false,
} as const;

const NO_ACTION_FLAGS = [
  'no_command_execution',
  'no_model_call',
  'no_cloud_call',
  'no_image_upload',
  'no_memory_write',
  'no_evidence',
  'no_verifier_success',
  'no_approval_or_permission_grant',
];

export const useOperatorStore = create<OperatorStoreState>((set, get) => ({
  composerText: '',
  lastDecision: null,
  traceItems: [],
  artifacts: [],
  selectedArtifactId: null,
  permissionModePreview: 'safe_preview',
  setComposerText: (value) => set({ composerText: value }),
  clearOperatorSession: () => set({
    composerText: '',
    lastDecision: null,
    traceItems: [],
    artifacts: [],
    selectedArtifactId: null,
  }),
  selectArtifact: (artifactId) => set({ selectedArtifactId: artifactId }),
  submitPreviewRequest: (request) => {
    const text = (request ?? get().composerText).trim();
    if (!text) return null;
    const decision = buildDecisionPreview(text);
    const artifact = buildArtifact(decision);
    const traceItems = buildTraceItems(decision);
    set((state) => ({
      composerText: text,
      lastDecision: decision,
      traceItems,
      artifacts: [artifact, ...state.artifacts.filter((item) => item.id !== artifact.id)].slice(0, 6),
      selectedArtifactId: artifact.id,
    }));
    return decision;
  },
}));

function buildDecisionPreview(request: string): OperatorDecisionPreview {
  const intents = classifyOperatorIntents(request);
  const primaryIntent = choosePrimaryIntent(intents);
  const routeId = chooseRouteId(intents, primaryIntent);
  const id = `operator-preview-${stablePreviewId(`${routeId}:${request}`)}`;
  return {
    id,
    request,
    intents,
    primaryIntent,
    routeId,
    modelCandidates: chooseModelCandidates(intents, primaryIntent),
    cloudNeeded: false,
    approvalNeeded: ['command_preview', 'approval_review'].includes(primaryIntent),
    memoryActionProposed: intents.includes('memory_action'),
    visionBoundaryRequired: intents.includes('vision_review'),
    researchBoundaryRequired: intents.includes('web_research'),
    artifactId: `${id}-artifact`,
    permissionMode: 'safe_preview',
    safety: FALSE_SAFETY_FLAGS,
  };
}

function buildArtifact(decision: OperatorDecisionPreview): OperatorArtifact {
  const typeByRoute: Record<OperatorRouteId, OperatorArtifactType> = {
    status_explainer: 'safe_plan_draft',
    safe_plan_builder: 'safe_plan_draft',
    code_prompt_builder: 'codex_prompt_draft',
    memory_policy_preview: 'memory_action_preview',
    model_hub_review: 'model_routing_summary',
    vision_review_plan: 'ui_review_plan',
    vision_to_code_prompt: 'codex_prompt_draft',
    research_plan: 'research_plan',
    command_approval_preview: 'command_approval_preview',
    approval_review: 'command_approval_preview',
  };
  return {
    id: decision.artifactId,
    type: typeByRoute[decision.routeId],
    status: 'preview-only',
    request: decision.request,
    safetyFlags: NO_ACTION_FLAGS,
  };
}

function buildTraceItems(decision: OperatorDecisionPreview): OperatorTraceItem[] {
  return [
    ['request_received', 'done'],
    ['intent_preview_generated', 'done'],
    ['route_selected', 'done'],
    ['model_candidate_selected', 'info'],
    ['permission_boundary_evaluated', decision.approvalNeeded ? 'blocked' : 'done'],
    ['cloud_boundary_evaluated', decision.researchBoundaryRequired ? 'blocked' : 'done'],
    ['memory_policy_evaluated', decision.memoryActionProposed ? 'blocked' : 'done'],
    ['artifact_draft_created', 'done'],
    ['blocked_actions_not_performed', 'blocked'],
  ].map(([step, status]) => ({
    id: `${decision.id}-${step}`,
    step: step as OperatorTraceItem['step'],
    status: status as OperatorTraceItem['status'],
  }));
}

function classifyOperatorIntents(request: string): OperatorIntent[] {
  const text = normalizeRequest(request);
  const intents = new Set<OperatorIntent>();
  if (hasAny(text, ['screenshot', 'image', 'visual', 'vision', 'gorsel', 'görsel', 'ekran goruntusu', 'ekran görüntüsü', 'ui bozuk', 'ui sorunu', 'ui issue', 'arayuz', 'arayüz'])) {
    intents.add('vision_review');
  }
  if (hasAny(text, ['codex prompt', 'kod', 'code', 'diff', 'test', 'pr', 'repo', 'patch'])) {
    intents.add('code_prompt');
  }
  if (hasAny(text, ['hatirla', 'hatırla', 'unut', 'hafiza', 'hafıza', 'memory', 'remember', 'forget'])) {
    intents.add('memory_action');
  }
  if (hasAny(text, ['web', 'arastir', 'araştır', 'internet', 'kaynak', 'source', 'research'])) {
    intents.add('web_research');
  }
  if (hasAny(text, ['model', 'lm studio', 'qwen', 'gemma', 'deepseek', 'openrouter', 'moonshot', 'kimi', 'model hub'])) {
    intents.add('model_hub');
  }
  if (hasAny(text, ['komut', 'calistir', 'çalıştır', 'execute', 'shell', 'terminal', 'run '])) {
    intents.add('command_preview');
  }
  if (hasAny(text, ['onay', 'approval', 'approve', 'permission', 'izin'])) {
    intents.add('approval_review');
  }
  if (hasAny(text, ['plan', 'sprint', 'next step', 'sonraki', 'safe', 'guvenli', 'güvenli'])) {
    intents.add('safe_plan');
  }
  if (hasAny(text, ['status', 'durum', 'health', 'nedir', 'explain', 'acikla', 'açıkla'])) {
    intents.add('ask_status');
  }
  if (!intents.size) intents.add('ask_status');
  return Array.from(intents);
}

function choosePrimaryIntent(intents: OperatorIntent[]): OperatorIntent {
  const priority: OperatorIntent[] = [
    'command_preview',
    'vision_review',
    'code_prompt',
    'memory_action',
    'web_research',
    'model_hub',
    'approval_review',
    'safe_plan',
    'ask_status',
  ];
  return priority.find((intent) => intents.includes(intent)) ?? 'unknown';
}

function chooseRouteId(intents: OperatorIntent[], primaryIntent: OperatorIntent): OperatorRouteId {
  if (intents.includes('vision_review') && intents.includes('code_prompt')) return 'vision_to_code_prompt';
  if (primaryIntent === 'vision_review') return 'vision_review_plan';
  if (primaryIntent === 'code_prompt') return 'code_prompt_builder';
  if (primaryIntent === 'memory_action') return 'memory_policy_preview';
  if (primaryIntent === 'web_research') return 'research_plan';
  if (primaryIntent === 'model_hub') return 'model_hub_review';
  if (primaryIntent === 'command_preview') return 'command_approval_preview';
  if (primaryIntent === 'approval_review') return 'approval_review';
  if (primaryIntent === 'safe_plan') return 'safe_plan_builder';
  return 'status_explainer';
}

function chooseModelCandidates(intents: OperatorIntent[], primaryIntent: OperatorIntent): OperatorModelCandidate[] {
  const candidates: OperatorModelCandidate[] = [];
  if (intents.includes('vision_review')) {
    candidates.push({ profileId: 'vision_review', modelHint: 'qwen/qwen3-vl-8b' });
  }
  if (intents.includes('code_prompt')) {
    candidates.push({ profileId: 'coding_review', modelHint: 'qwen2.5-coder-14b-instruct' });
  }
  if (primaryIntent === 'web_research') {
    candidates.push({ profileId: 'rerank_only', modelHint: 'qwen3-reranker-0.6b' });
  }
  if (primaryIntent === 'safe_plan' || primaryIntent === 'approval_review') {
    candidates.push({ profileId: 'reasoning_review', modelHint: 'deepseek-r1-distill-qwen-14b' });
  }
  if (!candidates.length) {
    candidates.push({ profileId: 'default_proposal', modelHint: 'google/gemma-4-12b' });
  }
  return uniqueCandidates(candidates);
}

function uniqueCandidates(candidates: OperatorModelCandidate[]): OperatorModelCandidate[] {
  const seen = new Set<string>();
  return candidates.filter((candidate) => {
    if (seen.has(candidate.profileId)) return false;
    seen.add(candidate.profileId);
    return true;
  });
}

function hasAny(text: string, keywords: string[]): boolean {
  return keywords.some((keyword) => text.includes(normalizeRequest(keyword)));
}

function normalizeRequest(request: string): string {
  return request
    .toLocaleLowerCase('tr-TR')
    .normalize('NFKD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/ı/g, 'i');
}

function stablePreviewId(value: string): string {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = ((hash << 5) - hash + value.charCodeAt(index)) | 0;
  }
  return Math.abs(hash).toString(36);
}
