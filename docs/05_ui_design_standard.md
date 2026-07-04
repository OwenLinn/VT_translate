# UI Design Standard

## Overlay Window

The subtitle overlay should be simple and non-intrusive.

Required behavior:

- Always on top
- Frameless or minimal frame
- Draggable by mouse
- Resizable in later stage
- Lock position in later stage
- Transparent or semi-transparent background
- Text must remain readable on bright and dark video backgrounds

## Default Style

- Background: black
- Background opacity: 55%
- Translation font size: 32
- Source font size: 20
- Translation color: white
- Source color: light gray
- Max lines: 2 translation lines
- Text alignment: center

## Soft Glass Overlay

The optional glass overlay is Liquid Glass-inspired but remains a custom PySide6
painted style. Do not describe it as an official Apple material.

Required behavior:

- Keep PySide6 as the UI framework
- Render a rounded translucent panel with soft shadow, subtle border, top
  highlight, and readable text shadow
- Keep `classic` mode available for lower-risk fallback
- Allow glass to be disabled from config or the overlay test CLI
- Animate subtitle changes with short fade and slide transitions when enabled
- Keep animations optional so slower machines can turn them off
- Treat native Acrylic/Mica experiments as off-by-default and non-blocking

## QML Liquid Glass-Inspired Overlay

The QML frontend is a Liquid Glass-inspired interface, not an official Apple
material. It should feel translucent, soft, and readable while keeping controls
compact enough for livestream viewing.

Required Phase 1 behavior:

- Subtitle bar with settings icon
- Settings icon opens a glass control hub
- Control hub rows open option popovers
- Start/Stop buttons update UI state only until pipeline integration
- Keep text readable over bright and dark video
- Keep the Widgets overlay as fallback

Required Phase 2 behavior:

- Use layered translucent cards with highlight, soft shadow, border, and subtle
  iridescence accents
- Approximate edge refraction and RGB split with QML gradient layers when no
  shader is available
- Animate hover, press, card open/close, and subtitle text changes with short
  durations
- Use a liquid thumb animation for segmented choices and Start/Stop state
- Provide a tuning mode for visual parameters
- Keep tuning mode separate from live ASR/translation pipeline execution

## Electron Liquid Glass-Inspired Overlay

The Electron frontend is also a Liquid Glass-inspired interface, not an
official Apple material. It is used for React/CSS motion and material tuning
experiments while Widgets and QML remain available as fallback frontends.

Required Phase 2 behavior:

- Transparent always-on-top Electron window
- Multi-window composition by default so invisible transparent UI does not
  block YouTube/player clicks
- Subtitle bar with compact settings icon
- Glass control hub and option popover
- Framer Motion open/close and subtitle update animation
- Zustand state for mock subtitle/status/settings data
- Tuning mode with presets, sliders, and Copy Parameters
- WebSocket message types prepared for Phase 3
- No real ASR, DeepSeek, glossary, or audio pipeline calls

Security requirements:

- Renderer must run with `nodeIntegration: false`
- Renderer must run with `contextIsolation: true`
- Renderer must run with `sandbox: true`
- Use preload only for minimal window/clipboard APIs
- Never store API keys in renderer code

Multi-window interaction requirements:

- Subtitle window is the geometry anchor
- Settings icon follows the subtitle window
- Control card opens beside the settings icon
- Popover opens beside the control card row that requested it
- Menus must stay inside the visible work area when the overlay is near the
  bottom of the screen
- Oversized tuning/control content may scroll inside its own window instead of
  being clipped
- ESC closes popover first, then the control card
- `single_legacy` mode remains available as fallback

## Display Modes

- Translation only
- Source + translation
- Source only for debugging

## Interaction

MVP interactions:

- Drag window
- Right-click menu or settings window
- Start/stop translation
- Show/hide source text
- Adjust font size
- Adjust opacity

Avoid:

- Complex professional subtitle editor UI
- Too many controls in MVP
