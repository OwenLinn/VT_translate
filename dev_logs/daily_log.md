# Daily Log

## Format

```md
## YYYY-MM-DD

### Work Done

- ...

### Tests Run

- ...

### Problems

- ...

### Next Steps

- ...
```

## 2026-07-01

### Work Done

- Created the Stage 0 scaffold for the YouTube Live Translator Overlay project.
- Added documentation, development logs, package folders, script placeholders,
  config example, requirements, pyproject metadata, and a minimal main module.
- Implemented Stage 1 config loading, logging setup, prompt building, DeepSeek
  API translation client, and translation smoke script.
- Added unit tests for config, prompt builder, and DeepSeek client behavior.
- Added DeepSeek model selection validation for `deepseek-v4-flash` and
  `deepseek-v4-pro`.
- Implemented Stage 2 WASAPI loopback capture, PCM conversion, WAV output, and
  audio capture smoke script.
- Added unit tests for resampling, WAV writing, loopback device listing, capture
  behavior, and no-frame fallback.
- Implemented Stage 3 faster-whisper file ASR wrapper and smoke script.
- Added unit tests for ASR language handling, model options, missing file
  errors, and CUDA fallback.
- Implemented Stage 4 energy VAD, segmenter, task queue, subtitle pipeline, and
  terminal pipeline smoke script.
- Added local audio file and WASAPI loopback modes to the terminal pipeline.
- Added `--max-audio-seconds` for three-minute local audio stability tests.
- Implemented Stage 5 PySide6 overlay test window with dragging, always-on-top,
  configurable text visibility, font sizes, colors, and background opacity.
- Implemented Stage 6 overlay pipeline app that connects local/loopback audio,
  VAD, ASR, DeepSeek translation, and the PySide6 overlay.
- Added Start/Stop controls and worker-thread subtitle updates so the overlay
  remains responsive during ASR and translation.
- Added `--overlay-pipeline-test` CLI options and optional Stage 6 result log
  output.
- Implemented Stage 7 manual glossary SQLite storage, repository APIs, prompt
  injection, conservative post-processing, and CLI management.
- Implemented Stage 8 SQLite-backed settings persistence and PySide6 settings
  window.
- Implemented Stage 9 subtitle JSONL logging, TXT/SRT export, and pipeline log
  integration.
- Verified CUDA ASR after adding CUDA Toolkit 12.0 `bin` to the process `PATH`.
- Implemented Stage 10 glossary candidate extraction from subtitle history.
- Added saved candidate status management for pending, accepted, and ignored
  suggestions.
- Added heuristic and DeepSeek-based glossary candidate classification.
- Added CLI workflow for extracting, listing, AI-classifying, accepting, and
  ignoring glossary candidates.
- Implemented continuous live loopback capture for the overlay pipeline using
  repeated short audio chunks.
- Added live overlay CLI options for continuous capture chunk duration and
  bounded smoke chunk counts.
- Implemented a Liquid Glass-inspired custom PySide6 soft glass overlay style.
- Added configurable glass panel painting, subtitle fade/slide animation,
  cross-fade updates, drag feedback, and classic/glass smoke-test switching.
- Added off-by-default native Windows backdrop attempts for experimental Mica,
  Acrylic, and Mica Alt effects.
- Implemented Local Agreement streaming subtitles with rolling audio windows,
  short ASR ticks, confirmed-prefix commits, partial events, and final
  full-sentence rewrites.
- Added recent-silence finalization to the streaming runner.
- Added streaming runtime config, terminal `--streaming-strategy`, overlay
  partial/final display support, and final subtitle reviser.
- Made terminal and overlay pipelines follow `streaming.enabled` by default, so
  the example config uses Local Agreement unless fixed segments are explicitly
  requested.

### Tests Run

- `.venv\Scripts\python.exe -m yt_live_translator.main`
- `.venv\Scripts\python.exe -m yt_live_translator.main --help`
- `.venv\Scripts\pytest.exe` passed with 13 tests.
- `.venv\Scripts\python.exe scripts\smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-TW` passed with manual API key entry.
- `.venv\Scripts\python.exe scripts\smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-CN` passed with manual API key entry.
- `.venv\Scripts\pytest.exe` passed with 21 tests after Stage 2 changes.
- `.venv\Scripts\python.exe scripts\smoke_audio_capture.py --list-devices`
  detected five WASAPI loopback devices.
