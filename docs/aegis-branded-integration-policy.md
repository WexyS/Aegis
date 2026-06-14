# Aegis-Branded Integration Policy

Decision: `AEGIS_BRANDED_INTEGRATION_POLICY_DEFINED`

## Scope

This policy defines how Aegis names future integration areas and how upstream
references are preserved. It does not add connectors, adapters, package
imports, vendored code, tool execution, model calls, or external API calls.

## Product Names

Public Aegis product surfaces should use Aegis-branded names:

- Aegis Code Workforce
- Aegis Design Studio
- Aegis Flow Engine
- Aegis Model Hub
- Aegis Memory OS
- Aegis Computer Operator
- Aegis Skill Foundry
- Aegis Agent Board
- Aegis YOLO Lab

These names describe Aegis capability areas. They do not imply any upstream
project is embedded or executing.

## Upstream References

Upstream names and URLs must remain available in:

- `src/aegis/core/integration_registry.py`
- engineering docs
- future notice files
- future license review records
- future security review records
- test fixtures that prove traceability is preserved

Do not remove upstream references to make Aegis look more original. Traceability
is part of the safety and compliance boundary.

## Public UI Policy

Public UI should not foreground upstream names as Aegis product brands.

Acceptable public phrasing:

- Aegis Code Workforce
- Aegis Model Hub
- Aegis Flow Engine
- supported by planned integrations
- source reference available in registry

Avoid public product framing such as:

- "Run Cline now"
- "Aider installed"
- "n8n ready"
- "OpenRouter enabled"
- "DeepSeek available"

unless a future execution sprint actually implements, verifies, and documents
those claims.

## License And Notice Policy

If code is ever vendored, copied, redistributed, or deeply embedded:

- perform license review first
- preserve copyright notices
- preserve required license text
- document attribution requirements
- add tests or checks that required notice files remain present
- do not remove upstream notices during refactors

Until that review exists, records should use:

`license_hint: "unknown_pending_review"`

## Strategy Preference

Preferred strategy order:

1. Native Aegis implementation when the capability is core to Aegis.
2. Clean-room reimplementation when ideas are useful but code reuse is risky.
3. External adapter when the upstream project should remain separately
   installed and controlled by explicit gates.
4. Research reference only when the project informs design but should not be
   connected.
5. Vendoring only after license, security, maintenance, and notice review.

## Non-Permission Rule

Integration registry metadata is not:

- installation
- execution permission
- approval
- capability lease
- evidence
- verifier success
- runtime health
- frontend authority

Future execution requires separate policy, approval, credential, process,
filesystem, model, context, evidence, verifier, and audit gates.
