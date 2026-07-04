"""QObject bridge used by the QML overlay frontend."""

from __future__ import annotations

from dataclasses import dataclass

from yt_live_translator.core.config import RuntimeConfig

try:
    from PySide6.QtCore import QObject, Property, Signal, Slot
except ImportError:  # pragma: no cover - exercised when PySide6 is unavailable.
    QObject = object  # type: ignore[assignment,misc]
    Property = None  # type: ignore[assignment]
    Signal = None  # type: ignore[assignment]

    def Slot(*_args, **_kwargs):  # type: ignore[no-redef]
        def decorator(func):
            return func

        return decorator


@dataclass(frozen=True)
class OverlayBridgeState:
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    asr_model: str
    deepseek_model: str
    api_key_status: str
    show_source: bool
    show_translation: bool
    subtitle_opacity: float
    glass_opacity: float
    card_opacity: float
    panel_tint_opacity: float
    glass_iridescence: float
    iridescence_width: float
    corner_radius: int
    card_corner_radius: int
    edge_width: float
    edge_opacity: float
    edge_darkening: float
    distortion: float
    reflect_power: float
    rgb_shift: float
    cyan_edge_opacity: float
    magenta_edge_opacity: float
    warm_edge_opacity: float
    shadow_opacity: float
    shadow_radius: int
    shadow_y_offset: int
    highlight_opacity: float
    radial_highlight_opacity: float
    top_highlight_height: float
    animation_ms: int
    thumb_move_ms: int
    thumb_stretch_scale: float
    thumb_compress_scale: float
    translation_font_size: int
    source_font_size: int


