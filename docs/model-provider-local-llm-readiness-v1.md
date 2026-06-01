# Model Provider / Local LLM Readiness v1

## 1. Decision

- Decision: `MODEL_PROVIDER_READINESS_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T03:06:00+03:00`
- Repository checkpoint before sprint: `96d6503385dd6774d5e5f1c8a88f66f3761f154e`
- Foundation tag: `foundation-v1-baseline`

This sprint defines the future model provider readiness contract. It does not
call, probe, download, install, move, delete, load, route, or execute any model.
It does not implement a provider endpoint, model router, chat surface, intent
classifier, planner, tool connection, memory mutation, dataset export, adapter,
or runtime behavior change.

## 2. Provider Classes

| Provider class | Location | Privacy risk | Network requirement | Storage expectation | Health check expectation | Timeout/failure behavior | Allowed future use | Forbidden current use | Disk-critical use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lm_studio_local` | local | local data boundary, provider logs still sensitive | localhost only | external LM Studio model root, outside repo | metadata/endpoint health only in future | structured unavailable/timeout/OOM | local generation after gates | no probing or calls now | blocked while disk is critical unless storage path approved |
| `ollama_local` | local | local data boundary, provider logs still sensitive | localhost only | external Ollama model root, outside repo | metadata/endpoint health only in future | structured unavailable/timeout/OOM | local generation after gates | no probing or calls now | blocked while disk is critical unless storage path approved |
| `openai_compatible_local` | local or LAN | depends on endpoint owner and network boundary | local/LAN endpoint | endpoint reference, no repo model weights | metadata/endpoint health only in future | structured unreachable/auth/timeout/OOM | local-compatible provider after gates | no probing or calls now | blocked if model storage or cache growth is unknown |
| `remote_api_provider` | remote | high; data leaves device | external network | no local model weights, possible cache/log records | auth, quota, privacy, and reachability health only in future | structured auth/rate/timeout/policy failures | remote proposal generation after privacy gates | no remote calls now | not blocked by local model disk, but blocked by privacy/policy gates |
| `mock_provider_for_tests` | test-only | no real data by default | none | no model weights | deterministic fake metadata only | deterministic structured failures | contract and failure tests | no production routing | allowed only as test fixture, not runtime truth |
| `offline_disabled_provider` | none | none | none | none | always disabled | `disabled` / `provider_unavailable` | explicit disabled state | no generation | allowed as safe default |

Provider availability is not permission. Provider readiness is not generation
success. Generation success is not verification success.

## 3. Model Metadata Contract

Future model descriptors should include:

- `provider_id`
- `provider_type`
- `provider_location`
- `model_id`
- `model_name`
- `model_family`
- `model_version`
- `model_format`
- `quantization`
- `parameter_size`
- `context_window`
- `input_modalities`
- `output_modalities`
- `supports_tool_calling`
- `supports_json_mode`
- `supports_vision`
- `supports_embeddings`
- `supports_streaming`
- `local_path_or_endpoint_ref`
- `privacy_class`
- `cost_class`
- `estimated_disk_gb`
- `estimated_vram_gb`
- `max_tokens`
- `license_notes`
- `provenance_refs`

Metadata is descriptive only. It cannot grant approval, capability, lease,
execution permission, evidence, verifier success, runtime truth, policy truth,
or model routing authority.

## 4. Provider Health Contract

Future health states:

- `unknown`
- `unavailable`
- `disabled`
- `reachable`
- `degraded`
- `ready_for_metadata_only`
- `ready_for_generation`
- `blocked_by_disk_pressure`
- `blocked_by_policy`
- `blocked_by_privacy`
- `blocked_by_missing_model`
- `timeout`
- `oom`
- `error`

Rules:

- Health check success is not generation success.
- Generation success is not verification success.
- Provider ready is not permission.
- Model available is not tool or action permission.
- Timeout, OOM, unavailable, policy-blocked, and privacy-blocked states remain
  structured failures.
- Fallback may not erase the original provider failure.
- Health diagnostics must remain read-only until a future explicit provider
  integration sprint.

## 5. Local and Remote Privacy Boundary

Local model use can keep data on the device, but still requires audit,
provenance, prompt/output handling, and provider log controls.

Remote model use requires:

- explicit data/privacy policy
- remote-provider policy gate
- redaction policy
- secret/token handling
- user/project data boundary
- cost and retention disclosure
- provider identity and model id logging

Rules:

- User, project, tenant, or local workspace data must not be sent remotely
  without explicit policy.
- Secrets, tokens, personal data, screenshots, voice, and proprietary content
  must not be sent to any model without redaction/governance.
- Provider logs must not leak sensitive prompts, context packages, paths,
  credentials, or outputs.
- Local/remote provider choice must be policy-gated and explainable.

## 6. Resource and Storage Boundary

Current resource readiness:

- Disk usage is about `92.3%`, which is critical.
- LM Studio model storage already uses about `31.82 GB`.
- Ollama model path exists but is empty.
- Model weights should remain outside the Aegis repo.

Proposed resource rules:

| Rule | Threshold or requirement |
| --- | --- |
| Critical disk block | disk usage `>= 90%` blocks model downloads and local model expansion unless an external storage path is explicitly approved |
| Warning disk gate | disk usage `>= 80%` requires storage review before model expansion |
| Preferred free disk | at least `25%` free disk or explicit external storage path |
| Model storage path | external provider-managed path, not inside Aegis repo |
| Model cache growth | must be bounded, visible, and operator-reviewed |
| Model deletion/move | requires explicit operator confirmation |
| VRAM budgeting | future provider readiness must include estimated VRAM and OOM behavior |

Resource pressure is not permission to delete logs, journals, evidence,
snapshots, model weights, caches, datasets, or adapters. Cleanup remains a
separate operator-approved workstream.

## 7. Model Output Authority Boundary

Model output is not:

- command truth
- runtime truth
- policy truth
- approval
- evidence
- verifier success
- memory authority
- model routing authority
- capability grant
- capability lease
- execution permission
- frontend authority

Future model output must be wrapped as a proposal or result with:

- `authority=false`
- `execution_permission=not_granted_by_model`
- `capability_grant=false`
- `approval_grant=false`
- `lease_grant=false`
- `evidence_provided_by_model=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

