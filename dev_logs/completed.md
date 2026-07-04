# Completed Work

This file records completed development tasks.

## Format

```md
## YYYY-MM-DD

- Completed:
  - ...
- Tests:
  - ...
- Notes:
  - ...
```

## 2026-07-01

- Completed:
  - Created Stage 0 project scaffold.
  - Added documentation, development logs, config example, package layout,
    scripts folder, tests folder, requirements, and pyproject metadata.
  - Added minimal main module smoke entry point.
  - Implemented Stage 1 config loading with `config.toml` fallback to
    `config.example.toml`.
  - Implemented logging setup, translation prompt builder, DeepSeek API client,
    and `scripts/smoke_translate.py`.
  - Added Stage 1 tests for config loading, API key resolution, prompt building,
    and DeepSeek client behavior.
  - Implemented Stage 2 WASAPI loopback device discovery and audio capture.
  - Implemented PCM16 downmixing, linear resampling, WAV writing, and
    `scripts/smoke_audio_capture.py`.
  - Added read timeout protection so silent/no-frame capture writes silence
    instead of hanging.
  - Implemented Stage 3 faster-whisper file transcription wrapper.
  - Implemented `scripts/smoke_asr_file.py` with language, model, device,
    compute type, beam size, and CPU fallback options.
  - Added tests for ASR language handling, model parameters, missing files, and
    CUDA load/transcription fallback.
  - Implemented Stage 4 energy VAD, PCM segmenter, task queue, terminal
    subtitle pipeline, and `scripts/smoke_pipeline_terminal.py`.
  - Added local-file and loopback audio source support for terminal pipeline
    smoke tests.
  - Added echo translation mode for no-key pipeline checks and DeepSeek mode for
    real translation smoke tests.
  - Added local-file pipeline duration limiting for about three-minute
    stability tests.
  - Implemented Stage 5 PySide6 overlay smoke window with always-on-top,
    dragging, configurable source/translation visibility, font sizes, colors,
    and background opacity.
  - Implemented Stage 6 PySide6 overlay pipeline app with a worker thread for
    audio loading, VAD, ASR, and translation.
  - Added CLI entry point `--overlay-pipeline-test` with local-file and WASAPI
    loopback audio sources.
  - Added Start/Stop controls and signal-based subtitle updates from the
    pipeline worker to the overlay UI.
  - Added optional Stage 6 result logging for smoke-test auditing without
    logging API keys.
  - Implemented Stage 7 SQLite database helpers and glossary table
    initialization.
  - Implemented `GlossaryRepository` for adding, listing, and matching manual
    glossary terms.
  - Implemented glossary prompt-term selection and conservative
    post-processing for leftover source terms.
  - Added `scripts/glossary_cli.py` for manual term creation, listing, and
    match checks.
  - Integrated glossary matching into translation smoke tests, terminal
    pipeline translation, and overlay pipeline translation.
  - Implemented Stage 8 SQLite-backed settings persistence with
    `SettingsRepository`.
  - Implemented Stage 8 PySide6 settings window for target/source language,
    subtitle style, ASR settings, and DeepSeek model selection.
  - Added `--settings-test`, `--settings-test-seconds`, and `--settings-db`
    to the main CLI.
  - Implemented Stage 9 subtitle JSONL log repository with TXT and SRT export.
  - Added `scripts/subtitle_log_cli.py` for subtitle log append/list/export
    smoke tests.
  - Connected subtitle log writing to both terminal and overlay pipelines.
  - Implemented Stage 10 `glossary_candidates` SQLite table and candidate
    repository.
  - Implemented candidate extraction from subtitle history source text.
  - Added inconsistent translation detection based on repeated source terms
    appearing with multiple translation variants.
  - Implemented heuristic candidate classification and optional DeepSeek
    candidate classification.
  - Added `scripts/glossary_candidates_cli.py` for extract, list, classify-ai,
    accept, and ignore workflows.
  - Connected accepted candidates to the manual glossary repository.
