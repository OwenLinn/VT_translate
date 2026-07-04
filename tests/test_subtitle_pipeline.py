from __future__ import annotations

from array import array
from dataclasses import dataclass
from pathlib import Path

from yt_live_translator.audio.resampler import PCM16Audio
from yt_live_translator.core.subtitle_pipeline import (
    PipelineConfig,
    StreamingPipelineConfig,
    run_terminal_pipeline_on_audio,
    run_streaming_pipeline_on_audio,
)
from yt_live_translator.speech.asr_faster_whisper import ASRFileResult, ASRSegmentText
from yt_live_translator.speech.segmenter import SegmenterConfig
from yt_live_translator.speech.streaming_agreement import LocalAgreementConfig


@dataclass
class FakeASR:
    calls: list[Path]

    def __call__(self, path: Path) -> ASRFileResult:
        self.calls.append(path)
        return ASRFileResult(
            audio_path=path,
            text="hello stream",
            language="en",
            segments=[ASRSegmentText(start=0.0, end=1.0, text="hello stream")],
            model_size="fake",
            device="cpu",
            compute_type="int8",
            beam_size=1,
            duration_seconds=1.0,
            latency_ms=12.0,
        )


@dataclass
class SequenceASR:
    texts: list[str]
    calls: list[Path]

    def __call__(self, path: Path) -> ASRFileResult:
        self.calls.append(path)
        index = min(len(self.calls) - 1, len(self.texts) - 1)
        text = self.texts[index]
        return ASRFileResult(
            audio_path=path,
            text=text,
            language="en",
            segments=[ASRSegmentText(start=0.0, end=1.0, text=text)],
            model_size="fake",
            device="cpu",
            compute_type="int8",
            beam_size=1,
            duration_seconds=1.0,
            latency_ms=10.0,
        )


def test_run_terminal_pipeline_on_audio_connects_asr_and_translation() -> None:
    sample_rate = 1000
    samples = array("h", [2000] * 1200)
    audio = PCM16Audio(pcm=samples.tobytes(), sample_rate=sample_rate, channels=1)
    fake_asr = FakeASR(calls=[])

    outputs = run_terminal_pipeline_on_audio(
        audio=audio,
        config=PipelineConfig(
            source_language="en",
            target_language="zh-TW",
            vad_threshold=0.01,
            segmenter=SegmenterConfig(
                frame_ms=100,
                min_speech_ms=200,
                max_speech_ms=500,
                silence_end_ms=200,
                padding_ms=0,
            ),
            max_segments=1,
        ),
        asr=fake_asr,
        translate=lambda text, _source, target: f"{target}:{text}",
    )

    assert len(outputs) == 1
    assert len(fake_asr.calls) == 1
    assert outputs[0].asr.source_text == "hello stream"
    assert outputs[0].translation.translated_text == "zh-TW:hello stream"
    assert outputs[0].translation.total_latency_ms >= outputs[0].asr.asr_latency_ms


def test_run_terminal_pipeline_calls_output_callback() -> None:
    sample_rate = 1000
    samples = array("h", [2000] * 1200)
    audio = PCM16Audio(pcm=samples.tobytes(), sample_rate=sample_rate, channels=1)
    seen = []

    outputs = run_terminal_pipeline_on_audio(
        audio=audio,
        config=PipelineConfig(
            source_language="en",
            target_language="zh-TW",
            vad_threshold=0.01,
            segmenter=SegmenterConfig(
                frame_ms=100,
                min_speech_ms=200,
                max_speech_ms=500,
                silence_end_ms=200,
                padding_ms=0,
            ),
            max_segments=1,
        ),
        asr=FakeASR(calls=[]),
        translate=lambda text, _source, target: f"{target}:{text}",
        on_output=seen.append,
    )

    assert seen == outputs


def test_run_terminal_pipeline_honors_stop_check() -> None:
    sample_rate = 1000
    samples = array("h", [2000] * 1200)
    audio = PCM16Audio(pcm=samples.tobytes(), sample_rate=sample_rate, channels=1)

    outputs = run_terminal_pipeline_on_audio(
        audio=audio,
        config=PipelineConfig(
            source_language="en",
            target_language="zh-TW",
            vad_threshold=0.01,
            segmenter=SegmenterConfig(
                frame_ms=100,
                min_speech_ms=200,
                max_speech_ms=500,
                silence_end_ms=200,
                padding_ms=0,
            ),
            max_segments=2,
        ),
        asr=FakeASR(calls=[]),
        translate=lambda text, _source, target: f"{target}:{text}",
        should_stop=lambda: True,
    )

    assert outputs == []


def test_streaming_pipeline_emits_partial_and_final_events() -> None:
    sample_rate = 1000
    samples = array("h", [2000] * 3000)
    audio = PCM16Audio(pcm=samples.tobytes(), sample_rate=sample_rate, channels=1)
    fake_asr = SequenceASR(
        texts=[
            "hello stream today",
            "hello stream today.",
            "hello stream today.",
        ],
        calls=[],
    )
    seen = []

    events = run_streaming_pipeline_on_audio(
        audio=audio,
        config=StreamingPipelineConfig(
            source_language="en",
            target_language="zh-TW",
            asr_tick_ms=1000,
            rolling_window_sec=3.0,
            overlap_sec=0.0,
            agreement=LocalAgreementConfig(
                source_language="en",
                min_commit_tokens=2,
                max_commit_sec=10,
                partial_interval_sec=0.1,
            ),
            max_final_segments=1,
        ),
        asr=fake_asr,
        translate=lambda text, _source, target: f"{target}:{text}",
        on_event=seen.append,
    )

    assert [event.kind for event in events] == ["partial", "final"]
    assert seen == events
    assert events[0].translation.source_text == "hello stream today"
    assert events[1].translation.source_text == "hello stream today."
    assert events[1].translation.translated_text == "zh-TW:hello stream today."


def test_streaming_pipeline_recent_silence_can_trigger_final() -> None:
    sample_rate = 1000
    speech = [2000] * 1200
    silence = [0] * 800
    audio = PCM16Audio(pcm=array("h", speech + silence).tobytes(), sample_rate=sample_rate, channels=1)
    fake_asr = SequenceASR(texts=["hello stream", "hello stream"], calls=[])

    events = run_streaming_pipeline_on_audio(
        audio=audio,
        config=StreamingPipelineConfig(
            source_language="en",
            target_language="zh-TW",
            asr_tick_ms=1000,
            rolling_window_sec=3.0,
            overlap_sec=0.0,
            agreement=LocalAgreementConfig(
                source_language="en",
                min_commit_tokens=5,
                max_commit_sec=10,
            ),
            max_final_segments=1,
            silence_end_ms=500,
            silence_threshold=0.001,
        ),
        asr=fake_asr,
        translate=lambda text, _source, target: f"{target}:{text}",
    )

    assert events[-1].kind == "final"
    assert events[-1].translation.source_text == "hello stream"
