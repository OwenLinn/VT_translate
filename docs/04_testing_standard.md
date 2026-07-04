# Testing Standard

## General Rules

Every stage must include a smoke test.

Before moving to the next stage:

- Run relevant script
- Confirm expected behavior
- Update dev logs
- Document known issues

## Unit Tests

Run:

```bash
pytest
```

Required tests:

- config loading
- prompt building
- glossary matching
- segmenter behavior

## Smoke Tests

### Stage 0

```bash
python -m yt_live_translator.main
pytest
```

Expected:

- main module prints `YouTube Live Translator Overlay - scaffold OK`
- project package imports successfully
- scaffold tests pass

### Translation

```bash
python scripts/smoke_translate.py --target zh-TW
python scripts/smoke_translate.py --target zh-CN
```

Expected:

- returns translated text
- no API key printed
- clear error if API key missing

### Audio Capture

```bash
python scripts/smoke_audio_capture.py --seconds 10 --output test_capture.wav
```

Expected:

- WAV file created
- captured audio is audible
- no crash when audio is silent

### ASR File

```bash
python scripts/smoke_asr_file.py --audio sample_en.wav --language en
python scripts/smoke_asr_file.py --audio sample_ja.wav --language ja
python scripts/smoke_asr_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --language ja --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --no-cpu-fallback
python scripts/smoke_asr_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --language ja --model models\anime-whisper-ct2-fp16 --device cuda --compute-type float16 --beam-size 3 --no-cpu-fallback
```

Expected:

- transcription printed
- language respected
- GPU usage if available
- local `models\faster-whisper-large-v3` loads without HuggingFace download
- local `models\anime-whisper-ct2-fp16` loads as a faster-whisper-compatible
  CTranslate2 model without Transformers

### Local Audio ASR + Translation File Test

```bash
python scripts/smoke_audio_translate_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --asr-provider faster_whisper --asr-model models\anime-whisper-ct2-fp16 --device cuda --compute-type float16 --beam-size 3 --translation echo --no-cpu-fallback
python scripts/smoke_audio_translate_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --asr-provider faster_whisper --asr-model models\anime-whisper-ct2-fp16 --device cuda --compute-type float16 --beam-size 3 --translation deepseek --no-cpu-fallback
python scripts/smoke_audio_translate_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --asr-provider faster_whisper --asr-model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 3 --translation deepseek --no-cpu-fallback
```

Expected:

- selected model path, device, compute type, CTranslate2 CUDA device count, and
  CPU fallback status are printed
- ASR output and translation output are printed
- ASR latency, translation latency, and total latency are printed
- `--no-cpu-fallback` fails clearly instead of silently using CPU
- reports are written under `runtime_logs/asr_model_tests/`

### Terminal Pipeline

```bash
python scripts/smoke_pipeline_terminal.py --source-lang auto --target zh-TW
python scripts/smoke_pipeline_terminal.py --streaming-strategy local_agreement --target zh-TW
python scripts/smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --max-audio-seconds 8 --no-glossary --no-subtitle-log
```

Expected:

- terminal prints source text and translation
- latency is printed
- can stop with Ctrl+C safely
- streaming mode prints `[PARTIAL]` and `[FINAL]` blocks with source,
  translation, and latency
- partial translation is rate-limited and final translation rewrites the full
  finalized subtitle

### Overlay Test

```bash
python -m yt_live_translator.main --overlay-test
python -m yt_live_translator.main --overlay-test --style glass --overlay-test-seconds 3
```

Expected:

- overlay appears
- overlay is draggable
- style settings apply
- glass mode renders a rounded semi-transparent panel with border, highlight,
  shadow, readable text, and fade/slide subtitle updates
- `--style classic` or `overlay.glass.enabled = false` restores the classic
  subtitle panel

### Overlay Pipeline Test

```bash
python -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 15 --close-on-finish
python -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 8 --close-on-finish
```

For a real translation smoke test, provide `DEEPSEEK_API_KEY` in the process
environment and use `--translation deepseek`.

Expected:

- overlay appears
- control window can start and stop the pipeline
- subtitle updates are sent from the worker thread to the UI
- UI remains responsive while ASR and translation run

### QML Overlay Phase 1 Test

```bash
python -m yt_live_translator.main --qml-overlay-test
python -m yt_live_translator.main --qml-overlay-test --qml-overlay-test-seconds 3
```

Expected:

- QML overlay appears
- Subtitle bar shows placeholder source and translation text
- Settings icon opens and closes the control hub
- Control rows open option popovers
- Start/Stop only changes QML running state in Phase 1
- Widgets overlay remains available through `--overlay-test`

### QML Overlay Phase 2 Tuning Test

```bash
python -m yt_live_translator.main --qml-overlay-tuning
python -m yt_live_translator.main --qml-overlay-tuning --qml-overlay-tuning-seconds 3
```

Expected:

- QML overlay appears with tuning controls
- Visual sliders update subtitle opacity, glass/card opacity, iridescence,
  edge/RGB split, distortion/reflect parameters, radius, shadow, highlight,
  font sizes, liquid thumb motion, and animation duration