- Tests:
  - `.venv\Scripts\python.exe -m yt_live_translator.main`
  - `.venv\Scripts\python.exe -m yt_live_translator.main --help`
  - `.venv\Scripts\pytest.exe` passed with 38 tests.
  - `.venv\Scripts\python.exe scripts\smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-TW` translated successfully with a manually entered API key.
  - `.venv\Scripts\python.exe scripts\smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-CN` translated successfully with a manually entered API key.
  - `.venv\Scripts\python.exe scripts\smoke_audio_capture.py --list-devices`
    detected WASAPI loopback devices.
  - `.venv\Scripts\python.exe scripts\smoke_audio_capture.py --seconds 6 --output work\stage2_test_capture_watchdog.wav --source-hint "C:\Users\Owen\Desktop\test_miko_audio.mp3"` captured 6 seconds from the default loopback device.
  - `work\stage2_test_capture_watchdog.wav` verified as 1 channel, 16000 Hz,
    96000 frames, 6.0 seconds, RMS 1903.85.
  - `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage3_english_tts.wav --language en --model tiny --device cpu --compute-type int8 --beam-size 1` transcribed English audio.
  - `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage2_test_capture_watchdog.wav --language ja --model tiny --device cpu --compute-type int8 --beam-size 1` transcribed Japanese audio.
  - `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage3_english_tts.wav --language en --model tiny --device cuda --compute-type float16 --beam-size 1` fell back to CPU int8 and transcribed successfully.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000` printed segment id, source text, echo translation, and latency.
  - `work\stage4_manual_pipeline_smoke.ps1` ran the same local MP3 with
    DeepSeek translation after manual API key entry; exit code 0.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --max-audio-seconds 180 --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 0 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --deepseek-timeout 30` processed about three minutes of local audio with echo translation.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --max-audio-seconds 180 --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 60 --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 0 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000` processed about three minutes of local audio with DeepSeek translation; 35 segments completed, exit code 0.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-test --overlay-test-seconds 3` opened and auto-closed the overlay smoke window.
  - `.venv\Scripts\pytest.exe` passed with 42 tests after Stage 6 changes.
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\main.py src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\core\subtitle_pipeline.py` passed.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 15 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --close-on-finish --auto-close-seconds 30` opened the overlay pipeline app, processed one local-audio segment, and exited with code 0.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 60 --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 20 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --silence-end-ms 700 --padding-ms 400 --close-on-finish --auto-close-seconds 90 --overlay-result-log work\stage6_overlay_pipeline_deepseek_latest.txt` completed a real DeepSeek overlay pipeline smoke test with a process-scoped API key.
  - `.venv\Scripts\python.exe -m yt_live_translator.main` printed the scaffold OK message after Stage 6 changes.
  - `.venv\Scripts\pytest.exe` passed with 49 tests after Stage 7 changes.
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\storage\db.py src\yt_live_translator\storage\glossary_repo.py src\yt_live_translator\translate\glossary_apply.py scripts\glossary_cli.py scripts\smoke_translate.py scripts\smoke_pipeline_terminal.py src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\main.py` passed.
  - `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 add --source Miko --target-zh-tw 咪口 --target-zh-cn 咪口 --source-lang ja --term-type person --note streamer` added a manual glossary term.
  - `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 list` listed the active glossary term.
  - `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 match --text "Miko starts the stream" --source-lang ja --target zh-TW` matched the Traditional Chinese target.
  - `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 match --text "Miko starts the stream" --source-lang ja --target zh-CN` matched the Simplified Chinese target.
  - `.venv\Scripts\pytest.exe` passed with 53 tests after Stage 8 and Stage 9 changes.
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\storage\settings_repo.py src\yt_live_translator\ui\settings_window.py src\yt_live_translator\storage\subtitle_log_repo.py scripts\subtitle_log_cli.py scripts\smoke_pipeline_terminal.py src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\main.py` passed.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --settings-test --settings-test-seconds 3 --settings-db work\stage8_settings_smoke.sqlite3` opened and auto-closed the settings window.
  - `.venv\Scripts\python.exe scripts\subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl append --segment-id 1 --source "Miko starts" --translation "Miko translated" --source-lang ja --target zh-TW --latency-ms 42 --start 0 --end 2.5` appended a subtitle log entry.
  - `.venv\Scripts\python.exe scripts\subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl list` listed the subtitle log entry.
  - `.venv\Scripts\python.exe scripts\subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-txt --output work\stage9_subtitle_log_smoke.txt` exported TXT.
  - `.venv\Scripts\python.exe scripts\subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-srt --output work\stage9_subtitle_log_smoke.srt` exported SRT.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 15 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --subtitle-log work\stage9_pipeline_log_smoke.jsonl --no-glossary` wrote a subtitle log from the terminal pipeline.
  - With `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin` added to the process `PATH`, `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --language ja --model tiny --device cuda --compute-type float16 --beam-size 1 --no-cpu-fallback` completed with `device=cuda`, `compute_type=float16`, and no CPU fallback.
  - `.venv\Scripts\pytest.exe` passed with 57 tests after Stage 10 changes.
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\storage\db.py src\yt_live_translator\storage\glossary_candidate_repo.py src\yt_live_translator\translate\glossary_candidates.py scripts\glossary_candidates_cli.py` passed.
  - `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 --log work\stage10_subtitle_log_smoke.jsonl extract --min-occurrences 2 --limit 10` extracted `Miko` and `Radahn` candidates.
  - `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 accept --id 1 --target-zh-tw MikoTW --target-zh-cn MikoCN` accepted a candidate into the manual glossary.
  - `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 ignore --id 2` ignored a candidate.
  - Re-running Stage 10 extraction kept the ignored candidate ignored and left no pending candidates.
  - `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_ai_candidates_smoke.sqlite3 classify-ai --limit 2 --deepseek-timeout 60` classified candidates with DeepSeek using a process-scoped API key.
  - Final full check: `.venv\Scripts\pytest.exe` passed with 57 tests.
  - Final full check: all Python files under `src`, `scripts`, and `tests`
    passed `py_compile`.
  - Final full check: `.venv\Scripts\python.exe -m yt_live_translator.main`
    printed the scaffold OK message.
  - Final full check: project file scan found no pasted DeepSeek API key.
  - Final GPU check: with CUDA Toolkit 12.0 `bin` added to process `PATH`,
    faster-whisper completed with `device=cuda`, `compute_type=float16`,
    `--no-cpu-fallback`, and about 10.3 seconds latency.
  - Implemented continuous live loopback capture mode for the overlay pipeline.
  - Added `--continuous-loopback`, `--loopback-chunk-seconds`, and
    `--max-loopback-chunks` CLI options.
  - Continuous mode now captures short system-audio chunks, runs the existing
    VAD/ASR/translation pipeline for each chunk, updates the overlay, writes
    subtitle logs, and continues until Stop is pressed.
  - Launched the continuous live overlay against the currently playing
    livestream with a process-scoped DeepSeek key and CUDA ASR.
  - `work\continuous_live_overlay_latest.txt` showed repeated chunk output
    from chunks 1, 2, and 3 with DeepSeek translations and latency values.
  - Implemented a Liquid Glass-inspired PySide6 soft glass overlay style with
    custom rounded panel painting, translucent fill, soft shadow, subtle border,
    top highlight, text shadows, and classic fallback.
  - Added optional subtitle fade/slide animations, cross-fade snapshots, and
    small drag feedback scaling.
  - Added overlay glass, animation, and off-by-default native effect settings
    to runtime config parsing and `config.example.toml`.
  - Added a non-blocking Windows DWM backdrop attempt for experimental native
    `mica`, `acrylic`, and `mica-alt` effects when explicitly enabled.
  - Added `--style glass` and `--style classic` to the overlay smoke CLI.
  - `.venv\Scripts\pytest.exe` passed with 63 tests after soft glass overlay
    changes.
  - All Python files under `src`, `scripts`, and `tests` passed
    `py_compile` after soft glass overlay changes.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-test --style glass --overlay-test-seconds 3`
    opened and auto-closed the glass overlay smoke window.
  - Project scan found no pasted `sk-` DeepSeek API key.
  - Implemented low-latency Local Agreement streaming subtitles with rolling
    audio windows, short ASR ticks, confirmed-prefix commits, partial subtitle
    events, and final subtitle rewrites.
  - Added recent-silence finalization for streaming audio so punctuation,
    timeout, max unconfirmed duration, and silence can all close a subtitle.
  - Added `speech/streaming_agreement.py`,
    `translate/final_subtitle_reviser.py`, and
    `tests/test_streaming_agreement.py`.
  - Added `[streaming]`, `[streaming.en]`, and `[streaming.ja]` config sections
    plus terminal/overlay `--streaming-strategy local_agreement` options.
  - Made terminal and overlay pipelines follow `streaming.enabled` by default,
    so `config.example.toml` uses Local Agreement unless
    `--streaming-strategy fixed_segments` is passed.
  - Overlay partial subtitles now render with a lighter text style and final
    subtitles replace the latest partial.
  - `.venv\Scripts\pytest.exe tests\test_streaming_agreement.py tests\test_config.py`
    passed with 16 tests.
  - `.venv\Scripts\pytest.exe tests\test_overlay_pipeline_app.py tests\test_overlay_window.py tests\test_subtitle_pipeline.py tests\test_streaming_agreement.py tests\test_final_subtitle_reviser.py tests\test_config.py`
    passed with 34 tests.
  - Final streaming check: `.venv\Scripts\pytest.exe` passed with 78 tests.
  - Final streaming check: all Python files under `src`, `scripts`, and
    `tests` passed `py_compile`.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file work\stage3_english_tts.wav --streaming-strategy local_agreement --source-lang en --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --no-glossary --no-subtitle-log`
    produced a `[FINAL]` streaming event with about 1.4 seconds latency.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --no-glossary --no-subtitle-log`
    also produced streaming-format output through the config default.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 4 --no-glossary --no-subtitle-log`
    produced a `[FINAL]` streaming event with about 3.1 seconds latency.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file work\stage3_english_tts.wav --streaming-strategy local_agreement --source-lang en --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --close-on-finish --auto-close-seconds 20 --no-glossary --no-subtitle-log`
    opened the overlay pipeline, processed streaming output, and exited with
    code 0.
- Notes:
  - All originally planned stages are complete.
  - DeepSeek API key was provided only as a process environment variable for
    smoke tests and was not written to project files.
  - Stage 6 DeepSeek smoke used CPU `tiny` ASR for speed; it proves pipeline
    integration but not final subtitle quality.
  - Stage 7 uses CLI management first; a richer glossary UI can reuse the
    repository APIs later.
  - CUDA ASR is now available in this environment when CUDA 12.0 `bin` is added
    to `PATH`.

## 2026-07-02

- Completed:
  - Launched the first live continuous loopback overlay pipeline test against
    a real YouTube livestream (Japanese → Traditional Chinese).
  - Diagnosed and fixed ASR model reload overhead with the first-class
    `FasterWhisperTranscriber` API. Terminal and overlay pipelines now load the
    WhisperModel once and reuse it across all segment/tick calls.
  - Verified pipeline latency of 1.6-4.4s per output event after the fix.
  - Identified that tiny ASR model quality is insufficient for Japanese game
    stream audio.
  - Discovered that HuggingFace Hub downloads are blocked by Radmin VPN.
  - Updated all documentation with findings.
- Tests:
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --source-lang ja --target zh-TW --translation deepseek --model tiny --device cuda` produced partial/final events with 1.6-4.4s latency.
  - CUDA tiny model load time independently measured at ~43s.
  - WASAPI loopback capture verified: default JBL Charge 3 device, RMS 1552.
  - `.venv\Scripts\pytest.exe tests\test_asr_faster_whisper.py tests\test_subtitle_pipeline.py tests\test_smoke_pipeline_terminal.py tests\test_overlay_pipeline_app.py`
    passed with 19 tests after reusable ASR changes.
  - `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --no-glossary --no-subtitle-log`
    produced a streaming `[FINAL]` event with about 1.8 seconds latency.
  - Final reusable-ASR check: `.venv\Scripts\pytest.exe` passed with 80 tests.
  - Final reusable-ASR check: all Python files under `src`, `scripts`, and
    `tests` passed `py_compile`.
  - Verified local `models\faster-whisper-large-v3` loads with CUDA float16 on
    `work\stage3_english_tts.wav`; 7.24 seconds of English audio transcribed
    in about 4.6 seconds with no CPU fallback.
  - Verified local large-v3 in the Local Agreement terminal pipeline on
    `C:\Users\Owen\Desktop\test_miko_audio.mp3` with echo translation; first
    output appeared at about 4.0 seconds including model warmup, then later
    ticks were about 0.7 seconds.
  - Updated `config.example.toml` and runtime docs to use
    `models/faster-whisper-large-v3` by default.
  - Fixed overlay pipeline shutdown cleanup so auto-close/app quit requests
    stop the worker and clean up a still-running QThread instead of leaving the
    process hanging.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --close-on-finish --auto-close-seconds 30 --no-glossary --no-subtitle-log --overlay-result-log work\large_v3_overlay_smoke.txt`
    opened the overlay, emitted partial/final events with local large-v3, wrote
    `Overlay pipeline finished`, and exited with code 0.
- Notes:
  - Model reuse is now part of the ASR API instead of an overlay-only
    workaround.
  - CPU fallback metadata now reports effective CPU `int8` settings accurately
    after CUDA model load failure.
  - Local large-v3 removes the immediate HuggingFace-download blocker for this
    workspace, but longer livestream quality checks are still needed.

## 2026-07-02 Overlay Hotfix

- Completed:
  - Added a main-thread `QObject` bridge for overlay pipeline worker signals so
    subtitle updates, status updates, errors, and finish handling no longer
    mutate Qt widgets from the worker thread.
  - Made pipeline subtitle updates non-animated and explicitly repaint the
    overlay labels/window, preventing stale opacity animation state from
    hiding subtitles.
  - Reworked close-on-finish/auto-close so the app exits from the Qt main
    thread after worker-thread cleanup and a short repaint delay.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\ui\overlay_window.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_overlay_pipeline_app.py tests\test_overlay_window.py`
    passed with 12 tests.
  - Local CUDA overlay smoke with `models\faster-whisper-large-v3` and echo
    translation wrote partial/final subtitles and exited with code 0.
  - Live loopback CUDA large-v3 + DeepSeek smoke completed with source
    `ご視聴ありがとうございました。`, translation `感謝您的收看。`, and
    5231 ms latency.
  - `.venv\Scripts\pytest.exe` passed with 80 tests.

