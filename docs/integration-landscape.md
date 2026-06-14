# Aegis Integration Landscape

Decision: `AEGIS_INTEGRATION_LANDSCAPE_DEFINED`

## Scope

This document describes the planned Aegis integration landscape. It is an
architecture and registry document only. It does not install, clone, vendor,
launch, call, authenticate, or execute any upstream project.

Aegis uses Aegis-branded product surfaces for the operator experience while
preserving upstream references internally for engineering traceability,
license review, attribution, and future security work.

## Product Framing

Aegis should not become a messy pile of separate apps. Aegis remains the
top-level local Mission Control system. External projects and providers are
represented as future integration candidates under Aegis-branded surfaces:

- Aegis Code Workforce
- Aegis Design Studio
- Aegis Flow Engine
- Aegis Model Hub
- Aegis Memory OS
- Aegis Computer Operator
- Aegis Skill Foundry
- Aegis Agent Board

The public product should foreground Aegis capability areas. Upstream names
belong in the internal registry, engineering docs, notices, and future license
review records.

## Current Registry Boundary

The current registry lives in
`src/aegis/core/integration_registry.py`.

Every integration record is disabled from execution. Records may describe
planned discovery, dry-run, approval-gated, power-mode, or YOLO Lab posture,
but the registry itself does not execute anything.

Current hard boundaries:

- no third-party code is vendored
- no external repository is cloned
- no external tool is launched
- no model provider is called
- no workflow engine is called
- no MCP/tool/plugin/agent execution is added
- no install status is claimed
- no license facts are claimed without review
- no API key, token, or secret is requested or stored

## Aegis-Branded Families

### Aegis Code Workforce

Represents future coding-assistant orchestration surfaces. Planned references
include OpenCode, Cline, Aider, Kilo Code, Codex CLI, Gemini CLI, and Cursor
Composer. These records are not runners and are not adapters in the current
runtime.

### Aegis Design Studio

Represents future design, UI generation, and HTML/design workflow ideas.
Planned references include Open Design, html-anything, and Multica. Aegis
should prefer clean-room reimplementation or carefully scoped adapters before
any vendoring.

### Aegis Flow Engine

Represents future workflow planning and automation surfaces. Planned references
include n8n, Langflow, and Dify. Current records are non-executing metadata and
do not start workflow engines.

### Aegis Model Hub

Represents local and optional external model-provider planning. Planned
references include LM Studio, Ollama, Open WebUI, OpenRouter, and DeepSeek.
Current model calls remain bounded by the existing Model Gateway. External API
providers are blocked from current routing.

### Aegis Memory OS

Represents future memory, retrieval, graph, and RAG-adjacent architecture.
Planned references include AnythingLLM, Mem0, Graphiti, Cognee, GraphRAG,
LightRAG, RAGFlow, and Khoj. Registry metadata does not write memory, retrieve
memory, build vector indexes, or grant authority.

### Aegis Computer Operator

Represents future computer-control planning. CUA is represented as a high-risk
future candidate. It is not connected to browser, desktop, OCR, vision, or
click execution in the current runtime.

### Aegis Skill Foundry

Represents future skill discovery and skill-design references. The
awesome-claude-code reference is cataloged for research only. It does not
import prompts, skills, or external instructions into runtime execution.

### Aegis Agent Board

Represents future agent-board and multi-agent orchestration planning. Goose and
QwenPaw are represented as future references only. Existing Aegis Agent Runtime
remains proposal-only.

## Upstream Traceability

The registry preserves upstream names and URLs because future work must be able
to answer:

- where did this integration idea come from?
- what license or notice review is required?
- what security review is needed before connection?
- what runtime capabilities would be required?
- what privacy, credential, process, filesystem, model, or computer-control
  risks are implied?

The registry uses `license_hint: "unknown_pending_review"` unless license facts
have been reviewed inside the repository.

## Execution Status

Allowed registry execution statuses are descriptive only:

- disabled
- discovery_only
- dry_run_only
- approval_gated_planned
- power_mode_planned
- yolo_lab_planned
- blocked

None of these statuses grants execution in the current sprint. YOLO Lab planned
records are still non-executing.

## Relationship To Product UI

Future UI should present Aegis capability areas, not upstream tools as primary
brands. Upstream names may appear in advanced traceability, notices, and
developer/audit views when necessary.

The UI must never show:

- fake installed status
- fake model availability
- fake connector readiness
- fake permission
- fake evidence or verifier success
- execution controls for disabled records

## Remaining Risks

- Upstream licenses are not reviewed.
- Upstream security postures are not reviewed.
- Provider and tool availability are not detected.
- Current records are architecture metadata, not live connector inventory.
- Future product work must avoid turning registry metadata into permission.
