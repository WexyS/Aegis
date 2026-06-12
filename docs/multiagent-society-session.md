# Deterministic Society Session

Decision: DETERMINISTIC_SOCIETY_SESSION_BACKEND_API

Deterministic Society Session creates a bounded, backend-owned proposal
session from AutoPilot output. It is a role-template session, not a live
autonomous multi-agent runtime.

## Scope

Implemented:

- deterministic Society Session backend model
- six fixed roles
- deterministic role proposals from AutoPilot report data
- optional memory id references
- timeline events for completed roles
- final report draft/summary
- REST API to run, retrieve, and list sessions
- process-local in-memory session storage

Not implemented:

- frontend UI
- WebSocket UI integration
- live autonomous multi-agent runtime
- LLM/model-dependent behavior
- tool execution
- shell execution
- network calls
- MCP calls
- memory writes
- automatic memory proposal, approval, rejection, or deletion
- graph runtime
- distributed agents
- consensus algorithms
- planner autonomy
- capability leases
- CodingAgent behavior

## Role Contracts

All role outputs are proposals. They are not truth, evidence, verifier success,
approval, lease, capability, or execution permission.

### Context Planner

Inputs:

- AutoPilot `context_preflight`
- root path
- source inventory summary
- limitations
- optional memory refs

Output:

- `context_requirements`
- context sources used
- local/read-only boundary
- no model provider required
- no network context
- context package does not grant execution permission

### Policy Reviewer

Inputs:

- AutoPilot `policy_gate`
- risk markers
- warnings
- limitations

Output:

- `risk_classification`
- read-only status
- mutation/shell/network/model/MCP/tool/memory write disallowed
- blocked and future-gated capabilities
- governance notes

### Memory Curator

Inputs:

- AutoPilot `memory_candidate_proposals`
- optional memory id refs

Output:

- `memory_review`
- candidate-only memory proposal summary
- suggested scopes and sensitivities
- explicit not persisted / not active status
- later user approval requirement

S3 does not read Memory OS records directly. Supplied memory ids are reference
only. Direct active-memory consumption is future-gated.

### AutoPilot Planner

Inputs:

- AutoPilot `source_inventory`
- findings
- risk markers

Output:

- `follow_up_plan`
- what the audit did
- what it did not do
- safe next read-only steps
- no mutation, shell, model, MCP, tool, or network requirement

### Verifier Reviewer

Inputs:

- AutoPilot `verifier_lite`
- report status
- required fields

Output:

- `verification_checklist`
- verifier-lite pass/fail/inconclusive/error state
- no full evidence verification claim
- report is not evidence
- verifier-lite remains scope-bound

### Report Writer

Inputs:

- all prior role proposals
- AutoPilot findings
- risk markers
- verifier-lite

Output:

- `report_draft`
- final summary
- findings summary
- memory candidate summary
- policy/context summary
- verifier-lite summary
- next actions

## Timeline Behavior

Timeline events are emitted only for roles that actually ran:

- `society_session_started`
- `context_planner_completed`
- `policy_reviewer_completed`
- `memory_curator_completed`
- `autopilot_planner_completed`
- `verifier_reviewer_completed`
- `report_writer_completed`
- `society_session_completed`

Events are backend-owned session facts, not runtime execution events and not
journal/evidence records.

## API

Endpoints:

- `POST /society/run`
- `GET /society/sessions/{session_id}`
- `GET /society/sessions`

`POST /society/run` accepts:

- `autopilot_report_id`
- optional `report_payload`
- optional `memory_ids`
- optional `society_name`

Primary path:

`autopilot_report_id` -> AutoPilot process-local report store -> deterministic
role proposals.

If a report id is missing, the API returns an `input_missing` session as HTTP
404 detail.

## Persistence

Sessions are stored in process-local memory. They are not durable across backend
restarts. No report/session files are written.

## Non-Authority Rules

Society Session preserves:

- agent proposes, backend decides
- role output is not truth
- role output is not evidence
- role output is not verifier success
- Society Session is not autonomous execution
- Society Session is not tool permission
- Society Session is not approval
- memory candidate proposal is not active memory
- retrieved memory is not authority
- AutoPilot report is not evidence
- report draft is not verifier success
- context package is not execution permission
- frontend state is not backend truth

Every session and proposal keeps:

- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_society_session_rc1`
- `verifier_success=false`
- `model_call_performed=false`
- `mcp_call_performed=false`
- `tool_call_performed=false`
- `shell_command_performed=false`
- `network_call_performed=false`

## Context and Memory Boundaries

Society consumes AutoPilot report metadata and optional memory id references
only. It does not create a context package, route to a provider, read raw
unrestricted context, or write Memory OS records.

Unknown or sensitive memory is not automatically consumed. Future UI work can
offer explicit user-controlled memory proposal and approval actions.

## Future-Gated Work

Future sprints may add Mission Control UI display, explicit Memory OS proposal
actions, durable session storage, richer role contracts, or a live MultiAgent
Society runtime. Those require separate scoped work and must preserve Aegis
authority, evidence, verifier, policy, approval, runtime, memory, and tool
boundaries.