- `.venv\Scripts\python.exe scripts\smoke_audio_capture.py --seconds 6 --output work\stage2_test_capture_watchdog.wav --source-hint "C:\Users\Owen\Desktop\test_miko_audio.mp3"` captured real system audio.
- `work\stage2_test_capture_watchdog.wav` verified as 6.0 seconds, 16000 Hz,
  mono, RMS 1903.85.
- `.venv\Scripts\pytest.exe` passed with 27 tests after Stage 3 changes.
- `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage3_english_tts.wav --language en --model tiny --device cpu --compute-type int8 --beam-size 1` transcribed English audio.
- `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage2_test_capture_watchdog.wav --language ja --model tiny --device cpu --compute-type int8 --beam-size 1` transcribed Japanese audio.
- `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage3_english_tts.wav --language en --model tiny --device cuda --compute-type float16 --beam-size 1` confirmed CPU fallback when CUDA runtime was unavailable.
- `.venv\Scripts\pytest.exe` passed with 33 tests after Stage 4 changes.
- `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000` printed terminal pipeline output.
- `work\stage4_manual_pipeline_smoke.ps1` ran the local MP3 pipeline with
  DeepSeek translation after manual API key entry and exited with code 0.
- `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --max-audio-seconds 180 --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 0 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --deepseek-timeout 30` processed about three minutes of local audio with echo translation.
- `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --max-audio-seconds 180 --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 60 --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 0 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000` processed about three minutes of local audio with DeepSeek translation; 35 segments completed, exit code 0.
- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-test --overlay-test-seconds 3` opened and auto-closed the overlay smoke window.
- `.venv\Scripts\pytest.exe` passed with 42 tests after Stage 6 changes.
- `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\main.py src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\core\subtitle_pipeline.py` passed.
- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 15 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --close-on-finish --auto-close-seconds 30` completed the no-key overlay pipeline smoke test.
- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 60 --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 20 --vad-threshold 0.005 --min-speech-ms 800 --max-speech-ms 5000 --silence-end-ms 700 --padding-ms 400 --close-on-finish --auto-close-seconds 90 --overlay-result-log work\stage6_overlay_pipeline_deepseek_latest.txt` completed the real DeepSeek overlay pipeline smoke test with a process-scoped API key.
- `.venv\Scripts\python.exe -m yt_live_translator.main` printed the scaffold OK message.
- `.venv\Scripts\pytest.exe` passed with 49 tests after Stage 7 changes.
- `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 add --source Miko --target-zh-tw MikoTW --target-zh-cn MikoCN --source-lang ja --term-type person --note streamer` added a manual glossary term.
- `.venv\Scripts\python.exe scripts\glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 list` listed the glossary term.
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
- `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --language ja --model tiny --device cuda --compute-type float16 --beam-size 1 --no-cpu-fallback` completed with CUDA after adding CUDA Toolkit 12.0 `bin` to `PATH`.
- `.venv\Scripts\pytest.exe` passed with 57 tests after Stage 10 changes.
- `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\storage\db.py src\yt_live_translator\storage\glossary_candidate_repo.py src\yt_live_translator\translate\glossary_candidates.py scripts\glossary_candidates_cli.py` passed.
- `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 --log work\stage10_subtitle_log_smoke.jsonl extract --min-occurrences 2 --limit 10` extracted glossary candidates from subtitle history.
- `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 accept --id 1 --target-zh-tw MikoTW --target-zh-cn MikoCN` accepted a candidate into the manual glossary.
- `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 ignore --id 2` ignored a candidate.
- `.venv\Scripts\python.exe scripts\glossary_candidates_cli.py --db work\stage10_ai_candidates_smoke.sqlite3 classify-ai --limit 2 --deepseek-timeout 60` classified candidates with DeepSeek using a process-scoped API key.
- Final full check: `.venv\Scripts\pytest.exe` passed with 57 tests.
- Final full check: all Python files under `src`, `scripts`, and `tests`
  passed `py_compile`.
- Final full check: `.venv\Scripts\python.exe -m yt_live_translator.main`
  printed the scaffold OK message.
- Final full check: project file scan found no pasted DeepSeek API key.
- Final GPU check: faster-whisper completed with `device=cuda`,
  `compute_type=float16`, `--no-cpu-fallback`, and about 10.3 seconds latency
  after adding CUDA Toolkit 12.0 `bin` to process `PATH`.
- `.venv\Scripts\pytest.exe` passed with 58 tests after continuous capture changes.
- `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\main.py tests\test_overlay_pipeline_app.py` passed.
- Launched continuous live overlay with `--continuous-loopback`,
  `--loopback-chunk-seconds 6`, CUDA ASR, DeepSeek translation, subtitle log,
  and result log while the user played a livestream.
- `work\continuous_live_overlay_latest.txt` showed repeated chunk output from
  chunks 1, 2, and 3.
- `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\core\config.py src\yt_live_translator\main.py tests\test_overlay_window.py tests\test_config.py` passed.
- `.venv\Scripts\pytest.exe tests\test_overlay_window.py tests\test_config.py`
  passed with 13 tests after soft glass overlay changes.
- `.venv\Scripts\pytest.exe` passed with 63 tests after soft glass overlay
  changes.
- All Python files under `src`, `scripts`, and `tests` passed `py_compile`.
- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-test --style glass --overlay-test-seconds 3`
  opened and auto-closed the glass overlay smoke window.
