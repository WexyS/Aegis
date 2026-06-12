# Action Attribution / Change Intelligence Contract
## Decision

- Decision: `ACTION_ATTRIBUTION_CONTRACT_WITH_TESTS`
- Contract version: `action-attribution-change-intelligence/1`
- Implementation surface: `src/aegis/core/action_attribution.py`
- Test surface: `tests/test_core/test_action_attribution.py`
- Previous sprint: `AUDIT_QUERY_LAYER_READINESS_WITH_TESTS`

This sprint adds a pure readiness contract for future action attribution and
change intelligence. It does not implement live attribution execution, file or
process monitoring, repo scans, raw journal reads, raw evidence reads, database
queries, model/tool/MCP/web calls, memory/context retrieval, API endpoints,
frontend UI, reports, artifacts, evidence creation, verifier success, or
runtime/journal/evidence/replay mutation.

## Scope

The contract validates caller-supplied attribution metadata and classifies
whether an attribution candidate is:

- a read-only attribution candidate
- future-gated
- unknown or external
- requiring human review
- blocked by missing metadata, authority claims, evidence claims, execution
  claims, truthfulness overclaims, or unsafe related decisions

The output is non-authoritative. Attribution metadata cannot grant permission,
approval, leases, capabilities, evidence, verifier success, runtime dispatch,
final causality, or frontend authority.

## Why Action Attribution Exists

Aegis should eventually answer questions such as:

- What changed?
- Which command may have caused it?
- Which approval allowed it?
- Which session did it belong to?
- Was there evidence?
- Was there verifier success?
- Was the change external, unknown, stale, or impossible to attribute?
- Which changes need operator review?

Before live attribution exists, Aegis needs a strict metadata contract that
prevents causality from being invented from weak, stale, frontend, model, MCP,
tool, or bounded projection data.

## Attribution Subject Categories

Supported subjects:

- `command_effect`
- `file_change`
- `process_change`
- `app_launch_observation`
- `provider_state_change`
- `model_inventory_change`
- `policy_decision_effect`
- `approval_effect`
- `clarification_effect`
- `evidence_state_change`
- `verifier_state_change`
- `replay_state_change`
- `maintenance_finding_change`
- `passive_observe_state_change`
- `repo_audit_readiness_change`
- `memory_governance_change`
- `context_policy_change`
- `capability_lease_candidate_change`
- `external_change_future`
- `unknown`

File and process changes remain future-gated until a later sprint defines a
safe observation boundary.

## Attribution Operations

Supported operations:

- `classify_attribution_candidate`
- `propose_causal_link`
- `propose_source_link`
- `propose_session_link`
- `propose_command_link`
- `propose_approval_link`
- `propose_evidence_ref_link`
- `propose_policy_link`
- `propose_unknown_external_change`
- `propose_operator_attention_summary`
- `propose_change_timeline_future`
- `unknown`

`propose_change_timeline_future` is future-gated. It does not create timelines,
reports, artifacts, evidence, verifier success, or persisted attribution
records.

## Confidence Classes

Supported confidence classes:

- `direct_source_ref`
- `strong_candidate`
- `weak_candidate`
- `inferred_low_trust`
- `conflicting`
- `insufficient_evidence`
- `unknown`

Confidence is a candidate label only. It is not evidence, verifier success, or
final causality.

## Causality Classes

Supported causality classes:

- `causality_not_claimed`
- `direct_causality_candidate`
- `indirect_causality_candidate`
- `temporal_correlation_only`
- `external_or_unknown`
- `conflicting_causality`
- `impossible_to_determine`
- `unknown`

Direct causality requires direct source refs. Temporal correlation, weak
inference, external/unknown attribution, conflicting causality, and impossible
states must remain explicitly labeled.

## Source Classes

Supported source classes:

- `command_lifecycle_projection`
- `approval_projection`
- `policy_projection`
- `evidence_ref_projection`
- `verifier_projection`
- `audit_query_projection`
- `passive_observe_projection`
- `maintenance_projection`
- `caller_supplied_metadata`
- `frontend_supplied_low_trust`
- `model_output_low_trust`
- `mcp_output_low_trust`
- `tool_output_low_trust`
- `future_file_observation_projection`
- `future_integrity_monitor_projection`
- `unknown`

Frontend, model, MCP, and tool outputs are lower trust. They cannot become
authoritative attribution, direct source refs, complete attribution, evidence,
verifier success, or final causality.

## Completeness Classes

Supported completeness classes:

- `complete_for_supplied_projection`
- `bounded_projection_only`
- `partial`
- `stale`
- `conflicting`
- `unavailable`
- `unknown`

