from __future__ import annotations

import pytest
from fastapi import HTTPException

from aegis.api import routes_vision
from aegis.core.config import load_settings


@pytest.mark.asyncio
async def test_vision_stream_is_disabled_by_default_before_capture(monkeypatch) -> None:
    monkeypatch.delenv("AEGIS_VISION_FEED", raising=False)
    load_settings(force_reload=True)

    def forbidden_capture() -> bytes:
        raise AssertionError("vision route must not capture frames while disabled")

    monkeypatch.setattr(routes_vision, "_capture_screen_frame", forbidden_capture)

    with pytest.raises(HTTPException) as exc_info:
        await routes_vision.video_feed()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["enabled"] is False
    assert exc_info.value.detail["frames_captured"] is False
    assert exc_info.value.detail["frontend_authority"] is False


@pytest.mark.asyncio
async def test_vision_status_reports_disabled_without_capture(monkeypatch) -> None:
    monkeypatch.delenv("AEGIS_VISION_FEED", raising=False)
    load_settings(force_reload=True)
    monkeypatch.setattr(
        routes_vision,
        "_capture_screen_frame",
        lambda: (_ for _ in ()).throw(AssertionError("status must not capture frames")),
    )

    status = await routes_vision.vision_status()

    assert status["status"] == "disabled"
    assert status["enabled"] is False
    assert status["frames_captured"] is False
    assert status["frontend_authority"] is False
