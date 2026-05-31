# Historical Evidence / Replay Debt Cleanup Design v1

- Design name: `Historical Evidence/Replay Debt Cleanup Design v1`
- Baseline: `foundation-v1-baseline`
- Baseline checkpoint commit: `2662d5de0be805985d095c83a2f11c646a4b6fc2`
- Baseline source commit: `b209db92d54d669a73cf98d63dbf869c8872bc07`
- Accepted condition: `READY_FOR_BASELINE_WITH_KNOWN_HISTORICAL_DEBT`
- Design recorded at: `2026-05-31T21:14:25+03:00`

This document is a read-only cleanup readiness design. It does not authorize
journal cleanup, archive execution, compaction, evidence rewrite, unknown-era
reclassification, or runtime health greenwashing.

## Current Baseline Debt

At the Foundation v1 baseline, current blockers are accepted as clear while
known historical, unknown-era, replay, and resource debt remain visible:

- Current blocker count: `0`
- Current evidence failure count: `0`
- Current missing evidence count: `0`
- Pending decision hygiene: `ok`
- Pending count: `0`
- Restored pending count: `0`
- Historical evidence debt count: `26`
- Historical missing evidence count: `23`
- Unknown-era evidence issue count: `10`
- Unknown-era missing evidence count: `0`
- Replay diagnostics status: `fail`
- Replay boundary classification: `historical_mixed_sequence_eras_or_reset_boundaries`
- System resource warning: disk usage around `92.1%`

Runtime health may remain `fail`. That is intentional until the visible debt is
handled or explicitly accepted by later operator-reviewed work.

## Debt Categories

| Category | Source of truth | Current/historical/unknown | Cleanup eligibility | Required handling |
| --- | --- | --- | --- | --- |
| Current evidence failure | `checks.evidence_audit.current_evidence_failure_count` | Current | `current_blocker_blocked` | Investigate before cleanup; never archive away as historical debt. |
| Current missing evidence | `checks.evidence_audit.current_missing_evidence_count` | Current | `current_blocker_blocked` | Treat as actionable runtime evidence gap. |
| Historical evidence debt | `checks.evidence_audit.historical_evidence_debt_count` | Historical when backed by session/restored metadata | `documentation_only` or `archive_candidate_requires_operator_approval` | Keep visible; future archive planning may reference it but must preserve records. |
| Historical missing evidence | `checks.evidence_audit.historical_missing_evidence_count` | Historical when proved by trusted metadata | `documentation_only` or `archive_candidate_requires_operator_approval` | Do not mark verified; document as historical missing evidence. |
| Unknown-era evidence issue | `checks.evidence_audit.unknown_era_evidence_issue_count` | Unknown | `unknown_era_quarantine` | Keep visible; do not infer historical status without proof. |
| Unknown-era missing evidence | `checks.evidence_audit.unknown_era_missing_evidence_count` | Unknown | `unknown_era_quarantine` | Keep visible and non-success even if count is zero at baseline. |
| Evidence failed | `failed_evidence_count`, verifier checks | Current, historical, or unknown by classification | Depends on era; never `verified` | Preserve failed state and verifier details. |
| Negative evidence backed | `negative_evidence_count`, `executor-negative-evidence/1` | Era-specific | `documentation_only` | Count as backed failed/unverified evidence, not missing and not success. |
| Unverified completed command | command lifecycle snapshot plus evidence audit classification | Historical or unknown unless current session proves current | `documentation_only` or `unknown_era_quarantine` | Do not convert to verified; keep visible until direct evidence exists. |
| Replay gaps | `checks.replay_diagnostics.sequence.gap_count` | Replay-boundary related | `replay_boundary_blocked` | Requires isolated replay analysis before any archive/compaction planning. |
| Duplicate sequences | `duplicate_sequence_count` / `duplicate_occurrence_count` | Replay-boundary related | `replay_boundary_blocked` | Blocks cleanup execution until cursor semantics are explicitly resolved. |
| Mixed sequence eras / reset boundaries | `mixed_sequence_eras_suspected`, sequence decreases | Replay-boundary related | `replay_boundary_blocked` | Current baseline blocker for cleanup execution; never resequence in place. |
| Recursive snapshot risk | replay/control-plane diagnostics | Historical control-plane bloat | `archive_candidate_requires_operator_approval` only after replay boundary clears | Preserve source journal; no silent snapshot removal. |
| Hash-chain risk | event journal integrity and cleanup boundary validation | Integrity boundary | `hash_chain_blocked` | Requires explicit boundary proof and original journal hash preservation. |
| Restored unresolved approval risk | pending decision hygiene | Current backend lifecycle if present | `current_blocker_blocked` when pending | Baseline count is zero; future pending records require backend lifecycle resolution. |
| Resource warnings | system diagnostics | Environment | `documentation_only` | Not journal cleanup eligible; keep visible until operator remediates disk/resource pressure. |

