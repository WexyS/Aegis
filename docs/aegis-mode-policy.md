# Aegis Mode Policy

Decision: `AEGIS_MODE_POLICY_DEFINED`

## Scope

Aegis Mode Policy defines product posture for future behavior. It does not
grant execution, start tools, call models, write memory, launch workflows,
control the computer, call external APIs, or mutate files.

The implementation lives in `src/aegis/core/mode_policy.py`.

## Modes

### Safe

Safe is the default local-first posture.

Rules:

- no silent memory writes
- no external API use
- no tool execution
- no agent execution
- no workflow execution
- no computer control
- no filesystem write
- Model Gateway may be used only for status or proposal-readiness boundaries,
  not as authority or execution permission

### Balanced

Balanced is a future posture for carefully reviewed local productivity.

Rules:

- low-risk memory candidates may be planned later, but are not implemented here
- external API requires preview and approval before any future use
- no computer control
- no unrestricted filesystem write
- ledger and approval posture remain required

### Power

Power is a future posture for broader approved capability.

Rules:

- broader future execution may be planned
- approval strategy is required
- activity ledger is required
- memory ledger is required
- post-run report is required
- no current execution is granted by this policy

### YOLO Lab

YOLO Lab is a future high-autonomy lab mode. It is not enabled now.

Required controls:

- kill switch
- session timebox
- activity ledger
- memory ledger
- scoped task boundary
- post-run report
- explicit operator awareness

YOLO Lab records still do not execute in the current architecture. The name is
a future lab posture, not a bypass around Aegis safety.

## Current Invariant

For every mode:

- `mode_allows_execution_now` returns false
- runtime dispatch is not allowed
- no evidence is created
- no verifier success is created
- no approval is granted
- no capability lease is granted
- frontend state is not authority

## Relationship To Integration Registry

Integration records may list allowed future modes, but that is planning
metadata only. A record that says it belongs in Power or YOLO Lab remains
non-executing until a future execution sprint implements and verifies all gates.

## Relationship To Model Gateway

Mode Policy can say whether model-assisted proposal readiness may be considered.
It does not call Model Gateway. It does not make model output truth, evidence,
approval, permission, verifier success, or capability lease.

## Remaining Risks

- Future UI must avoid turning mode labels into run buttons.
- Future execution slices must prove policy cannot be bypassed by mode labels.
- YOLO Lab needs especially strong test and operator-safety boundaries before
  any implementation.
