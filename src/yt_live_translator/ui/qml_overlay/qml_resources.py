"""Path helpers for the QML overlay frontend."""

from __future__ import annotations

from pathlib import Path


def qml_root() -> Path:
    return Path(__file__).resolve().parent / "qml"


def main_overlay_qml() -> Path:
    return qml_root() / "MainOverlay.qml"

