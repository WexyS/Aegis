# Aegis Model Hub

Decision: `AEGIS_MODEL_HUB_LM_STUDIO_READY`

## Scope

Aegis Model Hub is the user-facing surface for local model status, explicit LM
Studio probing, and explicit proposal-only local model completion.

It is not an autonomous model router, not a cloud provider broker, not model
execution permission, and not a truth source. The current implementation uses
the existing Model Gateway boundary for any explicit local LM Studio probe or
completion.

## Product Surface

Model Hub adds:

- `GET /model-hub/status`
- a Settings panel that displays LM Studio/Model Gateway configuration status
- an explicit `Probe LM Studio` action
- an explicit local proposal test composer
- visible non-authority and no-execution badges

The status endpoint is configuration and registry projection only. It does not
probe LM Studio, call a model, write memory, execute tools, mutate files, create
evidence, create verifier success, or edit environment files.

## Status Projection

`GET /model-hub/status` combines:

- `build_model_gateway_status()`
- `build_orchestrator_readiness()`
- sanitized Model Hub integration registry records
- Mode Policy summary

The LM Studio summary includes provider, base URL, host, enabled state, model
configuration state, failure reasons, and whether a live probe is still required
for live provider health.

Important boundary: configured metadata is not live provider proof.

## User-Triggered Probe

The frontend does not probe automatically. The `Probe LM Studio` button calls
`POST /model-gateway/probe`, which performs a bounded local `GET /v1/models`
only when the gateway is enabled and the configured URL is local and valid.

Disabled, misconfigured, unavailable, timeout, and error states remain
structured and visible.

## User-Triggered Proposal

The local proposal composer calls `POST /model-gateway/complete` only when the
operator clicks the send button.

The frontend sends a small safe metadata prompt:

- LM Studio configuration status
- Model Hub record identifiers and execution statuses
- integration family counts
- mode names and current execution grant flags
- non-authority rules

It does not send raw logs, raw journals, raw evidence, secrets, tokens, API
keys, repo content, or full upstream registry URLs.

Model output remains proposal-only. It is not truth, evidence, verifier
success, approval, permission, memory, or execution.

## Local Model Profiles And Resource Guardrails

Model Hub status includes static local profile recommendations for the current
operator hardware target: NVIDIA RTX 4080 with 12 GB VRAM and 32 GB RAM.

The current local-first recommendation order is:

- `fast_summary`: `qwen/qwen3.5-9b`, low memory pressure, short summaries
- `default_proposal`: `google/gemma-4-12b`, balanced default proposal profile
- `coding_review`: `qwen2.5-coder-14b-instruct`, manual coding review profile
- `reasoning_review`: `deepseek-r1-distill-qwen-14b`, manual reasoning review
- `heavy_experiment`: `gpt-oss-20b`, manual high-memory-pressure experiment
- `rerank_only`: `qwen3-reranker-0.6b`, rerank/search only, not completion safe

These profiles are recommendations only. They do not prove a model is installed,
loaded, live, fast, safe, or correct. Exact local model ids must still be
verified from LM Studio `/v1/models`, and the UI never switches models or edits
environment variables automatically.

The active profile match is based only on the configured
`AEGIS_LM_STUDIO_MODEL` metadata from Model Gateway status. A reranker-like
configured model is shown with a completion-safety warning.

## External Provider Readiness

Model Hub status also includes external provider readiness metadata for
OpenRouter, DeepSeek API, OpenAI, Anthropic, and Gemini.

Readiness checks only whether expected API key environment variables are
present. Key values are never exposed. Key presence is not authorization, not
approval, not privacy acceptance, not cost acceptance, and not execution
permission.

Cloud completion remains disabled. Automatic cloud fallback remains disabled.
Future external use requires External Provider Broker with explicit provider
enablement, exact provider/model selection, prompt preview, privacy warning,
cost warning, no secrets, and proposal-only output.

The current External Provider Broker Boundary adds only a dry-run provider setup
and prompt preview envelope. It does not call providers, expose key values,
send prompt payloads, enable cloud fallback, or grant approval/capability
leases. See `docs/external-provider-readiness.md` for readiness metadata and
`docs/external-provider-broker-boundary.md` for the broker preview boundary.

