# Bounded Agent Runtime

Decision: `BOUNDED_AGENT_RUNTIME_PROPOSAL_ONLY`

Current status: implemented as a proposal-only backend/API surface. The
historical decision name is retained for traceability; public product wording
should use Bounded Agent Runtime.

## Scope

Bounded Agent Runtime introduces backend-owned agent profiles, deterministic
proposal-only sessions, timeline events, and process-local session storage.

It is not an autonomous agent system. It is not a tool runner, MCP runner, shell
runner, file mutation path, memory writer, verifier, evidence creator, approval
system, capability lease system, scheduler, stream processor, browser
automation layer, or CodingAgent implementation.

## What It Is

Bounded Agent Runtime is a proposal engine:

- loads static built-in agent profiles
- references Skill Registry metadata
- records Model Gateway awareness without calling completions
- creates deterministic proposals
- creates deterministic timeline events
- stores successful sessions in process-local memory

Every output remains planning material only.

## What It Is Not

Bounded Agent Runtime does not:

- start an autonomous loop
- execute skills
- call tools
- call MCP
- call shell
- mutate files
- write memory
- call Model Gateway completions
- call external APIs
- create evidence
- create verifier success
- grant approval
- grant a capability lease
- dispatch runtime actions
- hide degraded or future-gated states

Agent output is not truth, evidence, verifier success, approval, permission,
capability, lease, policy, or runtime health.

## Agent Profiles

Static built-in profiles:

`context_agent`

- Role: `context_planner`
- Allowed skills: `context_package_review`, `model_assisted_explanation`
- Reviews supplied context boundaries.
- Context does not grant execution permission.

`memory_agent`

- Role: `memory_reviewer`
- Allowed skills: `memory_candidate_review`, `report_summarization`
- Reviews memory refs and future memory candidate boundaries.
- No memory retrieval or write is performed.

`autopilot_agent`

- Role: `autopilot_planner`
- Allowed skills: `repo_structure_audit`, `model_assisted_explanation`
- Reviews AutoPilot report references.
- Does not run AutoPilot or scan repositories.

`policy_agent`

- Role: `policy_reviewer`
- Allowed skills: `context_package_review`, `ecc_security_config_review`
- Summarizes blocked capabilities and policy boundaries.
- External skill references remain non-executable.

`verifier_agent`

- Role: `verifier_reviewer`
- Allowed skills: `context_package_review`
- Distinguishes checklist review from backend verifier success.
- Creates no verifier success.

`report_agent`

- Role: `report_writer`
- Allowed skills: `report_summarization`, `model_assisted_explanation`
- Aggregates prior proposal outputs into a proposal-only summary.
- Does not call Model Gateway for summarization in the current implementation.

## Session Model

Session inputs:

- `objective`
- `context_summary`
- optional `autopilot_report_id`
- optional `memory_refs`
- optional `skill_ids`
- optional `agent_ids`
- optional `use_model`
- optional `dry_run`

Session output includes:

- `session_id`
- `status`
- `mode`
- `input_summary`
- `requested_agent_ids`
- `requested_skill_ids`
- `agents`
- `referenced_skills`
- `proposals`
- `timeline`
- `warnings`
- `limitations`
- `failure_reasons`
- `created_at`
- `completed_at`
- `degraded_state`
- `model_gateway_awareness`
- non-execution and non-authority flags

Successful sessions are stored in process-local memory only. They disappear on
backend restart.

## Proposal-Only Behavior

Each proposal includes:

- `proposal_id`
- `agent_id`
- `proposal_type`
- `title`
- `summary`
- `inputs_used`
- `referenced_skill_ids`
- `claims`
- `limitations`
- `recommended_next_steps`
- `non_authority_flags`

Proposal claims are scoped to planning and review. They do not become evidence,
verifier success, policy allow, approval, or execution permission.

## Timeline Events

The current implementation emits deterministic timeline events inside the
returned session object:

- `agent_session_started`
- `agent_profile_loaded`
- one proposal-created event per requested agent
- `report_agent_summary_created` when the Report Agent runs
- `agent_session_completed`

Failed validation returns `agent_session_failed` and no proposals.

These are session records, not runtime journal events.

## Skill Registry Metadata Use

Bounded Agent Runtime uses Skill Registry metadata to:

- confirm allowed profile skills exist
- validate requested skill ids
- attach referenced skill metadata to sessions
- surface candidate/future-gated/external skill references

It does not:

- execute skills
- add skill run endpoints
- mutate skill enabled state
- connect MCP
- run external candidates
- call Model Gateway through model-required skill metadata

Allowed skill ids are references, not permission.

## Model Gateway Awareness

Bounded Agent Runtime reads Model Gateway status metadata only. It does not call
`/model-gateway/complete`.

When `use_model=true`, the session returns a degraded warning:

- `model_assisted_agents_future_gated`

The session remains deterministic and proposal-only. LM Studio is not required.

## API Endpoints

Added endpoints:

- `GET /agents/profiles`
- `GET /agents/profiles/{agent_id}`
- `POST /agents/sessions`
- `GET /agents/sessions`
- `GET /agents/sessions/{session_id}`

Profile endpoints are read-only. Session creation runs deterministic
proposal-only generation. Missing agent or skill ids return a clear validation
error.

## Example Session Request

```json
{
  "objective": "Review the bounded runtime before model-assisted Society.",
  "context_summary": "Use Model Gateway and Skill Registry foundations.",
  "agent_ids": ["context_agent", "policy_agent", "report_agent"],
  "dry_run": true,
  "use_model": false
}
```

## Limitations

- Sessions are process-local and not durable.
- Model assistance is future-gated.
- Agent profiles are static.
- No scheduler, streaming, retries, or long-running orchestration exists.
- No tool, MCP, shell, file, browser, memory, or external API behavior exists.
- No model-assisted Society, AutoPilot, Memory, or frontend integration is added.

## Future Integration Notes

Future Society work can consume Agent Runtime proposal timelines as
non-authoritative planning material.

Any future policy-gated agent execution path would need:

- explicit policy gates
- explicit user approval
- capability lease boundary
- scoped skill execution contract
- evidence expectations
- verifier/postcondition strategy
- rollback/error handling
- no hidden fallback
- runtime journal integration
- tests proving non-authority and fail-closed behavior
