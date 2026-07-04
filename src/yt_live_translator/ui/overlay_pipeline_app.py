"""Stage 6 overlay pipeline application."""

from __future__ import annotations

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
) -> None:
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
