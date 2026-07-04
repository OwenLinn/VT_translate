# AGENTS.md

## Project Name

YouTube Live Translator Overlay

## Project Goal

Build a Windows desktop tool that captures system audio from YouTube livestreams,
performs local ASR for English/Japanese, translates subtitles into Traditional or
Simplified Chinese, and displays them in a draggable always-on-top subtitle
overlay.

## Required Workflow

1. Read all files in `docs/` before modifying code.
2. Check `dev_logs/todo.md` before starting a task.
3. After completing a task, update:
   - `dev_logs/completed.md`
   - `dev_logs/todo.md`
   - `dev_logs/daily_log.md`
4. If a design decision is made, update:
   - `dev_logs/decisions.md`
5. If a bug or unresolved problem is found, update:
   - `dev_logs/issues.md`
6. Do not implement later-stage features before earlier-stage tests pass.
7. Do not remove or rewrite existing files unless necessary.
8. Keep code modular and testable.
9. Prioritize real-time performance and translation quality.
10. Do not hard-code API keys.

## Documentation Paths

- Project overview: `docs/00_project_overview.md`
- Requirements: `docs/01_requirements.md`
- Technical design: `docs/02_technical_design.md`
- Development plan: `docs/03_development_plan.md`
- Testing standard: `docs/04_testing_standard.md`
- UI design standard: `docs/05_ui_design_standard.md`
- Glossary design: `docs/06_glossary_design.md`
- Runtime config: `docs/07_runtime_config.md`
- Packaging notes: `docs/08_packaging_notes.md`
- QML overlay design: `docs/09_qml_overlay_design.md`
- Electron overlay design: `docs/10_electron_overlay_design.md`

## QML Overlay Development Rule

The project now supports a QML-based overlay frontend.

Before editing QML overlay code, read:

- `docs/09_qml_overlay_design.md`
- `docs/05_ui_design_standard.md`
- `docs/07_runtime_config.md`

Do not rewrite the ASR, translation, glossary, or subtitle pipeline when
working on QML UI tasks.

QML UI should communicate with Python only through `OverlayBridge`.

The old Widgets overlay must remain available as fallback until the user
confirms QML overlay is stable.

## Electron Overlay Rule

The project now has an Electron-based overlay frontend under:

`frontend/electron-overlay/`

When working on Electron overlay tasks:

1. Do not modify ASR, translation, glossary, or audio pipeline unless
   explicitly requested.
2. Keep Python backend and Electron frontend separated.
3. Use WebSocket message types defined in the Electron bridge.
4. Keep Electron renderer secure:
   - `nodeIntegration: false`
   - `contextIsolation: true`
   - `sandbox: true`
   - use preload for minimal APIs
5. Do not store API keys in renderer code.
6. Keep Widgets and QML overlays as fallback until Electron overlay is
   confirmed stable.
7. Phase 2 is visual and interaction prototype only.
8. Do not connect real pipeline until Phase 3.

## Development Logs

- Completed work: `dev_logs/completed.md`
- Todo list: `dev_logs/todo.md`
- Technical decisions: `dev_logs/decisions.md`
- Known issues: `dev_logs/issues.md`
- Daily development log: `dev_logs/daily_log.md`

## Stage Rule

This project must be developed stage by stage.

Do not proceed to the next stage until the current stage:

- runs successfully,
- has smoke tests,
- updates documentation,
- updates development logs.

## Current Priority

Start with Stage 0 and Stage 1 only:

- project scaffold
- config loading
- logging
- terminal-based smoke tests
- DeepSeek translation smoke test

Do not start UI or full pipeline before Stage 1 passes.
