"""Draggable always-on-top subtitle overlay with optional soft glass styling."""

from __future__ import annotations

from dataclasses import dataclass, replace

from yt_live_translator.core.config import OverlayConfig


class OverlayError(RuntimeError):
    """Raised when the overlay UI cannot be started."""


@dataclass(frozen=True)
class GlassStyle:
    enabled: bool = False
    corner_radius: int = 28
    background_opacity: float = 0.52
    border_opacity: float = 0.35
    highlight_opacity: float = 0.28
    shadow_opacity: float = 0.32
    shadow_blur_radius: int = 32
    noise_opacity: float = 0.025


@dataclass(frozen=True)
class AnimationStyle:
    enabled: bool = True
    fade_duration_ms: int = 160
    slide_offset_px: int = 8
    drag_scale: float = 0.985


@dataclass(frozen=True)
class NativeEffectStyle:
    enabled: bool = False
    effect: str = "none"


@dataclass(frozen=True)
class OverlayStyle:
    show_source: bool
    show_translation: bool
    font_family: str
    translation_font_size: int
    source_font_size: int
    translation_color: str
    source_color: str
    background_color: str
    background_opacity: float
    always_on_top: bool
    glass: GlassStyle = GlassStyle()
    animation: AnimationStyle = AnimationStyle()
    native_effect: NativeEffectStyle = NativeEffectStyle()


def style_from_config(config: OverlayConfig) -> OverlayStyle:
    return OverlayStyle(
        show_source=config.show_source,
        show_translation=config.show_translation,
        font_family=config.font_family,
        translation_font_size=config.translation_font_size,
        source_font_size=config.source_font_size,
        translation_color=config.translation_color,
        source_color=config.source_color,
        background_color=config.background_color,
        background_opacity=config.background_opacity,
        always_on_top=config.always_on_top,
        glass=GlassStyle(
            enabled=config.glass.enabled,
            corner_radius=config.glass.corner_radius,
            background_opacity=config.glass.background_opacity,
            border_opacity=config.glass.border_opacity,
            highlight_opacity=config.glass.highlight_opacity,
            shadow_opacity=config.glass.shadow_opacity,
            shadow_blur_radius=config.glass.shadow_blur_radius,
            noise_opacity=config.glass.noise_opacity,
        ),
        animation=AnimationStyle(
            enabled=config.animation.enabled,
            fade_duration_ms=config.animation.fade_duration_ms,
            slide_offset_px=config.animation.slide_offset_px,
            drag_scale=config.animation.drag_scale,
        ),
        native_effect=NativeEffectStyle(
            enabled=config.native_effect.enabled,
            effect=config.native_effect.effect,
        ),
    )


def style_with_mode(style: OverlayStyle, mode: str | None) -> OverlayStyle:
    if mode is None:
        return style
    if mode == "glass":
        return replace(style, glass=replace(style.glass, enabled=True))
    if mode == "classic":
        return replace(style, glass=replace(style.glass, enabled=False))
    raise ValueError("overlay style must be glass or classic")


def background_rgba(style: OverlayStyle) -> str:
    red, green, blue = _hex_to_rgb(style.background_color)
    alpha = max(0.0, min(1.0, _panel_background_opacity(style)))
    return f"rgba({red}, {green}, {blue}, {alpha:.3f})"


def build_overlay_stylesheet(style: OverlayStyle) -> str:
    radius = style.glass.corner_radius if style.glass.enabled else 8
    root_background = "transparent" if style.glass.enabled else background_rgba(style)
    return f"""
QWidget#overlayRoot {{
    background-color: {root_background};
    border-radius: {radius}px;
}}
QWidget#contentRoot {{
    background-color: transparent;
}}
QLabel#translationLabel {{
    color: {style.translation_color};
    font-family: "{style.font_family}";
    font-size: {style.translation_font_size}px;
    font-weight: 700;
    background-color: transparent;
}}
QLabel#sourceLabel {{
    color: {style.source_color};
    font-family: "{style.font_family}";
    font-size: {style.source_font_size}px;
    background-color: transparent;
}}
""".strip()


