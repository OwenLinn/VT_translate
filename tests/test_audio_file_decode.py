from __future__ import annotations

import numpy as np
import pytest

from yt_live_translator.core import subtitle_pipeline


def test_load_audio_file_as_pcm16_limits_duration(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake")

    def fake_decode_audio(path: str, sampling_rate: int):
        assert path == str(audio_path)
        assert sampling_rate == 10
        return np.linspace(-1.0, 1.0, 100, dtype=np.float32)

    import faster_whisper.audio

    monkeypatch.setattr(faster_whisper.audio, "decode_audio", fake_decode_audio)

    audio = subtitle_pipeline.load_audio_file_as_pcm16(
        audio_path,
        sample_rate=10,
        channels=1,
        max_duration_seconds=3,
    )

    assert audio.sample_rate == 10
    assert audio.channels == 1
    assert audio.frame_count == 30


def test_load_audio_file_as_pcm16_rejects_invalid_duration(tmp_path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake")

    with pytest.raises(ValueError, match="max_duration_seconds"):
        subtitle_pipeline.load_audio_file_as_pcm16(
            audio_path,
            sample_rate=10,
            channels=1,
            max_duration_seconds=0,
        )
