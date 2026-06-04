from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


CONTEXT_POLICY_VERSION = "context-retrieval-provider-context-budget/1"
CONTEXT_POLICY_EXECUTION_PERMISSION = "not_granted_by_context_policy"

CONTEXT_SOURCE_CATEGORIES = {
    "public_docs",
    "private_repo_code",
    "repository_metadata",
    "project_config",
    "runtime_logs",
    "raw_journal",
    "journal_projection",
    "evidence_refs",
    "raw_evidence",
    "maintenance_findings",
    "policy_decision_refs",
    "memory_refs",
    "user_memory",
    "project_memory",
    "repo_memory",
    "compliance_context",
    "developer_passport_context",
    "plugin_review_context",
    "vertical_pack_context",
    "web_search_result_future",
    "web_page_extract_future",
    "document_text_future",
    "pdf_extract_future",
    "image_observation_future",
    "video_observation_future",
    "mcp_output",
    "tool_output",
    "frontend_supplied_context",
    "external_agent_output_future",
    "secrets_or_tokens",
    "unknown",
}

PROVIDER_TARGET_CLASSES = {
    "passive_backend_only",
    "local_model_candidate",
    "local_embedding_candidate",
    "local_reranker_candidate",
    "cloud_model_candidate_later",
    "web_query_candidate_later",
    "memory_index_candidate_later",
    "vector_index_candidate_later",
    "no_provider_allowed",
    "future_gated",
    "unknown",
}

CONTEXT_OPERATIONS = {
    "classify_context",
    "propose_context_package",
    "propose_context_budget",
    "propose_redaction",
    "propose_provider_target",
    "propose_retrieval_future",
    "propose_embedding_future",
    "propose_reranking_future",
    "propose_memory_retrieval_future",
    "propose_web_research_future",
    "propose_document_parse_future",
    "propose_repo_read_future",
    "unknown",
}

PRIVACY_CLASSES = {
    "public",
    "internal",
    "private",
    "private_repo",
    "personal_private",
    "sensitive",
    "secret_like",
    "credential_like",
    "regulated_or_compliance_sensitive",
    "unknown",
}

PRIVATE_CONTEXT_SOURCES = {
    "private_repo_code",
    "project_config",
    "runtime_logs",
    "journal_projection",
    "maintenance_findings",
    "policy_decision_refs",
    "memory_refs",
    "user_memory",
    "project_memory",
    "repo_memory",
    "compliance_context",
    "developer_passport_context",
    "plugin_review_context",
    "vertical_pack_context",
}

MEMORY_CONTEXT_SOURCES = {"memory_refs", "user_memory", "project_memory", "repo_memory"}

LOW_TRUST_CONTEXT_SOURCES = {
    "frontend_supplied_context",
    "mcp_output",
    "tool_output",
    "web_search_result_future",
    "web_page_extract_future",
    "external_agent_output_future",
}

FUTURE_GATED_CONTEXT_SOURCES = {
    "web_search_result_future",
    "web_page_extract_future",
    "document_text_future",
    "pdf_extract_future",
    "image_observation_future",
    "video_observation_future",
    "external_agent_output_future",
}