- Project scan found no pasted `sk-` DeepSeek API key.
- `.venv\Scripts\pytest.exe tests\test_streaming_agreement.py tests\test_config.py`
  passed with 16 tests.
- `.venv\Scripts\pytest.exe tests\test_overlay_pipeline_app.py tests\test_overlay_window.py tests\test_subtitle_pipeline.py tests\test_streaming_agreement.py tests\test_final_subtitle_reviser.py tests\test_config.py`
  passed with 34 tests.
- `.venv\Scripts\pytest.exe` passed with 78 tests after Local Agreement
  streaming changes.
- All Python files under `src`, `scripts`, and `tests` passed `py_compile`.
- Local streaming terminal smoke on `work\stage3_english_tts.wav` produced a
  `[FINAL]` event with about 1.4 seconds latency.
- The same local terminal smoke without `--streaming-strategy` also produced
  streaming-format output through the config default.
- Local streaming terminal smoke on
  `C:\Users\Owen\Desktop\test_miko_audio.mp3` produced a `[FINAL]` event with
  about 3.1 seconds latency.
- Overlay pipeline streaming smoke with `work\stage3_english_tts.wav` opened,
  processed streaming output, and exited with code 0.

### Problems

- Windows console encoding initially failed on Chinese output; smoke script and
  manual test terminal were updated to use UTF-8.
- An invalid API key attempt returned 401; error handling was updated to avoid
  printing API response details that may include masked key fragments.
- A no-audio loopback read can block; capture now uses read timeout protection
  and silence fallback for missing frames.
- CUDA ASR originally failed because `cublas64_12.dll` was unavailable; after
  CUDA Toolkit 12.0 was installed and its `bin` directory was added to the
  process `PATH`, GPU ASR succeeded with no CPU fallback.
- DeepSeek translation timed out once with the default 10 second timeout during
  Stage 4 smoke testing; the terminal pipeline now supports
  `--deepseek-timeout`, and the manual smoke passed with 30 seconds.
- The PowerShell `Read-Host -AsSecureString` flow did not visibly continue after
  key entry, so the long DeepSeek stability test was rerun with a process-scoped
  environment variable.
- The Stage 6 DeepSeek smoke used CPU `tiny` ASR for speed, so ASR text quality
  is not representative of the final target model.
- PowerShell displays UTF-8 Japanese/Chinese log output as mojibake in some
  reads, but the continuous overlay pipeline writes UTF-8 logs and keeps
  updating the Qt overlay.
- Native Acrylic/Mica is not enabled by default; the Basic Glass overlay is the
  reliable path until native effects are explicitly implemented and tested.
- Short test clips with sentence-ending punctuation can go straight to final
  without a visible partial event; partial event formatting and partial/final
  pipeline behavior are covered by automated tests.

## 2026-07-02

### Work Done

- Launched continuous live loopback overlay pipeline against an active YouTube
  livestream (Japanese → Traditional Chinese) using the DeepSeek API.
- Diagnosed and fixed a critical issue where the ASR model was re-created on
  every streaming tick / segment call, causing ~43 seconds of model load
  overhead per tick.
- Added `FasterWhisperTranscriber` as a first-class reusable ASR API and wired
  both terminal and overlay pipelines to reuse one WhisperModel across all
  segment/tick calls.
