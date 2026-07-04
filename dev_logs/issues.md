# Known Issues

This file records unresolved bugs, risks, and technical problems.

## Open Issues

- Stage 6 to Stage 9 smoke tests mostly use CPU `tiny` ASR for fast validation.
  This validates threading, UI integration, glossary, settings, and logging,
  but Japanese subtitle quality should still be rechecked with the configured
  larger model and longer GPU runs.
- CUDA ASR works after adding `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin`
  to the process `PATH`, but the app does not yet manage CUDA runtime PATH
  setup automatically.
- Stage 10 candidate extraction uses lightweight heuristics before optional AI
  classification. It is suitable for surfacing repeated names and terms, but
  candidate quality should be tuned with longer real livestream subtitle logs.
- Continuous overlay capture currently processes short captured chunks in a
  loop. This is suitable for live manual testing, but a lower-latency
  sample-level streaming capture/segment queue is still a future improvement.
- PowerShell output can display UTF-8 Japanese/Chinese subtitle log text as
  mojibake even when the underlying log file is written as UTF-8.
- The native Acrylic/Mica section is currently an off-by-default experimental
  placeholder. The custom PySide6 Basic Glass style remains the supported
  overlay path until native effects are implemented and manually verified.
- CUDA model loading is extremely slow even for the tiny model (~43 seconds)
  on this machine. This may be a driver/runtime issue and needs investigation.
- HuggingFace Hub downloads may still be blocked by the VPN (Radmin VPN) /
  network environment, but `models\faster-whisper-large-v3` is now available
  locally and should be used for higher-quality Japanese ASR.
- The tiny ASR model produces poor recognition quality for Japanese game
  stream audio. Keep it only for fast smoke tests; local large-v3 still needs
  longer live-stream quality and latency validation.
- PowerShell `Get-Content` with `-Encoding UTF8` may still display mojibake
  for mixed CJK text due to console codepage limitations.
- QML Phase 2 glass uses gradient-based fallback layers for edge/RGB/reflection
  effects. It does not sample the actual YouTube/desktop background or perform
  shader-based refraction yet; those remain future work after user confirms the
  tuned visual parameters.
- A local Git repository now exists, but the current PowerShell session still
  does not expose `git.exe` on PATH. Use `C:\Program Files\Git\cmd\git.exe` or
  refresh the shell PATH until `git` works directly.
- On `C:\Users\Owen\Desktop\test_miko_audio.mp3`, `models\anime-whisper-ct2-fp16`
  ran successfully on CUDA without CPU fallback and was faster than local
  large-v3, but produced repeated/hallucinated text in several sections. Keep
  large-v3 as the default until anime-whisper is tested on cleaner and longer
  VTuber/anime-style audio.
- The anime-whisper DeepSeek translation smoke was not run because
  `DEEPSEEK_API_KEY` was not present in the process environment.

## Resolved Issues

- Electron multi-window control card and popover could be clipped when the
  subtitle anchor was near the bottom of the screen. Fixed by adding
  bottom-aware menu placement, dynamic popover height, remembered row offsets
  during subtitle dragging, and scroll protection for oversized control windows.
- `npm install` failed for `frontend/electron-overlay` because
  `electron-vite@2.3.0` only supports Vite 4/5 while the package requested
  Vite 6. Fixed by pinning Vite to `^5.4.0`, regenerating
  `package-lock.json`, adding the renderer input required by electron-vite,
  and verifying `npm install`, `npm run typecheck`, `npm run build`,
  `npm run dev:mock`, and `npm run dev:tuning`.
- Overlay pipeline subtitles were produced by the backend but could fail to
  appear in the GUI, and clicking the window could make the process report
  "not responding". Root cause: worker signals were connected to plain Python
  callbacks, allowing Qt widget updates and app-exit scheduling to run from
  the worker thread. Fixed by routing worker signals through a main-thread
  `QObject` bridge, disabling overlay animation for pipeline updates, forcing
  repaint after subtitle updates, and exiting only after worker cleanup.
- Controls-window subtitles could be visible while the floating overlay was
  not visible. Root cause: the overlay relied on default positioning and
  `Qt.Tool` window behavior, which can be hidden or de-prioritized in some
  Windows/Chrome focus states. Fixed by using a frameless top-level window,
  bottom-center positioning, and explicit show/raise/repaint on each update.
- The overlay could be visible and draggable while still not showing subtitle
  text. Root cause: transparent top-level windows with child QLabel rendering
  and graphics effects can fail to paint child text reliably on this Windows
  path. Fixed by directly painting the latest subtitle text in the overlay
  window's `paintEvent` with `QPainter`, while retaining QLabel updates as a
  secondary path.
