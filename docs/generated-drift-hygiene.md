# Generated Drift Hygiene

Decision: `SAFE_BASELINE_PUSH_TAG_DRIFT_HYGIENE_COMPLETE`

This note records the generated drift policy used while preserving the
Hackathon RC safe baseline. It is documentation only. It does not change
runtime, backend, API, frontend, launcher, Memory, AutoPilot, Society, model,
agent, skill, evidence, verifier, approval, lease, or capability behavior.

## Baseline Push Scope

S8 preserves the validated Hackathon RC and roadmap baseline before Model
Gateway, Skill Registry, and Bounded Agent Runtime work begins.

Before this hygiene note, local `main` was ahead of `origin/main` by the
validated RC implementation and roadmap commits:

- `1857b20` Align agent governance for hackathon RC
- `8e6eaef` Add RC readiness inventory report
- `2b15668` Add Memory OS RC1 core backend API
- `a40f574` Add AutoPilot RC1 core backend API
- `98ce2e9` Add deterministic Society Session RC1 API
- `cae57b1` Add Mission Control RC UI
- `57a3afd` Polish Mission Control RC visual layer
- `fbf2775` Add Hackathon RC demo smoke runbook
- `16ee3dd` Freeze Hackathon RC release package docs
- `b97ffcf` Fix Electron launcher environment for RC rehearsal
- `a5aad15` Document hackathon final roadmap realignment

The intended safe baseline tag is:

`hackathon-rc-safe-baseline-v1`

Tag purpose:

`Hackathon RC safe baseline before model/agent/skill expansion`

## Baseline Limitations

The baseline remains intentionally narrow:

- Memory OS is RC1 lifecycle/search, not full Memory OS v2.
- AutoPilot is read-only repo structure audit, not a full mission planner.
- Society is deterministic template output, not live autonomous multi-agent.
- verifier-lite is not full verifier success.
- AutoPilot reports and Society sessions are process-local.
- No model, MCP, tool, shell, cloud, or external network execution is part of
  the RC Golden Path.

## `frontend/next-env.d.ts` Drift

`frontend/next-env.d.ts` is a tracked Next.js-generated declaration file.

Observed behavior:

- `npm.cmd run build` completed without modifying the tracked file during S8.
- `npm.cmd run dev` rewrote the route type import from:

```ts
import "./.next/types/routes.d.ts";
```

to:

```ts
import "./.next/dev/types/routes.d.ts";
```

This is content drift, not line-ending-only drift. No `.gitattributes` change is
applied because the observed drift is not an EOL normalization problem.

Operator hygiene rule:

- Before any commit, run `git status --short --branch`.
- If `frontend/next-env.d.ts` is modified only by Next dev/launcher flow,
  restore it with:

```powershell
git restore -- frontend/next-env.d.ts
```

- Do not stage `frontend/next-env.d.ts` unless a scoped sprint explicitly
  changes the tracked Next declaration reference and explains why.
- Do not delete or untrack the file in a baseline/tag sprint.

## Runtime Artifact Hygiene

Do not stage:

- runtime logs
- screenshots
- temp smoke artifacts
- SQLite smoke databases
- report/session outputs
- model files
- vector databases
- datasets
- API keys, secrets, or tokens

## Next Intended Sprint

Recommended next sprint after the safe baseline push/tag:

`Model Gateway RC1 for LM Studio`

That sprint should start from the pushed/tagged baseline and keep model output
proposal-only, non-authoritative, and fail-closed when the provider is
unavailable.