## 2026-07-02 Overlay Visibility Fix

- Completed:
  - Changed the subtitle overlay from a `Qt.Tool` window to a frameless
    top-level window with always-on-top support.
  - Added one-time bottom-center screen positioning and an `ensure_visible()`
    helper that shows, raises, optionally activates, and repaints the overlay.
  - Wired overlay pipeline status/subtitle updates through `ensure_visible()`
    so the floating overlay follows the controls-window subtitle preview.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\ui\overlay_pipeline_app.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_overlay_window.py tests\test_overlay_pipeline_app.py`
    passed with 12 tests.

## 2026-07-02 Overlay Text Rendering Fix

- Completed:
  - Added direct `QPainter` subtitle rendering to the top-level overlay window.
  - Stored the latest source/translation/partial state in
    `SubtitleOverlayWindow` so `paintEvent` can draw text independently of
    child `QLabel` painting.
  - Kept QLabel updates for normal widget behavior while making direct painting
    the reliable path for transparent overlay display.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\ui\overlay_pipeline_app.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_overlay_window.py tests\test_overlay_pipeline_app.py`
    passed with 12 tests.

## 2026-07-02 QML Overlay Phase 1

- Completed:
  - Added the standalone QML overlay frontend package under
    `src\yt_live_translator\ui\qml_overlay`.
  - Added `OverlayBridge` as the only Python/QML state boundary for Phase 1.
  - Added `MainOverlay.qml` with placeholder subtitle data, settings icon,
    control hub, option popover, and reusable QML components.
  - Added `[ui]` and `[qml_overlay]` runtime config sections.
  - Added `--qml-overlay-test` and `--qml-overlay-test-seconds`.
  - Kept the existing Widgets overlay available as fallback.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\core\config.py src\yt_live_translator\main.py src\yt_live_translator\ui\qml_overlay\qml_bridge.py src\yt_live_translator\ui\qml_overlay\qml_overlay_app.py src\yt_live_translator\ui\qml_overlay\qml_resources.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_config.py tests\test_qml_overlay.py`
    passed with 15 tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 3`
    opened the QML overlay and exited with code 0.

