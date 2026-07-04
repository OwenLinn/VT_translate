# YouTube Live Translator Overlay

Windows desktop real-time translation subtitle overlay for YouTube livestreams.

Stage 0 contains only the project scaffold, documentation, development logs, and
minimal importable Python package.

## Stage 0 Smoke Test

```bash
python -m yt_live_translator.main
pytest
```

Expected main output:

```text
YouTube Live Translator Overlay - scaffold OK
```

## Stage 1 Translation Smoke Test

Configuration is loaded from `config.toml` when present, otherwise from
`config.example.toml`. The DeepSeek API key is read from the environment variable
named by `deepseek.api_key_env` (`DEEPSEEK_API_KEY` by default), or from
`deepseek.api_key` in a local uncommitted `config.toml`.

The DeepSeek model is selected with `deepseek.model`. Supported values are
`deepseek-v4-flash` and `deepseek-v4-pro`.

```bash
python scripts/smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-TW
python scripts/smoke_translate.py --text "Hello everyone, welcome to the stream." --target zh-CN
```

The smoke script prints only the translated text on success. It prints a clear
error when the API key is missing or the API request fails.

## Stage 2 Audio Capture Smoke Test

List WASAPI loopback devices:

```bash
python scripts/smoke_audio_capture.py --list-devices
```

Capture system output to a WAV file:

```bash
python scripts/smoke_audio_capture.py --seconds 10 --output test_capture.wav
```

The smoke script captures from the default WASAPI loopback device, converts the
audio to the configured target format (`16000 Hz`, mono by default), and writes a
16-bit PCM WAV file. If no loopback frames arrive, it fills the missing section
with silence instead of hanging.

## Stage 3 ASR File Smoke Test

Run faster-whisper on a local audio file:

```bash
python scripts/smoke_asr_file.py --audio sample_en.wav --language en --model tiny --device cpu --compute-type int8
python scripts/smoke_asr_file.py --audio sample_ja.wav --language ja --model tiny --device cpu --compute-type int8
python scripts/smoke_asr_file.py --audio "C:\Users\Owen\Desktop\test_miko_audio.mp3" --language ja --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --no-cpu-fallback
```

Supported language values are `auto`, `en`, and `ja`. The model, device,
compute type, and beam size can be overridden from the command line. If CUDA ASR
fails and fallback is enabled, the smoke script retries with CPU `int8` and
prints a warning.

The project now expects the local large model at
`models\faster-whisper-large-v3` for higher-quality Japanese ASR without
downloading from HuggingFace at runtime.

## Stage 4 Terminal Pipeline Smoke Test

Run the terminal pipeline on a local audio file:

```bash
python scripts/smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --model tiny --device cpu --compute-type int8 --beam-size 1
```

For a no-key pipeline check, use `--translation echo`. For real translation,
use `--translation deepseek` and provide `DEEPSEEK_API_KEY` in the environment.
The script prints segment id, source text, translated text, and latency.

It can also capture live system audio:

```bash
python scripts/smoke_pipeline_terminal.py --loopback-seconds 10 --source-lang auto --target zh-TW
```

Run the low-latency Local Agreement streaming strategy. Without an explicit
audio source, the script captures a short loopback window:

```bash
python scripts/smoke_pipeline_terminal.py --streaming-strategy local_agreement --target zh-TW
```

`config.example.toml` enables this streaming strategy by default. Use
`--streaming-strategy fixed_segments` only when comparing against the older VAD
segment behavior.

For a repeatable no-key check on local audio:

```bash
python scripts/smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 8 --no-glossary --no-subtitle-log
```

Higher-quality local-model check:

```bash
python scripts/smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --streaming-strategy local_agreement --source-lang ja --target zh-TW --translation echo --model models\faster-whisper-large-v3 --device cuda --compute-type float16 --beam-size 1 --max-segments 1 --max-audio-seconds 8 --no-glossary --no-subtitle-log
```

Streaming mode prints `[PARTIAL]` and `[FINAL]` blocks. Final subtitles are
translated from the full finalized sentence instead of only the latest delta.

For longer local-file stability testing, limit the decoded audio duration and
remove the segment cap:

```bash
python scripts/smoke_pipeline_terminal.py --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --max-audio-seconds 180 --max-segments 0 --source-lang ja --target zh-TW
```

## Stage 5 Overlay Smoke Test

Show the draggable always-on-top subtitle overlay:

```bash
python -m yt_live_translator.main --overlay-test
```

Show the Liquid Glass-inspired soft glass overlay. This is a custom PySide6
style, not an official Apple material:

```bash
python -m yt_live_translator.main --overlay-test --style glass
```

