from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_next_env_drift.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_next_env_drift", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_next_env(path: Path, extra: str = "") -> None:
    path.write_text(
        "\n".join(
            [
                '/// <reference types="next" />',
                '/// <reference types="next/image-types/global" />',
                extra,
                "",
                "// NOTE: This file should not be edited",
                "// see https://nextjs.org/docs/app/api-reference/config/typescript for more information.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_safe_file_passes(tmp_path, capsys) -> None:
    checker = _load_checker()
    target = tmp_path / "next-env.d.ts"
    _write_next_env(target)

    assert checker.main([str(target)]) == 0

    captured = capsys.readouterr()
    assert "safe" in captured.out


def test_dev_route_import_fails(tmp_path, capsys) -> None:
    checker = _load_checker()
    target = tmp_path / "next-env.d.ts"
    _write_next_env(target, 'import "./.next/dev/types/routes.d.ts";')

    assert checker.main([str(target)]) == 1

    captured = capsys.readouterr()
    assert ".next/dev/types/routes.d.ts" in captured.out
    assert "Remediation:" in captured.out


def test_build_route_import_fails(tmp_path, capsys) -> None:
    checker = _load_checker()
    target = tmp_path / "next-env.d.ts"
    _write_next_env(target, 'import "./.next/types/routes.d.ts";')

    assert checker.main([str(target)]) == 1

    captured = capsys.readouterr()
    assert ".next/types/routes.d.ts" in captured.out


def test_generic_next_import_fails(tmp_path, capsys) -> None:
    checker = _load_checker()
    target = tmp_path / "next-env.d.ts"
    _write_next_env(target, "import './.next/custom/generated.d.ts';")

    assert checker.main([str(target)]) == 1

    captured = capsys.readouterr()
    assert "import './.next/" in captured.out


def test_checker_does_not_rewrite_target_file(tmp_path) -> None:
    checker = _load_checker()
    target = tmp_path / "next-env.d.ts"
    _write_next_env(target, 'import "./.next/dev/types/routes.d.ts";')
    before = target.read_text(encoding="utf-8")

    assert checker.main([str(target)]) == 1

    assert target.read_text(encoding="utf-8") == before
