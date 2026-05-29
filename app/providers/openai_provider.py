from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSResult


class OpenAIProvider(TTSProvider):
    id = "openai"
    name = "OpenAI TTS"
    default_extension = ".mp3"

    def __init__(self, api_key: str, model: str, voice: str, audio_format: str) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.audio_format = (audio_format or "mp3").lower()

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
            raise RuntimeError("OPENAI_API_KEY não configurada no .env.")

        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("Dependência da OpenAI não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"openai_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.{self.audio_format}"
        file_path = output_dir / filename

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.audio.speech.create(
                model=self.model or "gpt-4o-mini-tts",
                voice=voice or self.voice or "alloy",
                input=text,
                response_format=self.audio_format or "mp3",
                speed=speed,
            )
            response.stream_to_file(str(file_path))
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Falha ao gerar áudio com OpenAI TTS. Verifique a chave, modelo, voz e conectividade."
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