FUTURE_GATED_OPERATIONS = {
    "propose_retrieval_future",
    "propose_embedding_future",
    "propose_reranking_future",
    "propose_memory_retrieval_future",
    "propose_web_research_future",
    "propose_document_parse_future",
    "propose_repo_read_future",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_context_policy": "context_policy_cannot_provide_evidence",
    "evidence_provided_by_policy": "context_policy_cannot_provide_evidence",
    "evidence_provided_by_inventory": "context_policy_cannot_provide_evidence",
    "evidence_created": "context_policy_cannot_provide_evidence",
    "verifier_success": "context_policy_cannot_mark_verifier_success",
    "verified_success": "context_policy_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "context_is_truth": "context_truth_claim_denied",
    "frontend_context_is_authority": "frontend_authority_not_allowed",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "web_output_is_truth": "web_output_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "external_agent_output_is_truth": "external_agent_output_truth_claim_denied",
    "provider_selected": "provider_selection_not_allowed",
    "cloud_routing_allowed": "cloud_routing_not_allowed",
    "local_model_routing_allowed": "local_model_routing_not_allowed",
    "memory_context_allowed": "memory_context_permission_not_allowed",
    "raw_journal_allowed": "raw_journal_not_allowed",
    "raw_evidence_allowed": "raw_evidence_not_allowed",
    "secret_context_allowed": "secret_context_not_allowed",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "context_retrieval_performed": "context_retrieval_request_denied",
    "context_package_created": "context_package_creation_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "repo_file_read_performed": "repo_file_read_request_denied",
    "web_query_performed": "web_query_request_denied",
    "document_parse_performed": "document_parse_request_denied",
    "vector_index_touched": "vector_index_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "model_call_performed": "model_call_request_denied",
    "cloud_sync_performed": "cloud_sync_request_denied",
    "data_sent_external": "external_data_transfer_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
}


@dataclass(frozen=True)
class ContextPolicyFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ProviderContextBudget:
    max_context_tokens: int | None = None
    recommended_context_tokens: int | None = None
    reserved_system_tokens: int | None = None
    reserved_instruction_tokens: int | None = None
    reserved_response_tokens: int | None = None
    max_source_count: int | None = None
    max_chunk_count: int | None = None
    max_chunk_tokens: int | None = None
    max_memory_items: int | None = None
    max_evidence_refs: int | None = None
    allow_raw_content: bool = False
    allow_summaries: bool = True
    allow_source_refs_only: bool = True
    requires_redaction: bool = False
    requires_citation: bool = True
    requires_freshness_check: bool = False
    requires_provenance: bool = True
    requires_human_review: bool = False


