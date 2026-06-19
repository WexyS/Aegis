# External Provider Broker Boundary

## Decision

Decision: `AEGIS_MODEL_HUB_PROVIDER_BROKER_BOUNDARY_READY`

External Provider Broker Boundary is the dry-run safety layer for future
operator-selected cloud or external model providers. It is not provider
integration, not cloud routing, not a model call, and not permission to send
data outside the machine.

Qwen 3 VL 8B is tracked separately as a local vision profile candidate. It does
not enable automatic screenshot/image routing. Screenshots and images require a
future explicit Vision Input Boundary before any automatic image path can exist.

## Scope

This boundary represents:

- provider setup guidance from existing readiness metadata
- operator-managed environment variable placeholders
- prompt preview and heuristic risk markers
- required operator acknowledgements for future broker use
- explicit disabled state for provider calls, cloud routing, and automatic
  fallback

It does not store keys, read key values into the UI, edit `.env`, call provider
APIs, add provider SDKs, run model completions, or create evidence/verifier
success.

## Current Provider Setup Guidance

The Model Hub may show placeholder commands for:

- OpenRouter: `AEGIS_OPENROUTER_API_KEY`, `AEGIS_OPENROUTER_MODEL`
- DeepSeek API: `AEGIS_DEEPSEEK_API_KEY`, `AEGIS_DEEPSEEK_MODEL`
- OpenAI: `AEGIS_OPENAI_API_KEY`, `AEGIS_OPENAI_MODEL`
- Anthropic: `AEGIS_ANTHROPIC_API_KEY`, `AEGIS_ANTHROPIC_MODEL`
- Gemini: `AEGIS_GEMINI_API_KEY`, `AEGIS_GEMINI_MODEL`

These are placeholders only. API key presence is boolean metadata and is never
authorization, cost acceptance, privacy acceptance, provider health, model
availability, or execution permission.

Cloud provider usage remains disabled unless a future broker/live-call sprint
explicitly enables it. No automatic cloud fallback exists.

## Prompt Preview Boundary

`POST /model-hub/external-provider-preview` returns a preview-only envelope.
The endpoint:

- accepts provider, optional model id, purpose, prompt, and operator
  acknowledgements
- redacts obvious secret-like prompt fragments in the displayed preview
- reports heuristic risk markers for secrets, raw journals, raw evidence,
  runtime logs, repo dumps, dependency/cache paths, and stack traces
- always keeps `would_call_provider=false`
- always keeps `external_api_called=false`, `model_call_performed=false`, and
  `data_sent_external=false`

The preview is not permission. Even when all acknowledgements are present, the
current result remains blocked until a future External Provider Broker
implementation exists.

## Required Future Acknowledgements

Future external provider use must require at least:

- cost warning acknowledgement
- privacy warning acknowledgement
- prompt preview review
- no-secrets confirmation
- proposal-only output acknowledgement

These acknowledgements are not approval, not a capability lease, and not
execution permission in this sprint.

## UI Rules

The Model Hub UI may display provider setup placeholders and run the dry-run
preview endpoint. It must not:

- render API key input fields
- save API keys
- reveal key values
- edit environment files
- show a "send to cloud" action
- infer authorization from key presence
- call cloud providers
- create model output authority

## Safety Invariants

The boundary preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_external_provider_broker_boundary`
- `provider_key_value_exposed=false`
- `cloud_call_performed=false`
- `external_api_called=false`
- `http_request_performed=false`
- `model_call_performed=false`
- `prompt_payload_sent=false`
- `data_sent_external=false`
- `memory_write_performed=false`
- `tool_call_performed=false`
- `mcp_call_performed=false`
- `plugin_execution_performed=false`
- `agent_execution_performed=false`
- `evidence_created=false`
- `verifier_success=false`
- `approval_granted=false`
- `capability_lease_granted=false`
- `mutation_performed=false`
- `frontend_authority=false`

## Relationship To Existing Layers

External Provider Readiness remains metadata-only. It reports provider names,
expected env vars, and key presence booleans.

Model Hub presents the boundary and preview endpoint, but does not bypass Model
Gateway and does not add provider routing.

Model Gateway remains the only implemented model-call boundary, and it is local
LM Studio/OpenAI-compatible only.

Mode Policy and Orchestrator readiness remain metadata and do not grant cloud
routing.

Deleted Memory records are hidden by default in the normal Mission Control UI
and are visible only through an explicit show-deleted audit toggle. Deleted
records remain non-active and do not grant authority.

## Intentionally Not Done

- No external provider API calls
- No provider SDKs
- No cloud fallback
- No provider authentication
- No key storage
- No `.env` writer
- No cloud model completion
- No transcript persistence
- No memory write
- No tool, MCP, plugin, workflow, shell, browser, computer, or agent execution
- No evidence or verifier success
- No approval or capability lease grant

## Remaining Risks

- Heuristic prompt risk markers are conservative hints, not complete data-loss
  prevention.
- Future broker implementation still needs explicit provider enablement,
  purpose policy, redaction policy, cost policy, privacy policy, auditability,
  and proposal-only output validation.
- Key presence cannot prove provider health, region/terms acceptance, billing
  status, account limits, model availability, latency, or quality.
