# Training Data & Model Adaptation Governance v1

## 1. Decision

- Decision: `TRAINING_GOVERNANCE_DOCUMENTED_ONLY`
- Recorded at: `2026-06-01T02:33:06+03:00`
- Repository checkpoint before sprint: `b2c266901fdaaddcb5c2069698c8fedfbb7bc486`
- Foundation tag: `foundation-v1-baseline`
- Foundation tag target: `2662d5de0be805985d095c83a2f11c646a4b6fc2`

This sprint defines governance for future training, evaluation, adaptation,
few-shot, adapter, fine-tuning, model-routing, memory, translation, vision,
voice, and vertical-pack datasets. It does not create datasets, export logs,
train models, call models, create adapters, download models, or change runtime
behavior.

Aegis training and adaptation data is audit-grade system material, not ordinary
prompt logs.

## 2. Core Rule: High-Quality Scale

Aegis must optimize for high-quality scale, not smallness. Dataset volume is
desirable only after provenance, labels, evidence alignment, redaction, policy
alignment, review, eval coverage, namespace governance, and rollback planning
are in place.

No dataset may be considered production-approved merely because it is large.
Scale without quality gates is treated as risk, not progress.

Low-quality scale is forbidden. High-quality scale is the long-term target.

## 3. Training and Adaptation Scope

| Target | Current status | Future allowed use | Never authority? |
| --- | --- | --- | --- |
| Prompt examples | design-only | curated few-shot/example library | yes |
| Few-shot skill examples | design-only | reviewed skill guidance | yes |
| Eval datasets | design-only | first-class before training | yes |
| Intent classification examples | design-only | curated classifier/eval data | yes |
| Tool-call examples | design-only | proposal/eval data after tool manifest policy | yes |
| Policy boundary examples | design-only | refusal/allowance eval data | yes |
| Approval boundary examples | design-only | approval-gate eval data | yes |
| Evidence integrity examples | design-only | verifier/evidence hallucination eval data | yes |
| Prompt injection/security examples | design-only | security eval and refusal training | yes |
| Translation/terminology examples | design-only | vertical-pack dataset after glossary governance | yes |
| Language learning examples | design-only | vertical-pack dataset after domain review | yes |
| Coding report examples | design-only | repo-audit/coding report eval data | yes |
| Repo audit examples | design-only | review/eval data with source refs | yes |
| Memory summarization examples | design-only | memory candidate/eval data after Memory Governance | yes |
| Context summarization examples | design-only | context package summary eval data | yes |
| Voice response style examples | design-only | style data after privacy/storage policy | yes |
| Vision observation examples | design-only | VLM observation eval data after media policy | yes |
| LoRA/adapter datasets | prohibited now | later only after promotion gates | yes |
| Fine-tuning datasets | prohibited now | later only after eval-before-train gates | yes |
| Vertical pack datasets | design-only | pack-specific curated datasets | yes |

No target may bypass parser, policy, approval, lease, verifier, evidence,
journal, runtime authority, or frontend truth boundaries.

## 4. Source Classification

| Source | Eval use | Training use | Required controls | Forbidden positive use |
| --- | --- | --- | --- | --- |
| Human-authored gold examples | yes | yes after review | provenance, labels, reviewer, version | none if complete |
| Operator-approved examples | yes | yes after scope review | approval marker, provenance, labels | outside approved scope |
| Verified runtime traces | yes | possible after curation | evidence refs, policy labels, redaction | without evidence refs |
| Negative evidence traces | yes | negative training only | negative label preserved | success examples |
| Failed evidence traces | yes | negative/error training only | failure label preserved | success examples |
| Missing evidence traces | yes | negative/evidence-integrity training only | missing label preserved | verified success |
| Unknown-era records | yes, quarantine/eval only | no until proven and reviewed | unknown label, quarantine | historical/success examples |
| Denied approval records | yes | refusal/denial training only | approval_denied label | "do this next time" examples |
| Policy-denied examples | yes | refusal/denial training only | policy_denied label | positive action examples |
| Frontend projections | limited eval only | no as truth | frontend_projection label | backend truth examples |
| Maintenance summaries | yes | possible after source refs | read-only/provenance labels | cleanup permission examples |
| Context Compiler packages | yes | possible as context-summary examples | non-authority labels | command truth examples |
| Synthetic model-generated examples | yes after validation | no until validated/reviewed | synthetic labels, schema/policy evals | unverified training |
| External docs | yes | possible after license/provenance review | source refs, license, redaction | runtime truth |
| Web/tool/MCP/plugin outputs | yes as untrusted examples | no until validated | untrusted source labels | policy authority |
| User/project memories | limited eval | only after Memory Governance | namespace, redaction, source refs | policy truth |
| Translation/glossary corpora | yes | yes after domain review | glossary refs, reviewer, domain | platform identity |
| Code/repo examples | yes | possible after license/source review | commit refs, redaction | current truth if stale |
| External customer/project data | quarantined only | prohibited without tenant governance | tenant isolation, redaction, approval | cross-tenant data |
| Voice/screenshot/vision data | limited eval | prohibited without media governance | privacy review, redaction, consent | verifier success |

