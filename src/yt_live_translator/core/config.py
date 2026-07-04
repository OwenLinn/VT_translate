"""Runtime configuration loading for the application."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_live_translator.core.models import SourceLanguage, TargetLanguage


DEEPSEEK_MODELS = ("deepseek-v4-flash", "deepseek-v4-pro")


class ConfigError(ValueError):
    """Raised when runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    target_language: TargetLanguage
    source_language: SourceLanguage
    mode: str


@dataclass(frozen=True)
class UIConfig:
    overlay_frontend: str


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key_env: str
    model: str
    base_url: str
    timeout_seconds: float
    api_key: str | None = None


@dataclass(frozen=True)
class ASRConfig:
    backend: str
    model: str
    device: str
    compute_type: str
    beam_size: int


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int
    channels: int
    chunk_ms: int


@dataclass(frozen=True)
class VADConfig:
    threshold: float
    min_speech_ms: int
    max_speech_ms: int
    silence_end_ms: int
    padding_ms: int


@dataclass(frozen=True)
class StreamingLanguageConfig:
    asr_tick_ms: int
    min_commit_tokens: int
    max_commit_sec: float
    silence_end_ms: int


@dataclass(frozen=True)
class StreamingConfig:
    enabled: bool
    strategy: str
    asr_tick_ms: int
    rolling_window_sec: float
    overlap_sec: float
    local_agreement_n: int
    min_commit_sec: float
    max_commit_sec: float
    max_unconfirmed_sec: float
    enable_partial_subtitle: bool
    enable_final_revision: bool
    en: StreamingLanguageConfig
    ja: StreamingLanguageConfig


@dataclass(frozen=True)
class OverlayGlassConfig:
    enabled: bool
    corner_radius: int
    background_opacity: float
    border_opacity: float
    highlight_opacity: float
    shadow_opacity: float
    shadow_blur_radius: int
    noise_opacity: float


@dataclass(frozen=True)
class OverlayAnimationConfig:
    enabled: bool
    fade_duration_ms: int
    slide_offset_px: int
    drag_scale: float


@dataclass(frozen=True)
class OverlayNativeEffectConfig:
    enabled: bool
    effect: str


@dataclass(frozen=True)
class OverlayConfig:
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
    glass: OverlayGlassConfig
    animation: OverlayAnimationConfig
    native_effect: OverlayNativeEffectConfig


@dataclass(frozen=True)
class QmlOverlaySubtitleConfig:
    show_source: bool
    show_translation: bool
    translation_font_size: int
    source_font_size: int
    font_family: str
    translation_color: str
    source_color: str
    text_shadow_opacity: float
    max_translation_lines: int
    max_source_lines: int


@dataclass(frozen=True)
class QmlOverlayGlassConfig:
    enabled: bool
    subtitle_background_opacity: float
    card_background_opacity: float
    panel_tint_opacity: float
    corner_radius: int
    subtitle_corner_radius: int
    card_corner_radius: int
    edge_width: float
    edge_opacity: float
    edge_darkening: float
    distortion: float
    reflect_power: float
    border_opacity: float
    highlight_opacity: float
    top_highlight_height: float
    radial_highlight_opacity: float
    shadow_opacity: float
    shadow_radius: int
    shadow_y_offset: int
    iridescence_enabled: bool
    iridescence_opacity: float
    iridescence_width: float
    rgb_shift: float
    cyan_edge_opacity: float
    magenta_edge_opacity: float
    warm_edge_opacity: float
    noise_opacity: float


@dataclass(frozen=True)
class QmlOverlayAnimationConfig:
    enabled: bool
    subtitle_fade_ms: int
    card_open_ms: int
    card_close_ms: int
    popover_open_ms: int
    popover_close_ms: int
    slide_offset_px: int
    scale_from: float
    scale_to: float
    thumb_move_ms: int
    thumb_stretch_scale: float
    thumb_compress_scale: float


@dataclass(frozen=True)
class QmlOverlayConfig:
    width: int
    height: int
    x: int
    y: int
    always_on_top: bool
    frameless: bool
    transparent_background: bool
    show_settings_icon: bool
    subtitle: QmlOverlaySubtitleConfig
    glass: QmlOverlayGlassConfig
    animation: QmlOverlayAnimationConfig


