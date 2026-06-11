from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

from aegis.core.config import PROJECT_ROOT
from aegis.core.identity_scope import validate_identity_scope_request
from aegis.core.memory_governance import validate_memory_governance_request


MEMORY_OS_RC1_SCHEMA_VERSION = "memory-os-rc1-core/1"
MEMORY_OS_RC1_EXECUTION_PERMISSION = "not_granted_by_memory_os_rc1"
DEFAULT_MEMORY_DB_PATH = PROJECT_ROOT / "data" / "memory_os_rc1.sqlite3"

MEMORY_STATUSES = {"proposed", "active", "rejected", "deleted"}
MEMORY_SCOPES = {"session", "project", "repository"}
MEMORY_SENSITIVITIES = {"public", "internal", "private", "sensitive", "secret_like"}
BLOCKED_SENSITIVITIES = {"secret_like", "credential_like", "unknown"}

GOVERNANCE_SCOPE_BY_RC_SCOPE = {
    "session": "session_only",
    "project": "project_scoped",
    "repository": "repository_scoped",
}

IDENTITY_PERSISTENCE_BY_RC_SCOPE = {
    "session": "session_only",
    "project": "project_scoped",
    "repository": "project_scoped",
}

PRIVACY_BY_SENSITIVITY = {
    "public": "public",
    "internal": "internal",
    "private": "local_private",
    "sensitive": "local_sensitive",
    "secret_like": "secret_like",
}

RETENTION_BY_SCOPE = {
    "session": "session_ttl",
    "project": "project_ttl",
    "repository": "project_ttl",
}


@dataclass(frozen=True)
class MemoryItem:
    id: str
    type: str
    content: str
    content_summary: str
    scope: str
    status: str
    sensitivity: str
    source_refs: tuple[Mapping[str, Any], ...]
    project_ref: str | None
    repository_ref: str | None
    session_ref: str | None
    created_at: int
    updated_at: int
    deleted_at: int | None
    metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "content_summary": self.content_summary,
            "scope": self.scope,
            "status": self.status,
            "sensitivity": self.sensitivity,
            "source_refs": [dict(item) for item in self.source_refs],
            "project_ref": self.project_ref,
            "repository_ref": self.repository_ref,
            "session_ref": self.session_ref,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "metadata": dict(self.metadata),
            "candidate_only": True,
            "retrieved_memory_is_truth": False,
            "memory_output_is_authority": False,
            "execution_permission": MEMORY_OS_RC1_EXECUTION_PERMISSION,
        }


@dataclass(frozen=True)
class MemoryOperationResult:
    ok: bool
    operation: str
    status: str
    memory_id: str | None = None
    memory: MemoryItem | None = None
    memories: tuple[MemoryItem, ...] = ()
    validation_result: Mapping[str, Any] | None = None
    governance_result: Mapping[str, Any] | None = None
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    failure_reasons: tuple[str, ...] = ()
    storage_mutation_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "operation": self.operation,
            "status": self.status,
            "memory_id": self.memory_id,
            "memory": self.memory.to_dict() if self.memory else None,
            "memories": [item.to_dict() for item in self.memories],
            "result_count": len(self.memories),
            "validation_result": dict(self.validation_result or {}),
            "governance_result": dict(self.governance_result or {}),
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "failure_reasons": list(self.failure_reasons),
            "storage_mutation_performed": self.storage_mutation_performed,
            "authority": False,
            "runtime_dispatch_allowed": False,
            "execution_permission": MEMORY_OS_RC1_EXECUTION_PERMISSION,
            "approval_grant": False,
            "capability_grant": False,
            "lease_grant": False,
            "evidence_provided_by_memory": False,
            "verifier_success": False,
            "memory_output_is_authority": False,
            "retrieved_memory_is_truth": False,
            "memory_retrieval_is_authority": False,
            "context_permission_granted": False,
            "model_call_performed": False,
            "mcp_call_performed": False,
            "tool_call_performed": False,
            "cloud_sync_performed": False,
            "data_sent_external": False,
        }
        return payload