Backend-owned parser, policy, lease, approval, verifier, evidence, journal, and
runtime authority checks remain mandatory.

## 8. Context Compiler Relationship

Compiled context may be passed to future model calls only after:

- provider readiness gates pass
- privacy checks pass
- policy checks pass
- explicit caller intent exists
- source refs and staleness markers are preserved

The Context Compiler package remains non-authoritative. Its contract metadata
must travel with future model request provenance. Raw journal remains excluded
by default. Known historical debt, unknown-era evidence labels, replay
diagnostics, and resource warnings must not be hidden by model prompts,
summaries, or outputs.

## 9. Training Governance Relationship

Model requests and responses are not automatically training data.

Rules:

- Provider logs do not become datasets automatically.
- Failures, timeouts, OOM, policy blocks, and privacy blocks are diagnostic
  records, not success examples.
- Generated examples remain `synthetic_unverified` until validated and
  reviewed.
- Failed actions cannot become success examples.
- Missing evidence cannot become verified.
- Unknown-era cannot become historical or success.
- Adapter/fine-tuning use requires dataset governance, redaction, eval,
  provenance, and rollback gates.

## 10. Model Router Relationship

This sprint does not implement a router.

Future router rules:

- Router may choose among providers only using policy, resource, privacy,
  capability, cost, and provenance metadata.
- A model cannot self-select its provider.
- A model provider recommendation is non-authoritative.
- Routing decisions must be logged and explainable.
- Local/remote changes must be policy-gated.
- Fallback must preserve the original failure state.
- Fallback cannot convert timeout, OOM, unavailable, or policy-blocked states
  into success.

## 11. Failure Taxonomy