@dataclass(frozen=True)
class StorageConfig:
    database_path: str
    subtitle_log_path: str


@dataclass(frozen=True)
class RuntimeConfig:
    app: AppConfig
    ui: UIConfig
    deepseek: DeepSeekConfig
    asr: ASRConfig
    audio: AudioConfig
    vad: VADConfig
    streaming: StreamingConfig
    overlay: OverlayConfig
    qml_overlay: QmlOverlayConfig
    storage: StorageConfig
    source_path: Path

    def resolve_deepseek_api_key(self) -> str | None:
        """Return the DeepSeek API key, preferring the configured environment variable."""

        env_value = os.environ.get(self.deepseek.api_key_env)
        if env_value:
            return env_value
        return self.deepseek.api_key


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_config(path: str | Path | None = None) -> RuntimeConfig:
    """Load `config.toml`, falling back to `config.example.toml` when absent."""

    root = project_root()
    requested_path = Path(path) if path is not None else root / "config.toml"
    if not requested_path.is_absolute():
        requested_path = root / requested_path

    source_path = requested_path
    if not source_path.exists():
        if path is not None:
            raise ConfigError(f"Config file not found: {source_path}")
        source_path = root / "config.example.toml"

    if not source_path.exists():
        raise ConfigError(f"No config file found at {requested_path} or {root / 'config.example.toml'}")

    try:
        with source_path.open("rb") as config_file:
            raw_config = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {source_path}: {exc}") from exc

    return parse_config(raw_config, source_path)


