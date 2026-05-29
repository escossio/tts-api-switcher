from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSResult


class GoogleProvider(TTSProvider):
    id = "google"
    name = "Google Text-to-Speech"

    def __init__(self, enabled: bool, credentials_path: str, voice: str) -> None:
        self.enabled = enabled
        self.credentials_path = credentials_path
        self.voice = voice

    def is_enabled(self) -> bool:
        return self.enabled and bool(self.credentials_path)

    def generate(
        self,
        text: str,
        language: str,
        voice: str,
        speed: float,
        output_dir: Path,
        filename: str | None = None,
    ) -> TTSResult:
        if not self.enabled:
            raise RuntimeError("GOOGLE_TTS_ENABLED=false. Provider Google desativado.")
        if not self.credentials_path:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS não configurada.")

        try:
            from google.cloud import texttospeech
        except Exception as exc:
            raise RuntimeError("Dependência do Google TTS não instalada no ambiente.") from exc

        _ = texttospeech
        raise RuntimeError(
            "Provider Google preparado, mas a geração real de áudio ainda não foi habilitada neste MVP."
        )
