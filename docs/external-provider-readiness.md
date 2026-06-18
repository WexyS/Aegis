# External Provider Readiness

## Decision

Decision: `AEGIS_MODEL_HUB_PROVIDER_READINESS_READY`

External Provider Readiness is the Model Hub metadata surface for future
operator-managed external model providers. It does not call providers, does not
store keys, does not print keys, does not edit `.env`, and does not enable cloud
completion.

## Scope

This readiness layer represents:

- planned external providers
- expected environment variable names
- API key presence as boolean metadata only
- cloud completion disabled state
- explicit future operator opt-in requirements
- prompt preview, cost warning, and privacy warning requirements
- proposal-only output boundaries

It is not External Provider Broker implementation and it is not cloud routing.

## Provider Records

Current readiness records:

- OpenRouter: `AEGIS_OPENROUTER_API_KEY`, `AEGIS_OPENROUTER_MODEL`
- DeepSeek API: `AEGIS_DEEPSEEK_API_KEY`, `AEGIS_DEEPSEEK_MODEL`
- OpenAI: `AEGIS_OPENAI_API_KEY`, `AEGIS_OPENAI_MODEL`
- Anthropic: `AEGIS_ANTHROPIC_API_KEY`, `AEGIS_ANTHROPIC_MODEL`
- Gemini: `AEGIS_GEMINI_API_KEY`, `AEGIS_GEMINI_MODEL`

Only the key presence boolean is exposed. Key values are never returned by the
readiness projection.

## Readiness Statuses

- `missing_key_disabled`: the expected API key environment variable is absent.
- `key_present_calls_disabled`: the key variable is present, but provider calls
  remain disabled.

Both states keep `cloud_completion_enabled=false` and
`automatic_fallback_allowed=false`.

## Operator Environment Placeholders

Examples use placeholder values only:

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
readiness metadata only until External Provider Broker is implemented.

## Cloud Escalation Policy

Current policy:

- automatic cloud fallback is disabled
- cloud calls are disabled now
- External Provider Broker is required before future use
- operator opt-in is required
- prompt preview is required
- cost warning is required
- privacy warning is required
- secret redaction is required
- output must remain proposal-only

Local failure must not silently trigger cloud routing.

## Prompt Safety

Future external provider prompts must not include by default:

- secrets or tokens
- raw logs
- raw journals
- raw evidence
- repo dumps
- private context without explicit future policy gates

Provider output must not become authority, evidence, verifier success, approval,
capability lease, memory write, tool execution, or runtime truth.

## Relationship To Model Hub

`GET /model-hub/status` includes this readiness projection so the UI can show
provider readiness without adding cloud buttons, key inputs, or provider calls.

The UI may display:

- provider name
- key missing or key present with calls disabled
- expected environment variable names
- cloud disabled badge
- automatic fallback disabled badge
- manual opt-in and prompt preview requirements

The UI must not render key values or claim provider usability from key presence.

## Relationship To Model Gateway

Model Gateway remains the only implemented model-call boundary and currently
supports explicit local LM Studio/OpenAI-compatible calls. External Provider
Readiness does not bypass Model Gateway and does not add external provider
runtime calls.

## Intentionally Not Done

- No cloud completion calls
- No provider SDKs
- No hidden cloud fallback
- No key storage
- No `.env` writer
- No external provider endpoints
- No transcript persistence
- No memory writes
- No tool, agent, workflow, shell, MCP, plugin, browser, or computer execution
- No evidence or verifier success
- No approval or capability lease grant

## Remaining Risks

- Key presence can only prove an environment variable exists; it cannot prove
  validity, account status, budget, region/terms acceptance, provider health, or
  model availability.
- Future broker work must implement purpose, privacy, cost, prompt preview,
  provider/model selection, and redaction gates before any external call.
