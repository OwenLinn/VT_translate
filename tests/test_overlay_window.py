from __future__ import annotations

import pytest

from yt_live_translator.core.config import (
    OverlayAnimationConfig,
    OverlayConfig,
    OverlayGlassConfig,
    OverlayNativeEffectConfig,
)
from yt_live_translator.ui.overlay_window import (
    AnimationStyle,
    GlassStyle,
    OverlayStyle,
    background_rgba,
    build_overlay_stylesheet,
    style_from_config,
    style_with_mode,
    _native_backdrop_type,
    _rgba_from_hex,
)


def test_style_from_config_maps_overlay_fields() -> None:
    config = OverlayConfig(
        show_source=True,
        show_translation=False,
        font_family="Microsoft JhengHei",
        translation_font_size=32,
        source_font_size=20,
        translation_color="#FFFFFF",
        source_color="#DDDDDD",
        background_color="#000000",
        background_opacity=0.55,
        always_on_top=True,
        glass=OverlayGlassConfig(
            enabled=True,
            corner_radius=28,
            background_opacity=0.52,
            border_opacity=0.35,
            highlight_opacity=0.28,
            shadow_opacity=0.32,
            shadow_blur_radius=32,
            noise_opacity=0.025,
        ),
        animation=OverlayAnimationConfig(
            enabled=True,
            fade_duration_ms=160,
            slide_offset_px=8,
            drag_scale=0.985,
        ),
        native_effect=OverlayNativeEffectConfig(enabled=False, effect="none"),
    )

    style = style_from_config(config)

    assert style.show_source is True
    assert style.show_translation is False
    assert style.font_family == "Microsoft JhengHei"
    assert style.background_opacity == 0.55
    assert style.glass.enabled is True
    assert style.glass.corner_radius == 28
    assert style.animation.fade_duration_ms == 160


def test_build_overlay_stylesheet_uses_configured_colors_and_fonts() -> None:
    style = OverlayStyle(
        show_source=True,
        show_translation=True,
        font_family="Test Font",
        translation_font_size=30,
        source_font_size=18,
        translation_color="#ABCDEF",
        source_color="#123456",
        background_color="#010203",
        background_opacity=0.5,
        always_on_top=True,
        glass=GlassStyle(enabled=False),
    )

    stylesheet = build_overlay_stylesheet(style)

    assert "rgba(1, 2, 3, 0.500)" in stylesheet
    assert "#ABCDEF" in stylesheet
    assert "#123456" in stylesheet
    assert 'font-family: "Test Font"' in stylesheet
    assert "font-size: 30px" in stylesheet


def test_glass_stylesheet_uses_transparent_root_and_corner_radius() -> None:
    style = OverlayStyle(
        show_source=True,
        show_translation=True,
        font_family="Test Font",
        translation_font_size=30,
        source_font_size=18,
        translation_color="#ABCDEF",
        source_color="#123456",
        background_color="#010203",
        background_opacity=0.5,
        always_on_top=True,
        glass=GlassStyle(enabled=True, corner_radius=28, background_opacity=0.52),
        animation=AnimationStyle(enabled=False),
    )

    stylesheet = build_overlay_stylesheet(style)

    assert "background-color: transparent" in stylesheet
    assert "border-radius: 28px" in stylesheet
    assert background_rgba(style) == "rgba(1, 2, 3, 0.520)"


def test_style_with_mode_can_force_glass_or_classic() -> None:
    style = OverlayStyle(
        show_source=True,
        show_translation=True,
        font_family="Test",
        translation_font_size=30,
        source_font_size=18,
        translation_color="#FFFFFF",
        source_color="#DDDDDD",
        background_color="#000000",
        background_opacity=0.5,
        always_on_top=True,
        glass=GlassStyle(enabled=False),
    )

    assert style_with_mode(style, "glass").glass.enabled is True
    assert style_with_mode(style, "classic").glass.enabled is False


def test_native_backdrop_type_maps_supported_experimental_effects() -> None:
    assert _native_backdrop_type("mica") == 2
    assert _native_backdrop_type("acrylic") == 3
    assert _native_backdrop_type("mica-alt") == 4
    assert _native_backdrop_type("none") is None


def test_partial_rgba_color_is_translucent() -> None:
    assert _rgba_from_hex("#FFFFFF", 0.68) == "rgba(255, 255, 255, 0.680)"


def test_background_rgba_rejects_invalid_color() -> None:
    style = OverlayStyle(
        show_source=True,
        show_translation=True,
        font_family="Test",
        translation_font_size=30,
        source_font_size=18,
        translation_color="#FFFFFF",
        source_color="#DDDDDD",
        background_color="black",
        background_opacity=0.5,
        always_on_top=True,
    )

    with pytest.raises(ValueError, match="Invalid"):
        background_rgba(style)
