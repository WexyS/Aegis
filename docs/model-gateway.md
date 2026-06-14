# Model Gateway

Decision: `LOCAL_MODEL_GATEWAY_LM_STUDIO`

Current status: implemented as a bounded local model-call boundary for explicit
LM Studio/OpenAI-compatible local endpoint use. The historical decision name is
retained for traceability; public product wording should use Model Gateway.

## Scope

Model Gateway adds a bounded local model-call boundary for Aegis. It supports
LM Studio through the local OpenAI-compatible HTTP API only.

This is a backend/API capability. The user-facing Model Hub panel may call this
boundary through explicit operator actions, but the gateway itself does not add
model-assisted Society, AutoPilot integration, Memory integration, Agent
Runtime integration, Skill Registry integration, cloud routing, hidden fallback,
evidence creation, verifier success, approval, lease, capability grants, tool
execution, MCP execution, shell execution, or file mutation.

## Why It Exists

The Hackathon baseline had real Memory, AutoPilot, Society, and Mission
Control surfaces, but no accepted model-call boundary. Model Gateway gives
model-assisted features one narrow local provider path with explicit
configuration, timeout handling, unavailable-state handling, and non-authority
response envelopes.

Existing deterministic RC flows must remain usable when LM Studio is disabled,
misconfigured, unavailable, slow, or returning malformed output.

## Provider Boundary

Supported provider:

- `lm_studio`

Allowed endpoint hosts:

- `127.0.0.1`
- `localhost`
- `::1`

Allowed base path:

- `/v1`

Rejected endpoint shapes include remote hosts, spoofed localhost domains,
credentials in URLs, query strings, fragments, and unsupported paths.

The gateway does not use older direct provider paths for new model-assisted
features. It does not silently fall back to cloud or another local provider.

## Configuration

Default settings are fail-closed:

- `model_gateway.enabled: false`
- `model_gateway.provider: lm_studio`
- `model_gateway.lm_studio_base_url: http://127.0.0.1:1234/v1`
- `model_gateway.lm_studio_model: not_configured`
- `model_gateway.timeout_seconds: 20.0`
- `model_gateway.max_input_chars: 8000`
- `model_gateway.max_output_tokens: 512`

Environment overrides:

- `AEGIS_MODEL_GATEWAY_ENABLED`
- `AEGIS_MODEL_PROVIDER`
- `AEGIS_LM_STUDIO_BASE_URL`
- `AEGIS_LM_STUDIO_MODEL`
- `AEGIS_MODEL_TIMEOUT_SECONDS`
- `AEGIS_MODEL_MAX_INPUT_CHARS`
- `AEGIS_MODEL_MAX_OUTPUT_TOKENS`

Model calls require the gateway to be enabled and a concrete model name to be
configured. Provider metadata or endpoint availability is not permission.

## API Surface

Endpoints:

- `GET /model-gateway/status`
- `POST /model-gateway/probe`
- `POST /model-gateway/complete`

`/status` is configuration-only and does not perform a provider request.

`/probe` performs a bounded local `GET /v1/models` only when the gateway is
enabled and the local URL configuration is valid.

`/complete` performs a bounded local `POST /v1/chat/completions` only when the
gateway is enabled, the local URL configuration is valid, the model is
configured, the purpose is allowed, and input/output budgets pass.

## Allowed Purposes

The current gateway accepts only proposal-oriented purposes:

- `explanation`
- `summarization`
- `report_polish`
- `proposal_draft`
- `society_commentary`
- `autopilot_interpretation`
- `memory_candidate_refinement`

These purposes describe output intent only. They do not grant execution,
approval, verification, evidence, memory writes, or tool calls.

## Response Envelope

Every response preserves non-authority fields:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_model_gateway`
- `evidence=false`
- `evidence_provided_by_model=false`
- `verifier_success=false`
- `approval_granted=false`
- `permission_granted=false`
- `capability_lease_granted=false`
- `memory_output_is_authority=false`
- `model_output_is_truth=false`
- `model_output_is_evidence=false`
- `model_output_is_verifier_success=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

The completion output is proposal material only. It is not truth, proof,
evidence, verifier success, approval, lease, capability, runtime health, policy
truth, or execution permission.

## Failure Handling

Expected degraded statuses include:

- `disabled`
- `misconfigured`
- `blocked`
- `unavailable`
- `timeout`
- `error`

Unavailable providers, timeouts, HTTP errors, malformed response shapes, empty
model output, oversized input, unsupported purposes, missing prompts, and
invalid model configuration fail closed with structured failure reasons.

## Safety Boundaries

Model Gateway does not:

- write memory
- create evidence
- create verifier success
- mutate runtime, journal, evidence, or replay state
- call tools, MCP, shell, browser, or external APIs
- mutate files
- execute skills or agents
- route to cloud providers
- create hidden fallback output
- persist transcripts
- authorize AutoPilot, Society, Memory, or Agent Runtime behavior

Successful `/complete` requests do send the supplied prompt payload to the
configured local LM Studio endpoint. Callers must not send raw secrets, raw
journals, raw evidence, private context, or repo content unless a future
context-policy integration explicitly permits it.

## Manual LM Studio Smoke

Optional local smoke, only when the operator has LM Studio running with a known
local model:

1. Set `AEGIS_MODEL_GATEWAY_ENABLED=true`.
2. Set `AEGIS_LM_STUDIO_MODEL` to the LM Studio model id.
3. Start the backend.
4. Call `GET /model-gateway/status`.
5. Call `POST /model-gateway/probe`.
6. Call `POST /model-gateway/complete` with a small harmless prompt.

The expected success path is a proposal-only `completed` response with all
non-authority fields preserved. The expected unavailable path is structured
degraded output, not a hidden fallback.

## Tests

The test suite covers:

- disabled default status
- local endpoint URL acceptance
- remote/spoofed/malformed URL rejection
- structured unavailable provider response
- provider probe through mocked transport
- malformed probe response fail-closed behavior
- mocked completion success
- disabled and missing-model completion blocks
- timeout fail-closed behavior
- malformed completion response fail-closed behavior
- oversized input rejection before transport
- immutable config object
- API status/probe/complete behavior through mocked transport
- API remote URL rejection without provider call
- config dependency hygiene defaults

## Intentionally Not Done

- No hidden or automatic frontend Model Gateway call
- No model-assisted Society model-assisted commentary
- No AutoPilot model-assisted interpretation
- No Memory candidate refinement integration
- No Agent Runtime or Skill Registry wiring
- No cloud provider routing
- No provider retry loop
- No transcript persistence
- No context package integration
- No live LM Studio smoke requirement
- No UI-driven `.env` or provider configuration mutation

## Remaining Risks

- LM Studio availability, model names, local resource pressure, and model
  quality are environment-specific.
- Prompt privacy still depends on future context-policy integration.
- The API remains intentionally narrow; the Model Hub UI must keep prompts small
  and safe.
- Future integrations must preserve the same non-authority envelope and must
  not bypass Model Gateway through older direct provider paths.
