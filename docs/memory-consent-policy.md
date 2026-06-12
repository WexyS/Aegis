# Memory Consent Policy

Decision: `MEMORY_CONSENT_POLICY_PLANNED`

Date: 2026-06-12

Scope: product and safety policy for memory consent. This document does not
change Memory OS code, write memory, retrieve memory, create memory indexes,
call models, or grant authority.

## Why This Exists

Aegis now has a local SQLite Memory OS core with explicit proposal, approval,
rejection, deletion, listing, and search behavior. The next product problem is
consent. Memory should make Aegis more useful without silently storing private
facts, interrupting every trivial workflow, or turning retrieved memory into
authority.

## Principles

- No silent long-term memory write by default.
- Do not interrupt the user for every trivial memory candidate.
- Use a Memory Inbox / candidate queue.
- Batch review at meaningful boundaries.
- Make sensitivity visible before approval.
- Session memory may be automatic only if non-persistent and disclosed.
- Secret, credential, private, or sensitive content requires explicit approval
  or must be blocked.
- Project preferences can be batched.
- The user can approve, reject, forget, delete, and inspect memory.
- Memory retrieval is context, not authority.
- Active memory must have lifecycle status and source references.

## Consent Classes

| Class | Default behavior | Required user action |
| --- | --- | --- |
| Ephemeral session context | Allowed for current session only when disclosed. | None, unless sensitive. |
| Low-risk memory candidate | Queue in Memory Inbox. | Batch approve or reject. |
| Project preference | Queue and group by project. | Batch approve or reject. |
| Repository preference | Queue and require project/repo scope clarity. | Explicit approve. |
| Personal private content | Queue as sensitive. | Explicit approve or reject. |
| Secret-like content | Block by default. | Do not store; allow only future explicit secure-secret flow. |
| Credential/API key/token | Block by default. | Do not store. |
| Imported legacy memory | Read-only until reviewed. | Approve, reject, archive, or delete. |

## Memory Inbox

Memory Inbox should show:

- candidate summary
- proposed scope: session, project, or repository
- sensitivity label
- source refs
- why Aegis thinks it may be useful
- retention suggestion
- exact action choices: approve, reject, edit, forget, delete
- whether content is raw, summarized, or redacted
- whether any model contributed to the candidate

The inbox should not block normal work for low-risk candidates. It should batch
review at natural boundaries, such as end of session, after an AutoPilot report,
or before starting a new project sprint.

## Sensitivity Rules

- Secret-like content is blocked.
- Credential-like content is blocked.
- Raw API keys, tokens, passwords, private keys, and `.env` values are blocked.
- Sensitive or personal content requires explicit approval.
- Private repository context requires project or repository scope clarity.
- Unknown sensitivity requires human review.
- Model output cannot decide sensitivity by itself.
- Frontend state cannot approve memory by itself.

## Lifecycle Status

Memory items should expose lifecycle state:

- proposed
- active
- rejected
- deleted
- archived
- expired
- blocked_sensitive
- blocked_secret
- needs_review

Current Memory OS already supports proposed, active, rejected, and deleted. The
remaining states should be added only in a scoped Memory UX/API sprint.

## Retrieval Boundary

Retrieved memory is not truth. Retrieved memory may:

- inform context
- suggest likely preferences
- help summarize prior project decisions
- provide source refs for user review

Retrieved memory must not:

- grant execution permission
- approve actions
- satisfy capability leases
- create evidence
- create verifier success
- override policy
- route private context to cloud
- silently persist new memory

## UX Flow

Recommended flow:

1. Aegis captures only session-local context during active work.
2. At meaningful boundaries, Aegis proposes memory candidates.
3. Candidates enter Memory Inbox with sensitivity and source refs.
4. Low-risk project preferences are batched.
5. Sensitive candidates require explicit single-item approval.
6. Secret-like or credential-like candidates are blocked and not stored.
7. Approved items become active.
8. Rejected items remain rejected or are deleted according to user choice.
9. User can forget/delete active items from the same UI.

## Relationship To Current Memory OS

Current implementation:

- local SQLite store
- explicit API/store calls
- proposal and approval lifecycle
- no model calls
- no cloud sync
- no vector index
- no authority from memory

Needed product work:

- Memory Inbox panel
- batched review
- sensitivity-aware display
- lifecycle filters
- deletion/forget UI clarity
- project/repository scope UX
- import/legacy memory review path

## Intentionally Not Done

This policy does not:

- change memory storage behavior
- write or delete memory
- retrieve memory
- generate embeddings
- create a memory graph
- call a model
- approve any candidate
- grant authority or permission
- introduce cloud sync