- Fixed CPU fallback metadata so fallback results report effective CPU `int8`
  settings instead of stale CUDA settings.
- Verified the newly downloaded local `models\faster-whisper-large-v3` model
  with CUDA float16 and updated config/docs to use it by default.
- Fixed overlay pipeline shutdown cleanup so auto-close/app quit requests stop
  the worker and clean up a still-running QThread.
- Verified that after the fix, pipeline latency dropped from ~42s to ~1.6-4.4s
  per output event.
- Identified that the tiny ASR model produces poor Japanese recognition for
  game stream audio, outputting garbled text with replacement characters.
- Confirmed that HuggingFace Hub is unreachable through the current VPN
  (Radmin VPN), preventing download of larger ASR models.
- Documented all findings in `issues.md`.

### Tests Run

- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --source-lang ja --target zh-TW --translation deepseek --model tiny --device cuda` — pipeline runs, produces partial/final events with 1.6-4.4s latency.
- CUDA tiny model load time measured at ~43s independently.
- WASAPI loopback capture verified working: default device JBL Charge 3, 2ch 44100Hz, RMS 1552 at normal stream volume.
- HuggingFace Hub connectivity confirmed blocked (WinError 10054).
- `.venv\Scripts\pytest.exe tests\test_asr_faster_whisper.py tests\test_subtitle_pipeline.py tests\test_smoke_pipeline_terminal.py tests\test_overlay_pipeline_app.py`
  passed with 19 tests after reusable ASR changes.
- `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --no-glossary --no-subtitle-log`
  produced a streaming `[FINAL]` event with about 1.8 seconds latency.
- Final reusable-ASR check: `.venv\Scripts\pytest.exe` passed with 80 tests.
- Final reusable-ASR check: all Python files under `src`, `scripts`, and
  `tests` passed `py_compile`.
- `.venv\Scripts\python.exe scripts\smoke_asr_file.py --audio work\stage3_english_tts.wav --language en --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --no-cpu-fallback`
  transcribed 7.24 seconds of English audio in about 4.6 seconds.
- `.venv\Scripts\python.exe scripts\smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --max-audio-seconds 8 --no-glossary --no-subtitle-log`
  produced partial/final events; the first output was about 4.0 seconds
  including model warmup, later ticks were about 0.7 seconds.
- `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --close-on-finish --auto-close-seconds 30 --no-glossary --no-subtitle-log --overlay-result-log work\large_v3_overlay_smoke.txt`
  opened the overlay, emitted partial/final events with local large-v3, wrote
  `Overlay pipeline finished`, and exited with code 0.

### Problems

- CUDA tiny model load takes ~43 seconds, which is abnormally slow and needs
  separate driver/runtime investigation.
- The first overlay large-v3 smoke attempt did not exit before the command
  timeout; this was fixed by adding app-exit QThread cleanup.
- HuggingFace Hub may still be inaccessible through Radmin VPN, but local
  large-v3 is now available in the workspace.
- tiny ASR quality remains insufficient for Japanese game stream audio and
  should only be used for fast smoke tests.

### Next Steps

- Investigate CUDA model loading speed (likely driver/runtime issue).
- Run longer livestream quality checks with the local large-v3 model.
- Continue product hardening: CUDA PATH diagnostics, quality testing with
  larger models.

### Overlay Hotfix

- Fixed a GUI-threading bug in the overlay pipeline app: worker signals were
  connected to plain Python callbacks, so subtitle/status updates and app-exit
  scheduling could run from the worker thread. A main-thread `QObject` bridge
  now receives worker signals and updates Qt widgets safely.
- Made pipeline subtitle updates non-animated and force a repaint so old
  opacity/position animation state cannot hide the current subtitle text.
- Changed close-on-finish and auto-close handling to wait for the worker thread
  to finish, then exit the app from the Qt main thread after a short repaint
  delay.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_pipeline_app.py src\yt_live_translator\ui\overlay_window.py`
  - `.venv\Scripts\pytest.exe tests\test_overlay_pipeline_app.py tests\test_overlay_window.py`
    passed with 12 tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --audio-file work\stage3_english_tts.wav --source-lang en --target zh-TW --translation echo --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --close-on-finish --auto-close-seconds 60 --no-glossary --no-subtitle-log --overlay-result-log work\large_v3_overlay_ui_bridge_echo.txt`
    displayed/wrote partial and final subtitles, exited with code 0, and left
    no Python process behind.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --streaming-strategy local_agreement --loopback-chunk-seconds 4 --max-loopback-chunks 1 --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 90 --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --close-on-finish --auto-close-seconds 180 --no-glossary --no-subtitle-log --overlay-result-log work\live_gpu_large_v3_deepseek_ui_bridge.txt`
    completed a live loopback + CUDA large-v3 + DeepSeek test in about
    14 seconds. The UTF-8 log contains source
    `ご視聴ありがとうございました。`, translation `感謝您的收看。`,
    and 5231 ms translation latency.
  - `.venv\Scripts\pytest.exe` passed with 80 tests.

