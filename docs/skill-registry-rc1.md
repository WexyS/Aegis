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

## External Source Readiness

The schema can represent future external candidates such as ECC selected skills
or Higgsfield MCP candidates as disabled/candidate/future-gated metadata.

S10 does not:

- bulk import ECC
- call GitHub
- call Higgsfield
- connect to MCP
- handle credentials
- enable external skills
- execute candidate skills

Future S10.1 can add selected external candidate intake with disabled-by-default
manifests, source provenance, risk classification, and no execution.

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
