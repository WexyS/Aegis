"""
AEGIS Test Configuration — Shared fixtures for all tests.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_SESSION_RUNTIME_ROOT = Path(tempfile.mkdtemp(prefix="aegis-pytest-runtime-"))
os.environ.setdefault("AEGIS_ENV", "test")
os.environ.setdefault("AEGIS_LOG_DIR", str(_SESSION_RUNTIME_ROOT / "logs"))
os.environ.setdefault("AEGIS_TEST_RUNTIME_ROOT", str(_SESSION_RUNTIME_ROOT))
os.environ.setdefault("AEGIS_UNDER_PYTEST", "1")

import pytest

from aegis.core.config import load_settings, AegisSettings
from aegis.core.commands import get_approval_manager
from aegis.core.event_journal import reset_runtime_journal_for_tests
from aegis.core.protocol import reset_sequence_for_testing


@pytest.fixture(autouse=True)
def isolate_runtime_state(tmp_path, monkeypatch):
    """Keep tests from reading or writing the operator's live runtime journal."""

    runtime_root = tmp_path / "aegis-test-runtime"
    log_dir = runtime_root / "logs"
    monkeypatch.setenv("AEGIS_ENV", "test")
    monkeypatch.setenv("AEGIS_LOG_DIR", str(log_dir))
    monkeypatch.setenv("AEGIS_TEST_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.delenv("AEGIS_ALLOW_LIVE_JOURNAL_IN_PYTEST", raising=False)
    load_settings(force_reload=True)
    reset_runtime_journal_for_tests()
    reset_sequence_for_testing()
    get_approval_manager().reset_for_tests()
    yield
    get_approval_manager().reset_for_tests()
    reset_runtime_journal_for_tests()
    reset_sequence_for_testing()


@pytest.fixture
def settings() -> AegisSettings:
    """Provide test settings."""
    return load_settings(force_reload=True)


@pytest.fixture
def sample_command_text() -> str:
    """A simple test command."""
    return "Open https://github.com"


@pytest.fixture
def sample_unknown_command() -> str:
    """An ambiguous command that should map to 'unknown'."""
    return "xyzzy foobar baz"
