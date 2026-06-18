# Aegis Model Hub Operator Setup

## Decision

Decision: `AEGIS_MODEL_HUB_LM_STUDIO_SMOKE_READY`

This guide explains how an operator can configure and smoke-test Aegis Model
Hub with LM Studio through the existing local Model Gateway.

It is an operator setup guide, not a new execution capability. It does not
grant approval, verifier success, evidence, memory writes, tool execution,
plugin execution, agent execution, shell access, file mutation, or cloud
fallback.

## What Model Hub Uses

Model Hub displays backend-owned status from:

- `GET /model-hub/status`
- `GET /model-gateway/status`
- explicit `POST /model-gateway/probe`
- explicit `POST /model-gateway/complete`

Status refresh is metadata only. It does not probe LM Studio and does not call a
model. Probe and completion require explicit operator action.

## Required Local Setup

LM Studio must be running locally with its OpenAI-compatible server enabled.
Aegis accepts local Model Gateway base URLs such as:

- `http://127.0.0.1:1234/v1`
- `http://localhost:1234/v1`
- `http://[::1]:1234/v1`

Remote hosts, spoofed localhost names, credentials in URLs, query strings,
fragments, and unsupported paths are rejected by Model Gateway.

Configure Aegis outside the UI through existing settings or environment
variables:

- `AEGIS_MODEL_GATEWAY_ENABLED=true`
- `AEGIS_MODEL_PROVIDER=lm_studio`
- `AEGIS_LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1`
- `AEGIS_LM_STUDIO_MODEL=<exact LM Studio model id>`
- `AEGIS_MODEL_TIMEOUT_SECONDS=20`
- `AEGIS_MODEL_MAX_INPUT_CHARS=8000`
- `AEGIS_MODEL_MAX_OUTPUT_TOKENS=512`

Do not put API keys, tokens, secrets, raw journals, raw evidence, or private
repo content into Model Hub smoke prompts.

## Local Profile Recommendations

For the current operator hardware target, NVIDIA RTX 4080 with 12 GB VRAM and
32 GB RAM, Model Hub exposes static profile recommendations:

- `qwen/qwen3.5-9b`: fast summaries and low-resource explanations
- `google/gemma-4-12b`: default balanced proposal profile
- `qwen2.5-coder-14b-instruct`: manual coding review profile
- `deepseek-r1-distill-qwen-14b`: manual reasoning review profile
- `gpt-oss-20b`: heavy manual experiment; may spill to RAM/CPU on 12 GB VRAM
- `qwen3-reranker-0.6b`: rerank/search only, not proposal/completion safe

The configured model is not live proof. Use LM Studio `/v1/models` or the
explicit probe path to verify the exact loaded model id.

## External Provider Readiness

Aegis can display planned external provider readiness metadata, but it does not
call external providers yet.

API keys are operator-managed environment variables. Aegis does not store keys,
print keys, edit `.env`, or expose key values. It only reports key presence as
boolean readiness metadata.

Placeholder examples:

```powershell
$env:AEGIS_OPENROUTER_API_KEY="<paste-key-in-your-own-shell>"
$env:AEGIS_OPENROUTER_MODEL="<future-model-id>"
$env:AEGIS_DEEPSEEK_API_KEY="<paste-key-in-your-own-shell>"
$env:AEGIS_DEEPSEEK_MODEL="<future-model-id>"
$env:AEGIS_OPENAI_API_KEY="<paste-key-in-your-own-shell>"
$env:AEGIS_OPENAI_MODEL="<future-model-id>"
$env:AEGIS_ANTHROPIC_API_KEY="<paste-key-in-your-own-shell>"
$env:AEGIS_ANTHROPIC_MODEL="<future-model-id>"
$env:AEGIS_GEMINI_API_KEY="<paste-key-in-your-own-shell>"
$env:AEGIS_GEMINI_MODEL="<future-model-id>"
```

These variables are not used to call providers yet in this sprint. They are
readiness metadata only until a future live External Provider Broker is
implemented.

The current External Provider Broker Boundary can preview provider setup and a
redacted prompt envelope through `POST /model-hub/external-provider-preview`.
The preview remains blocked and must keep `would_call_provider=false`,
`external_api_called=false`, and `data_sent_external=false`.

Future cloud use requires explicit provider enablement, exact provider/model
selection, prompt preview, cost warning, privacy warning, no secrets, no raw
logs/journals/evidence/repo dumps by default, and proposal-only output.