## Eligibility Rules

`not_cleanup_eligible`

- Inputs: current blockers, current evidence failures, current missing evidence,
  pending decisions, approval/policy uncertainty, or untrusted metadata.
- Required proof: direct current-session evidence that the issue is not current,
  or backend lifecycle resolution for pending decisions.
- Required validation: focused evidence, command lifecycle, and maintenance tests.
- Failure mode: cleanup sprint stops; no archive, compaction, deletion, or
  reclassification.
- Future mutation allowed: no.

`documentation_only`

- Inputs: debt already classified by existing read-only diagnostics and not
  requiring journal changes.
- Required proof: maintenance/evidence/replay diagnostics remain visible and
  read-only.
- Required validation: `git diff --check` plus relevant evidence, maintenance,
  journal cleanup, and threat-model tests.
- Failure mode: document remains draft or is not committed.
- Future mutation allowed: no.

`archive_candidate_requires_operator_approval`

- Inputs: historical evidence or control-plane debt that can be preserved in an
  immutable archive without deleting the source journal.
- Required proof: original journal path, original SHA-256, backup path outside
  the source journal, restore plan, replay plan, evidence preservation statement,
  and operator approval.
- Required validation: backup verification, restore rehearsal, replay validation,
  hash-chain validation, and evidence audit preservation checks.
- Failure mode: abort before mutation; keep source journal untouched.
- Future mutation allowed: archive-only in a later explicitly approved sprint.

`compaction_candidate_requires_backup_restore_replay_validation`

- Inputs: future explicit compaction plan after archive-only readiness is proven.
- Required proof: explicit compaction boundary, original archive, restore plan,
  replay validation, hash-chain strategy, evidence preservation, and operator
  boundary approval.
- Required validation: isolated temp-copy replay and post-action audit must pass
  before any source-facing operation is considered.
- Failure mode: rollback to untouched source journal and preserved archive.
- Future mutation allowed: only in a later boundary-approved sprint; in-place
  rewrite/truncate/delete remains forbidden by default.

`unknown_era_quarantine`

- Inputs: evidence issues without trusted current-session, historical session,
  restored metadata, or source snapshot proof.
- Required proof: direct metadata that establishes era; `restored_at` alone is
  not original event age.
- Required validation: evidence audit confirms unknown-era count decreases only
  when proof exists.
- Failure mode: keep unknown-era issue visible and non-success.
- Future mutation allowed: no.

`hash_chain_blocked`

- Inputs: hash-chain mismatch, missing original hash, malformed journal, or
  boundary validation requiring explicit hash handling.
- Required proof: original SHA-256, preserved archive, and explicit boundary
  strategy.
- Required validation: hash-chain/integrity checks before and after any future
  action.
- Failure mode: cleanup execution remains blocked.
- Future mutation allowed: no until a later boundary sprint approves it.

`replay_boundary_blocked`

- Inputs: mixed sequence eras, sequence decreases, gaps, duplicate sequences, or
  snapshot resync fallback risk.
- Required proof: replay cursor semantics are documented and validated on an
  isolated copy.
- Required validation: replay from original and candidate archive/compaction
  outputs, including evidence and command lifecycle preservation.
- Failure mode: cleanup execution remains blocked and runtime health remains
  honest.
- Future mutation allowed: no until boundary proof and operator approval exist.

`current_blocker_blocked`

- Inputs: current evidence failure, current missing evidence, pending decision,
  command lifecycle failure, or runtime snapshot failure.
