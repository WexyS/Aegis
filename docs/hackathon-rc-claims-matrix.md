# Hackathon RC Claims Matrix

Decision: `HACKATHON_RC_CLAIMS_MATRIX_V1`

This matrix defines judge-safe wording. It prevents overclaiming and separates
working RC behavior from future-gated product direction.

| Claim | Status | Evidence/validation source | Limitation | Safe wording for judges |
| --- | --- | --- | --- | --- |
| Real Memory OS backend/API | Implemented in RC1-Core scope | Memory API tests and S5/S6 UI smoke | Scope is proposal lifecycle, not full autonomous memory | "Memory OS RC1-Core supports governed local memory proposals." |
| Local SQLite memory | Implemented | Memory store/API behavior and UI smoke | SQLite is local; memory is not authority | "Memory is local SQLite-backed state." |
| Governed proposal lifecycle | Implemented | UI propose/approve/reject/search smoke | Approval is explicit; no silent activation | "Memory candidates require explicit operator action." |
| Memory retrieval as authority | Not claimed | Core invariants and UI labels | Retrieval cannot grant permission or truth | "Memory informs the operator; it does not authorize actions." |
| Read-only AutoPilot audit | Implemented in RC1-Core scope | AutoPilot API/core tests and Golden Path smoke | Bounded local audit only | "AutoPilot performs a read-only local audit." |
| Real directory scan | Implemented for local root path | AutoPilot report rendered from safe sample project | Demo path must use safe local project | "AutoPilot scans a selected local project in read-only mode." |
| AutoPilot mutates files | Not implemented | Scope docs and AutoPilot validation | No file mutation in RC Golden Path | "AutoPilot does not mutate demo project files." |
| AutoPilot report is evidence | Not claimed | UI labels and claim boundary | Report is useful context, not evidence | "The report is a backend audit output, not evidence." |
| verifier-lite | Implemented as label/metadata | AutoPilot report UI | Not full verifier success | "verifier-lite is a limited signal, not full verification." |
| Full verifier success | Not claimed | Claim boundary | Only backend verifier logic may grant verifier success | "The RC does not claim full verifier success from the report." |
| Deterministic Society Session | Implemented in RC1 scope | Society API/core tests and UI smoke | Deterministic role-template session only | "Society renders bounded deterministic role proposals." |
| Live autonomous multi-agent | Not implemented | Scope docs and Society limitations | No live agent loop | "This is not live autonomous multi-agent execution." |
| Premium Mission Control UI | Implemented for RC surface | S4.1 visual polish and S5/S6 browser smoke | Visual layer is presentation only | "Mission Control provides a polished RC control surface." |
| Golden Path UI smoke passed | Passed in S5, rechecked in S6 where practical | Browser smoke results | Smoke is local environment evidence, not production certification | "The local Golden Path smoke passed." |
| WebSocket baseline | Passed | WebSocket smoke and runtime channel connection | RC track-specific events are not separately streamed | "The runtime WebSocket baseline connects." |
| AutoPilot report persistence | Process-local/in-memory | API list metadata and docs | Cleared by backend restart | "Reports are process-local for this RC." |
| Society session persistence | Process-local/in-memory | API list metadata and docs | Cleared by backend restart | "Sessions are process-local for this RC." |
| Model/MCP/tool/shell/network behavior | Not implemented in RC path | Scope docs, tests, and smoke boundaries | Future-gated | "The RC Golden Path does not call models, MCP, tools, shell, cloud, or external network." |
| Production deployment | Not claimed | Release package boundary | Local demo only | "This is a local Hackathon RC package." |
| Frontend authority | Not claimed | Aegis invariants and UI labels | Frontend renders backend state | "The frontend presents backend-owned state." |
