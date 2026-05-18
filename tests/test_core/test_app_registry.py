from __future__ import annotations

import json

from aegis.core.app_map import (
    AppDiscoveryRoots,
    discover_installed_apps,
    get_app_config,
    refresh_installed_app_registry,
    resolve_app_name,
)


def test_discovers_start_menu_shortcuts_as_launch_targets(tmp_path) -> None:
    start_menu = tmp_path / "Start Menu"
    start_menu.mkdir()
    shortcut = start_menu / "Epic Games Launcher.lnk"
    shortcut.write_text("shortcut-placeholder", encoding="utf-8")

    discovered = discover_installed_apps(AppDiscoveryRoots(start_menu_dirs=[start_menu]))

    assert discovered["epic games launcher"]["path"] == str(shortcut)
    assert discovered["epic games launcher"]["source"] == "start_menu"
    assert discovered["epic games launcher"]["aliases"] == ["epic games launcher"]
    assert discovered["epic games launcher"]["window_keywords"] == ["Epic Games Launcher"]


def test_discovers_program_files_executables_with_process_name(tmp_path) -> None:
    program_root = tmp_path / "Program Files"
    steam_dir = program_root / "Steam"
    steam_dir.mkdir(parents=True)
    steam_exe = steam_dir / "steam.exe"
    steam_exe.write_text("", encoding="utf-8")

    discovered = discover_installed_apps(AppDiscoveryRoots(program_dirs=[program_root]))

    assert discovered["steam"]["path"] == str(steam_exe)
    assert discovered["steam"]["process_name"] == "steam.exe"
    assert discovered["steam"]["source"] == "program_files"


def test_discovers_steam_games_from_appmanifest(tmp_path) -> None:
    steam = tmp_path / "Steam"
    steamapps = steam / "steamapps"
    steamapps.mkdir(parents=True)
    (steamapps / "appmanifest_730.acf").write_text(
        '"AppState"\n{\n    "appid" "730"\n    "name" "Counter-Strike 2"\n}',
        encoding="utf-8",
    )

    discovered = discover_installed_apps(AppDiscoveryRoots(steam_dirs=[steam]))

    assert discovered["counter strike 2"]["path"] == "steam://rungameid/730"
    assert discovered["counter strike 2"]["source"] == "steam"
    assert "counter-strike 2" in discovered["counter strike 2"]["aliases"]


def test_discovers_epic_games_from_manifests(tmp_path) -> None:
    manifest_dir = tmp_path / "EpicManifests"
    install_dir = tmp_path / "Fortnite"
    manifest_dir.mkdir()
    install_dir.mkdir()
    executable = install_dir / "FortniteLauncher.exe"
    executable.write_text("", encoding="utf-8")
    (manifest_dir / "Fortnite.item").write_text(
        json.dumps({
            "DisplayName": "Fortnite",
            "InstallLocation": str(install_dir),
            "LaunchExecutable": "FortniteLauncher.exe",
            "AppName": "FortniteLive",
        }),
        encoding="utf-8",
    )

    discovered = discover_installed_apps(AppDiscoveryRoots(epic_manifest_dirs=[manifest_dir]))

    assert discovered["fortnite"]["path"] == str(executable)
    assert discovered["fortnite"]["process_name"] == "FortniteLauncher.exe"
    assert discovered["fortnite"]["source"] == "epic"


def test_refresh_registry_makes_discovered_apps_resolvable(tmp_path) -> None:
    start_menu = tmp_path / "Start Menu"
    start_menu.mkdir()
    (start_menu / "Steam.lnk").write_text("shortcut-placeholder", encoding="utf-8")

    refresh_installed_app_registry(AppDiscoveryRoots(start_menu_dirs=[start_menu]))

    assert resolve_app_name("steam") == "steam"
    assert get_app_config("steam")["path"].endswith("Steam.lnk")


def test_brave_is_configured_as_a_verified_browser_target() -> None:
    assert resolve_app_name("brave") == "brave"
    config = get_app_config("brave")
    assert config["process_name"] == "brave.exe"
    assert "Brave" in config["window_keywords"]
    assert config["fallback"] == "chrome"