- Required proof: current blocker resolved by normal runtime lifecycle and
  verified by maintenance scan.
- Required validation: focused current-failure tests plus read-only maintenance
  scan.
- Failure mode: no baseline cleanup activity.
- Future mutation allowed: no.

## Future Cleanup Preconditions

Before any future cleanup action can be considered, all of the following must be
true:

1. Current blocker count is `0`.
2. Current evidence failure count is `0`.
3. Current missing evidence count is `0`.
4. Pending decision hygiene is `ok`, with pending and restored pending counts
   at `0`.
5. Historical and unknown-era debt remains visible in maintenance output.
6. Unknown-era records are not reclassified without trusted metadata.
7. Replay diagnostics are reviewed and any boundary blocker is explicitly
   addressed.
8. Original journal SHA-256 is recorded before any candidate action.
9. Backup path is separate from the source journal and is writable.
10. Restore plan is documented before mutation.
11. Replay validation plan is documented before mutation.
12. Evidence preservation statement covers failed, missing, unverified, and
    negative evidence.
13. Operator approval is explicit, scoped, and separate from any approval grant
    path.

## Required Backup, Restore, Replay, and Hash Checks

Any future archive or compaction sprint must perform these checks in order:

1. Record source journal path, size, event count, first/last sequence, and
   SHA-256.
2. Create a backup outside the source journal path.
3. Verify backup SHA-256 equals the original SHA-256.
4. Rehearse restore in an isolated temporary copy, not the live runtime path.
5. Replay the isolated copy and compare command lifecycle, evidence audit,
   pending decision hygiene, and replay diagnostics.
6. Verify hash-chain behavior and document any explicit boundary.
7. Verify failed, missing, unverified, and negative evidence records remain
   visible.
8. Verify unknown-era records remain unknown unless proven otherwise.
9. Require an operator checkpoint before any archive action.
10. After any future action, rerun maintenance and compare against the preflight
    report.

If validation fails at any point, the future sprint must abort, preserve the
original journal and backup, record the failed check, and leave runtime health
non-greenwashed.

## UI and Maintenance Wording

Maintenance and UI should keep these distinctions clear:

- Use "current blocker" only for current-session evidence, lifecycle, pending,
  or runtime issues.
- Use "historical evidence debt" only when trusted metadata proves historical
  scope.
- Use "unknown-era evidence issue" when proof is insufficient.
- Use "replay boundary blocked" for mixed sequence eras, gaps, duplicate
  sequences, or reset-boundary risks.
- Use "negative evidence backed" for explicit failed/unverified evidence.
- Avoid "clean", "fixed", "resolved", "healthy", or "safe" unless the backend
  source of truth proves it.
- State "no mutation performed" for read-only scans.
- State that runtime health may remain `fail` while historical, unknown-era,
  replay, or resource debt remains visible.

## Future Phases

Phase 0: read-only debt inventory and operator report.

Phase 1: backup/export plan generation with no journal mutation.

Phase 2: restore rehearsal in an isolated temporary copy.

Phase 3: replay validation on the isolated copy.

Phase 4: hash-chain and integrity validation.

Phase 5: explicit operator approval checkpoint.

Phase 6: archive-only action with no source deletion.

Phase 7: optional compaction plan. Source journal rewrite, truncation, deletion,
or resequencing remains forbidden unless a later explicitly approved boundary
sprint proves it is safe.

Phase 8: post-action audit, maintenance comparison, rollback verification, and
operator report.

## Non-Goals

- No journal mutation, rewrite, truncation, repair, deletion, compaction, or
  resequencing.
- No evidence rewrite or fabricated verification.
- No unknown-era debt reclassification without proof.
- No runtime health greenwashing.
- No approval, policy, verifier, runtime authority, command lifecycle, or
  evidence semantic change.
- No Context Compiler, Memory OS, MCP Gateway, Model Router, capability lease,
  plugin architecture, or other post-foundation module work.

## Recommended Next Workstream

`Maintenance / Foundation Readiness UI Clarity v1`

The next sprint should improve operator wording and visibility for Foundation
readiness versus runtime health without changing backend truth, hiding debt, or
adding cleanup actions.