def parse_config(raw_config: dict[str, Any], source_path: Path) -> RuntimeConfig:
    app = _section(raw_config, "app")
    ui = _optional_section(raw_config, "ui")
    deepseek = _section(raw_config, "deepseek")
    asr = _section(raw_config, "asr")
    audio = _section(raw_config, "audio")
    vad = _section(raw_config, "vad")
    streaming = _optional_section(raw_config, "streaming")
    overlay = _section(raw_config, "overlay")
    overlay_glass = _optional_section(overlay, "glass")
    overlay_animation = _optional_section(overlay, "animation")
    overlay_native_effect = _optional_section(overlay, "native_effect")
    qml_overlay = _optional_section(raw_config, "qml_overlay")
    qml_overlay_subtitle = _optional_section(qml_overlay, "subtitle")
    qml_overlay_glass = _optional_section(qml_overlay, "glass")
    qml_overlay_animation = _optional_section(qml_overlay, "animation")
    storage = _section(raw_config, "storage")

    return RuntimeConfig(
        app=AppConfig(
            target_language=_target_language(_string(app, "target_language")),
            source_language=_source_language(_string(app, "source_language")),
            mode=_string(app, "mode"),
        ),
        ui=UIConfig(
            overlay_frontend=_overlay_frontend(_string_default(ui, "overlay_frontend", "widgets")),
        ),
        deepseek=DeepSeekConfig(
            api_key_env=_string(deepseek, "api_key_env"),
            model=_deepseek_model(_string(deepseek, "model")),
            base_url=_string(deepseek, "base_url"),
            timeout_seconds=_number(deepseek, "timeout_seconds"),
            api_key=_optional_string(deepseek, "api_key"),
        ),
        asr=ASRConfig(
            backend=_string(asr, "backend"),
            model=_string(asr, "model"),
            device=_string(asr, "device"),
            compute_type=_string(asr, "compute_type"),
            beam_size=_int(asr, "beam_size"),
        ),
        audio=AudioConfig(
            sample_rate=_int(audio, "sample_rate"),
            channels=_int(audio, "channels"),
            chunk_ms=_int(audio, "chunk_ms"),
        ),
        vad=VADConfig(
            threshold=_number(vad, "threshold"),
            min_speech_ms=_int(vad, "min_speech_ms"),
            max_speech_ms=_int(vad, "max_speech_ms"),
            silence_end_ms=_int(vad, "silence_end_ms"),
            padding_ms=_int(vad, "padding_ms"),
        ),
        streaming=StreamingConfig(
            enabled=_bool_default(streaming, "enabled", False),
            strategy=_streaming_strategy(_string_default(streaming, "strategy", "local_agreement")),
            asr_tick_ms=_int_default(streaming, "asr_tick_ms", 1000),
            rolling_window_sec=_number_default(streaming, "rolling_window_sec", 8.0),
            overlap_sec=_number_default(streaming, "overlap_sec", 1.0),
            local_agreement_n=_int_default(streaming, "local_agreement_n", 2),
            min_commit_sec=_number_default(streaming, "min_commit_sec", 1.2),
            max_commit_sec=_number_default(streaming, "max_commit_sec", 3.0),
            max_unconfirmed_sec=_number_default(streaming, "max_unconfirmed_sec", 4.0),
            enable_partial_subtitle=_bool_default(streaming, "enable_partial_subtitle", True),
            enable_final_revision=_bool_default(streaming, "enable_final_revision", True),
            en=_streaming_language_config(
                _optional_section(streaming, "en"),
                default_asr_tick_ms=800,
                default_min_commit_tokens=5,
                default_max_commit_sec=2.5,
                default_silence_end_ms=350,
            ),
            ja=_streaming_language_config(
                _optional_section(streaming, "ja"),
                default_asr_tick_ms=1000,
                default_min_commit_tokens=8,
                default_max_commit_sec=3.5,
                default_silence_end_ms=450,
            ),
        ),
        overlay=OverlayConfig(
            show_source=_bool(overlay, "show_source"),
            show_translation=_bool(overlay, "show_translation"),
            font_family=_string(overlay, "font_family"),
            translation_font_size=_int(overlay, "translation_font_size"),
            source_font_size=_int(overlay, "source_font_size"),
            translation_color=_string(overlay, "translation_color"),
            source_color=_string(overlay, "source_color"),
            background_color=_string(overlay, "background_color"),
            background_opacity=_number(overlay, "background_opacity"),
            always_on_top=_bool(overlay, "always_on_top"),
            glass=OverlayGlassConfig(
                enabled=_bool_default(overlay_glass, "enabled", False),
                corner_radius=_int_default(overlay_glass, "corner_radius", 28),
                background_opacity=_number_default(overlay_glass, "background_opacity", 0.52),
                border_opacity=_number_default(overlay_glass, "border_opacity", 0.35),
                highlight_opacity=_number_default(overlay_glass, "highlight_opacity", 0.28),
                shadow_opacity=_number_default(overlay_glass, "shadow_opacity", 0.32),
                shadow_blur_radius=_int_default(overlay_glass, "shadow_blur_radius", 32),
                noise_opacity=_number_default(overlay_glass, "noise_opacity", 0.025),
            ),
            animation=OverlayAnimationConfig(
                enabled=_bool_default(overlay_animation, "enabled", True),
                fade_duration_ms=_int_default(overlay_animation, "fade_duration_ms", 160),
                slide_offset_px=_int_default(overlay_animation, "slide_offset_px", 8),
                drag_scale=_number_default(overlay_animation, "drag_scale", 0.985),
            ),
            native_effect=OverlayNativeEffectConfig(
                enabled=_bool_default(overlay_native_effect, "enabled", False),
                effect=_string_default(overlay_native_effect, "effect", "none"),
            ),
        ),
        qml_overlay=QmlOverlayConfig(
            width=_int_default(qml_overlay, "width", 900),
            height=_int_default(qml_overlay, "height", 96),
            x=_int_default(qml_overlay, "x", 200),
            y=_int_default(qml_overlay, "y", 80),
            always_on_top=_bool_default(qml_overlay, "always_on_top", True),
            frameless=_bool_default(qml_overlay, "frameless", True),
            transparent_background=_bool_default(qml_overlay, "transparent_background", True),
            show_settings_icon=_bool_default(qml_overlay, "show_settings_icon", True),
            subtitle=QmlOverlaySubtitleConfig(
                show_source=_bool_default(
                    qml_overlay_subtitle,
                    "show_source",
                    _bool(overlay, "show_source"),
                ),
                show_translation=_bool_default(
                    qml_overlay_subtitle,
                    "show_translation",
                    _bool(overlay, "show_translation"),
                ),
                translation_font_size=_int_default(
                    qml_overlay_subtitle,
                    "translation_font_size",
                    _int(overlay, "translation_font_size"),
                ),
                source_font_size=_int_default(
                    qml_overlay_subtitle,
                    "source_font_size",
                    _int(overlay, "source_font_size"),
                ),
                font_family=_string_default(
                    qml_overlay_subtitle,
                    "font_family",
                    _string(overlay, "font_family"),
                ),
                translation_color=_string_default(
                    qml_overlay_subtitle,
                    "translation_color",
                    _string(overlay, "translation_color"),
                ),
                source_color=_string_default(
                    qml_overlay_subtitle,
                    "source_color",
                    _string(overlay, "source_color"),
                ),
                text_shadow_opacity=_number_default(
                    qml_overlay_subtitle,
                    "text_shadow_opacity",
                    0.55,
                ),
                max_translation_lines=_int_default(qml_overlay_subtitle, "max_translation_lines", 2),
                max_source_lines=_int_default(qml_overlay_subtitle, "max_source_lines", 1),
            ),
            glass=QmlOverlayGlassConfig(
                enabled=_bool_default(qml_overlay_glass, "enabled", True),
                subtitle_background_opacity=_number_default(
                    qml_overlay_glass,
                    "subtitle_background_opacity",
                    _number_default(overlay_glass, "background_opacity", 0.52),
                ),
                card_background_opacity=_number_default(
                    qml_overlay_glass,
                    "card_background_opacity",
                    0.46,
                ),
                panel_tint_opacity=_number_default(qml_overlay_glass, "panel_tint_opacity", 0.32),
                corner_radius=_int_default(
                    qml_overlay_glass,
                    "corner_radius",
                    _int_default(overlay_glass, "corner_radius", 28),
                ),
                subtitle_corner_radius=_int_default(qml_overlay_glass, "subtitle_corner_radius", 28),
                card_corner_radius=_int_default(qml_overlay_glass, "card_corner_radius", 30),
                edge_width=_number_default(qml_overlay_glass, "edge_width", 2.0),
                edge_opacity=_number_default(
                    qml_overlay_glass,
                    "edge_opacity",
                    _number_default(qml_overlay_glass, "border_opacity", 0.36),
                ),
                edge_darkening=_number_default(qml_overlay_glass, "edge_darkening", 0.08),
                distortion=_number_default(qml_overlay_glass, "distortion", 0.018),
                reflect_power=_number_default(qml_overlay_glass, "reflect_power", 0.28),
                border_opacity=_number_default(
                    qml_overlay_glass,
                    "border_opacity",
                    _number_default(overlay_glass, "border_opacity", 0.35),
                ),
                highlight_opacity=_number_default(
                    qml_overlay_glass,
                    "highlight_opacity",
                    _number_default(overlay_glass, "highlight_opacity", 0.28),
                ),
                top_highlight_height=_number_default(
                    qml_overlay_glass,
                    "top_highlight_height",
                    0.36,
                ),
                radial_highlight_opacity=_number_default(
                    qml_overlay_glass,
                    "radial_highlight_opacity",
                    0.18,
                ),
                shadow_opacity=_number_default(
                    qml_overlay_glass,
                    "shadow_opacity",
                    _number_default(overlay_glass, "shadow_opacity", 0.32),
                ),
                shadow_radius=_int_default(qml_overlay_glass, "shadow_radius", 28),
                shadow_y_offset=_int_default(qml_overlay_glass, "shadow_y_offset", 8),
                iridescence_enabled=_bool_default(qml_overlay_glass, "iridescence_enabled", True),
                iridescence_opacity=_number_default(
                    qml_overlay_glass,
                    "iridescence_opacity",
                    0.26,
                ),
                iridescence_width=_number_default(qml_overlay_glass, "iridescence_width", 2.0),
                rgb_shift=_number_default(qml_overlay_glass, "rgb_shift", 0.012),
                cyan_edge_opacity=_number_default(qml_overlay_glass, "cyan_edge_opacity", 0.22),
                magenta_edge_opacity=_number_default(
                    qml_overlay_glass,
                    "magenta_edge_opacity",
                    0.18,
                ),
                warm_edge_opacity=_number_default(qml_overlay_glass, "warm_edge_opacity", 0.12),
                noise_opacity=_number_default(qml_overlay_glass, "noise_opacity", 0.018),
            ),
            animation=QmlOverlayAnimationConfig(
                enabled=_bool_default(qml_overlay_animation, "enabled", True),
                subtitle_fade_ms=_int_default(qml_overlay_animation, "subtitle_fade_ms", 140),
                card_open_ms=_int_default(qml_overlay_animation, "card_open_ms", 180),
                card_close_ms=_int_default(qml_overlay_animation, "card_close_ms", 130),
                popover_open_ms=_int_default(qml_overlay_animation, "popover_open_ms", 160),
                popover_close_ms=_int_default(qml_overlay_animation, "popover_close_ms", 120),
                slide_offset_px=_int_default(qml_overlay_animation, "slide_offset_px", 12),
                scale_from=_number_default(qml_overlay_animation, "scale_from", 0.965),
                scale_to=_number_default(qml_overlay_animation, "scale_to", 1.0),
                thumb_move_ms=_int_default(qml_overlay_animation, "thumb_move_ms", 220),
                thumb_stretch_scale=_number_default(
                    qml_overlay_animation,
                    "thumb_stretch_scale",
                    1.10,
                ),
                thumb_compress_scale=_number_default(
                    qml_overlay_animation,
                    "thumb_compress_scale",
                    0.96,
                ),
            ),
        ),
        storage=StorageConfig(
            database_path=_string(storage, "database_path"),
            subtitle_log_path=_string(storage, "subtitle_log_path"),
        ),
        source_path=source_path,
    )


