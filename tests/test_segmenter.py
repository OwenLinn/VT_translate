from __future__ import annotations

from array import array

from yt_live_translator.audio.resampler import PCM16Audio
from yt_live_translator.speech.segmenter import SegmenterConfig, segment_audio
from yt_live_translator.speech.vad import EnergyVAD, pcm16_rms


def test_pcm16_rms_detects_energy() -> None:
    samples = array("h", [0, 1000, -1000, 0])

    assert pcm16_rms(samples.tobytes()) > 0
    assert pcm16_rms(b"") == 0


def test_segment_audio_splits_on_silence() -> None:
    sample_rate = 1000
    frame_samples = 100
    speech_frame = array("h", [2000] * frame_samples).tobytes()
    silence_frame = array("h", [0] * frame_samples).tobytes()
    pcm = b"".join(
        [
            speech_frame,
            speech_frame,
            speech_frame,
            silence_frame,
            silence_frame,
            speech_frame,
            speech_frame,
            speech_frame,
        ]
    )
    audio = PCM16Audio(pcm=pcm, sample_rate=sample_rate, channels=1)

    segments = segment_audio(
        audio=audio,
        vad=EnergyVAD(threshold=0.01),
        config=SegmenterConfig(
            frame_ms=100,
            min_speech_ms=200,
            max_speech_ms=1000,
            silence_end_ms=200,
            padding_ms=0,
        ),
    )

    assert len(segments) == 2
    assert segments[0].segment_id == 1
    assert segments[0].start_time == 0.0
    assert round(segments[0].end_time, 2) == 0.3
    assert round(segments[1].start_time, 2) == 0.5


def test_segment_audio_respects_max_speech_duration() -> None:
    sample_rate = 1000
    frame_samples = 100
    speech_frame = array("h", [2000] * frame_samples).tobytes()
    audio = PCM16Audio(pcm=speech_frame * 6, sample_rate=sample_rate, channels=1)

    segments = segment_audio(
        audio=audio,
        vad=EnergyVAD(threshold=0.01),
        config=SegmenterConfig(
            frame_ms=100,
            min_speech_ms=100,
            max_speech_ms=300,
            silence_end_ms=200,
            padding_ms=0,
        ),
    )

    assert len(segments) == 2
    assert all(round(segment.end_time - segment.start_time, 2) == 0.3 for segment in segments)
