from __future__ import annotations

import hashlib
import math
import struct
import wave
from pathlib import Path

from .base import TTSProvider, TTSResult


class MockProvider(TTSProvider):
    id = "mock"
    name = "Mock Provider"

    def generate(
        self,
        text: str,
        language: str,
        voice: str,
        speed: float,
        output_dir: Path,
        filename: str | None = None,
    ) -> TTSResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = filename or self._build_filename(text)
        file_path = output_dir / filename
        self._write_tone(file_path, text=text, speed=speed)
        return TTSResult(filename=filename, file_path=file_path)

    def _build_filename(self, text: str) -> str:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        return f"mock_{digest}.wav"

    def _write_tone(self, file_path: Path, text: str, speed: float) -> None:
        sample_rate = 22050
        duration = max(1.0, min(5.0, 2.0 / max(speed, 0.1)))
        amplitude = 16000
        checksum = sum(text.encode("utf-8"))
        base_freq = 440 + (checksum % 220)
        frame_count = int(sample_rate * duration)

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            frames = bytearray()
            for index in range(frame_count):
                sample = int(amplitude * math.sin(2 * math.pi * base_freq * index / sample_rate))
                frames.extend(struct.pack("<h", sample))
            wav_file.writeframes(bytes(frames))
