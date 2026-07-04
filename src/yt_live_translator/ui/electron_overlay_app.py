"""Launcher helpers for the Electron overlay frontend."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from yt_live_translator.core.config import project_root
from yt_live_translator.ui.overlay_window import OverlayError


ELECTRON_OVERLAY_RELATIVE_PATH = Path("frontend") / "electron-overlay"
WINDOWS_NPM_FALLBACK = Path(r"C:\Program Files\nodejs\npm.cmd")


def electron_overlay_root() -> Path:
    return project_root() / ELECTRON_OVERLAY_RELATIVE_PATH


def electron_overlay_command(mode: str) -> list[str]:
    if mode == "mock":
        return ["npm", "run", "dev:mock"]
    if mode == "tuning":
        return ["npm", "run", "dev:tuning"]
    if mode == "live":
        return ["npm", "run", "dev:live"]
    raise ValueError("Electron overlay mode must be mock, tuning, or live")


def resolve_npm_command() -> str:
    if WINDOWS_NPM_FALLBACK.exists():
        return str(WINDOWS_NPM_FALLBACK)
    return "npm"


def electron_overlay_env() -> dict[str, str]:
    env = os.environ.copy()
    if WINDOWS_NPM_FALLBACK.exists():
        node_dir = str(WINDOWS_NPM_FALLBACK.parent)
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    return env


def run_electron_overlay(mode: str) -> int:
    root = electron_overlay_root()
    if not root.exists():
        raise OverlayError(f"Electron overlay frontend not found: {root}")
    package_json = root / "package.json"
    if not package_json.exists():
        raise OverlayError(f"Electron overlay package.json not found: {package_json}")

    env = electron_overlay_env()
    env["OVERLAY_MODE"] = mode
    try:
        command = electron_overlay_command(mode)
        command[0] = resolve_npm_command()
        return subprocess.call(command, cwd=root, env=env)
    except FileNotFoundError as exc:
        raise OverlayError("npm is required to run the Electron overlay frontend") from exc