@dataclass(frozen=True)
class ContextPolicyInput:
    request_id: str | None
    context_source_category: str | None
    context_operation: str | None
    privacy_class: str | None
    provider_target_class: str | None
    namespace: str | None
    project_ref: str | None
    repository_ref: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    budget: ProviderContextBudget | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class ContextPolicyDecision:
    contract_version: str
    policy_status: str
    request_id: str | None
    context_source_category: str | None
    context_operation: str | None
    privacy_class: str | None
    provider_target_class: str | None
    namespace: str | None
    provider_target_status: str
    budget_status: str
    source_delivery_mode: str
    redaction_required: bool
    citation_required: bool
    provenance_required: bool
    lower_trust_source: bool
    future_gated: bool
    failure_reasons: tuple[str, ...]
    failures: tuple[ContextPolicyFailure, ...]
    context_input: ContextPolicyInput | None
    budget: ProviderContextBudget | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = CONTEXT_POLICY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_context_policy: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    context_retrieval_performed: bool = False
    context_package_created: bool = False
    memory_retrieval_performed: bool = False
    repo_file_read_performed: bool = False
    web_query_performed: bool = False
    document_parse_performed: bool = False
    vector_index_touched: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    model_call_performed: bool = False
    cloud_sync_performed: bool = False
    data_sent_external: bool = False
    provider_selected: bool = False
    cloud_routing_allowed: bool = False
    local_model_routing_allowed: bool = False
    memory_context_allowed: bool = False
    raw_journal_allowed: bool = False
    raw_evidence_allowed: bool = False
    secret_context_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_context_policy_request(
    request: Mapping[str, Any],
    *,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> ContextPolicyDecision:
    """Validate caller-supplied context metadata without retrieving context."""

    if not isinstance(request, Mapping):
        failure = ContextPolicyFailure(
            reason="missing_request",
            field="request",
            message="context policy request must be caller-supplied metadata",
        )
        return _decision(
            policy_status="clarification_required",
            request_id=None,
            context_source_category=None,
            context_operation=None,
            privacy_class=None,
            provider_target_class=None,
            namespace=None,
            provider_target_status="blocked",
            budget_status="missing",
            source_delivery_mode="none",
            redaction_required=False,
            citation_required=True,
            provenance_required=True,
            lower_trust_source=False,
            future_gated=False,
            failures=(failure,),
            context_input=None,
            budget=None,
        )

    data = deepcopy(dict(request))
    failures: list[ContextPolicyFailure] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "local_model_inventory": local_model_inventory_decision,
        "model_auto_mode": model_auto_mode_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures)

    request_id = _text(data.get("request_id"))
    source_category = _text(data.get("context_source_category"))
    operation = _text(data.get("context_operation"))
    privacy_class = _text(data.get("privacy_class"))
    provider_target = _text(data.get("provider_target_class"))
    namespace = _text(data.get("namespace"))
    budget = _budget(data.get("budget_policy", data.get("context_budget")))
    source_refs = _mapping_tuple(data.get("source_refs"))
    provenance = _mapping_tuple(data.get("provenance"))
    context_input = ContextPolicyInput(
        request_id=request_id,
        context_source_category=source_category,
        context_operation=operation,
        privacy_class=privacy_class,
        provider_target_class=provider_target,
        namespace=namespace,
        project_ref=_text(data.get("project_ref")),
        repository_ref=_text(data.get("repository_ref")),
        source_refs=source_refs,
        provenance=provenance,
        budget=budget,
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
    )

    _validate_required_fields(context_input, failures)
    _validate_source_policy(context_input, failures)
    _validate_provider_policy(context_input, model_auto_mode_decision, failures)
    _validate_identity_policy(context_input, identity_scope_decision, failures)
    _validate_memory_policy(context_input, memory_governance_decision, failures)
    _validate_budget(context_input, failures)
    _validate_policy_extension(policy_extension_decision, failures)

    future_gated = _future_gated(context_input)
    lower_trust = source_category in LOW_TRUST_CONTEXT_SOURCES
    redaction_required = _redaction_required(context_input)
    citation_required = bool(budget.requires_citation if budget else True)
    provenance_required = bool(budget.requires_provenance if budget else True)
    source_delivery_mode = _source_delivery_mode(context_input, failures)
    provider_status = _provider_target_status(context_input, failures, future_gated)

    return _decision(
        policy_status=_policy_status(context_input, failures, future_gated),
        request_id=request_id,
        context_source_category=source_category,
        context_operation=operation,
        privacy_class=privacy_class,
        provider_target_class=provider_target,
        namespace=namespace,
        provider_target_status=provider_status,
        budget_status=_budget_status(context_input, failures),
        source_delivery_mode=source_delivery_mode,
        redaction_required=redaction_required,
        citation_required=citation_required,
        provenance_required=provenance_required,
        lower_trust_source=lower_trust,
        future_gated=future_gated,
        failures=tuple(failures),
        context_input=context_input,
        budget=budget,
    )


def _decision(
    *,
    policy_status: str,
    request_id: str | None,
    context_source_category: str | None,
    context_operation: str | None,
    privacy_class: str | None,
    provider_target_class: str | None,
    namespace: str | None,
    provider_target_status: str,
    budget_status: str,
    source_delivery_mode: str,
    redaction_required: bool,
    citation_required: bool,
    provenance_required: bool,
    lower_trust_source: bool,
    future_gated: bool,
    failures: tuple[ContextPolicyFailure, ...],
    context_input: ContextPolicyInput | None,
    budget: ProviderContextBudget | None,
) -> ContextPolicyDecision:
    return ContextPolicyDecision(
        contract_version=CONTEXT_POLICY_VERSION,
        policy_status=policy_status,
        request_id=request_id,
        context_source_category=context_source_category,
        context_operation=context_operation,
        privacy_class=privacy_class,
        provider_target_class=provider_target_class,
        namespace=namespace,
        provider_target_status=provider_target_status,
        budget_status=budget_status,
        source_delivery_mode=source_delivery_mode,
        redaction_required=redaction_required,
        citation_required=citation_required,
        provenance_required=provenance_required,
        lower_trust_source=lower_trust_source,
        future_gated=future_gated,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        context_input=context_input,
        budget=budget,
    )


