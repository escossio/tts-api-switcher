from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSResult


class OpenAIProvider(TTSProvider):
    id = "openai"
    name = "OpenAI TTS"

    def __init__(self, api_key: str, model: str, voice: str) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        text: str,
        language: str,
        voice: str,
        speed: float,
        output_dir: Path,
        filename: str | None = None,
    ) -> TTSResult:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY não configurada.")

        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("Dependência da OpenAI não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = filename or "openai_not_implemented.wav"
        file_path = output_dir / filename

        client = OpenAI(api_key=self.api_key)
        _ = client
        raise RuntimeError(
            "Provider OpenAI preparado, mas a gravação de áudio real ainda não foi habilitada neste MVP."
        )
