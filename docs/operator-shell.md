# Aegis Unified Operator Shell

## Purpose

The Unified Operator Shell makes Mission the main local-first operator entry:
one composer, Auto Mode preview chips, deterministic route preview, process
trace, and draft artifacts.

This sprint is a shell-level product transition. It is not the Auto Mode Router,
not autonomous execution, and not model/provider integration.

## Current Boundary

Auto Mode preview is deterministic frontend-only UX metadata. It uses simple
keyword matching to preview an intent, route, model profile candidate, boundary
requirements, process trace, and draft artifact.

The preview does not:

- execute commands
- call local or cloud models
- call external providers
- upload screenshots or images
- write memory
- create evidence
- create verifier success
- grant approval, permission, leases, or authority

Process trace is summarized operational metadata, not hidden reasoning.
Artifacts are preview-only frontend drafts and are not persisted to backend.

## Safety Invariants

- Aegis remains local-first.
- Cloud use requires a future explicit broker and operator consent.
- Model output remains proposal-only and cannot become authority.
- Memory retrieval and memory proposals are not authority.
- Verifier, evidence, approval, lease, and permission state cannot be created by
  model output or frontend state.
- Permission profiles must be backend-owned before any execution path exists.

## Future Stages

- Auto Mode Router
- Memory Auto Mode
- Model Routing Local + Cloud
- Vision Input Boundary
- External Research Boundary
- Code Workforce
- Explicit Cloud Provider Live Broker

Each future stage requires a scoped sprint, tests, safety gates, and explicit
backend-owned authority boundaries before any runtime behavior is added.
