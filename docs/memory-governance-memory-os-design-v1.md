# Memory Governance / Memory OS Design v1

## 1. Decision

- Decision: `MEMORY_GOVERNANCE_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T03:32:00+03:00`
- Repository checkpoint before sprint: `31aab109c42d02e44d0c3d3da50a45e72ebcb5c1`
- Foundation tag: `foundation-v1-baseline`

This sprint designs future Memory Governance and Memory OS boundaries. It does
not implement memory storage, retrieval, writes, vector stores, embeddings,
databases, endpoints, model calls, external APIs, SDKs, plugins, skills,
vertical packs, or runtime behavior.

## 2. Non-Authority Rules

Memory is not:

- command truth
- runtime truth
- policy truth
- approval
- execution permission
- capability grant
- capability lease
- evidence
- verifier success
- tool permission
- model routing authority
- frontend authority
- training truth without curation

Memory cannot:

- make `runtime_health` healthy
- hide current, historical, unknown-era, replay, or resource debt
- mark unknown-era data as historical
- mark missing evidence as verified
- turn failed actions into success
- create, activate, refresh, or expand leases
- bypass approval, policy, verifier, evidence, journal, or runtime authority

Memory may provide context for review. It cannot authorize action.

## 3. Memory Layer Architecture

| Layer | Purpose | Allowed content | Forbidden content | Authority | Write requirements | Retrieval requirements | Retention | Provenance/privacy/conflict behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Ephemeral Interaction Buffer | active turn context | current prompts, transient UI state | durable facts, secrets | none | no persistence | current task only | minutes/session | discard by default; no policy authority |
| 2. Session Working Memory | session continuity | short-lived decisions, task notes | cross-project facts | none | session id, source refs | session namespace only | session | stale at session end |
| 3. Task State Memory | long-running workflow state | task objective, checkpoints, blockers | execution permission | none | task id, owner, source refs | task-scoped | task lifetime | conflict surfaces to operator |
| 4. User Preference Memory | operator preferences | style, workflow preferences | policy override, approval | none | explicit user or reviewed inference | user namespace, sensitivity filter | long-term with review | preference cannot override policy |
| 5. Project Memory | repo/project notes | architecture notes, test style | repo truth replacement | none | project id, commit/source refs | project namespace | project-scoped | refresh against repo truth |
| 6. Domain Knowledge Memory | reusable domain context | glossary, terminology, domain notes | platform authority | none | source/license refs | domain/pack scoped | reviewed long-term | pack-specific, not global truth |
| 7. Provenance Memory | source tracking | source refs, origin, review status | unsupported claims | none | mandatory refs | by referenced scope | audit-retained | supports traceability only |
| 8. Evidence-linked Memory | summaries of evidence | evidence summaries with refs | new evidence, verifier result | none | evidence refs, status labels | evidence-aware retrieval | tied to evidence retention | cannot alter evidence truth |
| 9. Policy/Permission Memory | policy context | past policy decisions as references | permission grant, lease | none | policy decision refs | policy review only | audit-retained | backend policy remains authority |
| 10. Quarantine / Conflict Memory | unsafe or disputed memory | conflicts, stale, unknown-era, synthetic, untrusted items | truth claims | none | quarantine reason | excluded from truth retrieval | until reviewed/revoked | must surface conflicts |
| 11. Derived Summary Memory | compressed context | summaries with source refs | raw truth replacement | none | source refs, summarizer id | least-context retrieval | expires unless reviewed | summary is not evidence |
| 12. Long-term Stable Memory | reviewed durable facts | stable user/project/domain facts | secrets, policy bypass | none | review, namespace, retention | narrow scoped retrieval | long-term with decay review | explicit review required |
| 13. Decay / Retention Index | lifecycle control | expiry, freshness, revocation markers | sensitive content copies | none | retention policy | controls eligibility | varies | deletion can keep audit marker only |
| 14. Retrieval Policy Layer | retrieval governance | access policy and filters | content authority | none | policy definition | every retrieval passes here | audit-retained | enforces namespace/sensitivity/staleness |