## 2026-07-02 QML Overlay Phase 2

- Completed:
  - Improved `GlassCard.qml` with layered shadows, translucent highlight,
    iridescence border, and bottom accent.
  - Added smoother animation behavior for subtitle opacity/font changes and
    glass parameter changes.
  - Added `TuningControls.qml` and wired sliders to `OverlayBridge`.
  - Added visual tuning bridge properties for subtitle opacity, glass/card
    opacity, iridescence opacity/width, corner radius, shadow opacity/radius,
    highlight opacity, font sizes, and animation duration.
  - Added Copy current parameters as a TOML snippet helper.
  - Added `--qml-overlay-tuning` and `--qml-overlay-tuning-seconds`.
  - Kept QML Phase 2 as UI-only work; no live ASR/translation pipeline starts.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\main.py src\yt_live_translator\ui\qml_overlay\qml_bridge.py src\yt_live_translator\ui\qml_overlay\qml_overlay_app.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_qml_overlay.py tests\test_config.py`
    passed with 17 tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 2`
    opened the normal QML overlay and exited with code 0.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-tuning --qml-overlay-tuning-seconds 2`
    opened the tuning UI and exited with code 0.
  - `.venv\Scripts\pytest.exe` passed with 88 tests.
  - All Python files under `src`, `scripts`, and `tests` passed
    `py_compile`.

## 2026-07-02 QML Overlay Phase 2 WpfGlassMenu Reference Pass

- Completed:
  - Read the WpfGlassMenu reference files requested by the user and used them
    only as visual/algorithmic references.
  - Added `GlassEdge.qml`, `GlassHighlight.qml`, `LiquidThumb.qml`, and
    `TuningPanel.qml`.
  - Reworked `GlassCard.qml` to compose base tint, panel tint, highlight,
    edge/RGB accents, edge darkening, and soft shadows.
  - Reworked `ControlHubCard.qml` Start/Stop controls to use `LiquidThumb`.
  - Expanded `OverlayBridge`, `config.example.toml`, and config parsing with
    lens-style material parameters.
  - Kept Phase 2 UI-only; no ASR, DeepSeek, glossary, or live pipeline
    integration was added.
- Tests:
  - `.venv\Scripts\pytest.exe` passed with 88 tests.
  - All Python files under `src`, `scripts`, and `tests` passed
    `py_compile`.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-tuning --qml-overlay-tuning-seconds 2`
    opened the tuning UI and exited with code 0.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 2`
    opened the normal QML overlay and exited with code 0.

## 2026-07-03 Electron Overlay Phase 2 Prototype

- Completed:
  - Added `frontend\electron-overlay` with Electron, React, TypeScript, Vite,
    Framer Motion, Zustand, and CSS material layers.
  - Added secure Electron main/preload setup with `nodeIntegration: false`,
    `contextIsolation: true`, `sandbox: true`, and a minimal preload API.
  - Added React reimplementations of the Phase 2 overlay UI:
    `GlassCard`, `GlassEdge`, `GlassHighlight`, `LiquidThumb`, subtitle bar,
    settings icon, control hub, option popover, and tuning panel.
  - Added mock subtitle/status events plus WebSocket bridge message contracts
    for `ws://127.0.0.1:8765`.
  - Added Python launch helpers and CLI flags:
    `--electron-overlay-test` and `--electron-overlay-tuning`.
  - Added `docs\10_electron_overlay_design.md` and updated AGENTS, design,
    testing, UI, runtime, and development-plan docs.
  - Kept Electron Phase 2 separate from ASR, DeepSeek, glossary, audio capture,
    and live pipeline integration.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_app.py src\yt_live_translator\main.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 9
    tests.
  - `.venv\Scripts\pytest.exe` passed with 97 tests.
  - Frontend `npm run typecheck` and live Electron launch were not run because
    `npm` is not available in the current PowerShell PATH.

