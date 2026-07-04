# QML Overlay Design

The QML frontend is a Liquid Glass-inspired overlay shell built on Qt Quick.
It coexists with the existing PySide6 Widgets overlay, which remains the
fallback until QML is proven stable in live use.

## Architecture

```text
Python runtime config
  -> OverlayBridge QObject
  -> QQmlApplicationEngine
  -> MainOverlay.qml
  -> QML components
```

QML communicates with Python only through `OverlayBridge`.

Phase 1 and Phase 2 do not call the ASR, translation, glossary, or subtitle
pipeline. They use placeholder subtitle data and UI-only Start/Stop state.

## Phase 1 Components

- `MainOverlay.qml`: top-level transparent overlay window
- `SubtitleBar.qml`: subtitle display surface
- `SettingsIconButton.qml`: compact settings button
- `ControlHubCard.qml`: status, Start/Stop, and settings rows
- `OptionPopoverCard.qml`: row-driven option selection
- `SettingRow.qml`: reusable label/value row
- `PillButton.qml`: compact command button
- `StatusBadge.qml`: running/stopped badge
- `GlassCard.qml`: shared translucent rounded panel

## Phase 2 Components

- `TuningControls.qml`: visual tuning controls for opacity, iridescence, corner
  radius, shadow, highlight, font size, and animation duration
- `TuningPanel.qml`: expanded Phase 2 material tuning panel
- `GlassEdge.qml`: gradient-based edge, RGB split, edge darkening, and
  iridescence accent layer
- `GlassHighlight.qml`: top linear highlight, radial corner glow, and bottom
  reflection layer
- `LiquidThumb.qml`: segmented-control thumb with stretch, move, compress, and
  settle animation
- `GlassSlider.qml`: compact glass-themed slider control
- `GlassTheme.qml`: shared design-token holder for later theme consolidation

Phase 2 expands `OverlayBridge` with runtime visual parameters. QML sliders
call bridge setter slots, and bound QML properties update immediately.

The Copy current parameters button writes a TOML snippet to the clipboard when
available and prints the same snippet to stdout.

## WpfGlassMenu Reference Summary

The WpfGlassMenu archive was used only as a visual and algorithmic reference.
No WPF, C#, compiled shader, or HLSL code was copied into this project.

Reference ideas translated into QML concepts:

- Lens parameters: edge width, distortion, reflect power, RGB shift, object
  size, and shape mode become QML tuning parameters.
- Glass surface layering: background tint, inner darkening, highlight, border,
  iridescent edge, and shadow become separate QML layers.
- Edge treatment: shader-style RGB offset is approximated with cyan/magenta
  gradient borders in `GlassEdge.qml`.
- Highlight treatment: top linear shine, radial corner glow, and bottom
  reflection are implemented in `GlassHighlight.qml`.
- Selection thumb motion: the original stretch/move/compress idea is
  reimplemented as a compact QML `LiquidThumb` animation.

Phase 2 does not sample the real YouTube/window background and does not ship a
shader. The current implementation is a QML gradient fallback designed for
manual visual tuning.

## Phase 2 Material Parameters

Pending user confirmation:

- `subtitle_background_opacity`
- `card_background_opacity`
- `panel_tint_opacity`
- `edge_width`
- `edge_opacity`
- `edge_darkening`
- `distortion`
- `reflect_power`
- `rgb_shift`
- `cyan_edge_opacity`
- `magenta_edge_opacity`
- `warm_edge_opacity`
- `highlight_opacity`
- `top_highlight_height`
- `radial_highlight_opacity`
- `shadow_opacity`
- `shadow_radius`
- `shadow_y_offset`
- `thumb_move_ms`
- `thumb_stretch_scale`
- `thumb_compress_scale`

## Phase 1 CLI

```powershell
python -m yt_live_translator.main --qml-overlay-test
```

For automated smoke testing:

```powershell
python -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 3
```

## Phase 2 CLI

```powershell
python -m yt_live_translator.main --qml-overlay-tuning
```

For automated smoke testing:

```powershell
python -m yt_live_translator.main --qml-overlay-tuning --qml-overlay-tuning-seconds 3
```

## Development Rules

- Keep Widgets overlay fallback available.
- Keep QML UI separate from pipeline internals.
- Use `OverlayBridge` for all Python/QML state transfer.
- Do not expose API keys to QML.
- Do not implement shader-only effects unless they have a fallback path.
- Do not implement Phase 3 pipeline integration in Phase 1 or Phase 2.
