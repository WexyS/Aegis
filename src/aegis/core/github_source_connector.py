from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


GITHUB_SOURCE_CONNECTOR_VERSION = "github-source-connector-readiness/1"
GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION = "not_granted_by_github_source_connector"

GITHUB_OBJECT_CLASSES = {
    "github_repository",
    "github_file",
    "github_directory",
    "github_branch",
    "github_commit",
    "github_tag",
    "github_release",
    "github_issue",
    "github_pull_request",
    "github_discussion",
    "github_actions_workflow",
    "github_security_advisory",
    "github_package",
    "github_gist_future",
    "unknown",
}

REPOSITORY_VISIBILITY_CLASSES = {
    "public_repository",
    "private_repository",
    "internal_repository_future",
    "fork_public",
    "fork_private",
    "archived_repository",
    "deleted_or_unavailable",
    "unknown_visibility",
}

SOURCE_INTENT_CLASSES = {
    "repo_overview",
    "readme_review",
    "architecture_review",
    "dependency_review",
    "security_static_notes",
    "issue_triage",
    "pull_request_review",
    "release_notes_review",
    "changelog_review",
    "documentation_review",
    "license_review",
    "repo_audit_candidate_source",
    "developer_work_passport_candidate_source",
    "compliance_evidence_candidate_source",
    "source_citation_lookup",
    "unknown",
}

ACCESS_METHOD_CLASSES = {
    "no_access",
    "url_classification_only",
    "github_api_future",
    "browser_fetch_future",
    "raw_file_fetch_future",
    "git_clone_future",
    "local_clone_future",
    "mcp_github_future",
    "unknown",
}

PRIVACY_CLASSES = {
    "public_metadata",
    "public_source_candidate",
    "private_repo_metadata",
    "private_repo_content",
    "secret_like",
    "credential_like",
    "personal_private",
    "sensitive",
    "unknown",
}

SOURCE_TRUST_CLASSES = {
    "source_ref_candidate",
    "public_metadata_candidate",
    "official_github_metadata_candidate",
    "repository_content_candidate",
    "issue_or_pr_discussion_low_trust",
    "user_generated_low_trust",
    "archived_or_stale",
    "unavailable",
    "unknown",
}

FRESHNESS_CLASSES = {
    "commit_pinned",
    "branch_floating",
    "release_pinned",
    "tag_pinned",
    "current_required",
    "recent_required",
    "historical_allowed",
    "stale",
    "unknown",
}

CACHE_POLICY_CLASSES = {
    "no_cache",
    "source_ref_only",
    "session_metadata_only",
    "short_ttl_metadata",
    "durable_cache_future",
    "raw_content_cache_prohibited",
    "unknown",
}

ALLOWED_FUTURE_SOURCE_SCOPES = {
    "repository_metadata_only",
    "readme_candidate",
    "docs_candidate",
    "package_metadata_candidate",
    "dependency_manifest_candidate",
    "selected_file_candidate",
    "issue_metadata_candidate",
    "pr_metadata_candidate",
    "release_metadata_candidate",
    "no_raw_content",
    "unknown",
}

BLOCKED_SOURCE_SCOPES = {
    "secrets",
    "credentials",
    "env_files",
    "private_keys",
    "generated_artifacts",
    "build_outputs",
    "node_modules",
    "vendor_dependencies",
    "model_files",
    "vector_db_files",
    "runtime_journals",
    "raw_evidence_files",
    "unknown_sensitive",
}

FUTURE_ACCESS_METHODS = {
    "github_api_future",
    "browser_fetch_future",
    "raw_file_fetch_future",
    "git_clone_future",
    "local_clone_future",
    "mcp_github_future",
}