Bounded, partial, stale, conflicting, unavailable, and unknown projections
cannot claim complete attribution. Complete attribution is only meaningful for
the supplied projection, and still does not become evidence, verifier success,
or final causality.

## Truthfulness Rules

- Attribution candidate is not evidence.
- Attribution candidate is not verifier success.
- Attribution candidate is not approval.
- Attribution candidate is not permission.
- Attribution candidate is not a lease or capability grant.
- Attribution cannot invent missing command, approval, evidence, verifier, or
  session links.
- Attribution cannot collapse external/unknown changes into Aegis-caused
  changes.
- Attribution cannot collapse temporal correlation into causality.
- Attribution cannot treat bounded audit projections as full history.

## Direct Causality vs Temporal Correlation

`direct_causality_candidate` requires direct source refs and
`direct_source_ref` confidence. The contract still returns
`causality_claim_final=false`.

`temporal_correlation_only` remains temporal-only and requires review. It is not
a command effect, approval effect, evidence proof, or verifier success.

## Unknown, External, and Conflicting Attribution

Unknown, external, impossible, insufficient, and conflicting states are
preserved as explicit output fields. They require human review and must not be
converted into success, Aegis-caused changes, or complete attribution.

## Relationship to Audit Query Layer

Audit Query Layer output is projection metadata. It can be referenced as source
metadata, but it does not provide raw history, live query execution, evidence,
verifier success, or final attribution. Bounded audit query projections cannot
support full attribution claims.

## Relationship to Passive Observe-Only Mode

Passive Observe output remains read-only projection metadata. It is not live
truth and cannot prove causality.

## Relationship to Maintenance Scan and Runtime Health

Maintenance projections can be attribution sources for candidate summaries, but
runtime health, historical debt, unknown issues, replay debt, and resource
warnings must remain visible. Attribution cannot hide or resolve them.

## Relationship to Command Lifecycle, Approval, Policy, Evidence, and Verifier Projections

Command lifecycle, approval, policy, evidence-ref, and verifier projections may
be referenced as source classes. Evidence refs remain refs only. Verifier
projection remains projection only. Approval projection does not grant approval.
Policy projection does not grant execution permission.

## Relationship to Future System Drift and Integrity Monitoring

Future file, process, and integrity monitor projections remain future-gated.
This sprint does not implement watchers, file scans, process scans, integrity
monitoring, or drift detection.

## Relationship to Developer Work Passport and Compliance Evidence

Developer Work Passport and Compliance Evidence decisions are candidate
metadata only. Attribution output is not proof of work quality, compliance,
certification, official audit status, or safety.

## Why Attribution Is Not Evidence, Verifier Success, or Approval

Attribution can describe a candidate relationship between supplied projections.
Evidence must come from backend evidence surfaces. Verifier success must come
from verifier surfaces. Approval must come from approval lifecycle records.
Attribution cannot create or replace any of those authorities.

## Tests Added

`tests/test_core/test_action_attribution.py` covers:

- valid command effect attribution with direct refs
- approval and evidence state attribution boundaries
- passive observe projection-only attribution
- missing required metadata and unsupported taxonomy values
- direct causality requirements
- temporal-only, inferred, conflicting, insufficient, unknown, and external
  preservation
- bounded/stale projection overclaim rejection
- low-trust frontend/model/MCP/tool attribution rejection
- model/provider readiness and lease candidate non-proof behavior
- audit query bounded projection non-full-history behavior
- rejection of live observation, scans, reads, raw journal/evidence access,
  database queries, model/tool/MCP/web calls, memory/context retrieval,
  attribution record creation, timelines, reports, mutations, artifacts, and
  external transfer
- unsafe related decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No live attribution executor
- No file/process watcher
- No repo scan or file read
- No process inspection
- No raw journal or raw evidence read
- No database query
- No model/tool/MCP/web/API call
- No memory or context retrieval
- No attribution record persistence
- No timeline/report/artifact generation
- No runtime/API/frontend integration
- No evidence or verifier success
- No approval, lease, capability, or dispatch grant
- No journal/evidence/replay/runtime mutation

## Future Implementation Notes

A future implementation sprint must define:

- backend-owned source adapters
- time-window and session-link semantics
- exact command, approval, evidence, and verifier reference requirements
- external/unknown attribution handling
- stale/partial/conflicting review flows
- audit logging for attribution attempts
- evidence expectations for live attribution
- verifier expectations for any claimed postcondition
- strict separation between candidate attribution and final causality

## Remaining Risks

- The contract validates metadata only; it does not prove that supplied source
  refs are current, complete, or live.
- Future live attribution could introduce risk if it reads raw state, monitors
  files/processes, or mutates records without a separate boundary sprint.
- Full attribution remains safe only for explicitly complete supplied
  projections and still cannot become final causality by itself.
