# Skill Registry Core RC1

Decision: `SKILL_REGISTRY_CORE_RC1_CODEX_SKILL_PACK_V1`

## Scope

Skill Registry RC1 is a backend-owned static metadata catalog for Aegis skills.
It defines manifest fields, risk classification, execution-mode metadata,
capability requirements, allowed scopes, and read-only API visibility.

It does not execute skills. It does not call Model Gateway, MCP, tools, shell,
network, external APIs, GitHub, memory, AutoPilot, Society, or frontend code.
It does not mutate files, memory, runtime state, journals, evidence, replay
state, or registry state.

## What It Is Not

Skill Registry RC1 is not:

- a skill runner
- a plugin loader
- a dynamic import system
- an MCP client
- a tool dispatcher
- an agent runtime
- a Model Gateway caller
- a memory writer
- approval
- a capability lease
- execution permission
- evidence
- verifier success

Skill manifest metadata is not permission. Skill enabled or available metadata
is not approval. Model-required metadata is not a model call. External candidate
metadata is not an MCP connection.

## Manifest Fields

RC1 manifests include:

- `skill_id`
- `name`
- `version`
- `description`
- `category`
- `status`
- `risk_class`
- `execution_mode`
- `input_contract`
- `output_contract`
- `required_capabilities`
- `allowed_scopes`
- `requires_model`
- `requires_network`
- `requires_mcp`
- `requires_shell`
- `requires_credentials`
- `can_mutate_files`
- `can_write_memory`
- `external_source`
- `limitations`
- `non_authority_flags`

Required non-authority flags remain false for catalog output:

- `authority`
- `permission_granted`
- `approval_granted`
- `capability_lease_granted`
- `evidence_created`
- `verifier_success`
- `runtime_dispatch_allowed`
- `memory_write_performed`
- `model_call_performed`
- `mcp_call_performed`
- `tool_call_performed`
- `shell_command_performed`
- `file_mutation_performed`

## Status Values

- `available`
- `disabled`
- `future_gated`
- `candidate`
- `blocked`

In RC1, `available` means available in the catalog only. It does not mean
runtime execution is available.

## Risk Classes

- `local_read_only`
- `local_model_required`
- `external_network_required`
- `mcp_required`
- `credential_required`
- `mutation_capable`
- `high_risk_external`
- `unknown_risk`

Side-effecting requirements must be represented as candidate, future-gated, or
blocked metadata. They are not active execution paths.

## Execution Modes

- `metadata_only`
- `read_only_planned`
- `model_assisted_planned`
- `external_candidate`
- `future_policy_gated`

There is no executable mode in RC1.

## Initial Built-In Skills

`repo_structure_audit`

- Maps conceptually to AutoPilot RC1 read-only repo structure audit.
- Risk: `local_read_only`
- Execution mode: `read_only_planned`
- The registry does not run AutoPilot.

`memory_candidate_review`

- Describes future review of Memory OS candidate metadata.
- Risk: `local_read_only`
- Execution mode: `metadata_only`
- The registry does not write memory.

`society_review`

- Describes future review of deterministic Society Session proposals.
- Risk: `local_read_only`
- Execution mode: `metadata_only`
- Society output remains proposal-only.

`report_summarization`

- Describes future model-assisted report summarization.
- Risk: `local_model_required`
- Execution mode: `model_assisted_planned`
- The registry does not call Model Gateway.

`context_package_review`

- Describes future review of context package metadata.
- Risk: `local_read_only`
- Execution mode: `metadata_only`
- Context packages do not grant permission.

`model_assisted_explanation`

- Describes future Model Gateway assisted explanation.
- Risk: `local_model_required`
- Execution mode: `model_assisted_planned`
- The registry does not call Model Gateway.

## API Endpoints

Read-only endpoints:

- `GET /skills`
- `GET /skills/{skill_id}`

There is no `POST /skills/.../run`, execute, enable, disable, import, sync, or
external registration endpoint in RC1.

## Validation Rules

The validator blocks:

- missing required fields
- invalid status, risk class, or execution mode
- wildcard capabilities or scopes
- non-authority flags set to true
- active side-effect requirements that are not future-gated candidates
- model-required skills without a model-required risk class
- MCP/network/credential/mutation requirements with mismatched risk classes

The validator itself is metadata-only and performs no execution.

