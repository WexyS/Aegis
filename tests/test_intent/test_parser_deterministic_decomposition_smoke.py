"""Parser smoke tests for feature-flagged deterministic decomposition."""

from __future__ import annotations

import pytest

from aegis.core.config import load_settings
from aegis.intent.parser import IntentParser


@pytest.fixture(autouse=True)
def reset_deterministic_decomposition(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ENABLE_DETERMINISTIC_DECOMPOSITION", raising=False)
    load_settings(force_reload=True)
    yield
    monkeypatch.delenv("ENABLE_DETERMINISTIC_DECOMPOSITION", raising=False)
    load_settings(force_reload=True)


def _set_flag(monkeypatch: pytest.MonkeyPatch, enabled: bool) -> None:
    monkeypatch.setenv("ENABLE_DETERMINISTIC_DECOMPOSITION", "true" if enabled else "false")
    load_settings(force_reload=True)


def _reload_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_DETERMINISTIC_DECOMPOSITION", raising=False)
    load_settings(force_reload=True)


async def _parse(text: str):
    return await IntentParser().parse(text)


def _assert_no_deterministic_metadata(results) -> None:
    assert all(result.metadata.get("decomposition") != "deterministic" for result in results)


def _assert_ready_metadata(result, *, step_index: int, step_count: int, source_span: str) -> None:
    assert result.metadata["decomposition"] == "deterministic"
    assert result.metadata["plan_status"] == "ready"
    assert result.metadata["step_index"] == step_index
    assert result.metadata["step_count"] == step_count
    assert result.metadata["source_span"] == source_span


def _assert_non_ready_metadata(result, *, plan_status: str) -> None:
    assert result.metadata["decomposition"] == "deterministic"
    assert result.metadata["plan_status"] == plan_status
    assert result.metadata.get("ambiguities") or result.metadata.get("guard_notes")


def _assert_non_executable_unknown(results) -> None:
    executable_intents = {"open_app", "click", "browser_click", "desktop_click"}

    assert [result.intent for result in results] == ["unknown"]
    assert not any(result.intent in executable_intents for result in results)


def test_default_config_enables_deterministic_decomposition(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    assert load_settings().features.deterministic_decomposition is True


@pytest.mark.asyncio
async def test_env_override_false_single_app_commands_keep_legacy_parser_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_flag(monkeypatch, False)

    cases = [
        ("notepad aç", "notepad"),
        ("not defterini aç", "notepad"),
        ("hesap makinesi aç", "calc"),
    ]

    for text, app in cases:
        results = await _parse(text)
        assert [result.intent for result in results] == ["open_app"]
        assert results[0].params["app"] == app
        _assert_no_deterministic_metadata(results)


@pytest.mark.asyncio
async def test_default_on_open_type_notepad_acip_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("notepad açıp merhaba yaz")

    assert [result.intent for result in results] == ["open_app", "type"]
    assert results[0].params["app"] == "notepad"
    assert results[1].params["text"] == "merhaba"
    assert results[1].params["_require_focus"] == "notepad"
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="notepad")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="merhaba")


@pytest.mark.asyncio
async def test_default_on_open_type_not_defteri_ve_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("not defterini aç ve merhaba yaz")

    assert [result.intent for result in results] == ["open_app", "type"]
    assert results[0].params["app"] == "notepad"
    assert results[1].params == {"text": "merhaba", "_require_focus": "notepad"}
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="not defterini")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="merhaba")


@pytest.mark.asyncio
async def test_default_on_open_search_brave_turkish_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("brave açıp python nedir ara")

    assert [result.intent for result in results] == ["open_app", "search_web"]
    assert results[0].params["app"] == "brave"
    assert results[1].params["query"] == "python nedir"
    assert results[1].params["browser"] == "brave"
    assert "brave" not in results[1].params["query"]
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="brave")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="python nedir")


@pytest.mark.asyncio
async def test_default_on_open_search_chrome_turkish_keeps_query_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("chrome aç ve python nedir ara")

    assert [result.intent for result in results] == ["open_app", "search_web"]
    assert results[0].params["app"] == "chrome"
    assert results[1].params["query"] == "python nedir"
    assert results[1].params["query"] != "ve python nedir"
    assert results[1].params["browser"] == "chrome"
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="chrome")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="python nedir")