def _section(raw_config: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw_config.get(name)
    if not isinstance(value, dict):
        raise ConfigError(f"Missing [{name}] section")
    return value


def _optional_section(raw_config: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw_config.get(name)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"Invalid [{name}] section")
    return value


def _string(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"Missing or invalid string config value: {key}")
    return value


def _string_default(section: dict[str, Any], key: str, default: str) -> str:
    value = section.get(key, default)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"Invalid string config value: {key}")
    return value


def _optional_string(section: dict[str, Any], key: str) -> str | None:
    value = section.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"Invalid string config value: {key}")
    return value


def _int_default(section: dict[str, Any], key: str, default: int) -> int:
    value = section.get(key, default)
    if not isinstance(value, int):
        raise ConfigError(f"Invalid integer config value: {key}")
    return value


def _int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"Missing or invalid integer config value: {key}")
    return value


def _number_default(section: dict[str, Any], key: str, default: float) -> float:
    value = section.get(key, default)
    if not isinstance(value, int | float):
        raise ConfigError(f"Invalid numeric config value: {key}")
    return float(value)


def _number(section: dict[str, Any], key: str) -> float:
    value = section.get(key)
    if not isinstance(value, int | float):
        raise ConfigError(f"Missing or invalid numeric config value: {key}")
    return float(value)


