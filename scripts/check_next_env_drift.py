from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_NEXT_ENV_PATH = Path("frontend/next-env.d.ts")
FORBIDDEN_MARKERS = (
    ".next/dev/types/routes.d.ts",
    ".next/types/routes.d.ts",
    'import "./.next/',
    "import './.next/",
)


def find_next_env_drift(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [marker for marker in FORBIDDEN_MARKERS if marker in content]


def check_next_env(path: Path = DEFAULT_NEXT_ENV_PATH) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, [f"missing file: {path}"]
    return (violations := find_next_env_drift(path)) == [], violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if frontend/next-env.d.ts contains generated Next route imports."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(DEFAULT_NEXT_ENV_PATH),
        help="Path to next-env.d.ts. Defaults to frontend/next-env.d.ts from repo root.",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    ok, violations = check_next_env(path)
    if ok:
        print(f"{path}: safe; no generated .next route imports found.")
        return 0

    print(f"{path}: generated Next env drift detected.")
    for marker in violations:
        print(f"- forbidden marker: {marker}")
    print(
        "Remediation: restore frontend/next-env.d.ts to the canonical two Next reference lines "
        "and the existing NOTE comment. Do not commit generated .next route imports."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
