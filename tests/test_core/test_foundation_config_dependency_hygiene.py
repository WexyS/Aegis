from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from aegis.core.config import load_settings
from aegis.core.local_model_inventory import validate_local_model_inventory_request
from aegis.models.llm import LLMProvider


PROJECT_ROOT = Path(__file__).resolve().parents[2]


MODEL_ENV_VARS = [
    "AEGIS_BACKEND",
    "AEGIS_BASE_URL",
    "AEGIS_DEFAULT_MODEL",
    "AEGIS_CHAT_MODEL",
    "AEGIS_CODE_MODEL",
    "AEGIS_EMBED_MODEL",
    "aegis_backend",
    "aegis_base_url",
    "aegis_default_model",
    "aegis_chat_model",
    "aegis_code_model",
    "aegis_embed_model",
]


@pytest.fixture
def default_settings(monkeypatch: pytest.MonkeyPatch):
    for name in MODEL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    safe_model_defaults = {
        "AEGIS_BACKEND": "offline_disabled",
        "AEGIS_BASE_URL": "",
        "AEGIS_DEFAULT_MODEL": "not_configured",
        "AEGIS_CHAT_MODEL": "not_configured",
        "AEGIS_CODE_MODEL": "not_configured",
        "AEGIS_EMBED_MODEL": "not_configured",
    }
    for name, value in safe_model_defaults.items():
        monkeypatch.setenv(name, value)
    return load_settings(force_reload=True)


def test_memory_config_defaults_are_reserved_and_non_authoritative(default_settings) -> None:
    memory = default_settings.memory

    assert memory.governance_status == "not_implemented"
    assert memory.semantic_auto_index is False
    assert memory.procedural_enabled is False
    assert memory.memory_write_authorized is False
    assert memory.memory_retrieval_authorized is False
    assert memory.vector_store_enabled is False
    assert memory.rag_enabled is False
    assert getattr(memory, "evidence_created", False) is False
    assert getattr(memory, "verifier_success", False) is False
    assert getattr(memory, "policy_override", False) is False


def test_model_config_defaults_do_not_authorize_provider_calls(default_settings) -> None:
    models = default_settings.models

    assert models.backend == "offline_disabled"
    assert models.base_url == ""
    assert models.default_model == "not_configured"
    assert models.chat_model == "not_configured"
    assert models.code_model == "not_configured"
    assert models.embed_model == "not_configured"
    assert models.provider_status == "not_configured"
    assert models.provider_health_verified is False
    assert models.model_calls_authorized is False
    assert models.embedding_generation_authorized is False
    assert models.auto_mode_enabled is False


@pytest.mark.asyncio
async def test_llm_provider_generate_denies_http_without_config_authorization(
    monkeypatch: pytest.MonkeyPatch,
    default_settings,
) -> None:
    class ForbiddenAsyncClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("provider URL config must not trigger endpoint probing or model calls")

    monkeypatch.setattr("aegis.models.llm.httpx.AsyncClient", ForbiddenAsyncClient)

    provider = LLMProvider()

    assert await provider.generate("hello", model_type="chat") == ""


@pytest.mark.asyncio
async def test_llm_provider_embed_denies_http_without_embedding_authorization(
    monkeypatch: pytest.MonkeyPatch,
    default_settings,
) -> None:
    class ForbiddenAsyncClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("embedding model config must not trigger endpoint probing")

    monkeypatch.setattr("aegis.models.llm.httpx.AsyncClient", ForbiddenAsyncClient)

    provider = LLMProvider()

    assert await provider.embed("hello") == []


def test_model_vector_dependencies_are_optional_not_runtime_permission() -> None:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]
    optional = data["project"]["optional-dependencies"]

    assert not any(dep.startswith("ollama") for dep in dependencies)
    assert not any(dep.startswith("qdrant-client") for dep in dependencies)
    assert any(dep.startswith("ollama") for dep in optional["model"])
    assert any(dep.startswith("qdrant-client") for dep in optional["vector"])


def test_runtime_code_does_not_import_ollama_or_qdrant_clients_directly() -> None:
    forbidden_imports = (
        "import ollama",
        "from ollama",
        "import qdrant_client",
        "from qdrant_client",
        "import qdrant",
        "from qdrant",
    )

    offenders: list[str] = []
    for path in (PROJECT_ROOT / "src" / "aegis").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(pattern in text for pattern in forbidden_imports):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []


def test_models_yaml_is_metadata_not_provider_health_or_auto_mode() -> None:
    text = (PROJECT_ROOT / "config" / "models.yaml").read_text(encoding="utf-8")

    assert "Future-Gated Model Registry Metadata" in text
    assert "not endpoint health" in text
    assert "not consumed as runtime provider selection" in text
    assert "not live resource verification" in text


def test_local_model_inventory_metadata_still_does_not_authorize_calls() -> None:
    decision = validate_local_model_inventory_request(
        {
            "request_id": "config-hygiene:model-inventory",
            "project_ref": "project:aegis",
            "tenant_scope": "local",
            "namespace": "model_inventory",
            "provider_id": "provider:offline",
            "provider_class": "offline_disabled_provider",
            "provider_status": "disabled_by_policy",
            "privacy_class": "local_only",
            "data_sensitivity_allowed": ["none"],
            "context_policy": {
                "can_receive_secret_like_content": False,
                "can_receive_raw_journal": False,
                "requires_source_refs": True,
                "output_requires_validation": True,
            },
        }
    )

    assert decision.runtime_dispatch_allowed is False
    assert decision.model_call_performed is False
    assert decision.provider_authenticated is False
    assert decision.auto_mode_execution_allowed is False
    assert decision.evidence_provided_by_inventory is False
    assert decision.verifier_success is False
