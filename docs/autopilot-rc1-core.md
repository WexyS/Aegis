# AutoPilot RC1-Core

Decision: AUTOPILOT_RC1_CORE_BACKEND_API

AutoPilot RC1-Core is the first real Hackathon RC backend path for a safe,
read-only project/repository structure audit.

This is not autonomous execution. It is not CodingAgent. It is not Society. It
does not call models, tools, MCP servers, shell commands, web, or cloud APIs.

## Scope

Implemented:

- Single task: `repo_structure_audit`.
- Explicit local path validation.
- Real read-only directory tree walk.
- Generated/heavy directory exclusions.
- File metadata collection without file content reads.
- Structured JSON report.
- Verifier-lite checks.
- Candidate-only memory proposals in the report.
- FastAPI endpoints for run/list/retrieve.
- Process-local in-memory report storage.

Not implemented:

- Frontend UI.
- Memory UI.
- Society runtime.
- deterministic society session.
- live MCP/tool execution.
- shell command execution.
- file mutation.
- model analysis or LLM-generated findings.
- provider/model routing.
- context package creation.
- scheduling.
- patch generation.
- advanced risk analysis.
- automatic Memory OS persistence.

## Read-Only Guarantees

AutoPilot RC1-Core uses Python filesystem metadata APIs only. It does not:

- execute shell commands
- perform network calls
- call models
- call MCP/tools
- mutate files
- write report artifacts
- write Memory OS records
- read file contents

Reports include explicit safety fields:

- `mutation_performed=false`
- `shell_command_performed=false`
- `network_call_performed=false`
- `model_call_performed=false`
- `mcp_call_performed=false`
- `memory_write_performed=false`
- `runtime_dispatch_allowed=false`
- `execution_permission=not_granted_by_autopilot_rc1`

## Scanner Behavior

The scanner requires an explicit `root_path`. It rejects:

- missing paths
- file paths
- filesystem or drive roots
- root symlinks
- home-relative paths
- invalid paths

It walks directories without following symlinks. File contents are not read.
Large files are skipped as metadata-only.

Ignored folders:

- `.git`
- `.venv`
- `venv`
- `node_modules`
- `.next`
- `dist`
- `build`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`

Collected metadata includes:

- root path
- scan time
- total files and directories
- included file metadata
- excluded directories and files
- extension summary
- key files
- package/config files
- docs paths
- tests paths
- frontend/backend indicators
- warnings and limitations

## Report Shape

Reports include:

- `report_id`
- `task_id`
- `task_name`
- `status`
- `root_path`
- `started_at`
- `completed_at`
- `duration_ms`
- `context_preflight`
- `policy_gate`
- `source_inventory`
- `findings`
- `risk_markers`
- `memory_candidate_proposals`
- `verifier_lite`
- `warnings`
- `limitations`
- `degraded_state`

The report is backend-owned runtime output, but it is still not evidence and
not verifier success.

## Risk Markers

Risk markers are deterministic and simple:

- missing README
- missing tests directory
- missing docs directory
- package/dependency file present
- env/key-like file detected, content not read
- large files skipped
- generated folders skipped
- frontend/backend indicators detected
- unknown project type
- no obvious test config detected

AutoPilot RC1-Core does not perform model-based interpretation or deep security
analysis.

## Context Preflight

S2 uses an explicit RC1 preflight object:

- local repo read-only context is true
- model provider required is false
- network context is disallowed
- MCP/tool context is disallowed
- memory is not consumed
- no context package is created
- context does not grant execution permission

Full Context Policy/token budget integration is future-gated.

## Policy Gate

The policy gate records:

- `mutation_allowed=false`
- `shell_allowed=false`
- `network_allowed=false`
- `model_allowed=false`
- `mcp_allowed=false`
- `tool_allowed=false`
- `memory_write_allowed=false`
- `read_only=true`

This does not weaken or replace existing policy systems.

## Memory Candidate Proposals

AutoPilot reports may include memory candidate proposals such as project
structure summaries or detected stack hints.

Rules:

- memory candidate proposal is not active memory
- memory candidate proposal is not persisted
- AutoPilot does not call `/memory/propose`
- AutoPilot does not silently write Memory OS records
- later UI work can offer explicit user-controlled proposal/approval actions

## Verifier-Lite

Verifier-lite checks:

- scan completed without mutation
- root path was validated
- file/directory counts are coherent
- excluded directories are recorded
- report has required fields
- shell/network/model/MCP were not used
- operation remained read-only

States:

- `pass`
- `fail`
- `inconclusive`
- `error`

Verifier-lite is not evidence. It does not certify all findings and does not
grant execution permission.

## API

Endpoints:

- `POST /autopilot/run`
- `GET /autopilot/reports/{report_id}`
- `GET /autopilot/reports`

`POST /autopilot/run` accepts:

- `task_id`, currently `repo_structure_audit`
- `root_path`
- optional `include_dirs`
- optional `exclude_dirs`

Report persistence is process-local in-memory storage. Reports are not durable
across backend restarts and no report files are written.

## Future-Gated Work

Future sprints may add a Mission Control report panel, explicit Memory OS
proposal actions, Society Session handoff, richer source classification,
Context Policy integration, durable report storage, or model-assisted analysis.
Each must remain scoped and preserve Aegis authority, evidence, verifier,
policy, approval, and runtime truth boundaries.