## Rendered Flow QA Notes

The Settings surface is expected to load Model Hub status automatically without
probing or completing. The rendered panel must keep disabled and misconfigured
states visible, including backend failure reasons and warnings.

The probe and local proposal actions are explicit operator actions. A rendered
status refresh must not call `POST /model-gateway/probe` or
`POST /model-gateway/complete`.

Broker preview actions must call only
`POST /model-hub/external-provider-preview`; that endpoint must keep
`would_call_provider=false`, `external_api_called=false`, and
`data_sent_external=false`.

The local proposal output is displayed with non-authority flags near the model
text so the UI does not imply truth, approval, verifier success, tool/MCP use,
shell/file mutation, or capability grants.

Live LM Studio smoke is environment-dependent. It should be run only when the
operator has already configured and started a local LM Studio/OpenAI-compatible
endpoint. If LM Studio is disabled, missing, or misconfigured, the correct
product behavior is a clear fail-closed state rather than a hidden fallback.

Operator setup and smoke commands are documented in
`docs/model-hub-operator-setup.md`. The optional helper script
`scripts/model_hub_live_smoke.py` calls only the local Aegis API, defaults to a
status-only check, and requires explicit `--live --complete
--confirm-local-lm-studio` flags before it asks the backend to perform a local
proposal-only completion.

## Configuration

The UI reads backend-reported configuration. It does not write `.env`, modify
settings files, store secrets, configure provider keys, or change model
provider routing.

Model Gateway configuration remains controlled outside the UI through existing
settings and environment variables.

## No Cloud Fallback

OpenRouter, DeepSeek, and other external/cloud provider records remain blocked
or metadata-only in the Integration Registry. Model Hub does not infer cloud
permission from those records and does not create a cloud fallback path.

## Relationship To Model Gateway

Model Gateway is the narrow backend/API boundary that can perform a local LM
Studio probe or local OpenAI-compatible completion after validation.

Model Hub is the product surface that presents this boundary and invokes those
existing endpoints only through explicit user actions.

Model Hub must not bypass Model Gateway with direct provider calls.

## Relationship To Orchestrator And Mode Policy

Orchestrator readiness and Mode Policy are displayed as metadata. They do not
grant execution, cloud routing, tool execution, agent execution, workflow
execution, computer control, approval, lease, capability, evidence, or verifier
success.

## Safety Invariants

Model Hub preserves:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_model_hub`
- `evidence_created=false`
- `verifier_success=false`
- `approval_granted=false`
- `capability_lease_granted=false`
- `provider_probe_performed=false` on status
- `http_request_performed=false` on status
- `model_call_performed=false` on status
- `memory_write_performed=false`
- `tool_call_performed=false`
- `agent_execution_performed=false`
- `workflow_execution_performed=false`
- `computer_control_performed=false`
- `external_api_called=false`
- `data_sent_external=false`
- `config_mutation_allowed=false`

Probe and completion responses use the Model Gateway non-authority envelope.

## Tests

Coverage includes:

- Model Hub status endpoint when the gateway is disabled
- configured metadata projection without LM Studio probing
- no provider probe, HTTP request, model call, execution, memory write, tool
  call, agent execution, workflow execution, computer control, external API, or
  data sent from the status endpoint
- sanitized Model Hub integration records without upstream URLs
- blocked external/cloud provider records remain blocked
- Mode Policy does not grant execution

## Intentionally Not Done

- No automatic provider probing
- No automatic model completion
- No cloud provider routing
- No external provider completion calls
- No automatic cloud fallback
- No model provider key management
- No `.env` or settings mutation from the UI
- No transcript persistence
- No memory write
- No tool, plugin, workflow, agent, MCP, shell, browser, or computer execution
- No evidence or verifier success creation

## Remaining Risks

- LM Studio availability, loaded model names, latency, context limits, and local
  resources remain operator-environment specific.
- Prompt privacy still depends on the caller keeping the proposal prompt small
  and safe.
- The UI does not yet provide a full local model inventory manager.
- Future provider expansion must keep local/cloud boundaries explicit and must
  not infer permission from registry metadata.