No source can influence runtime behavior directly. Every source must pass
classification, redaction, provenance, labeling, review, and eval gates before
use beyond quarantine.

## 5. Dataset Quality Tiers

| Tier | Allowed usage | Forbidden usage | Required controls | Scalable? |
| --- | --- | --- | --- | --- |
| `forbidden` | none | eval, training, adapter, runtime influence | reason for rejection | no |
| `raw_untrusted` | isolated collection only | training, eval metrics, adapters | source type, quarantine marker | no |
| `quarantined_candidate` | manual review queue | training/adapters/runtime use | initial labels, source refs | no |
| `eval_candidate` | evaluation only | training/adapters | provenance, labels, redaction check | limited |
| `training_candidate` | controlled training experiments only | adapter/fine-tune release | complete labels, redaction, quality scores | controlled |
| `human_gold` | eval and training | runtime authority | reviewer/operator approval, expected output | yes, after manifest |
| `adapter_ready` | adapter/fine-tune candidate | production runtime by itself | eval report, manifest, rollback | yes |
| `production_approved_dataset` | future runtime-adjacent adapter use | authority or policy replacement | versioned approval, regression gates | yes |
| `revoked` | audit only | all eval/training/adapter use | revocation reason and timestamp | no |

Dataset tier is never permission, approval, evidence, verifier success, or
runtime truth.

## 6. Gold Data Standard

`human_gold` examples must include:

- `dataset_item_id`
- source reference
- expected output
- risk tier
- capability category where relevant
- approval requirement
- evidence expectation
- policy decision label
- success/failure label
- reviewer or operator approval marker where applicable
- redaction status
- allowed usage
- forbidden usage
- dataset version
- freshness/staleness note
- provenance refs
- namespace/project scope if relevant
- domain/vertical pack scope if relevant

Gold examples must be precise, complete, and manually curated. Aegis must not
optimize for dataset volume before provenance, labels, evidence alignment,
redaction, policy alignment, human review, eval coverage, namespace governance,
and rollback planning are in place.

`adapter_ready` additionally requires eval coverage, dataset manifest
validation, rollback plan, baseline comparison, and operator approval for the
adapter use case.

## 7. Data Quality Scoring

Future scoring fields:

- `provenance_score`
- `label_quality_score`
- `evidence_alignment_score`
- `redaction_score`
- `policy_alignment_score`
- `human_review_score`
- `freshness_score`
- `domain_relevance_score`
- `namespace_isolation_score`
- `eval_coverage_score`

Rules:

- no provenance means no training
- no redaction means no training if sensitive data may exist
- missing evidence cannot become `verified_success`
- failed action cannot become success
- unknown-era cannot become historical or success
- frontend projection cannot become backend truth
- `synthetic_unverified` cannot enter training
- approval-denied cannot become positive "do this next time" data
- policy-denied examples can be used for refusal/denial training only
- unreviewed external customer/project data cannot enter training
- large volume cannot compensate for missing provenance, labels, evidence
  alignment, redaction, or policy alignment

## 8. Canonical Labels

