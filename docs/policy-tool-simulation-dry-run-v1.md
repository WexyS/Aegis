# Policy / Tool Simulation Dry Run v1

Decision: `POLICY_TOOL_SIMULATION_CONTRACT_WITH_TESTS`

## Scope

This sprint defines a pure backend-owned policy/tool simulation contract for
Aegis. The simulation explains what a proposed action would require before
execution, but it does not execute tools or grant permission.

The implementation adds:

- `src/aegis/core/tool_simulation.py`
- `tests/test_core/test_tool_simulation.py`

This is a code/text/docs/tests-only contract. It does not call browser, app,
file, shell, API, model, memory, plugin, or MCP systems. It does not create UI,
screenshots, visual assets, generated images, evidence, verifier success,
approvals, leases, runtime events, journal entries, replay records, or runtime
state changes.

## Why Simulation Exists

Mission Control defines how future operator-facing dry-run cards can present
proposed actions. Policy/tool simulation is the backend preflight layer that can
produce consistent, non-executing simulation metadata for those cards.

Without this contract, dry-run cards risk becoming manually assembled and
inconsistent. Tool selection could be confused with execution, policy could be
duplicated, evidence and verifier expectations could be incomplete, and frontend
code could infer authority it must never own.

## Relationship To Mission Control

Mission Control can consume simulation metadata through the pure
`mission_control_input_from_simulation(...)` adapter. The adapter copies the
simulation result into Mission Control preview fields such as normalized intent,
route, proposed tool, risk tier, policy reference, approval and lease
requirements, evidence and verifier expectations, rollback status, timeout
fallback metadata, provider interstitial risk, alternatives, and source refs.

Mission Control remains non-authoritative. Simulation remains non-executing.
Neither layer approves, dispatches, creates a lease, creates evidence, marks
verifier success, or mutates runtime state.

## Simulation Fields

`ToolSimulationInput` accepts caller-supplied metadata:

- `request_id`, `command_id`, `raw_user_request`, `normalized_intent`
- `route_kind`, `proposed_action`, `proposed_tool`, `tool_category`
- `capability_category`, `risk_tier`
- `target_app`, `target_url`, `search_provider`, `query`
- `affected_resources`, `data_sensitivity`
- `policy_rule_refs`, `policy_decision_hint`
- `approval_hint`, `lease_hint`
- `evidence_expectation_hint`, `verifier_expectation_hint`
- `timeout_budget_ref`, `rollback_status`
- `provider_interstitial_risk`, `fallback_expectation`
- `source_refs`, `claims`

`ToolSimulationResult` includes:

- `simulation_version`
- `simulation_id`
- request, command, intent, route, action, tool, category, risk, and capability
  metadata
- `policy_simulation_status`
- policy refs and hints
- `approval_required`, `approval_reason`
- `lease_required`, `lease_reason`, proposed lease scope and duration
- `evidence_expected`
- `verifier_expected`
- `affected_resources`
- `blocked_reasons`, `warnings`, `unknowns`, `alternatives`, `findings`
- `operator_attention_required`
- rollback, timeout/fallback, and provider interstitial metadata
- invariant non-authority fields

The invariant fields are:

- `can_execute=false`
- `would_dispatch=false`
- `dispatch_performed=false`
- `authority=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_tool_simulation`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_created=false`
- `evidence_provided_by_simulation=false`
- `verifier_success=false`
- `mutation_performed=false`
- `frontend_authority=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

## Status Taxonomy

Allowed simulation statuses:

- `simulation_ready`
- `policy_allows_but_requires_execution_gate`
- `approval_required`
- `lease_required`
- `blocked_by_policy`
- `blocked_by_unknown_risk`
- `blocked_by_missing_resource_scope`
- `blocked_by_missing_evidence_expectation`
- `blocked_by_missing_verifier_expectation`
- `blocked_by_destructive_action`
- `blocked_by_unavailable_rollback`
- `blocked_by_provider_interstitial_risk`
- `blocked_by_quarantined_tool`
- `unsupported_tool`
- `unsupported_action`
- `clarification_required`

`simulation_ready` does not mean execution allowed. Policy-allowed simulation
does not mean runtime dispatch allowed. Approval-required simulation does not
grant approval. Lease-required simulation does not create a lease. Blocked,
unsupported, and clarification-required statuses never execute.

## Risk And Tool Category Model

Risk tiers:

- `read_only`
- `browser_open`
- `browser_search`
- `app_launch`
- `local_file_read`
- `local_file_write`
- `external_api_read`
- `external_api_write`
- `memory_read`
- `memory_write`
- `plugin_execution`
- `cleanup_archive`
- `cleanup_compaction`
- `destructive_system_change`
- `unknown`

Tool categories:

- `app_tool`
- `browser_tool`
- `file_tool`
- `shell_tool`
- `api_tool`
- `memory_tool`
- `plugin_tool`
- `cleanup_tool`
- `model_tool`
- `unknown_tool`

Unknown tools and unknown risk block or require operator attention.
Quarantined click surfaces (`click`, `browser_click`, `desktop_click`) block.
Raw lifecycle/control commands such as `/force_idle` and `/reset_memory` are not
simulated as direct execution. Vision and live-feed surfaces block without a
future explicit privacy gate.

## Evidence Expectation Model

Allowed evidence expectations:

- `no_evidence_expected`
- `process_window_verification_expected`
- `browser_url_verification_expected`
- `provider_interstitial_check_expected`
- `file_hash_or_diff_expected`
- `policy_decision_ref_expected`
- `timeout_projection_expected`
- `human_review_required`
- `unknown_evidence_expectation`

Side-effecting simulations require affected resources and evidence
expectations. Evidence expectation is not evidence, and simulation cannot create
evidence.

## Verifier Expectation Model

`ToolSimulationVerifierExpectation` includes:

- `verifier_required`
- `verifier_name`
- `verifier_postcondition`
- `verifier_failure_modes`
- `verifier_success_required_for_completion`

High-risk simulations require verifier expectation metadata. Verifier
expectation is not verifier success. Dispatch success remains separate from
verifier success.

## Approval And Lease Relationship

Simulation may set:

- `approval_required=true`
- `approval_reason`
- `lease_required=true`
- `lease_reason`
- `proposed_lease_scope`
- `proposed_lease_duration`

These fields are explanatory only. The simulation does not create approval,
grant approval, create a lease, activate a lease, or make repeated approvals
unnecessary by itself.

## Rollback And Staging Relationship

Rollback statuses:

- `not_applicable`
- `unavailable`
- `manual_only`
- `staging_required`
- `backup_required`
- `reversible_with_plan`
- `compensating_action_only`
- `unknown`

Rollback metadata is descriptive only. Destructive simulations with unavailable
or unknown rollback block. Rollback availability does not grant permission.

## Provider Interstitial Relationship

Browser/search simulations can carry provider interstitial metadata. When
`search_provider=google`, the contract surfaces the known Google `/sorry`
bot-challenge verifier risk as `google_sorry_bot_challenge` and
`search_verification_blocked_by_provider`.

Simulation does not bypass provider challenges, click through interstitials,
enable fallback, or mark browser/search verification as successful.

## Timeout And Fallback Relationship

Simulation may reference:

- `timeout_budget_ref`
- `timeout_projection_possible`
- `fallback_available`
- `fallback_type`
- `fallback_is_success=false`

Timeout is not success. Fallback is not success. Retry is not success. If a
caller claims `fallback_is_success=true`, the simulation records a blocker and
normalizes the result back to `fallback_is_success=false`.

## Policy Relationship

Simulation may reference caller-supplied policy refs or policy decision hints.
It does not create policy decisions, call runtime policy, or override policy.
Policy denied remains denied. Unknown policy context remains an unknown or
blocked simulation condition.

## Tool Registry Relationship

The contract uses static supported/quarantined tool metadata only. It does not
dynamically load tools, start MCP servers, inspect plugins, call tools, or
dispatch actions. Missing, unsupported, quarantined, or future-gated tools block
or require clarification.

## Frontend Non-Authority Relationship

Frontend may display backend simulation results in a future UI. Frontend cannot
create simulation authority, dispatch, approve, create leases, create evidence,
mark verifier success, or mutate simulation into runtime truth.

Caller-supplied frontend authority fields are rejected.

## Compliance Wording Boundary

Simulation rejects claims of:

- legal, compliance, or security certification
- official audit result
- court-admissible evidence
- proof of compliance
- proof of control effectiveness
- organization-safe claims

Simulation is not certification, legal proof, an official audit result, or a
control-effectiveness result.

## Tests Added

Focused tests cover:

- valid read-only simulation as non-authoritative and non-dispatchable
- browser search provider/evidence/verifier/interstitial expectations
- app launch process/window verifier expectation
- local file write resource and evidence requirements
- destructive rollback blocking
- unknown risk and unknown tool blocking
- quarantined click blocking
- raw control command blocking
- vision/live feed blocking
- external API write approval/lease/evidence expectations without dispatch
- plugin and memory write not masquerading as read-only
- authority, grant, runtime dispatch, evidence, verifier, and frontend authority
  rejection
- policy denied non-override
- approval and lease explanatory-only behavior
- timeout/fallback not success
- provider interstitial non-bypass
- compliance wording rejection
- input immutability
- pure Mission Control consumption of simulation metadata

## Intentionally Not Done

- no runtime integration
- no orchestrator, planner, executor, tool registry, or MCP integration
- no frontend UI
- no browser/app/file/shell/API/model/memory/plugin calls
- no image generation, screenshot, mockup, or visual asset
- no approval, denial, clarification, or lease lifecycle changes
- no evidence creation or verifier mutation
- no runtime, journal, evidence, replay, snapshot, timeout, or health mutation
- no cleanup/archive/compaction execution
- no click implementation
- no vision/live feed enablement
- no schema/protocol expansion

## Future Runtime Integration Notes

Future runtime integration must keep this sequence explicit:

1. parse and normalize intent
2. build policy/tool simulation metadata
3. render or pass through Mission Control preview
4. collect operator decision when required
5. re-run backend policy at the execution boundary
6. dispatch only through existing runtime authority
7. verify and record evidence through existing verifier/evidence contracts
8. append journal events only through runtime-owned append paths

Simulation output must never be treated as runtime truth or execution
permission.

## Remaining Risks

The current helper consumes caller-supplied metadata and static tool categories.
Future work must define how parser, policy, tool metadata, evidence, verifier,
lease, and Mission Control contexts are assembled without letting frontend,
model output, plugin manifests, or user-supplied claims become authority.