def _validate_required_fields(
    context_input: ContextPolicyInput,
    failures: list[ContextPolicyFailure],
) -> None:
    required = {
        "request_id": context_input.request_id,
        "context_source_category": context_input.context_source_category,
        "context_operation": context_input.context_operation,
        "privacy_class": context_input.privacy_class,
        "provider_target_class": context_input.provider_target_class,
        "namespace": context_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if context_input.context_source_category and context_input.context_source_category not in CONTEXT_SOURCE_CATEGORIES:
        _add_failure(
            failures,
            "unsupported_context_source_category",
            "context_source_category",
            "context source category is not recognized",
        )
    if context_input.context_operation and context_input.context_operation not in CONTEXT_OPERATIONS:
        _add_failure(failures, "unsupported_context_operation", "context_operation", "operation is not recognized")
    if context_input.privacy_class and context_input.privacy_class not in PRIVACY_CLASSES:
        _add_failure(failures, "unsupported_privacy_class", "privacy_class", "privacy class is not recognized")
    if context_input.provider_target_class and context_input.provider_target_class not in PROVIDER_TARGET_CLASSES:
        _add_failure(
            failures,
            "unsupported_provider_target_class",
            "provider_target_class",
            "provider target class is not recognized",
        )
    if context_input.budget is None:
        _add_failure(failures, "missing_context_budget", "budget_policy", "context budget metadata is required")
    if _requires_refs_or_provenance(context_input) and not (context_input.source_refs or context_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "durable and reference context requires source refs or provenance",
        )


def _validate_source_policy(
    context_input: ContextPolicyInput,
    failures: list[ContextPolicyFailure],
) -> None:
    source = context_input.context_source_category
    privacy = context_input.privacy_class
    budget = context_input.budget
    if source == "secrets_or_tokens" or privacy in {"secret_like", "credential_like"}:
        _add_failure(failures, "secret_context_blocked", "privacy_class", "secret and credential context is blocked")
    if source == "raw_journal":
        _add_failure(failures, "raw_journal_blocked_by_default", "context_source_category", "raw journal is blocked")
    if source == "raw_evidence":
        refs_only = bool(budget and budget.allow_source_refs_only and not budget.allow_raw_content)
        if not refs_only:
            _add_failure(
                failures,
                "raw_evidence_blocked_by_default",
                "context_source_category",
                "raw evidence is blocked unless a future refs-only policy applies",
            )
    if source == "evidence_refs" and budget and budget.allow_raw_content:
        _add_failure(failures, "evidence_refs_must_remain_refs_only", "budget_policy", "evidence refs are refs-only")
    if _future_gated(context_input):
        return
    if source in LOW_TRUST_CONTEXT_SOURCES and _truthy(_field_value(context_input, "authority")):
        _add_failure(failures, "low_trust_context_authority_denied", "context_source_category", "lower trust context")


def _validate_provider_policy(
    context_input: ContextPolicyInput,
    model_auto_mode_decision: Any | None,
    failures: list[ContextPolicyFailure],
) -> None:
    target = context_input.provider_target_class
    privacy = context_input.privacy_class
    source = context_input.context_source_category
    if target == "cloud_model_candidate_later":
        if privacy in {"private", "private_repo", "personal_private", "sensitive", "regulated_or_compliance_sensitive"}:
            _add_failure(failures, "private_context_to_cloud_denied", "provider_target_class", "private context cannot target cloud")
        if privacy == "unknown":
            _add_failure(failures, "unknown_sensitivity_blocks_provider_routing", "privacy_class", "unknown sensitivity blocks routing")
    if target not in {"passive_backend_only", "no_provider_allowed"} and privacy == "unknown":
        _add_failure(failures, "unknown_sensitivity_blocks_provider_routing", "privacy_class", "unknown sensitivity blocks routing")
    if source == "private_repo_code" and target == "cloud_model_candidate_later":
        _add_failure(failures, "private_repo_context_to_cloud_denied", "provider_target_class", "private repo context is local/passive only")
    if model_auto_mode_decision is not None and _field_bool(model_auto_mode_decision, "provider_selected"):
        _add_failure(
            failures,
            "model_auto_mode_provider_selection_claim_denied",
            "model_auto_mode_decision.provider_selected",
            "context policy cannot accept provider selection as context permission",
        )


def _validate_identity_policy(
    context_input: ContextPolicyInput,
    identity_scope_decision: Any | None,
    failures: list[ContextPolicyFailure],
) -> None:
    if not _requires_identity(context_input):
        return
    if identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private context requires identity scope")
        return
    status = str(_field_value(identity_scope_decision, "scope_status") or "")
    if status.startswith("blocked") or status == "clarification_required":
        _add_failure(failures, "identity_scope_not_ready", "identity_scope_decision.scope_status", "identity scope is not ready")


def _validate_memory_policy(
    context_input: ContextPolicyInput,
    memory_governance_decision: Any | None,
    failures: list[ContextPolicyFailure],
) -> None:
    if context_input.context_source_category not in MEMORY_CONTEXT_SOURCES:
        return
    if memory_governance_decision is None:
        _add_failure(
            failures,
            "missing_memory_governance",
            "memory_governance_decision",
            "memory-derived context requires Memory Governance",
        )
        return
    status = str(_field_value(memory_governance_decision, "governance_status") or "")
    if status.startswith("blocked") or status == "clarification_required":
        _add_failure(
            failures,
            "memory_governance_not_ready",
            "memory_governance_decision.governance_status",
            "memory governance is not ready",
        )


def _validate_budget(
    context_input: ContextPolicyInput,
    failures: list[ContextPolicyFailure],
) -> None:
    budget = context_input.budget
    if budget is None:
        return
    numbers = {
        "max_context_tokens": budget.max_context_tokens,
        "recommended_context_tokens": budget.recommended_context_tokens,
        "reserved_system_tokens": budget.reserved_system_tokens,
        "reserved_instruction_tokens": budget.reserved_instruction_tokens,
        "reserved_response_tokens": budget.reserved_response_tokens,
        "max_source_count": budget.max_source_count,
        "max_chunk_count": budget.max_chunk_count,
        "max_chunk_tokens": budget.max_chunk_tokens,
        "max_memory_items": budget.max_memory_items,
        "max_evidence_refs": budget.max_evidence_refs,
    }
    for field, value in numbers.items():
        if value is not None and value < 0:
            _add_failure(failures, "invalid_budget_value", f"budget_policy.{field}", "budget values cannot be negative")
    if budget.max_context_tokens is not None and budget.recommended_context_tokens is not None:
        reserved = sum(
            value or 0
            for value in (
                budget.reserved_system_tokens,
                budget.reserved_instruction_tokens,
                budget.reserved_response_tokens,
            )
        )
        if budget.recommended_context_tokens + reserved > budget.max_context_tokens:
            _add_failure(
                failures,
                "budget_constraints_exceeded",
                "budget_policy.recommended_context_tokens",
                "recommended and reserved tokens exceed max context tokens",
            )
        if budget.max_chunk_tokens and budget.max_chunk_tokens > budget.max_context_tokens:
            _add_failure(
                failures,
                "budget_constraints_exceeded",
                "budget_policy.max_chunk_tokens",
                "chunk tokens exceed max context tokens",
            )
    if budget.max_source_count is not None and budget.max_source_count > 100:
        _add_failure(failures, "budget_constraints_exceeded", "budget_policy.max_source_count", "source count too broad")
    if budget.max_chunk_count is not None and budget.max_chunk_count > 1000:
        _add_failure(failures, "budget_constraints_exceeded", "budget_policy.max_chunk_count", "chunk count too broad")
    if budget.allow_raw_content and context_input.privacy_class in {
        "private",
        "private_repo",
        "personal_private",
        "sensitive",
        "regulated_or_compliance_sensitive",
        "unknown",
    }:
        _add_failure(failures, "raw_private_context_denied", "budget_policy.allow_raw_content", "raw private context is denied")


def _validate_policy_extension(policy_extension_decision: Any | None, failures: list[ContextPolicyFailure]) -> None:
    if policy_extension_decision is None:
        return
    outcome = str(_field_value(policy_extension_decision, "policy_outcome") or "")
    if outcome.startswith("blocked") or outcome in {"unsupported", "unknown"}:
        _add_failure(
            failures,
            "policy_extension_not_ready",
            "policy_extension_decision.policy_outcome",
            "context policy cannot contradict a blocked policy extension decision",
        )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[ContextPolicyFailure],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot override context policy with authority, dispatch, grants, evidence, verifier success, provider selection, retrieval, model, web, vector, API, MCP, tool, or external transfer behavior",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[ContextPolicyFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim context authority, permissions, grants, evidence, verifier success, or provider routing",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform context retrieval, packaging, memory, repo, web, document, vector, model, cloud, API, MCP, or tool behavior",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", CONTEXT_POLICY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "context policy metadata cannot grant execution permission",
            )


