# Hackathon RC Sprint Sequence

## Decision

Decision: `HACKATHON_RC_SPRINT_SEQUENCE_DOCUMENTED_ONLY`

This document records sprint order and gates only. It does not implement
Memory, AutoPilot, Society, frontend, protocol, API, or runtime behavior.

## Sequence

### D0 - Docs / Agent Governance Realignment v1

Align agent instructions and planning docs so Hackathon RC work can proceed
without weakening Aegis invariants.

Gate: `AGENTS.md`, `HACKATHON_RC_SCOPE.md`, and `AEGIS_VISION.md` clearly
separate operational instructions, RC scope, and long-term vision.

### S0 - Foundation + RC Readiness Inventory v1

Inventory current backend, frontend, API, runtime, tests, and docs against the
declared Hackathon RC scope.

Gate: identify what already works, what is missing, what is blocked, and what
must be future-gated.

### S1 - Memory OS RC1-Core Backend + API

Implement the narrow governed memory proposal and approval path.

Gate: one propose -> approve cycle works, and one invalid proposal is blocked by
governance.

### S2 - AutoPilot RC1-Core Backend + API

Implement bounded read-only AutoPilot audit/report behavior.

Gate: AutoPilot produces a parseable report without claiming evidence or
verifier success.

### S3 - Deterministic Society Session Backend

Implement deterministic session artifact generation from available backend
data.

Gate: Society consumes live Memory/AutoPilot data where available, or downgrades
truthfully to static preview.

### S4 - Premium Mission Control UI

Implement the single-page RC Mission Control surface.

Gate: working panels render real backend data; non-working panels are removed,
blocked, or marked future-gated.

### S5 - Fail-Safe + Integration Testing

Validate startup, health, Memory, AutoPilot, Society, UI, and release fallback.

Gate: Tier-0 must-work criteria in `docs/HACKATHON_RC_SCOPE.md` pass or claims
are narrowed.

### S6 - Polish / Judge Package / Demo Script

Prepare the demo narrative, screenshots if needed, known limitations, and
repeatable judge flow.

Gate: demo package claims only working, validated RC behavior.
