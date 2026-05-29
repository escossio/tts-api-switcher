from __future__ import annotations

from html import escape
from pathlib import Path

from .base import TTSProvider, TTSResult


class PollyProvider(TTSProvider):
    id = "polly"
    name = "Amazon Polly"
    default_extension = ".mp3"

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        default_region: str,
        voice_id: str,
        engine: str,
        output_format: str,
    ) -> None:
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.default_region = default_region
        self.voice_id = voice_id
        self.engine = engine or "neural"
        self.output_format = (output_format or "mp3").lower()

    def is_enabled(self) -> bool:
        return bool(self.access_key_id) and bool(self.secret_access_key) and bool(self.default_region)

    def disabled_reason(self) -> str | None:
        if not self.access_key_id or not self.secret_access_key:
            return "AWS_ACCESS_KEY_ID ou AWS_SECRET_ACCESS_KEY não configurados no .env."
        if not self.default_region:
            return "AWS_DEFAULT_REGION não configurada no .env."
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
        if not self.access_key_id or not self.secret_access_key:
            raise RuntimeError("AWS_ACCESS_KEY_ID ou AWS_SECRET_ACCESS_KEY não configurados no .env.")
        if not self.default_region:
            raise RuntimeError("AWS_DEFAULT_REGION não configurada no .env.")

        try:
            import boto3
        except Exception as exc:
            raise RuntimeError("Dependência boto3 não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"polly_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.mp3"
        file_path = output_dir / filename

        effective_voice = voice or self.voice_id
        if not effective_voice:
            raise RuntimeError("AWS_POLLY_VOICE_ID não configurada e voice ausente no request.")

        rate = f"{int(round(speed * 100))}%"
        safe_text = escape(text)
        ssml = f'<speak><prosody rate="{rate}">{safe_text}</prosody></speak>'

        try:
            client = boto3.client("polly", region_name=self.default_region)

            request = {
                "Text": ssml,
                "TextType": "ssml",
                "VoiceId": effective_voice,
                "OutputFormat": self.output_format or "mp3",
            }
            if self.engine:
                request["Engine"] = self.engine

            response = client.synthesize_speech(**request)
            audio_stream = response.get("AudioStream")
            if audio_stream is None:
                raise RuntimeError("Amazon Polly não retornou fluxo de áudio.")

            with open(file_path, "wb") as audio_file:
                audio_file.write(audio_stream.read())
        except RuntimeError:
            file_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            message = getattr(exc, "response", {}).get("Error", {}).get("Message") if hasattr(exc, "response") else ""
            if message:
                raise RuntimeError(f"Falha ao gerar áudio com Amazon Polly: {message}") from exc
            raise RuntimeError(
                "Falha ao gerar áudio com Amazon Polly. Verifique credenciais, voice, engine e conectividade."
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
