from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


WEB_RESEARCH_GATEWAY_VERSION = "web-research-gateway-readiness/1"
WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION = "not_granted_by_web_research_gateway"

RESEARCH_SUBJECTS = {
    "general_web_research",
    "official_docs_research",
    "api_reference_research",
    "release_notes_research",
    "security_advisory_research",
    "package_dependency_research",
    "legal_regulatory_research",
    "product_pricing_research",
    "news_current_events_research",
    "academic_paper_research",
    "github_public_repo_research_future",
    "github_issue_pr_research_future",
    "vendor_status_page_research",
    "troubleshooting_research",
    "source_verification_research",
    "contradiction_check_research",
    "citation_lookup_research",
    "unknown",
}

RESEARCH_OPERATIONS = {
    "classify_research_request",
    "propose_query_plan",
    "propose_source_selection",
    "propose_source_quality_check",
    "propose_freshness_check",
    "propose_contradiction_check",
    "propose_citation_plan",
    "propose_cache_policy",
    "propose_privacy_redaction",
    "propose_context_package_future",
    "propose_browser_fetch_future",
    "propose_search_api_future",
    "unknown",
}

SOURCE_PROVIDER_CLASSES = {
    "no_provider",
    "browser_search_future",
    "official_search_api_future",
    "general_search_api_future",
    "domain_limited_fetch_future",
    "github_api_future",
    "package_registry_api_future",
    "academic_index_future",
    "vendor_status_api_future",
    "local_cache_future",
    "unknown",
}

SOURCE_TYPE_CLASSES = {
    "official_primary_source",
    "vendor_documentation",
    "standards_body",
    "government_regulator",
    "academic_source",
    "security_advisory",
    "package_registry",
    "github_repository",
    "github_issue_or_pr",
    "vendor_status_page",
    "reputable_news_source",
    "community_forum",
    "blog_or_opinion",
    "social_media",
    "search_snippet",
    "scraped_page_extract_future",
    "unknown",
}

SOURCE_QUALITY_CLASSES = {
    "high_authority",
    "medium_authority",
    "low_authority",
    "community_low_trust",
    "snippet_only_low_trust",
    "unverifiable",
    "conflicting",
    "unknown",
}

FRESHNESS_CLASSES = {
    "current_required",
    "recent_required",
    "stable_reference",
    "historical_allowed",
    "stale",
    "unknown",
}

PRIVACY_CLASSES = {
    "public_query",
    "internal_context",
    "private_user_context",
    "private_repo_context",
    "personal_private",
    "sensitive",
    "secret_like",
    "credential_like",
    "regulated_or_compliance_sensitive",
    "unknown",
}

RESEARCH_RISK_CLASSES = {"info", "low", "medium", "high", "critical", "unknown"}

CACHE_POLICY_CLASSES = {
    "no_cache",
    "session_cache_only",
    "short_ttl_cache",
    "source_ref_cache_only",
    "durable_cache_future",
    "prohibited_cache",
    "unknown",
}

RESULT_AUTHORITY_CLASSES = {
    "source_candidate_only",
    "citation_candidate_only",
    "contradiction_candidate_only",
    "freshness_candidate_only",
    "synthesis_candidate_only",
    "unavailable",
    "unknown",
}

FUTURE_PROVIDER_CLASSES = {
    "browser_search_future",
    "official_search_api_future",
    "general_search_api_future",
    "domain_limited_fetch_future",
    "github_api_future",
    "package_registry_api_future",
    "academic_index_future",
    "vendor_status_api_future",
}

FUTURE_OPERATIONS = {
    "propose_context_package_future",
    "propose_browser_fetch_future",
    "propose_search_api_future",
}

LOW_TRUST_SOURCE_TYPES = {
    "community_forum",
    "blog_or_opinion",
    "social_media",
    "search_snippet",
    "scraped_page_extract_future",
}

PRIVATE_OR_SENSITIVE_PRIVACY = {
    "private_user_context",
    "private_repo_context",
    "personal_private",
    "sensitive",
    "regulated_or_compliance_sensitive",
    "unknown",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_web_research": "web_research_cannot_provide_evidence",
    "evidence_created": "web_research_cannot_provide_evidence",
    "verifier_success": "web_research_cannot_mark_verifier_success",
    "verified_success": "web_research_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "source_truth_claimed": "source_truth_claim_denied",
    "synthesis_truth_claimed": "synthesis_truth_claim_denied",
    "private_query_leak_allowed": "private_query_leak_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "web_query_performed": "web_query_denied",
    "browser_fetch_performed": "browser_fetch_denied",
    "search_api_called": "search_api_call_denied",
    "http_request_performed": "http_request_denied",
    "external_api_called": "external_api_call_denied",
    "github_api_called": "github_api_call_denied",
    "page_extract_performed": "page_extract_denied",
    "scraping_performed": "scraping_denied",
    "model_call_performed": "model_call_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "cache_written": "cache_write_denied",
    "source_record_created": "source_record_creation_denied",
    "citation_record_created": "citation_record_creation_denied",
    "report_generated": "report_generation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
}


