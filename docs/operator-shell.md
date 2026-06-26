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
model during route preview. After a route preview exists, the operator may use
the separate **Generate local draft** button to make one explicit request to
the existing local Model Gateway. It sends only the current request and visible
route, intent, candidate-preference, and detail metadata. It does not include
memory, files, previous chats, secrets, runtime logs, raw evidence, or cloud
context. External-provider metadata remains disabled, vision remains a future
boundary, and no cloud fallback is introduced. Context is closed by default and keeps route/trace metadata behind
an explicit secondary drawer so `OperatorResponseDraft` remains the primary
output.

The local result is displayed separately as **Local proposal** with explicit
labels: unverified model output, not evidence, not execution, not approval, and
not verifier success. Failure states show the backend error and do not create a
manufactured fallback answer. A copy action is local clipboard interaction only.

Memory-related routes now offer a separate **Create memory candidate** review
form. The form calls the existing Memory proposal API only after explicit
submission. The Memory Inbox reads backend-owned proposed, active, rejected,
and optionally deleted records, and exposes explicit approve, reject, and
confirmed-delete actions. Every mutation is followed by a backend refresh.
Active is a lifecycle state only; it is not authority, truth, evidence,
permission, or verifier success. The client blocks common secret-like key and
credential-assignment patterns before submission, while backend validation
remains authoritative.

This shell includes a backend-owned Auto Mode Router preview contract for route
classification. It is not live Auto Mode execution, autonomous execution, or
model/provider integration.

## Current Boundary

Auto Mode preview is deterministic metadata. The frontend prefers
`POST /operator/preview-route`, which returns the backend-owned
`aegis-operator-auto-router-preview` contract. If the backend is unavailable,
the shell falls back to the existing deterministic frontend preview and labels
that fallback clearly.

Both route-preview paths use simple keyword matching to preview an intent, route, model
profile candidate, boundary requirements, process trace, and draft artifact.
The backend contract is the stronger source for route preview metadata, but it
still does not grant authority or execution permission.

Backend route previews also include a deterministic read-only Capability Broker
assessment. The compact assessment remains inside the collapsed route-preview
surface and below the primary response. It explains whether the request maps to
observation, explanation, proposal, a future approval requirement, unavailable
execution, an unavailable provider, or an unsupported/ambiguous path. Frontend
fallback previews do not manufacture this backend-owned assessment.

The assessment does not execute commands, tools, browser or filesystem actions;
call local/cloud models or providers; write Memory; grant approval, permission,
leases, or capabilities; create evidence; run a verifier; or authorize
execution. It does not alter Maintenance Scan warning health or repair/hide
historical, evidence, replay, or quarantine debt. Local Model Gateway readiness
remains a separate environment-dependent fact until a configured acceptance
smoke actually verifies it.

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

An explicit local proposal is outside the deterministic preview operation and
is the only new model-call path in this workspace. It never runs on page load,
route preview, preference changes, or Memory Inbox activity.

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

## Keyboard And Status Accessibility

The Context trigger reports its expanded state and controls the named Context
drawer. Opening the drawer moves focus to its close button, Tab and Shift+Tab
remain within the drawer, Escape or the backdrop closes it, and keyboard focus
returns to the trigger. When closed, the drawer installs no keyboard trap. Its
bounded mobile width and internal scrolling keep it usable at narrow Windows
and browser viewports.

Interactive workspace controls share a visible amber focus outline in addition
to their existing text and icon labels. Route preview, explicit local proposal,
copy, and Memory Inbox lifecycle results use concise live-region updates.
Failures remain alerts. Memory validation links the error summary to the
relevant field where practical, and delete confirmation receives focus before
requiring a second explicit action. Cancel returns focus to that record's
delete button.

The local proposal readiness label describes only the current explicit request:
not checked, request in progress, response received, disabled, incomplete
configuration, or unavailable. It does not probe on page load and does not call
or start LM Studio. A response-received label appears only after the existing
backend completion contract returns an actual completed response.

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
