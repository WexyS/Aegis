import { create } from 'zustand';

import { previewOperatorRoute } from '@/lib/api';
import type {
  OperatorArtifact,
  OperatorArtifactType,
  OperatorBackendRoutePreview,
  OperatorDecisionPreview,
  OperatorIntent,
  OperatorModelCandidate,
  OperatorPermissionMode,
  OperatorPreviewSource,
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
  previewSource: OperatorPreviewSource;
  backendPreviewAvailable: boolean;
  backendPreviewError: string | null;
  setComposerText: (value: string) => void;
  clearOperatorSession: () => void;
  selectArtifact: (artifactId: string) => void;
  submitPreviewRequest: (request?: string) => Promise<OperatorDecisionPreview | null>;
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
  'no_external_provider_call',
  'no_kimi_moonshot_call',
  'no_image_upload',
  'no_video_upload',
  'no_memory_write',
  'no_tool_call',
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
  previewSource: 'frontend_fallback',
  backendPreviewAvailable: false,
  backendPreviewError: null,
  setComposerText: (value) => set({ composerText: value }),
  clearOperatorSession: () => set({
    composerText: '',
    lastDecision: null,
    traceItems: [],
    artifacts: [],
    selectedArtifactId: null,
    previewSource: 'frontend_fallback',
    backendPreviewAvailable: false,
    backendPreviewError: null,
  }),
  selectArtifact: (artifactId) => set({ selectedArtifactId: artifactId }),
  submitPreviewRequest: async (request) => {
    const text = (request ?? get().composerText).trim();
    if (!text) return null;
    let decision: OperatorDecisionPreview;
    let artifact: OperatorArtifact;
    let traceItems: OperatorTraceItem[];

    try {
      const backendPreview = await previewOperatorRoute(text);
      decision = mapBackendDecisionPreview(backendPreview);
      artifact = mapBackendArtifact(backendPreview);
      traceItems = backendPreview.trace_items.map((item) => ({
        id: item.id,
        step: item.step,
        status: item.status,
        detail: item.detail,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Backend preview unavailable.';
      decision = buildDecisionPreview(text, {
        previewSource: 'frontend_fallback',
        backendPreviewAvailable: false,
        backendPreviewError: message,
      });
      artifact = buildArtifact(decision);
      traceItems = buildTraceItems(decision);
    }

    set((state) => ({
      composerText: text,
      lastDecision: decision,
      traceItems,
      artifacts: [artifact, ...state.artifacts.filter((item) => item.id !== artifact.id)].slice(0, 6),
      selectedArtifactId: artifact.id,
      previewSource: decision.previewSource,
      backendPreviewAvailable: decision.backendPreviewAvailable,
      backendPreviewError: decision.backendPreviewError,
    }));
    return decision;
  },
}));

function buildDecisionPreview(
  request: string,
  source: {
    previewSource: OperatorPreviewSource;
    backendPreviewAvailable: boolean;
    backendPreviewError: string | null;
  } = {
    previewSource: 'frontend_fallback',
    backendPreviewAvailable: false,
    backendPreviewError: null,
  },
): OperatorDecisionPreview {
  const intents = classifyOperatorIntents(request);
  const primaryIntent = choosePrimaryIntent(intents);
  const routeId = chooseRouteId(intents, primaryIntent);
  const id = `operator-preview-${stablePreviewId(`${routeId}:${request}`)}`;
  return {
    id,
    contract: 'aegis-operator-auto-router-preview',
    status: 'preview_only',
    routerMode: 'deterministic_preview',
    previewSource: source.previewSource,
    backendPreviewAvailable: source.backendPreviewAvailable,
    backendPreviewError: source.backendPreviewError,
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

function mapBackendDecisionPreview(backendPreview: OperatorBackendRoutePreview): OperatorDecisionPreview {
  return {
    id: backendPreview.preview_id,
    contract: backendPreview.contract,
    status: backendPreview.status,
    routerMode: backendPreview.router_mode,
    previewSource: 'backend_contract',
    backendPreviewAvailable: true,
    backendPreviewError: null,
    request: backendPreview.request,
    intents: backendPreview.intents,
    primaryIntent: backendPreview.primary_intent,
    routeId: backendPreview.route_id,
    modelCandidates: backendPreview.model_candidates.map((candidate) => ({
      profileId: candidate.profile_id,
      modelHint: candidate.model_hint,
      selectedForCall: candidate.selected_for_call,
      proposalOnly: candidate.proposal_only,
    })),
    cloudNeeded: backendPreview.cloud_needed,
    approvalNeeded: backendPreview.approval_needed,
    memoryActionProposed: backendPreview.memory_action_proposed,
    visionBoundaryRequired: backendPreview.vision_boundary_required,
    researchBoundaryRequired: backendPreview.research_boundary_required,
    artifactId: backendPreview.artifact.id,
    permissionMode: backendPreview.permission_mode,
    safety: {
      commandExecutionPerformed: backendPreview.command_execution_performed,
      modelCallPerformed: backendPreview.model_call_performed,
      cloudCallPerformed: backendPreview.cloud_call_performed,
      imageUploadPerformed: backendPreview.image_upload_performed,
      memoryWritePerformed: backendPreview.memory_write_performed,
      evidenceCreated: backendPreview.evidence_created,
      verifierSuccessCreated: backendPreview.verifier_success,
      approvalGranted: backendPreview.approval_granted,
      permissionGranted: backendPreview.permission_granted,
      backendAuthority: backendPreview.authority,
    },
  };
}

function mapBackendArtifact(backendPreview: OperatorBackendRoutePreview): OperatorArtifact {
  const mapped: OperatorArtifact = {
    id: backendPreview.artifact.id,
    type: backendPreview.artifact.type,
    status: 'preview-only',
    title: backendPreview.artifact.title,
    request: backendPreview.artifact.request,
    summary: backendPreview.artifact.summary,
    body: backendPreview.artifact.body,
    safetyFlags: backendPreview.artifact.safety_flags,
  };

  if (!mapped.body) {
    return { ...mapped, body: buildArtifactBody(mapped, mapBackendDecisionPreview(backendPreview)) };
  }

  return mapped;
}

function artifactTitle(type: OperatorArtifactType): string {
  const titles: Record<OperatorArtifactType, string> = {
    safe_plan_draft: 'Safe plan draft',
    codex_prompt_draft: 'Codex prompt draft',
    ui_review_plan: 'UI review plan',
    research_plan: 'Research plan',
    memory_action_preview: 'Memory action preview',
    model_routing_summary: 'Model routing summary',
    command_approval_preview: 'Command approval preview',
  };
  return titles[type];
}

function artifactSummary(type: OperatorArtifactType): string {
  const summaries: Record<OperatorArtifactType, string> = {
    safe_plan_draft: 'A bounded plan outline with validation and explicit not-done boundaries.',
    codex_prompt_draft: 'A draft prompt for a future Codex handoff, not a patch or execution result.',
    ui_review_plan: 'A UI review checklist that requires a future Vision Input Boundary for images.',
    research_plan: 'A source plan that would require an external research boundary before live web use.',
    memory_action_preview: 'A memory lifecycle proposal that would require explicit approve/reject/delete controls.',
    model_routing_summary: 'A model profile summary that does not prove any model is loaded or live.',
    command_approval_preview: 'A command safety preview that blocks execution until backend-owned approval and verifier gates exist.',
  };
  return summaries[type];
}

function buildArtifactBody(artifact: OperatorArtifact, decision: OperatorDecisionPreview): string {
  const selectedRoute = decision.routeId.replaceAll('_', ' ');
  const intents = decision.intents.join(', ');
  const modelCandidates = decision.modelCandidates
    .map((candidate) => `${candidate.profileId}: ${candidate.modelHint}`)
    .join('\n');
  const boundaryLines = [
    `Route: ${selectedRoute}`,
    `Intent preview: ${intents}`,
    `Model candidate metadata:\n${modelCandidates}`,
    `Approval required before any action: ${decision.approvalNeeded ? 'yes' : 'no'}`,
    `Memory action proposed: ${decision.memoryActionProposed ? 'yes, review-only' : 'no'}`,
    `Vision boundary required: ${decision.visionBoundaryRequired ? 'yes' : 'no'}`,
    `External research boundary required: ${decision.researchBoundaryRequired ? 'yes' : 'no'}`,
  ];

  if (artifact.type === 'codex_prompt_draft') {
    return [
      'Draft Codex handoff',
      '',
      `User request: ${artifact.request}`,
      '',
      'Goal:',
      '- Inspect the relevant Aegis files first.',
      '- Keep the change narrow and truth-safe.',
      '- Preserve backend-owned authority, approvals, evidence, verifier semantics, and runtime state.',
      '- Validate with focused tests and report commit/push separately.',
      '',
      'Preview metadata:',
      ...boundaryLines.map((line) => `- ${line}`),
      '',
      'Not performed by this preview:',
      '- no command execution',
      '- no model call',
      '- no cloud call',
      '- no memory write',
      '- no evidence or verifier success',
    ].join('\n');
  }

  if (artifact.type === 'command_approval_preview') {
    return [
      'Command approval preview',
      '',
      `Requested action: ${artifact.request}`,
      '',
      'This is blocked at preview level. A future executable action would need:',
      '- backend policy evaluation',
      '- explicit operator approval',
      '- scoped capability permission',
      '- evidence expectations',
      '- verifier postconditions',
      '',
      'No command was dispatched from this shell.',
    ].join('\n');
  }

  if (artifact.type === 'memory_action_preview') {
    return [
      'Memory lifecycle preview',
      '',
      `Request: ${artifact.request}`,
      '',
      'Aegis can only present this as a candidate lifecycle item here.',
      'Persistent memory would require explicit approve/reject/delete controls and sensitivity review.',
      '',
      'No memory write was performed.',
    ].join('\n');
  }

  if (artifact.type === 'model_routing_summary') {
    return [
      'Model routing summary',
      '',
      `Request: ${artifact.request}`,
      '',
      'Candidate profiles:',
      modelCandidates,
      '',
      'This does not prove the model is loaded, healthy, selected, or called.',
      'Model output would remain proposal-only.',
    ].join('\n');
  }

  if (artifact.type === 'research_plan') {
    return [
      'External research boundary plan',
      '',
      `Request: ${artifact.request}`,
      '',
      'Before live research, Aegis would need explicit source policy, privacy review, provider boundary, and citation/provenance requirements.',
      'No web query, browser fetch, API call, or external data transfer occurred.',
    ].join('\n');
  }

  if (artifact.type === 'ui_review_plan') {
    return [
      'UI review plan',
      '',
      `Request: ${artifact.request}`,
      '',
      'Review focus:',
      '- visual hierarchy',
      '- clickability and focus behavior',
      '- responsive layout',
      '- truthful runtime/debt labels',
      '- no hidden authority in frontend state',
      '',
      'Image/vision handling remains future-gated unless explicitly scoped.',
    ].join('\n');
  }

  return [
    'Safe plan draft',
    '',
    `Request: ${artifact.request}`,
    '',
    'Suggested next steps:',
    '- inspect the existing implementation and contracts',
    '- identify the smallest safe change',
    '- preserve runtime, approval, evidence, verifier, model, memory, and tool boundaries',
    '- add focused validation',
    '- report what changed and what stayed intentionally out of scope',
    '',
    'Preview metadata:',
    ...boundaryLines.map((line) => `- ${line}`),
  ].join('\n');
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
  const type = typeByRoute[decision.routeId];
  const artifact: OperatorArtifact = {
    id: decision.artifactId,
    type,
    status: 'preview-only',
    title: artifactTitle(type),
    summary: artifactSummary(type),
    request: decision.request,
    safetyFlags: NO_ACTION_FLAGS,
  };
  return {
    ...artifact,
    body: buildArtifactBody(artifact, decision),
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
  if (hasAny(text, ['codex prompt', 'kod', 'code', 'diff', 'test', 'pull request', 'github pr', 'repo', 'patch'])) {
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
