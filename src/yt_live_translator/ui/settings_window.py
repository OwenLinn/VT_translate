"""Stage 8 settings window."""

from __future__ import annotations

from pathlib import Path

from yt_live_translator.core.config import DEEPSEEK_MODELS, RuntimeConfig
from yt_live_translator.storage.db import resolve_database_path
from yt_live_translator.storage.settings_repo import SettingsRepository, SettingsSnapshot
from yt_live_translator.ui.overlay_window import OverlayError


def run_settings_window(
    runtime_config: RuntimeConfig,
    *,
    database_path: str | Path | None = None,
    close_after_seconds: float | None = None,
) -> int:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import (
            QApplication,
            QComboBox,
            QDoubleSpinBox,
            QFormLayout,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise OverlayError("PySide6 is required for the settings window. Install it with: pip install PySide6") from exc

    repository = SettingsRepository(resolve_database_path(runtime_config, database_path))
    snapshot = repository.load(runtime_config)

    app = QApplication.instance() or QApplication([])
    window = QWidget()
    window.setWindowTitle("YouTube Live Translator Settings")
    window.setMinimumWidth(420)

    target_language = QComboBox()
    target_language.addItems(["zh-TW", "zh-CN"])
    target_language.setCurrentText(snapshot.target_language)

    source_language = QComboBox()
    source_language.addItems(["auto", "en", "ja"])
    source_language.setCurrentText(snapshot.source_language)

    translation_font_size = _spin_box(8, 96, snapshot.translation_font_size)
    source_font_size = _spin_box(8, 72, snapshot.source_font_size)
    translation_color = QLineEdit(snapshot.translation_color)
    source_color = QLineEdit(snapshot.source_color)
    background_opacity = QDoubleSpinBox()
    background_opacity.setRange(0.0, 1.0)
    background_opacity.setSingleStep(0.05)
    background_opacity.setDecimals(2)
    background_opacity.setValue(snapshot.background_opacity)

    asr_model = QLineEdit(snapshot.asr_model)
    asr_device = QComboBox()
    asr_device.addItems(["cuda", "cpu"])
    asr_device.setCurrentText(snapshot.asr_device if snapshot.asr_device in ("cuda", "cpu") else "cpu")
    asr_compute_type = QLineEdit(snapshot.asr_compute_type)
    asr_beam_size = _spin_box(1, 10, snapshot.asr_beam_size)

    deepseek_model = QComboBox()
    deepseek_model.addItems(list(DEEPSEEK_MODELS))
    deepseek_model.setCurrentText(snapshot.deepseek_model)

    form = QFormLayout()
    form.addRow("Target", target_language)
    form.addRow("Source", source_language)
    form.addRow("Translation size", translation_font_size)
    form.addRow("Source size", source_font_size)
    form.addRow("Translation color", translation_color)
    form.addRow("Source color", source_color)
    form.addRow("Background opacity", background_opacity)
    form.addRow("ASR model", asr_model)
    form.addRow("ASR device", asr_device)
    form.addRow("ASR compute", asr_compute_type)
    form.addRow("ASR beam", asr_beam_size)
    form.addRow("DeepSeek model", deepseek_model)

    save_button = QPushButton("Save")
    layout = QVBoxLayout(window)
    layout.addLayout(form)
    layout.addWidget(save_button)

    def save() -> None:
        try:
            repository.save(
                SettingsSnapshot(
                    target_language=target_language.currentText(),
                    source_language=source_language.currentText(),
                    translation_font_size=translation_font_size.value(),
                    source_font_size=source_font_size.value(),
                    translation_color=translation_color.text().strip(),
                    source_color=source_color.text().strip(),
                    background_opacity=background_opacity.value(),
                    asr_model=asr_model.text().strip(),
                    asr_device=asr_device.currentText(),
                    asr_compute_type=asr_compute_type.text().strip(),
                    asr_beam_size=asr_beam_size.value(),
                    deepseek_model=deepseek_model.currentText(),
                )
            )
        except ValueError as exc:
            QMessageBox.warning(window, "Invalid settings", str(exc))
            return
        QMessageBox.information(window, "Settings", "Saved")

    save_button.clicked.connect(save)
    window.show()

    if close_after_seconds is not None:
        QTimer.singleShot(round(close_after_seconds * 1000), app.quit)
    return app.exec()


def _spin_box(minimum: int, maximum: int, value: int):
    from PySide6.QtWidgets import QSpinBox

    spin_box = QSpinBox()
    spin_box.setRange(minimum, maximum)
    spin_box.setValue(value)
    return spin_box
