# Historical Evidence Replay Debt Closure

Decision: `HISTORICAL_EVIDENCE_REPLAY_DEBT_CLOSURE_PLANNED`

Date: 2026-06-12

Scope: closure plan only. This document does not archive, compact, truncate,
rewrite, resequence, delete, or mutate runtime journals, evidence records,
runtime state, Git history, or generated artifacts.

## Why This Exists

Aegis currently keeps historical, unknown-era, and replay debt visible. That is
correct. The next step is not to hide it; the next step is to close it with a
clear operational model that preserves inspectability while preventing safely
retired older debt from blocking current product work forever.

Missing historical evidence cannot be reconstructed unless source evidence
actually exists. Unknown-era issues must not be guessed into success.

## Current Observed State

Latest read-only maintenance scan during the system integrity audit reported:

- scan version: `maintenance-scan/1`
- read-only: true
- runtime health summary status: `fail`
- current blocker count: 0
- current evidence failure count: 0
- current missing evidence count: 0
- pending decision blocker count: 0
- unknown-era evidence issue count: 25
- unknown-era missing evidence count: 19
- replay diagnostics status: `fail`
- replay boundary classification:
  `historical_mixed_sequence_eras_or_reset_boundaries`
- evidence audit status: `fail`
- runtime snapshot status: `warning`
- observed maintenance mutations: none

The largest local runtime artifact observed during audit was
`logs/runtime_events.jsonl`, hundreds of MB in size. That file must not be
deleted or compacted as a side effect of this plan.

## Debt Classes

| Debt class | Meaning | Closure treatment |
| --- | --- | --- |
| Active operational debt | Current blockers, current missing evidence, current evidence failures, pending approvals, restored pending work, or live runtime inconsistency. | Must be fixed or explicitly blocked before clean baseline. |
| Historical debt | Old event/evidence/replay issues with known historical classification. | Can be archived into a older manifest if backup, replay, and operator gates pass. |
| Unknown-era evidence | Events without enough session/source context to prove current or historical era. | Must remain visible unless source evidence resolves the classification. |
| Replay boundary debt | Sequence resets, hash-chain mismatch, mixed eras, recursive snapshots, or replay discontinuities. | Requires backup, restore, replay, hash-chain checks, and operator approval before closure. |
| Resource/log pressure | Large local journals, logs, caches, or generated artifacts. | Requires backup and explicit cleanup sprint; no blind deletion. |

## What Can Be Repaired

These may be repaired in future scoped sprints:

- current missing evidence where the current command has available backend
  evidence that was not linked correctly
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

2. Archived older manifest
   - List historical and unknown-era issues exactly as observed.
   - Preserve reason, source, era classification, and uncertainty.
   - Include hash references to backed-up source artifacts.
   - Mark non-reconstructable missing evidence as non-reconstructable.

3. Retired older baseline
   - Declare the old mixed-era journal range as retired only after restore,
     replay, and hash-chain checks.
   - The retired baseline remains inspectable.
   - Retired does not mean deleted, verified, or greenwashed.

4. Clean current operational baseline
   - New runtime health can separate current operational blockers from archived
     older debt.
   - Active runtime must not fail solely because safely retired older debt
     remains archived.
   - Archived debt must remain reportable in a older section.

## Required Gates

No closure execution is allowed until all gates pass:

- operator confirms closure scope
- backup path is explicit and project-approved
- backup hashes are recorded
- restore rehearsal passes in an isolated location
- replay verification passes or records exact irreparable gaps
- hash-chain verification passes or records exact retired discontinuities
- current pending approvals are zero or explicitly preserved
- current evidence failures are zero or explicitly blocked
- current missing evidence is zero or explicitly blocked
- no generated artifacts or secrets are staged
- operator confirms no-suppression and no-guessing rules

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

Closure may move retired debt to an archived older section only after gates
pass. It must not delete the debt from observability.

## No-Guessing Rule

If a missing historical evidence item cannot be reconstructed from source
records, it remains missing. The correct status is archived non-reconstructable,
not verified.

If an unknown-era item cannot be assigned to a session with source evidence, it
remains unknown-era. The correct status is archived unknown-era, not historical
success.

## Maintenance Scan Reporting Target

After a future closure sprint, maintenance scan should report:

- current operational health
- current blockers
- current evidence failures
- current missing evidence
- pending decisions
- archived older debt summary
- archived older manifest reference
- replay/hash-chain closure status
- whether archived debt still needs operator attention

Current health should not fail solely because archived older debt is preserved.
It should still fail for active blockers, current missing evidence, current
evidence failures, replay/hash-chain issues in the current baseline, or hidden
debt.

## Acceptance Criteria

Closure is accepted only when:

- backup exists and restore verification passed
- archived older manifest exists and is inspectable
- non-reconstructable evidence remains labeled as non-reconstructable
- unknown-era issues remain labeled unless source evidence resolves them
- clean current operational baseline is created without hiding older debt
- maintenance scan separates active current blockers from archived older debt
- no journal/evidence/replay mutation was performed without explicit operator
  approval
- no fake evidence or verifier success was created

## Intentionally Not Done

This plan does not:

- archive or compact logs
- delete runtime journals
- rewrite event sequences
- repair hash-chain mismatches
- fabricate missing evidence
- convert unknown-era items into historical success
- change maintenance scan behavior
- change runtime health semantics
- stage generated artifacts