Every layer is non-authoritative. Layer placement changes retrieval and review
rules, not runtime permission.

## 4. Namespace Model

Namespaces:

- `user`
- `project`
- `tenant`
- `aegis_core`
- `skill_plugin`
- `vertical_pack`
- `external_integration`
- `model_provider`
- `temporary_session`
- `quarantined`

Rules:

- Namespaces must not leak into each other without policy.
- External project/customer data requires tenant/project governance.
- Translation/Glossa memory must not redefine Aegis platform identity.
- Project memory must not override repo/source truth.
- User preference memory must not override policy.
- Skill/plugin memory must not grant tool permission.
- Model/provider memory must not select providers as authority.
- Quarantined namespace is excluded from truth retrieval by default.

## 5. Memory Item Schema

Future memory items should include:

- `memory_id`
- `memory_version`
- `namespace`
- `layer`
- `source_type`
- `source_ref`
- `created_at`
- `updated_at`
- `expires_at`
- `retention_class`
- `sensitivity_class`
- `redaction_status`
- `provenance_refs`
- `confidence`
- `staleness`
- `conflict_refs`
- `quarantine_status`
- `labels`
- `allowed_usage`
- `forbidden_usage`
- `written_by`
- `reviewed_by`
- `authority=false`
- `execution_permission=not_granted_by_memory`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_memory=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`

This is documentation only. No memory item type or store is implemented here.

## 6. Write Governance

Future memory candidates may be proposed by:

- explicit user request
- operator-approved note
- task lifecycle summary
- Context Compiler summary candidate
- model-generated `MemoryCandidate`
- verified runtime summary
- policy decision summary
- evidence summary
- skill or vertical pack output

Write rules:

- Model output may propose memory only.
- Context Compiler may package candidates only after governance exists.
- Memory writes require source refs, namespace, retention, sensitivity,
  redaction status, conflict check, and policy check.
- Sensitive memory requires explicit approval.
- External project/customer memory requires tenant/project rules.
- No automatic write from model output, tool output, frontend projection, raw
  logs, runtime journal, provider logs, or MCP/plugin content.
- Memory write is side-effecting and must be policy-gated in future.

## 7. Read and Retrieval Governance

Retrieval policy:

- task-specific retrieval
- namespace-limited retrieval
- sensitivity-aware retrieval
- staleness-aware retrieval
- conflict-aware retrieval
- least-context principle
- no broad all-memory injection
- provenance refs required
- retrieved memory remains non-authoritative

Retrieved memory must not override backend truth, policy, approval, evidence,
verifier results, runtime health, command lifecycle, or journal state.

## 8. Quarantine and Conflict Model

Quarantine candidates:

- conflicting memory
- stale memory
- unverified memory
- unknown-era memory
- frontend-derived memory
- synthetic memory
- external tool-derived memory
- plugin-derived memory
- sensitive unredacted memory

Rules:

- Quarantined memory cannot be used as truth.
- Conflicts are surfaced, not silently resolved.
- Unknown-era memory remains unknown.
- Stale memory requires refresh.
- Frontend-derived memory is reference-only.
- Synthetic memory requires validation.
- Conflict resolution requires policy/review and preserves provenance.

## 9. Retention and Decay

Retention classes:

- `ephemeral`
- `session`
- `task`
- `project`
- `long_term`
- `legal_audit_retained`
- `quarantined`
- `revoked_deleted_marker`

Rules:

- Memory should expire unless explicitly long-term.
- Stale memory must not be silently used.
- Retention must respect privacy and namespace.
- Deletion/forgetting may preserve an audit marker where required, without
  retaining sensitive content unnecessarily.
- Evidence and journal retention remain separate from memory retention.
- Memory deletion is not journal cleanup, evidence cleanup, or verifier repair.

## 10. Redaction and Privacy

Sensitive classes:

- secrets
- API keys
- tokens
- file paths
- personal data
- emails/messages
- screenshots
- voice recordings
- external customer/project data
- proprietary code/content
- tenant/project data

Rules:

- Secrets must not enter memory.
- Sensitive data requires redaction or explicit allowed namespace.
- External project/customer memory must be tenant-scoped.
- Provider/model logs must not leak sensitive memory.
- Memory used in remote model context requires privacy policy.
- Cross-project retrieval requires explicit policy and audit.

## 11. Context Compiler Relationship

- Context Compiler may include memory summaries only as non-authoritative
  context.
- Memory refs and provenance must travel with compiled context.
- Context cannot make memory authoritative.
- Context must preserve staleness, conflict, quarantine, sensitivity, and
  namespace markers.
- Context must not include broad memory dumps by default.
- Raw journal remains excluded by default.
- Context cannot grant approval, permission, capability, lease, evidence, or
  runtime truth.

## 12. LLM, Provider, and Lifecycle Relationship

- Model output may propose `MemoryCandidate` only.
- Model cannot write memory.
- Model cannot decide memory truth.
- Memory summarizer output remains non-authoritative.
- Provider selection must respect memory privacy and namespace constraints.
- Retrieval can increase context size and resource pressure.
- Memory-derived routing suggestions are non-authoritative.
- Stale or quarantined memory cannot select providers as truth.

## 13. Training Governance Relationship

- Memory items are not training data by default.
- Memory summaries may become dataset candidates only through governance.
- Human gold or project memory requires source refs and review.
- User preferences cannot become policy-bypass training examples.
- Quarantined or conflicting memory cannot be promoted.
- Memory deletion/revocation must prevent future training use.
- Failed, missing, unknown-era, frontend-derived, or synthetic memory labels
  must remain visible in dataset curation.

## 14. Policy, Lease, and Approval Relationship

- Memory cannot grant policy permission.
- Memory cannot create or activate leases.
- Memory cannot satisfy approval.
- Memory cannot reduce risk tier.
- Memory can provide historical context for review only.
- Policy decisions remain backend-owned.
- Approval records remain lifecycle/journal-owned.
- Lease state remains policy/approval/audit-owned.

## 15. Evidence, Verifier, and Runtime Health Relationship

- Memory can summarize evidence only with refs.
- Memory cannot create evidence.
- Memory cannot mark verifier success.
- Memory cannot make runtime health healthy.
- Memory cannot hide current, historical, unknown-era, replay, or resource debt.
- Evidence and journal truth remain separate from memory summaries.
- Negative evidence remains negative; memory cannot convert it to success.

## 16. MCP and Tool Gateway Relationship

- Memory can inform tool-call proposals only as context.
- Memory cannot authorize tool calls.
- Remembered tool preference cannot override policy.
- Skill/plugin memory cannot grant tool permission.
- Tool output cannot write memory automatically.
- MCP/tool content is untrusted until validated.
- Tool availability and MCP discovery are not memory permission.

## 17. External API / SDK Relationship

- External apps require tenant/project memory isolation.
- API keys must have memory scopes and must not be stored as raw memory.
- External integration memory must include `project_id` or `tenant_id`.
- No cross-project retrieval without explicit policy.
- Glossa, language-learning, customer, and freelance workflows require
  separate namespaces.
- Memory export requires explicit approval, policy, and redaction review.

## 18. Vertical Pack Relationship

Translation/Terminology memory may include:

- glossary terms
- style preferences
- domain terminology
- reviewer decisions

Language Learning memory may include:

- learner level
- recurring mistakes
- progress
- review schedule

Repo Audit memory may include:

- repo architecture notes
- previous audit findings
- test style

Business/Freelance memory may include:

- preferences
- proposal context
- platform constraints

Rules:

- Vertical pack memory is namespace-specific.
- Vertical pack memory cannot define Aegis platform identity.
- Pack memory cannot bypass global policy.
- Pack write actions remain approval/policy/evidence gated.

## 19. Future API / Contract Sketch

Documentation-only contract names:

- `MemoryItem`
- `MemoryCandidate`
- `MemoryNamespace`
- `MemoryWriteRequest`
- `MemoryWriteDecision`
- `MemoryRetrievalRequest`
- `MemoryRetrievalResult`
- `MemoryConflict`
- `MemoryQuarantineRecord`
- `MemoryRetentionPolicy`
- `MemoryRedactionPolicy`
- `MemoryAuditRecord`

Common fields:

- `authority=false`
- `execution_permission=not_granted_by_memory`
- `approval_grant=false`
- `capability_grant=false`
- `lease_grant=false`
- `evidence_provided_by_memory=false`
- `requires_backend_validation=true`
- `requires_policy_check=true`
- `namespace`
- `layer`
- `source_refs`
- `provenance_refs`
- `sensitivity`
- `retention`
- `staleness`
- `confidence`
- `quarantine_status`

## 20. Gates Before Memory Implementation

Required gates:

1. Memory Governance document complete.
2. Redaction/privacy policy accepted.
3. Namespace model accepted.
4. Memory item schema accepted.
5. Write governance accepted.
6. Retrieval governance accepted.
7. Conflict/quarantine model accepted.
8. Retention/decay model accepted.
9. Training governance relationship accepted.
10. Context Compiler memory boundary accepted.
11. LLM authority boundary accepted.
12. No-authority tests designed.
13. Memory write negative tests designed.
14. Retrieval policy tests designed.
15. Privacy and namespace leakage tests designed.

No Memory OS implementation should begin while these gates are absent.

## 21. Test Plan for Future Implementation

No tests are added in this documentation-only sprint because no memory type,
store, endpoint, retrieval path, embedding path, or write path is introduced.

When pure memory contract helpers are added, tests should assert:

- memory grants no execution permission
- memory grants no approval, capability, or lease
- memory creates no evidence or verifier success
- memory cannot override policy
- memory cannot make runtime health healthy
- memory cannot hide known debt or resource warnings
- model/context/tool/frontend output cannot write memory automatically
- retrieval is namespace-limited and provenance-bearing
- quarantined/conflicting/stale memory is not truth
- no vector DB, endpoint, model call, or embedding call occurs in contract tests

## 22. Non-Goals

- No Memory OS implementation.
- No memory writes.
- No memory database, files, or vector store.
- No embeddings.
- No model calls.
- No retrieval.
- No Context Compiler runtime memory path.
- No MCP/tool memory path.
- No command execution/planning memory path.
- No model router memory path.
- No external API/SDK implementation.
- No skill/plugin/vertical pack behavior.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  runtime health, backend, frontend, or API semantic change.
- No cleanup, archive, or compaction execution.
- No generated artifacts, vector DB files, model files, dataset files, adapter
  files, fake memory, fake health, fake evidence, or fake metrics.

## 23. Remaining Risks

- Memory write/retrieval tests are still future work.
- No concrete storage backend is selected.
- No privacy/redaction implementation exists yet.
- No namespace leak tests exist yet.
- Memory Governance is design-only and not connected to Context Compiler,
  providers, tools, or runtime.
- Current runtime health still reflects known historical/replay/resource debt.

## 24. Recommended Next Workstream

Recommended next prompt:

`MCP/Tool Gateway Readiness v1`

Reason: memory, model, context, policy, and lease boundaries are now documented.
The next high-risk surface is tool gateway readiness, where tool availability
must not become tool permission and MCP/tool output must remain untrusted until
validated.

Alternative:

`External API / SDK Readiness v1`

Use this if external integration and tenant/project isolation need to be
designed before gateway work.
