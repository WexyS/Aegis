# Historical Evidence Replay Debt Closure

Decision: `HISTORICAL_EVIDENCE_REPLAY_APPLY_GATE_READY_BUT_BLOCKED`

Date: 2026-06-13

Scope: safe closure readiness only. This document does not archive, compact,
truncate, rewrite, resequence, delete, or mutate runtime journals, evidence
records, runtime state, Git history, or generated artifacts.

## Why This Exists

Aegis keeps historical, unknown-era, and replay debt visible. That is correct.
The next step is not to hide it; the next step is to close it with an
operational model that preserves inspectability while preventing safely retired
older debt from blocking current product work forever.

Missing historical evidence cannot be reconstructed unless source evidence
actually exists. Unknown-era issues must not be guessed into success.

## Current Observed State

The read-only maintenance scan for this closure sprint reported:

- scan version: `maintenance-scan/1`
- runtime health summary status: `fail`
- current blocker count: 0
- current evidence failure count: 0
- current missing evidence count: 0
- historical evidence debt count: 0
- historical missing evidence count: 0
- unknown-era evidence issue count: 25
- unknown-era missing evidence count: 19
- replay diagnostics status: `fail`
- replay boundary classification:
  `historical_mixed_sequence_eras_or_reset_boundaries`
- closure readiness status: `needs_operator_attention`

No current evidence failure or current missing evidence was observed. Closure
execution remains blocked because the unknown-era and replay-boundary debt
cannot be safely retired without backup, restore, replay/hash-chain, exact-item
listing, and operator gates.

## Implementation Added

The closure work now has a dry-run planner, exact-item manifest contract, gate
validators, and a manifest-only apply boundary:

- module: `src/aegis/core/historical_debt_closure.py`
- helper:
  `build_historical_evidence_replay_debt_closure_plan(...)`
- item manifest:
  `build_historical_debt_item_manifest(...)`
- backup metadata:
  `build_historical_debt_backup_manifest(...)`
- replay/hash-chain gate:
  `build_manifest_only_replay_hash_chain_gate(...)`
- apply-readiness boundary:
  `evaluate_historical_evidence_replay_debt_closure_apply_readiness(...)`
- manifest-only apply:
  `apply_manifest_only_historical_evidence_replay_quarantine(...)`

The helpers consume caller-supplied maintenance/evidence/replay metadata only
unless the caller explicitly supplies a manifest store. They do not read
journals, create backup artifacts, fabricate evidence, mark verifier success,
rewrite replay history, or mutate original runtime stores.

Manifest-only apply is intentionally narrow. It can write archive/quarantine
and clean-current-baseline state only into a caller-supplied manifest store
after every gate passes. Original journal, evidence, and replay stores remain
untouched.

The maintenance scan projection now explicitly separates:

- active operational debt
- archived historical debt status
- quarantined unknown-era debt status
- closure execution status

Current live output intentionally reports `not_archived`, `not_quarantined`,
and `not_executed` because local apply remains blocked.

## Debt Classes

| Debt class | Meaning | Closure treatment |
| --- | --- | --- |
| Active operational debt | Current blockers, current missing evidence, current evidence failures, pending approvals, restored pending work, or live runtime inconsistency. | Must be fixed or explicitly blocked before clean baseline. |
| Historical debt | Old event/evidence/replay issues with known historical classification. | Can be archived only after exact listing, backup, restore, replay/hash-chain, and operator gates pass. |
| Unknown-era evidence | Events without enough session/source context to prove current or historical era. | Must remain visible unless source evidence resolves the classification. |
| Replay boundary debt | Sequence resets, hash-chain mismatch, mixed eras, recursive snapshots, or replay discontinuities. | Requires backup, restore, replay/hash-chain checks, exact boundary reasoning, and operator approval before closure. |
| Resource/log pressure | Large local journals, logs, caches, or generated artifacts. | Requires backup and explicit cleanup sprint; no blind deletion. |

## What Can Be Repaired

These may be repaired in future scoped sprints:

- current missing evidence where current backend evidence exists but is not
  linked correctly
- current evidence failures caused by verifier bugs
- journal projection/snapshot alignment bugs
- process-local state that can be rebuilt from canonical journal entries
- generated drift that can be restored or intentionally regenerated
- stale docs that misclassify historical debt as current product state

## What Cannot Be Repaired By Guessing

These must not be fabricated:

- missing execution evidence for old actions when no source evidence exists
- verifier success for actions that never passed verifier checks
- event hashes or previous hashes that do not match known source records
- exact session identity for unknown-era events without source evidence
- approval state for historical actions without backend lifecycle evidence
- runtime health claims that require hidden debt suppression

## Closure Model

The correct closure model has four durable parts:

1. Backup snapshot
   - Copy journal, evidence, runtime metadata, and relevant config into an
     operator-approved backup location.
   - Record file sizes and hashes.
   - Do not mutate source files during backup verification.