## External Candidate Intake S10.1

S10.1 adds selected external skill/MCP candidate manifests as Aegis-native
metadata. No external source is installed, executed, cloned, authenticated, or
connected.

External candidate entries are code-defined catalog records only. They preserve
source URLs and risk classifications so future review can reason about them
without granting permission.

S10.1 does not:

- bulk import ECC
- call GitHub
- call Higgsfield
- connect to MCP
- handle credentials
- enable external skills
- execute candidate skills
- generate media
- spend credits or quota
- store credentials

### ECC Candidate Entries

ECC candidate source references:

- `https://github.com/affaan-m/ecc`
- `https://github.com/affaan-m/ECC`

The catalog treats ECC as an external agent-harness skill reference. It does not
install ECC, run ECC scripts, execute external `SKILL.md` instructions, call
GitHub APIs, or import ECC content in bulk.

Added Aegis-native ECC candidate manifests:

`ecc_repo_scan_review`

- Category: `external_skill_reference`
- Status: `candidate`
- Risk: `unknown_risk`
- Execution mode: `external_candidate`
- Required capabilities: `repo_read_only_context`, `operator_review`
- No repo scan is performed by Skill Registry.

`ecc_article_writing_reference`

- Category: `external_skill_reference`
- Status: `candidate`
- Risk: `local_model_required`
- Execution mode: `external_candidate`
- Required capabilities: `model_gateway_proposal_generation`,
  `operator_review`, `source_refs_only`
- No Model Gateway call is performed by Skill Registry.

`ecc_security_config_review`

- Category: `external_skill_reference`
- Status: `candidate`
- Risk: `unknown_risk`
- Execution mode: `external_candidate`
- Required capabilities: `security_config_metadata_review`,
  `operator_review`, `source_refs_only`
- No shell execution, secret access, credential access, or verifier success is
  created.

`ecc_github_ops_reference`

- Category: `external_skill_reference`
- Status: `future_gated`
- Risk: `high_risk_external`
- Execution mode: `future_policy_gated`
- Required capabilities: `github_auth`, `network_access`,
  `explicit_user_approval`, `mutation_policy_gate`,
  `capability_lease_required_future`
- No GitHub API call, GitHub mutation, credential handling, or network action is
  performed.

### Higgsfield MCP Candidate Entry

Higgsfield candidate source reference:

- `https://mcp.higgsfield.ai/mcp`

Added Aegis-native Higgsfield candidate manifest:

`higgsfield_mcp_media_generation`

- Category: `external_mcp`
- Status: `future_gated`
- Risk: `high_risk_external`
- Execution mode: `external_candidate`
- Requires network: true
- Requires MCP: true
- Requires credentials: true
- Required capabilities: `external_mcp_connect`, `media_generation`,
  `explicit_user_authorization`, `credential_boundary`,
  `quota_or_credit_acknowledgement`

This entry is not connected, not authenticated, and not available for RC1
execution. It creates no media and spends no quota or credits.

### Disabled/Future-Gated Semantics

For external candidates:

- `candidate` means the manifest exists for review only.
- `future_gated` means future use requires explicit policy, approval,
  credential, lease, and audit boundaries before any execution.
- `external_candidate` means external origin metadata exists, not that the
  external system is installed or callable.
- `future_policy_gated` means the candidate is blocked from execution until a
  later sprint defines and validates the missing gates.

Before any future external execution, Aegis would need:

- explicit policy gate
- explicit user approval
- credential boundary
- capability lease
- scoped network/MCP connector
- audit/reporting strategy
- no hidden fallback
- error and rollback handling
- evidence expectations
- verifier/postcondition strategy

## Relationship To Model Gateway

Model-required skills can declare `requires_model=true`, but Skill Registry RC1
does not call `/model-gateway/complete`. Future model-assisted behavior must
route through Model Gateway and preserve proposal-only output.

## Relationship To Agent Runtime

Future Bounded Agent Runtime may reference skill manifests as allowed metadata.
That reference will not be execution permission. Agent runtime work must add its
own policy, budget, proposal, and non-authority gates.

## Limitations

- Catalog is code-defined and static.
- No persistence or runtime mutation exists.
- No external manifest intake exists yet.
- No frontend UI exists yet.
- Skill availability is catalog metadata only.
- Built-in skill entries are conceptual bridges, not execution adapters.
