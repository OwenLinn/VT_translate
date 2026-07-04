from __future__ import annotations

import json
from pathlib import Path

import pytest

from yt_live_translator.ui.electron_overlay_app import (
    electron_overlay_command,
    electron_overlay_root,
)


ROOT = Path(__file__).resolve().parents[1]
ELECTRON_ROOT = ROOT / "frontend" / "electron-overlay"


def test_electron_overlay_root_and_scripts_exist() -> None:
    assert electron_overlay_root() == ELECTRON_ROOT
    package_json = ELECTRON_ROOT / "package.json"
    assert package_json.exists()

    package = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = package["scripts"]
    assert scripts["dev:mock"] == "cross-env OVERLAY_MODE=mock electron-vite dev"
    assert scripts["dev:tuning"] == "cross-env OVERLAY_MODE=tuning electron-vite dev"
    assert "OVERLAY_BRIDGE_MODE=live" in scripts["dev:live"]
    assert "OVERLAY_BRIDGE_URL=ws://127.0.0.1:8765" in scripts["dev:live"]
    assert scripts["typecheck"] == "tsc --noEmit"
    assert package["devDependencies"]["electron-vite"] == "^2.3.0"
    assert package["devDependencies"]["vite"] == "^5.4.0"


@pytest.mark.parametrize(
    ("mode", "command"),
    [
        ("mock", ["npm", "run", "dev:mock"]),
        ("tuning", ["npm", "run", "dev:tuning"]),
        ("live", ["npm", "run", "dev:live"]),
    ],
)
def test_electron_overlay_command(mode: str, command: list[str]) -> None:
    assert electron_overlay_command(mode) == command


def test_electron_overlay_command_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError):
        electron_overlay_command("pipeline")


def test_electron_main_window_uses_secure_renderer_options() -> None:
    window_source = (ELECTRON_ROOT / "src" / "main" / "window.ts").read_text(encoding="utf-8")
    assert "transparent: true" in window_source
    assert "alwaysOnTop: true" in window_source
    assert "nodeIntegration: false" in window_source
    assert "contextIsolation: true" in window_source
    assert "sandbox: true" in window_source
    assert "preload:" in window_source


def test_electron_multi_window_structure_exists() -> None:
    windows = ELECTRON_ROOT / "src" / "main" / "windows"
    expected = {
        "overlayWindowManager.ts",
        "createOverlayWindow.ts",
        "subtitleWindow.ts",
        "settingsIconWindow.ts",
        "controlCardWindow.ts",
        "popoverWindow.ts",
        "windowGeometry.ts",
    }
    assert expected.issubset({path.name for path in windows.iterdir()})


def test_electron_multi_window_is_default_with_single_legacy_fallback() -> None:
    main_source = (ELECTRON_ROOT / "src" / "main" / "main.ts").read_text(encoding="utf-8")
    assert 'OVERLAY_WINDOW_MODE === "single_legacy"' in main_source
    assert "OVERLAY_BRIDGE_MODE" in main_source
    assert "createBackendBridgeClient" in main_source
    assert 'OverlayWindowManager' in main_source
    assert 'createOverlayWindow(overlayMode)' in main_source


def test_electron_multi_windows_use_secure_renderer_options() -> None:
    source = (
        ELECTRON_ROOT / "src" / "main" / "windows" / "createOverlayWindow.ts"
    ).read_text(encoding="utf-8")
    assert "transparent: true" in source
    assert "frame: false" in source
    assert "alwaysOnTop: true" in source
    assert "skipTaskbar: true" in source
    assert "nodeIntegration: false" in source
    assert "contextIsolation: true" in source
    assert "sandbox: true" in source
    assert "window:" in source