- Copy current parameters prints/copies a TOML snippet
- No ASR, DeepSeek, glossary, or pipeline worker starts in Phase 2

### Electron Overlay Phase 2 Test

Static tests that do not require npm dependencies:

```bash
pytest tests/test_electron_overlay.py
```

Python launcher checks:

```bash
python -m yt_live_translator.main --electron-overlay-test
python -m yt_live_translator.main --electron-overlay-tuning
```

Frontend checks after installing npm dependencies:

```bash
cd frontend/electron-overlay
npm run typecheck
npm run dev:mock
npm run dev:tuning
```

Expected:

- Electron transparent overlay opens in mock mode
- Tuning mode opens with material sliders and presets
- Default mode opens separate subtitle, settings icon, control card, and
  popover BrowserWindows
- `OVERLAY_WINDOW_MODE=single_legacy` keeps the original single-window fallback
- Renderer uses mock events when no WebSocket backend is available
- Electron window keeps `nodeIntegration: false`, `contextIsolation: true`,
  and `sandbox: true`
- Renderer does not read or store API keys
- Widgets and QML fallback overlays remain available
- No ASR, DeepSeek, glossary, or pipeline worker starts in Phase 2

### Electron Overlay Live Test

Local echo smoke test:

```bash
python -m yt_live_translator.main --electron-overlay-live --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-audio-seconds 8 --max-segments 1 --close-on-finish
```

Live YouTube loopback test:

```bash
python -m yt_live_translator.main --electron-overlay-live --continuous-loopback --loopback-chunk-seconds 4 --source-lang auto --target zh-TW --translation deepseek --streaming-strategy local_agreement --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --max-segments 0
```

Expected:

- Python starts a localhost bridge at `ws://127.0.0.1:8765`
- Electron launches in live bridge mode
- Electron subtitle window receives partial/final subtitle events
- Start/Stop controls send commands back to Python
- DeepSeek API key stays in Python environment/config only
- Subtitle log and glossary behavior match the existing overlay pipeline

### Continuous Overlay Pipeline Test

```bash
python -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --loopback-chunk-seconds 4 --max-loopback-chunks 1 --source-lang auto --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --close-on-finish
```

Expected:

- overlay appears
- app captures a short loopback chunk and processes it
- result log or subtitle log shows chunk-based output
- Stop ends after the active capture chunk completes

### Manual Glossary Test

```bash
python scripts/glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 add --source Miko --target-zh-tw MikoTW --target-zh-cn MikoCN --source-lang ja --term-type person
python scripts/glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 list
python scripts/glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 match --text "Miko starts the stream" --source-lang ja --target zh-TW
python scripts/glossary_cli.py --db work\stage7_glossary_smoke.sqlite3 match --text "Miko starts the stream" --source-lang ja --target zh-CN
```

Expected:

- SQLite database is created when missing
- added term appears in list output
- zh-TW and zh-CN matches return the configured target
- matching glossary terms are included in translation prompts
- conservative post-processing replaces obvious leftover source terms only

### Settings UI Test

```bash
python -m yt_live_translator.main --settings-test --settings-test-seconds 3 --settings-db work\stage8_settings_smoke.sqlite3
```

Expected:

- settings window opens
- target/source language, subtitle style, ASR, and DeepSeek controls are shown
- settings repository can persist values and reject invalid values

### Subtitle Log Test

```bash
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl append --segment-id 1 --source "Miko starts" --translation "Miko translated" --source-lang ja --target zh-TW --latency-ms 42 --start 0 --end 2.5
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl list
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-txt --output work\stage9_subtitle_log_smoke.txt
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-srt --output work\stage9_subtitle_log_smoke.srt
```

Expected:

- JSONL subtitle log is appended
- TXT export contains source and translated text
- SRT export contains subtitle timing
- terminal and overlay pipelines write subtitle logs unless disabled

### AI Glossary Candidate Test

```bash
python scripts/subtitle_log_cli.py --log work\stage10_subtitle_log_smoke.jsonl append --segment-id 1 --source "Miko fights Radahn" --translation "Miko translation A" --source-lang en --target zh-TW --latency-ms 10 --start 0 --end 2
python scripts/subtitle_log_cli.py --log work\stage10_subtitle_log_smoke.jsonl append --segment-id 2 --source "Miko meets Radahn" --translation "Miko translation B" --source-lang en --target zh-TW --latency-ms 11 --start 2 --end 4
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 --log work\stage10_subtitle_log_smoke.jsonl extract --min-occurrences 2 --limit 10
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 list --status pending
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 accept --id 1 --target-zh-tw MikoTW --target-zh-cn MikoCN
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 ignore --id 2
```

Optional DeepSeek classification smoke:

```bash
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 classify-ai --limit 20 --deepseek-timeout 60
```

Expected:

- repeated source terms are extracted from subtitle history
- candidates with multiple translation variants are marked inconsistent
- AI classification can fill term type and zh-TW/zh-CN suggestions
- accepted candidates enter the manual glossary
- ignored candidates are not reactivated by later extraction runs
