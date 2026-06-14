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
