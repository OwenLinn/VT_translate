# Runtime Config

Use TOML for runtime config.

Example:

```toml
[app]
target_language = "zh-TW"
source_language = "auto"
mode = "balanced"

[ui]
overlay_frontend = "qml"

[deepseek]
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-flash"
timeout_seconds = 10

[asr]
backend = "faster-whisper"
model = "models/faster-whisper-large-v3"
device = "cuda"
compute_type = "float16"
beam_size = 3

[audio]
sample_rate = 16000
channels = 1
chunk_ms = 30

[vad]
threshold = 0.5
min_speech_ms = 1200
max_speech_ms = 5000
silence_end_ms = 700
padding_ms = 400

[streaming]
enabled = true
strategy = "local_agreement"
asr_tick_ms = 1000
rolling_window_sec = 8
overlap_sec = 1.0
local_agreement_n = 2
min_commit_sec = 1.2
max_commit_sec = 3.0
max_unconfirmed_sec = 4.0
enable_partial_subtitle = true
enable_final_revision = true

[streaming.en]
asr_tick_ms = 800
min_commit_tokens = 5
max_commit_sec = 2.5
silence_end_ms = 350

[streaming.ja]
asr_tick_ms = 1000
min_commit_tokens = 8
max_commit_sec = 3.5
silence_end_ms = 450

[overlay]
show_source = true
show_translation = true
font_family = "Microsoft JhengHei"
translation_font_size = 32
source_font_size = 20
translation_color = "#FFFFFF"
source_color = "#DDDDDD"
background_color = "#000000"
background_opacity = 0.55
always_on_top = true

[overlay.glass]
enabled = true
corner_radius = 28
background_opacity = 0.52
border_opacity = 0.35
highlight_opacity = 0.28
shadow_opacity = 0.32
shadow_blur_radius = 32
noise_opacity = 0.025

[overlay.animation]
enabled = true
fade_duration_ms = 160
slide_offset_px = 8
drag_scale = 0.985

[overlay.native_effect]
enabled = false
effect = "none"

[qml_overlay]
width = 900
height = 96
x = 200
y = 80
always_on_top = true
frameless = true
transparent_background = true
show_settings_icon = true

[qml_overlay.subtitle]
show_source = true
show_translation = true
translation_font_size = 30
source_font_size = 18
font_family = "Microsoft JhengHei"
translation_color = "#FFFFFF"
source_color = "#D8D8D8"
text_shadow_opacity = 0.55
max_translation_lines = 2
max_source_lines = 1

[qml_overlay.glass]
enabled = true
subtitle_background_opacity = 0.58
card_background_opacity = 0.46
panel_tint_opacity = 0.32
corner_radius = 28
subtitle_corner_radius = 28
card_corner_radius = 30
edge_width = 2.0
edge_opacity = 0.36
edge_darkening = 0.08
distortion = 0.018
reflect_power = 0.28
border_opacity = 0.36
highlight_opacity = 0.30
top_highlight_height = 0.36
radial_highlight_opacity = 0.18
shadow_opacity = 0.30
shadow_radius = 28
shadow_y_offset = 8
iridescence_enabled = true
iridescence_opacity = 0.26
iridescence_width = 2.0
rgb_shift = 0.012
cyan_edge_opacity = 0.22
magenta_edge_opacity = 0.18
warm_edge_opacity = 0.12
noise_opacity = 0.018

[qml_overlay.animation]
enabled = true
subtitle_fade_ms = 140
card_open_ms = 180
card_close_ms = 130
popover_open_ms = 160
popover_close_ms = 120
slide_offset_px = 12
scale_from = 0.965
scale_to = 1.0
thumb_move_ms = 220
thumb_stretch_scale = 1.10
thumb_compress_scale = 0.96
```

Do not commit real API keys.

## Streaming

`streaming.strategy = "local_agreement"` enables the low-latency rolling-window
path. The ASR runner ticks every `asr_tick_ms`, compares the last
`local_agreement_n` hypotheses, commits only stable prefixes, and keeps the
unstable tail as partial subtitle text.

When `streaming.enabled = true`, terminal and overlay pipeline commands use the
configured streaming strategy by default. Pass `--streaming-strategy
fixed_segments` to fall back to the older VAD segment path for comparison.

Use `[streaming.en]` and `[streaming.ja]` to tune language-specific commit
thresholds. English uses word-token prefix matching; Japanese and auto-detected
Japanese text use character-prefix matching.

`enable_partial_subtitle` controls partial subtitle events. `enable_final_revision`
controls whether final subtitles are translated again from the full finalized
source sentence.

## Overlay Style

`overlay.glass.enabled` enables the custom soft glass subtitle panel. It is a
PySide6-painted fallback-friendly style, not an official Apple material. Set it
to `false` or run the overlay smoke test with `--style classic` to use the
classic semi-transparent panel.

`overlay.animation.enabled` controls short fade/slide subtitle updates and the
small drag feedback scale. Set it to `false` if animation should be disabled.

`overlay.native_effect` is reserved for optional Windows Acrylic/Mica
experiments. It remains disabled by default and must not block the Basic Glass
overlay from working. Supported experimental `effect` values are `none`,
`mica`, `acrylic`, and `mica-alt`.

## QML Overlay

`ui.overlay_frontend` can be `widgets` or `qml`. The current Phase 1 QML command
is `--qml-overlay-test`; it opens a placeholder overlay shell and does not
connect to ASR or translation.

`[qml_overlay]` controls the QML window size, placement, topmost behavior,
transparency, subtitle text styling, and basic glass parameters. These settings
are intentionally separate from `[overlay]` so the Widgets fallback remains
stable while QML is being developed.

`--qml-overlay-tuning` opens the Phase 2 visual tuning UI. It updates QML state
through `OverlayBridge` only and does not save settings yet. Use Copy current
parameters to produce a TOML snippet that can be manually moved into config.

Phase 2 material parameters are inspired by lens/glass shader concepts, but the
current implementation uses Qt Quick gradients and animations only. It does not
sample the real desktop/video background and does not require shader build
steps.

## Electron Overlay

The Electron overlay prototype is stored under `frontend/electron-overlay`.
Phase 2 commands are:

```powershell
python -m yt_live_translator.main --electron-overlay-test
python -m yt_live_translator.main --electron-overlay-tuning
```

Electron Phase 2 currently keeps visual parameters in frontend Zustand state
and preset files. Copy Parameters emits an `[electron_overlay.glass]` TOML
snippet for manual migration, but settings are not persisted automatically.

The reserved backend bridge is `ws://127.0.0.1:8765`. Until Phase 3, the
renderer uses mock subtitle/status events and must not read API keys or start
pipeline workers.

Live Electron mode is launched with:

```powershell
python -m yt_live_translator.main --electron-overlay-live --continuous-loopback
```

The Python process starts the WebSocket bridge and owns the real pipeline.
Electron connects to `OVERLAY_BRIDGE_URL` and does not read API keys.

`OVERLAY_WINDOW_MODE` controls the Electron overlay window layout:

- `multi`: default, separate BrowserWindows for subtitle, settings icon,
  control card, and popover
- `single_legacy`: original single transparent BrowserWindow prototype

## DeepSeek Model Selection

`deepseek.model` must be one of:

- `deepseek-v4-flash`
- `deepseek-v4-pro`

Use `deepseek-v4-flash` by default for lower latency. Use `deepseek-v4-pro`
when translation quality is more important than speed.