def _policy_status(
    context_input: ContextPolicyInput,
    failures: list[ContextPolicyFailure],
    future_gated: bool,
) -> str:
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any("secret" in reason or "credential" in reason for reason in reasons):
            return "blocked_by_secret_policy"
        if "raw_journal_blocked_by_default" in reasons:
            return "blocked_by_raw_journal_policy"
        if "raw_evidence_blocked_by_default" in reasons:
            return "blocked_by_raw_evidence_policy"
        if "missing_memory_governance" in reasons or "memory_governance_not_ready" in reasons:
            return "blocked_by_missing_memory_governance"
        if "missing_identity_scope" in reasons or "identity_scope_not_ready" in reasons:
            return "blocked_by_missing_identity_scope"
        if "budget_constraints_exceeded" in reasons or "invalid_budget_value" in reasons:
            return "blocked_by_budget_policy"
        if any("privacy" in reason or "cloud" in reason or "routing" in reason for reason in reasons):
            return "blocked_by_privacy_policy"
        if any("authority" in reason or "provider_selection" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        if any("request_denied" in reason or "external_data_transfer" in reason for reason in reasons):
            return "blocked_by_execution_claim"
        if "policy_extension_not_ready" in reasons:
            return "blocked_by_policy_extension"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        return "blocked_by_policy"
    if future_gated:
        return "future_gated"
    if context_input.human_review_required or (context_input.budget and context_input.budget.requires_human_review):
        return "proposal_requires_human_review"
    if context_input.context_operation == "classify_context":
        return "metadata_ready"
    return "proposal_ready"


def _provider_target_status(
    context_input: ContextPolicyInput,
    failures: list[ContextPolicyFailure],
    future_gated: bool,
) -> str:
    if failures:
        return "blocked"
    if future_gated or context_input.provider_target_class in {
        "future_gated",
        "cloud_model_candidate_later",
        "web_query_candidate_later",
        "memory_index_candidate_later",
        "vector_index_candidate_later",
    }:
        return "future_gated"
    if context_input.provider_target_class in {"passive_backend_only", "no_provider_allowed"}:
        return "metadata_only"
    return "proposal_only"


def _budget_status(context_input: ContextPolicyInput, failures: list[ContextPolicyFailure]) -> str:
    if context_input.budget is None:
        return "missing"
    reasons = {failure.reason for failure in failures}
    if "budget_constraints_exceeded" in reasons or "invalid_budget_value" in reasons:
        return "blocked"
    if context_input.budget.requires_human_review:
        return "requires_human_review"
    return "metadata_ready"


def _source_delivery_mode(context_input: ContextPolicyInput, failures: list[ContextPolicyFailure]) -> str:
    reasons = {failure.reason for failure in failures}
    if reasons:
        return "blocked"
    budget = context_input.budget
    if context_input.context_source_category in {"evidence_refs", "raw_evidence"}:
        return "refs_only"
    if budget and budget.allow_raw_content:
        return "raw_content_candidate"
    if budget and budget.allow_summaries:
        return "summary_candidate"
    return "refs_only"


def _future_gated(context_input: ContextPolicyInput) -> bool:
    return (
        context_input.context_source_category in FUTURE_GATED_CONTEXT_SOURCES
        or context_input.context_operation in FUTURE_GATED_OPERATIONS
        or context_input.provider_target_class
        in {
            "future_gated",
            "web_query_candidate_later",
            "memory_index_candidate_later",
            "vector_index_candidate_later",
        }
    )


def _redaction_required(context_input: ContextPolicyInput) -> bool:
    budget = context_input.budget
    if budget and budget.requires_redaction:
        return True
    return context_input.privacy_class in {
        "private",
        "private_repo",
        "personal_private",
        "sensitive",
        "regulated_or_compliance_sensitive",
        "unknown",
    } or context_input.context_source_category in PRIVATE_CONTEXT_SOURCES


def _requires_identity(context_input: ContextPolicyInput) -> bool:
    return (
        context_input.context_source_category in PRIVATE_CONTEXT_SOURCES
        or context_input.privacy_class
        in {"private", "private_repo", "personal_private", "sensitive", "regulated_or_compliance_sensitive"}
    )


def _requires_refs_or_provenance(context_input: ContextPolicyInput) -> bool:
    return context_input.context_source_category not in {None, "unknown", "frontend_supplied_context"}


def _budget(value: Any) -> ProviderContextBudget | None:
    if not isinstance(value, Mapping):
        return None
    return ProviderContextBudget(
        max_context_tokens=_int(value.get("max_context_tokens")),
        recommended_context_tokens=_int(value.get("recommended_context_tokens")),
        reserved_system_tokens=_int(value.get("reserved_system_tokens")),
        reserved_instruction_tokens=_int(value.get("reserved_instruction_tokens")),
        reserved_response_tokens=_int(value.get("reserved_response_tokens")),
        max_source_count=_int(value.get("max_source_count")),
        max_chunk_count=_int(value.get("max_chunk_count")),
        max_chunk_tokens=_int(value.get("max_chunk_tokens")),
        max_memory_items=_int(value.get("max_memory_items")),
        max_evidence_refs=_int(value.get("max_evidence_refs")),
        allow_raw_content=_truthy(value.get("allow_raw_content")),
        allow_summaries=_truthy(value.get("allow_summaries"), default=True),
        allow_source_refs_only=_truthy(value.get("allow_source_refs_only"), default=True),
        requires_redaction=_truthy(value.get("requires_redaction")),
        requires_citation=_truthy(value.get("requires_citation"), default=True),
        requires_freshness_check=_truthy(value.get("requires_freshness_check")),
        requires_provenance=_truthy(value.get("requires_provenance"), default=True),
        requires_human_review=_truthy(value.get("requires_human_review")),
    )


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(deepcopy(item) for item in value if isinstance(item, Mapping))


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "allowed", "grant"}
    return bool(value)


def _add_failure(
    failures: list[ContextPolicyFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(ContextPolicyFailure(reason=reason, field=field, message=message))