| Label | Meaning | Positive training allowed? |
| --- | --- | --- |
| `verified_success` | backend evidence/verifier supports success | yes, with evidence and policy refs |
| `verified_failure` | backend verifier supports failure | no; negative/error examples only |
| `negative_evidence` | explicit failed/non-executed evidence | no; negative examples only |
| `missing_evidence` | expected evidence absent | no |
| `failed_evidence` | evidence check failed | no |
| `unknown_era` | era cannot be proven | no |
| `policy_denied` | policy denied action | refusal/denial only |
| `approval_denied` | operator denied approval | refusal/denial only |
| `approval_required` | action requires approval | yes only as boundary example |
| `proposed_only` | proposal, no execution | proposal training only |
| `read_only` | no side effect | yes if source is reviewed |
| `side_effecting` | side effect possible | only with policy/approval/evidence context |
| `hallucinated_tool` | nonexistent/unregistered tool | denial/tool-safety only |
| `prompt_injection` | untrusted instruction attempt | security eval/refusal only |
| `stale_context` | old context | no current-truth training |
| `frontend_projection` | frontend view/reference | no backend-truth training |
| `human_gold` | reviewed canonical example | yes within scope |
| `synthetic_unverified` | generated but unvalidated | no |
| `synthetic_validated` | generated and reviewed | limited, with labels |
| `redacted` | sensitive data handled | required for sensitive data |
| `contains_sensitive_data` | sensitive data present | no until redacted/allowed |
| `external_project_data` | external project/customer data | no without tenant governance |
| `tenant_scoped` | namespace-bound item | only within scope |
| `adapter_ready` | passed adapter gates | yes for approved adapter work |
| `revoked` | removed from allowed use | no |

## 9. Positive and Negative Example Rules

- `verified_success` may be used only with evidence refs and policy context.
- `negative_evidence` is useful as negative training, not success training.
- `failed_evidence` must not become success.
- `missing_evidence` must not become verified.
- `unknown_era` must stay unknown and not become historical or success.
- `approval_denied` must not become "do this next time."
- `policy_denied` examples are useful for refusal/denial training.
- `prompt_injection` examples are useful for negative/security evals.
- `hallucinated_tool` examples are useful for denial/tool-safety evals.
- `frontend_projection` is not backend truth.
- `synthetic_unverified` cannot enter training without validation.
- `human_gold` may be used only when reviewed and scoped.

## 10. Redaction and Privacy

Sensitive data classes:

- user identifiers
- local paths
- secrets, API keys, tokens
- personal data
- emails/messages
- screenshots
- voice recordings
- code secrets
- proprietary content
- external customer/project data
- tenant/project-specific memory

Rules:

- secrets never enter training
- personal data requires redaction or explicit allowed namespace
- external project data requires project/tenant governance
- screenshots and voice data require special handling
- model provider logs must not leak sensitive context
- training data must not cross tenant/project namespaces without explicit
  governance
- local paths should be normalized/redacted unless needed for repo-local evals

## 11. Provenance Requirements

Every future training/eval item should track:

- `dataset_item_id`
- `source_type`
- `source_ref`
- `commit_hash` if repo-derived
- `journal_event_id` if runtime-derived
- `evidence_ref` if evidence-derived
- `policy_decision_ref` if policy-derived
- `approval_ref` if approval-derived
- `generated_by` if synthetic
- `reviewed_by` if human-reviewed
- `created_at`
- labels
- allowed usage
- forbidden usage
- retention
- redaction status
- namespace/project id if relevant
- dataset family
- quality scores

## 12. Dataset Promotion Gates

Allowed transitions:

- `raw_untrusted` -> `quarantined_candidate`
- `quarantined_candidate` -> `eval_candidate` after source classification and
  initial labeling
- `eval_candidate` -> `training_candidate` after redaction, provenance, and
  label completion
- `training_candidate` -> `human_gold` after review and expected output
  validation
- `human_gold` -> `adapter_ready` after eval coverage and manifest validation
- `adapter_ready` -> `production_approved_dataset` after baseline metrics,
  regression gates, rollback plan, and operator approval

Blocked transitions:

- `forbidden` cannot transition
- `revoked` cannot be used
- unknown-era cannot become success through promotion
- missing/failed evidence cannot become verified through promotion
- frontend projection cannot become backend truth through promotion

`adapter_ready` requires:

- provenance verified
- labels complete
- redaction complete
- policy alignment checked
- evidence status preserved
- human/operator review completed where required
- eval impact measured
- rollback plan exists
- dataset manifest updated
- namespace/project isolation verified where relevant

## 13. Eval-Before-Train Rule

No adapter or fine-tune may proceed without an eval dataset and baseline
metrics.

Required eval coverage before training/adaptation:

- policy bypass tests
- approval bypass tests
- evidence hallucination tests
- tool hallucination tests
- unknown-era preservation tests
- prompt injection tests
- domain quality tests
- privacy/redaction leakage tests
- namespace leakage tests
- vertical-pack quality tests where relevant

No runtime deployment can proceed without regression tests and rollback plan.
Model behavior never replaces policy, approval, verifier, evidence, or runtime
authority.

## 14. Adapter and LoRA Governance

Adapters are optional specialization layers. Adapter output remains
non-authoritative.

An adapter cannot:

- grant permission
- reduce risk tier
- create evidence
- override policy
- approve actions
- create leases
- write memory
- mark runtime health healthy

Every adapter must reference:

- base model id
- dataset id/version
- eval report
- intended capability
- risk tier
- rollback plan
- storage path
- provenance
- operator approval where required

No adapter runtime use is allowed without model/provider readiness, resource
gates, policy gates, lease/evidence/audit relationships, and eval gates.

## 15. Target Dataset Families

| Dataset family | Pilot | Early | Mature | Large-scale target | Required evals |
| --- | --- | --- | --- | --- | --- |
| Tool-call proposal | design only | curated proposals | broad tool coverage | high-quality scaled | hallucinated tool, policy, approval |
| Intent classification | design only | common intents | broad intent/risk coverage | high-quality scaled | risk, ambiguity, clarification |
| Command proposal | design only | reviewed proposals | side-effect boundaries | high-quality scaled | parser, policy, evidence |
| Policy/refusal | design only | denial examples | policy families | high-quality scaled | bypass/refusal |
| Approval boundary | design only | approval examples | lifecycle coverage | high-quality scaled | approval bypass |
| Evidence integrity | design only | evidence labels | verifier failure/missing cases | high-quality scaled | evidence hallucination |
| Prompt injection/security | design only | attack examples | broad attack families | high-quality scaled | injection/refusal |
| Memory summarization | design only | namespace examples | conflict/quarantine coverage | high-quality scaled | memory leakage |
| Context summarization | design only | package examples | stale/unknown/debt coverage | high-quality scaled | context authority |
| Repo audit/coding report | design only | reviewed reports | multi-language repos | high-quality scaled | source refs, false positive rate |
| Translation/terminology | design only | glossary examples | domain-specific packs | high-quality scaled | term accuracy |
| Language learning | design only | reviewed examples | learner-level coverage | high-quality scaled | pedagogy/domain quality |
| Vertical pack datasets | design only | pack-specific gold | broad workflows | high-quality scaled | pack-specific evals |
| Voice style | design only | style examples | privacy-reviewed voices | high-quality scaled | privacy/style |
| Vision observation | design only | visual observations | modality coverage | high-quality scaled | observation vs verification |
| Model routing recommendation | design only | routing examples | provider/resource coverage | high-quality scaled | privacy/cost/failure |

Exact final counts require empirical eval planning. The categories above define
scale maturity without pretending that arbitrary size equals quality.

## 16. Model Router Relationship

- Model router may select models based on metadata, policy, resource, privacy,
  and capability constraints.
- Training data cannot teach a model to self-route outside policy.
- Provider/model choice must be logged.
- Local/remote privacy constraints must be honored.
- OOM, timeout, and unavailable model states are failure examples, not success
  examples.
- Model routing data must include provider/model provenance.

## 17. Memory Relationship

- Memory summaries may become eval/training candidates only with provenance and
  redaction.
