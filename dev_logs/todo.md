# Todo

## Current Stage

All planned stages complete

## Tasks

- [x] Create project folders
- [x] Create AGENTS.md
- [x] Create docs
- [x] Create dev_logs
- [x] Create package layout
- [x] Create config.example.toml
- [x] Create requirements.txt
- [x] Create pyproject.toml
- [x] Verify import works
- [x] Load config from `config.toml`
- [x] Fallback to `config.example.toml`
- [x] Read DeepSeek API key from environment variable or local config
- [x] Implement `deepseek_client.py`
- [x] Implement `prompt_builder.py`
- [x] Implement `scripts/smoke_translate.py`
- [x] Add config tests
- [x] Add prompt builder tests
- [x] Verify zh-TW translation smoke test
- [x] Verify zh-CN translation smoke test
- [x] Allow selecting `deepseek-v4-flash` or `deepseek-v4-pro`
- [x] Implement `audio/wasapi_capture.py`
- [x] Implement `audio/resampler.py`
- [x] Implement `scripts/smoke_audio_capture.py`
- [x] Detect WASAPI loopback output devices
- [x] Capture speaker output to WAV
- [x] Avoid hanging when no loopback frames arrive
- [x] Implement `speech/asr_faster_whisper.py`
- [x] Implement `scripts/smoke_asr_file.py`
- [x] Support ASR language parameter: `auto`, `en`, `ja`
- [x] Support ASR model size setting
- [x] Verify English ASR file smoke test
- [x] Verify Japanese ASR file smoke test
- [x] Verify CUDA failure gives CPU fallback warning
- [x] Implement `speech/vad.py`
- [x] Implement `speech/segmenter.py`
- [x] Implement `core/task_queue.py`
- [x] Implement `core/subtitle_pipeline.py`
- [x] Implement `scripts/smoke_pipeline_terminal.py`
- [x] Verify local-file terminal pipeline with echo translation
- [x] Verify local-file terminal pipeline with DeepSeek translation
- [x] Print segment id, source text, translated text, and latency
- [x] Support reading about 3 minutes of local audio for stability tests
- [x] Implement `ui/overlay_window.py`
- [x] Support always-on-top overlay test window
- [x] Support dragging overlay window
- [x] Support font size, font color, and background opacity from config
- [x] Support show/hide source and translation from config
- [x] Verify overlay smoke test with auto-close
- [x] Implement Stage 6 overlay pipeline app
- [x] Start the pipeline and overlay from the main CLI
- [x] Send subtitle updates from pipeline output callbacks to the UI
- [x] Keep UI responsive by running ASR and translation in a QThread worker
- [x] Add Start/Stop controls for the overlay pipeline
- [x] Verify local-file overlay pipeline with echo translation
- [x] Verify local-file overlay pipeline with DeepSeek translation
- [x] Add optional result logging for Stage 6 smoke tests
- [x] Implement SQLite glossary storage
- [x] Implement `glossary_repo.py`
- [x] Implement `glossary_apply.py`
- [x] Inject active glossary terms into translation prompts
- [x] Add conservative glossary post-processing
- [x] Provide CLI or simple UI for adding glossary entries
- [x] Implement `settings_window.py`
- [x] Configure target language
- [x] Configure source language
- [x] Configure font size
- [x] Configure font color
- [x] Configure background opacity
- [x] Configure ASR model
- [x] Configure DeepSeek model
- [x] Save settings
- [x] Implement `subtitle_log_repo.py`
- [x] Save source text, translation, timestamp, and latency
- [x] Export subtitle history as TXT
- [x] Export subtitle history as SRT
- [x] Connect subtitle logging to terminal pipeline
- [x] Connect subtitle logging to overlay pipeline
- [x] Extract candidate terms from ASR source text
- [x] Detect inconsistent translations
- [x] Ask AI to classify likely names/game terms
- [x] Save glossary candidates
- [x] Allow user to accept or ignore candidates

## Later

- [x] Stage 1: Config and translation smoke test
- [x] Stage 2: Audio capture smoke test
- [x] Stage 3: ASR file smoke test
- [x] Stage 4: Terminal real-time pipeline
- [x] Stage 5: Overlay window
- [x] Stage 6: Real-time overlay pipeline
- [x] Stage 7: Manual glossary
- [x] Stage 8: Settings UI
- [x] Stage 9: Subtitle log
- [x] Stage 10: AI glossary candidates

## Product Hardening

- [x] Continuous live loopback capture for overlay pipeline
- [x] Liquid Glass-inspired PySide6 soft glass overlay style
- [x] Optional subtitle fade/slide animation and drag feedback
- [x] Off-by-default native Acrylic/Mica experiment config placeholder
- [x] Low-latency Local Agreement streaming subtitle strategy
- [x] Partial subtitle and final subtitle rewrite event path
- [x] Local faster-whisper large-v3 model smoke test
- [x] QML Liquid Glass overlay Phase 1 shell
- [x] QML Liquid Glass visual polish and tuning controls
- [x] Electron Liquid Glass overlay Phase 2 visual prototype
- [x] Electron overlay multi BrowserWindow split
- [x] Electron overlay WebSocket pipeline integration
- [ ] QML overlay pipeline integration
- [ ] CUDA runtime PATH startup diagnostics
- [ ] Quality testing with local large-v3 on long livestream audio
- [ ] Lower-latency sample-level streaming capture pipeline

## Discovered 2026-07-04

- [x] Fix Electron overlay live pipeline: subtitle events not reaching GUI
- [x] Fix Electron overlay settings icon button click not responding
- [x] Add debug logging across WebSocket → main process → IPC → renderer chain
- [x] Add robust WebSocket message parsing (string/ArrayBuffer/Buffer)
- [x] Add Python bridge client-connect pipeline status sync

- [x] Harden interactive launch script command execution and Electron npm/node PATH fallback
- [x] Restore Git executable/repository metadata so Git status and commits can be updated
- [ ] Refresh shell PATH so `git` works without the full executable path

## Discovered 2026-07-02

- [ ] Investigate abnormally slow CUDA model loading (~43s for tiny)
- [x] Make ASR model reuse a first-class feature
- [ ] Find stable network/model-sync route for future ASR model updates
- [ ] Verify local large-v3 Japanese quality on cleaner audio source
