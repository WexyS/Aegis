# Historical Evidence / Replay Debt Inventory v1

## A. Decision

- Decision: `INVENTORY_DOCUMENTED_ONLY`
- Recorded at: `2026-05-31T21:43:26+03:00`
- Current inventory commit baseline: `0e2965769e5461ed5eb6d57a9da1499c8cdeb262`
- Foundation baseline tag: `foundation-v1-baseline`
- Foundation baseline document commit: `2662d5de0be805985d095c83a2f11c646a4b6fc2`
- Accepted baseline condition: `READY_FOR_BASELINE_WITH_KNOWN_HISTORICAL_DEBT`

This report is read-only inventory. It does not clean, mutate, rewrite,
compact, repair, delete, reclassify, or hide journal, evidence, replay, pending
decision, or maintenance data.

## B. Source of Truth

| Area | Authoritative surface | Notes |
| --- | --- | --- |
| Evidence debt | `audit_action_evidence()` in `src/aegis/core/evidence_audit.py`; surfaced at `checks.evidence_audit` | Uses recent journal events supplied by maintenance plus command lifecycle snapshot. |
| Unknown-era issues | Evidence audit era classification and command lifecycle classification | Unknown remains unknown when current/historical proof is unavailable. |
| Replay diagnostics | `build_runtime_replay_gap_diagnostics()` in `src/aegis/core/journal_cleanup.py`; surfaced at `checks.replay_diagnostics` | Reads the journal file directly and reports sequence, control-plane, and hash-chain risk. |
| Pending decision hygiene | `build_pending_decision_hygiene_report()` in `src/aegis/core/pending_decision_hygiene.py`; surfaced at `checks.pending_decision_hygiene` | Read-only command lifecycle hygiene report. |
| Foundation readiness | `_foundation_closure_readiness()` in `src/aegis/core/maintenance.py`; surfaced at `checks.foundation_closure_readiness` | Projection only; separate from runtime health. |
| Runtime health | `_runtime_health_summary()` in `src/aegis/core/maintenance.py`; surfaced as maintenance `summary` and `checks.runtime_health` | Direct component health signal; not greenwashed by closure readiness. |
| Event journal integrity | `RuntimeEventJournal.snapshot()` and `verify_integrity_locked()` in `src/aegis/core/event_journal.py` | Snapshot is based on the in-memory journal tail and integrity state. |

## C. Baseline vs Current Comparison

| Metric | Foundation baseline | Current live scan | Direction |
| --- | ---: | ---: | --- |
| Runtime health | `fail` | `fail` | unchanged |
| Closure readiness | `needs_operator_attention` | `needs_operator_attention` | unchanged |
| Current blocker count | `0` | `0` | unchanged |
| Current evidence failure count | `0` | `0` | unchanged |
| Current missing evidence count | `0` | `0` | unchanged |
| Pending decision hygiene | `ok` | `ok` | unchanged |
| Pending count | `0` | `0` | unchanged |
| Restored pending count | `0` | `0` | unchanged |
| Historical evidence debt count | `26` | `18` | decreased |
| Historical missing evidence count | `23` | `16` | decreased |
| Unknown-era evidence issue count | `10` | `10` | unchanged |
| Unknown-era missing evidence count | `0` | `0` | unchanged |
| Replay diagnostics status | `fail` | `fail` | unchanged |
| Replay boundary classification | `historical_mixed_sequence_eras_or_reset_boundaries` | `historical_mixed_sequence_eras_or_reset_boundaries` | unchanged |
| Replay cleanup execution blocked | not separately recorded | `true` | visible |
| System resources | `warning` | `warning` | unchanged |
| Disk usage | `92.1%` | `92.1%` | unchanged |
| Maintenance read-only | `true` | `true` | unchanged |
| Closure mutation performed | `false` | `false` | unchanged |

Current live evidence audit details:

- Evidence audit status: `fail`
- Action event count: `71`
- Projected action count: `33`
- Evidence audit limit: `50`
- Scope: `all_recent_action_events`
- Missing evidence count: `16`
- Historical evidence debt count: `18`
- Historical missing evidence count: `16`
- Unknown-era evidence issue count: `10`
- Unknown-era missing evidence count: `0`
- Failed evidence count: `2`
- Negative evidence count: `0`
- Verifier check failure count: `0`
- Critical/check classes still include `verifier_check_failed: 2`
- Omitted action classification count: `13`
- Omitted command lifecycle classification count: `0`

Current live replay diagnostics details:

- Journal event count scanned: `155114`
- Parse errors: `0`
- Sequence decreases: `785`
- Sequence gaps: `669`
- Duplicate occurrence count: `59675`
- Duplicate sequence count: `1131`
- Mixed sequence eras suspected: `true`
- Control-plane events: `283`
- `SNAPSHOT_CREATED`: `221`
- `SYSTEM_ONLINE`: `62`
- Recursive snapshot risk count: `88`
- Hash-chain mismatches: `1`
- Replay blocker: `mixed_sequence_eras`
- Replay cleanup execution blocked: `true`

## D. Count Drift Explanation

### Proven from code

- Maintenance calls `runtime_journal.recent_events()` and passes those events to
  `audit_action_evidence(..., limit=50, include_historical=True, ...)`.
- `RuntimeEventJournal.recent_events()` returns the in-memory journal tail, not a
  fresh full-file scan.
