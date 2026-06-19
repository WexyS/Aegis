from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend" / "src"


def _read(path: str) -> str:
    return (FRONTEND / path).read_text(encoding="utf-8")


def _assert_contains_all(source: str, expected: tuple[str, ...]) -> None:
    missing = [item for item in expected if item not in source]
    assert not missing, missing


def test_operator_store_false_safety_flags_are_all_defined() -> None:
    store = _read("store/useOperatorStore.ts")

    _assert_contains_all(
        store,
        (
            "commandExecutionPerformed: false",
            "modelCallPerformed: false",
            "cloudCallPerformed: false",
            "imageUploadPerformed: false",
            "memoryWritePerformed: false",
            "evidenceCreated: false",
            "verifierSuccessCreated: false",
            "approvalGranted: false",
            "permissionGranted: false",
            "backendAuthority: false",
        ),
    )


def test_operator_store_does_not_import_or_call_execution_surfaces() -> None:
    store = _read("store/useOperatorStore.ts")
    prohibited = (
        "@/lib/api",
        "sendCommand",
        "askAegis",
        "previewExternalProviderBroker",
        "fetch(",
        "WebSocket",
        "socket.",
        "modelGateway",
        "probeModelGateway",
        "completeWithModelGateway",
        "writeMemory(",
        "proposeMemory(",
        "approveMemory(",
        "deleteMemory(",
        "grantApproval(",
    )

    for token in prohibited:
        assert token not in store, token


def test_operator_artifacts_and_trace_remain_preview_only() -> None:
    store = _read("store/useOperatorStore.ts")
    artifacts = _read("features/operator-shell/components/OperatorArtifactsPanel.tsx")
    process = _read("features/operator-shell/components/OperatorProcessPanel.tsx")

    _assert_contains_all(
        store,
        (
            "status: 'preview-only'",
            "no_command_execution",
            "no_model_call",
            "no_cloud_call",
            "no_image_upload",
            "no_memory_write",
            "no_evidence",
            "no_verifier_success",
            "no_approval_or_permission_grant",
            "blocked_actions_not_performed",
        ),
    )
    assert "StatusBadge label={t.previewOnly}" in artifacts
    assert "artifactSummary" in artifacts
    assert "processTraceSafetyCopy" in process
    assert "traceNoActionsDetail" in process


def test_operator_copy_uses_summarized_metadata_not_hidden_reasoning() -> None:
    en = _read("i18n/en.ts")
    process = _read("features/operator-shell/components/OperatorProcessPanel.tsx")

    assert "Summarized operational metadata, not hidden reasoning." in en
    assert "No command, model, memory, cloud, evidence, verifier, or approval action was performed" in en
    assert "processTraceCopy" in process
    assert "processTraceSafetyCopy" in process


def test_route_preview_is_deterministic_preview_metadata() -> None:
    route_preview = _read("features/operator-shell/components/OperatorRoutePreview.tsx")
    en = _read("i18n/en.ts")

    assert "deterministicPreview" in route_preview
    assert "routePreviewSafetyCopy" in route_preview
    assert "deterministic frontend UX metadata" in en
    assert "not model intelligence" in en
    assert "not backend authority" in en


def test_composer_attachment_and_voice_are_placeholders_not_uploads() -> None:
    composer = _read("features/operator-shell/components/OperatorComposer.tsx")

    assert "PlaceholderButton" in composer
    assert "attachmentPlaceholder" in composer
    assert "microphonePlaceholder" in composer
    assert 'type="file"' not in composer
    assert "upload" not in composer.lower()
    assert "FormData" not in composer
    assert "fetch(" not in composer


def test_operator_routing_keywords_cover_expected_cases() -> None:
    store = _read("store/useOperatorStore.ts")

    keyword_groups = {
        "vision_ui_screenshot": (
            "screenshot",
            "image",
            "vision",
            "ui sorunu",
            "ui issue",
            "arayuz",
        ),
        "codex_code_repo_test_diff": (
            "codex prompt",
            "code",
            "diff",
            "test",
            "repo",
            "patch",
        ),
        "memory_remember_forget": (
            "memory",
            "remember",
            "forget",
            "hafiza",
        ),
        "web_research_source": (
            "web",
            "internet",
            "source",
            "research",
        ),
        "model_provider_names": (
            "model",
            "lm studio",
            "qwen",
            "gemma",
            "deepseek",
            "openrouter",
            "moonshot",
            "kimi",
        ),
        "command_execute_shell_run": (
            "komut",
            "execute",
            "shell",
            "terminal",
            "run ",
        ),
        "approval_permission": (
            "onay",
            "approval",
            "approve",
            "permission",
            "izin",
        ),
    }

    for group, keywords in keyword_groups.items():
        missing = [keyword for keyword in keywords if keyword not in store]
        assert not missing, f"{group}: {missing}"


def test_store_keeps_deterministic_preview_builder_frontend_local() -> None:
    store = _read("store/useOperatorStore.ts")

    assert "buildDecisionPreview" in store
    assert "classifyOperatorIntents" in store
    assert "chooseRouteId" in store
    assert "stablePreviewId" in store
    assert re.search(r"cloudNeeded:\s*false", store)
    assert "permissionMode: 'safe_preview'" in store