Return to the classic subtitle panel:

```bash
python -m yt_live_translator.main --overlay-test --style classic
```

For automated smoke checks, close it after a few seconds:

```bash
python -m yt_live_translator.main --overlay-test --overlay-test-seconds 3
python -m yt_live_translator.main --overlay-test --style glass --overlay-test-seconds 3
```

## Stage 6 Overlay Pipeline Smoke Test

Run the overlay pipeline on a local audio file without an API key:

```bash
python -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation echo --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 15 --close-on-finish
```

Run the same overlay pipeline with DeepSeek translation by providing
`DEEPSEEK_API_KEY` as a process environment variable:

```bash
python -m yt_live_translator.main --overlay-pipeline-test --audio-file "C:\Users\Owen\Desktop\test_miko_audio.mp3" --source-lang ja --target zh-TW --translation deepseek --deepseek-timeout 60 --model tiny --device cpu --compute-type int8 --beam-size 1 --max-segments 1 --max-audio-seconds 20 --close-on-finish --overlay-result-log work\stage6_overlay_pipeline_deepseek_latest.txt
```

The Stage 6 app keeps the PySide6 overlay responsive while ASR and translation
run in a worker thread. Start/Stop controls are available in a small control
window.

For continuous live YouTube audio, use short loopback chunks:

```bash
python -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --loopback-chunk-seconds 6 --source-lang auto --target zh-TW --translation deepseek --model tiny --device cuda --compute-type float16 --beam-size 1 --max-segments 1
```

Continuous mode captures one short system-audio chunk, processes it, updates the
overlay, and immediately captures the next chunk until Stop is pressed.

Use the streaming strategy in the overlay pipeline to show lighter partial
subtitles and replace them with final subtitles:

```bash
python -m yt_live_translator.main --overlay-pipeline-test --continuous-loopback --streaming-strategy local_agreement --loopback-chunk-seconds 4 --source-lang auto --target zh-TW --translation deepseek --model tiny --device cuda --compute-type float16 --beam-size 1
```

## Stage 7 Manual Glossary

Add a manual glossary term:

```bash
python scripts/glossary_cli.py add --source Miko --target-zh-tw MikoTW --target-zh-cn MikoCN --source-lang ja --term-type person
```

List active terms:

```bash
python scripts/glossary_cli.py list
```

Check which terms match a subtitle:

```bash
python scripts/glossary_cli.py match --text "Miko starts the stream" --source-lang ja --target zh-TW
```

Glossary terms are stored in the SQLite database configured by
`storage.database_path`. Translation smoke tests, the terminal pipeline, and the
overlay pipeline use active matching terms by default. Use `--no-glossary` to
disable glossary matching for a smoke run, or `--glossary-db` to point at a
different SQLite database.

## Stage 8 Settings UI

Open the settings window:

```bash
python -m yt_live_translator.main --settings-test
```

For an automated smoke check:

```bash
python -m yt_live_translator.main --settings-test --settings-test-seconds 3 --settings-db work\stage8_settings_smoke.sqlite3
```

The settings UI persists user-editable language, subtitle style, ASR, and
DeepSeek model settings to the SQLite `app_settings` table.

## Stage 9 Subtitle Log

Append and export subtitle history:

```bash
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl append --segment-id 1 --source "Miko starts" --translation "Miko translated" --source-lang ja --target zh-TW --latency-ms 42 --start 0 --end 2.5
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-txt --output work\stage9_subtitle_log_smoke.txt
python scripts/subtitle_log_cli.py --log work\stage9_subtitle_log_smoke.jsonl export-srt --output work\stage9_subtitle_log_smoke.srt
```

The terminal and overlay pipelines write subtitle history by default using
`storage.subtitle_log_path`. Use `--no-subtitle-log` to disable writing or
`--subtitle-log` to override the JSONL path.

## Stage 10 AI Glossary Candidates

Extract glossary candidates from subtitle history:

```bash
python scripts/glossary_candidates_cli.py --log work\stage10_subtitle_log_smoke.jsonl --db work\stage10_candidates_smoke.sqlite3 extract --min-occurrences 2
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 list
```

Classify pending candidates with DeepSeek:

```bash
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 classify-ai --limit 20 --deepseek-timeout 60
```

Accept or ignore candidates:

```bash
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 accept --id 1 --target-zh-tw MikoTW --target-zh-cn MikoCN
python scripts/glossary_candidates_cli.py --db work\stage10_candidates_smoke.sqlite3 ignore --id 2
```

Accepted candidates are written into the manual glossary. Ignored candidates
keep their ignored status when extraction is run again.