@dataclass(frozen=True)
class WebResearchGatewayFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedWebResearchReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class WebResearchGatewayInput:
    request_id: str | None
    research_subject: str | None
    research_operation: str | None
    namespace: str | None
    privacy_class: str | None
    freshness_class: str | None
    source_provider_class: str | None
    source_type_class: str | None
    source_quality_class: str | None
    cache_policy_class: str | None
    result_authority_class: str | None
    research_risk_class: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    source_metadata_claimed: bool
    citation_required: bool
    contradiction_present: bool
    memory_derived_context: bool
    project_or_user_scoped_context: bool
    human_review_required: bool


@dataclass(frozen=True)
class WebResearchGatewayDecision:
    contract_version: str
    readiness_status: str
    request_id: str | None
    research_subject: str | None
    research_operation: str | None
    namespace: str | None
    privacy_class: str | None
    freshness_class: str | None
    source_provider_class: str | None
    source_type_class: str | None
    source_quality_class: str | None
    cache_policy_class: str | None
    result_authority_class: str | None
    research_risk_class: str
    query_privacy_status: str
    provider_status: str
    source_quality_status: str
    freshness_status: str
    citation_status: str
    cache_status: str
    result_authority_status: str
    redaction_required: bool
    contradiction_handling_required: bool
    human_review_required: bool
    future_gated: bool
    related_references: tuple[RelatedWebResearchReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[WebResearchGatewayFailure, ...]
    research_input: WebResearchGatewayInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_web_research: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    web_query_performed: bool = False
    browser_fetch_performed: bool = False
    search_api_called: bool = False
    http_request_performed: bool = False
    external_api_called: bool = False
    github_api_called: bool = False
    page_extract_performed: bool = False
    scraping_performed: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    mcp_call_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    cache_written: bool = False
    source_record_created: bool = False
    citation_record_created: bool = False
    report_generated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    private_query_leak_allowed: bool = False
    source_truth_claimed: bool = False
    synthesis_truth_claimed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_web_research_gateway_request(
    request: Mapping[str, Any] | None,
    *,
    system_drift_integrity_decision: Any | None = None,
    action_attribution_decision: Any | None = None,
    audit_query_layer_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> WebResearchGatewayDecision:
    """Validate future web research planning metadata without network behavior."""

    if not isinstance(request, Mapping):
        failure = WebResearchGatewayFailure(
            reason="missing_request",
            field="request",
            message="web research gateway requires caller-supplied metadata",
        )
        return _decision(research_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[WebResearchGatewayFailure] = []
    related_references: list[RelatedWebResearchReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "system_drift_integrity": system_drift_integrity_decision,
        "action_attribution": action_attribution_decision,
        "audit_query_layer": audit_query_layer_decision,
        "passive_observe": passive_observe_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_provider_health": local_provider_health_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "capability_lease": capability_lease_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    research_input = WebResearchGatewayInput(
        request_id=_text(data.get("request_id")),
        research_subject=_text(data.get("research_subject")),
        research_operation=_text(data.get("research_operation")),
        namespace=_text(data.get("namespace")),
        privacy_class=_text(data.get("privacy_class")),
        freshness_class=_text(data.get("freshness_class")),
        source_provider_class=_text(data.get("source_provider_class")),
        source_type_class=_text(data.get("source_type_class")),
        source_quality_class=_text(data.get("source_quality_class")),
        cache_policy_class=_text(data.get("cache_policy_class")),
        result_authority_class=_text(data.get("result_authority_class")),
        research_risk_class=_text(data.get("research_risk_class")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        source_metadata_claimed=_truthy(data.get("source_metadata_claimed")),
        citation_required=_truthy(data.get("citation_required"), default=True),
        contradiction_present=_truthy(data.get("contradiction_present")),
        memory_derived_context=_truthy(data.get("memory_derived_context")),
        project_or_user_scoped_context=_truthy(data.get("project_or_user_scoped_context")),
        human_review_required=_truthy(data.get("human_review_required")),
    )

    _validate_required(research_input, failures)
    _validate_privacy(research_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)
    _validate_source_quality(research_input, failures)
    _validate_cache(research_input, failures)

    return _decision(
        research_input=research_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    research_input: WebResearchGatewayInput | None,
    related_references: tuple[RelatedWebResearchReference, ...],
    failures: tuple[WebResearchGatewayFailure, ...],
) -> WebResearchGatewayDecision:
    future_gated = bool(research_input and _is_future_gated(research_input))
    return WebResearchGatewayDecision(
        contract_version=WEB_RESEARCH_GATEWAY_VERSION,
        readiness_status=_readiness_status(research_input, list(failures), future_gated),
        request_id=research_input.request_id if research_input else None,
        research_subject=research_input.research_subject if research_input else None,
        research_operation=research_input.research_operation if research_input else None,
        namespace=research_input.namespace if research_input else None,
        privacy_class=research_input.privacy_class if research_input else None,
        freshness_class=research_input.freshness_class if research_input else None,
        source_provider_class=research_input.source_provider_class if research_input else None,
        source_type_class=research_input.source_type_class if research_input else None,
        source_quality_class=research_input.source_quality_class if research_input else None,
        cache_policy_class=research_input.cache_policy_class if research_input else None,
        result_authority_class=research_input.result_authority_class if research_input else None,
        research_risk_class=_risk_class(research_input, list(failures)),
        query_privacy_status=_query_privacy_status(research_input, list(failures)),
        provider_status=_provider_status(research_input, list(failures), future_gated),
        source_quality_status=_source_quality_status(research_input, list(failures)),
        freshness_status=_freshness_status(research_input, list(failures)),
        citation_status=_citation_status(research_input, list(failures)),
        cache_status=_cache_status(research_input, list(failures)),
        result_authority_status=_result_authority_status(research_input, list(failures)),
        redaction_required=bool(research_input and research_input.privacy_class in PRIVATE_OR_SENSITIVE_PRIVACY),
        contradiction_handling_required=bool(
            research_input
            and (
                research_input.contradiction_present
                or research_input.research_subject == "contradiction_check_research"
                or research_input.research_operation == "propose_contradiction_check"
                or research_input.source_quality_class == "conflicting"
            )
        ),
        human_review_required=_human_review_required(research_input, list(failures), future_gated),
        future_gated=future_gated,
        related_references=related_references,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        research_input=research_input,
    )


def _validate_required(research_input: WebResearchGatewayInput, failures: list[WebResearchGatewayFailure]) -> None:
    for field in (
        "request_id",
        "research_subject",
        "research_operation",
        "namespace",
        "privacy_class",
        "freshness_class",
        "source_provider_class",
        "cache_policy_class",
    ):
        if not getattr(research_input, field):
            _add_failure(failures, f"missing_{field}", field, f"web research request is missing {field}")
    if research_input.research_subject and research_input.research_subject not in RESEARCH_SUBJECTS:
        _add_failure(failures, "unsupported_research_subject", "research_subject", "research subject is not recognized")
    if research_input.research_operation and research_input.research_operation not in RESEARCH_OPERATIONS:
        _add_failure(failures, "unsupported_research_operation", "research_operation", "research operation is not recognized")
    if research_input.privacy_class and research_input.privacy_class not in PRIVACY_CLASSES:
        _add_failure(failures, "unsupported_privacy_class", "privacy_class", "privacy class is not recognized")
    if research_input.freshness_class and research_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")
    if research_input.source_provider_class and research_input.source_provider_class not in SOURCE_PROVIDER_CLASSES:
        _add_failure(failures, "unsupported_source_provider_class", "source_provider_class", "source provider class is not recognized")
    if research_input.source_type_class and research_input.source_type_class not in SOURCE_TYPE_CLASSES:
        _add_failure(failures, "unsupported_source_type_class", "source_type_class", "source type class is not recognized")
    if research_input.source_quality_class and research_input.source_quality_class not in SOURCE_QUALITY_CLASSES:
        _add_failure(failures, "unsupported_source_quality_class", "source_quality_class", "source quality class is not recognized")
    if research_input.cache_policy_class and research_input.cache_policy_class not in CACHE_POLICY_CLASSES:
        _add_failure(failures, "unsupported_cache_policy_class", "cache_policy_class", "cache policy class is not recognized")
    if research_input.result_authority_class and research_input.result_authority_class not in RESULT_AUTHORITY_CLASSES:
        _add_failure(failures, "unsupported_result_authority_class", "result_authority_class", "result authority class is not recognized")
    if research_input.research_risk_class and research_input.research_risk_class not in RESEARCH_RISK_CLASSES:
        _add_failure(failures, "unsupported_research_risk_class", "research_risk_class", "research risk class is not recognized")
    if research_input.source_metadata_claimed and not research_input.source_quality_class:
        _add_failure(
            failures,
            "missing_source_quality_class",
            "source_quality_class",
            "claimed source metadata requires an explicit source quality class",
        )
    if research_input.source_metadata_claimed and not (research_input.source_refs or research_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "claimed source metadata requires source refs or provenance",
        )


def _validate_privacy(
    research_input: WebResearchGatewayInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[WebResearchGatewayFailure],
) -> None:
    if research_input.privacy_class in {"secret_like", "credential_like"}:
        _add_failure(failures, "secret_or_credential_query_blocked", "privacy_class", "secrets and credentials cannot become web queries")
    if research_input.privacy_class in {"private_user_context", "private_repo_context"} and research_input.source_provider_class in FUTURE_PROVIDER_CLASSES:
        _add_failure(failures, "private_context_external_query_blocked", "privacy_class", "private user or repo context cannot be routed to web providers")
    if research_input.privacy_class == "unknown" and research_input.source_provider_class in FUTURE_PROVIDER_CLASSES:
        _add_failure(failures, "unknown_privacy_external_query_blocked", "privacy_class", "unknown privacy blocks external query planning")
    if research_input.memory_derived_context and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "memory-derived web research context requires Memory Governance")
    if (research_input.project_or_user_scoped_context or research_input.privacy_class in PRIVATE_OR_SENSITIVE_PRIVACY) and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private or scoped web research metadata requires Identity Scope")
    if research_input.privacy_class == "sensitive" and context_policy_decision is None:
        _add_failure(failures, "missing_context_policy", "context_policy_decision", "sensitive web research metadata requires Context Policy")
    if context_policy_decision is not None and _field_bool(context_policy_decision, "data_sent_external"):
        _add_failure(failures, "context_policy_contradicted", "context_policy_decision", "context policy cannot allow external data transfer here")


def _validate_source_quality(research_input: WebResearchGatewayInput, failures: list[WebResearchGatewayFailure]) -> None:
    if research_input.source_type_class == "search_snippet" and research_input.source_quality_class not in {
        None,
        "snippet_only_low_trust",
        "low_authority",
        "unverifiable",
        "unknown",
    }:
        _add_failure(failures, "search_snippet_cannot_be_high_authority", "source_type_class", "search snippets are low-trust and not evidence")
    if research_input.source_type_class == "community_forum" and research_input.source_quality_class == "high_authority":
        _add_failure(failures, "community_forum_cannot_be_high_authority", "source_quality_class", "community sources must remain lower trust")
    if research_input.freshness_class == "unknown" and research_input.research_subject in {
        "security_advisory_research",
        "news_current_events_research",
        "product_pricing_research",
        "vendor_status_page_research",
    }:
        _add_failure(failures, "unknown_freshness_blocks_current_research", "freshness_class", "current-sensitive research requires freshness metadata")


def _validate_cache(research_input: WebResearchGatewayInput, failures: list[WebResearchGatewayFailure]) -> None:
    if research_input.cache_policy_class == "prohibited_cache" and research_input.source_provider_class in {"local_cache_future"}:
        _add_failure(failures, "cache_policy_blocks_cache_provider", "cache_policy_class", "prohibited cache cannot use a cache provider")
    if research_input.cache_policy_class == "durable_cache_future" and research_input.privacy_class != "public_query":
        _add_failure(failures, "durable_cache_requires_public_query", "cache_policy_class", "durable cache candidates require public query metadata")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[WebResearchGatewayFailure],
    related_references: list[RelatedWebResearchReference],
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
            f"{label} cannot grant web research authority, dispatch, grants, evidence, verifier success, execution, network calls, cache writes, truth, or reports",
        )
    related_references.append(
        RelatedWebResearchReference(
            label=label,
            observed_status=_related_status(decision),
            reference_only=True,
            authority=False,
            future_gated=_related_future_gated(decision),
            implementation_claim=False,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[WebResearchGatewayFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, source truth, synthesis truth, proof, or private leakage",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform web/search/browser/API/fetch/scrape/model/tool/MCP/cache/report/mutation/external behavior",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", WEB_RESEARCH_GATEWAY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "web research gateway metadata cannot grant execution permission",
            )


def _readiness_status(
    research_input: WebResearchGatewayInput | None,
    failures: list[WebResearchGatewayFailure],
    future_gated: bool,
) -> str:
    if research_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(
            "secret" in reason
            or "credential" in reason
            or "private_context" in reason
            or "unknown_privacy" in reason
            or "private_query_leak" in reason
            for reason in reasons
        ):
            return "blocked_by_privacy_policy"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if any("search_snippet" in reason or "community_forum" in reason or "freshness" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "truth" in reason or "proof" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        if any(
            "denied" in reason
            or "external" in reason
            or "generation" in reason
            or "mutation" in reason
            for reason in reasons
        ):
            return "blocked_by_execution_claim"
        if any("cache" in reason for reason in reasons):
            return "blocked_by_cache_policy"
        return "blocked_by_policy"
    if future_gated:
        return "future_gated"
    if research_input.human_review_required or _human_review_required(research_input, failures, future_gated):
        return "proposal_requires_human_review"
    return "research_plan_ready"


def _query_privacy_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.privacy_class in PRIVATE_OR_SENSITIVE_PRIVACY:
        return "redaction_required"
    return "public_or_no_external_data"


def _provider_status(
    research_input: WebResearchGatewayInput | None,
    failures: list[WebResearchGatewayFailure],
    future_gated: bool,
) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.source_provider_class == "no_provider":
        return "no_provider"
    if future_gated:
        return "future_gated"
    if research_input.source_provider_class == "local_cache_future":
        return "future_cache_candidate"
    return "provider_candidate_only"


def _source_quality_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.source_quality_class in {"community_low_trust", "snippet_only_low_trust", "low_authority", "unverifiable"}:
        return "low_trust_candidate"
    if research_input.source_quality_class == "conflicting":
        return "conflicting_candidate"
    if research_input.source_quality_class == "high_authority":
        return "high_authority_candidate"
    return "quality_candidate"


def _freshness_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.freshness_class == "stale":
        return "stale_preserved"
    if research_input.freshness_class == "unknown":
        return "unknown_freshness"
    return "freshness_requirement_preserved"


def _citation_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.result_authority_class == "citation_candidate_only" or research_input.citation_required:
        return "citation_candidate_only"
    return "citation_not_claimed"


def _cache_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    if research_input.cache_policy_class == "no_cache":
        return "no_cache"
    if research_input.cache_policy_class == "session_cache_only":
        return "session_cache_candidate_only"
    if research_input.cache_policy_class == "source_ref_cache_only":
        return "source_ref_cache_candidate_only"
    if research_input.cache_policy_class == "prohibited_cache":
        return "cache_prohibited"
    return "future_cache_candidate"


def _result_authority_status(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if research_input is None or failures:
        return "blocked"
    return research_input.result_authority_class or "source_candidate_only"


def _risk_class(research_input: WebResearchGatewayInput | None, failures: list[WebResearchGatewayFailure]) -> str:
    if failures:
        return "high"
    if research_input is None:
        return "unknown"
    if research_input.research_risk_class:
        return research_input.research_risk_class
    if research_input.privacy_class in {"secret_like", "credential_like", "regulated_or_compliance_sensitive"}:
        return "critical"
    if research_input.privacy_class in PRIVATE_OR_SENSITIVE_PRIVACY:
        return "high"
    return "info"


def _human_review_required(
    research_input: WebResearchGatewayInput | None,
    failures: list[WebResearchGatewayFailure],
    future_gated: bool,
) -> bool:
    if research_input is None:
        return True
    if failures or future_gated or research_input.human_review_required:
        return True
    return (
        research_input.privacy_class in PRIVATE_OR_SENSITIVE_PRIVACY
        or research_input.source_quality_class in {"community_low_trust", "snippet_only_low_trust", "unverifiable", "conflicting", "unknown"}
        or research_input.freshness_class in {"stale", "unknown"}
        or research_input.contradiction_present
        or research_input.cache_policy_class in {"durable_cache_future", "prohibited_cache", "unknown"}
    )


def _is_future_gated(research_input: WebResearchGatewayInput) -> bool:
    return (
        research_input.source_provider_class in FUTURE_PROVIDER_CLASSES
        or research_input.research_operation in FUTURE_OPERATIONS
        or research_input.research_subject in {"github_public_repo_research_future", "github_issue_pr_research_future"}
        or research_input.source_type_class == "scraped_page_extract_future"
        or research_input.cache_policy_class == "durable_cache_future"
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "readiness_status",
        "policy_status",
        "policy_outcome",
        "governance_status",
        "scope_status",
        "selection_mode",
        "probe_result_status",
        "inventory_status",
        "lifecycle_state",
        "query_status",
        "attribution_status",
        "display_state",
        "decision_status",
    ):
        value = _field_value(decision, field)
        if value:
            return str(value)
    return None


def _related_future_gated(decision: Any) -> bool:
    status = str(_related_status(decision) or "")
    return _field_bool(decision, "future_gated") or "future" in status


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
    failures: list[WebResearchGatewayFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(WebResearchGatewayFailure(reason=reason, field=field, message=message))
