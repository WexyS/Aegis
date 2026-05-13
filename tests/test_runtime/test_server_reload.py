from pathlib import Path

from aegis.core.config import PROJECT_ROOT, ServerSettings
from aegis.main import get_uvicorn_reload_options


def test_server_reload_defaults_off_for_runtime_stability() -> None:
    assert ServerSettings().reload is False


def test_dev_reload_is_scoped_to_backend_sources() -> None:
    options = get_uvicorn_reload_options(reload=True)

    reload_dirs = {Path(path).resolve() for path in options["reload_dirs"]}
    assert reload_dirs == {
        (PROJECT_ROOT / "src" / "aegis").resolve(),
        (PROJECT_ROOT / "config").resolve(),
    }

    reload_excludes = set(options["reload_excludes"])
    assert "frontend/.next/*" in reload_excludes
    assert "frontend/node_modules/*" in reload_excludes
    assert "logs/*" in reload_excludes
    assert "data/*" in reload_excludes