@pytest.mark.asyncio
async def test_default_on_open_search_brave_english_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("open brave and search python")

    assert [result.intent for result in results] == ["open_app", "search_web"]
    assert results[0].params["app"] == "brave"
    assert results[1].params == {"query": "python", "browser": "brave"}
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="brave")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="python")


@pytest.mark.asyncio
async def test_default_on_unknown_open_type_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("unknownapp aç ve merhaba yaz")

    _assert_non_executable_unknown(results)
    _assert_non_ready_metadata(results[0], plan_status="clarification_required")
    assert results[0].metadata["ambiguities"] == ["unknown app for open+type: unknownapp"]


@pytest.mark.asyncio
async def test_default_on_unknown_open_search_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("unknownapp aç ve python ara")

    _assert_non_executable_unknown(results)
    _assert_non_ready_metadata(results[0], plan_status="clarification_required")
    assert results[0].metadata["ambiguities"] == ["unknown app for open+search: unknownapp"]


@pytest.mark.asyncio
async def test_default_on_ambiguous_compound_click_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("brave aç ve ilk sonuca tıkla")

    _assert_non_executable_unknown(results)
    _assert_non_ready_metadata(results[0], plan_status="clarification_required")
    assert "click target resolution" in results[0].metadata["ambiguities"][0]


@pytest.mark.asyncio
async def test_default_on_generic_click_that_button_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("click that button")

    _assert_non_executable_unknown(results)
    _assert_non_ready_metadata(results[0], plan_status="clarification_required")
    assert "click target resolution" in results[0].metadata["ambiguities"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "click that button",
        "\u015funa t\u0131kla",
        "buna t\u0131kla",
        "brave a\u00e7 ve ilk sonuca t\u0131kla",
        "chrome a\u00e7 ve ilk sonuca t\u0131kla",
    ],
)
async def test_default_on_unresolved_click_examples_never_emit_executable_click_or_partial_open(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    _reload_default(monkeypatch)

    results = await _parse(text)

    _assert_non_executable_unknown(results)
    if results[0].metadata.get("decomposition") == "deterministic":
        _assert_non_ready_metadata(results[0], plan_status="clarification_required")


@pytest.mark.asyncio
async def test_default_on_unrelated_text_falls_back_to_legacy_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    _reload_default(monkeypatch)

    results = await _parse("merhaba")

    assert [result.intent for result in results] == ["general_chat"]
    _assert_no_deterministic_metadata(results)


@pytest.mark.asyncio
async def test_default_on_known_site_open_search_falls_back_to_legacy_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reload_default(monkeypatch)

    cases = [
        ("google aç ve python ara", "https://www.google.com", "python"),
        ("youtube aç ve müzik ara", "https://www.youtube.com", "müzik"),
    ]

    for text, url, query in cases:
        results = await _parse(text)
        assert [result.intent for result in results] == ["open_url", "search_web"]
        assert results[0].params["url"] == url
        assert results[1].params["query"] == query
        _assert_no_deterministic_metadata(results)


@pytest.mark.asyncio
async def test_default_on_legacy_compound_search_tails_still_use_compound_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reload_default(monkeypatch)

    cases = [
        ("brave açıp python nedir araması yap", "python nedir"),
        ("brave açıp python bul", "python"),
        ("brave açıp python googlela", "python"),
    ]

    for text, query in cases:
        results = await _parse(text)
        assert [result.intent for result in results] == ["open_app", "search_web"]
        assert results[0].params["app"] == "brave"
        assert results[1].params == {"query": query, "browser": "brave"}
        assert results[0].metadata["decomposition"] == "compound_app_search"
        assert results[1].metadata["decomposition"] == "compound_app_search"


@pytest.mark.asyncio
async def test_default_on_single_intent_commands_still_use_existing_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reload_default(monkeypatch)

    cases = [
        ("notepad aç", "open_app", {"app": "notepad"}),
        ("not defterini aç", "open_app", {"app": "notepad"}),
        ("hesap makinesi aç", "open_app", {"app": "calc"}),
        ("read README.md", "read_file", {"path": "readme.md"}),
        ("git status", "git_action", {"git_cmd": "status"}),
    ]

    for text, intent, expected_params in cases:
        results = await _parse(text)
        assert [result.intent for result in results] == [intent]
        for key, value in expected_params.items():
            assert results[0].params[key] == value
        _assert_no_deterministic_metadata(results)
