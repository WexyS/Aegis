# Hackathon RC Demo Script

Decision: `HACKATHON_RC_DEMO_SCRIPT_V1`

This is a 3-5 minute judge-facing script for the narrow Hackathon RC. Keep the
tone confident and accurate. Do not imply model execution, tool execution,
shell execution, network execution, live autonomous agents, report evidence, or
full verifier success.

## Opening

"Aegis is a local-first Mission Control workspace for trustworthy computer
operation. This release candidate focuses on one narrow, honest path:
Memory remembers, AutoPilot audits, Society reasons, Aegis governs."

## Positioning

"The point of this RC is not to claim broad autonomy. It is to show a governed
control-plane workflow where backend-owned state drives the UI, limitations are
visible, and every meaningful state change comes from an explicit backend
response or operator action."

## Golden Path Walkthrough

"I start in the Hackathon RC tab. The Golden Path strip shows the path the demo
will exercise: AutoPilot audit, candidate review, explicit Memory action,
Society Session, and report timeline."

"First, AutoPilot runs a read-only local audit against a safe demo project. It
does not mutate files. The report is rendered in Mission Control with source
inventory, docs/tests signals, risk markers, limitations, and a verifier-lite
label."

"The report is useful, but it is not evidence and verifier-lite is not full
backend verifier success. Aegis says that directly in the UI."

## Memory Line

"Next, Memory OS RC1-Core shows candidate memory proposals. A candidate is not
active memory. I explicitly propose it, then approve it. I can also propose a
manual memory item and reject it. Memory is local SQLite-backed state, and
retrieval is not authority or permission."

## AutoPilot Line

"AutoPilot RC1-Core is a read-only audit and report producer. It gives the
operator structured context without pretending to be autonomous execution."

## Society Line

"Now I run a deterministic Society Session from the selected AutoPilot report.
This is not a live multi-agent loop. It is a bounded deterministic session that
renders role proposals from backend data."

"The six roles are Context Planner, Policy Reviewer, Memory Curator, AutoPilot
Planner, Verifier Reviewer, and Report Writer. They produce proposals,
limitations, a timeline, and a final summary."

## Trust And Safety Line

"The important product behavior is claim hygiene. Aegis does not hide its
limits: reports and Society sessions are process-local, Memory is local
SQLite, verifier-lite is not full verification, and no model, MCP, tool, shell,
cloud, or external network execution is part of this RC path."

## Limitation Line

"If the backend restarts, process-local reports and Society sessions are gone,
so the operator reruns AutoPilot and Society. The UI does not invent those
states."

## Closing

"This RC demonstrates the operating philosophy: a polished Mission Control
surface with backend-owned truth, explicit operator actions, visible
limitations, and no fake success. Memory remembers, AutoPilot audits, Society
reasons, Aegis governs."
