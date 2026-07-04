# Development Plan

Development must proceed by stages.

## Stage 0: Project Scaffold

Goal:
Create project structure, documentation, development logs, config example, and
basic Python package layout.

Must complete:

- Create folders
- Create AGENTS.md
- Create docs
- Create dev_logs
- Create src package
- Create tests folder
- Create scripts folder
- Create requirements.txt
- Create pyproject.toml
- Create config.example.toml

Pass condition:

- Project imports successfully
- `python -m yt_live_translator.main --help` runs or prints a basic message
- dev logs updated

## Stage 1: Config, Logging, and Translation Smoke Test

Goal:
Create minimal config loading, logging, and DeepSeek translation call.

Must complete:

- Load config from `config.toml`
- Fallback to `config.example.toml` if needed
- Read DeepSeek API key from environment variable or config
- Implement `deepseek_client.py`
- Implement `prompt_builder.py`
- Implement `scripts/smoke_translate.py`

Pass condition:

- A test sentence can be translated into Traditional Chinese
- A test sentence can be translated into Simplified Chinese
- API key is not hard-coded
- Error messages are clear
- dev logs updated

## Stage 2: Audio Capture Smoke Test

Goal:
Capture Windows system audio using WASAPI loopback.

Must complete:

- Implement `audio/wasapi_capture.py`
- Implement `audio/resampler.py`
- Implement `scripts/smoke_audio_capture.py`
- Save 10 seconds of captured audio as WAV for manual verification

Pass condition:

- Script detects audio output devices
- Script captures speaker output
- WAV file can be played back
- No crash when no audio is playing
- dev logs updated

## Stage 3: ASR File Smoke Test

Goal:
Run faster-whisper on a local audio file.

Must complete:

- Implement `speech/asr_faster_whisper.py`
- Implement `scripts/smoke_asr_file.py`
- Support language parameter: en, ja, auto
- Support model size setting

Pass condition:

- English audio file can be transcribed
- Japanese audio file can be transcribed
- GPU mode works if CUDA is available
- CPU fallback works or gives clear warning
- dev logs updated

## Stage 4: Terminal Real-Time Pipeline

Goal:
Connect audio capture, VAD, ASR, translation, and terminal output.

Must complete:

- Implement `speech/vad.py`
- Implement `speech/segmenter.py`
- Implement `core/task_queue.py`
- Implement `core/subtitle_pipeline.py`
- Implement `scripts/smoke_pipeline_terminal.py`
- Add low-latency `local_agreement` streaming mode with rolling audio buffer,
  partial subtitle events, and final subtitle rewrites

Pass condition:

- While YouTube audio is playing, terminal prints segment id, source text,
  translated text, and latency estimate
- In streaming mode terminal prints `[PARTIAL]` and `[FINAL]` source,
  translation, and latency blocks
- English livestream audio works
- Japanese livestream audio works
- Average delay is acceptable for manual testing
- dev logs updated

## Stage 5: Basic Overlay Window

Goal:
Display translated subtitle in an always-on-top draggable window.

Must complete:

- Implement `ui/overlay_window.py`
- Support always-on-top
- Support dragging
- Support font size
- Support font color
- Support background opacity
- Support show/hide source text
- Support show/hide translation

Pass condition:

- Overlay appears above browser
- Overlay can be dragged
- Subtitle text updates from test data
- Settings can be loaded from config
- dev logs updated

## Stage 6: Real-Time Overlay Pipeline

Goal:
Connect the real-time pipeline to the overlay UI.

Must complete:

- Main app starts pipeline and overlay
- Subtitle display queue updates UI
- UI does not freeze during ASR or translation
- App can start/stop translation
- Overlay can display lower-confidence partial subtitles and replace them with
  final subtitles without obvious flicker

Pass condition:

- YouTube livestream audio results appear in overlay
- UI remains responsive
- Start/stop works
- `--streaming-strategy local_agreement` works with the overlay pipeline
- dev logs updated

## Stage 7: Manual Glossary

Goal:
Add glossary support for names and game terms.

Must complete:

- Implement SQLite database
- Implement glossary table
- Implement `glossary_repo.py`
- Implement `glossary_apply.py`
- Implement glossary injection into prompt
- Implement conservative post-processing
- Provide simple UI or CLI for adding glossary entries

Pass condition:

- User can add a term
- Translation prompt includes active glossary
- Glossary term affects later translations
- Traditional and Simplified Chinese targets are supported
- dev logs updated

## Stage 8: Settings UI

Goal:
Allow user to configure subtitle style and runtime settings.

Must complete:

- Implement `settings_window.py`
- Configure target language
- Configure source language
- Configure font size
- Configure font color
- Configure background opacity
- Configure ASR model
- Configure DeepSeek model
- Save settings

Pass condition:

- Settings persist after restart
- Invalid settings are handled
- dev logs updated

## Stage 9: Subtitle Log and Export

Goal:
Save subtitle history locally.

Must complete:

- Implement `subtitle_log_repo.py`
- Save source text, translation, timestamp, latency
- Export TXT
- Optionally export SRT

Pass condition:

- Subtitle logs are saved
- Logs can be exported
- dev logs updated

## Stage 10: AI Glossary Candidate Extraction

Goal:
Analyze subtitle history and suggest high-frequency special terms.

Must complete:

- Extract candidate terms from ASR source text
- Detect inconsistent translations
- Ask AI to classify likely names/game terms
- Save candidates
- User can accept/ignore candidates

Pass condition:

- Candidates are shown
- Accepted terms enter glossary
- Ignored terms are not repeatedly suggested
- dev logs updated

## QML Overlay Refactor

### Phase 1: QML Overlay Shell

Goal:
Create a QML Liquid Glass-inspired overlay shell without connecting it to the
live ASR or translation pipeline.

Must complete:

- Add `ui/qml_overlay` Python package
- Add `OverlayBridge` QObject
- Add `MainOverlay.qml`
- Add subtitle bar, settings icon, control hub, option popover, and basic
  reusable QML components
- Add `--qml-overlay-test`
- Keep the Widgets overlay available as fallback

Pass condition:

- `python -m yt_live_translator.main --qml-overlay-test` opens the QML overlay
- Settings icon opens/closes the control hub
- Control rows open/close option popovers
- Start/Stop update QML running state only
- `pytest` and `py_compile` pass

### Phase 2: Liquid Glass Polish

Goal:
Refine glass visuals, animation, and tuning controls in QML.

Must complete:

- Improve `GlassCard` with layered translucent glass, highlight, shadow, and
  iridescence accents
- Add `GlassEdge`, `GlassHighlight`, and `LiquidThumb` as QML/Qt Quick
  reimplementations inspired by the WpfGlassMenu reference
- Add hover/open/close/subtitle animation polish
- Add `--qml-overlay-tuning`
- Add visual sliders for subtitle opacity, glass/card opacity, iridescence,
  edge/RGB split, distortion/reflect parameters, corner radius, shadow,
  highlight, font size, and animation duration
- Add a Copy current parameters action

Pass condition:

- `python -m yt_live_translator.main --qml-overlay-tuning` opens the tuning UI
- Slider changes update the QML overlay immediately
- Copy current parameters emits a TOML snippet
- `pytest` and `py_compile` pass

### Phase 3: Pipeline Integration

Goal:
Connect QML Start/Stop and subtitle updates to the real overlay pipeline while
keeping the Widgets frontend as fallback.

## Electron Overlay Refactor

### Phase 2: Electron Liquid Glass Prototype

Goal:
Create an Electron / React / TypeScript overlay prototype for Liquid
Glass-inspired material, animation, and manual tuning. This is a visual and
interaction phase only.

Must complete:

- Add `frontend/electron-overlay`
- Use Electron, React, TypeScript, Vite, Framer Motion, and Zustand
- Add secure Electron main/preload setup
- Add subtitle bar, settings icon, control hub, option popover, glass material
  layers, liquid thumb, and tuning panel
- Add mock subtitle events and WebSocket client message contracts
- Split the Electron overlay into separate BrowserWindows for subtitle,
  settings icon, control card, and popover surfaces
- Keep `OVERLAY_WINDOW_MODE=single_legacy` as a fallback for the original
  single-window prototype
- Add `--electron-overlay-test`
- Add `--electron-overlay-tuning`
- Keep Widgets and QML overlays available as fallback
- Do not connect ASR, DeepSeek, glossary, or audio capture

Pass condition:

- Python static tests verify the scaffold, scripts, security flags, bridge
  types, multi-window files, and Phase 2 boundary
- After npm dependencies are installed, `npm run dev:mock`,
  `npm run dev:tuning`, and `npm run typecheck` can be used for manual visual
  testing

### Phase 3: Electron Pipeline Bridge

Goal:
Connect the Electron renderer to a local Python WebSocket bridge while keeping
API keys and pipeline workers outside the renderer.

Must complete:

- Add Python WebSocket server on `127.0.0.1:8765`
- Forward subtitle/status/settings events to Electron
- Forward Start/Stop/settings commands back to Python
- Keep renderer free of API keys and pipeline internals
- Add `--electron-overlay-live`
- Keep mock/tuning commands available for UI-only work

Pass condition:

- Electron live command launches the Python bridge and Electron overlay
- Start/Stop commands reach the Python pipeline
- Partial/final subtitles update the Electron subtitle window
- API keys never appear in renderer code
- `npm run typecheck`, `npm run build`, and `pytest` pass
