# Aegis Ask Product Slice

Decision: `AEGIS_ASK_PRODUCT_SLICE_READY`

## Scope

Aegis Ask is the first user-facing read-only explanation slice. It lets the user
ask natural-language questions about Aegis status, warning meaning,
capabilities, Skill Registry metadata, Tool Registry metadata, Model Gateway
status, safety boundaries, and safe next steps.

It is not autonomous execution, command execution, tool execution, plugin
execution, MCP, memory write, evidence repair, verifier success, approval,
capability lease, or frontend authority.

## Backend Contract

The deterministic backend core lives in `src/aegis/core/ask.py`.

The Ask response envelope includes:

- `answer`
- `intent`
- `source_refs`
- `known`
- `unknown`
- `limitations`
- `recommended_next_steps`
- `non_authority_flags`
- `runtime_health_summary`
- explicit false/null truth-critical fields for memory writes, execution,
  evidence, verifier success, approvals, leases, tool execution, plugin
  execution, and agent execution

The main Ask engine is deterministic backend code. Agent Runtime, Skill
Registry, Plugin Lifecycle, and Model Gateway are not the main Ask engine.

## API

`POST /ask` accepts a question plus optional flags:

- `include_memory`
- `include_model_polish`
- `include_autopilot`
- `include_agent_proposal`
- `scope`
- `max_sources`

The endpoint uses backend-owned read-only metadata:

- current maintenance/system status projection
- Skill Registry metadata
- Tool Registry metadata
- Model Gateway status metadata
- Agent Runtime profile catalog metadata
- plugin manifest/lifecycle summary metadata

It does not run tools, commands, plugins, agents, MCP, AutoPilot scans, memory
writes, model completions, background jobs, or verifier/evidence creation.

## Frontend

The frontend panel lives in
`frontend/src/features/ask/components/AskAegisPanel.tsx`.

It renders the backend response sections:

- Answer
- Runtime truth
- Known
- Unknown
- Limitations
- Recommended next steps
- Sources
- Safety / non-authority flags

The frontend does not synthesize health, authority, evidence, verifier success,
approval, capability, or execution state.

## Runtime Health Truth

Ask preserves raw-vs-active diagnostics:

- raw evidence/replay failures remain visible
- current operational blockers can be clear without making runtime health green
- historical/quarantined debt remains visible
- missing evidence is not fabricated

## Capability Boundaries

Skill Registry is catalog/introspection only.

Tool Registry metadata is not a tool call.

Plugin manifest/lifecycle metadata is not plugin load, dynamic import, or
execution.

Model Gateway status is metadata. Model polish is not performed in this first
slice, and model output would remain non-authoritative in a future slice.

Memory is not included by default. Ask does not write memory. Memory retrieval,
when later added behind explicit consent/read-only handling, remains context
only and not authority.

AutoPilot is not run by Ask by default. AutoPilot reports are read-only
candidate reports, not evidence.

Agent Runtime may supply profile metadata, but it is proposal-only and not the
Ask engine.

## Intentionally Not Done

- no command execution
- no tool/plugin/MCP/agent execution
- no model call
- no memory write
- no AutoPilot hidden scan
- no raw journal dump
- no evidence or verifier creation
- no approval/capability/lease grant
- no broad frontend redesign

## Remaining Risks

- The UI is useful but still not the final premium Mission Control experience.
- Memory search needs a future read-only/consent-safe integration that avoids
  hidden persistence side effects.
- Model-assisted polish needs a future local-only provider gate and strict
  context privacy rules before it can be enabled.
- More source-specific read-only summaries are needed before Ask can answer
  deeper repo and operational questions.
