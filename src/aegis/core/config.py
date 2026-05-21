"""
AEGIS Core Config — Settings loader.

Loads configuration from YAML files and environment variables.
Provides typed, validated access to all settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from aegis.core.errors import ConfigurationError


# ---------------------------------------------------------------------------
# Locate project root and config directory
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Fallback: assume 3 levels up from core/config.py → src/aegis/core/
    return Path(__file__).resolve().parent.parent.parent.parent


PROJECT_ROOT = _find_project_root()
CONFIG_DIR = PROJECT_ROOT / "config"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigurationError(f"Config file must contain a YAML mapping: {path}")
        return data
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Typed settings models
# ---------------------------------------------------------------------------

class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8400
    workers: int = 1
    reload: bool = False


class SafetySettings(BaseModel):
    safe_mode: bool = True
    dry_run_default: bool = True
    require_approval_high_risk: bool = True
    max_actions_per_command: int = 10
    max_plan_depth: int = 5
    cooldown_seconds: float = 1.0


class LoggingSettings(BaseModel):
    level: str = "DEBUG"
    format: str = "jsonl"
    directory: str = "./logs"
    max_file_size_mb: int = 50
    retention_days: int = 30


class MemorySettings(BaseModel):
    stm_max_turns: int = 20
    episodic_retention_days: int = 90
    semantic_auto_index: bool = True
    procedural_enabled: bool = True


class ModelSettings(BaseModel):
    backend: str = "ollama"
    base_url: str = "http://localhost:11434"
    timeout: float = 120.0
    default_model: str = "qwen3:8b"
    chat_model: str = "qwen3:8b"
    code_model: str = "qwen2.5-coder:14b"
    embed_model: str = "nomic-embed-text"
    
    # Recovery Budget (Reliability Science)
    max_recovery_depth: int = 3
    max_vision_attempts: int = 2
    max_replans: int = 2


class FeatureFlags(BaseModel):
    cloud_fallback: bool = False
    multimodal: bool = False
    speech_io: bool = False
    agent_loop: bool = False
    deterministic_decomposition: bool = False
    replay_enabled: bool = True


class AegisSettings(BaseModel):
    """Aggregated settings from config/settings.yaml + environment."""

    server: ServerSettings = Field(default_factory=ServerSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    env: str = "development"
    debug: bool = True


# ---------------------------------------------------------------------------
# Environment overrides
# ---------------------------------------------------------------------------

class EnvOverrides(BaseSettings):
    """Environment variable overrides (from .env or OS env)."""

    aegis_host: str = "127.0.0.1"
    aegis_port: int = 8400
    aegis_env: str = "development"
    aegis_debug: bool = True
    aegis_safe_mode: bool = True
    aegis_dry_run: bool = True
    aegis_require_approval_high_risk: bool = True
    aegis_log_level: str = "DEBUG"
    aegis_log_dir: str = "./logs"
    aegis_backend: str = "ollama"
    aegis_base_url: str = "http://localhost:11434"
    aegis_model_timeout: float = 120.0
    aegis_default_model: str = "qwen3:8b"
    aegis_chat_model: str = "qwen3:8b"
    aegis_code_model: str = "qwen2.5-coder:14b"
    aegis_embed_model: str = "nomic-embed-text"
    aegis_cloud_enabled: bool = False
    enable_deterministic_decomposition: bool | None = Field(
        None,
        validation_alias="ENABLE_DETERMINISTIC_DECOMPOSITION",
    )
    
    # Recovery Budget
    aegis_max_recovery_depth: int = 3
    aegis_max_vision_attempts: int = 2
    aegis_max_replans: int = 2

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# ---------------------------------------------------------------------------
# Global settings loader (singleton-ish)
# ---------------------------------------------------------------------------

_settings: AegisSettings | None = None
_env: EnvOverrides | None = None


def load_settings(force_reload: bool = False) -> AegisSettings:
    """Load settings from config/settings.yaml and apply .env overrides."""
    global _settings
    if _settings is not None and not force_reload:
        return _settings

    yaml_data = load_yaml(CONFIG_DIR / "settings.yaml")
    _settings = AegisSettings(**yaml_data)

    # Apply environment overrides
    env_overrides = load_env(force_reload=force_reload)
    
    _settings.env = env_overrides.aegis_env
    _settings.debug = env_overrides.aegis_debug
    
    # Server
    _settings.server.host = env_overrides.aegis_host
    _settings.server.port = env_overrides.aegis_port
    
    # Safety
    _settings.safety.safe_mode = env_overrides.aegis_safe_mode
    _settings.safety.dry_run_default = env_overrides.aegis_dry_run
    _settings.safety.require_approval_high_risk = env_overrides.aegis_require_approval_high_risk
    
    # Logging
    _settings.logging.level = env_overrides.aegis_log_level
    _settings.logging.directory = env_overrides.aegis_log_dir
    
    # Models
    _settings.models.backend = env_overrides.aegis_backend
    _settings.models.base_url = env_overrides.aegis_base_url
    _settings.models.timeout = env_overrides.aegis_model_timeout
    _settings.models.default_model = env_overrides.aegis_default_model
    _settings.models.chat_model = env_overrides.aegis_chat_model
    _settings.models.code_model = env_overrides.aegis_code_model
    _settings.models.embed_model = env_overrides.aegis_embed_model
    _settings.models.max_recovery_depth = env_overrides.aegis_max_recovery_depth
    _settings.models.max_vision_attempts = env_overrides.aegis_max_vision_attempts
    _settings.models.max_replans = env_overrides.aegis_max_replans
    
    # Features
    if env_overrides.aegis_cloud_enabled:
        _settings.features.cloud_fallback = True
    if env_overrides.enable_deterministic_decomposition is not None:
        _settings.features.deterministic_decomposition = env_overrides.enable_deterministic_decomposition

    return _settings


def load_env(force_reload: bool = False) -> EnvOverrides:
    """Load and cache environment variable overrides."""
    global _env
    if _env is not None and not force_reload:
        return _env

    _env = EnvOverrides()
    return _env


def get_settings() -> AegisSettings:
    """Get cached settings, loading if necessary."""
    return load_settings()


def get_env() -> EnvOverrides:
    """Get cached env overrides, loading if necessary."""
    return load_env()
