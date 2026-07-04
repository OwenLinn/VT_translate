from __future__ import annotations

import wave
from array import array

from yt_live_translator.audio.resampler import PCM16Audio, convert_pcm16, write_wav


def test_convert_pcm16_downmixes_stereo_to_mono() -> None:
    stereo = array("h", [1000, 3000, -1000, -3000])

    audio = convert_pcm16(
        pcm=stereo.tobytes(),
        source_sample_rate=16000,
        source_channels=2,
        target_sample_rate=16000,
        target_channels=1,
    )

    samples = array("h")
    samples.frombytes(audio.pcm)
    assert list(samples) == [2000, -2000]
    assert audio.sample_rate == 16000
    assert audio.channels == 1


def test_convert_pcm16_resamples_to_target_rate() -> None:
    mono = array("h", [0, 1000, 2000, 3000])

    audio = convert_pcm16(
        pcm=mono.tobytes(),
        source_sample_rate=4,
        source_channels=1,
        target_sample_rate=2,
        target_channels=1,
    )

    assert audio.frame_count == 2
    assert audio.duration_seconds == 1.0


def test_write_wav_creates_readable_file(tmp_path) -> None:
    output = tmp_path / "capture.wav"
    audio = PCM16Audio(pcm=array("h", [0, 1000, -1000]).tobytes(), sample_rate=16000, channels=1)

    write_wav(output, audio)

    with wave.open(str(output), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 3