class OverlayBridge(QObject):
    """Small state bridge between Python and QML.

    Phase 1 intentionally exposes UI state and request signals only. Pipeline
    start/stop wiring is deferred to the QML pipeline phase.
    """

    subtitleChanged = Signal()
    runningChanged = Signal()
    settingsChanged = Signal()
    requestStart = Signal()
    requestStop = Signal()
    requestOpenSettings = Signal()
    requestSaveSettings = Signal()

    def __init__(self, state: OverlayBridgeState) -> None:
        super().__init__()
        self._source_text = state.source_text
        self._translated_text = state.translated_text
        self._is_partial = False
        self._is_running = False
        self._source_language = state.source_language
        self._target_language = state.target_language
        self._asr_model = state.asr_model
        self._deepseek_model = state.deepseek_model
        self._api_key_status = state.api_key_status
        self._show_source = state.show_source
        self._show_translation = state.show_translation
        self._subtitle_opacity = state.subtitle_opacity
        self._glass_opacity = state.glass_opacity
        self._card_opacity = state.card_opacity
        self._panel_tint_opacity = state.panel_tint_opacity
        self._glass_iridescence = state.glass_iridescence
        self._iridescence_width = state.iridescence_width
        self._corner_radius = state.corner_radius
        self._card_corner_radius = state.card_corner_radius
        self._edge_width = state.edge_width
        self._edge_opacity = state.edge_opacity
        self._edge_darkening = state.edge_darkening
        self._distortion = state.distortion
        self._reflect_power = state.reflect_power
        self._rgb_shift = state.rgb_shift
        self._cyan_edge_opacity = state.cyan_edge_opacity
        self._magenta_edge_opacity = state.magenta_edge_opacity
        self._warm_edge_opacity = state.warm_edge_opacity
        self._shadow_opacity = state.shadow_opacity
        self._shadow_radius = state.shadow_radius
        self._shadow_y_offset = state.shadow_y_offset
        self._highlight_opacity = state.highlight_opacity
        self._radial_highlight_opacity = state.radial_highlight_opacity
        self._top_highlight_height = state.top_highlight_height
        self._animation_ms = state.animation_ms
        self._thumb_move_ms = state.thumb_move_ms
        self._thumb_stretch_scale = state.thumb_stretch_scale
        self._thumb_compress_scale = state.thumb_compress_scale
        self._translation_font_size = state.translation_font_size
        self._source_font_size = state.source_font_size

    @classmethod
    def from_runtime_config(cls, runtime_config: RuntimeConfig) -> "OverlayBridge":
        api_key_status = "configured" if runtime_config.resolve_deepseek_api_key() else "missing"
        qml = runtime_config.qml_overlay
        return cls(
            OverlayBridgeState(
                source_text="QML overlay frontend is ready.",
                translated_text="Liquid Glass overlay preview.",
                source_language=runtime_config.app.source_language,
                target_language=runtime_config.app.target_language,
                asr_model=runtime_config.asr.model,
                deepseek_model=runtime_config.deepseek.model,
                api_key_status=api_key_status,
                show_source=qml.subtitle.show_source,
                show_translation=qml.subtitle.show_translation,
                subtitle_opacity=1.0,
                glass_opacity=qml.glass.subtitle_background_opacity,
                card_opacity=qml.glass.card_background_opacity,
                panel_tint_opacity=qml.glass.panel_tint_opacity,
                glass_iridescence=qml.glass.iridescence_opacity,
                iridescence_width=qml.glass.iridescence_width,
                corner_radius=qml.glass.corner_radius,
                card_corner_radius=qml.glass.card_corner_radius,
                edge_width=qml.glass.edge_width,
                edge_opacity=qml.glass.edge_opacity,
                edge_darkening=qml.glass.edge_darkening,
                distortion=qml.glass.distortion,
                reflect_power=qml.glass.reflect_power,
                rgb_shift=qml.glass.rgb_shift,
                cyan_edge_opacity=qml.glass.cyan_edge_opacity,
                magenta_edge_opacity=qml.glass.magenta_edge_opacity,
                warm_edge_opacity=qml.glass.warm_edge_opacity,
                shadow_opacity=qml.glass.shadow_opacity,
                shadow_radius=qml.glass.shadow_radius,
                shadow_y_offset=qml.glass.shadow_y_offset,
                highlight_opacity=qml.glass.highlight_opacity,
                radial_highlight_opacity=qml.glass.radial_highlight_opacity,
                top_highlight_height=qml.glass.top_highlight_height,
                animation_ms=qml.animation.subtitle_fade_ms,
                thumb_move_ms=qml.animation.thumb_move_ms,
                thumb_stretch_scale=qml.animation.thumb_stretch_scale,
                thumb_compress_scale=qml.animation.thumb_compress_scale,
                translation_font_size=qml.subtitle.translation_font_size,
                source_font_size=qml.subtitle.source_font_size,
            )
        )

    def update_subtitle(self, source: str, translation: str, *, partial: bool = False) -> None:
        self._source_text = source
        self._translated_text = translation
        self._is_partial = partial
        self.subtitleChanged.emit()

    def _emit_settings_changed(self) -> None:
        self.settingsChanged.emit()
        self.subtitleChanged.emit()

    @Property(str, notify=subtitleChanged)
    def sourceText(self) -> str:
        return self._source_text

    @Property(str, notify=subtitleChanged)
    def translatedText(self) -> str:
        return self._translated_text

    @Property(bool, notify=subtitleChanged)
    def isPartial(self) -> bool:
        return self._is_partial

    @Property(bool, notify=runningChanged)
    def isRunning(self) -> bool:
        return self._is_running

    @Property(str, notify=settingsChanged)
    def sourceLanguage(self) -> str:
        return self._source_language

    @Property(str, notify=settingsChanged)
    def targetLanguage(self) -> str:
        return self._target_language

    @Property(str, notify=settingsChanged)
    def asrModel(self) -> str:
        return self._asr_model

    @Property(str, notify=settingsChanged)
    def deepseekModel(self) -> str:
        return self._deepseek_model

    @Property(str, notify=settingsChanged)
    def apiKeyStatus(self) -> str:
        return self._api_key_status

    @Property(bool, notify=subtitleChanged)
    def showSource(self) -> bool:
        return self._show_source

    @Property(bool, notify=subtitleChanged)
    def showTranslation(self) -> bool:
        return self._show_translation

    @Property(float, notify=subtitleChanged)
    def subtitleOpacity(self) -> float:
        return self._subtitle_opacity

    @Property(float, notify=subtitleChanged)
    def glassOpacity(self) -> float:
        return self._glass_opacity

    @Property(float, notify=subtitleChanged)
    def cardOpacity(self) -> float:
        return self._card_opacity

    @Property(float, notify=subtitleChanged)
    def panelTintOpacity(self) -> float:
        return self._panel_tint_opacity

    @Property(float, notify=subtitleChanged)
    def glassIridescence(self) -> float:
        return self._glass_iridescence

    @Property(float, notify=subtitleChanged)
    def iridescenceWidth(self) -> float:
        return self._iridescence_width

    @Property(int, notify=subtitleChanged)
    def cornerRadius(self) -> int:
        return self._corner_radius

    @Property(int, notify=subtitleChanged)
    def cardCornerRadius(self) -> int:
        return self._card_corner_radius

    @Property(float, notify=subtitleChanged)
    def edgeWidth(self) -> float:
        return self._edge_width

    @Property(float, notify=subtitleChanged)
    def edgeOpacity(self) -> float:
        return self._edge_opacity

    @Property(float, notify=subtitleChanged)
    def edgeDarkening(self) -> float:
        return self._edge_darkening

    @Property(float, notify=subtitleChanged)
    def distortion(self) -> float:
        return self._distortion

    @Property(float, notify=subtitleChanged)
    def reflectPower(self) -> float:
        return self._reflect_power

    @Property(float, notify=subtitleChanged)
    def rgbShift(self) -> float:
        return self._rgb_shift

    @Property(float, notify=subtitleChanged)
    def cyanEdgeOpacity(self) -> float:
        return self._cyan_edge_opacity

    @Property(float, notify=subtitleChanged)
    def magentaEdgeOpacity(self) -> float:
        return self._magenta_edge_opacity

    @Property(float, notify=subtitleChanged)
    def warmEdgeOpacity(self) -> float:
        return self._warm_edge_opacity

    @Property(float, notify=subtitleChanged)
    def shadowOpacity(self) -> float:
        return self._shadow_opacity

    @Property(int, notify=subtitleChanged)
    def shadowRadius(self) -> int:
        return self._shadow_radius

    @Property(int, notify=subtitleChanged)
    def shadowYOffset(self) -> int:
        return self._shadow_y_offset

    @Property(float, notify=subtitleChanged)
    def highlightOpacity(self) -> float:
        return self._highlight_opacity

    @Property(float, notify=subtitleChanged)
    def radialHighlightOpacity(self) -> float:
        return self._radial_highlight_opacity

    @Property(float, notify=subtitleChanged)
    def topHighlightHeight(self) -> float:
        return self._top_highlight_height

    @Property(int, notify=subtitleChanged)
    def animationMs(self) -> int:
        return self._animation_ms

    @Property(int, notify=subtitleChanged)
    def thumbMoveMs(self) -> int:
        return self._thumb_move_ms

    @Property(float, notify=subtitleChanged)
    def thumbStretchScale(self) -> float:
        return self._thumb_stretch_scale

    @Property(float, notify=subtitleChanged)
    def thumbCompressScale(self) -> float:
        return self._thumb_compress_scale

    @Property(int, notify=subtitleChanged)
    def translationFontSize(self) -> int:
        return self._translation_font_size

    @Property(int, notify=subtitleChanged)
    def sourceFontSize(self) -> int:
        return self._source_font_size

    @Slot()
    def startTranslation(self) -> None:
        if not self._is_running:
            self._is_running = True
            self.runningChanged.emit()
        self.requestStart.emit()

    @Slot()
    def stopTranslation(self) -> None:
        if self._is_running:
            self._is_running = False
            self.runningChanged.emit()
        self.requestStop.emit()

    @Slot(str)
    def setSourceLanguage(self, value: str) -> None:
        self._source_language = value
        self._emit_settings_changed()

    @Slot(str)
    def setTargetLanguage(self, value: str) -> None:
        self._target_language = value
        self._emit_settings_changed()

    @Slot(str)
    def setAsrModel(self, value: str) -> None:
        self._asr_model = value
        self._emit_settings_changed()

    @Slot(str)
    def setDeepseekModel(self, value: str) -> None:
        self._deepseek_model = value
        self._emit_settings_changed()

    @Slot(bool)
    def setShowSource(self, value: bool) -> None:
        self._show_source = value
        self._emit_settings_changed()

    @Slot(bool)
    def setShowTranslation(self, value: bool) -> None:
        self._show_translation = value
        self._emit_settings_changed()

    @Slot(float)
    def setSubtitleOpacity(self, value: float) -> None:
        self._subtitle_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setGlassOpacity(self, value: float) -> None:
        self._glass_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setCardOpacity(self, value: float) -> None:
        self._card_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setPanelTintOpacity(self, value: float) -> None:
        self._panel_tint_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setGlassIridescence(self, value: float) -> None:
        self._glass_iridescence = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setIridescenceWidth(self, value: float) -> None:
        self._iridescence_width = _clamp_float(value, 0.0, 8.0)
        self._emit_settings_changed()

    @Slot(int)
    def setCornerRadius(self, value: int) -> None:
        self._corner_radius = max(0, min(60, value))
        self._emit_settings_changed()

    @Slot(int)
    def setCardCornerRadius(self, value: int) -> None:
        self._card_corner_radius = max(0, min(64, value))
        self._emit_settings_changed()

    @Slot(float)
    def setEdgeWidth(self, value: float) -> None:
        self._edge_width = _clamp_float(value, 0.0, 12.0)
        self._emit_settings_changed()

    @Slot(float)
    def setEdgeOpacity(self, value: float) -> None:
        self._edge_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setEdgeDarkening(self, value: float) -> None:
        self._edge_darkening = _clamp_float(value, 0.0, 0.5)
        self._emit_settings_changed()

    @Slot(float)
    def setDistortion(self, value: float) -> None:
        self._distortion = _clamp_float(value, 0.0, 0.08)
        self._emit_settings_changed()

    @Slot(float)
    def setReflectPower(self, value: float) -> None:
        self._reflect_power = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setRgbShift(self, value: float) -> None:
        self._rgb_shift = _clamp_float(value, 0.0, 0.06)
        self._emit_settings_changed()

    @Slot(float)
    def setCyanEdgeOpacity(self, value: float) -> None:
        self._cyan_edge_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setMagentaEdgeOpacity(self, value: float) -> None:
        self._magenta_edge_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setWarmEdgeOpacity(self, value: float) -> None:
        self._warm_edge_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setShadowOpacity(self, value: float) -> None:
        self._shadow_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(int)
    def setShadowRadius(self, value: int) -> None:
        self._shadow_radius = max(0, min(80, value))
        self._emit_settings_changed()

    @Slot(int)
    def setShadowYOffset(self, value: int) -> None:
        self._shadow_y_offset = max(-20, min(40, value))
        self._emit_settings_changed()

    @Slot(float)
    def setHighlightOpacity(self, value: float) -> None:
        self._highlight_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setRadialHighlightOpacity(self, value: float) -> None:
        self._radial_highlight_opacity = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(float)
    def setTopHighlightHeight(self, value: float) -> None:
        self._top_highlight_height = _clamp_float(value, 0.0, 1.0)
        self._emit_settings_changed()

    @Slot(int)
    def setAnimationMs(self, value: int) -> None:
        self._animation_ms = max(0, min(800, value))
        self._emit_settings_changed()

    @Slot(int)
    def setThumbMoveMs(self, value: int) -> None:
        self._thumb_move_ms = max(0, min(800, value))
        self._emit_settings_changed()

    @Slot(float)
    def setThumbStretchScale(self, value: float) -> None:
        self._thumb_stretch_scale = _clamp_float(value, 1.0, 1.5)
        self._emit_settings_changed()

    @Slot(float)
    def setThumbCompressScale(self, value: float) -> None:
        self._thumb_compress_scale = _clamp_float(value, 0.7, 1.0)
        self._emit_settings_changed()

    @Slot(int)
    def setTranslationFontSize(self, value: int) -> None:
        self._translation_font_size = max(12, min(72, value))
        self._emit_settings_changed()

    @Slot(int)
    def setSourceFontSize(self, value: int) -> None:
        self._source_font_size = max(10, min(48, value))
        self._emit_settings_changed()

    @Slot()
    def saveSettings(self) -> None:
        self.requestSaveSettings.emit()

    @Slot()
    def openSettings(self) -> None:
        self.requestOpenSettings.emit()

    @Slot(result=str)
    def copyCurrentParameters(self) -> str:
        text = self.current_parameter_text()
        try:
            from PySide6.QtGui import QGuiApplication

            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)
        except Exception:
            pass
        print(text)
        return text

    def current_parameter_text(self) -> str:
        return "\n".join(
            [
                "[qml_overlay.subtitle]",
                f"translation_font_size = {self._translation_font_size}",
                f"source_font_size = {self._source_font_size}",
                f"show_source = {str(self._show_source).lower()}",
                f"show_translation = {str(self._show_translation).lower()}",
                "",
                "[qml_overlay.glass]",
                f"subtitle_background_opacity = {self._glass_opacity:.3f}",
                f"card_background_opacity = {self._card_opacity:.3f}",
                f"panel_tint_opacity = {self._panel_tint_opacity:.3f}",
                f"corner_radius = {self._corner_radius}",
                f"card_corner_radius = {self._card_corner_radius}",
                f"edge_width = {self._edge_width:.3f}",
                f"edge_opacity = {self._edge_opacity:.3f}",
                f"edge_darkening = {self._edge_darkening:.3f}",
                f"distortion = {self._distortion:.3f}",
                f"reflect_power = {self._reflect_power:.3f}",
                f"highlight_opacity = {self._highlight_opacity:.3f}",
                f"top_highlight_height = {self._top_highlight_height:.3f}",
                f"radial_highlight_opacity = {self._radial_highlight_opacity:.3f}",
                f"shadow_opacity = {self._shadow_opacity:.3f}",
                f"shadow_radius = {self._shadow_radius}",
                f"shadow_y_offset = {self._shadow_y_offset}",
                f"iridescence_opacity = {self._glass_iridescence:.3f}",
                f"iridescence_width = {self._iridescence_width:.3f}",
                f"rgb_shift = {self._rgb_shift:.3f}",
                f"cyan_edge_opacity = {self._cyan_edge_opacity:.3f}",
                f"magenta_edge_opacity = {self._magenta_edge_opacity:.3f}",
                f"warm_edge_opacity = {self._warm_edge_opacity:.3f}",
                "",
                "[qml_overlay.animation]",
                f"subtitle_fade_ms = {self._animation_ms}",
                f"thumb_move_ms = {self._thumb_move_ms}",
                f"thumb_stretch_scale = {self._thumb_stretch_scale:.3f}",
                f"thumb_compress_scale = {self._thumb_compress_scale:.3f}",
            ]
        )


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))