class MemoryStore:
    """SQLite-backed Memory OS RC1-Core store.

    This store is intentionally local and narrow. It persists explicit API/store
    requests only; it does not infer memories, call models, index vectors, emit
    runtime events, or grant authority.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_MEMORY_DB_PATH

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_summary TEXT NOT NULL DEFAULT '',
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    source_refs_json TEXT NOT NULL DEFAULT '[]',
                    project_ref TEXT,
                    repository_ref TEXT,
                    session_ref TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    deleted_at INTEGER,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_items(status);
                CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_items(scope);
                CREATE INDEX IF NOT EXISTS idx_memory_sensitivity ON memory_items(sensitivity);
                CREATE INDEX IF NOT EXISTS idx_memory_project ON memory_items(project_ref);
                CREATE INDEX IF NOT EXISTS idx_memory_repository ON memory_items(repository_ref);
                CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_items(session_ref);
                """
            )

    def propose(self, request: Mapping[str, Any]) -> MemoryOperationResult:
        memory_id = _text(request.get("id")) or _text(request.get("memory_id")) or f"mem_{uuid4().hex}"
        normalized = self._normalize_proposal(request, memory_id)
        validation = self._validate_proposal(normalized)
        if validation["status"] != "valid":
            return MemoryOperationResult(
                ok=False,
                operation="propose",
                status="blocked_by_validation",
                memory_id=memory_id,
                validation_result=validation,
                governance_result={"status": "not_run_due_to_validation_failure"},
                failure_reasons=tuple(validation["failure_reasons"]),
                limitations=_common_limitations(),
            )

        governance = self._validate_governance(normalized)
        if governance["status"] not in {"proposal_ready", "proposal_requires_human_review"}:
            return MemoryOperationResult(
                ok=False,
                operation="propose",
                status="blocked_by_governance",
                memory_id=memory_id,
                validation_result=validation,
                governance_result=governance,
                failure_reasons=tuple(governance.get("failure_reasons", ())),
                limitations=_common_limitations(),
            )

        now = _now()
        item = MemoryItem(
            id=memory_id,
            type=normalized["type"],
            content=normalized["content"],
            content_summary=normalized["content_summary"],
            scope=normalized["scope"],
            status="proposed",
            sensitivity=normalized["sensitivity"],
            source_refs=tuple(normalized["source_refs"]),
            project_ref=normalized["project_ref"],
            repository_ref=normalized["repository_ref"],
            session_ref=normalized["session_ref"],
            created_at=now,
            updated_at=now,
            deleted_at=None,
            metadata=normalized["metadata"],
        )
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_items (
                    id, type, content, content_summary, scope, status, sensitivity,
                    source_refs_json, project_ref, repository_ref, session_ref,
                    created_at, updated_at, deleted_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _item_values(item),
            )
        return MemoryOperationResult(
            ok=True,
            operation="propose",
            status="proposed",
            memory_id=memory_id,
            memory=item,
            validation_result=validation,
            governance_result=governance,
            limitations=_common_limitations(),
            storage_mutation_performed=True,
        )

    def approve(self, memory_id: str) -> MemoryOperationResult:
        return self._transition(memory_id, operation="approve", from_status="proposed", to_status="active")

    def reject(self, memory_id: str, reason: str | None = None) -> MemoryOperationResult:
        return self._transition(
            memory_id,
            operation="reject",
            from_status="proposed",
            to_status="rejected",
            metadata_patch={"rejection_reason": reason} if reason else None,
        )

    def delete(self, memory_id: str) -> MemoryOperationResult:
        self.initialize()
        item = self.get(memory_id)
        if item is None:
            return _missing_result("delete", memory_id)
        if item.status not in {"proposed", "active"}:
            return MemoryOperationResult(
                ok=False,
                operation="delete",
                status="blocked_by_invalid_transition",
                memory_id=memory_id,
                memory=item,
                validation_result={
                    "status": "invalid_transition",
                    "failure_reasons": ["delete_requires_proposed_or_active_memory"],
                },
                governance_result={"status": "not_applicable_lifecycle_transition"},
                failure_reasons=("delete_requires_proposed_or_active_memory",),
                limitations=_common_limitations(),
            )

        now = _now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE memory_items SET status = ?, updated_at = ?, deleted_at = ? WHERE id = ?",
                ("deleted", now, now, memory_id),
            )
        deleted = self.get(memory_id)
        return MemoryOperationResult(
            ok=True,
            operation="delete",
            status="deleted",
            memory_id=memory_id,
            memory=deleted,
            validation_result={"status": "valid_transition"},
            governance_result={"status": "not_applicable_lifecycle_transition"},
            limitations=_common_limitations(),
            storage_mutation_performed=True,
        )

    def get(self, memory_id: str) -> MemoryItem | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM memory_items WHERE id = ?", (memory_id,)).fetchone()
        return _row_to_item(row) if row else None

    def list_memories(
        self,
        *,
        status: str | None = None,
        scope: str | None = None,
        sensitivity: str | None = None,
        project_ref: str | None = None,
        repository_ref: str | None = None,
        session_ref: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> MemoryOperationResult:
        filters: list[str] = []
        params: list[Any] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        elif not include_deleted:
            filters.append("status != ?")
            params.append("deleted")
        if scope:
            filters.append("scope = ?")
            params.append(scope)
        if sensitivity:
            filters.append("sensitivity = ?")
            params.append(_normalize_sensitivity(sensitivity))
        if project_ref:
            filters.append("project_ref = ?")
            params.append(project_ref)
        if repository_ref:
            filters.append("repository_ref = ?")
            params.append(repository_ref)
        if session_ref:
            filters.append("session_ref = ?")
            params.append(session_ref)

        query = "SELECT * FROM memory_items"
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(_safe_limit(limit))

        self.initialize()
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return MemoryOperationResult(
            ok=True,
            operation="list",
            status="listed",
            memories=tuple(_row_to_item(row) for row in rows),
            validation_result={"status": "valid"},
            governance_result={"status": "not_applicable_read_candidate_projection"},
            warnings=_search_warnings(),
            limitations=_common_limitations(),
        )

    def search(
        self,
        *,
        keyword: str | None = None,
        scope: str | None = None,
        sensitivity: str | None = None,
        project_ref: str | None = None,
        repository_ref: str | None = None,
        session_ref: str | None = None,
        status: str | None = None,
        include_sensitive: bool = False,
        limit: int = 50,
    ) -> MemoryOperationResult:
        filters = ["status = ?"]
        params: list[Any] = [status or "active"]
        if keyword:
            filters.append("(content LIKE ? OR content_summary LIKE ? OR type LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like])
        if scope:
            filters.append("scope = ?")
            params.append(scope)
        if sensitivity:
            filters.append("sensitivity = ?")
            params.append(_normalize_sensitivity(sensitivity))
        elif not include_sensitive:
            filters.append("sensitivity NOT IN (?, ?)")
            params.extend(["sensitive", "secret_like"])
        if project_ref:
            filters.append("project_ref = ?")
            params.append(project_ref)
        if repository_ref:
            filters.append("repository_ref = ?")
            params.append(repository_ref)
        if session_ref:
            filters.append("session_ref = ?")
            params.append(session_ref)

        query = (
            "SELECT * FROM memory_items WHERE "
            + " AND ".join(filters)
            + " ORDER BY updated_at DESC LIMIT ?"
        )
        params.append(_safe_limit(limit))

        self.initialize()
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return MemoryOperationResult(
            ok=True,
            operation="search",
            status="searched",
            memories=tuple(_row_to_item(row) for row in rows),
            validation_result={"status": "valid"},
            governance_result={"status": "not_applicable_read_candidate_projection"},
            warnings=_search_warnings(),
            limitations=_common_limitations(),
        )

    def _transition(
        self,
        memory_id: str,
        *,
        operation: str,
        from_status: str,
        to_status: str,
        metadata_patch: Mapping[str, Any] | None = None,
    ) -> MemoryOperationResult:
        self.initialize()
        item = self.get(memory_id)
        if item is None:
            return _missing_result(operation, memory_id)
        if item.status != from_status:
            return MemoryOperationResult(
                ok=False,
                operation=operation,
                status="blocked_by_invalid_transition",
                memory_id=memory_id,
                memory=item,
                validation_result={
                    "status": "invalid_transition",
                    "failure_reasons": [f"{operation}_requires_{from_status}_memory"],
                },
                governance_result={"status": "not_applicable_lifecycle_transition"},
                failure_reasons=(f"{operation}_requires_{from_status}_memory",),
                limitations=_common_limitations(),
            )
        now = _now()
        metadata = dict(item.metadata)
        if metadata_patch:
            metadata.update(metadata_patch)
        with self._connect() as conn:
            conn.execute(
                "UPDATE memory_items SET status = ?, updated_at = ?, metadata_json = ? WHERE id = ?",
                (to_status, now, json.dumps(metadata, sort_keys=True), memory_id),
            )
        updated = self.get(memory_id)
        return MemoryOperationResult(
            ok=True,
            operation=operation,
            status=to_status,
            memory_id=memory_id,
            memory=updated,
            validation_result={"status": "valid_transition"},
            governance_result={"status": "not_applicable_lifecycle_transition"},
            limitations=_common_limitations(),
            storage_mutation_performed=True,
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _normalize_proposal(self, request: Mapping[str, Any], memory_id: str) -> dict[str, Any]:
        scope = _text(request.get("scope")) or "session"
        sensitivity = _normalize_sensitivity(request.get("sensitivity"))
        source_refs = _source_refs(request.get("source_refs") or request.get("source_ref"))
        if not source_refs:
            source_refs = ({"ref_id": "memory-os-rc1-api", "ref_type": "api_request"},)
        return {
            "id": memory_id,
            "type": _text(request.get("type")) or "temporary_scratch",
            "content": _text(request.get("content")) or "",
            "content_summary": _text(request.get("summary") or request.get("content_summary")) or "",
            "scope": scope,
            "sensitivity": sensitivity,
            "source_refs": source_refs,
            "project_ref": _text(request.get("project_ref")),
            "repository_ref": _text(request.get("repository_ref")),
            "session_ref": _text(request.get("session_ref")),
            "metadata": _mapping_or_empty(request.get("metadata")),
            "request_id": _text(request.get("request_id")) or f"memory-os-rc1:{memory_id}",
            "human_review_required": _truthy(request.get("human_review_required")),
        }

    def _validate_proposal(self, normalized: Mapping[str, Any]) -> dict[str, Any]:
        failures: list[str] = []
        if not normalized["content"]:
            failures.append("missing_content")
        if normalized["scope"] not in MEMORY_SCOPES:
            failures.append("unsupported_scope")
        if normalized["sensitivity"] not in MEMORY_SENSITIVITIES:
            failures.append("unsupported_sensitivity")
        if normalized["sensitivity"] in BLOCKED_SENSITIVITIES:
            failures.append("blocked_sensitive_memory")
        if normalized["scope"] == "session" and not normalized["session_ref"]:
            failures.append("missing_session_ref")
        if normalized["scope"] == "project" and not normalized["project_ref"]:
            failures.append("missing_project_ref")
        if normalized["scope"] == "repository":
            if not normalized["project_ref"]:
                failures.append("missing_project_ref")
            if not normalized["repository_ref"]:
                failures.append("missing_repository_ref")
        return {
            "status": "blocked" if failures else "valid",
            "failure_reasons": failures,
            "schema_version": MEMORY_OS_RC1_SCHEMA_VERSION,
        }

    def _validate_governance(self, normalized: Mapping[str, Any]) -> dict[str, Any]:
        identity_decision = None
        if normalized["scope"] in {"project", "repository"}:
            identity_decision = validate_identity_scope_request(
                {
                    "request_id": f"identity:{normalized['id']}",
                    "scope_id": f"memory-os-rc1:{normalized['scope']}:{normalized['id']}",
                    "subject_kind": "repository" if normalized["scope"] == "repository" else "project",
                    "subject_ref": normalized["repository_ref"] or normalized["project_ref"],
                    "user_ref": "user:local",
                    "profile_ref": "profile:local",
                    "operator_ref": "operator:local",
                    "tenant_ref": "tenant:local",
                    "workspace_ref": "workspace:aegis",
                    "project_ref": normalized["project_ref"],
                    "repository_ref": normalized["repository_ref"],
                    "session_ref": normalized["session_ref"] or f"session:{normalized['id']}",
                    "namespace": "memory_os_rc1",
                    "data_boundary": "private_repo_local_only"
                    if normalized["scope"] == "repository"
                    else "project_local_only",
                    "privacy_class": PRIVACY_BY_SENSITIVITY[normalized["sensitivity"]],
                    "persistence_scope": IDENTITY_PERSISTENCE_BY_RC_SCOPE[normalized["scope"]],
                    "source_refs": normalized["source_refs"],
                    "limitations": list(_common_limitations()),
                }
            )
        decision = validate_memory_governance_request(
            {
                "request_id": normalized["request_id"],
                "memory_id": normalized["id"],
                "memory_category": _governance_category(normalized["type"]),
                "memory_status": "proposed",
                "memory_scope": GOVERNANCE_SCOPE_BY_RC_SCOPE[normalized["scope"]],
                "operation": "propose_write",
                "identity_scope_ref": f"memory-os-rc1:{normalized['scope']}:{normalized['id']}",
                "project_ref": normalized["project_ref"],
                "repository_ref": normalized["repository_ref"],
                "session_ref": normalized["session_ref"],
                "tenant_ref": "tenant:local",
                "workspace_ref": "workspace:aegis",
                "profile_ref": "profile:local",
                "user_ref": "user:local",
                "namespace": "memory_os_rc1",
                "data_boundary": "local_only",
                "privacy_class": PRIVACY_BY_SENSITIVITY[normalized["sensitivity"]],
                "sensitivity_class": normalized["sensitivity"],
                "retention_policy": RETENTION_BY_SCOPE[normalized["scope"]],
                "source_refs": normalized["source_refs"],
                "provenance": normalized["source_refs"],
                "confidence": 0.5,
                "freshness": "caller_supplied",
                "human_review_required": normalized["human_review_required"],
                "limitations": list(_common_limitations()),
            },
            identity_scope_decision=identity_decision,
        )
        return {
            "status": decision.governance_status,
            "operation_status": decision.operation_status,
            "failure_reasons": list(decision.failure_reasons),
            "source_trust": decision.source_trust,
            "current_memory_candidate": decision.current_memory_candidate,
            "authority": decision.authority,
            "runtime_dispatch_allowed": decision.runtime_dispatch_allowed,
            "execution_permission": decision.execution_permission,
            "evidence_provided_by_memory_governance": decision.evidence_provided_by_memory_governance,
            "verifier_success": decision.verifier_success,
        }


def _missing_result(operation: str, memory_id: str) -> MemoryOperationResult:
    return MemoryOperationResult(
        ok=False,
        operation=operation,
        status="not_found",
        memory_id=memory_id,
        validation_result={"status": "not_found", "failure_reasons": ["unknown_memory_id"]},
        governance_result={"status": "not_applicable_missing_memory"},
        failure_reasons=("unknown_memory_id",),
        limitations=_common_limitations(),
    )


def _item_values(item: MemoryItem) -> tuple[Any, ...]:
    return (
        item.id,
        item.type,
        item.content,
        item.content_summary,
        item.scope,
        item.status,
        item.sensitivity,
        json.dumps([dict(ref) for ref in item.source_refs], sort_keys=True),
        item.project_ref,
        item.repository_ref,
        item.session_ref,
        item.created_at,
        item.updated_at,
        item.deleted_at,
        json.dumps(dict(item.metadata), sort_keys=True),
    )


def _row_to_item(row: sqlite3.Row) -> MemoryItem:
    return MemoryItem(
        id=str(row["id"]),
        type=str(row["type"]),
        content=str(row["content"]),
        content_summary=str(row["content_summary"]),
        scope=str(row["scope"]),
        status=str(row["status"]),
        sensitivity=str(row["sensitivity"]),
        source_refs=tuple(_json_list(row["source_refs_json"])),
        project_ref=row["project_ref"],
        repository_ref=row["repository_ref"],
        session_ref=row["session_ref"],
        created_at=int(row["created_at"]),
        updated_at=int(row["updated_at"]),
        deleted_at=row["deleted_at"],
        metadata=_json_mapping(row["metadata_json"]),
    )


def _json_list(value: str) -> Iterable[Mapping[str, Any]]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return ()
    if isinstance(parsed, list):
        return tuple(item for item in parsed if isinstance(item, Mapping))
    return ()


def _json_mapping(value: str) -> Mapping[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _source_refs(value: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Mapping):
        return (dict(value),)
    if isinstance(value, str) and value.strip():
        return ({"ref_id": value.strip(), "ref_type": "caller_supplied"},)
    if isinstance(value, (list, tuple)):
        refs = []
        for item in value:
            if isinstance(item, Mapping):
                refs.append(dict(item))
            elif isinstance(item, str) and item.strip():
                refs.append({"ref_id": item.strip(), "ref_type": "caller_supplied"})
        return tuple(refs)
    return ()


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _governance_category(value: str) -> str:
    allowed = {
        "user_preference",
        "project_preference",
        "repo_memory",
        "task_session_memory",
        "conversation_summary",
        "temporary_scratch",
    }
    return value if value in allowed else "temporary_scratch"


def _normalize_sensitivity(value: Any) -> str:
    text = _text(value) or "private"
    return text.lower().replace("-", "_")


def _safe_limit(value: int | str | None) -> int:
    try:
        parsed = int(value or 50)
    except (TypeError, ValueError):
        parsed = 50
    return max(1, min(parsed, 500))


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _now() -> int:
    return int(time.time())


def _common_limitations() -> tuple[str, ...]:
    return (
        "memory_os_rc1_core_only",
        "retrieved_memory_is_candidate_only",
        "memory_output_is_not_evidence",
        "memory_retrieval_does_not_grant_execution_permission",
        "no_embeddings_vector_graph_model_mcp_tool_or_cloud_behavior",
    )


def _search_warnings() -> tuple[str, ...]:
    return (
        "memory_search_is_keyword_only",
        "search_results_are_candidates_not_truth_or_authority",
        "sensitive_memories_are_excluded_by_default_unless_explicitly_requested",
    )
