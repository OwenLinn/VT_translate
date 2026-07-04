# Electron Overlay Design

The Electron overlay is a Phase 2 frontend prototype for Liquid Glass-inspired
subtitle visuals and tuning. It coexists with the Widgets and QML overlays.

Phase 2 mock/tuning mode does not connect to ASR, DeepSeek, glossary, audio
capture, or the live pipeline. Live mode uses a Python WebSocket bridge for the
real subtitle pipeline.

## Architecture

```text
Python CLI
  -> npm script
  -> Electron main process
  -> OverlayWindowManager
  -> multiple BrowserWindow surfaces
  -> secure preload API
  -> React renderer
  -> per-window React views
  -> mock events or ws://127.0.0.1:8765
```

The frontend lives under:

```text
frontend/electron-overlay/
```

Python launcher commands:

```powershell
python -m yt_live_translator.main --electron-overlay-test
python -m yt_live_translator.main --electron-overlay-tuning
python -m yt_live_translator.main --electron-overlay-live --continuous-loopback
```

These commands launch `npm run dev:mock`, `npm run dev:tuning`, or
`npm run dev:live`.

## Window Mode

Electron overlay defaults to multi-window mode:

```powershell
OVERLAY_WINDOW_MODE=multi
```

The old single transparent BrowserWindow prototype remains available as a
fallback:

```powershell
OVERLAY_WINDOW_MODE=single_legacy
```

Multi-window mode splits overlay UI into separate transparent BrowserWindows:

- `SubtitleWindow`: subtitle surface only
- `SettingsIconWindow`: compact settings trigger
- `ControlCardWindow`: status, Start/Stop, and setting rows
- `PopoverWindow`: option selections for the active row

This avoids making one large transparent hit-test surface cover the YouTube or
video player area.

## Security Boundary

Electron renderer security is required:

- `nodeIntegration: false`
- `contextIsolation: true`
- `sandbox: true`
- preload exposes only minimal overlay APIs
- renderer must not store or read API keys
- DeepSeek keys remain in Python process environment/config only

The preload currently exposes:

- `setInteractive(interactive: boolean)`
- `copyText(text: string)`

## Components

- `SubtitleBar.tsx`: glass subtitle display with partial/final animation
- `SettingsIconButton.tsx`: compact overlay control trigger
- `ControlHubCard.tsx`: mock Start/Stop, display, language, and model controls
- `OptionPopoverCard.tsx`: segmented option selection
- `GlassCard.tsx`: shared Liquid Glass-inspired material container
- `GlassEdge.tsx`: edge/refraction accent layer
- `GlassHighlight.tsx`: highlight and reflection layers
- `LiquidThumb.tsx`: spring animated segmented-control thumb
- `TuningPanel.tsx`: Phase 2 material and motion tuning surface

In multi-window mode the same React component library is reused, but
`App.tsx` renders by `?window=`:

- `index.html?window=subtitle`
- `index.html?window=settings-icon`
- `index.html?window=control-card`
- `index.html?window=popover`

The legacy single-window path renders the original combined layout when no
`window` query parameter is present.

The implementation uses React, TypeScript, Framer Motion, Zustand, and CSS
`backdrop-filter` layers. It does not copy WPF, C#, HLSL, QML, or shader code.

## Bridge Message Types

The Phase 3 bridge will use `ws://127.0.0.1:8765`.

Renderer-side TypeScript message contracts are defined in:

```text
frontend/electron-overlay/src/renderer/bridge/messageTypes.ts
```

Current event types:

- `SubtitleEvent`
- `StatusEvent`
- `SettingsEvent`
- `CommandMessage`

Phase 2 sends commands from controls but accepts that no backend is connected.
Mock events keep the UI animated and usable for tuning.

Live mode uses:

```text
Python pipeline
  -> ElectronOverlayBridge
  -> ws://127.0.0.1:8765
  -> Electron main BackendBridgeClient
  -> OverlayWindowManager
  -> BrowserWindow renderers
```

The Python bridge emits `SubtitleEvent`, `StatusEvent`, and `SettingsEvent`.
Electron sends `CommandMessage` for Start, Stop, language, display mode, and
DeepSeek model selection.

## Multi-Window IPC

Shared IPC contracts are defined in:

```text
frontend/electron-overlay/src/shared/overlayIpcTypes.ts
```

Renderer-to-main channels:

- `overlay:toggle-control-card`
- `overlay:open-control-card`
- `overlay:close-control-card`
- `overlay:open-popover`
- `overlay:close-popover`
- `overlay:escape`
- `overlay:setting-selected`
- `overlay:update-window-position`

Main-to-renderer channels:

- `overlay:state-updated`
- `overlay:position-updated`
- `overlay:popover-content`
- `overlay:subtitle-event`

In Phase 2, the Electron main process is the UI state source of truth for
multi-window mode. Each renderer receives snapshots and sends user intents
through preload IPC.

## Geometry

Window geometry lives in:

```text
frontend/electron-overlay/src/main/windows/windowGeometry.ts
```

Default sizes:

- subtitle: 900 x 108
- settings icon: 72 x 72
- control card: 420 x 252
- tuning control card: 460 x 660
- popover: 260 x 156

The subtitle window is the anchor. Moving the subtitle window repositions the
settings icon, control card, and popover while clamping them to the visible work
area.

Menus use bottom-aware placement. When the subtitle anchor is near the bottom of
the screen, the control card and popover shift upward instead of extending past
the work area. Popover height is selected by content type, and oversized control
surfaces can scroll inside their own BrowserWindow rather than being cut off.

## Tuning Presets

Presets are stored in:

```text
frontend/electron-overlay/src/renderer/presets/
```

Current presets:

- `cleanDark`
- `ultraCleanDark`
- `elegantGlass`
- `debugStrong`

Copy Parameters produces a TOML snippet for later manual config migration. It
does not save runtime config in Phase 2.

## Phase 2 Boundary

Allowed:

- visual material work
- motion tuning
- mock subtitles
- WebSocket client shape
- command message shape
- docs and tests

Not allowed until Phase 3:

- starting ASR workers from Electron
- calling DeepSeek from renderer
- reading API keys in renderer
- connecting real audio capture
- replacing Widgets or QML fallback overlays

## Live Boundary

Allowed:

- Python starts/stops the existing subtitle pipeline
- Python sends partial/final subtitle events to Electron
- Electron sends UI commands to Python
- Electron main updates window state and renderer snapshots

Still forbidden:

- reading API keys in renderer
- importing Python pipeline logic into Electron
- calling DeepSeek directly from renderer or Electron main

## Verification

Static Python tests validate the Electron scaffold without requiring npm
dependencies:

```powershell
pytest tests/test_electron_overlay.py
```

After npm dependencies are installed, run:

```powershell
cd frontend/electron-overlay
npm run typecheck
npm run build
npm run dev:mock
npm run dev:tuning
```