PRIVATE_VISIBILITY_CLASSES = {"private_repository", "internal_repository_future", "fork_private"}
PRIVATE_PRIVACY_CLASSES = {"private_repo_metadata", "private_repo_content", "personal_private", "sensitive", "unknown"}
LOW_TRUST_OBJECTS = {"github_issue", "github_pull_request", "github_discussion"}
PINNED_FRESHNESS_CLASSES = {"commit_pinned", "release_pinned", "tag_pinned"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_github_source": "github_source_cannot_provide_evidence",
    "evidence_created": "github_source_cannot_provide_evidence",
    "verifier_success": "github_source_cannot_mark_verifier_success",
    "verified_success": "github_source_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "frontend_output_is_truth": "frontend_output_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "source_truth_claimed": "source_truth_claim_denied",
    "repo_audit_proof_claimed": "repo_audit_proof_claim_denied",
    "private_repo_access_allowed": "private_repo_access_permission_denied",
    "raw_content_ingestion_allowed": "raw_content_ingestion_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "github_api_called": "github_api_call_denied",
    "github_url_fetched": "github_url_fetch_denied",
    "browser_fetch_performed": "browser_fetch_denied",
    "raw_file_fetch_performed": "raw_file_fetch_denied",
    "git_clone_performed": "git_clone_denied",
    "local_repo_read_performed": "local_repo_read_denied",
    "repo_scan_performed": "repo_scan_denied",
    "file_read_performed": "file_read_denied",
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
    "model_call_performed": "model_call_denied",
    "web_query_performed": "web_query_denied",
    "http_request_performed": "http_request_denied",
    "external_api_called": "external_api_call_denied",
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

FORBIDDEN_BEHAVIOR_REASONS = set(FORBIDDEN_BEHAVIOR_FIELDS.values())


@dataclass(frozen=True)
class GitHubSourceConnectorFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedGitHubSourceReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class GitHubSourceConnectorInput:
    request_id: str | None
    github_object_class: str | None
    repository_visibility_class: str | None
    source_intent_class: str | None
    access_method_class: str | None
    privacy_class: str | None
    source_trust_class: str | None
    freshness_class: str | None
    cache_policy_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    allowed_future_source_scopes: tuple[str, ...]
    blocked_source_scopes: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    memory_derived_context: bool
    project_or_repository_scoped: bool
    raw_content_requested: bool


@dataclass(frozen=True)
class GitHubSourceConnectorDecision:
    contract_version: str
    connector_status: str
    request_id: str | None
    github_object_class: str | None
    repository_visibility_class: str | None
    source_intent_class: str | None
    access_method_class: str | None
    privacy_class: str | None
    source_trust_class: str | None
    freshness_class: str | None
    cache_policy_class: str | None
    namespace: str | None
    source_readiness_status: str
    privacy_access_status: str
    source_trust_status: str
    freshness_status: str
    cache_status: str
    raw_content_status: str
    allowed_future_source_scopes: tuple[str, ...]
    blocked_source_scopes: tuple[str, ...]
    lower_trust_source: bool
    human_review_required: bool
    future_gated: bool
    related_references: tuple[RelatedGitHubSourceReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[GitHubSourceConnectorFailure, ...]
    source_input: GitHubSourceConnectorInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_github_source: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    github_api_called: bool = False
    github_url_fetched: bool = False
    browser_fetch_performed: bool = False
    raw_file_fetch_performed: bool = False
    git_clone_performed: bool = False
    local_repo_read_performed: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
    mcp_call_performed: bool = False
    tool_call_performed: bool = False
    model_call_performed: bool = False
    web_query_performed: bool = False
    http_request_performed: bool = False
    external_api_called: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    cache_written: bool = False
    source_record_created: bool = False
    citation_record_created: bool = False
    report_generated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    private_repo_access_allowed: bool = False
    raw_content_ingestion_allowed: bool = False
    source_truth_claimed: bool = False
    repo_audit_proof_claimed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_github_source_connector_request(
    request: Mapping[str, Any] | None,
    *,
    web_research_gateway_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
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
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> GitHubSourceConnectorDecision:
    """Validate GitHub source planning metadata without network or repo-read behavior."""

    if not isinstance(request, Mapping):
        failure = GitHubSourceConnectorFailure(
            reason="missing_request",
            field="request",
            message="GitHub source connector requires caller-supplied metadata",
        )
        return _decision(source_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[GitHubSourceConnectorFailure] = []
    related_references: list[RelatedGitHubSourceReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "web_research_gateway": web_research_gateway_decision,
        "local_model_context_profile": local_model_context_profile_decision,
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
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    source_input = GitHubSourceConnectorInput(
        request_id=_text(data.get("request_id")),
        github_object_class=_text(data.get("github_object_class")),
        repository_visibility_class=_text(data.get("repository_visibility_class")),
        source_intent_class=_text(data.get("source_intent_class")),
        access_method_class=_text(data.get("access_method_class")),
        privacy_class=_text(data.get("privacy_class")),
        source_trust_class=_text(data.get("source_trust_class")),
        freshness_class=_text(data.get("freshness_class")),
        cache_policy_class=_text(data.get("cache_policy_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        allowed_future_source_scopes=_text_tuple(data.get("allowed_future_source_scopes")),
        blocked_source_scopes=_text_tuple(data.get("blocked_source_scopes")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        memory_derived_context=_truthy(data.get("memory_derived_context")),
        project_or_repository_scoped=_truthy(data.get("project_or_repository_scoped")),
        raw_content_requested=_truthy(data.get("raw_content_requested")),
    )

    _validate_required(source_input, failures)
    _validate_privacy_and_access(source_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)
    _validate_source_scope(source_input, failures)
    _validate_trust_and_freshness(source_input, failures)
    _validate_cache(source_input, failures)

    return _decision(
        source_input=source_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    source_input: GitHubSourceConnectorInput | None,
    related_references: tuple[RelatedGitHubSourceReference, ...],
    failures: tuple[GitHubSourceConnectorFailure, ...],
) -> GitHubSourceConnectorDecision:
    future_gated = bool(source_input and _is_future_gated(source_input))
    return GitHubSourceConnectorDecision(
        contract_version=GITHUB_SOURCE_CONNECTOR_VERSION,
        connector_status=_connector_status(source_input, list(failures), future_gated),
        request_id=source_input.request_id if source_input else None,
        github_object_class=source_input.github_object_class if source_input else None,
        repository_visibility_class=source_input.repository_visibility_class if source_input else None,
        source_intent_class=source_input.source_intent_class if source_input else None,
        access_method_class=source_input.access_method_class if source_input else None,
        privacy_class=source_input.privacy_class if source_input else None,
        source_trust_class=source_input.source_trust_class if source_input else None,
        freshness_class=source_input.freshness_class if source_input else None,
        cache_policy_class=source_input.cache_policy_class if source_input else None,
        namespace=source_input.namespace if source_input else None,
        source_readiness_status=_source_readiness_status(source_input, list(failures), future_gated),
        privacy_access_status=_privacy_access_status(source_input, list(failures)),
        source_trust_status=_source_trust_status(source_input, list(failures)),
        freshness_status=_freshness_status(source_input, list(failures)),
        cache_status=_cache_status(source_input, list(failures)),
        raw_content_status=_raw_content_status(source_input, list(failures)),
        allowed_future_source_scopes=source_input.allowed_future_source_scopes if source_input else (),
        blocked_source_scopes=source_input.blocked_source_scopes if source_input else (),
        lower_trust_source=bool(source_input and _is_low_trust(source_input)),
        human_review_required=_human_review_required(source_input, list(failures), future_gated),
        future_gated=future_gated,
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        source_input=source_input,
    )


def _validate_required(source_input: GitHubSourceConnectorInput, failures: list[GitHubSourceConnectorFailure]) -> None:
    for field in (
        "request_id",
        "github_object_class",
        "repository_visibility_class",
        "source_intent_class",
        "access_method_class",
        "privacy_class",
        "source_trust_class",
        "freshness_class",
        "cache_policy_class",
        "namespace",
    ):
        if not getattr(source_input, field):
            _add_failure(failures, f"missing_{field}", field, f"GitHub source request is missing {field}")
    if source_input.github_object_class and source_input.github_object_class not in GITHUB_OBJECT_CLASSES:
        _add_failure(failures, "unsupported_github_object_class", "github_object_class", "GitHub object class is not recognized")
    if source_input.repository_visibility_class and source_input.repository_visibility_class not in REPOSITORY_VISIBILITY_CLASSES:
        _add_failure(
            failures,
            "unsupported_repository_visibility_class",
            "repository_visibility_class",
            "repository visibility class is not recognized",
        )
    if source_input.source_intent_class and source_input.source_intent_class not in SOURCE_INTENT_CLASSES:
        _add_failure(failures, "unsupported_source_intent_class", "source_intent_class", "source intent class is not recognized")
    if source_input.access_method_class and source_input.access_method_class not in ACCESS_METHOD_CLASSES:
        _add_failure(failures, "unsupported_access_method_class", "access_method_class", "access method class is not recognized")
    if source_input.privacy_class and source_input.privacy_class not in PRIVACY_CLASSES:
        _add_failure(failures, "unsupported_privacy_class", "privacy_class", "privacy class is not recognized")
    if source_input.source_trust_class and source_input.source_trust_class not in SOURCE_TRUST_CLASSES:
        _add_failure(failures, "unsupported_source_trust_class", "source_trust_class", "source trust class is not recognized")
    if source_input.freshness_class and source_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")
    if source_input.cache_policy_class and source_input.cache_policy_class not in CACHE_POLICY_CLASSES:
        _add_failure(failures, "unsupported_cache_policy_class", "cache_policy_class", "cache policy class is not recognized")
    if not (source_input.source_refs or source_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "GitHub source metadata requires source refs or provenance",
        )


def _validate_privacy_and_access(
    source_input: GitHubSourceConnectorInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[GitHubSourceConnectorFailure],
) -> None:
    if source_input.privacy_class in {"secret_like", "credential_like"}:
        _add_failure(failures, "secret_or_credential_source_blocked", "privacy_class", "secret and credential GitHub source metadata is blocked")
    if source_input.repository_visibility_class == "deleted_or_unavailable" or source_input.source_trust_class == "unavailable":
        _add_failure(failures, "source_unavailable", "repository_visibility_class", "deleted or unavailable repositories cannot be source candidates")
    if source_input.repository_visibility_class in PRIVATE_VISIBILITY_CLASSES and source_input.access_method_class in FUTURE_ACCESS_METHODS:
        _add_failure(failures, "private_repository_access_blocked", "access_method_class", "private repository API/fetch/clone access is blocked")
    if source_input.privacy_class == "private_repo_content" and source_input.access_method_class in FUTURE_ACCESS_METHODS:
        _add_failure(failures, "private_repo_content_access_blocked", "privacy_class", "private repo content requires a later explicit boundary")
    if source_input.privacy_class == "unknown" and source_input.access_method_class in FUTURE_ACCESS_METHODS:
        _add_failure(failures, "unknown_privacy_external_access_blocked", "privacy_class", "unknown privacy blocks GitHub access planning")
    if source_input.raw_content_requested:
        _add_failure(failures, "raw_content_request_blocked", "raw_content_requested", "raw content ingestion is not allowed by readiness metadata")
    if source_input.memory_derived_context and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "memory-derived GitHub source context requires Memory Governance")
    if _requires_identity(source_input) and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private or repository-scoped GitHub metadata requires Identity Scope")
    if context_policy_decision is not None and _field_bool(context_policy_decision, "data_sent_external"):
        _add_failure(failures, "context_policy_contradicted", "context_policy_decision", "Context Policy cannot allow external transfer here")


def _validate_source_scope(source_input: GitHubSourceConnectorInput, failures: list[GitHubSourceConnectorFailure]) -> None:
    for scope in source_input.allowed_future_source_scopes:
        if scope not in ALLOWED_FUTURE_SOURCE_SCOPES:
            _add_failure(failures, "unsupported_allowed_source_scope", "allowed_future_source_scopes", "future source scope is not recognized")
        if scope in BLOCKED_SOURCE_SCOPES:
            _add_failure(failures, "blocked_scope_laundered_as_allowed", "allowed_future_source_scopes", "blocked source scope cannot be allowed")
    for scope in source_input.blocked_source_scopes:
        if scope not in BLOCKED_SOURCE_SCOPES:
            _add_failure(failures, "unsupported_blocked_source_scope", "blocked_source_scopes", "blocked source scope is not recognized")
        else:
            _add_failure(failures, f"blocked_source_scope_{scope}", "blocked_source_scopes", f"{scope} is blocked for GitHub source readiness")
    if "no_raw_content" not in source_input.allowed_future_source_scopes and source_input.access_method_class in {"raw_file_fetch_future", "git_clone_future"}:
        _add_failure(failures, "raw_content_boundary_missing", "allowed_future_source_scopes", "raw-capable future methods require no_raw_content boundary metadata")


def _validate_trust_and_freshness(source_input: GitHubSourceConnectorInput, failures: list[GitHubSourceConnectorFailure]) -> None:
    if source_input.github_object_class in LOW_TRUST_OBJECTS and source_input.source_trust_class not in {
        None,
        "issue_or_pr_discussion_low_trust",
        "user_generated_low_trust",
        "source_ref_candidate",
        "unknown",
    }:
        _add_failure(failures, "issue_pr_discussion_must_remain_low_trust", "source_trust_class", "issues and PR discussions are user-generated")
    if source_input.github_object_class == "github_security_advisory":
        if source_input.source_trust_class not in {None, "official_github_metadata_candidate", "source_ref_candidate"}:
            _add_failure(failures, "security_advisory_requires_official_metadata", "source_trust_class", "security advisory candidates require official metadata")
        if source_input.freshness_class not in {None, "current_required", "recent_required", "commit_pinned", "release_pinned", "tag_pinned"}:
            _add_failure(failures, "security_advisory_requires_freshness", "freshness_class", "security advisory candidates require freshness metadata")
    if source_input.repository_visibility_class == "archived_repository" and source_input.source_trust_class not in {None, "archived_or_stale", "source_ref_candidate"}:
        _add_failure(failures, "archived_repository_must_preserve_stale_status", "source_trust_class", "archived repositories must preserve stale/archived status")


def _validate_cache(source_input: GitHubSourceConnectorInput, failures: list[GitHubSourceConnectorFailure]) -> None:
    if source_input.cache_policy_class == "durable_cache_future" and source_input.privacy_class not in {"public_metadata", "public_source_candidate"}:
        _add_failure(failures, "durable_cache_requires_public_source", "cache_policy_class", "durable cache candidates require public source metadata")
    if source_input.cache_policy_class != "raw_content_cache_prohibited" and source_input.access_method_class == "raw_file_fetch_future":
        _add_failure(failures, "raw_file_future_requires_raw_cache_prohibition", "cache_policy_class", "raw file fetch candidates require raw content cache prohibition")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[GitHubSourceConnectorFailure],
    related_references: list[RelatedGitHubSourceReference],
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
            f"{label} cannot authorize GitHub access, fetch, clone, reads, records, truth, evidence, verifier success, dispatch, or grants",
        )
    related_references.append(
        RelatedGitHubSourceReference(
            label=label,
            observed_status=_related_status(decision),
            authority=False,
            future_gated=_field_bool(decision, "future_gated"),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(label: str, source: Any, failures: list[GitHubSourceConnectorFailure]) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, truth, proof, or access permission",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot call GitHub, fetch, clone, read files, call models/tools, cache, create records, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", GITHUB_SOURCE_CONNECTOR_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "GitHub source metadata cannot grant execution permission",
            )


def _connector_status(
    source_input: GitHubSourceConnectorInput | None,
    failures: list[GitHubSourceConnectorFailure],
    future_gated: bool,
) -> str:
    if source_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if "execution_permission_claim_denied" in reasons:
            return "blocked_by_authority_claim"
        if any(reason in FORBIDDEN_BEHAVIOR_REASONS for reason in reasons):
            return "blocked_by_execution_claim"
        if any("call" in reason or "fetch" in reason or "clone" in reason or "read" in reason or "cache_write" in reason or "record" in reason or "report" in reason or "artifact" in reason or "transfer" in reason or "mutation" in reason for reason in reasons):
            return "blocked_by_execution_claim"
        if any("secret" in reason or "credential" in reason or "private" in reason or "scope" in reason or "raw_content" in reason or "unavailable" in reason for reason in reasons):
            return "blocked_by_privacy_or_source_scope"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        return "blocked_by_policy"
    if future_gated:
        return "source_candidate_future_gated"
    if source_input.human_review_required or _human_review_required(source_input, failures, future_gated):
        return "source_candidate_requires_human_review"
    return "source_candidate_ready"


def _source_readiness_status(
    source_input: GitHubSourceConnectorInput | None,
    failures: list[GitHubSourceConnectorFailure],
    future_gated: bool,
) -> str:
    if source_input is None or failures:
        return "blocked"
    if future_gated:
        return "future_access_candidate_only"
    if source_input.access_method_class == "url_classification_only":
        return "url_classification_metadata_only"
    return "source_ref_metadata_only"


def _privacy_access_status(source_input: GitHubSourceConnectorInput | None, failures: list[GitHubSourceConnectorFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.privacy_class in {"public_metadata", "public_source_candidate"}:
        return "public_metadata_candidate"
    if source_input.privacy_class in {"private_repo_metadata", "private_repo_content"}:
        return "private_repo_reference_only"
    if source_input.privacy_class == "unknown":
        return "unknown_requires_review"
    return "restricted_reference_only"


def _source_trust_status(source_input: GitHubSourceConnectorInput | None, failures: list[GitHubSourceConnectorFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if _is_low_trust(source_input):
        return "low_trust_user_generated_candidate"
    if source_input.source_trust_class == "official_github_metadata_candidate":
        return "official_metadata_candidate_not_evidence"
    if source_input.source_trust_class == "archived_or_stale":
        return "archived_or_stale_candidate"
    return "source_ref_candidate_not_truth"


def _freshness_status(source_input: GitHubSourceConnectorInput | None, failures: list[GitHubSourceConnectorFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.freshness_class == "branch_floating":
        return "floating_branch_not_pinned"
    if source_input.freshness_class in PINNED_FRESHNESS_CLASSES:
        return "pinned_metadata_candidate_not_proof"
    if source_input.freshness_class in {"current_required", "recent_required"}:
        return "freshness_requirement_preserved"
    if source_input.freshness_class == "stale":
        return "stale_metadata_preserved"
    return "freshness_metadata_only"


def _cache_status(source_input: GitHubSourceConnectorInput | None, failures: list[GitHubSourceConnectorFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.cache_policy_class == "no_cache":
        return "no_cache"
    if source_input.cache_policy_class == "source_ref_only":
        return "source_ref_only"
    if source_input.cache_policy_class == "raw_content_cache_prohibited":
        return "raw_content_cache_prohibited"
    return "metadata_cache_candidate_only"


def _raw_content_status(source_input: GitHubSourceConnectorInput | None, failures: list[GitHubSourceConnectorFailure]) -> str:
    if source_input is None or failures:
        return "blocked"
    if source_input.access_method_class == "raw_file_fetch_future":
        return "raw_fetch_future_gated_no_ingestion"
    if "no_raw_content" in source_input.allowed_future_source_scopes:
        return "raw_content_prohibited"
    return "metadata_only_no_raw_ingestion"


def _human_review_required(
    source_input: GitHubSourceConnectorInput | None,
    failures: list[GitHubSourceConnectorFailure],
    future_gated: bool,
) -> bool:
    if source_input is None:
        return False
    return bool(
        failures
        or future_gated
        or source_input.human_review_required
        or source_input.repository_visibility_class in PRIVATE_VISIBILITY_CLASSES
        or source_input.privacy_class in PRIVATE_PRIVACY_CLASSES
        or source_input.github_object_class in LOW_TRUST_OBJECTS
        or source_input.freshness_class in {"branch_floating", "unknown"}
        or source_input.source_trust_class in {"unknown", "user_generated_low_trust", "issue_or_pr_discussion_low_trust"}
    )


def _is_future_gated(source_input: GitHubSourceConnectorInput) -> bool:
    return source_input.access_method_class in FUTURE_ACCESS_METHODS or source_input.github_object_class == "github_gist_future"


def _is_low_trust(source_input: GitHubSourceConnectorInput) -> bool:
    return source_input.github_object_class in LOW_TRUST_OBJECTS or source_input.source_trust_class in {
        "issue_or_pr_discussion_low_trust",
        "user_generated_low_trust",
        "unknown",
    }


def _requires_identity(source_input: GitHubSourceConnectorInput) -> bool:
    return bool(
        source_input.project_or_repository_scoped
        or source_input.repository_visibility_class in PRIVATE_VISIBILITY_CLASSES
        or source_input.privacy_class in {"private_repo_metadata", "private_repo_content", "personal_private", "sensitive"}
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "connector_status",
        "readiness_status",
        "profile_status",
        "policy_status",
        "scope_status",
        "governance_status",
        "selection_mode",
        "probe_status",
        "inventory_status",
        "audit_status",
        "passport_status",
        "compliance_status",
        "mission_status",
        "simulation_status",
    ):
        value = _field_value(decision, field)
        if value is not None:
            return str(value)
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
    return bool(value)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (deepcopy(dict(value)),)
    if isinstance(value, (list, tuple)):
        return tuple(deepcopy(dict(item)) for item in value if isinstance(item, Mapping))
    return ()


def _add_failure(
    failures: list[GitHubSourceConnectorFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(GitHubSourceConnectorFailure(reason=reason, field=field, message=message))
