# System Drift / Integrity Monitoring Readiness
## Decision

- Decision: `SYSTEM_DRIFT_INTEGRITY_READINESS_WITH_TESTS`
- Contract version: `system-drift-integrity-monitoring-readiness/1`
- Implementation surface: `src/aegis/core/system_drift_integrity.py`
- Test surface: `tests/test_core/test_system_drift_integrity.py`
- Previous sprint: `ACTION_ATTRIBUTION_CONTRACT_WITH_TESTS`

This sprint adds a pure readiness contract for future system drift and
integrity monitoring. It does not implement live monitoring, file watchers,
process watchers, hashing, file reads, repo scans, process inspection, database
queries, raw journal reads, raw evidence reads, model/tool/MCP/web calls,
memory/context retrieval, reports, artifacts, evidence creation, verifier
success, API endpoints, frontend UI, or runtime/journal/evidence/replay
mutation.

## Scope

The contract validates caller-supplied baseline/current metadata and classifies
whether a drift or integrity candidate is:

- ready as metadata-only
- future-gated
- incomplete because baseline/current metadata is missing
- requiring human review
- blocked by missing metadata, authority claims, evidence claims, proof claims,
  live monitoring claims, mutation claims, or unsafe related decisions

The output is non-authoritative. Drift metadata cannot grant permission,
approval, leases, capabilities, evidence, verifier success, runtime dispatch,
proof, final causality, or frontend authority.

## Why System Drift / Integrity Monitoring Exists

Aegis should eventually answer:

- What changed since a known baseline?
- Did config, dependencies, process state, providers, model inventory, app
  registry, tool registry, policy, evidence debt, replay diagnostics, resources,
  or frontend generated artifacts drift?
- Was the change expected, unexpected, Aegis-attributed, external, unknown,
  stale, conflicting, or incomplete?
- Does the candidate require operator attention?
- Which source refs support the candidate?

This sprint defines the metadata boundary before any live monitoring exists.

## Drift Subject Categories

Supported drift subjects:

- `file_metadata_drift`
- `file_hash_drift_future`
- `config_drift`
- `dependency_drift`
- `environment_drift`
- `process_presence_drift`
- `service_port_drift`
- `app_registry_drift`
- `tool_registry_drift`
- `provider_config_drift`
- `model_inventory_drift`
- `policy_boundary_drift`
- `dispatch_surface_drift`
- `memory_governance_drift`
- `context_policy_drift`
- `capability_lease_drift`
- `passive_observe_state_drift`
- `maintenance_projection_drift`
- `evidence_debt_drift`
- `replay_diagnostics_drift`
- `resource_pressure_drift`
- `frontend_generated_drift`
- `external_unknown_drift`
- `unknown`

Future hash, process, and external observation subjects remain future-gated.

## Integrity Subject Categories

Supported integrity subjects:

- `critical_config_integrity`
- `dispatch_policy_integrity`
- `provider_config_integrity`
- `model_metadata_integrity`
- `dependency_integrity`
- `frontend_generated_artifact_integrity`
- `journal_boundary_integrity_future`
- `evidence_ref_integrity_future`
- `repo_source_integrity_future`
- `plugin_manifest_integrity`
- `vertical_pack_integrity`
- `unknown`

Journal, evidence, and repo-source integrity are future-gated until explicit
backend-owned read/hash/evidence boundaries exist.

## Drift Operations

Supported operations:

- `classify_drift_candidate`
- `compare_supplied_baseline_metadata`
- `compare_supplied_current_metadata`
- `propose_integrity_finding`
- `propose_operator_attention`
- `propose_expected_change`
- `propose_external_or_unknown_change`
- `propose_future_monitoring_scope`
- `unknown`

`propose_future_monitoring_scope` is future-gated. It does not start watchers,
monitoring, scans, hash computation, or background indexing.

## Drift Status Classes

Supported drift statuses:

- `no_drift_claimed`
- `drift_candidate`
- `expected_change_candidate`
- `unexpected_change_candidate`
- `external_or_unknown_change`
- `conflicting_change`
- `stale_baseline`
- `missing_baseline`
- `missing_current_state`
- `insufficient_metadata`
- `future_gated`
- `unknown`

## Integrity Status Classes

Supported integrity statuses:

- `integrity_not_claimed`
- `integrity_candidate`
- `integrity_warning_candidate`
- `integrity_blocker_candidate`
- `integrity_unknown`
- `integrity_unavailable`
- `future_gated`
- `unknown`

Integrity candidates are not proof, evidence, verifier success, or runtime
truth.

## Baseline and Current Source Classes

Baseline source classes:

- `caller_supplied_baseline`
- `maintenance_projection_baseline`
- `passive_observe_baseline`
- `audit_query_projection_baseline`
- `action_attribution_projection_baseline`
- `config_metadata_baseline`
- `repo_audit_readiness_baseline`
- `future_file_hash_baseline`
- `future_process_snapshot_baseline`
- `unknown`

Current source classes:

- `caller_supplied_current_metadata`
- `maintenance_projection_current`
- `passive_observe_current`
- `audit_query_projection_current`
- `action_attribution_projection_current`
- `config_metadata_current`
- `repo_audit_readiness_current`
- `future_file_hash_current`
- `future_process_snapshot_current`
- `unknown`

Future hash and process snapshot classes are future-gated. They do not imply
hash computation or process inspection happened.

## Attribution Relationship Classes

Supported attribution relationships:

- `not_attributed`
- `aegis_attributed_candidate`
- `external_candidate`
- `unknown_external`
- `temporal_correlation_only`
- `conflicting_attribution`
- `attribution_unavailable`
- `unknown`

Attribution relationships are candidate labels only. They are not final
causality.

## Severity Classes

Supported severity classes:

- `info`
- `low`
- `medium`
- `high`
- `critical`
- `unknown`

Severity is a review cue. It is not proof of verified drift.

## Completeness Classes

Supported completeness classes:

- `complete_for_supplied_metadata`
- `bounded_metadata_only`
- `partial`
- `stale`
- `conflicting`
- `unavailable`
- `unknown`

Bounded, partial, stale, conflicting, unavailable, and unknown metadata cannot
claim full drift analysis.

## Truthfulness Rules

- Drift candidate is not proof.
- Integrity candidate is not evidence.
- Hash metadata is not verifier success.
- Baseline comparison is not permission.
- Drift attribution is not final causality.
- Expected changes are not integrity success.
- Unexpected changes are not proof.
- Temporal correlation cannot become expected attributed change.
- Frontend/model/MCP/tool output cannot become authority or truth.
- Missing baselines, stale baselines, missing current state, insufficient
  metadata, external/unknown changes, and conflicting changes remain explicit.

## Missing, Stale, and Conflicting Baseline Rules

Missing baseline, stale baseline, missing current state, insufficient metadata,
and conflicting state all require review. The contract preserves these states
and never converts them into no-drift, integrity success, proof, or verifier
success.

## Expected vs Unexpected vs External/Unknown Drift

Expected change, unexpected change, and external/unknown change are distinct
candidate states:

- expected change does not imply integrity success
- unexpected change does not imply proof
- external/unknown change does not become Aegis-attributed drift
- temporal correlation remains temporal-only

## Current Blocker vs Historical and Resource Debt

The contract preserves current blockers, historical debt, and resource debt as
separate flags. It does not hide runtime health fail, replay debt, unknown-era
issues, or resource warnings.

## Relationship to Action Attribution

Action Attribution output can be referenced as candidate metadata. It cannot
become final causality or drift proof.

## Relationship to Audit Query Layer

Audit Query Layer output remains projection metadata. Bounded projections do not
authorize full drift analysis, raw journal access, raw evidence access, or live
query execution.

## Relationship to Passive Observe-Only Mode

Passive Observe output remains read-only projection metadata and not live truth.

## Relationship to Maintenance Scan and Runtime Health

Maintenance scan and runtime health projections can be referenced, but drift
readiness cannot mutate maintenance state, hide debt, or fake healthy runtime
state.

## Relationship to Evidence and Replay Diagnostics

Evidence and replay diagnostics remain projection/ref surfaces unless a future
backend-owned evidence boundary is explicitly added. This contract does not read
raw evidence, read raw journals, mutate replay state, or mark verifier success.

## Relationship to Future File, Process, and Hash Monitoring

Future file hash, process snapshot, journal boundary, evidence ref, and repo
source integrity surfaces are future-gated. This sprint does not start
monitoring, watch files or processes, scan, read files, or compute hashes.

## Relationship to Developer Work Passport and Compliance Evidence

Developer Work Passport and Compliance Evidence decisions are reference-only
candidate metadata. Drift/integrity readiness output is not proof of compliance,
work quality, safety, certification, or official audit status.

## Why Drift and Integrity Candidates Are Not Evidence, Verifier Success, or Proof

Drift and integrity candidates classify supplied metadata. Evidence must come
from backend evidence surfaces. Verifier success must come from verifier
surfaces. Proof requires future explicit source, evidence, verifier, and audit
boundaries.

## Tests Added

`tests/test_core/test_system_drift_integrity.py` covers:

- valid config, frontend-generated, dispatch-surface, and resource-pressure
  drift candidates
- missing required metadata and unsupported taxonomy values
- missing baseline, stale baseline, missing current state, insufficient
  metadata, external/unknown, and conflicting state preservation
- expected/unexpected/temporal-correlation truthfulness boundaries
- action attribution candidate non-final-causality boundary
- bounded metadata full-analysis rejection
- future hash/process source future-gating
- rejection of monitoring, watchers, scans, reads, hash computation, raw
  journal/evidence reads, database queries, model/tool/MCP/web calls,
  memory/context retrieval, records, reports, mutations, artifacts, and
  external transfer
- unsafe related decision rejection
- input immutability and frozen output

## Intentionally Not Done

- No live integrity monitoring
- No file/process watchers
- No file reads, repo scans, or hash computation
- No process inspection
- No raw journal or raw evidence reads
- No database queries
- No model/tool/MCP/web/API calls
- No memory or context retrieval
- No drift/integrity record persistence
- No timeline/report/artifact generation
- No runtime/API/frontend integration
- No evidence or verifier success
- No approval, lease, capability, or dispatch grant
- No journal/evidence/replay/runtime mutation

## Future Implementation Notes

A future implementation sprint must define:

- backend-owned baseline sources
- backend-owned current-state sources
- file/process/hash observation boundaries
- allowed path/process scopes
- evidence expectations for each observation
- verifier expectations for each finding
- drift record persistence rules
- review flows for missing/stale/conflicting/external changes
- strict separation between drift candidate and proof

## Remaining Risks

- The contract validates supplied metadata only; it does not prove that supplied
  baseline/current refs are complete or current.
- Future live monitoring could introduce risk if it reads files, watches
  processes, computes hashes, or writes records without a separate safety
  boundary sprint.
- Integrity candidates remain candidate-only until backend evidence and verifier
  boundaries are implemented.
