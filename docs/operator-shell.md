# Aegis Unified Operator Shell

## Purpose

The Unified Operator Shell is the main local-first operator entry: one composer,
one primary response draft, a compact route preview, and a secondary context
inspector. The primary navigation now follows workspace tasks: new task,
history, projects, outputs, memory, customize, and settings.

The former dashboard-style Mission, Ask, Work, Capabilities, and diagnostic
panels are not parallel primary destinations. Existing surfaces remain
available through the workspace drawer, Settings, or Advanced diagnostics when
their detail is needed.

History and Outputs use current browser-session frontend state only. They do
not load durable conversations, manufacture example projects, persist
artifacts, or claim backend authority. Projects therefore presents a truthful
zero-state and only offers buttons that prefill a bounded Operator request.

The composer includes model-candidate and planning-detail preferences. These
values are presentation metadata: they do not select, load, probe, or call a
model. External-provider metadata remains disabled, and no cloud fallback is
introduced. Context is closed by default and keeps route/trace metadata behind
an explicit secondary drawer so `OperatorResponseDraft` remains the primary
output.

This shell includes a backend-owned Auto Mode Router preview contract for route
classification. It is not live Auto Mode execution, autonomous execution, or
model/provider integration.

## Current Boundary

Auto Mode preview is deterministic metadata. The frontend prefers
`POST /operator/preview-route`, which returns the backend-owned
`aegis-operator-auto-router-preview` contract. If the backend is unavailable,
the shell falls back to the existing deterministic frontend preview and labels
that fallback clearly.

Both paths use simple keyword matching to preview an intent, route, model
profile candidate, boundary requirements, process trace, and draft artifact.
The backend contract is the stronger source for route preview metadata, but it
still does not grant authority or execution permission.

The route preview recognizes model/provider wording such as LM Studio, Qwen,
Gemma, DeepSeek, OpenRouter, Moonshot, and Kimi as Model Hub review metadata.
That classification is not model intelligence, not execution, not evidence, not
verifier success, not approval, not permission, and not provider selection.

The preview does not:

- execute commands
- call local or cloud models
- call external providers
- call Kimi or Moonshot
- upload screenshots or images
- upload video
- write memory
- call tools or MCP
- create evidence
- create verifier success
- grant approval, permission, leases, or authority

Attachment, voice, screenshot, image, and vision controls in this shell remain
placeholders or boundary previews. They do not upload files, call models, call
providers, or perform computer/tool actions.

Process trace is summarized operational metadata, not hidden reasoning.
Artifacts are preview-only drafts and are not evidence, verifier output,
approval, permission, or execution result.

`OperatorResponseDraft` is the main output surface. It renders the selected
artifact summary and a copy-ready body before the compact route metadata. Copy
requires an explicit operator click and does not write memory, persist an
artifact, execute a tool, or create evidence. The context inspector keeps the
trace, artifact list, and legacy detail surfaces available as secondary tools.

Memory copy describes the real consent and lifecycle boundary only. The shell
does not claim a fixed active-layer count because the frontend does not own or
verify that runtime fact.

## Preview Source Labels

- Backend contract: route preview came from the backend-owned deterministic
  preview endpoint. It remains preview-only.
- Frontend fallback: route preview was generated locally because the backend
  endpoint was unavailable. No action was performed.

The source label must remain visible so the UI does not imply frontend-created
truth or silently hide backend availability problems.

## Safety Invariants

- Aegis remains local-first.
- Cloud use requires a future explicit broker and operator consent.
- Model output remains proposal-only and cannot become authority.
- Memory retrieval and memory proposals are not authority.
- Verifier, evidence, approval, lease, and permission state cannot be created by
  model output or frontend state.
- Permission profiles must be backend-owned before any execution path exists.

## Future Stages

- Memory Auto Mode
- Model Routing Local + Cloud
- Vision Input Boundary
- External Research Boundary
- Code Workforce
- Explicit Cloud Provider Live Broker

Each future stage requires a scoped sprint, tests, safety gates, and explicit
backend-owned authority boundaries before any runtime behavior is added.
