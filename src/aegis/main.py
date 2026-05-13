import sys
import asyncio

# Windows Asyncio Fix for Playwright/Subprocesses
# Must be set before any other imports that might trigger loop creation
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis import __app_name__, __version__
from aegis.core.config import PROJECT_ROOT, get_settings, load_env, load_settings
from aegis.core.commands import restore_approval_manager_from_journal
from aegis.api.ws_bridge import create_socketio_app, start_runtime_workers, stop_runtime_workers


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = load_settings()
    env = load_env()
    logger.info(
        "⚡ Aegis v%s starting — env=%s, safe_mode=%s, dry_run=%s",
        __version__, env.aegis_env, settings.safety.safe_mode, settings.safety.dry_run_default,
    )
    if restore_approval_manager_from_journal():
        logger.info("Restored command lifecycle state from runtime journal.")

    # Start telemetry broadcast loop
    start_runtime_workers()
    logger.info("📡 WebSocket event bridge online.")

    try:
        yield
    finally:
        stop_runtime_workers()

    logger.info("Aegis shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

    fastapi_app = FastAPI(
        title=__app_name__,
        version=__version__,
        description="Deterministic Autonomous Runtime Platform",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @fastapi_app.get("/health", tags=["system"])
    async def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "safe_mode": settings.safety.safe_mode,
            "dry_run": settings.safety.dry_run_default,
        }

    # Command pipeline
    from aegis.api.routes_command import router as command_router
    fastapi_app.include_router(command_router)

    # Vision feed
    from aegis.api.routes_vision import router as vision_router
    fastapi_app.include_router(vision_router)

    # Wrap FastAPI with Socket.IO ASGI middleware
    asgi_app = create_socketio_app(fastapi_app)

    return asgi_app


app = create_app()


def get_uvicorn_reload_options(reload: bool) -> dict[str, object]:
    """Constrain dev reload so generated UI/cache/journal files cannot restart the backend."""
    if not reload:
        return {}

    return {
        "reload_dirs": [
            str(PROJECT_ROOT / "src" / "aegis"),
            str(PROJECT_ROOT / "config"),
        ],
        "reload_excludes": [
            "frontend/*",
            "frontend/.next/*",
            "frontend/node_modules/*",
            "logs/*",
            "data/*",
            "scratch/*",
            ".venv/*",
            ".pytest_cache/*",
            "__pycache__/*",
            "*.pyc",
        ],
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "aegis.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        **get_uvicorn_reload_options(settings.server.reload),
        log_level=settings.logging.level.lower(),
        loop="asyncio" if sys.platform != "win32" else "auto",
    )