Structured future failures:

- `provider_unavailable`
- `model_missing`
- `model_disabled`
- `endpoint_unreachable`
- `auth_missing`
- `auth_invalid`
- `timeout`
- `rate_limited`
- `oom`
- `insufficient_disk`
- `insufficient_vram`
- `context_too_large`
- `invalid_output_schema`
- `unsafe_output`
- `privacy_policy_blocked`
- `policy_blocked`
- `unknown_error`

Every failure should preserve provider id, model id when known, source refs,
privacy class, retry/fallback eligibility, and whether any output was produced.
No failure may be represented as verified success.

## 12. Future API / Contract Sketch

Documentation-only contract names:

- `ModelProviderDescriptor`
- `ModelDescriptor`
- `ModelProviderHealth`
- `ModelGenerationRequest`
- `ModelGenerationResult`
- `ModelFailure`
- `ModelUsageRecord`

Common fields:

- `schema_version`
- `provider_id`
- `provider_type`
- `provider_location`
- `model_id`
- `input_refs`
- `context_package_refs`
- `privacy_class`
- `cost_class`
- `resource_estimate`
- `failure_state`
- `generated_at`
- `authority=false`
- `execution_permission=not_granted_by_model`
- `evidence_provided_by_model=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

Generation requests should reference inputs and context packages by provenance,
not embed raw journal data by default. Generation results should carry schema
validation status, safety validation status, and structured failure metadata.

## 13. Gates Before First Real Model Call

Required gates:

1. Disk/resource gate resolved or external model storage approved.
2. Provider descriptor contract implemented.
3. Provider health check contract implemented and tested.
4. Timeout, OOM, unavailable, auth, and policy failure handling tested.
5. Privacy policy defined.
6. Redaction policy defined.
7. Model output schema validation implemented.
8. LLM authority boundary enforced.
9. Context Compiler read-only contract enforced.
10. Training governance accepted.
11. Policy/capability/lease relationship defined.
12. No-execution tests pass.
13. Fallback/failure tests pass.
14. No generated, model, dataset, adapter, or local environment artifacts are
    staged.

No model call should happen while these gates are absent.

## 14. Test Plan for Future Implementation

No tests are added in this documentation-only sprint because no type helper or
runtime surface is introduced.

When a pure provider contract helper is added, tests should assert:

- provider ready does not grant permission
- model metadata does not grant permission
- model output has `execution_permission=not_granted_by_model`
- timeout/OOM/unavailable remain failures
- disk pressure produces `blocked_by_disk_pressure`
- remote provider is blocked without privacy policy
- context package output remains non-authoritative
- fallback preserves original failure state
- model output cannot create evidence or verifier success
- model output cannot create approval, capability, or lease
- no model endpoint is called by contract tests

## 15. Non-Goals

- No local model call.
- No remote model call.
- No LM Studio/Ollama/OpenAI-compatible endpoint probe.
- No model install, download, move, load, or deletion.
- No model router.
- No model generation.
- No chat or intent-classification runtime behavior.
- No model output connected to execution, planning, tools, MCP, memory,
  plugins, skills, or vertical packs.
- No dataset, adapter, training export, benchmark, or model artifact.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  runtime health, backend, frontend, or API semantic change.

## 16. Remaining Risks

- Disk usage remains critical around `92.3%`.
- Existing local model storage is already large and outside the repo.
- Provider logs could leak sensitive prompts or context if not governed later.
- Remote provider usage is blocked until privacy and redaction policy exist.
- No empirical provider metadata or health data is collected in this sprint.

## 17. Recommended Next Workstream

Recommended next prompt:

`Model Lifecycle / VRAM Budget Design v1`

Reason: model provider readiness now has a non-authoritative contract. The next
safe design step is a lifecycle and resource budget model for installed models,
VRAM limits, OOM handling, and storage growth without calling or moving models.

Alternative:

`Memory Governance / Memory OS Design v1`

Use this if model/provider work should remain blocked until disk/resource
pressure is addressed.