## 2026-07-03 Electron Overlay npm Dependency Fix

- Completed:
  - Changed `frontend\electron-overlay` from Vite 6 to `vite@^5.4.0`, matching
    `electron-vite@2.3.0` peer dependency support.
  - Generated `package-lock.json` with the resolved Vite 5 dependency tree.
  - Added explicit renderer `build.rollupOptions.input` for electron-vite.
  - Added `.gitignore` entries for Electron `node_modules`, `out`, and local
    dev logs.
- Tests:
  - `npm install` completed without `--force` or `--legacy-peer-deps`.
  - `npm run typecheck` passed.
  - `npm run build` passed.
  - `npm run dev:mock` started the renderer dev server and Electron app.
  - `npm run dev:tuning` started the renderer dev server and Electron app.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 9
    tests.

## 2026-07-03 Electron Overlay Multi-Window Split

- Completed:
  - Added `frontend\electron-overlay\src\main\windows` with
    `OverlayWindowManager`, window geometry, and separate BrowserWindow
    factories for subtitle, settings icon, control card, and popover.
  - Added `frontend\electron-overlay\src\shared\overlayIpcTypes.ts` for typed
    preload IPC contracts and UI state snapshots.
  - Changed Electron default window mode to multi-window while preserving
    `OVERLAY_WINDOW_MODE=single_legacy`.
  - Split the React renderer by `?window=subtitle`, `?window=settings-icon`,
    `?window=control-card`, and `?window=popover`.
  - Kept Phase 2 mock/tuning-only; no ASR, DeepSeek, glossary, or audio
    pipeline integration was added.
