"""Lightweight energy-based VAD for Stage 4 smoke tests."""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass


@dataclass(frozen=True)
class VADDecision:
    is_speech: bool
    rms: float
    normalized_rms: float


@dataclass(frozen=True)
class EnergyVAD:
    """A simple PCM16 energy gate.

    This is intentionally small and deterministic for Stage 4 smoke tests. A
    Silero-based implementation can replace it later without changing the
    segmenter contract.
    """

    threshold: float = 0.01

    def analyze(self, pcm: bytes) -> VADDecision:
        rms = pcm16_rms(pcm)
        normalized = rms / 32768.0
        return VADDecision(
            is_speech=normalized >= self.threshold,
            rms=rms,
            normalized_rms=normalized,
        )


def pcm16_rms(pcm: bytes) -> float:
    samples = array("h")
    samples.frombytes(pcm)
    if not samples:
        return 0.0
    square_sum = sum(sample * sample for sample in samples)
    return math.sqrt(square_sum / len(samples))
