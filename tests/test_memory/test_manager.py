from __future__ import annotations

from aegis.memory.store import MemoryStore


def _store(tmp_path):
    return MemoryStore(tmp_path / "memory.sqlite3")


def _session_payload(**overrides):
    payload = {
        "type": "task_session_memory",
        "content": "Prefer concise Aegis sprint reports with validation output.",
        "summary": "Report format preference",
        "scope": "session",
        "session_ref": "session:test",
        "sensitivity": "private",
        "source_refs": [{"ref_id": "test", "ref_type": "unit"}],
    }
    payload.update(overrides)
    return payload


def test_propose_valid_memory_creates_proposed_item(tmp_path):
    result = _store(tmp_path).propose(_session_payload())

    assert result.ok is True
    assert result.status == "proposed"
    assert result.memory is not None
    assert result.memory.status == "proposed"
    assert result.governance_result["status"] == "proposal_ready"
    payload = result.to_dict()
    assert payload["authority"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["retrieved_memory_is_truth"] is False
    assert payload["evidence_provided_by_memory"] is False


def test_approve_proposed_memory_activates_it(tmp_path):
    store = _store(tmp_path)
    proposed = store.propose(_session_payload())

    approved = store.approve(proposed.memory_id or "")

    assert approved.ok is True
    assert approved.status == "active"
    assert approved.memory is not None
    assert approved.memory.status == "active"
    assert approved.governance_result["status"] == "not_applicable_lifecycle_transition"


def test_reject_proposed_memory_rejects_it(tmp_path):
    store = _store(tmp_path)
    proposed = store.propose(_session_payload(content="Temporary note to reject."))

    rejected = store.reject(proposed.memory_id or "", reason="not useful")

    assert rejected.ok is True
    assert rejected.status == "rejected"
    assert rejected.memory is not None
    assert rejected.memory.metadata["rejection_reason"] == "not useful"


def test_delete_active_memory_soft_deletes_it_and_excludes_by_default(tmp_path):
    store = _store(tmp_path)
    proposed = store.propose(_session_payload(content="Delete me later."))
    approved = store.approve(proposed.memory_id or "")

    deleted = store.delete(approved.memory_id or "")
    listed = store.list_memories()
    listed_with_deleted = store.list_memories(include_deleted=True)

    assert deleted.ok is True
    assert deleted.status == "deleted"
    assert listed.memories == ()
    assert [item.status for item in listed_with_deleted.memories] == ["deleted"]


def test_invalid_transition_is_blocked(tmp_path):
    store = _store(tmp_path)
    proposed = store.propose(_session_payload(content="Approve once only."))
    store.approve(proposed.memory_id or "")

    second_approve = store.approve(proposed.memory_id or "")

    assert second_approve.ok is False
    assert second_approve.status == "blocked_by_invalid_transition"
    assert "approve_requires_proposed_memory" in second_approve.failure_reasons


def test_secret_like_memory_is_blocked_by_validation_before_storage(tmp_path):
    store = _store(tmp_path)

    result = store.propose(_session_payload(sensitivity="secret-like", content="API key is abc"))

    assert result.ok is False
    assert result.status == "blocked_by_validation"
    assert "blocked_sensitive_memory" in result.failure_reasons
    assert store.list_memories(include_deleted=True).memories == ()


def test_missing_project_ref_blocks_project_memory(tmp_path):
    result = _store(tmp_path).propose(
        _session_payload(
            scope="project",
            session_ref=None,
            content="Project scoped memory without project ref.",
        )
    )

    assert result.ok is False
    assert result.status == "blocked_by_validation"
    assert "missing_project_ref" in result.failure_reasons


def test_project_memory_uses_identity_and_governance(tmp_path):
    result = _store(tmp_path).propose(
        _session_payload(
            type="project_preference",
            scope="project",
            session_ref=None,
            project_ref="project:aegis",
            content="Project reports must include line statistics.",
        )
    )

    assert result.ok is True
    assert result.memory is not None
    assert result.memory.scope == "project"
    assert result.governance_result["status"] == "proposal_ready"


def test_repository_memory_requires_repository_ref(tmp_path):
    result = _store(tmp_path).propose(
        _session_payload(
            type="repo_memory",
            scope="repository",
            session_ref=None,
            project_ref="project:aegis",
            content="Repo scoped memory missing repository ref.",
        )
    )

    assert result.ok is False
    assert "missing_repository_ref" in result.failure_reasons


def test_search_active_memories_by_keyword_and_scope(tmp_path):
    store = _store(tmp_path)
    sprint = store.propose(_session_payload(content="Mission Control uses backend truth."))
    other = store.propose(
        _session_payload(
            content="Unrelated note about terminal output.",
            session_ref="session:other",
        )
    )
    store.approve(sprint.memory_id or "")
    store.approve(other.memory_id or "")

    result = store.search(keyword="Mission", scope="session", session_ref="session:test")

    assert result.ok is True
    assert [item.content for item in result.memories] == ["Mission Control uses backend truth."]
    assert result.to_dict()["memory_retrieval_is_authority"] is False


def test_search_excludes_sensitive_by_default(tmp_path):
    store = _store(tmp_path)
    normal = store.propose(_session_payload(content="Visible active note.", sensitivity="private"))
    sensitive = store.propose(
        _session_payload(
            content="Sensitive active note.",
            sensitivity="sensitive",
            human_review_required=True,
        )
    )
    store.approve(normal.memory_id or "")
    store.approve(sensitive.memory_id or "")

    default_result = store.search(keyword="active")
    explicit_result = store.search(keyword="active", include_sensitive=True)

    assert [item.content for item in default_result.memories] == ["Visible active note."]
    assert {item.content for item in explicit_result.memories} == {
        "Visible active note.",
        "Sensitive active note.",
    }