- Tests:
  - `npm run typecheck` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 13
    tests.

## 2026-07-03 Electron Overlay Bottom-Clipping Fix

- Completed:
  - Added bottom-aware menu placement in Electron multi-window geometry.
  - Control card now shifts upward when there is not enough space below the
    subtitle anchor.
  - Popover height is selected by content type, and active row offset is
    preserved while the subtitle window moves.
  - Control card windows can scroll internally if tuning content exceeds the
    available work area height.
  - Replaced mojibake mock subtitle text in `OverlayWindowManager` with ASCII
    mock strings.
- Tests:
  - `npm run typecheck` passed.
  - `npm run lint` passed.
  - `npm run build` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 14
    tests.
  - `.venv\Scripts\pytest.exe` passed with 102 tests.

## 2026-07-03 Electron Overlay Live Pipeline Bridge

- Completed:
  - Added `ElectronOverlayBridge`, a Python localhost WebSocket bridge at
    `ws://127.0.0.1:8765`.
  - Added `--electron-overlay-live`, reusing the existing pipeline options for
    local audio, loopback, continuous loopback, ASR, DeepSeek, glossary, and
    subtitle logs.
  - Added Electron main-process `BackendBridgeClient`.
  - Live mode disables Electron mock events and feeds real subtitle/status
    events into `OverlayWindowManager`.
  - Start/Stop, source language, target language, display mode, and DeepSeek
    model controls are forwarded from Electron renderer IPC to Python.
  - Added `npm run dev:live`.
  - Kept API keys and pipeline code out of Electron renderer.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py src\yt_live_translator\ui\electron_overlay_app.py src\yt_live_translator\main.py`
    passed.
  - `npm run typecheck` passed.
  - `npm run build` passed.
  - `npm run lint` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16
    tests.

## 2026-07-04 Electron Overlay Live Pipeline Debugging & Fix

- Completed:
  - Added robust `coerceMessageData()` in `BackendBridgeClient` to handle
    string, ArrayBuffer, and TypedArray WebSocket message payloads across
    different Electron/Node.js WebSocket implementations.
  - Changed message parse errors to log and continue instead of incorrectly
    marking the connection as disconnected.
  - Added exponential back-off reconnect (1s, 2s, 4s, ... capped at 10s).
  - Added `console.log` debug output to `BackendBridgeClient`,
    `OverlayWindowManager.applyBackendEvent()`, `toggleControlCard()`, and
    each multi-window renderer's IPC state subscription.
  - Fixed `MultiWindowApp` useEffect dependency from unstable zustand
    selector to stable `windowType`, preventing potential listener leaks.
  - Added `_pipeline_running` flag to `ElectronOverlayBridge` and send
    current pipeline status ("running" / "idle") when a new WebSocket client
    connects, preventing stale UI state.
  - Added `print()` logging to the Python bridge for client connect,
    disconnect, command received, and broadcast events.
  - Fixed settings-icon `onClick` handler to properly await and log the
    `toggleControlCard()` IPC result instead of silently ignoring errors.
  - Added `launch.bat` and `launch.ps1` interactive launch scripts.
- Tests:
  - `npm run typecheck` passed.
  - `npm run build` passed.
  - `npm run lint` passed.
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16 tests.
  - `.venv\Scripts\pytest.exe` passed with 104 tests.

## 2026-07-04 Project State Check & Launch Hardening

- Completed:
  - Reviewed the current workspace after user-side changes.
  - Confirmed the Electron Python launcher now uses a child-process
    environment that prepends `C:\Program Files\nodejs` when the bundled
    Windows `npm.cmd` fallback exists, so Electron launch works even when the
    current shell PATH does not expose npm/node.
  - Hardened `launch.ps1` to execute Python with an argument array instead of
    `Invoke-Expression`, preserving local audio paths with spaces and avoiding
    fragile command-string parsing.
  - Corrected the interactive launch script note: `--electron-overlay-live`
    starts the Electron frontend automatically from Python.
  - Removed an unused import from the Electron overlay bridge.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py src\yt_live_translator\ui\electron_overlay_app.py src\yt_live_translator\main.py` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16 tests.
  - `npm run typecheck` passed after adding `C:\Program Files\nodejs` to the test process PATH.
  - `npm run lint` passed after adding `C:\Program Files\nodejs` to the test process PATH.
  - `npm run build` passed after adding `C:\Program Files\nodejs` to the test process PATH.
  - `launch.ps1` parsed successfully as a PowerShell scriptblock.
  - `.venv\Scripts\pytest.exe` passed with 104 tests.
  - Project scan found no pasted `sk-` DeepSeek API key.