- Memory cannot be used as training truth without source refs.
- Quarantined/conflicting memory cannot be promoted.
- User preference data must not become policy override behavior.
- Project memory must be refreshed against repo/source truth before training.
- Memory namespace and tenant/project boundaries must be preserved.
- Memory write decisions remain governed by Memory Governance, not model output.

## 18. Translation, Terminology, and Vertical Packs

- Translation examples require source language, target language, domain,
  glossary refs, style target, quality labels, and reviewer.
- Terminology examples require term source, domain, context, accepted
  translation, rejected alternatives, and reviewer.
- Vertical pack datasets must stay namespace-specific.
- Glossa/translation examples must not define Aegis platform identity; they are
  vertical-pack examples.
- Each vertical pack dataset requires its own evals, labels, quality criteria,
  forbidden examples, and promotion gates.

## 19. Synthetic Data Governance

Synthetic examples can be useful for coverage, but they are untrusted by
default.

Rules:

- synthetic examples require validation against schemas, policy, and evals
- synthetic examples must be labeled synthetic
- synthetic data cannot prove runtime behavior
- synthetic policy-bypass examples are useful for negative tests
- synthetic data cannot become `adapter_ready` without review and validation
- synthetic unverified data cannot enter training

## 20. No Automatic Training From Logs

Runtime logs, journals, evidence records, maintenance scans, model outputs, and
frontend projections must not be automatically exported into training datasets.

They may only become dataset candidates through an explicit curation pipeline:

1. collect candidate
2. classify source
3. redact
4. label
5. attach provenance
6. quarantine uncertain data
7. review
8. evaluate
9. promote or reject
10. version dataset
11. record manifest

No journal/evidence/replay data should be copied into training directories in
this governance sprint.

## 21. Dataset Manifest Schema Proposal

Future manifest fields:

- `dataset_id`
- `dataset_version`
- `purpose`
- `source_types`
- `item_count`
- labels
- allowed usage
- forbidden usage
- redaction status
- reviewer
- created_at
- source refs
- eval report refs
- adapter refs if any
- rollback notes
- quality score summary
- namespace/project scope
- retention policy
- dataset family
- promotion status

The manifest is documentation for future design. No `datasets/`, `adapters/`,
or manifest directories are created in this sprint.

## 22. Future Storage Layout

Possible future layout, documentation only:

```text
datasets/
  evals/
  training/
  synthetic/
  quarantined/
  gold/
adapters/
eval_reports/
dataset_manifests/
```

Do not create these directories until an explicit storage/governance sprint
authorizes it. Large datasets and adapters should not live inside the Aegis repo
unless a future architecture decision justifies it.

## 23. Gates Before First Training or Adaptation Sprint

Required gates:

- dataset governance complete
- redaction policy complete
- eval harness defined
- baseline model measured
- policy bypass eval exists
- approval bypass eval exists
- evidence hallucination eval exists
- unknown-era preservation eval exists
- privacy/redaction leakage eval exists
- namespace leakage eval exists
- adapter registry design exists
- rollback plan exists
- disk/model storage gate passes
- model provider readiness complete
- LLM authority boundary enforced

No training/adaptation sprint should proceed while these gates are absent.

## 24. Non-Goals

- No model training.
- No fine-tuning.
- No adapter creation.
- No model download, install, move, or deletion.
- No model call.
- No dataset export.
- No runtime log export.
- No journal/evidence/replay copy into training directories.
- No `datasets/` or `adapters/` directories.
- No runtime, backend, frontend, policy, approval, verifier, Context Compiler,
  journal, evidence, replay, or runtime health semantics changed.

## 25. Recommended Next Workstream

Recommended next prompt:

`Context Compiler Read-Only Contract Implementation v1`

Reason: policy, lease, resource, LLM authority, and training governance
boundaries now exist as design constraints. The next narrow implementation can
add a read-only, non-authoritative Context Compiler contract surface if it keeps
the same no-execution guarantees.

Alternative:

`Model Provider / Local LLM Readiness v1`

Use this only if disk/resource risk remains accepted as a blocker for downloads
and the sprint stays readiness-only with no model calls, installs, or routing.
