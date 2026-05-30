from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSProviderError, TTSResult, normalize_voice


class OpenAIProvider(TTSProvider):
    id = "openai"
    name = "OpenAI TTS"
    default_extension = ".mp3"
    supports_voice_list = True

    SUPPORTED_VOICES = [
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "nova",
        "onyx",
        "sage",
        "shimmer",
        "verse",
    ]

    def __init__(self, api_key: str, model: str, voice: str, audio_format: str) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.audio_format = (audio_format or "mp3").lower()

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def disabled_reason(self) -> str | None:
        if not self.api_key:
            return "OPENAI_API_KEY não configurada no .env."
        return None

    def list_voices(self) -> list[dict[str, object]]:
        default_voice = (self.voice or "").strip()
        return [
            normalize_voice(
                voice,
                name=voice,
                description="Voz suportada pelo app para OpenAI TTS.",
                default=voice == default_voice,
            )
            for voice in self.SUPPORTED_VOICES
        ]

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
            raise TTSProviderError("missing_api_key", "OPENAI_API_KEY não configurada no .env.")

        try:
            from openai import OpenAI
        except Exception as exc:
            raise TTSProviderError(
                "unknown_provider_error",
                "Dependência da OpenAI não instalada no ambiente.",
            ) from exc

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
            status_code = getattr(exc, "status_code", None)
            code = getattr(exc, "code", None)
            message = str(exc).lower()

            if status_code == 401:
                raise TTSProviderError(
                    "unauthorized_401_key_invalid_or_revoked",
                    "OpenAI recusou a requisição. Verifique a chave, revogação ou permissão da conta.",
                ) from exc

            if status_code == 429 or code == "insufficient_quota":
                if "billing" in message or "plan" in message:
                    raise TTSProviderError(
                        "billing_required",
                        "OpenAI recusou a requisição por billing ou plano insuficientes.",
                    ) from exc
                raise TTSProviderError(
                    "quota_exceeded",
                    "OpenAI recusou a requisição por quota insuficiente.",
                ) from exc

            if status_code == 400:
                if "voice" in message:
                    raise TTSProviderError(
                        "invalid_voice",
                        "OpenAI rejeitou a voz informada.",
                    ) from exc
                if "model" in message:
                    raise TTSProviderError(
                        "invalid_model",
                        "OpenAI rejeitou o modelo informado.",
                    ) from exc

            if "connection" in message or "network" in message or "timeout" in message:
                raise TTSProviderError(
                    "network_error",
                    "OpenAI indisponível no momento. Tente novamente.",
                ) from exc

            raise TTSProviderError(
                "unknown_provider_error",
                "Falha ao gerar áudio com OpenAI TTS. Verifique a chave, modelo, voz e conectividade.",
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