def test_electron_multi_window_geometry_avoids_bottom_clipping() -> None:
    geometry = (
        ELECTRON_ROOT / "src" / "main" / "windows" / "windowGeometry.ts"
    ).read_text(encoding="utf-8")
    manager = (
        ELECTRON_ROOT / "src" / "main" / "windows" / "overlayWindowManager.ts"
    ).read_text(encoding="utf-8")
    layout_css = (ELECTRON_ROOT / "src" / "renderer" / "styles" / "layout.css").read_text(
        encoding="utf-8"
    )

    assert "anchorMenuY" in geometry
    assert "fitHeight" in geometry
    assert "popoverHeightFor" in geometry
    assert 'activePopover === "language"' in geometry
    assert "activePopoverRowOffset" in manager
    assert "this.relayout(this.state.activePopover, bounds)" in manager
    assert "overflow-y: auto" in layout_css


def test_preload_exposes_minimal_overlay_api() -> None:
    preload_source = (ELECTRON_ROOT / "src" / "preload" / "preload.ts").read_text(encoding="utf-8")
    assert "contextBridge.exposeInMainWorld" in preload_source
    assert "setInteractive" in preload_source
    assert "copyText" in preload_source
    assert "toggleControlCard" in preload_source
    assert "openPopover" in preload_source
    assert "settingSelected" in preload_source
    assert "DEEPSEEK_API_KEY" not in preload_source
    assert "api_key" not in preload_source.lower()


def test_shared_overlay_ipc_types_define_window_state_contract() -> None:
    shared = (ELECTRON_ROOT / "src" / "shared" / "overlayIpcTypes.ts").read_text(encoding="utf-8")
    assert 'export type OverlayWindowType = "subtitle" | "settings-icon" | "control-card" | "popover"' in shared
    assert "export interface OverlayUiState" in shared
    assert "export interface OverlayRendererApi" in shared
    assert "overlay:toggle-control-card" in shared
    assert "overlay:state-updated" in shared
    assert "overlay:position-updated" in shared


def test_bridge_message_types_exist() -> None:
    message_types = (
        ELECTRON_ROOT / "src" / "shared" / "backendBridgeTypes.ts"
    ).read_text(encoding="utf-8")
    assert "export interface SubtitleEvent" in message_types
    assert "export interface StatusEvent" in message_types
    assert "export interface CommandMessage" in message_types
    assert '"deepseek-v4-flash"' in message_types
    assert '"deepseek-v4-pro"' in message_types


def test_python_electron_live_bridge_exists_and_keeps_keys_server_side() -> None:
    bridge = (ROOT / "src" / "yt_live_translator" / "ui" / "electron_overlay_bridge.py").read_text(
        encoding="utf-8"
    )
    main_py = (ROOT / "src" / "yt_live_translator" / "main.py").read_text(encoding="utf-8")
    assert "asyncio.start_server" in bridge
    assert "127.0.0.1" in bridge
    assert "run_electron_overlay_live" in bridge
    assert "resolve_deepseek_api_key" in bridge
    assert "--electron-overlay-live" in main_py
    assert "sk-" not in bridge


def test_phase_2_components_exist() -> None:
    components = ELECTRON_ROOT / "src" / "renderer" / "components"
    expected = {
        "GlassCard.tsx",
        "GlassEdge.tsx",
        "GlassHighlight.tsx",
        "SubtitleBar.tsx",
        "SettingsIconButton.tsx",
        "ControlHubCard.tsx",
        "OptionPopoverCard.tsx",
        "GlassSlider.tsx",
        "TuningPanel.tsx",
        "LiquidThumb.tsx",
    }
    assert expected.issubset({path.name for path in components.iterdir()})


def test_electron_phase_2_does_not_call_python_pipeline() -> None:
    renderer_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ELECTRON_ROOT / "src" / "renderer").rglob("*")
        if path.suffix in {".ts", ".tsx"}
    )
    forbidden = ["subtitle_pipeline", "DeepSeekClient", "faster_whisper", "glossary_repo"]
    for token in forbidden:
        assert token not in renderer_sources
