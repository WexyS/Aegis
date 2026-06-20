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
    assert "previewOperatorRoute" in store
    assert "import { previewOperatorRoute } from '@/lib/api';" in store
    prohibited = (
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
            "no_external_provider_call",
            "no_kimi_moonshot_call",
            "no_image_upload",
            "no_video_upload",
            "no_memory_write",
            "no_tool_call",
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

    assert "previewSourceBackend" in route_preview
    assert "previewSourceFallback" in route_preview
    assert "routePreviewSafetyCopy" in route_preview
    assert "deterministic route metadata" in en
    assert "backend-owned deterministic preview contract" in en
    assert "frontend fallback preview" in en


def test_composer_attachment_is_disabled_and_model_controls_are_preferences() -> None:
    composer = _read("features/operator-shell/components/OperatorComposer.tsx")

    assert "attachmentUnavailable" in composer
    assert "disabled title={t.attachmentUnavailable}" in composer
    assert "modelPreference" in composer
    assert "planningDetail" in composer
    assert 'value="external_provider" disabled' in composer
    assert "Mic" not in composer
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
    assert "backend_contract" in store
    assert "frontend_fallback" in store
    assert "backendPreviewAvailable" in store
    assert "backendPreviewError" in store
    assert re.search(r"cloudNeeded:\s*false", store)
    assert "permissionMode: 'safe_preview'" in store
    assert "'pull request'" in store
    assert "'github pr'" in store
    assert "'pr'," not in store


def test_unified_workspace_uses_response_draft_as_primary_output() -> None:
    shell = _read("features/operator-shell/components/UnifiedOperatorShell.tsx")
    response = _read("features/operator-shell/components/OperatorResponseDraft.tsx")

    assert shell.index("<OperatorResponseDraft />") < shell.index("<OperatorRoutePreview")
    _assert_contains_all(
        response,
        (
            "selectedArtifact.body",
            "navigator.clipboard.writeText",
            "responseDraftSafetyFooter",
            "<article",
        ),
    )


def test_artifact_body_is_copy_ready_and_preview_only() -> None:
    store = _read("store/useOperatorStore.ts")
    artifacts = _read("features/operator-shell/components/OperatorArtifactsPanel.tsx")

    _assert_contains_all(store, ("buildArtifactBody", "body: buildArtifactBody"))
    _assert_contains_all(
        artifacts,
        ("navigator.clipboard.writeText", "selected.body", "<pre", "StatusBadge label={t.previewOnly}"),
    )


def test_primary_navigation_is_workspace_focused_and_legacy_panels_are_secondary() -> None:
    sidebar = _read("features/sidebar/components/Sidebar.tsx")
    drawer = _read("features/operator-shell/components/OperatorWorkspaceDrawer.tsx")

    primary_match = re.search(r"const NAV_ITEMS = \[(.*?)\] as const;", sidebar, re.DOTALL)
    assert primary_match is not None
    primary = primary_match.group(1)
    _assert_contains_all(primary, ("'History'", "'Projects'", "'Outputs'", "'Memory'", "'Customize'", "'Settings'"))
    assert "'Skills'" not in primary
    for legacy in ("labelKey: 'mission'", "labelKey: 'ask'", "labelKey: 'work'", "labelKey: 'capabilities'", "'Advanced'"):
        assert legacy not in primary

    _assert_contains_all(
        drawer,
        ("target: 'History'", "target: 'Projects'", "target: 'Outputs'", "target: 'Memory'", "target: 'Settings'", "target: 'Skills'", "target: 'Advanced'"),
    )


def test_memory_copy_does_not_claim_ten_plus_active_layers() -> None:
    sources = "\n".join(
        (
            _read("i18n/en.ts"),
            _read("i18n/tr.ts"),
            _read("features/operator-shell/components/UnifiedOperatorShell.tsx"),
            _read("features/operator-shell/components/OperatorContextPanel.tsx"),
        )
    ).lower()

    unsupported_claims = (
        "10+ active " + "layer",
        "10+ active " + "layers",
        "10+ aktif " + "katman",
    )
    for unsupported_claim in unsupported_claims:
        assert unsupported_claim not in sources
