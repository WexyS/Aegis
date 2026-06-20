from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend" / "src"


def _read(path: str) -> str:
    return (FRONTEND / path).read_text(encoding="utf-8")


def test_primary_navigation_is_exact_and_legacy_dashboard_is_secondary() -> None:
    sidebar = _read("features/sidebar/components/Sidebar.tsx")
    primary = re.search(r"const NAV_ITEMS = \[(.*?)\] as const;", sidebar, re.DOTALL)
    assert primary is not None
    primary_source = primary.group(1)

    assert [item for item in ("History", "Projects", "Outputs", "Memory", "Customize", "Settings") if f"id: '{item}'" in primary_source] == [
        "History",
        "Projects",
        "Outputs",
        "Memory",
        "Customize",
        "Settings",
    ]
    for legacy in ("Mission", "Ask", "Work", "Capabilities", "Skills", "Advanced"):
        assert f"id: '{legacy}'" not in primary_source
    assert "startNewTask();" in sidebar
    assert "setActiveTab('Advanced')" in sidebar


def test_page_wires_real_workspace_surfaces_without_fake_registry_data() -> None:
    page = _read("app/page.tsx")
    projects = _read("features/workspace/components/ProjectsSurface.tsx")
    en = _read("i18n/en.ts")

    for route in ("History", "Projects", "Outputs", "Memory", "Customize", "Settings"):
        assert f"activeTab === '{route}'" in page
    assert "No saved projects" in en
    assert "Project persistence is not implemented" in en
    assert "openPrompt" in projects
    assert "fetch(" not in projects


def test_history_and_outputs_are_current_session_only() -> None:
    store = _read("store/useOperatorStore.ts")
    history = _read("features/workspace/components/HistorySurface.tsx")
    outputs = _read("features/workspace/components/OutputsSurface.tsx")
    en = _read("i18n/en.ts")

    assert "sessionHistory" in store
    assert "localStorage" not in store
    assert "sessionHistory" in history
    assert "artifacts" in outputs
    assert "Current browser session only" in en
    assert "Session-only frontend drafts" in en
    for source in (history, outputs):
        assert "fetch(" not in source


def test_context_is_closed_by_default_and_metadata_stays_secondary() -> None:
    ui_store = _read("store/useUIStore.ts")
    shell = _read("features/operator-shell/components/UnifiedOperatorShell.tsx")
    route = _read("features/operator-shell/components/OperatorRoutePreview.tsx")

    assert "isInspectorOpen: false" in ui_store
    assert "event.key === 'Escape'" in shell
    assert "{isInspectorOpen && (" in shell
    assert shell.index("<OperatorResponseDraft />") < shell.index("<OperatorRoutePreview")
    assert "<details" in route
    assert "<details open" not in route


def test_model_and_planning_controls_cannot_claim_or_perform_selection() -> None:
    composer = _read("features/operator-shell/components/OperatorComposer.tsx")
    store = _read("store/useOperatorStore.ts")

    for value in ("auto", "fast_summary", "balanced_draft", "code_review", "reasoning_plan", "vision_review"):
        assert f'value="{value}"' in composer
    assert 'value="external_provider" disabled' in composer
    assert "setModelPreference" in store
    assert "setPlanningDetail" in store
    for prohibited in ("completeWithModelGateway", "probeModelGateway", "fetch(", "WebSocket", "hidden reasoning"):
        assert prohibited not in composer


def test_new_operator_workspace_avoids_unsupported_product_claims() -> None:
    sources = "\n".join(
        _read(path)
        for path in (
            "features/operator-shell/components/UnifiedOperatorShell.tsx",
            "features/operator-shell/components/OperatorComposer.tsx",
            "features/operator-shell/components/OperatorResponseDraft.tsx",
            "features/workspace/components/HistorySurface.tsx",
            "features/workspace/components/ProjectsSurface.tsx",
            "features/workspace/components/OutputsSurface.tsx",
            "features/workspace/components/CustomizeSurface.tsx",
        )
    ).lower()

    for unsupported in ("mission control", "aegis os", "telemetry", "fake logs", "10+ active layer", "10+ active layers"):
        assert unsupported not in sources
    assert ">execute<" not in sources
    assert ">deploy<" not in sources


def test_operator_workspace_has_responsive_overflow_and_touch_contracts() -> None:
    shell = _read("features/operator-shell/components/UnifiedOperatorShell.tsx")
    sidebar = _read("features/sidebar/components/Sidebar.tsx")
    composer = _read("features/operator-shell/components/OperatorComposer.tsx")

    assert "min-w-0" in shell
    assert "overflow-y-auto" in shell
    assert "w-14" in sidebar and "lg:w-60" in sidebar
    assert "h-10" in composer
    assert "sm:grid-cols-2" in _read("features/operator-shell/components/OperatorQuickActions.tsx")
