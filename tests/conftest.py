"""
AEGIS Test Configuration — Shared fixtures for all tests.
"""

from __future__ import annotations

import pytest

from aegis.core.config import load_settings, AegisSettings


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
