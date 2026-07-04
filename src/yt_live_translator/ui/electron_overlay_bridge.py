"""Electron overlay live bridge.

This module keeps ASR, translation, glossary, and API keys in Python while the
Electron overlay only receives subtitle/status events over localhost WebSocket.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import struct
import subprocess
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from yt_live_translator.audio.wasapi_capture import capture_loopback
from yt_live_translator.core.config import RuntimeConfig
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.core.subtitle_pipeline import (
    PipelineOutput,
    StreamingPipelineEvent,
    load_audio_file_as_pcm16,
    run_streaming_pipeline_on_audio,
    run_terminal_pipeline_on_audio,
)
from yt_live_translator.speech.asr_faster_whisper import FasterWhisperTranscriber
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
from yt_live_translator.ui.electron_overlay_app import (
    electron_overlay_env,
    electron_overlay_root,
    resolve_npm_command,
)
from yt_live_translator.ui.overlay_pipeline_app import (
    OverlayPipelineOptions,
    _append_result_log,
    _build_pipeline_config,
    _build_streaming_pipeline_config,
    _run_continuous_loopback_pipeline,
)
from yt_live_translator.ui.overlay_window import OverlayError


BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8765
BRIDGE_URL = f"ws://{BRIDGE_HOST}:{BRIDGE_PORT}"
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class ElectronOverlayBridge:
    def __init__(self, runtime_config: RuntimeConfig, options: OverlayPipelineOptions) -> None:
        self.runtime_config = runtime_config
        self.options = options
        self.clients: set[asyncio.StreamWriter] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.server: asyncio.AbstractServer | None = None
        self.pipeline_thread: threading.Thread | None = None
        self.stop_requested = threading.Event()
        self.running_lock = threading.Lock()
        self._pipeline_running = False

    async def run(self) -> None:
        try:
            self.loop = asyncio.get_running_loop()
            self.server = await asyncio.start_server(self._handle_client, BRIDGE_HOST, BRIDGE_PORT)
            print(f"[bridge] WebSocket server listening on {BRIDGE_URL}")
            await self.broadcast_status("idle", True, "Bridge ready")
            if self.options.auto_start:
                self.start_pipeline()
            await self.server.serve_forever()
        except asyncio.CancelledError:
            print("[bridge] server cancelled")
        except Exception as exc:
            print(f"[bridge] server fatal error: {exc}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            print("[bridge] server shutting down", flush=True)
            if self.server:
                self.server.close()
                await self.server.wait_closed()

    def shutdown(self) -> None:
        self.request_stop()
        if self.loop is None or self.server is None:
            return
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.server.close)
        else:
            print("[bridge] event loop already stopped, skipping server close")

    def start_pipeline(self) -> bool:
        with self.running_lock:
            if self.pipeline_thread and self.pipeline_thread.is_alive():
                return False
            self.stop_requested.clear()
            self._pipeline_running = True
            self.pipeline_thread = threading.Thread(
                target=self._run_pipeline,
                name="electron-overlay-pipeline",
                daemon=True,
            )
            self.pipeline_thread.start()
            return True

    def request_stop(self) -> None:
        self.stop_requested.set()
        self._pipeline_running = False
        self.broadcast_status_threadsafe("stopping", True, "Stopping pipeline")

    def _is_pipeline_active(self) -> bool:
        with self.running_lock:
            return self._pipeline_running and self.pipeline_thread is not None and self.pipeline_thread.is_alive()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            await self._handshake(reader, writer)
            self.clients.add(writer)
            print(f"[bridge] client connected (total clients: {len(self.clients)})")
            pipeline_active = self._is_pipeline_active()
            status = "running" if pipeline_active else "idle"
            detail = "Pipeline active" if pipeline_active else "Electron connected"
            await self.broadcast_status(status, True, detail)
            await self._send_json(writer, self._settings_event())
            while not reader.at_eof():
                message = await self._read_text_frame(reader, writer)
                if message is None:
                    break
                if message == "":
                    continue
                await self._handle_command(json.loads(message))
        except (ConnectionError, asyncio.IncompleteReadError, json.JSONDecodeError, TimeoutError):
            pass
        except Exception as exc:
            print(f"[bridge] unexpected error in client handler: {exc}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            print(f"[bridge] client disconnected (remaining clients: {len(self.clients)})")

    async def _handle_command(self, message: dict[str, Any]) -> None:
        if message.get("type") != "command":
            return
        command = message.get("command")
        value = message.get("value")
        print(f"[bridge] received command: {command} value={value}")
        if command == "start":
            self.start_pipeline()
            return
        if command == "stop":
            self.request_stop()
            return
        if command == "setSourceLanguage" and value in ("auto", "en", "ja"):
            self.options = replace(self.options, source_language=value)
            await self._broadcast_json(self._settings_event())
            return
        if command == "setTargetLanguage" and value in ("zh-TW", "zh-CN"):
            self.options = replace(self.options, target_language=value)
            await self._broadcast_json(self._settings_event())
            return
        if command == "setTranslationModel" and value in ("deepseek-v4-flash", "deepseek-v4-pro"):
            deepseek = replace(self.runtime_config.deepseek, model=value)
            self.runtime_config = replace(self.runtime_config, deepseek=deepseek)
            await self._broadcast_json(self._settings_event())

    def _run_pipeline(self) -> None:
        try:
            self.broadcast_status_threadsafe("starting", True, "Starting pipeline")
            _append_result_log(self.options, "Electron overlay pipeline started")
            pipeline_config = _build_pipeline_config(self.runtime_config, self.options)
            streaming_config = _build_streaming_pipeline_config(self.runtime_config, self.options)
            translate = self._build_translator()
            subtitle_log = (
                SubtitleLogRepository(resolve_subtitle_log_path(self.runtime_config, self.options.subtitle_log_path))
                if self.options.subtitle_log_enabled
                else None
            )

            transcriber = FasterWhisperTranscriber(
                language=self.options.source_language,
                model_size=self.options.model_size,
                device=self.options.device,
                compute_type=self.options.compute_type,
                beam_size=self.options.beam_size,
            )
            self.broadcast_status_threadsafe("starting", True, "Loading ASR model")
            transcriber.ensure_model_loaded()
            if transcriber.used_cpu_fallback:
                self.broadcast_status_threadsafe("running", True, "ASR CPU fallback active")

            def asr(segment_path: Path):
                return transcriber.transcribe(segment_path)

            def on_output(output: PipelineOutput, chunk_index: int | None = None) -> None:
                if subtitle_log is not None:
                    subtitle_log.append_translation(
                        output.translation,
                        start_time=output.asr.start_time,
                        end_time=output.asr.end_time,
                    )
                self.broadcast_subtitle_threadsafe(
                    segment_id=output.asr.segment_id,
                    kind="final",
                    source=output.asr.source_text,
                    translation=output.translation.translated_text,
                    source_lang=output.asr.source_language,
                    target_lang=output.translation.target_language,
                    latency_ms=output.translation.total_latency_ms,
                )
                self.broadcast_status_threadsafe(
                    "running",
                    True,
                    f"Segment {output.asr.segment_id} latency {output.translation.total_latency_ms:.0f} ms",
                )

            if self.options.continuous_loopback:
                _run_continuous_loopback_pipeline(
                    runtime_config=self.runtime_config,
                    options=self.options,
                    pipeline_config=pipeline_config,
                    streaming_config=streaming_config,
                    asr=asr,
                    translate=translate,
                    on_output=on_output,
                    on_streaming_event=self._on_streaming_event,
                    should_stop=self.stop_requested.is_set,
                    update_status=lambda message: self.broadcast_status_threadsafe("running", True, message),
                    subtitle_log=subtitle_log,
                )
            else:
                self.broadcast_status_threadsafe("starting", True, "Loading audio")
                audio = self._load_audio()
                self.broadcast_status_threadsafe("running", True, "Running pipeline")
                if self.options.streaming_strategy == "local_agreement":
                    run_streaming_pipeline_on_audio(
                        audio=audio,
                        config=streaming_config,
                        asr=asr,
                        translate=translate,
                        on_event=lambda event: self._on_streaming_event(event, None, subtitle_log),
                        should_stop=self.stop_requested.is_set,
                    )
                else:
                    run_terminal_pipeline_on_audio(
                        audio=audio,
                        config=pipeline_config,
                        asr=asr,
                        translate=translate,
                        on_output=lambda output: on_output(output, None),
                        should_stop=self.stop_requested.is_set,
                    )
            self.broadcast_status_threadsafe(
                "idle" if self.stop_requested.is_set() else "running",
                True,
                "Stopped" if self.stop_requested.is_set() else "Finished",
            )
        except Exception as exc:
            self.broadcast_status_threadsafe("error", True, str(exc))
        finally:
            self._pipeline_running = False
            _append_result_log(self.options, "Electron overlay pipeline finished")

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
        self.broadcast_subtitle_threadsafe(
            segment_id=event.asr.segment_id,
            kind=event.kind,
            source=event.asr.source_text,
            translation=event.translation.translated_text,
            source_lang=event.asr.source_language,
            target_lang=event.translation.target_language,
            latency_ms=event.translation.total_latency_ms,
        )
        self.broadcast_status_threadsafe(
            "running",
            True,
            f"{event.kind.title()} latency {event.translation.total_latency_ms:.0f} ms",
        )

    def _build_translator(self):
        repository = (
            open_glossary_repository(self.runtime_config, self.options.glossary_db)
            if self.options.glossary_enabled
            else None
        )
        if self.options.translation_mode == "echo":
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

        deepseek_config = self.runtime_config.deepseek
        if self.options.deepseek_timeout is not None:
            deepseek_config = replace(deepseek_config, timeout_seconds=self.options.deepseek_timeout)
        client = DeepSeekClient(
            config=deepseek_config,
            api_key=self.runtime_config.resolve_deepseek_api_key(),
        )
        return lambda text, source, target: translate_with_glossary(
            client,
            text=text,
            source_language=source,
            target_language=target,
            repository=repository,
        )

    def _load_audio(self):
        if self.options.audio_file:
            return load_audio_file_as_pcm16(
                self.options.audio_file,
                sample_rate=self.runtime_config.audio.sample_rate,
                channels=self.runtime_config.audio.channels,
                max_duration_seconds=self.options.max_audio_seconds,
            )
        if self.options.loopback_seconds is None:
            raise ValueError("Either audio_file, loopback_seconds, or continuous_loopback is required")
        return capture_loopback(
            seconds=self.options.loopback_seconds,
            target_sample_rate=self.runtime_config.audio.sample_rate,
            target_channels=self.runtime_config.audio.channels,
            chunk_ms=self.runtime_config.audio.chunk_ms,
        ).audio

    def broadcast_status_threadsafe(self, status: str, connected: bool, detail: str | None = None) -> None:
        _append_result_log(
            self.options,
            f"[BridgeStatus] status={status} connected={connected} clients={len(self.clients)} detail={detail or ''}",
        )
        print(
            "[bridge] status "
            f"status={status} connected={connected} clients={len(self.clients)} detail={_ascii_safe(detail or '')}",
            flush=True,
        )
        self._submit_broadcast(
            {
                "type": "status",
                "status": status,
                "backendConnected": connected,
                "detail": detail,
            }
        )

    async def broadcast_status(self, status: str, connected: bool, detail: str | None = None) -> None:
        await self._broadcast_json(
            {
                "type": "status",
                "status": status,
                "backendConnected": connected,
                "detail": detail,
            }
        )

    def broadcast_subtitle_threadsafe(
        self,
        *,
        segment_id: int,
        kind: str,
        source: str,
        translation: str,
        source_lang: str,
        target_lang: str,
        latency_ms: float,
    ) -> None:
        _append_result_log(
            self.options,
            "\n".join(
                [
                    f"[BridgeSubtitle] kind={kind} segment={segment_id} clients={len(self.clients)} "
                    f"source_chars={len(source)} translation_chars={len(translation)} latency={latency_ms:.0f} ms",
                    f"Source: {source}",
                    f"Translation: {translation}",
                ]
            ),
        )
        print(
            "[bridge] subtitle "
            f"kind={kind} segment={segment_id} clients={len(self.clients)} "
            f"source_chars={len(source)} translation_chars={len(translation)} latency={latency_ms:.0f}ms",
            flush=True,
        )
        self._submit_broadcast(
            {
                "type": "subtitle",
                "segmentId": segment_id,
                "kind": kind,
                "source": source,
                "translation": translation,
                "sourceLang": source_lang,
                "targetLang": target_lang,
                "latencyMs": round(latency_ms),
                "timestampMs": round(time.time() * 1000),
            }
        )

    def _settings_event(self) -> dict[str, Any]:
        return {
            "type": "settings",
            "sourceLang": self.options.source_language,
            "targetLang": self.options.target_language,
            "translationModel": self.runtime_config.deepseek.model,
        }

    def _submit_broadcast(self, payload: dict[str, Any]) -> None:
        if self.loop is None:
            return
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self._broadcast_json(payload)))

    async def _broadcast_json(self, payload: dict[str, Any]) -> None:
        disconnected: list[asyncio.StreamWriter] = []
        type_label = payload.get("type", "?")
        for writer in list(self.clients):
            try:
                await self._send_json(writer, payload)
            except ConnectionError:
                disconnected.append(writer)
        for writer in disconnected:
            self.clients.discard(writer)
        if disconnected:
            print(f"[bridge] removed {len(disconnected)} disconnected clients during {type_label} broadcast")

    async def _send_json(self, writer: asyncio.StreamWriter, payload: dict[str, Any]) -> None:
        writer.write(_encode_text_frame(json.dumps(payload, ensure_ascii=False)))
        await writer.drain()

    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        raw_headers = await reader.readuntil(b"\r\n\r\n")
        headers = raw_headers.decode("latin-1").split("\r\n")
        key = ""
        for header in headers:
            name, _, value = header.partition(":")
            if name.lower() == "sec-websocket-key":
                key = value.strip()
                break
        if not key:
            raise ConnectionError("Missing Sec-WebSocket-Key")
        accept = base64.b64encode(hashlib.sha1((key + WEBSOCKET_GUID).encode("ascii")).digest()).decode("ascii")
        writer.write(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii")
        )
        await writer.drain()

    async def _read_text_frame(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> str | None:
        first, second = await reader.readexactly(2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", await reader.readexactly(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", await reader.readexactly(8))[0]
        if opcode == 0x8:
            if length >= 2:
                await reader.readexactly(length)
            return None
        if opcode == 0x9:
            payload = await reader.readexactly(length)
            pong = bytes([0x8A, length]) + payload
            writer.write(pong)
            await writer.drain()
            return ""
        if opcode == 0xA:
            if length > 0:
                await reader.readexactly(length)
            return ""
        mask = await reader.readexactly(4) if masked else b"\x00\x00\x00\x00"
        payload = bytearray(await reader.readexactly(length))
        if masked:
            for index in range(length):
                payload[index] ^= mask[index % 4]
        if opcode != 0x1:
            print(f"[bridge] unexpected opcode {opcode:#x} len={length}", flush=True)
            return ""
        return payload.decode("utf-8")


def _encode_text_frame(text: str) -> bytes:
    payload = text.encode("utf-8")
    length = len(payload)
    if length < 126:
        header = bytes([0x81, length])
    elif length < 65536:
        header = bytes([0x81, 126]) + struct.pack("!H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack("!Q", length)
    return header + payload


def _ascii_safe(text: str) -> str:
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


def run_electron_overlay_live(runtime_config: RuntimeConfig, options: OverlayPipelineOptions) -> int:
    root = electron_overlay_root()
    package_json = root / "package.json"
    if not package_json.exists():
        raise OverlayError(f"Electron overlay package.json not found: {package_json}")

    bridge = ElectronOverlayBridge(runtime_config, options)
    ready = threading.Event()
    failure: list[BaseException] = []

    def run_bridge() -> None:
        async def runner() -> None:
            ready.set()
            await bridge.run()

        try:
            asyncio.run(runner())
        except asyncio.CancelledError:
            pass
        except BaseException as exc:
            failure.append(exc)
            ready.set()

    bridge_thread = threading.Thread(target=run_bridge, name="electron-overlay-bridge", daemon=True)
    bridge_thread.start()
    ready.wait(timeout=2.0)
    if failure:
        raise OverlayError(f"Electron overlay bridge failed: {failure[0]}")

    env = electron_overlay_env()
    env["OVERLAY_BRIDGE_MODE"] = "live"
    env["OVERLAY_BRIDGE_URL"] = BRIDGE_URL
    env.setdefault("OVERLAY_WINDOW_MODE", "multi")
    if options.result_log:
        result_log_path = Path(options.result_log)
        if not result_log_path.is_absolute():
            result_log_path = Path.cwd() / result_log_path
        suffix = result_log_path.suffix or ".txt"
        frontend_log = result_log_path.with_name(f"{result_log_path.stem}_electron{suffix}")
        env["OVERLAY_FRONTEND_DEBUG_LOG"] = str(frontend_log)
    process: subprocess.Popen[bytes] | None = None
    frontend_exit_code: int | None = None
    try:
        process = subprocess.Popen([resolve_npm_command(), "run", "dev:live"], cwd=root, env=env)
        _append_result_log(options, "Electron frontend command launched; bridge lifetime is tied to Python process")
        while True:
            exit_code = process.poll()
            if exit_code is not None and frontend_exit_code is None:
                frontend_exit_code = exit_code
                message = (
                    f"Electron frontend command exited with code {exit_code}; "
                    "keeping Python bridge alive until manual shutdown"
                )
                print(f"[bridge] {message}", flush=True)
                _append_result_log(options, message)
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 130
    except FileNotFoundError as exc:
        raise OverlayError("npm is required to run the Electron overlay frontend") from exc
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
        bridge.shutdown()
