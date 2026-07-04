# Technical Decisions

## Initial Decisions

- Platform: Windows first
- Language: Python 3.11
- UI: PySide6
- Audio capture: PyAudioWPatch with WASAPI loopback
- VAD: Silero VAD
- ASR: faster-whisper
- Translation: DeepSeek API
- Storage: SQLite
- Config: TOML
- Development method: staged development with smoke tests

## 2026-07-01

- Added a root-level package shim so `python -m yt_live_translator.main` works
  from a source checkout before editable installation.
- Implemented the Stage 1 DeepSeek client with Python standard-library HTTP
  calls so the smoke test can run before optional API client dependencies are
  installed.
- DeepSeek authentication failures are reported without echoing API response
  details that may include masked key fragments.
- DeepSeek model selection is controlled by `deepseek.model` and is currently
  limited to `deepseek-v4-flash` or `deepseek-v4-pro`.
- Stage 2 uses PyAudioWPatch with the default WASAPI loopback device for system
  audio capture.
- Stage 2 writes 16-bit PCM WAV output after downmixing/resampling to the
  configured audio target format.
- Blocking loopback reads are guarded by a daemon read timeout; missing frames
  are filled with silence so no-audio captures do not hang.
- Stage 3 uses faster-whisper for file ASR and keeps model/device/compute
  options configurable from smoke script arguments.
- ASR CUDA failures during model load or transcription retry with CPU `int8`
  by default so smoke tests can still run on machines without CUDA runtime DLLs.
- Stage 4 uses an energy-based VAD for smoke-test determinism; Silero VAD can
  replace it later behind the same segmenter contract.
- Stage 4 terminal pipeline supports both local audio files and live WASAPI
  loopback capture. Local-file mode is the primary automated smoke path.
- Stage 4 provides `echo` translation mode for no-key pipeline checks and
  `deepseek` mode for real translation.
- Local-file pipeline smoke tests can limit decoded audio with
  `--max-audio-seconds`; use `--max-audio-seconds 180 --max-segments 0` for the
  three-minute stability run.
- Stage 5 keeps PySide6 imports lazy so non-GUI tests and CLI commands can run
  without initializing Qt.
- Stage 6 connects the existing terminal pipeline to the overlay with an
  output callback instead of duplicating ASR/translation orchestration.
- Stage 6 runs audio loading, VAD, ASR, and translation in a PySide6 `QThread`
  worker and uses signals to update the overlay, keeping the UI thread
  responsive.
- Stage 6 smoke tests can write an optional result log containing status,
  source text, translation, and latency. API keys remain process-scoped and are
  not written to the log.
- Stage 6 keeps local-file audio as the primary repeatable smoke path; WASAPI
  loopback remains available through `--loopback-seconds` for live YouTube
  testing.
- Stage 7 stores manual glossary terms in the configured SQLite database and
  initializes the `glossary_terms` table lazily when the repository opens.
- Stage 7 only injects glossary terms that match the current source subtitle,
  source language, enabled state, and requested target language.
- Stage 7 treats English exact terms with word boundaries and non-English terms
  with literal phrase matching so Japanese names and game terms still match
  naturally.
- Stage 7 post-processing is intentionally conservative: it replaces leftover
  source terms in the translated subtitle only when the source subtitle matched
  the term and the configured target is not already present.
- Stage 8 stores user-editable runtime settings in the SQLite `app_settings`
  table instead of rewriting `config.toml`, avoiding accidental changes to
  local API-key configuration.
- Stage 8 keeps the settings window as a focused PySide6 form over the current
  supported settings: language, subtitle style, ASR model/device/compute/beam,
  and DeepSeek model.
- Stage 9 stores subtitle history as JSONL for append-only writes during live
  translation and exports TXT/SRT from that local history.
- Stage 9 writes subtitle logs from both terminal and overlay pipelines by
  default, with command-line options to override the path or disable logging.
- CUDA ASR smoke tests should use `--no-cpu-fallback` when validating GPU
  availability so CPU fallback cannot mask CUDA runtime problems.
- Stage 10 stores AI glossary suggestions separately from accepted manual
  glossary terms in `glossary_candidates`, so ignored or pending suggestions do
  not affect translation.
- Stage 10 extraction uses deterministic local heuristics first, allowing smoke
  tests without an API key. DeepSeek classification is optional and updates the
  same saved candidate rows.
- Stage 10 marks candidates as inconsistent when the same source term appears
  across multiple translation variants in subtitle history.
- Stage 10 accept/ignore is explicit: accepting creates a normal manual
  glossary entry, while ignoring preserves the ignored state across future
  extraction runs.
