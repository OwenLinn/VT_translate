"""Stage 6 overlay pipeline application."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from pathlib import Path

from yt_live_translator.audio.wasapi_capture import capture_loopback
from yt_live_translator.core.config import RuntimeConfig
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.core.subtitle_pipeline import (
    PipelineConfig,
    PipelineOutput,
    StreamingPipelineConfig,
    StreamingPipelineEvent,
    load_audio_file_as_pcm16,
    run_terminal_pipeline_on_audio,
    run_streaming_pipeline_on_audio,
)
from yt_live_translator.speech.asr_faster_whisper import ASRError, FasterWhisperTranscriber
from yt_live_translator.speech.segmenter import SegmenterConfig
from yt_live_translator.speech.streaming_agreement import LocalAgreementConfig
from yt_live_translator.storage.subtitle_log_repo import (
    SubtitleLogRepository,
    resolve_subtitle_log_path,
)
from yt_live_translator.translate.deepseek_client import DeepSeekClient
from yt_live_translator.translate.glossary_apply import (
    apply_conservative_post_processing,
    open_glossary_repository,
    translate_with_glossary,
)
from yt_live_translator.ui.overlay_window import OverlayError, SubtitleOverlayWindow, style_from_config


@dataclass(frozen=True)
class OverlayPipelineOptions:
    audio_file: str | None = None
    loopback_seconds: float | None = None
    max_audio_seconds: float | None = None
    source_language: SourceLanguage = "auto"
    target_language: TargetLanguage = "zh-TW"
    translation_mode: str = "deepseek"
    deepseek_timeout: float | None = None
    model_size: str = "tiny"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 1
    max_segments: int | None = 2
    vad_threshold: float = 0.005
    min_speech_ms: int = 800
    max_speech_ms: int = 5000
    silence_end_ms: int = 700
    padding_ms: int = 400
    auto_start: bool = True
    close_on_finish: bool = False
    auto_close_seconds: float | None = None
    result_log: str | None = None
    glossary_db: str | None = None
    glossary_enabled: bool = True
    subtitle_log_path: str | None = None
    subtitle_log_enabled: bool = True
    continuous_loopback: bool = False
    loopback_chunk_seconds: float = 6.0
    max_loopback_chunks: int | None = None
    streaming_strategy: str = "fixed_segments"
    asr_mode: str = "chunked"
    capture_frame_ms: int = 250
    asr_window_seconds: float = 6.0
    asr_tick_ms: int = 1000
    streaming_output_cleanup: bool = True


def run_overlay_pipeline_app(runtime_config: RuntimeConfig, options: OverlayPipelineOptions) -> int:
    try:
        from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
        from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
    except ImportError as exc:
        raise OverlayError("PySide6 is required for the overlay pipeline app. Install it with: pip install PySide6") from exc

    class ControlsWindow(QWidget):
        close_requested = Signal()

        def closeEvent(self, event) -> None:
            self.close_requested.emit()
            event.accept()

    class PipelineWorker(QObject):
        subtitle_ready = Signal(str, str, float, str)
        status_changed = Signal(str)
        failed = Signal(str)
        finished = Signal()

        def __init__(self) -> None:
            super().__init__()
            self._stop_requested = False

        def request_stop(self) -> None:
            self._stop_requested = True

        def should_stop(self) -> bool:
            return self._stop_requested

        def run(self) -> None:
            try:
                _append_result_log(options, "Overlay pipeline started")
                pipeline_config = _build_pipeline_config(runtime_config, options)
                streaming_config = _build_streaming_pipeline_config(runtime_config, options)
                translate = _build_translator(runtime_config, options)
                subtitle_log = (
                    SubtitleLogRepository(resolve_subtitle_log_path(runtime_config, options.subtitle_log_path))
                    if options.subtitle_log_enabled
                    else None
                )

                transcriber = FasterWhisperTranscriber(
                    language=options.source_language,
                    model_size=options.model_size,
                    device=options.device,
                    compute_type=options.compute_type,
                    beam_size=options.beam_size,
                )
                self.status_changed.emit("Loading ASR model")
                transcriber.ensure_model_loaded()
                _append_result_log(
                    options,
                    "ASR model loaded "
                    f"device={transcriber.effective_device} "
                    f"compute_type={transcriber.effective_compute_type} "
                    f"cpu_fallback={transcriber.used_cpu_fallback}",
                )
                if transcriber.used_cpu_fallback:
                    self.status_changed.emit("Falling back to CPU int8 for ASR")

                def asr(segment_path: Path):
                    return transcriber.transcribe(segment_path)

                def on_output(output: PipelineOutput, chunk_index: int | None = None) -> None:
                    if subtitle_log is not None:
                        subtitle_log.append_translation(
                            output.translation,
                            start_time=output.asr.start_time,
                            end_time=output.asr.end_time,
                        )
                    _append_result_log(
                        options,
                        "\n".join(
                            [
                                f"[Segment {output.asr.segment_id}]",
                                f"Chunk: {chunk_index}" if chunk_index is not None else "Chunk: single",
                                f"Source: {output.asr.source_text}",
                                f"Translation: {output.translation.translated_text}",
                                f"Latency: {output.translation.total_latency_ms:.0f} ms",
                            ]
                        ),
                    )
                    self.subtitle_ready.emit(
                        output.asr.source_text,
                        output.translation.translated_text,
                        output.translation.total_latency_ms,
                        "final",
                    )
                    self.status_changed.emit(
                        f"Segment {output.asr.segment_id} latency {output.translation.total_latency_ms:.0f} ms"
                    )

                if options.continuous_loopback:
                    _run_continuous_loopback_pipeline(
                        runtime_config=runtime_config,
                        options=options,
                        pipeline_config=pipeline_config,
                        streaming_config=streaming_config,
                        asr=asr,
                        translate=translate,
                        on_output=on_output,
                        on_streaming_event=self._on_streaming_event,
                        should_stop=self.should_stop,
                        update_status=self.status_changed.emit,
                        subtitle_log=subtitle_log,
                        transcriber=transcriber,
                    )
                else:
                    self.status_changed.emit("Loading audio")
                    audio = _load_audio(runtime_config, options)
                    self.status_changed.emit("Running pipeline")
                    if options.streaming_strategy == "local_agreement":
                        run_streaming_pipeline_on_audio(
                            audio=audio,
                            config=streaming_config,
                            asr=asr,
                            translate=translate,
                            on_event=lambda event: self._on_streaming_event(event, None, subtitle_log),
                            should_stop=self.should_stop,
                        )
                    else:
                        run_terminal_pipeline_on_audio(
                            audio=audio,
                            config=pipeline_config,
                            asr=asr,
                            translate=translate,
                            on_output=lambda output: on_output(output, None),
                            should_stop=self.should_stop,
                        )
                self.status_changed.emit("Stopped" if self._stop_requested else "Finished")
                _append_result_log(
                    options,
                    "Overlay pipeline stopped"
                    if self._stop_requested
                    else "Overlay pipeline finished",
                )
            except Exception as exc:
                _append_result_log(options, f"Overlay pipeline failed: {exc}")
                self.failed.emit(str(exc))
            finally:
                self.finished.emit()

        def _on_streaming_event(
            self,
            event: StreamingPipelineEvent,
            chunk_index: int | None = None,
            subtitle_log: SubtitleLogRepository | None = None,
        ) -> None:
            if event.kind == "final" and subtitle_log is not None:
                subtitle_log.append_translation(
                    event.translation,
                    start_time=event.asr.start_time,
                    end_time=event.asr.end_time,
                )
            _append_result_log(
                options,
                "\n".join(
                    [
                        f"[{event.kind.upper()}]",
                        f"Chunk: {chunk_index}" if chunk_index is not None else "Chunk: single",
                        f"Source: {event.asr.source_text}",
                        f"Translation: {event.translation.translated_text}",
                        f"Latency: {event.translation.total_latency_ms:.0f} ms",
                    ]
                ),
            )
            self.subtitle_ready.emit(
                event.asr.source_text,
                event.translation.translated_text,
                event.translation.total_latency_ms,
                event.kind,
            )
            self.status_changed.emit(
                f"{event.kind.title()} latency {event.translation.total_latency_ms:.0f} ms"
            )

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    overlay = SubtitleOverlayWindow(style_from_config(runtime_config.overlay))
    overlay.update_subtitle("Ready.", "Ready.", animate=False)
    overlay.show()

    controls = ControlsWindow()
    controls.setWindowTitle("YouTube Live Translator Controls")
    controls.setMinimumWidth(360)
    if runtime_config.overlay.always_on_top:
        controls.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    status_label = QLabel("Ready")
    latest_translation_label = QLabel("Latest translation will appear here.")
    latest_translation_label.setWordWrap(True)
    latest_translation_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    latest_source_label = QLabel("")
    latest_source_label.setWordWrap(True)
    latest_source_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    start_button = QPushButton("Start")
    stop_button = QPushButton("Stop")
    stop_button.setEnabled(False)
    layout = QVBoxLayout(controls)
    layout.addWidget(status_label)
    layout.addWidget(latest_translation_label)
    layout.addWidget(latest_source_label)
    layout.addWidget(start_button)
    layout.addWidget(stop_button)
    controls.show()

    thread_state = {"thread": None, "worker": None}
    app_exit_code = {"value": 0}
    shutdown_state = {"requested": False, "exit_after_thread": False, "exit_delay_ms": 0}
    subtitle_state = {"has_subtitle": False}

    def schedule_app_exit(delay_ms: int = 0) -> None:
        QTimer.singleShot(delay_ms, lambda: app.exit(app_exit_code["value"]))

    class PipelineUiBridge(QObject):
        @Slot(str, str, float, str)
        def show_subtitle(self, source: str, translation: str, _latency: float, kind: str) -> None:
            subtitle_state["has_subtitle"] = True
            overlay.update_subtitle(
                source,
                translation,
                animate=False,
                partial=kind == "partial",
            )
            latest_translation_label.setText(translation)
            latest_source_label.setText(source)
            overlay.ensure_visible(activate=True)
            controls.raise_()

        @Slot(str)
        def show_status(self, message: str) -> None:
            status_label.setText(message)
            if not subtitle_state["has_subtitle"]:
                overlay.update_subtitle(
                    source_text=message,
                    translated_text="Waiting for subtitle...",
                    animate=False,
                    partial=True,
                )
                overlay.ensure_visible(activate=False)

        @Slot(str)
        def show_error(self, message: str) -> None:
            app_exit_code["value"] = 1
            status_label.setText(f"Error: {message}")

        @Slot()
        def worker_finished(self) -> None:
            stop_button.setEnabled(False)
            if options.close_on_finish:
                shutdown_state["exit_after_thread"] = True
                shutdown_state["exit_delay_ms"] = max(
                    shutdown_state["exit_delay_ms"],
                    1200,
                )

        @Slot()
        def thread_finished(self) -> None:
            thread_state["thread"] = None
            thread_state["worker"] = None
            start_button.setEnabled(True)
            stop_button.setEnabled(False)
            if shutdown_state["requested"] or shutdown_state["exit_after_thread"]:
                schedule_app_exit(shutdown_state["exit_delay_ms"])

    ui_bridge = PipelineUiBridge()

    def start_pipeline() -> None:
        if thread_state["thread"] is not None:
            return
        shutdown_state["requested"] = False
        shutdown_state["exit_after_thread"] = False
        shutdown_state["exit_delay_ms"] = 0
        thread = QThread()
        worker = PipelineWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.subtitle_ready.connect(ui_bridge.show_subtitle, Qt.ConnectionType.QueuedConnection)
        worker.status_changed.connect(ui_bridge.show_status, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(ui_bridge.show_error, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(ui_bridge.worker_finished, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(ui_bridge.thread_finished, Qt.ConnectionType.QueuedConnection)
        thread_state["thread"] = thread
        thread_state["worker"] = worker
        start_button.setEnabled(False)
        stop_button.setEnabled(True)
        latest_translation_label.setText("Latest translation will appear here.")
        latest_source_label.setText("")
        subtitle_state["has_subtitle"] = False
        status_label.setText("Starting")
        thread.start()

    def stop_pipeline() -> None:
        worker = thread_state["worker"]
        if worker is not None:
            worker.request_stop()
            status_label.setText("Stopping")

    def request_app_shutdown(delay_ms: int = 0) -> None:
        shutdown_state["requested"] = True
        shutdown_state["exit_after_thread"] = True
        shutdown_state["exit_delay_ms"] = max(shutdown_state["exit_delay_ms"], delay_ms)
        worker = thread_state["worker"]
        thread = thread_state["thread"]
        if worker is not None:
            worker.request_stop()
            status_label.setText("Stopping")
        if thread is None or not thread.isRunning():
            schedule_app_exit(delay_ms)

    def stop_thread_on_exit() -> None:
        worker = thread_state["worker"]
        thread = thread_state["thread"]
        if worker is not None:
            worker.request_stop()
        if thread is not None and thread.isRunning():
            thread.quit()

    start_button.clicked.connect(start_pipeline)
    stop_button.clicked.connect(stop_pipeline)
    controls.close_requested.connect(lambda: request_app_shutdown(0))
    app.aboutToQuit.connect(stop_thread_on_exit)
    if options.auto_start:
        QTimer.singleShot(0, start_pipeline)
    if options.auto_close_seconds is not None:
        QTimer.singleShot(
            round(options.auto_close_seconds * 1000),
            lambda: request_app_shutdown(0),
        )
    app.exec()
    return app_exit_code["value"]


def _build_pipeline_config(runtime_config: RuntimeConfig, options: OverlayPipelineOptions) -> PipelineConfig:
    return PipelineConfig(
        source_language=options.source_language,
        target_language=options.target_language,
        vad_threshold=options.vad_threshold,
        segmenter=SegmenterConfig(
            frame_ms=runtime_config.audio.chunk_ms,
            min_speech_ms=options.min_speech_ms,
            max_speech_ms=options.max_speech_ms,
            silence_end_ms=options.silence_end_ms,
            padding_ms=options.padding_ms,
        ),
        max_segments=options.max_segments,
    )


def _build_streaming_pipeline_config(
    runtime_config: RuntimeConfig,
    options: OverlayPipelineOptions,
) -> StreamingPipelineConfig:
    language_config = runtime_config.streaming.ja if options.source_language == "ja" else runtime_config.streaming.en
    return StreamingPipelineConfig(
        source_language=options.source_language,
        target_language=options.target_language,
        asr_tick_ms=language_config.asr_tick_ms or runtime_config.streaming.asr_tick_ms,
        rolling_window_sec=runtime_config.streaming.rolling_window_sec,
        overlap_sec=runtime_config.streaming.overlap_sec,
        agreement=LocalAgreementConfig(
            source_language=options.source_language,
            agreement_n=runtime_config.streaming.local_agreement_n,
            min_commit_sec=runtime_config.streaming.min_commit_sec,
            max_commit_sec=language_config.max_commit_sec,
            max_unconfirmed_sec=runtime_config.streaming.max_unconfirmed_sec,
            min_commit_tokens=language_config.min_commit_tokens,
            enable_partial_subtitle=runtime_config.streaming.enable_partial_subtitle,
        ),
        enable_final_revision=runtime_config.streaming.enable_final_revision,
        max_final_segments=options.max_segments,
        silence_end_ms=language_config.silence_end_ms,
        silence_threshold=options.vad_threshold,
    )


def _run_continuous_loopback_pipeline(
    *,
    runtime_config: RuntimeConfig,
    options: OverlayPipelineOptions,
    pipeline_config: PipelineConfig,
    streaming_config: StreamingPipelineConfig,
    asr,
    translate,
    on_output,
    on_streaming_event,
    should_stop,
    update_status,
    subtitle_log,
    transcriber=None,
) -> None:
    if options.asr_mode == "streaming":
        if transcriber is None:
            raise ValueError("transcriber is required for streaming ASR mode")
        _run_continuous_streaming_asr_pipeline(
            runtime_config=runtime_config,
            options=options,
            transcriber=transcriber,
            translate=translate,
            on_streaming_event=on_streaming_event,
            should_stop=should_stop,
            update_status=update_status,
            subtitle_log=subtitle_log,
        )
        return

    if options.loopback_chunk_seconds <= 0:
        raise ValueError("loopback_chunk_seconds must be greater than 0")
    chunk_index = 0
    while not should_stop():
        if options.max_loopback_chunks is not None and chunk_index >= options.max_loopback_chunks:
            break
        chunk_index += 1
        update_status(f"Capturing live audio chunk {chunk_index}")
        _append_result_log(options, f"[Status] Capturing live audio chunk {chunk_index}")
        audio = capture_loopback(
            seconds=options.loopback_chunk_seconds,
            target_sample_rate=runtime_config.audio.sample_rate,
            target_channels=runtime_config.audio.channels,
            chunk_ms=runtime_config.audio.chunk_ms,
        )
        _append_result_log(
            options,
            "\n".join(
                [
                    f"[Capture {chunk_index}]",
                    f"Device: {audio.device.name}",
                    f"CapturedFrames: {audio.captured_frames}",
                    f"SilenceFallbackFrames: {audio.silence_fallback_frames}",
                    f"Elapsed: {audio.elapsed_seconds:.2f} s",
                ]
            ),
        )
        if should_stop():
            break
        if audio.captured_frames <= 0:
            message = f"Skipping silent live audio chunk {chunk_index}"
            update_status(message)
            _append_result_log(options, f"[Status] {message}")
            continue
        update_status(f"Processing live audio chunk {chunk_index}")
        _append_result_log(options, f"[Status] Processing live audio chunk {chunk_index}")
        if options.streaming_strategy == "local_agreement":
            run_streaming_pipeline_on_audio(
                audio=audio.audio,
                config=streaming_config,
                asr=asr,
                translate=translate,
                on_event=lambda event, index=chunk_index: on_streaming_event(event, index, subtitle_log),
                should_stop=should_stop,
            )
        else:
            run_terminal_pipeline_on_audio(
                audio=audio.audio,
                config=pipeline_config,
                asr=asr,
                translate=translate,
                on_output=lambda output, index=chunk_index: on_output(output, index),
                should_stop=should_stop,
            )


def _run_continuous_streaming_asr_pipeline(
    *,
    runtime_config,
    options,
    transcriber,
    translate,
    on_streaming_event,
    should_stop,
    update_status,
    subtitle_log,
) -> None:
    from yt_live_translator.audio.loopback_stream import stream_loopback_frames
    from yt_live_translator.core.streaming_asr_session import StreamingAsrSession
    from yt_live_translator.speech.streaming_agreement import LocalAgreementConfig

    frame_ms = options.capture_frame_ms
    asr_window_sec = options.asr_window_seconds
    asr_tick_ms_val = options.asr_tick_ms

    agreement_config = LocalAgreementConfig(
        source_language=options.source_language,
        agreement_n=2,
        min_commit_sec=1.2,
        max_commit_sec=3.0,
        max_unconfirmed_sec=4.0,
        min_commit_tokens=8 if options.source_language == "ja" else 5,
        enable_partial_subtitle=True,
        enable_final_revision=False,
    )

    session = StreamingAsrSession(
        transcriber=transcriber,
        source_language=options.source_language,
        sample_rate=runtime_config.audio.sample_rate,
        channels=runtime_config.audio.channels,
        asr_window_seconds=asr_window_sec,
        asr_tick_ms=asr_tick_ms_val,
        capture_frame_ms=frame_ms,
        agreement_config=agreement_config,
        beam_size=options.beam_size,
        enable_output_cleanup=options.streaming_output_cleanup,
    )

    update_status("Starting true streaming ASR pipeline")
    _append_result_log(options, "[Status] True streaming ASR pipeline started")

    from yt_live_translator.core.subtitle_pipeline import StreamingPipelineEvent
    from yt_live_translator.core.streaming_translation_worker import (
        StreamingTranslationResult,
        StreamingTranslationWorker,
    )

    is_echo = options.translation_mode == "echo"

    STALE_CLEAR_SECONDS = 8.0
    last_emitted_monotonic = time.monotonic()
    subtitle_is_cleared = False

    pending_text: str | None = None
    pending_start: float | None = None
    pending_merge_count: int = 0
    fragment_stats = {"pending": 0, "merged": 0, "dropped": 0, "overlap_trim": 0, "too_long": 0}

    def _emit_clear_subtitle() -> None:
        nonlocal subtitle_is_cleared
        if subtitle_is_cleared:
            return
        subtitle_is_cleared = True
        _append_result_log(
            options,
            f"[streaming-idle] stale subtitle clear after {STALE_CLEAR_SECONDS}s",
        )
        clear_event = StreamingPipelineEvent(
            kind="clear",
            asr=_make_asr_result_raw(
                segment_id=0,
                source_text="",
                source_language=options.source_language,
                start_time=0.0,
                end_time=0.0,
                asr_latency_ms=0.0,
            ),
            translation=_make_translation_result_raw(
                segment_id=0,
                source_text="",
                translated_text="",
                options=options,
            ),
        )
        on_streaming_event(clear_event, None, subtitle_log)

    def _on_worker_result_emit(result: StreamingTranslationResult) -> None:
        nonlocal last_emitted_monotonic, subtitle_is_cleared
        pipe_event = StreamingPipelineEvent(
            kind=result.kind,
            asr=_make_asr_result_raw(
                segment_id=result.segment_id,
                source_text=result.source_text,
                source_language=result.source_language,
                start_time=result.start_time,
                end_time=result.end_time,
                asr_latency_ms=result.asr_latency_ms,
            ),
            translation=_make_translation_result_raw(
                segment_id=result.segment_id,
                source_text=result.source_text,
                translated_text=result.translated_text,
                options=options,
                translation_latency_ms=result.translation_latency_ms,
            ),
        )
        on_streaming_event(pipe_event, None, subtitle_log)
        last_emitted_monotonic = time.monotonic()
        subtitle_is_cleared = False

    def _maybe_emit(evt, merged_text: str | None = None) -> None:
        if is_echo:
            _emit_translated(evt, merged_text)
            return
        source = merged_text if merged_text is not None else evt.source_text
        if evt.kind == "final":
            translation_worker.submit_final(
                segment_id=evt.segment_id,
                source_text=source,
                asr_latency_ms=evt.asr_latency_ms,
                start_time=evt.start_time,
                end_time=evt.end_time,
            )
        else:
            translation_worker.submit_partial(
                segment_id=evt.segment_id,
                source_text=source,
                asr_latency_ms=evt.asr_latency_ms,
                start_time=evt.start_time,
                end_time=evt.end_time,
            )

    translation_worker: StreamingTranslationWorker | None = None

    if is_echo:

        def _emit_translated(evt, merged_text: str | None = None) -> None:
            source = merged_text if merged_text is not None else evt.source_text
            translated = translate(source, options.source_language, options.target_language)
            pipe_event = StreamingPipelineEvent(
                kind=evt.kind,
                asr=_make_asr_result(evt, options.source_language),
                translation=_make_translation_result_raw(
                    segment_id=evt.segment_id,
                    source_text=source,
                    translated_text=translated,
                    options=options,
                ),
            )
            on_streaming_event(pipe_event, None, subtitle_log)
    else:
        translation_worker = StreamingTranslationWorker(
            translate=translate,
            on_result=_on_worker_result_emit,
            source_language=options.source_language,
            target_language=options.target_language,
            session_started_monotonic=time.monotonic(),
            mode="fresh",
            max_final_queue=1,
            max_display_lag_ms=8000,
            max_task_age_ms=4500,
            update_status=update_status,
            append_log=lambda msg: _append_result_log(options, msg),
        )
        translation_worker.start()

    def _merge_pending(current: str) -> str | None:
        nonlocal pending_text, pending_start, pending_merge_count
        if not pending_text:
            return current

        max_merged_len = 60

        if len(pending_text) > 30:
            _append_result_log(
                options,
                f"[streaming-fragment] drop pending too long before merge: "
                f"pending_len={len(pending_text)} max_pending=30",
            )
            fragment_stats["dropped"] += 1
            fragment_stats["too_long"] += 1
            pending_text = None
            pending_start = None
            pending_merge_count = 0
            if len(current) <= max_merged_len and not _is_probable_ja_fragment(current):
                _append_result_log(
                    options,
                    "[streaming-fragment] drop pending and use current "
                    f"current_len={len(current)}",
                )
                return current
            _append_result_log(
                options,
                "[streaming-fragment] drop pending and skip current "
                f"current_len={len(current)} fragment_like={_is_probable_ja_fragment(current)}",
            )
            fragment_stats["dropped"] += 1
            return None

        overlap = _find_max_overlap_suffix_prefix(pending_text, current, min_overlap=4)
        if overlap > 0:
            current_trimmed = current[overlap:]
            fragment_stats["overlap_trim"] += 1
        else:
            current_trimmed = current
        merged = pending_text.rstrip("\u2026\u3001\u3002 ") + current_trimmed

        if len(merged) > max_merged_len:
            _append_result_log(
                options,
                f"[streaming-fragment] drop merged too long: "
                f"merged_len={len(merged)} max={max_merged_len} "
                f"pending_len={len(pending_text)} current_len={len(current)}",
            )
            fragment_stats["dropped"] += 1
            fragment_stats["too_long"] += 1
            pending_text = None
            pending_start = None
            pending_merge_count = 0
            if len(current) <= max_merged_len and not _is_probable_ja_fragment(current):
                _append_result_log(
                    options,
                    "[streaming-fragment] drop pending and use current "
                    f"current_len={len(current)}",
                )
                return current
            _append_result_log(
                options,
                "[streaming-fragment] drop pending and skip current "
                f"current_len={len(current)} fragment_like={_is_probable_ja_fragment(current)}",
            )
            fragment_stats["dropped"] += 1
            return None

        _append_result_log(
            options,
            f"[streaming-fragment] emit merged: pending=\"{pending_text[:40]}\" "
            f"overlap={overlap} current=\"{current[:40]}\" "
            f"merged_len={len(merged)} merge_cnt={pending_merge_count}",
        )
        pending_text = None
        pending_start = None
        pending_merge_count = 0
        fragment_stats["merged"] += 1
        if _is_probable_ja_fragment(merged):
            norm = _normalize_fragment_text(merged)
            if len(norm) < 5:
                _append_result_log(
                    options,
                    f"[streaming-fragment] drop merged still fragment: \"{merged[:60]}\"",
                )
                fragment_stats["dropped"] += 1
                return None
        return merged

    def _handle_fragment(source: str) -> None:
        nonlocal pending_text, pending_start, pending_merge_count
        if pending_merge_count >= 1:
            _append_result_log(
                options,
                f"[streaming-fragment] drop stale pending due repeated fragment "
                f"old=\"{pending_text[:40]}\"",
            )
            fragment_stats["dropped"] += 1
            pending_text = source
            pending_start = 0.0
            pending_merge_count = 0
            fragment_stats["pending"] += 1
            _append_result_log(
                options,
                f"[streaming-fragment] pending fragment: \"{source[:60]}\" "
                f"len={len(source)}",
            )
            return

        if pending_text is not None and len(pending_text) > 30:
            _append_result_log(
                options,
                f"[streaming-fragment] drop pending too long: "
                f"len={len(pending_text)} \"{pending_text[:60]}\"",
            )
            fragment_stats["dropped"] += 1
            fragment_stats["too_long"] += 1
            pending_text = source
            pending_start = 0.0
            pending_merge_count = 0
            fragment_stats["pending"] += 1
            _append_result_log(
                options,
                f"[streaming-fragment] pending fragment: \"{source[:60]}\" "
                f"len={len(source)}",
            )
            return

        if pending_text:
            merged = pending_text.rstrip("\u2026\u3001\u3002 ") + source
            if len(merged) > 60:
                _append_result_log(
                    options,
                    f"[streaming-fragment] drop merged too long: "
                    f"pending_len={len(pending_text)} current_len={len(source)} "
                    f"merged_len={len(merged)}",
                )
                fragment_stats["dropped"] += 1
                fragment_stats["too_long"] += 1
                pending_text = source
                pending_start = 0.0
                pending_merge_count = 0
                fragment_stats["pending"] += 1
                _append_result_log(
                    options,
                    f"[streaming-fragment] pending fragment: \"{source[:60]}\" "
                    f"len={len(source)}",
                )
                return
            pending_text = merged
            pending_merge_count += 1
            fragment_stats["pending"] += 1
            _append_result_log(
                options,
                f"[streaming-fragment] merge pending fragment: + "
                f"\"{source[:40]}\" cnt={pending_merge_count} "
                f"pending_len={len(pending_text)}",
            )
        else:
            pending_text = source
            pending_start = 0.0
            pending_merge_count = 0
            fragment_stats["pending"] += 1
            _append_result_log(
                options,
                f"[streaming-fragment] pending fragment: \"{source[:60]}\" "
                f"len={len(source)}",
            )

    for frame in stream_loopback_frames(
        frame_ms=frame_ms,
        sample_rate=runtime_config.audio.sample_rate,
        channels=runtime_config.audio.channels,
        should_stop=should_stop,
    ):
        events = session.push_audio(frame)

        for event in events:
            source = event.source_text

            if is_echo:
                _emit_translated(event)
                continue

            if options.source_language == "ja" and _is_probable_ja_fragment(source):
                _handle_fragment(source)
                continue

            merged = _merge_pending(source)
            if merged is not None:
                _maybe_emit(event, merged_text=merged)

        if not is_echo and time.monotonic() - last_emitted_monotonic > STALE_CLEAR_SECONDS:
            _emit_clear_subtitle()

    flush_events = session.flush()
    for event in flush_events:
        if is_echo:
            _emit_translated(event)
            continue

        source = event.source_text

        if pending_text and not _is_probable_ja_fragment(source):
            merged = _merge_pending(source)
            if merged is not None:
                _maybe_emit(event, merged_text=merged)
        elif pending_text:
            norm = _normalize_fragment_text(pending_text)
            if len(norm) >= 6:
                _append_result_log(
                    options,
                    f"[streaming-fragment] flush long pending: \"{pending_text[:60]}\" "
                    f"len={len(pending_text)} norm_len={len(norm)}",
                )
                _maybe_emit(event, merged_text=pending_text)
                fragment_stats["merged"] += 1
            else:
                _append_result_log(
                    options,
                    f"[streaming-fragment] drop tiny pending: \"{pending_text[:60]}\" "
                    f"len={len(pending_text)} norm_len={len(norm)}",
                )
                fragment_stats["dropped"] += 1
                _maybe_emit(event)
        else:
            _maybe_emit(event)
        pending_text = None
        pending_start = None
        pending_merge_count = 0

    if translation_worker is not None:
        translation_worker.stop(drain_final=True)
        _append_result_log(
            options,
            f"[streaming-fragment] stats pending={fragment_stats['pending']} "
            f"merged={fragment_stats['merged']} dropped={fragment_stats['dropped']} "
            f"overlap_trim={fragment_stats['overlap_trim']} "
            f"too_long={fragment_stats['too_long']}",
        )

    _append_result_log(options, "[Status] True streaming ASR pipeline finished")


def _make_asr_result(event, source_language: str) -> "ASRResult":
    from yt_live_translator.core.models import ASRResult

    return ASRResult(
        segment_id=event.segment_id,
        source_text=event.source_text,
        source_language=source_language,
        start_time=event.start_time,
        end_time=event.end_time,
        asr_latency_ms=event.asr_latency_ms,
    )


def _make_asr_result_raw(
    *,
    segment_id: int,
    source_text: str,
    source_language: str,
    start_time: float,
    end_time: float,
    asr_latency_ms: float,
) -> "ASRResult":
    from yt_live_translator.core.models import ASRResult

    return ASRResult(
        segment_id=segment_id,
        source_text=source_text,
        source_language=source_language,
        start_time=start_time,
        end_time=end_time,
        asr_latency_ms=asr_latency_ms,
    )


def _make_translation_result(event, translated_text: str, options) -> "TranslationResult":
    from yt_live_translator.core.models import TranslationResult

    return TranslationResult(
        segment_id=event.segment_id,
        source_text=event.source_text,
        translated_text=translated_text,
        source_language=options.source_language,
        target_language=options.target_language,
        total_latency_ms=event.asr_latency_ms,
    )


def _make_translation_result_raw(
    *,
    segment_id: int,
    source_text: str,
    translated_text: str,
    options,
    translation_latency_ms: float = 0.0,
) -> "TranslationResult":
    from yt_live_translator.core.models import TranslationResult

    return TranslationResult(
        segment_id=segment_id,
        source_text=source_text,
        translated_text=translated_text,
        source_language=options.source_language,
        target_language=options.target_language,
        total_latency_ms=translation_latency_ms,
    )


JA_ALLOW_SHORT = frozenset(("はい", "いや", "え？", "え?", "あはは", "ありがとう", "うん", "うん。", "ええ", "そう", "はい。"))


def _normalize_fragment_text(text: str) -> str:
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        if (
            0x4E00 <= cp <= 0x9FFF
            or 0x3040 <= cp <= 0x309F
            or 0x30A0 <= cp <= 0x30FF
            or 0x0020 <= cp <= 0x007E
        ):
            result.append(ch)
    return "".join(result)


def _is_probable_ja_fragment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True

    if stripped in JA_ALLOW_SHORT:
        return False

    norm = _normalize_fragment_text(stripped)
    if len(norm) < 4:
        return True

    fragment_prefixes = (
        "に、", "を、", "が、", "は、", "も、", "と、", "で、",
        "って", "った", "たこと", "いらなかった", "くらいに", "ってきて",
    )
    for prefix in fragment_prefixes:
        if stripped.startswith(prefix):
            return True

    if len(stripped) < 18:
        short_starts = ("に", "を", "が", "は", "も", "と", "で", "って", "った")
        if stripped.startswith(short_starts) and norm not in JA_ALLOW_SHORT:
            return True

    return False


def _find_max_overlap_suffix_prefix(left: str, right: str, min_overlap: int = 4) -> int:
    max_possible = min(len(left), len(right))
    best = 0
    for n in range(min_overlap, max_possible + 1):
        if left[-n:] == right[:n]:
            best = n
    return best


def _load_audio(runtime_config: RuntimeConfig, options: OverlayPipelineOptions):
    if options.audio_file:
        return load_audio_file_as_pcm16(
            options.audio_file,
            sample_rate=runtime_config.audio.sample_rate,
            channels=runtime_config.audio.channels,
            max_duration_seconds=options.max_audio_seconds,
        )
    if options.loopback_seconds is None:
        raise ValueError("Either audio_file or loopback_seconds is required")
    return capture_loopback(
        seconds=options.loopback_seconds,
        target_sample_rate=runtime_config.audio.sample_rate,
        target_channels=runtime_config.audio.channels,
        chunk_ms=runtime_config.audio.chunk_ms,
    ).audio


def _build_translator(runtime_config: RuntimeConfig, options: OverlayPipelineOptions):
    repository = (
        open_glossary_repository(runtime_config, options.glossary_db)
        if options.glossary_enabled
        else None
    )
    if options.translation_mode == "echo":
        def echo_translate(text: str, source: SourceLanguage, target: TargetLanguage) -> str:
            translated = f"[echo:{target}] {text}"
            matched_terms = (
                repository.find_matching_terms(
                    text=text,
                    source_language=source,
                    target_language=target,
                )
                if repository is not None
                else []
            )
            return apply_conservative_post_processing(
                source_text=text,
                translated_text=translated,
                matched_terms=matched_terms,
                target_language=target,
            )

        return echo_translate
    deepseek_config = runtime_config.deepseek
    if options.deepseek_timeout is not None:
        deepseek_config = replace(deepseek_config, timeout_seconds=options.deepseek_timeout)
    client = DeepSeekClient(
        config=deepseek_config,
        api_key=runtime_config.resolve_deepseek_api_key(),
    )
    return lambda text, source, target: translate_with_glossary(
        client,
        text=text,
        source_language=source,
        target_language=target,
        repository=repository,
    )


def _append_result_log(options: OverlayPipelineOptions, text: str) -> None:
    if not options.result_log:
        return
    path = Path(options.result_log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(text.rstrip() + "\n")
