# Capability Model

Decision: `AEGIS_CAPABILITY_MODEL_DEFINED`

Date: 2026-06-12

## Purpose

The capability model defines how Aegis should move from passive inspection to
real work without weakening trust boundaries.

Capability metadata is not permission. A capability tier describes what kind of
work may be considered. Actual execution still requires backend policy,
approval where needed, scoped inputs, evidence expectations, verifier checks,
and runtime lifecycle handling.

## Capability Tiers

| Tier | Meaning | Current examples | Permission rule |
| --- | --- | --- | --- |
| Observe | Read backend-owned state or local metadata without mutation. | maintenance scan, tool registry, app registry, runtime snapshot | Can run automatically when read-only and bounded. |
| Explain | Summarize observed state without claiming truth beyond sources. | deterministic summaries, Model Gateway proposal text | Output is proposal/context only. |
| Propose | Create a plan, candidate action, memory proposal, or agent proposal. | action proposals, Memory proposals, historical debt closure dry-run, Agent Runtime sessions | Proposal is not execution permission. |
| Read-only execute | Perform bounded non-mutating local inspection. | AutoPilot repository structure audit | Allowed only with scoped path and policy limits. |
| Approval-gated mutate | Perform local mutation after explicit approval and verifier strategy. | `create_logging_directory`, `create_scratch_directory` | Requires backend approval and safety gate. |
| Policy-gated external | Use network, MCP, external API, paid connector, or cloud model. | future only | Requires explicit policy, privacy, credential, approval, and cost gates. |
| Blocked | Refuse unsafe or unsupported action. | destructive commands, secrets, unknown external access | Must fail closed and preserve reason. |

## Automatic Work

Aegis may automatically run bounded work only when all are true:

- local-only
- read-only or explicitly low-risk
- no secrets or credential handling
- no external network
- no hidden model/tool/MCP fallback
- no mutation
- backend-owned state records what happened

Examples:

- runtime snapshot projection
- read-only maintenance scan
- registry listing
- safe status endpoints

## Read-Only Work

Read-only work can be useful and real. It still needs scope limits.

Current read-only work:

- AutoPilot local repository structure audit
- maintenance diagnostics
- registry/catalog projection

Read-only output is not evidence unless an evidence contract explicitly says so.
AutoPilot reports are analysis output, not verifier proof.

## Model-Assisted Work

Model-assisted work may explain, summarize, polish, or draft proposals.

Rules:

- Model output is not truth.
- Model output is not evidence.
- Model output is not verifier success.
- Model output is not approval or permission.
- Local Model Gateway is preferred when configured.
- Cloud model routing is not allowed by default.
- Raw secrets, raw journals, and raw private evidence must not be sent to a
  model without future explicit policy.

Current implemented model boundary:

- Model Gateway can call configured local LM Studio/OpenAI-compatible endpoints
  when enabled and valid.
- Agent Runtime reads Model Gateway status metadata but does not call model
  completions.

## Approval-Gated Mutation

Mutation requires more than intent.

Required gates:

- backend policy allow
- explicit user approval when risk requires it
- scoped target
- safety preflight
- evidence expectation
- verifier or postcondition strategy
- journal/runtime lifecycle record
- no hidden fallback

Current approved mutation examples are limited maintenance actions:

- `create_logging_directory`
- `create_scratch_directory`

## Blocked Work

Aegis must block:

- destructive broad shell commands
- hidden external network calls
- credential/API key handling outside explicit future flows
- model output treated as authority
- frontend-created authority
- plugin/skill metadata treated as permission
- unbounded filesystem access
- cleanup/archive/compaction execution without operator gates
- historical evidence reconstruction by guessing

## Current Implemented Capabilities

- command governance and approval lifecycle
- read-only maintenance scan
- historical evidence/replay closure dry-run planning
- action proposal lifecycle for narrow maintenance actions
- local Memory OS explicit lifecycle operations
- AutoPilot read-only repository structure audit
- deterministic Society Session proposal output
- local Model Gateway boundary
- static Skill Registry metadata
- proposal-only Bounded Agent Runtime

Historical evidence/replay closure apply is currently limited to a
caller-supplied manifest store after all gates pass. It is not journal rewrite,
evidence repair, replay repair, or runtime health suppression.

## Future Capabilities

Future capability work should add real product value in this order:

1. Aegis Ask read-only explanation.
2. Intent Router / Capability Broker.
3. More read-only local inspection capabilities.
4. Memory Inbox and consent-based memory intelligence.
5. Agent-to-skill proposal flow.
6. Approved local safe actions with evidence/verifier strategy.
7. Optional MCP and external connector layer.

## Safety Boundary

No capability tier can override:

- backend-owned truth
- policy decisions
- approval requirements
- evidence requirements
- verifier requirements
- memory consent
- context privacy
- generated artifact hygiene
- historical debt visibility
