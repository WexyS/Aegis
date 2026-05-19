"""Parser smoke tests for feature-flagged deterministic decomposition."""

from __future__ import annotations

import pytest

from aegis.core.config import load_settings
from aegis.intent.parser import IntentParser


@pytest.fixture(autouse=True)
def reset_deterministic_decomposition(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_DETERMINISTIC_DECOMPOSITION", "false")
    load_settings(force_reload=True)
    yield
    monkeypatch.setenv("ENABLE_DETERMINISTIC_DECOMPOSITION", "false")
    load_settings(force_reload=True)


def _set_flag(monkeypatch: pytest.MonkeyPatch, enabled: bool) -> None:
    monkeypatch.setenv("ENABLE_DETERMINISTIC_DECOMPOSITION", "true" if enabled else "false")
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


@pytest.mark.asyncio
async def test_flag_off_single_app_commands_keep_legacy_parser_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
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
async def test_flag_on_open_type_notepad_acip_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("notepad açıp merhaba yaz")

    assert [result.intent for result in results] == ["open_app", "type"]
    assert results[0].params["app"] == "notepad"
    assert results[1].params["text"] == "merhaba"
    assert results[1].params["_require_focus"] == "notepad"
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="notepad")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="merhaba")


@pytest.mark.asyncio
async def test_flag_on_open_type_not_defteri_ve_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("not defterini aç ve merhaba yaz")

    assert [result.intent for result in results] == ["open_app", "type"]
    assert results[0].params["app"] == "notepad"
    assert results[1].params == {"text": "merhaba", "_require_focus": "notepad"}
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="not defterini")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="merhaba")


@pytest.mark.asyncio
async def test_flag_on_open_search_brave_turkish_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("brave açıp python nedir ara")

    assert [result.intent for result in results] == ["open_app", "search_web"]
    assert results[0].params["app"] == "brave"
    assert results[1].params["query"] == "python nedir"
    assert results[1].params["browser"] == "brave"
    assert "brave" not in results[1].params["query"]
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="brave")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="python nedir")


@pytest.mark.asyncio
async def test_flag_on_open_search_brave_english_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("open brave and search python tutorial")

    assert [result.intent for result in results] == ["open_app", "search_web"]
    assert results[0].params["app"] == "brave"
    assert results[1].params == {"query": "python tutorial", "browser": "brave"}
    _assert_ready_metadata(results[0], step_index=0, step_count=2, source_span="brave")
    _assert_ready_metadata(results[1], step_index=1, step_count=2, source_span="python tutorial")


@pytest.mark.asyncio
async def test_flag_on_unknown_open_type_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("unknownapp aç ve merhaba yaz")

    assert [result.intent for result in results] == ["unknown"]
    assert results[0].metadata["decomposition"] == "deterministic"
    assert results[0].metadata["plan_status"] == "clarification_required"
    assert results[0].metadata["ambiguities"] == ["unknown app for open+type: unknownapp"]


@pytest.mark.asyncio
async def test_flag_on_ambiguous_compound_click_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("brave aç ve ilk sonuca tıkla")

    assert [result.intent for result in results] == ["unknown"]
    assert results[0].metadata["decomposition"] == "deterministic"
    assert results[0].metadata["plan_status"] == "clarification_required"
    assert "click target resolution" in results[0].metadata["ambiguities"][0]


@pytest.mark.asyncio
async def test_flag_on_generic_click_that_button_is_non_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("click that button")

    assert [result.intent for result in results] == ["unknown"]
    assert results[0].metadata["decomposition"] == "deterministic"
    assert results[0].metadata["plan_status"] == "clarification_required"
    assert "click target resolution" in results[0].metadata["ambiguities"][0]


@pytest.mark.asyncio
async def test_flag_on_unrelated_text_falls_back_to_legacy_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_flag(monkeypatch, True)

    results = await _parse("merhaba")

    assert [result.intent for result in results] == ["general_chat"]
    _assert_no_deterministic_metadata(results)