### Overlay Visibility Fix

- Fixed a visibility issue where the controls window could show subtitles while
  the overlay itself was not visible. The overlay is now a frameless top-level
  window instead of a `Qt.Tool` window, is positioned once at the bottom center
  of the active screen, and exposes `ensure_visible()` to show/raise/repaint it
  whenever status or subtitle text changes.
- The overlay pipeline now calls `ensure_visible()` for waiting/status text and
  real subtitle updates, so a visible controls-window preview and the floating
  subtitle overlay stay in sync.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\ui\overlay_pipeline_app.py`
  - `.venv\Scripts\pytest.exe tests\test_overlay_window.py tests\test_overlay_pipeline_app.py`
    passed with 12 tests.

### Overlay Text Rendering Fix

- Fixed a second overlay display issue where the overlay window was visible and
  draggable, but subtitle text still did not appear even though the controls
  window showed current subtitles. The overlay now stores the latest source and
  translation text and paints them directly in the top-level window's
  `paintEvent` using `QPainter`, so transparent-window child-label rendering is
  no longer the only text path.
- QLabel rendering remains in place, but the direct painter path is the
  reliable fallback for the transparent overlay window.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\overlay_window.py src\yt_live_translator\ui\overlay_pipeline_app.py`
  - `.venv\Scripts\pytest.exe tests\test_overlay_window.py tests\test_overlay_pipeline_app.py`
    passed with 12 tests.

### QML Overlay Phase 1

- Added a QML Liquid Glass-inspired overlay frontend shell without connecting it
  to ASR, DeepSeek, glossary, or the live subtitle pipeline.
- Added `src\yt_live_translator\ui\qml_overlay` with:
  - `OverlayBridge` QObject
  - `qml_overlay_app.py`
  - `qml_resources.py`
  - `MainOverlay.qml`
  - Phase 1 components for subtitle bar, settings icon, control hub, option
    popover, setting rows, pill buttons, status badge, and basic glass card.
- Added `--qml-overlay-test` and `--qml-overlay-test-seconds`.
- Added `[ui]` and `[qml_overlay]` config sections while keeping the Widgets
  overlay fallback intact.
- Added `docs\09_qml_overlay_design.md` and updated runtime/config/testing docs
  plus `AGENTS.md` with QML overlay development rules.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\core\config.py src\yt_live_translator\main.py src\yt_live_translator\ui\qml_overlay\qml_bridge.py src\yt_live_translator\ui\qml_overlay\qml_overlay_app.py src\yt_live_translator\ui\qml_overlay\qml_resources.py`
  - `.venv\Scripts\pytest.exe tests\test_config.py tests\test_qml_overlay.py`
    passed with 15 tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 3`
    opened the QML overlay and exited with code 0.

### QML Overlay Phase 2

- Added Liquid Glass visual polish to the QML overlay:
  - layered glass card shadows
  - translucent highlights
  - iridescence border and bottom accent
  - smoother opacity/font/card animations
- Added Phase 2 tuning mode:
  - `--qml-overlay-tuning`
  - `--qml-overlay-tuning-seconds`
  - `TuningControls.qml`
  - runtime sliders for subtitle opacity, glass opacity, card opacity,
    iridescence opacity/width, corner radius, shadow opacity, highlight
    opacity, translation/source font sizes, and animation duration.
- Expanded `OverlayBridge` with visual tuning properties and setter slots.
- Added Copy current parameters, which copies a TOML snippet to the clipboard
  when available and prints it to stdout.
