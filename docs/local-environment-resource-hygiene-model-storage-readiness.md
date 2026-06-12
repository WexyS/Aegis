# Local Environment Resource Hygiene & Model Storage Readiness
## 1. Decision

- Decision: `RESOURCE_READINESS_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T02:12:34+03:00`
- Repository checkpoint before sprint: `bdce8e00abb6fde782075e33fcf04c28f1c6eb32`
- Foundation tag: `foundation-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This report is read-only. It does not delete files, clean caches, move model
weights, mutate runtime state, rewrite journals, compact archives, repair
evidence, change runtime health, or add model/provider execution behavior.

## 2. Current Resource Snapshot

Read-only inventory was collected from local filesystem inspection and
`collect_system_resource_snapshot()`.

| Resource | Current value | Status |
| --- | --- | --- |
| Disk path | `C:\` | maintenance disk target |
| Disk total | `952.29 GB` | observed |
| Disk used | `878.62 GB` | observed |
| Disk free | `73.67 GB` | observed |
| Disk percent | `92.3%` | critical by proposed model-readiness threshold |
| Memory total | `33.98 GB` | observed |
| Memory used | `21.71 GB` | observed |
| Memory available | `12.27 GB` | observed |
| Memory percent | `63.9%` | not current blocker |
| CPU percent | `22.3%` | snapshot only |
| System resource status | `warning` | because disk percent is above 90% |
| Process resource status | `ok` | read-only process snapshot succeeded |

Foundation state already treated disk pressure around `92.1%` as visible
resource debt. The current read-only snapshot is consistent with that baseline:
disk pressure remains the relevant blocker for local model expansion.

## 3. Repo-Local Inventory

Largest repo-local top-level directories and files:

| Path | Size | Classification |
| --- | ---: | --- |
| `frontend/` | `1.33 GB` | mostly dependencies/build cache |
| `frontend/node_modules/` | `1.07 GB` | `dependency_cache_reinstallable` |
| `logs/` | `402.18 MB` | mixed runtime artifacts; mostly do-not-touch without boundary |
| `.venv/` | `366.40 MB` | `dependency_cache_reinstallable` |
| `frontend/.next/` | `274.88 MB` | `generated_build_cache` |
| `scratch/` | `35.14 MB` | candidate for review; contains local temp/test artifacts |
| `data/` | `14.02 MB` | runtime/local data; do not touch without owner review |
| `.git/` | `2.46 MB` | repository metadata; do not touch manually |
| `tests/` | `3.51 MB` | source-controlled test assets |
| `src/` | `1.77 MB` | source-controlled runtime code |
| `.pytest_cache/` | `81 KB` | generated test cache |

Largest non-dependency files found in the repo:

| Path | Size | Classification |
| --- | ---: | --- |
| `logs/runtime_events.jsonl` | `361.26 MB` | `journal_evidence_replay_do_not_touch` |
| `logs/archive/runtime_events_20260510T183129Z_historical_broken.jsonl` | `25.21 MB` | `journal_evidence_replay_do_not_touch` |
| `frontend/.next/cache/webpack/client-production/0.pack` | `40.65 MB` | `generated_build_cache` |
| `frontend/.next/cache/webpack/server-production/0.pack` | `40.18 MB` | `generated_build_cache` |
| `frontend/.next/dev/cache/webpack/client-development/*.pack.gz` | multiple 6-15 MB files | `generated_build_cache` |

The repo itself is not the primary disk-pressure source. The largest visible
repo-local cleanup opportunities are generated frontend build cache and
dependency caches, but they should still be cleaned only in a later
operator-approved hygiene sprint.

## 4. External Model Storage Inventory

Read-only model path checks:

| Path | Status | Size | Notes |
| --- | --- | ---: | --- |
| `C:\Users\nemes\.lmstudio\models` | exists | `31.82 GB` | current LM Studio model storage |
| `C:\Users\nemes\.lmstudio\models\unsloth` | exists | `19.09 GB` | external model storage; do not touch |
| `C:\Users\nemes\.lmstudio\models\lmstudio-community` | exists | `11.86 GB` | external model storage; do not touch |
| `C:\Users\nemes\.lmstudio\models\Qwen` | exists | `609.54 MB` | external model storage; do not touch |
| `C:\Users\nemes\.lmstudio\models\mradermacher` | exists | `287.58 MB` | external model storage; do not touch |
| `C:\Users\nemes\.cache\lm-studio\models` | missing | alternate LM Studio path |
| `C:\Users\nemes\.ollama\models` | exists, empty | `0 B` | reference only; user currently uses LM Studio |

Model files are outside the Aegis repo and must not be moved, deleted, or
deduplicated without explicit operator confirmation. Aegis should not store
large model weights inside the repository.

## 5. Cleanup Classification

| Category | Examples | Current classification | Future handling |
| --- | --- | --- | --- |
| Generated frontend build cache | `frontend/.next/` | `generated_build_cache` | safe cleanup candidate only after operator review |
| Dependency cache | `frontend/node_modules/`, `.venv/` | `dependency_cache_reinstallable` | reinstallable, but do not delete in this sprint |
| Test cache | `.pytest_cache/` | `safe_to_delete_manually_after_review` | small; not worth urgent action |
| Scratch artifacts | `scratch/` | `safe_to_delete_manually_after_review` for generated temp files only | review contents before deletion |
| Runtime logs | `logs/` | mixed | classify before any retention policy |
| Runtime journal | `logs/runtime_events.jsonl` | `journal_evidence_replay_do_not_touch` | no mutation without explicit journal boundary sprint |
| Archived historical journal | `logs/archive/*.jsonl` | `journal_evidence_replay_do_not_touch` | preserve as evidence/replay material |
| Runtime/local data | `data/` | `runtime_artifact_keep` / `unknown_do_not_touch` | requires owner review |
| Repository metadata | `.git/` | `unknown_do_not_touch` | never manually clean |
| External LM Studio models | `C:\Users\nemes\.lmstudio\models` | `external_model_storage_do_not_touch_without_operator_confirmation` | manage through operator-confirmed model lifecycle only |

Do not treat resource pressure as permission to mutate journal, evidence,
replay, snapshot, approval, or policy data.

## 6. Log and Artifact Retention Design

Recommended future log policy:

- Keep runtime journals append-only until a journal cleanup boundary sprint
  explicitly proves backup, restore, replay, hash-chain, and operator gates.
- Separate runtime journals from transient logs.
- Add future log rotation only for non-authoritative transient logs first.
- Suggested non-authoritative log defaults:
  - max file size: `10-25 MB`
  - retained rotated files: `5-10`
  - compression: optional after operator review
  - validation temp logs: write outside the repo or under a clearly ignored
    temp directory
- Screenshots/artifacts:
  - keep only when explicitly tied to validation evidence
  - store under an ignored artifact directory
  - add age/size retention policy before generating more
- Build artifacts:
  - `.next/` can be rebuilt and should be eligible for future generated-cache
    cleanup
  - `node_modules/` and `.venv/` are reinstallable but should be removed only
    by an explicit environment cleanup sprint

Do not apply log rotation to `logs/runtime_events.jsonl` until journal replay,
hash-chain, archive, restore, and operator approval requirements are satisfied.

## 7. Model Storage Readiness

Recommended storage model:

- Keep Aegis source code and model weights separate.
- Default external model root: `C:\Users\nemes\.lmstudio\models` while LM Studio
  remains the operator-selected provider.
- Do not create an Aegis-in-repo model cache.
- If Aegis later needs model metadata, store small metadata records in Aegis,
  not model weights.
- Proposed metadata registry fields:
  - provider
  - model id/name
  - local path reference
  - size
  - quantization
  - context length
  - modality
  - license/source
  - installed_at
  - last_verified_at
  - provenance
  - operator notes
- Model deletion policy:
  - requires operator confirmation
  - must show path, size, provider, and model identity
  - must never be triggered by Context Compiler, Memory, Model Router, MCP, or
    plugin output
  - should prefer provider UI/manual deletion until Aegis has explicit model
    lifecycle gates

Suggested free-space thresholds:

| Threshold | Rule |
| --- | --- |
| Disk usage `>= 90%` | critical; block model downloads unless operator supplies explicit external storage |
| Disk usage `>= 80%` | warning; require storage review before model expansion |
| Preferred before downloads | at least `25%` free disk or explicit operator-approved external storage path |
| Large coding model | reserve `20-50 GB` free depending on quantization and variants |
| Small chat model | reserve `4-10 GB` |
| Embedding model | reserve `1-5 GB` |
| Reranker | reserve `1-5 GB` |
| Vision model | reserve `8-30 GB` |
| STT/TTS model | reserve `2-20 GB` depending on quality and language coverage |

Current state: disk usage is `92.3%`, so model-router/local-model expansion
should be blocked until storage is reviewed or an external model storage path is
explicitly approved.

## 8. Relationship to Future Phases

| Future phase | Resource gate |
| --- | --- |
| Model Provider / Local LLM Readiness | blocked while disk remains critical unless external storage is approved |
| Model Lifecycle / VRAM Budget Design | may proceed as design-only; implementation needs disk and VRAM inventory |
| Memory Governance / Memory OS Design | design can proceed; persistent memory storage needs retention and growth policy |
| MCP / Tool Gateway Readiness | design can proceed; tool caches/artifacts need per-tool retention |
| VLM Visual Evidence Loop | blocked for implementation until screenshot/video retention and storage gates exist |
| Voice Mode | blocked for implementation until audio artifact retention and model storage gates exist |
| Vertical Pack Expansion | read-only planning can proceed; generated artifacts need pack-level retention budgets |

Resource readiness should be a preflight input for any phase that downloads
models, stores embeddings, generates media artifacts, or expands logs.

## 9. No-Cleanup Action Plan

Recommended future phases:

1. Phase A: read-only inventory refresh with exact disk, repo, model, cache, and
   log sizes.
2. Phase B: operator-reviewed cleanup candidate report.
3. Phase C: backup/restore plan for anything non-generated.
4. Phase D: generated cache cleanup script design for `.next`, `.pytest_cache`,
   and other rebuildable caches.
5. Phase E: log rotation implementation for non-authoritative transient logs
   only.
6. Phase F: model storage path setup outside the repository.
7. Phase G: model download/install sprint only after free-space gate passes.

No cleanup, archive, compaction, deletion, or model movement should happen
without an explicit future sprint and operator confirmation.

## 10. README / Docs Note

README does not need a change in this sprint. A future small docs update should
add:

- expected free disk before local model work
- reminder that model weights should live outside the repo
- LM Studio storage path guidance
- warning that runtime journals are not normal logs and must not be deleted as
  cache

## 11. Remaining Risks

- Disk usage remains critical at `92.3%`.
- `logs/runtime_events.jsonl` is large, but it is authoritative journal data and
  remains do-not-touch.
- Existing `.next`, `.venv`, and `node_modules` cleanup could free space but
  would change the local dev environment and should be operator-confirmed.
- LM Studio model storage already uses `31.82 GB`; future model downloads could
  worsen disk pressure quickly.
- No live `/maintenance/scan` endpoint was required for this report; resource
  data came from local read-only diagnostics and filesystem inspection.

## 12. Recommended Next Workstream

Recommended next prompt:

`LLM Authority Boundary Contract`

Reason: before local provider/model-router work begins, Aegis should explicitly
define that LLM outputs remain advisory until parsed, policy-checked,
approval-gated, executed, verified, evidenced, and journaled.

Alternative:

`Training Data & Model Adaptation Governance`

Use this if model/data provenance, fine-tuning, retrieval, or adaptation risk is
more urgent than provider authority boundaries.
