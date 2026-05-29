from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSResult


class ElevenLabsProvider(TTSProvider):
    id = "elevenlabs"
    name = "ElevenLabs"
    default_extension = ".mp3"

    def __init__(self, api_key: str, model: str, voice_id: str, output_format: str) -> None:
        self.api_key = api_key
        self.model = model or "eleven_multilingual_v2"
        self.voice_id = voice_id
        self.output_format = output_format or "mp3_44100_128"

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def disabled_reason(self) -> str | None:
        if not self.api_key:
            return "ELEVENLABS_API_KEY não configurada no .env."
        return None

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
            raise RuntimeError("ELEVENLABS_API_KEY não configurada no .env.")

        effective_voice = voice or self.voice_id
        if not effective_voice:
            raise RuntimeError("ElevenLabs requer ELEVENLABS_VOICE_ID ou um voice_id no request.")

        try:
            from elevenlabs import VoiceSettings
            from elevenlabs.client import ElevenLabs
        except Exception as exc:
            raise RuntimeError("Dependência elevenlabs não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"elevenlabs_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.mp3"
        file_path = output_dir / filename

        try:
            client = ElevenLabs(api_key=self.api_key)
            response = client.text_to_speech.convert(
                text=text,
                voice_id=effective_voice,
                model_id=self.model,
                output_format=self.output_format,
                voice_settings=VoiceSettings(speed=speed),
            )

            with open(file_path, "wb") as audio_file:
                for chunk in response:
                    if chunk:
                        audio_file.write(chunk)
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Falha ao gerar áudio com ElevenLabs. Verifique a chave, voice_id, modelo e conectividade."
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