- Kept QML Phase 2 separate from ASR, DeepSeek, glossary, and live pipeline
  execution.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\main.py src\yt_live_translator\ui\qml_overlay\qml_bridge.py src\yt_live_translator\ui\qml_overlay\qml_overlay_app.py`
  - `.venv\Scripts\pytest.exe tests\test_qml_overlay.py tests\test_config.py`
    passed with 17 tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 2`
    opened the normal QML overlay and exited with code 0.

### Electron Overlay Phase 2 Prototype

- Added `frontend\electron-overlay` as a separate Electron / React /
  TypeScript frontend prototype.
- Added secure Electron window setup with transparent always-on-top overlay
  behavior and renderer security flags.
- Added React Liquid Glass-inspired material/motion components:
  - `GlassCard`
  - `GlassEdge`
  - `GlassHighlight`
  - `LiquidThumb`
  - `SubtitleBar`
  - `ControlHubCard`
  - `OptionPopoverCard`
  - `TuningPanel`
- Added mock subtitle event stream and WebSocket message contracts for the
  future `ws://127.0.0.1:8765` Python bridge.
- Added Python CLI launch flags:
  - `--electron-overlay-test`
  - `--electron-overlay-tuning`
- Kept Phase 2 visual-only: no ASR, DeepSeek, glossary, audio capture, or
  pipeline integration was added.
- Verification:
  - `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_app.py src\yt_live_translator\main.py`
    passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 9
    tests.
  - `.venv\Scripts\pytest.exe` passed with 97 tests.
  - Frontend `npm run typecheck` and live Electron launch were not run because
    `npm` is not available in the current PowerShell PATH.

### Electron Overlay npm Dependency Fix

- Fixed the npm install dependency conflict by downgrading Vite from 6.x to
  `^5.4.0`, which is supported by `electron-vite@2.3.0`.
- Regenerated `package-lock.json` through `npm install`; no `--force` or
  `--legacy-peer-deps` was used.
- Added the renderer input expected by electron-vite so `dev:mock` and
  `dev:tuning` can start.
- Added `.gitignore` entries for Electron generated dependencies and build
  output.
- Verification:
  - `npm install` passed.
  - `npm run typecheck` passed.
  - `npm run build` passed.
  - `npm run dev:mock` started the renderer dev server and Electron app.
  - `npm run dev:tuning` started the renderer dev server and Electron app.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 9
    tests.

### Electron Overlay Multi-Window Split

- Reworked Electron overlay default mode from one transparent BrowserWindow to
  multi BrowserWindow composition:
  - `SubtitleWindow`
  - `SettingsIconWindow`
  - `ControlCardWindow`
  - `PopoverWindow`
- Added `OverlayWindowManager` as the main-process UI state source of truth for
  Phase 2 mock/tuning mode.
- Added typed IPC contracts in `src\shared\overlayIpcTypes.ts`.
- Added geometry anchoring so settings/control/popover windows follow the
  subtitle window.
- Kept `OVERLAY_WINDOW_MODE=single_legacy` for fallback.
- Verification:
  - `npm run typecheck` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 13
    tests.

### Electron Overlay Bottom-Clipping Fix

- Fixed menu clipping when the overlay is positioned near the bottom of the
  screen.
- Added bottom-aware geometry for control card and popover windows.
- Preserved active popover row offset when the subtitle anchor moves.
- Added internal scroll protection for oversized control/tuning windows.
- Cleaned mojibake mock subtitle strings in Electron main-process state.
- Verification:
  - `npm run typecheck` passed.
  - `npm run lint` passed.
  - `npm run build` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 14
    tests.
  - `.venv\Scripts\pytest.exe` passed with 102 tests.

### Electron Overlay Live Pipeline Bridge

- Added Python `ElectronOverlayBridge` with a localhost WebSocket server at
  `ws://127.0.0.1:8765`.
- Added `--electron-overlay-live` to launch the real Python pipeline with the
  Electron multi-window overlay.
- Added Electron main-process `BackendBridgeClient` for live subtitle/status
  events and Start/Stop/settings commands.
- Added `npm run dev:live`.
- Kept ASR, DeepSeek, glossary, subtitle logging, and API keys in Python.
- Verification:
  - Python bridge/main files passed `py_compile`.
  - `npm run typecheck` passed.
  - `npm run build` passed.
  - `npm run lint` passed.
  - `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16
    tests.
  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-tuning --qml-overlay-tuning-seconds 2`
    opened the tuning UI and exited with code 0.
  - `.venv\Scripts\pytest.exe` passed with 88 tests.
  - All Python files under `src`, `scripts`, and `tests` passed
    `py_compile`.

  - `.venv\Scripts\python.exe -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 2`
    opened the normal QML overlay and exited with code 0.