- `project_action_timeline(..., limit=50, ...)` bounds the action projection to
  the latest 50 combined action/non-executable timeline records.
- `ApprovalManager.snapshot()` returns command lifecycle `records[-50:]`.
- Evidence audit counts historical action issues from the bounded action
  timeline and unverified completed command issues from the bounded command
  snapshot.
- Therefore historical evidence debt and historical missing evidence counts can
  drift between scans when newer runtime events or command records enter the
  bounded projections and older historical records fall out.
- Replay diagnostics are different: `build_runtime_replay_gap_diagnostics()`
  opens the journal file and scans it directly. Replay counts are therefore not
  bounded by the evidence audit `limit=50` projection.
- Unknown-era issue count can remain stable while historical missing evidence
  changes because current live unknown-era issues are currently represented by
  `unknown_era_unverified_completed: 10`, not by unknown-era missing evidence.

### Likely but not proven from current inspection

- The decrease from `26 -> 18` historical evidence debt and `23 -> 16`
  historical missing evidence is consistent with the bounded action projection
  shifting after later scans/runtime events.
- It is also consistent with command lifecycle records being reconciled or
  replaced by newer records before this inventory sprint.

### Not established

- The current code inspection does not prove that any journal cleanup occurred.
- The current code inspection does not prove that historical records were
  repaired, deleted, or reclassified.
- The current code inspection does not prove a single exact event-by-event cause
  for each count difference between the baseline and current scan.
- No unknown-era issue was proven historical by this inventory.

## E. Debt Category Inventory

| Category | Current state | Inventory classification |
| --- | --- | --- |
| Current evidence failure | `0` | No current evidence failure in latest scan. |
| Current missing evidence | `0` | No current missing evidence in latest scan. |
| Historical evidence debt | `18` | Visible historical debt; not cleaned. |
| Historical missing evidence | `16` | Visible historical missing evidence; not verified. |
| Unknown-era evidence issue | `10` | Conservative unknown-era debt; not guessed as historical. |
| Unknown-era missing evidence | `0` | No unknown-era missing evidence in latest scan, but category remains monitored. |
| Evidence failed | `2` failed evidence records | Failed evidence remains non-success. |
| Negative evidence backed | `0` in latest scan | Category supported by evidence audit, but not present in current live window. |
| Unverified completed command | `10` command lifecycle unverified completed | Classified as unknown-era unverified completed due unavailable proof and replay attention. |
| Replay gaps | `669` gaps | Replay-boundary debt; cleanup execution blocked. |
| Duplicate sequences | `1131` duplicate sequence numbers, `59675` duplicate occurrences | Replay cursor ambiguity; cleanup execution blocked. |
| Mixed sequence eras / reset boundaries | `785` decreases, mixed era suspected | Primary replay blocker. |
| Recursive snapshot risk | `88` | Historical control-plane bloat risk; archive/compaction requires explicit boundary. |
| Hash-chain risk | `1` mismatch | Hash-chain boundary risk; cleanup execution blocked. |
| Restored unresolved approval risk | `0` pending/restored pending | No current pending approval blocker. |
| Resource warnings | disk `92.1%`, status `warning` | Environmental debt; not journal cleanup eligible. |

## F. Cleanup Eligibility

| Current category | Eligibility rule | Rationale |
| --- | --- | --- |
| Current evidence failure `0` | none active; future nonzero becomes `current_blocker_blocked` | Current failures must be investigated before cleanup. |
| Current missing evidence `0` | none active; future nonzero becomes `current_blocker_blocked` | Missing current evidence is not historical debt. |
| Historical evidence debt `18` | `documentation_only` or future `archive_candidate_requires_operator_approval` | Must remain visible and preserved. |
| Historical missing evidence `16` | `documentation_only` or future `archive_candidate_requires_operator_approval` | Must not be marked verified. |
| Unknown-era evidence issue `10` | `unknown_era_quarantine` | Cannot be treated as historical without trusted metadata. |
| Failed evidence `2` | era-dependent; never verified | Preserve failed state and verifier/check context. |
| Unverified completed command `10` | `unknown_era_quarantine` | Current metadata does not prove historical era. |
| Replay gaps / duplicates / mixed eras | `replay_boundary_blocked` | Cleanup execution remains blocked until replay boundary proof exists. |
| Hash-chain mismatch | `hash_chain_blocked` | Requires original hash, backup, restore, replay, and explicit boundary strategy. |
| Recursive snapshot risk | future archive candidate only after blockers clear | Control-plane bloat must not be removed silently. |
| Restored approvals `0` | none active; future nonzero becomes `current_blocker_blocked` | Pending decisions require backend lifecycle handling. |
| Resource warning | `documentation_only` | Environment issue, not cleanup permission. |

## G. Recommendation

The inventory is sufficient for the current frontend/operator clarity path. No
new read-only helper is necessary yet because existing maintenance output already
exposes:

- evidence audit scope and limit,
- action and command lifecycle counts,
- current/historical/unknown-era split,
- class counts,
- replay sequence/control-plane/hash-chain details,
- pending decision hygiene,
- closure readiness,
- read-only and mutation flags.

Recommended next prompt:

`App Registry relevance/noise reduction v1`

Alternative prompt if a future operator needs exact event-level diff attribution
for the `26 -> 18` drift:

`Evidence/Replay Inventory Diagnostics v1`

That alternative should add a read-only event-level inventory helper only if the
operator needs exact record identifiers beyond the current bounded maintenance
projection.
