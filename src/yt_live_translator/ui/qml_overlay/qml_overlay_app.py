"""QML overlay frontend launch helpers."""

from __future__ import annotations

from yt_live_translator.core.config import RuntimeConfig
from yt_live_translator.ui.overlay_window import OverlayError
from yt_live_translator.ui.qml_overlay.qml_bridge import OverlayBridge
from yt_live_translator.ui.qml_overlay.qml_resources import main_overlay_qml, qml_root


def run_qml_overlay_test(
    runtime_config: RuntimeConfig,
    close_after_seconds: float | None = None,
    *,
    tuning_mode: bool = False,
) -> int:
    try:
        from PySide6.QtCore import QTimer, QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise OverlayError("PySide6 QtQml is required for the QML overlay frontend") from exc

    qml_file = main_overlay_qml()
    if not qml_file.exists():
        raise OverlayError(f"QML overlay entrypoint not found: {qml_file}")

    app = QApplication.instance() or QApplication([])
    bridge = OverlayBridge.from_runtime_config(runtime_config)
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_root()))
    engine.rootContext().setContextProperty("overlayBridge", bridge)
    engine.rootContext().setContextProperty(
        "qmlOverlayConfig",
        _qml_config_dict(runtime_config, tuning_mode=tuning_mode),
    )
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        raise OverlayError(f"Failed to load QML overlay: {qml_file}")

    QTimer.singleShot(
        1600,
        lambda: bridge.update_subtitle(
            "QML overlay uses placeholder subtitle data.",
            "Liquid Glass tuning shell is running." if tuning_mode else "The glass overlay shell is running.",
            partial=False,
        ),
    )
    if close_after_seconds is not None:
        QTimer.singleShot(round(close_after_seconds * 1000), app.quit)
    return app.exec()


def run_qml_overlay_tuning(runtime_config: RuntimeConfig, close_after_seconds: float | None = None) -> int:
    return run_qml_overlay_test(
        runtime_config,
        close_after_seconds=close_after_seconds,
        tuning_mode=True,
    )


def _qml_config_dict(runtime_config: RuntimeConfig, *, tuning_mode: bool = False) -> dict:
    qml = runtime_config.qml_overlay
    return {
        "width": qml.width,
        "height": qml.height,
        "x": qml.x,
        "y": qml.y,
        "alwaysOnTop": qml.always_on_top,
        "frameless": qml.frameless,
        "transparentBackground": qml.transparent_background,
        "showSettingsIcon": qml.show_settings_icon,
        "fontFamily": qml.subtitle.font_family,
        "translationColor": qml.subtitle.translation_color,
        "sourceColor": qml.subtitle.source_color,
        "textShadowOpacity": qml.subtitle.text_shadow_opacity,
        "maxTranslationLines": qml.subtitle.max_translation_lines,
        "maxSourceLines": qml.subtitle.max_source_lines,
        "cornerRadius": qml.glass.corner_radius,
        "subtitleCornerRadius": qml.glass.subtitle_corner_radius,
        "cardCornerRadius": qml.glass.card_corner_radius,
        "cardOpacity": qml.glass.card_background_opacity,
        "panelTintOpacity": qml.glass.panel_tint_opacity,
        "borderOpacity": qml.glass.border_opacity,
        "edgeWidth": qml.glass.edge_width,
        "edgeOpacity": qml.glass.edge_opacity,
        "edgeDarkening": qml.glass.edge_darkening,
        "distortion": qml.glass.distortion,
        "reflectPower": qml.glass.reflect_power,
        "highlightOpacity": qml.glass.highlight_opacity,
        "topHighlightHeight": qml.glass.top_highlight_height,
        "radialHighlightOpacity": qml.glass.radial_highlight_opacity,
        "shadowOpacity": qml.glass.shadow_opacity,
        "shadowRadius": qml.glass.shadow_radius,
        "shadowYOffset": qml.glass.shadow_y_offset,
        "iridescenceEnabled": qml.glass.iridescence_enabled,
        "iridescenceOpacity": qml.glass.iridescence_opacity,
        "iridescenceWidth": qml.glass.iridescence_width,
        "rgbShift": qml.glass.rgb_shift,
        "cyanEdgeOpacity": qml.glass.cyan_edge_opacity,
        "magentaEdgeOpacity": qml.glass.magenta_edge_opacity,
        "warmEdgeOpacity": qml.glass.warm_edge_opacity,
        "subtitleFadeMs": qml.animation.subtitle_fade_ms,
        "cardOpenMs": qml.animation.card_open_ms,
        "cardCloseMs": qml.animation.card_close_ms,
        "popoverOpenMs": qml.animation.popover_open_ms,
        "popoverCloseMs": qml.animation.popover_close_ms,
        "slideOffsetPx": qml.animation.slide_offset_px,
        "scaleFrom": qml.animation.scale_from,
        "scaleTo": qml.animation.scale_to,
        "thumbMoveMs": qml.animation.thumb_move_ms,
        "thumbStretchScale": qml.animation.thumb_stretch_scale,
        "thumbCompressScale": qml.animation.thumb_compress_scale,
        "tuningMode": tuning_mode,
    }