## 2026-07-04

### Work Done

- Created `launch.bat` and `launch.ps1` interactive launch scripts with
  6-step parameter prompts (API key, languages, model, overlay type, audio
  source).
- Diagnosed two Electron overlay live pipeline issues:
  1. No subtitle output in Electron multi-window GUI despite pipeline
     producing events on the Python side.
  2. Settings icon button click not responding (no control card or popover).
- Root cause analysis:
  - Issue 1: WebSocket message `data` type inconsistency across Electron
    main-process WebSocket implementations (could be string, ArrayBuffer, or
    Buffer). Parse errors silently caused the connection to appear
    disconnected. Additionally, pipeline auto-started before Electron
    connected, so early events were broadcast to empty client set.
  - Issue 2: The settings-icon renderer's zustand `useEffect` dependency was
    an unstable function reference, potentially causing listener leaks.
    Error was silently discarded with `void`.
- Fixed `BackendBridgeClient` (`backendBridgeClient.ts`):
  - Added `coerceMessageData()` supporting string, ArrayBuffer, and
    ArrayBufferView payloads.
  - Parse errors now log and continue instead of disconnecting.
  - Added exponential reconnect back-off.
  - Added debug `console.log` for connect/disconnect/event receive.
- Fixed `OverlayWindowManager` (`overlayWindowManager.ts`):
  - Added `console.log` in `applyBackendEvent`, `toggleControlCard` for
    subtitle/status/settings/control visibility debugging.
- Fixed `MultiWindowApp` (`App.tsx`):
  - Changed `useEffect` dependency from `applyUiState` to `windowType`.
  - Added `console.log` for state subscription lifecycle.
  - Fixed settings-icon `onClick` to await and log IPC result.
- Fixed `ElectronOverlayBridge` (`electron_overlay_bridge.py`):
  - Added `_pipeline_running` flag and `_is_pipeline_active()`.
  - Client connect now sends correct pipeline status ("running"/"idle").
  - Added `print()` logging for client connect/disconnect, commands, and
    broadcast cleanup.
- Current-state check after user-side changes:
  - Confirmed Python Electron launch uses the npm/node PATH fallback through
    `electron_overlay_env()`.
  - Hardened `launch.ps1` to run Python with an argument array instead of
    `Invoke-Expression`, preserving local audio paths with spaces.
  - Corrected the launch script's Electron note so it says Python starts the
    Electron frontend automatically.
  - Removed an unused import from `electron_overlay_bridge.py`.

### Tests Run

- `npm run typecheck` passed.
- `npm run build` passed.
- `npm run lint` passed.
- `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py` passed.
- `.venv\Scripts\pytest.exe tests\test_electron_overlay.py` passed with 16 tests.
- `.venv\Scripts\pytest.exe` passed with 104 tests.
- Current-state check: `.venv\Scripts\python.exe -m py_compile src\yt_live_translator\ui\electron_overlay_bridge.py src\yt_live_translator\ui\electron_overlay_app.py src\yt_live_translator\main.py`
  passed.
- Current-state check: `.venv\Scripts\pytest.exe tests\test_electron_overlay.py`
  passed with 16 tests.
- Current-state check: `npm run typecheck`, `npm run lint`, and
  `npm run build` passed after the test process prepended
  `C:\Program Files\nodejs` to PATH.
- Current-state check: `launch.ps1` parsed successfully as a PowerShell
  scriptblock.
- Current-state check: `.venv\Scripts\pytest.exe` passed with 104 tests.
- Current-state check: project scan found no pasted `sk-` DeepSeek API key.

### Problems

- Git is not installed on this machine; no version control snapshot available.
- Current workspace also has no `.git` directory, so Git status/staging/commit
  cannot be updated here until repository metadata and Git executable are both
  available.
- Electron overlay live pipeline has never been end-to-end tested with real
  subtitle output reaching the GUI. The fixes here add robust parsing and
  debug logging so the next live test run will produce actionable output.

### Next Steps

- Run a live end-to-end test and inspect the debug console output.
- If subtitles still do not appear, the debug logs will pinpoint the exact
  failure point in the Python → WebSocket → main process → IPC → renderer chain.