def _bool_default(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"Invalid boolean config value: {key}")
    return value


def _bool(section: dict[str, Any], key: str) -> bool:
    value = section.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"Missing or invalid boolean config value: {key}")
    return value


def _target_language(value: str) -> TargetLanguage:
    if value not in ("zh-TW", "zh-CN"):
        raise ConfigError("target_language must be zh-TW or zh-CN")
    return value


def _source_language(value: str) -> SourceLanguage:
    if value not in ("auto", "en", "ja"):
        raise ConfigError("source_language must be auto, en, or ja")
    return value


def _deepseek_model(value: str) -> str:
    if value not in DEEPSEEK_MODELS:
        allowed = ", ".join(DEEPSEEK_MODELS)
        raise ConfigError(f"deepseek.model must be one of: {allowed}")
    return value


def _overlay_frontend(value: str) -> str:
    if value not in ("widgets", "qml"):
        raise ConfigError("ui.overlay_frontend must be widgets or qml")
    return value


def _streaming_strategy(value: str) -> str:
    if value != "local_agreement":
        raise ConfigError("streaming.strategy must be local_agreement")
    return value


def _streaming_language_config(
    section: dict[str, Any],
    *,
    default_asr_tick_ms: int,
    default_min_commit_tokens: int,
    default_max_commit_sec: float,
    default_silence_end_ms: int,
) -> StreamingLanguageConfig:
    return StreamingLanguageConfig(
        asr_tick_ms=_int_default(section, "asr_tick_ms", default_asr_tick_ms),
        min_commit_tokens=_int_default(section, "min_commit_tokens", default_min_commit_tokens),
        max_commit_sec=_number_default(section, "max_commit_sec", default_max_commit_sec),
        silence_end_ms=_int_default(section, "silence_end_ms", default_silence_end_ms),
    )