- Notes:
  - This workspace currently has no `.git` directory, and `git.exe` is not
    available on PATH, so Git status/staging/commit could not be updated from
    this environment.

## 2026-07-04 Git Repository Initialization

- Completed:
  - Initialized a local Git repository in the project workspace after Git was
    installed on the machine.
  - Added `models/` to `.gitignore` so the local faster-whisper model directory
    is not committed.
- Tests:
  - Git status was checked with `C:\Program Files\Git\cmd\git.exe`.
- Notes:
  - The current shell PATH still does not expose `git`, so Git commands were
    run with the full Git executable path.

## 2026-07-04 Anime Whisper Local Audio Smoke

- Completed:
  - Verified `models\anime-whisper-ct2-fp16` exists locally and has the
    expected faster-whisper / CTranslate2 model files.
  - Added ASR runtime diagnostics for selected model path, model path
    existence, CTranslate2 availability, CUDA device count, requested device,
    requested compute type, and CPU fallback status.
  - Updated `scripts\smoke_asr_file.py` to print ASR startup diagnostics.
  - Added `scripts\smoke_audio_translate_file.py` for local audio -> ASR ->
    translation smoke testing with `faster_whisper`, `echo` or `deepseek`,
    glossary matching/post-processing, latency reporting, strict
    `--no-cpu-fallback`, and timestamped reports under
    `runtime_logs\asr_model_tests`.
  - Added a DeepSeek missing-key preflight so `deepseek` mode fails before
    loading the ASR model when `DEEPSEEK_API_KEY` is absent.
  - Added `runtime_logs/` to `.gitignore`.
  - Updated testing and runtime-config docs with anime-whisper smoke commands.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\speech\asr_faster_whisper.py scripts\smoke_asr_file.py scripts\smoke_audio_translate_file.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_asr_faster_whisper.py tests\test_smoke_audio_translate_file.py tests\test_smoke_pipeline_terminal.py`
    passed with 12 tests.
  - Anime-whisper ASR-only smoke on `C:\Users\Owen\Desktop\test_miko_audio.mp3`
    with CUDA float16, beam 3, and `--no-cpu-fallback` completed with
    `device=cuda`, `compute_type=float16`, `CTranslate2 CUDA devices: 1`, no
    CPU fallback, 175.09s audio duration, and about 16.8s ASR latency.
  - Anime-whisper ASR + echo translation smoke completed with no CPU fallback
    and wrote `runtime_logs\asr_model_tests\anime_whisper_ct2_fp16_test_20260704_121339.txt`.
  - Large-v3 baseline ASR + echo translation smoke completed with no CPU
    fallback and wrote
    `runtime_logs\asr_model_tests\large_v3_baseline_20260704_121449.txt`.
  - DeepSeek missing-key preflight returned a clear error without loading the
    ASR model.
  - `.venv\Scripts\pytest.exe` passed with 107 tests.
  - Project scan found no pasted `sk-` DeepSeek API key.
- Notes:
  - `DEEPSEEK_API_KEY` was not present in the process environment, so the
    DeepSeek translation smoke was not run in this pass.
  - On the local Miko test audio, anime-whisper was faster than local large-v3
    but produced repeated/hallucinated text in several sections. Large-v3 was
    slower but much more coherent on this sample.

## 2026-07-04 Electron Live Overlay Diagnostics

- Completed:
  - Added bridge-side result-log instrumentation for Electron live status and
    subtitle broadcasts, including connected client count, segment id,
    source/translation character counts, and latency.
  - Added ASCII-safe console diagnostics for bridge status/subtitle events so
    PowerShell output remains readable even when CJK subtitle text would render
    as mojibake.
  - Hardened `launch.ps1` startup encoding by switching the console to UTF-8
    and setting `PYTHONUTF8=1` plus `PYTHONIOENCODING=utf-8` for the launched
    Python process.
- Tests:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py`
    passed.
  - `launch.ps1` parsed successfully as a PowerShell scriptblock.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16
    tests.
  - `npm run typecheck` passed after prepending `C:\Program Files\nodejs` to
    the test process PATH.
  - `.venv\Scripts\pytest.exe` passed with 107 tests.
  - Project scan found no pasted `sk-` DeepSeek API key.