- Continuous overlay capture reuses the existing stable loopback capture and
  subtitle pipeline in short chunks instead of introducing a second streaming
  audio engine. This gives live continuous behavior while keeping VAD, ASR,
  glossary, translation, overlay, and subtitle logging on the same code path.
- Continuous overlay capture exposes `--max-loopback-chunks` for bounded smoke
  tests and leaves it unset for manual live viewing sessions.
- The soft glass overlay remains a custom PySide6-painted style instead of an
  official Apple material or a new UI framework. This keeps the existing Stage
  5 and Stage 6 window stack stable.
- Windows Acrylic/Mica native effects are represented by an off-by-default
  experimental config section and a best-effort DWM call on Windows. Basic
  Glass must remain the default reliable path, and native effects must not
  block overlay startup.
- The low-latency path uses Local Agreement instead of fixed six-second chunks
  as the primary live strategy. It compares recent rolling-window ASR
  hypotheses, commits only stable prefixes, exposes partial subtitles for fast
  feedback, and retranslates full finalized sentences for final quality.
- `streaming.enabled = true` makes Local Agreement the default with the example
  config. The fixed VAD segment path remains available only as an explicit
  fallback via `--streaming-strategy fixed_segments`.
- Partial subtitle translation is deliberately rate-limited by text growth and
  time so each ASR tick does not call DeepSeek. Final subtitles remain the
  durable log/export event.

## 2026-07-02

- The streaming pipeline's rolling-window design calls ASR on each tick, so
  `transcribe_file()` was loading a new WhisperModel every call (~43s each).
  Model reuse is now a first-class ASR API via `FasterWhisperTranscriber`,
  which loads once, reuses the model across ticks/segments, and records the
  effective CPU fallback device/compute settings accurately.
- The workspace now uses the local `models/faster-whisper-large-v3` directory as
  the default ASR model path. This avoids runtime HuggingFace downloads and
  gives Japanese ASR a higher-quality baseline than `tiny`.
- Overlay pipeline app shutdown now requests worker stop and cleans up the
  running QThread on `aboutToQuit`, because model load/ASR work can otherwise
  outlive the UI event loop during smoke tests or manual closes.
- QML overlay development is split into phases. Phase 1 adds a standalone Qt
  Quick frontend shell, `OverlayBridge`, placeholder subtitle data, and UI-only
  controls. It deliberately does not call ASR, DeepSeek, glossary, or the live
  pipeline. The Widgets overlay remains the fallback until QML is verified in
  live use.
- QML Phase 2 keeps the same non-pipeline boundary. Tuning sliders update
  `OverlayBridge` runtime state and can copy a TOML snippet, but they do not
  persist settings or start live workers. Persistence and live Start/Stop are
  reserved for Phase 3.
- WpfGlassMenu is reference-only for QML Phase 2. The project does not copy WPF,
  C#, HLSL, or compiled shader code. Lens/shader ideas are reimplemented as Qt
  Quick properties, gradient layers, and animation components. Real background
  sampling/shader refraction remains deferred.
- Electron overlay development is split from the Python backend. Phase 2 lives
  in `frontend/electron-overlay`, uses mock events plus a WebSocket client
  contract, and deliberately does not start ASR, DeepSeek, glossary, or audio
  pipeline workers.
- Electron renderer security is mandatory: `nodeIntegration: false`,
  `contextIsolation: true`, `sandbox: true`, and a minimal preload API. API keys
  must stay in the Python process/config boundary and must not be stored in
  renderer code.
- Widgets and QML overlays remain available as fallback while the Electron
  overlay is only a visual/material/motion tuning prototype.
- Electron overlay now defaults to multi BrowserWindow mode to avoid one large
  transparent window intercepting clicks over YouTube/video content. The
  subtitle, settings icon, control card, and popover are separate windows
  anchored by subtitle geometry.
- `OVERLAY_WINDOW_MODE=single_legacy` remains available for the original
  single-window prototype. Multi-window mode keeps the Electron main process as
  the UI state source of truth and broadcasts state snapshots to each renderer
  through typed preload IPC.
- Electron live mode uses a Python-owned localhost WebSocket bridge at
  `ws://127.0.0.1:8765`. Python keeps ownership of audio capture, ASR,
  DeepSeek, glossary, subtitle logging, and API keys. Electron main connects as
  a WebSocket client and updates `OverlayWindowManager`; renderers never call
  DeepSeek or read API keys.
- Electron launch helpers construct a child-process environment with the
  Windows Node.js install directory prepended when `C:\Program Files\nodejs\npm.cmd`
  exists. This makes Python-started Electron modes resilient when the current
  shell PATH does not expose `npm` or `node`.
- The interactive Windows launch script executes Python with a PowerShell
  argument array instead of `Invoke-Expression`, so user-entered audio paths and
  CLI options are not reparsed as a single command string.
