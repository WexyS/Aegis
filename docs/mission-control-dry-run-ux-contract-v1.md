# Mission Control / Dry-Run UX Contract v1

Decision: `MISSION_CONTROL_DRY_RUN_CONTRACT_WITH_TESTS`

## Scope

This sprint defines a pure backend-owned Mission Control dry-run preview
contract for proposed Aegis actions. The preview explains what would happen
before execution so future operator-facing surfaces can reduce approval fatigue
without weakening policy, approval, evidence, verifier, lease, or runtime
boundaries.

The implementation adds `src/aegis/core/mission_control.py` and focused tests in
`tests/test_core/test_mission_control.py`. It is text/code/docs only.

No image generation, screenshot creation, visual mockup, design asset, model
call, API call, tool call, browser action, runtime dispatch, journal append,
evidence mutation, verifier success, approval grant, lease creation, or frontend
authority is introduced.

## Why Mission Control Exists

Aegis already has backend safety contracts, but a yes/no prompt can still be too
thin for an operator. Mission Control exists to make the proposed action
legible before execution:

- what intent was normalized;
- which route, tool, action, and target are proposed;
- what risk tier and capability category apply;
- what policy decided and why;
- whether approval or a future scoped lease is required;
- what evidence and verifier behavior is expected;
- what rollback, staging, timeout, fallback, provider, privacy, limitation, and
  alternative context exists;
- which operator decision options may be rendered later.

The preview is explanation only. It is not permission.

## Approval Fatigue Problem

Vague approval prompts make repeated human-in-the-loop decisions weaker over
time. Operators may approve reflexively when the prompt does not explain risk,
resources, evidence, verifier checks, failure modes, rollback limits, timeout
behavior, or safer alternatives.

Mission Control turns the pre-action explanation into a structured contract so
future UI can render clear cards without becoming a source of authority.

## Dry-Run Preview Fields

`MissionControlInput` accepts caller-supplied metadata such as:

- `request_id`, `command_id`, `raw_user_request`, `normalized_intent`;
- `route_kind`, `proposed_action`, `proposed_tool`;
- `target_app`, `target_url`, `search_provider`, `query`;
- `affected_resources`;
- `risk_tier`, `capability_category`;
- `policy_decision_ref`, `policy_decision_status`, `policy_reason`;
- `approval_required`, `approval_reason`;
- `lease_required`, `lease_scope`, `lease_duration`;
- `evidence_expectation`, `verifier_expectation`;
- `timeout_budget_ref`, `fallback_expectation`;
- `rollback_status`, `rollback_plan_ref`;
- `provider_interstitial_risk`;
- `data_sensitivity`, `privacy_notes`;
- `limitations`, `unknowns`, `alternatives`;
- `operator_options`, `source_refs`.

`MissionControlPreviewContract` always preserves the invariant fields:

- `authority=false`;
- `runtime_dispatch_allowed=false`;
- `execution_permission=not_granted_by_mission_control`;
- `approval_grant=false`;
- `capability_grant=false`;
- `lease_grant=false`;
- `evidence_provided_by_preview=false`;
- `verifier_success=false`;
- `mutation_performed=false`;
- `frontend_authority=false`;
- `requires_backend_validation=true`;
- `requires_policy_check=true`;
- `requires_operator_decision_when_required=true`.

## Risk Tier Model

Preview risk tiers are non-authoritative:

- `read_only`;
- `browser_open`;
- `browser_search`;
- `app_launch`;
- `local_file_read`;
- `local_file_write`;
- `external_api_read`;
- `external_api_write`;
- `memory_read`;
- `memory_write`;
- `plugin_execution`;
- `cleanup_archive`;
- `cleanup_compaction`;
- `destructive_system_change`;
- `unknown`.

The validator fails or blocks unsafe previews when high-risk actions lack
affected resources or evidence expectations, destructive actions lack rollback
or staging context, or write/plugin/memory/API actions pretend to be read-only.

Unknown risk produces `operator_attention_required`.

## Operator Decision Options

Allowed operator option metadata:

- `approve_once`;
- `deny`;
- `ask_clarification`;
- `request_dry_run_details`;
- `request_safer_alternative`;
- `create_scoped_lease_candidate`;
- `cancel`;
- `block`.

Mission Control only describes these options. It does not execute the option,
resolve approval, deny, cancel, block, or create a lease.

## Evidence Expectation Model

Allowed evidence expectation values:

- `no_evidence_expected`;
- `process_window_verification_expected`;
- `browser_url_verification_expected`;
- `provider_interstitial_check_expected`;
- `file_hash_or_diff_expected`;
- `policy_decision_ref_expected`;
- `timeout_projection_expected`;
- `human_review_required`;
- `unknown_evidence_expectation`.

Evidence expectation is not evidence. The preview cannot create evidence, mark
evidence complete, or convert missing evidence into success.

## Verifier Expectation Model

`MissionControlVerifierExpectation` includes:

