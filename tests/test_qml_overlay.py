from __future__ import annotations

import pytest

from yt_live_translator.core.config import load_config
from yt_live_translator.ui.qml_overlay.qml_bridge import OverlayBridge
from yt_live_translator.ui.qml_overlay.qml_overlay_app import _qml_config_dict
from yt_live_translator.ui.qml_overlay.qml_resources import main_overlay_qml, qml_root


def test_qml_resource_paths_exist() -> None:
    assert qml_root().is_dir()
    assert main_overlay_qml().is_file()
    assert (qml_root() / "components" / "SubtitleBar.qml").is_file()
    assert (qml_root() / "components" / "ControlHubCard.qml").is_file()
    assert (qml_root() / "components" / "OptionPopoverCard.qml").is_file()
    assert (qml_root() / "components" / "GlassEdge.qml").is_file()
    assert (qml_root() / "components" / "GlassHighlight.qml").is_file()
    assert (qml_root() / "components" / "LiquidThumb.qml").is_file()
    assert (qml_root() / "components" / "TuningPanel.qml").is_file()


def test_overlay_bridge_uses_runtime_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    config = load_config()

    bridge = OverlayBridge.from_runtime_config(config)

    assert bridge.sourceLanguage == config.app.source_language
    assert bridge.targetLanguage == "zh-TW"
    assert bridge.asrModel == "models/faster-whisper-large-v3"
    assert bridge.deepseekModel == "deepseek-v4-flash"
    assert bridge.apiKeyStatus == "configured"
    assert bridge.showSource is True
    assert bridge.showTranslation is True


def test_overlay_bridge_updates_state_and_emits_signals() -> None:
    bridge = OverlayBridge.from_runtime_config(load_config())
    subtitle_events: list[bool] = []
    running_events: list[bool] = []
    settings_events: list[bool] = []
    bridge.subtitleChanged.connect(lambda: subtitle_events.append(True))
    bridge.runningChanged.connect(lambda: running_events.append(True))
    bridge.settingsChanged.connect(lambda: settings_events.append(True))

    bridge.update_subtitle("source", "translation", partial=True)
    bridge.startTranslation()
    bridge.setSourceLanguage("ja")
    bridge.setDeepseekModel("deepseek-v4-pro")
    bridge.setSubtitleOpacity(2.0)
    bridge.setCardOpacity(0.42)
    bridge.setCornerRadius(36)
    bridge.setEdgeWidth(4.0)
    bridge.setRgbShift(0.02)
    bridge.setShadowOpacity(0.25)
    bridge.setThumbMoveMs(260)
    bridge.setAnimationMs(220)
    bridge.stopTranslation()

    assert bridge.sourceText == "source"
    assert bridge.translatedText == "translation"
    assert bridge.isPartial is True
    assert bridge.isRunning is False
    assert bridge.sourceLanguage == "ja"
    assert bridge.deepseekModel == "deepseek-v4-pro"
    assert bridge.subtitleOpacity == 1.0
    assert bridge.cardOpacity == 0.42
    assert bridge.cornerRadius == 36
    assert bridge.edgeWidth == 4.0
    assert bridge.rgbShift == 0.02
    assert bridge.shadowOpacity == 0.25
    assert bridge.thumbMoveMs == 260
    assert bridge.animationMs == 220
    assert len(subtitle_events) >= 2
    assert len(running_events) == 2
    assert len(settings_events) >= 3


def test_qml_config_dict_uses_runtime_config() -> None:
    config = load_config()

    qml_config = _qml_config_dict(config)

    assert qml_config["width"] == config.qml_overlay.width
    assert qml_config["fontFamily"] == config.qml_overlay.subtitle.font_family
    assert qml_config["translationColor"] == config.qml_overlay.subtitle.translation_color
    assert qml_config["cardOpacity"] == config.qml_overlay.glass.card_background_opacity
    assert qml_config["edgeWidth"] == config.qml_overlay.glass.edge_width
    assert qml_config["rgbShift"] == config.qml_overlay.glass.rgb_shift
    assert qml_config["thumbMoveMs"] == config.qml_overlay.animation.thumb_move_ms
    assert qml_config["subtitleFadeMs"] == config.qml_overlay.animation.subtitle_fade_ms
    assert qml_config["tuningMode"] is False


def test_qml_config_dict_can_enable_tuning_mode() -> None:
    qml_config = _qml_config_dict(load_config(), tuning_mode=True)

    assert qml_config["tuningMode"] is True


def test_overlay_bridge_current_parameter_text_contains_toml_sections() -> None:
    bridge = OverlayBridge.from_runtime_config(load_config())
    bridge.setTranslationFontSize(34)
    bridge.setGlassIridescence(0.2)

    text = bridge.current_parameter_text()

    assert "[qml_overlay.subtitle]" in text
    assert "translation_font_size = 34" in text
    assert "[qml_overlay.glass]" in text
    assert "iridescence_opacity = 0.200" in text
    assert "edge_width =" in text
    assert "rgb_shift =" in text
    assert "thumb_move_ms =" in text