2. Archived legacy manifest
   - List historical issues exactly as observed.
   - Preserve reason, source, era classification, and uncertainty.
   - Include hash references to backed-up source artifacts.
   - Mark non-reconstructable missing evidence as non-reconstructable.

3. Unknown-era quarantine manifest
   - List unknown-era issues exactly as observed.
   - Preserve why each item is still unknown.
   - Do not convert unknown-era items into historical success.
   - Keep the manifest inspectable after closure.

4. Clean current operational baseline
   - New runtime health can separate current operational blockers from archived
     or quarantined legacy debt.
   - Active runtime must not fail solely because safely retired debt remains
     archived.
   - Archived and quarantined debt must remain reportable.

## Required Gates

No closure execution is allowed until all gates pass:

- operator confirms closure scope
- backup path is explicit and project-approved
- backup manifest is written and hashes are recorded
- restore/readback verification passes in an isolated location
- replay/hash-chain verification passes or records exact irreparable gaps
- exact historical and unknown-era items are listed
- current pending approvals are zero or explicitly preserved
- current evidence failures are zero or explicitly blocked
- current missing evidence is zero or explicitly blocked
- maintenance scan continues to expose archived/quarantined debt separately
- no generated artifacts or secrets are staged
- operator confirms no-suppression and no-guessing rules

The operator confirmation must reference the exact dry-run plan id or backup
id. A generic confirmation is not sufficient.

## No-Suppression Rule

Maintenance scan must not hide:

- unknown-era evidence issues
- replay boundary debt
- hash-chain mismatches
- missing historical evidence
- negative evidence
- failed verifier checks
- unverified completed actions
- resource/log pressure

Closure may move retired debt to archived or quarantined sections only after
all gates pass. It must not delete the debt from observability.

## No-Guessing Rule

If missing historical evidence cannot be reconstructed from source records, it
remains missing. The correct status is archived non-reconstructable, not
verified.

If an unknown-era item cannot be assigned to a session with source evidence, it
remains unknown-era. The correct status is quarantined unknown-era, not
historical success.

## Maintenance Scan Reporting Target

Maintenance scan should report:

- current operational health
- current blockers
- current evidence failures
- current missing evidence
- pending decisions
- archived historical debt summary
- archived manifest reference
- quarantined unknown-era debt summary
- replay/hash-chain closure status
- whether archived or quarantined debt still needs operator attention

Current health should not fail solely because archived older debt is preserved.
It should still fail for active blockers, current missing evidence, current
evidence failures, replay/hash-chain issues in the current baseline, or hidden
debt.

## Current Closure Result

The apply gate exists, but local apply remains blocked.

Reasons:

- replay diagnostics still fail
- unknown-era evidence issues remain
- unknown-era missing evidence remains
- live evidence classification output lists only 20 action classifications
  while unknown-era issue count is 25
- exact item manifest is therefore incomplete for local apply
- no runtime backup artifact was created in this sprint
- no restore/readback verification artifact was created
- no operator confirmation referencing the live plan id or backup id was
  provided
- no local manifest store apply was executed

This is the correct result. The sprint produced a safe dry-run contract and
manifest-only apply gate instead of pretending debt was closed.

## Tests Added

Focused tests cover:

- dry-run closure plan is non-mutating
- closure blocks without backup, restore, replay/hash-chain, operator, and
  exact-item gates
- exact item manifest is required and count mismatch blocks apply
- unknown-era issues are not guessed away
- missing evidence is not fabricated
- replay/hash-chain unavailable does not pass silently
- manifest-only replay gate can pass only with explicit untouched-store reason
- operator confirmation must reference the plan id or backup id
- current operational debt blocks closure projection
- manifest-only apply refuses without a supplied manifest store
- manifest-only apply mutates only the supplied manifest store in synthetic
  tests
- maintenance scan exposes active, archived, quarantined, and not-executed
  closure state separately

## Acceptance Criteria

Closure is accepted only when:

- backup exists and restore verification passed
- archived legacy manifest exists and is inspectable
- unknown-era quarantine manifest exists and is inspectable
- non-reconstructable evidence remains labeled as non-reconstructable
- unknown-era issues remain labeled unless source evidence resolves them
- clean current operational baseline is created without hiding older debt
- maintenance scan separates active current blockers from archived/quarantined
  debt
- no journal/evidence/replay mutation was performed without explicit operator
  approval
- no fake evidence or verifier success was created

## Intentionally Not Done

This sprint did not:

- archive or compact logs
- write local runtime backup artifacts
- write local runtime archive or quarantine artifacts
- delete runtime journals
- rewrite event sequences
- repair hash-chain mismatches
- fabricate missing evidence
- convert unknown-era items into historical success
- change runtime health to green
- stage generated artifacts