- `verifier_required`;
- `verifier_name`;
- `verifier_postcondition`;
- `verifier_failure_modes`;
- `verifier_success_required_for_completion`.

Verifier expectation is not verifier success. The preview cannot mark an action
verified, and the verifier cannot be frontend-owned.

## Rollback And Staging Model

Allowed rollback statuses:

- `not_applicable`;
- `unavailable`;
- `manual_only`;
- `staging_required`;
- `backup_required`;
- `reversible_with_plan`;
- `compensating_action_only`;
- `unknown`.

Rollback plan metadata is not rollback execution. Rollback availability does
not make an action safe by itself. Destructive previews with `unknown` or
`unavailable` rollback are blocked by the validator.

## Timeout And Fallback Relationship

Mission Control may reference timeout and fallback expectations through
`timeout_budget_ref` and `fallback_expectation`.

Fallback is not success. Timeout projection is not success. Retry is not
success. If a caller claims `fallback_is_success=true`, the validator records a
failure and the contract normalizes the preview output back to
`fallback_is_success=false`.

## Provider Interstitial Relationship

For browser and search previews, Mission Control can include
`provider_interstitial_risk`.

When `search_provider=google`, the contract can surface the known Google
`/sorry` bot-challenge risk as `google_sorry_bot_challenge` and
`search_verification_blocked_by_provider`.

The preview does not bypass provider challenges, click through interstitials,
mark search as verified, or enable fallback. If a caller asks for bypass, the
validator rejects the claim and normalizes `bypass_allowed=false`.

## Compliance And Product Wording Boundary

Mission Control may describe compliance evidence packs as audit-readiness or
human-review candidates only. It rejects wording that claims:

- legal, compliance, or security certification;
- official audit result;
- court-admissible evidence;
- proof of compliance;
- proof of control effectiveness.

The preview is not legal advice, certification, official audit output, or proof
that controls are effective.

## Relationships

Policy:
Mission Control may reference policy decisions. It does not create, override,
or resolve policy. Policy denied remains denied.

Approval:
Mission Control explains approval requirements. It does not approve, deny, or
resolve pending decisions.

Capability Lease:
Mission Control may describe a scoped lease candidate. It does not create,
activate, or grant a lease.

Evidence and Verifier:
Mission Control describes expectations only. It cannot create evidence or
verifier success.

Runtime Timeout:
Mission Control may reference timeout/fallback expectations. It cannot emit
timeout events, mutate command lifecycle, or run watchdog enforcement.

Provider Interstitial Registry:
Mission Control may warn about provider interstitial risks. It cannot bypass
interstitials.

Compliance Evidence Pack:
Mission Control may display audit-readiness limitations. It cannot certify.

Frontend:
Future frontend cards may render backend preview contracts. Frontend cannot
create authority, make a preview executable, approve actions, create leases,
provide evidence, mark verifier success, or become source of truth.

## Tests Added

Focused tests cover:

- valid read-only non-authoritative preview;
- browser search provider/evidence/verifier expectations;
- app launch process/window verifier expectation;
- high-risk local file write resource/evidence requirements;
- destructive unknown rollback blocking;
- unknown risk operator attention;
- authority, grants, runtime dispatch, frontend authority rejection;
- evidence/verifier/success claim rejection;
- external API write, plugin execution, and memory write pretending read-only;
- compliance certification wording rejection;
- policy denied non-override;
- approval and lease candidate explanatory-only behavior;
- timeout/fallback not success;
- provider interstitial warning not bypass;
- input immutability;
- no image/model/tool generation requirement.

## Intentionally Not Done

- no live runtime integration;
- no execution, approval, denial, lease, or lifecycle resolver;
- no event emission, journal append, evidence creation, verifier mutation, or
  replay mutation;
- no frontend UI;
- no image generation, screenshot, mockup, or visual asset;
- no browser click, desktop click, generic click, vision, OCR, accessibility,
  voice, plugin marketplace, memory graph, autonomous loop, self-modifying code,
  LLM planner integration, Ultron bridge, or unified launcher;
- no schema/protocol expansion.

## Future UI Implementation Notes

Future UI should render backend-created `MissionControlPreviewContract` values
as non-authoritative cards. It should visually separate proposal, policy,
approval requirement, evidence expectation, verifier expectation, rollback,
timeout/fallback, provider risk, limitations, alternatives, and operator options.

The UI must not compute authority fields, mutate preview state into approval,
or treat a rendered card as execution permission. Backend snapshot, event
journal, protocol events, execution evidence, and verifier output remain the
source of truth.

## Remaining Risks

Mission Control is currently a standalone validator/helper. Future integration
must define where previews are built from parser, guard, policy, timeout, and
verifier metadata without allowing frontend, model output, or caller-supplied
claims to become authority.

Future lease UX requires a separate backend-owned lifecycle contract so scoped
leases reduce approval fatigue without becoming hidden auto-approval.