## Disabled Smoke

With the gateway disabled, Model Hub should still load and explain the fail
closed state.

Expected result:

- `/model-hub/status` loads
- `/model-gateway/status` reports `disabled`
- `/model-gateway/probe` reports `disabled`
- `/model-gateway/complete` reports `disabled`
- no hidden fallback is used
- no evidence or verifier success is created

This is a successful disabled-path behavior, not a live LM Studio success.

## Configured Smoke

After the environment is configured and the backend is restarted:

1. Open the Model Hub panel.
2. Confirm status shows the local provider and configured model id.
3. Confirm status still says live provider health is not proved until probe.
4. Click `Probe LM Studio`.

Expected success path:

- probe response status is `ready`
- `provider_probe_performed=true`
- `http_request_performed=true`
- `model_call_performed=false`
- no memory/tool/MCP/shell/file mutation is performed

Expected fail-closed path:

- status is `unavailable`, `timeout`, `misconfigured`, or `error`
- failure reasons remain visible
- no cloud fallback is attempted

## Proposal-Only Completion Smoke

Completion is optional and should be done only after the operator confirms LM
Studio is local, running, and loaded with the intended model.

Use a small harmless prompt, for example:

```text
Summarize the current Aegis Model Hub state and recommend the safest next
operator step. Do not claim execution, approval, evidence, verifier success,
memory writes, tool access, shell access, file mutation, or cloud access.
```

Expected success path:

- completion response status is `completed`
- `model_call_performed=true`
- `generation_performed=true`
- `prompt_payload_sent=true`
- `authority=false`
- `runtime_dispatch_allowed=false`
- `model_output_is_truth=false`
- `model_output_is_evidence=false`
- `model_output_is_verifier_success=false`
- `approval_granted=false`
- `capability_lease_granted=false`

The returned text is proposal material only. It is not runtime truth, evidence,
verification, approval, permission, memory, or execution.

## Optional Operator Smoke Script

The script `scripts/model_hub_live_smoke.py` is an operator-run helper for the
existing local Aegis API. It does not edit `.env`, does not write files, does
not start LM Studio, and does not create evidence.

Status-only smoke:

```powershell
.\.venv\Scripts\python.exe scripts\model_hub_live_smoke.py
```

Status plus probe:

```powershell
.\.venv\Scripts\python.exe scripts\model_hub_live_smoke.py --probe
```

Explicit local completion smoke:

```powershell
.\.venv\Scripts\python.exe scripts\model_hub_live_smoke.py --probe --live --complete --confirm-local-lm-studio
```

The completion endpoint is not called unless `--live`, `--complete`, and
`--confirm-local-lm-studio` are all present.

## Safe Output Interpretation

Treat the smoke result as operational diagnostics:

- `disabled` means the gateway is fail-closed.
- `configured` means metadata is present, not provider health.
- `ready` probe means the local `/v1/models` request returned an acceptable
  response shape.
- `completed` means the local endpoint returned model text inside the
  non-authority envelope.

None of these states grants command execution, tool access, plugin execution,
agent execution, approval, lease, capability, evidence, verifier success, or
runtime health.

## Troubleshooting

Common fail-closed causes:

- LM Studio server is not running.
- The loaded model id does not match `AEGIS_LM_STUDIO_MODEL`.
- The base URL lacks `/v1`.
- The configured URL uses a remote host or contains credentials/query/fragment.
- The model is too slow for `AEGIS_MODEL_TIMEOUT_SECONDS`.
- The prompt exceeds `AEGIS_MODEL_MAX_INPUT_CHARS`.
- The requested output exceeds `AEGIS_MODEL_MAX_OUTPUT_TOKENS`.

Fix the local setup and rerun the explicit smoke. Do not add cloud fallback to
make the smoke pass.

## Intentionally Not Done

- No `.env` mutation
- No settings writer
- No automatic provider probe
- No automatic model call
- No cloud fallback
- No external provider calls
- No provider key storage or `.env` writer
- No memory write
- No tool, plugin, MCP, shell, browser, file, or agent execution
- No evidence creation
- No verifier success creation
- No transcript persistence

## Remaining Risks

- LM Studio model ids, loaded state, latency, context limits, quality, and local
  resource pressure are operator-environment specific.
- A successful local completion is still proposal-only and can be wrong.
- Future context-policy integration is required before larger private context
  packages are sent to any model.
