# Technical Design

## Selected Tech Stack

- Language: Python 3.11
- UI: PySide6 backend tools, Qt Quick / QML, and Electron frontend prototypes
- Overlay frontend options: PySide6 Widgets fallback, Qt Quick / QML, and
  Electron / React
- Audio capture: PyAudioWPatch with WASAPI loopback
- VAD: Silero VAD
- ASR: faster-whisper with CTranslate2 and CUDA
- Translation: DeepSeek API
- Storage: SQLite
- Config: TOML
- Packaging later: PyInstaller or Nuitka

## Why This Design

ASR runs locally to reduce long-session cost and keep latency stable.
Translation uses DeepSeek API because the text token amount is small, while
translation quality is better than small local models.

## Pipeline

```text
Windows audio output
  -> WASAPI loopback capture
  -> Audio frame queue / rolling audio buffer
  -> VAD segmenter or Local Agreement streaming strategy
  -> faster-whisper ASR
  -> confirmed prefix / partial tail
  -> DeepSeek partial or final translation
  -> glossary correction
  -> subtitle display queue
  -> PySide6 overlay
```

## Overlay Frontends

The original Widgets overlay remains the fallback frontend. A newer QML
frontend is available for Liquid Glass-inspired UI work and is launched with
`--qml-overlay-test` during Phase 1.

```text
Python / PySide6 backend
  -> OverlayBridge QObject
  -> Qt Quick / QML overlay frontend
```

QML must not call ASR, translation, glossary, or subtitle pipeline APIs
directly. It receives state and sends user intents through `OverlayBridge`.
Pipeline integration is deferred to the QML pipeline phase.

An Electron frontend prototype is available under `frontend/electron-overlay`
for Phase 2 Liquid Glass material, animation, and tuning work. It is launched
through `--electron-overlay-test` or `--electron-overlay-tuning`.

```text
Python CLI
  -> npm script
  -> Electron main/preload
  -> React renderer
  -> mock events or WebSocket bridge
```

Electron Phase 2 does not call ASR, DeepSeek, glossary, or audio capture. The
reserved bridge endpoint is `ws://127.0.0.1:8765`, with message contracts
defined in the frontend TypeScript bridge.

Electron live mode starts a Python localhost WebSocket bridge at
`ws://127.0.0.1:8765`. The Python process owns audio capture, ASR, DeepSeek,
glossary, subtitle logging, and API keys. Electron main connects as a
WebSocket client, updates `OverlayWindowManager`, and broadcasts state to each
BrowserWindow renderer through preload IPC.

## Low-Latency Streaming Strategy

The fixed VAD segment path remains available as `fixed_segments`, but
`config.example.toml` enables `local_agreement` as the default live strategy.
This strategy keeps a rolling audio buffer, runs ASR at short ticks, and
compares the most recent ASR hypotheses. Text is committed only when the same
prefix appears across the last N hypotheses or when the configured wait
thresholds are reached.

Streaming output has two event types:

- `partial`: lower-confidence text shown with a lighter overlay style. Partial
  translation is rate-limited so every ASR tick does not call the translation
  API.
- `final`: a complete subtitle rewrite using the full finalized source sentence
  rather than only the latest delta.

Final events are triggered by sentence-ending punctuation, VAD/silence
boundaries, max sentence duration, or an overly long unconfirmed tail. The UI
replaces the latest partial with final text to avoid visible flicker.

## Concurrency Model

- UI thread: PySide6 main thread
- Audio capture worker: background thread
- VAD/segmenter worker: background thread
- ASR worker: single GPU worker
- Translation worker: asyncio or thread pool
- Subtitle display: event signal to UI
- AI glossary extraction: later-stage background task

## Default Runtime Modes

### Low Latency Mode

- ASR model: local `models/faster-whisper-large-v3`
- beam_size: 1 or 2
- strategy: local_agreement
- ASR tick: 0.8 to 1.0 seconds
- confirmed commit window: 1.2 to 3.5 seconds depending on language
- target delay: 2 to 4 seconds

### Balanced Mode

- ASR model: local `models/faster-whisper-large-v3`
- beam_size: 3
- segment length: 2.5 to 4 seconds
- target delay: 3 to 6 seconds

### High Quality Mode

- ASR model: large-v3 or large-v3-turbo
- beam_size: 5
- segment length: 3 to 5 seconds
- target delay: 5 to 9 seconds

## Default Mode

Balanced Mode.
