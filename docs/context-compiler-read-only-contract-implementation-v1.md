# Context Compiler Read-Only Contract Implementation v1

## 1. Decision

- Decision: `CONTEXT_CONTRACT_WITH_NON_AUTHORITY_TESTS`
- Recorded at: `2026-06-01T02:40:54+03:00`
- Repository checkpoint before sprint: `6395a3bc655f45aaf4f51d8ca37b7edca768683c`
- Foundation tag: `foundation-v1-baseline`

This sprint hardens the existing Context Compiler package contract. It does not
add a runtime endpoint, connect context to execution or planning, call models,
write memory, mutate runtime state, or change policy, approval, verifier,
evidence, replay, journal, or runtime health semantics.

## 2. Contract Metadata

Compiled context packages now expose explicit non-authority metadata:

- `context_contract_version=context-read-only-contract/1`
- `context_package_id`
- `source_refs`
- `source_versions`
- `authority=false`
- `non_executing=true`
- `capability_grant=false`
- `approval_grant=false`
- `lease_grant=false`
- `execution_permission=not_granted_by_context`
- `requires_backend_validation=true`
- `requires_policy_recheck=true`
- `memory_mutation=false`
- `journal_mutation=false`
- `evidence_mutation=false`
- `runtime_mutation=false`
- `raw_journal_included=false`

These fields are package assertions only. They do not authorize dispatch,
create leases, satisfy approval, satisfy evidence, or replace backend runtime
truth.

## 3. Source Summaries

The compiler remains pure over caller-supplied inputs. It can summarize:

- request metadata
- runtime snapshot
- command lifecycle snapshot
- policy boundary output
- non-executable guard state
- evidence audit summary
- maintenance scan summary
- frontend projection reference

The package records source references and best-effort source versions. Missing
or unversioned sources remain visible as `unavailable` or `unversioned`.

## 4. Evidence and Debt Preservation

Evidence audit current, historical, and unknown-era counts remain separate in
the verifier evidence summary. Maintenance summaries now preserve read-only
runtime health, foundation closure readiness, pending hygiene, replay
diagnostics, and resource warning fields when supplied by the caller.

The package reports:

- `known_debt_visible=true` when supplied evidence or maintenance summaries show
  historical debt, failed evidence, replay debt, or resource warning debt.
- `unknown_era_preserved=true` when supplied summaries include unknown-era
  evidence labels.

These flags are visibility markers, not cleanup permission and not health
greenwashing.

## 5. Raw Journal Boundary

Raw runtime events remain excluded. Even if a caller requests raw runtime event
inclusion through the budget, the package records only omission metadata:

- `raw_journal_included=false`
- omitted runtime event count
- safety warning that raw runtime events were omitted

A future raw journal exposure would require a separate boundary sprint with
redaction, budget, provenance, and non-authority tests.

## 6. Frontend, Policy, Lease, and Model Boundaries

- Frontend projection remains reference-only and `used_as_authority=false`.
- Policy boundary data remains source state and still requires backend policy
  recheck before dispatch.
- Approval-granted source state is not context approval.
- Context output cannot create or activate a capability lease.
- Memory, model, plugin, MCP, tool, or frontend output cannot become permission
  through this contract.
- No LLM provider is called and no model routing is introduced.

## 7. Tests

Focused tests assert:

- top-level contract fields are explicit and non-authoritative
- source references and source versions are exposed
- historical and unknown-era evidence counts are preserved separately
- unknown-era counts are not collapsed into historical labels
- maintenance runtime health, closure readiness, replay diagnostics, resource
  warnings, and mutation flags are preserved read-only
- untrusted permission and mutation fields from inputs are not promoted
- raw journal inclusion remains false
- supplied inputs are not mutated

## 8. Non-Goals

- No runtime endpoint.
- No planner/executor/tool connection.
- No model call, model router, dataset export, training job, adapter, or Memory
  OS implementation.
- No MCP gateway, plugin execution, skill execution, or vertical pack behavior.
- No cleanup, archive, or compaction execution.
- No journal, evidence, replay, snapshot, runtime, approval, policy, verifier,
  or frontend authority semantic change.

## 9. Recommended Next Workstream

Recommended next prompt:

`MCP/Tool Gateway Readiness v1`

Reason: Context packages now have explicit read-only contract metadata, while
policy and lease designs remain non-executing. The next safe architecture step
is a read-only gateway contract that proves tool availability is not tool
permission before any gateway implementation begins.

Alternative:

`Context Compiler Read-Only API Exposure Design v1`

Use this only if it remains design/read-only and does not expose context to
execution, planning, memory mutation, model routing, or command permission.
