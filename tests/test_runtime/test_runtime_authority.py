from __future__ import annotations

from aegis.core.protocol import RuntimeState
from aegis.core.runtime_authority import RuntimeAuthority


def test_runtime_authority_starts_from_idle_independent_of_journal() -> None:
    authority = RuntimeAuthority(session_id="test-session", queue_capacity=4)
    snapshot = authority.snapshot(journal={"last_sequence_num": 99, "last_event_hash": "old-failed-hash"})

    assert snapshot["session_id"] == "test-session"
    assert snapshot["fsm_state"] == RuntimeState.IDLE.value
    assert snapshot["last_event_sequence"] == 99
    assert snapshot["last_event_hash"] == "old-failed-hash"


def test_runtime_authority_tracks_legal_fsm_transition() -> None:
    authority = RuntimeAuthority(session_id="test-session")

    source, target, legal = authority.transition(RuntimeState.THINKING, from_state=RuntimeState.IDLE)

    assert legal is True
    assert source == RuntimeState.IDLE
    assert target == RuntimeState.THINKING
    assert authority.snapshot()["fsm_state"] == RuntimeState.THINKING.value


def test_runtime_authority_rejects_illegal_transition_without_mutating_state() -> None:
    authority = RuntimeAuthority(session_id="test-session")

    source, target, legal = authority.transition(RuntimeState.EXECUTING, from_state=RuntimeState.IDLE)

    assert legal is False
    assert source == RuntimeState.IDLE
    assert target == RuntimeState.EXECUTING
    assert authority.snapshot()["fsm_state"] == RuntimeState.IDLE.value


def test_runtime_authority_uses_current_state_when_reported_source_is_stale() -> None:
    authority = RuntimeAuthority(session_id="test-session")
    authority.transition(RuntimeState.FAILED, from_state=RuntimeState.IDLE, force=True)

    source, target, legal = authority.transition(RuntimeState.IDLE, from_state=RuntimeState.EXECUTING)

    assert legal is True
    assert source == RuntimeState.FAILED
    assert target == RuntimeState.IDLE
    assert authority.snapshot()["fsm_state"] == RuntimeState.IDLE.value
