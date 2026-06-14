# Premium Mission Control Shell

Decision: `AEGIS_PREMIUM_MISSION_CONTROL_SHELL_READY`

## Scope

The premium Mission Control shell is a user-facing information architecture and
frontend product pass. It makes Aegis easier to understand without changing
runtime authority.

The current shell adapts the supplied Stitch Mission Workspace direction as a
native Aegis React/Next interface. Stitch exports, screenshots, and image
references were used as design input only; no generated HTML, CDN dependencies,
or external design assets are committed into Aegis.

This shell is not:

- command execution
- tool execution
- plugin execution
- MCP execution
- agent execution
- model routing
- memory write
- evidence creation
- verifier success
- approval, lease, or capability grant

## Navigation Model

The default product navigation is:

- Mission: calm first screen with Ask entry, runtime truth, trust stack,
  capability preview, Context Inspector, Approval Gate pattern, and next safe
  step.
- Ask: read-only Aegis Ask panel.
- Work: Aegis Control, governed command runtime, approvals, and timeline
  surfaces.
- Memory: consent-aware Memory OS framing and future Memory Inbox direction.
- Capabilities: user-facing capability map with implemented, read-only,
  proposal-only, metadata-only, approval-gated, and future-gated labels.
- Advanced: raw diagnostics, registries, graph, vision/future-gated surfaces,
  timeline, and runtime console.
- Settings: local UI preferences, including the English/Turkish language
  selector. Settings are presentation preferences and do not call models,
  tools, APIs, memory, or runtime execution.

## Runtime Truth

The shell keeps backend-owned state as the source of truth.

Mission Home may summarize:

- runtime health projection
- current blockers
- pending approvals and clarifications
- raw evidence status
- raw replay status
- WebSocket connection state

It must not claim full health when status is warning or unknown. Current
blockers can be zero while raw evidence/replay debt remains visible.

The Mission Composer includes a presentation-only reasoning mode selector:

- Deterministic
- Local model
- External disabled

These controls do not select a provider, call a model, route context, or grant
execution permission. They are UI framing for future policy-backed routing.

The Mission screen also includes safety chips for read-only behavior, no tool
execution, no memory write, and approval-gated action boundaries.

## Electron Shell

The Electron shell uses Aegis-owned window chrome so the app can be maximized,
minimized, closed, and toggled into fullscreen from the interface. The renderer
only receives a narrow whitelisted `windowAction` bridge. This bridge is for
desktop window control only and does not expose shell, filesystem, runtime,
approval, evidence, model, tool, plugin, MCP, or execution authority.

DevTools no longer opens automatically in the development shell. It can still
be enabled explicitly with `AEGIS_OPEN_DEVTOOLS=1` when debugging is needed.

## Ask Router Hardening

Ask remains deterministic and local-only. The router now distinguishes:

- Tool Registry questions
- Skill Registry questions
- Plugin Registry questions

Execution-like requests still route to the safe unsupported path.

## Capability Surface

Capabilities are labeled honestly:

- implemented
- read-only
- proposal-only
- metadata-only
- approval-gated
- future-gated
- blocked/unsupported

Future concepts such as Model Council, External API Broker, Codex Review Board,
and Robustness Lab are represented as planned roadmap framing only.

## Memory Framing

The Memory screen introduces the product direction for Memory Inbox and
candidate review while preserving current boundaries:

- no silent long-term writes
- candidate memory is not active memory
- active memory is not authority
- retrieval is context only
- approve, reject, delete, and forget remain first-class lifecycle controls

## Advanced Diagnostics

Advanced keeps raw diagnostic power available without making it the first user
experience. It contains:

- Maintenance Scan raw details
- Runtime Stats
- Tool Registry
- Application Registry
- Agent Graph
- Vision Lab
- Chaos Shield
- Scientific Timeline
- Runtime Console

These panels remain presentation surfaces over backend data and projections.

## Intentionally Not Done

- No new runtime execution.
- No model calls.
- No external API routing or provider key handling.
- No model racing.
- No plugin execution.
- No MCP execution.
- No automatic memory persistence.
- No evidence or verifier success creation.
- No broad frontend rewrite.
- No ECC or G0DM0D3 code copied into Aegis.
- No Stitch HTML pasted into Aegis.
- No generated screenshots or external reference assets committed.

## Remaining Risks

- The shell is a first product-quality pass, not a full design system rewrite.
- Memory Inbox is framed but not fully implemented.
- Model Council, External API Broker, Review Board, and Robustness Lab remain
  future work.
- More rendered QA across Electron and varied runtime states is still useful.