def run_overlay_test(
    style: OverlayStyle,
    close_after_seconds: float | None = None,
    style_mode: str | None = None,
) -> int:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise OverlayError("PySide6 is required for the overlay window. Install it with: pip install PySide6") from exc

    app = QApplication.instance() or QApplication([])
    window = SubtitleOverlayWindow(style_with_mode(style, style_mode))
    window.update_subtitle(
        source_text="Now testing the subtitle overlay.",
        translated_text="Glass overlay subtitle test.",
    )
    window.show()
    QTimer.singleShot(
        1500,
        lambda: window.update_subtitle("Drag me around.", "Cross-fade update sample."),
    )
    if close_after_seconds is not None:
        QTimer.singleShot(round(close_after_seconds * 1000), app.quit)
    return app.exec()


class SubtitleOverlayWindow:  # pragma: no cover - exercised by smoke tests.
    def __init__(self, style: OverlayStyle) -> None:
        try:
            from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt
            from PySide6.QtGui import QColor
            from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect, QVBoxLayout, QWidget
        except ImportError as exc:
            raise OverlayError(
                "PySide6 is required for the overlay window. Install it with: pip install PySide6"
            ) from exc

        class _Window(QWidget):
            def __init__(self, outer: "SubtitleOverlayWindow") -> None:
                super().__init__()
                self.outer = outer

            def paintEvent(self, event) -> None:
                super().paintEvent(event)
                self.outer._paint_panel(self)

            def mousePressEvent(self, event) -> None:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.outer._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    self.outer._set_drag_active(True)
                    event.accept()

            def mouseMoveEvent(self, event) -> None:
                if event.buttons() & Qt.MouseButton.LeftButton and self.outer._drag_position is not None:
                    self.move(event.globalPosition().toPoint() - self.outer._drag_position)
                    event.accept()

            def mouseReleaseEvent(self, event) -> None:
                self.outer._drag_position = None
                self.outer._set_drag_active(False)
                event.accept()

        self._qt = {
            "QColor": QColor,
            "QEasingCurve": QEasingCurve,
            "QParallelAnimationGroup": QParallelAnimationGroup,
            "QPoint": QPoint,
            "QPropertyAnimation": QPropertyAnimation,
            "QGraphicsOpacityEffect": QGraphicsOpacityEffect,
        }
        self.style = style
        self._drag_position = None
        self._drag_active = False
        self._current_animation = None
        self._native_effect_attempted = False
        self._was_positioned = False
        self._source_text = ""
        self._translated_text = ""
        self._partial = False
        self.window = _Window(self)
        self.window.setObjectName("overlayRoot")
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if style.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.window.setWindowFlags(flags)
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.window.setMinimumSize(720, 120)
        self.window.resize(980, 170)

        self.content_widget = QWidget(self.window)
        self.content_widget.setObjectName("contentRoot")
        self.opacity_effect = QGraphicsOpacityEffect(self.content_widget)
        self.opacity_effect.setOpacity(1.0)
        self.content_widget.setGraphicsEffect(self.opacity_effect)

        self.translation_label = QLabel()
        self.translation_label.setObjectName("translationLabel")
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translation_label.setWordWrap(True)

        self.source_label = QLabel()
        self.source_label.setObjectName("sourceLabel")
        self.source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_label.setWordWrap(True)

        self._apply_text_shadow(self.translation_label, blur_radius=8, y_offset=2)
        self._apply_text_shadow(self.source_label, blur_radius=6, y_offset=1)

        outer_layout = QVBoxLayout(self.window)
        outer_layout.setContentsMargins(24, 18, 24, 18)
        inner_layout = QVBoxLayout(self.content_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(8)
        inner_layout.addWidget(self.translation_label)
        inner_layout.addWidget(self.source_label)
        outer_layout.addWidget(self.content_widget)
        self.window.setStyleSheet(build_overlay_stylesheet(style))
        self.update_subtitle("", "", animate=False)

    def update_subtitle(
        self,
        source_text: str = "",
        translated_text: str = "",
        *,
        animate: bool = True,
        partial: bool = False,
    ) -> None:
        previous_snapshot = None
        if animate and self.style.animation.enabled and self.window.isVisible():
            previous_snapshot = self.content_widget.grab()
        self._source_text = source_text
        self._translated_text = translated_text
        self._partial = partial
        self.translation_label.setVisible(self.style.show_translation)
        self.source_label.setVisible(self.style.show_source)
        self._set_partial_style(partial)
        self.translation_label.setText(translated_text if self.style.show_translation else "")
        self.source_label.setText(source_text if self.style.show_source else "")
        if animate and self.style.animation.enabled:
            self._animate_subtitle_update(previous_snapshot)
        else:
            self.opacity_effect.setOpacity(1.0)
            self.translation_label.update()
            self.source_label.update()
            self.content_widget.update()
            self.window.repaint()

    def show(self) -> None:
        self.window.show()
        self.ensure_visible(activate=False)
        self._try_apply_native_effect()

    def ensure_visible(self, *, activate: bool = False) -> None:
        if self.window.isMinimized():
            self.window.showNormal()
        elif not self.window.isVisible():
            self.window.show()
        self._position_bottom_center_once()
        self.window.raise_()
        if activate:
            self.window.activateWindow()
        self.window.repaint()

    def _position_bottom_center_once(self) -> None:
        if self._was_positioned:
            return
        screen = self.window.screen()
        if screen is None:
            return
        available = screen.availableGeometry()
        width = min(self.window.width(), max(720, available.width() - 80))
        height = self.window.height()
        x = available.x() + max(0, (available.width() - width) // 2)
        y = available.y() + max(0, available.height() - height - 72)
        self.window.resize(width, height)
        self.window.move(x, y)
        self._was_positioned = True

    def _paint_panel(self, widget) -> None:
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
        except ImportError as exc:
            raise OverlayError("PySide6 is required for painting the overlay") from exc

        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = widget.rect().adjusted(12, 12, -12, -12)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        if self._drag_active and self.style.animation.enabled:
            scale = self.style.animation.drag_scale
            shrink_x = rect.width() * (1.0 - scale) / 2.0
            shrink_y = rect.height() * (1.0 - scale) / 2.0
            rect = rect.adjusted(round(shrink_x), round(shrink_y), -round(shrink_x), -round(shrink_y))

        radius = self.style.glass.corner_radius if self.style.glass.enabled else 8
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self.style.glass.enabled:
            shadow_alpha = _alpha(self.style.glass.shadow_opacity)
            for offset, divisor in ((10, 4), (5, 7), (2, 11)):
                painter.fillPath(
                    _translated_path(path, 0, offset),
                    QColor(0, 0, 0, max(1, shadow_alpha // divisor)),
                )
            bg_alpha = _alpha(_panel_background_opacity(self.style) + (0.08 if self._drag_active else 0.0))
            painter.fillPath(path, _qcolor_from_hex(self.style.background_color, bg_alpha))
            if self.style.glass.noise_opacity > 0:
                painter.fillPath(path, QColor(255, 255, 255, _alpha(self.style.glass.noise_opacity)))

            border = QPen(QColor(255, 255, 255, _alpha(self.style.glass.border_opacity)))
            border.setWidth(1)
            painter.setPen(border)
            painter.drawPath(path)

            highlight = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            highlight.setColorAt(0.0, QColor(255, 255, 255, _alpha(self.style.glass.highlight_opacity)))
            highlight.setColorAt(0.32, QColor(255, 255, 255, max(1, _alpha(self.style.glass.highlight_opacity) // 5)))
            highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillPath(path, highlight)
        else:
            painter.fillPath(path, _qcolor_from_hex(self.style.background_color, _alpha(self.style.background_opacity)))

        self._paint_subtitle_text(painter, rect)
        painter.setPen(Qt.PenStyle.NoPen)

    def _paint_subtitle_text(self, painter, panel_rect) -> None:
        try:
            from PySide6.QtCore import Qt, QRectF
            from PySide6.QtGui import QColor, QFont, QTextOption
        except ImportError as exc:
            raise OverlayError("PySide6 is required for painting overlay text") from exc

        text_blocks: list[tuple[str, str, int, bool]] = []
        if self.style.show_translation and self._translated_text:
            text_blocks.append(
                (
                    self._translated_text,
                    self.style.translation_color,
                    self.style.translation_font_size,
                    True,
                )
            )
        if self.style.show_source and self._source_text:
            text_blocks.append(
                (
                    self._source_text,
                    self.style.source_color,
                    self.style.source_font_size,
                    False,
                )
            )
        if not text_blocks:
            return

        content_rect = panel_rect.adjusted(40, 24, -40, -24)
        if content_rect.width() <= 0 or content_rect.height() <= 0:
            return

        spacing = 8 if len(text_blocks) > 1 else 0
        translation_height = int(content_rect.height() * 0.62) if len(text_blocks) > 1 else content_rect.height()
        source_height = max(1, content_rect.height() - translation_height - spacing)
        rects = (
            [QRectF(content_rect.x(), content_rect.y(), content_rect.width(), translation_height)]
            if len(text_blocks) == 1
            else [
                QRectF(content_rect.x(), content_rect.y(), content_rect.width(), translation_height),
                QRectF(
                    content_rect.x(),
                    content_rect.y() + translation_height + spacing,
                    content_rect.width(),
                    source_height,
                ),
            ]
        )

        option = QTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        for (text, color, font_size, bold), text_rect in zip(text_blocks, rects, strict=False):
            font = QFont(self.style.font_family)
            font.setPixelSize(font_size)
            font.setBold(bold)
            painter.setFont(font)
            alpha = 174 if self._partial else 255
            shadow_color = QColor(0, 0, 0, 210)
            text_color = _qcolor_from_hex(color, alpha)
            painter.setPen(shadow_color)
            painter.drawText(text_rect.translated(0, 2), text, option)
            painter.setPen(text_color)
            painter.drawText(text_rect, text, option)

    def _apply_text_shadow(self, label, *, blur_radius: int, y_offset: int) -> None:
        try:
            from PySide6.QtGui import QColor
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
        except ImportError as exc:
            raise OverlayError("PySide6 is required for text effects") from exc
        effect = QGraphicsDropShadowEffect(label)
        effect.setBlurRadius(blur_radius)
        effect.setOffset(0, y_offset)
        effect.setColor(QColor(0, 0, 0, 190))
        label.setGraphicsEffect(effect)

    def _animate_subtitle_update(self, previous_snapshot=None) -> None:
        duration = max(0, self.style.animation.fade_duration_ms)
        if duration <= 0:
            return
        QParallelAnimationGroup = self._qt["QParallelAnimationGroup"]
        QPropertyAnimation = self._qt["QPropertyAnimation"]
        QEasingCurve = self._qt["QEasingCurve"]
        QPoint = self._qt["QPoint"]
        QGraphicsOpacityEffect = self._qt["QGraphicsOpacityEffect"]

        start_position = self.content_widget.pos() + QPoint(0, self.style.animation.slide_offset_px)
        end_position = self.content_widget.pos()
        self.content_widget.move(start_position)
        self.opacity_effect.setOpacity(0.0)

        opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity", self.window)
        opacity_animation.setDuration(duration)
        opacity_animation.setStartValue(0.0)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        slide_animation = QPropertyAnimation(self.content_widget, b"pos", self.window)
        slide_animation.setDuration(duration)
        slide_animation.setStartValue(start_position)
        slide_animation.setEndValue(end_position)
        slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self.window)
        group.addAnimation(opacity_animation)
        group.addAnimation(slide_animation)
        snapshot_label = None
        if previous_snapshot is not None and not previous_snapshot.isNull():
            from PySide6.QtWidgets import QLabel

            snapshot_label = QLabel(self.window)
            snapshot_label.setPixmap(previous_snapshot)
            snapshot_label.setGeometry(self.content_widget.geometry())
            snapshot_label.show()
            snapshot_effect = QGraphicsOpacityEffect(snapshot_label)
            snapshot_effect.setOpacity(1.0)
            snapshot_label.setGraphicsEffect(snapshot_effect)
            snapshot_animation = QPropertyAnimation(snapshot_effect, b"opacity", self.window)
            snapshot_animation.setDuration(duration)
            snapshot_animation.setStartValue(1.0)
            snapshot_animation.setEndValue(0.0)
            snapshot_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            group.addAnimation(snapshot_animation)
        group.finished.connect(lambda: self.content_widget.move(end_position))
        if snapshot_label is not None:
            group.finished.connect(snapshot_label.deleteLater)
        self._current_animation = group
        group.start()

    def _set_drag_active(self, active: bool) -> None:
        self._drag_active = active
        self.window.update()

    def _set_partial_style(self, partial: bool) -> None:
        if partial:
            translation_color = _rgba_from_hex(self.style.translation_color, 0.68)
            source_color = _rgba_from_hex(self.style.source_color, 0.58)
        else:
            translation_color = self.style.translation_color
            source_color = self.style.source_color
        self.translation_label.setStyleSheet(f"color: {translation_color};")
        self.source_label.setStyleSheet(f"color: {source_color};")

    def _try_apply_native_effect(self) -> None:
        if self._native_effect_attempted:
            return
        if not self.style.native_effect.enabled or self.style.native_effect.effect == "none":
            return
        self._native_effect_attempted = True
        try:
            _apply_windows_backdrop(int(self.window.winId()), self.style.native_effect.effect)
        except Exception:
            return


def _panel_background_opacity(style: OverlayStyle) -> float:
    return style.glass.background_opacity if style.glass.enabled else style.background_opacity


def _qcolor_from_hex(color: str, alpha: int):
    from PySide6.QtGui import QColor

    red, green, blue = _hex_to_rgb(color)
    return QColor(red, green, blue, max(0, min(255, alpha)))


def _rgba_from_hex(color: str, opacity: float) -> str:
    red, green, blue = _hex_to_rgb(color)
    return f"rgba({red}, {green}, {blue}, {max(0.0, min(1.0, opacity)):.3f})"


def _translated_path(path, dx: int, dy: int):
    from PySide6.QtGui import QTransform

    return QTransform().translate(dx, dy).map(path)


def _apply_windows_backdrop(hwnd: int, effect: str) -> bool:
    import ctypes
    import sys
    from ctypes import wintypes

    backdrop_type = _native_backdrop_type(effect)
    if sys.platform != "win32" or backdrop_type is None:
        return False

    value = ctypes.c_int(backdrop_type)
    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmSetWindowAttribute.argtypes = [
        wintypes.HWND,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    dwmapi.DwmSetWindowAttribute.restype = wintypes.HRESULT
    result = dwmapi.DwmSetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(38),
        ctypes.byref(value),
        wintypes.DWORD(ctypes.sizeof(value)),
    )
    return result == 0


def _native_backdrop_type(effect: str) -> int | None:
    normalized = effect.strip().lower().replace("-", "_")
    if normalized in {"auto"}:
        return 1
    if normalized in {"mica", "main_window", "mainwindow"}:
        return 2
    if normalized in {"acrylic", "transient_window", "transientwindow"}:
        return 3
    if normalized in {"mica_alt", "tabbed_window", "tabbedwindow"}:
        return 4
    return None


def _alpha(opacity: float) -> int:
    return round(max(0.0, min(1.0, opacity)) * 255)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid #RRGGBB color: {color}")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