- Notes:
  - The next live run should inspect `--overlay-result-log` for
    `[BridgeSubtitle] clients=...` entries. `clients=0` means Electron did not
    connect to the Python bridge; `clients>0` means the subtitle reached the
    WebSocket bridge and the remaining issue is in Electron main/IPC/renderer
    display.

## 2026-07-04 Electron Live Overlay Subtitle Display Fix

- Completed:
  - Fixed the Electron multi-window preload path and build output by compiling
    preload as CommonJS `preload.cjs` and loading that file from every
    BrowserWindow.
  - Confirmed the previous visible mock subtitle was the renderer store's
    initial state; renderer windows were not receiving the preload IPC API, so
    main-process state broadcasts could not update the subtitle window.
  - Kept renderer security settings intact: `nodeIntegration: false`,
    `contextIsolation: true`, and `sandbox: true`.
  - Added Electron frontend debug logging across backend WebSocket receive,
    manager state patch/broadcast, and renderer state subscription.
  - Changed Electron live launcher lifetime so the Python bridge remains alive
    until manual shutdown instead of being tied to short-lived frontend command
    behavior.
  - Skipped all-silence WASAPI fallback chunks in continuous live capture so
    empty startup chunks are not sent to GPU ASR.
  - Hardened subtitle-window CSS so the live subtitle card/content fills the
    transparent BrowserWindow and wraps long text.
- Tests:
  - `npm run typecheck` passed.
  - `npm run lint` passed.
  - `npm run build` passed and generated `out\preload\preload.cjs`.
  - `.venv\Scripts\pytest.exe tests\test_overlay_pipeline_app.py tests\test_electron_overlay.py`
    passed with 22 tests.
  - `.venv\Scripts\pytest.exe` passed with 108 tests.
  - Project scan found no pasted `sk-` DeepSeek API key.
  - Live Electron run with CUDA large-v3 and DeepSeek showed
    `[BridgeSubtitle] clients=1` in the Python bridge log and
    `renderer subtitle stateUpdated ... translatedChars=...` in the Electron
    frontend log.
- Notes:
  - `work\electron_live_debug_cjs_preload_electron.txt` confirms real subtitle
    events reached the subtitle renderer after the CommonJS preload fix.
