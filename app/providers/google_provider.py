from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSProviderError, TTSResult, normalize_voice


class GoogleProvider(TTSProvider):
    id = "google"
    name = "Google Text-to-Speech"
    default_extension = ".mp3"
    supports_voice_list = True

    SUPPORTED_VOICES = [
        "pt-BR-Neural2-A",
        "pt-BR-Neural2-B",
        "pt-BR-Neural2-C",
        "pt-BR-Wavenet-A",
        "pt-BR-Wavenet-B",
        "pt-BR-Wavenet-C",
        "pt-BR-Standard-A",
        "pt-BR-Standard-B",
        "pt-BR-Standard-C",
    ]

    def __init__(
        self,
        enabled: bool,
        credentials_path: str,
        voice: str,
        language_code: str,
        audio_encoding: str,
    ) -> None:
        self.enabled = enabled
        self.credentials_path = credentials_path
        self.voice = voice
        self.language_code = language_code
        self.audio_encoding = (audio_encoding or "MP3").upper()

    def is_enabled(self) -> bool:
        return self.enabled and bool(self.credentials_path)

    def disabled_reason(self) -> str | None:
        if not self.enabled:
            return "GOOGLE_TTS_ENABLED=false. Provider Google desativado."
        if not self.credentials_path:
            return "GOOGLE_APPLICATION_CREDENTIALS não configurada no .env."
        return None

    def list_voices(self) -> list[dict[str, object]]:
        default_voice = (self.voice or "").strip()
        return [
            normalize_voice(
                voice,
                name=voice,
                language="pt-BR",
                description="Lista padrão inicial de vozes pt-BR para Google TTS.",
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
        if not self.enabled:
            raise TTSProviderError("provider_disabled", "Google TTS desativado no .env.")
        if not self.credentials_path:
            raise TTSProviderError("credentials_file_missing", "GOOGLE_APPLICATION_CREDENTIALS não configurada no .env.")

        credential_file = Path(self.credentials_path).expanduser()
        if not credential_file.exists():
            raise TTSProviderError(
                "credentials_file_missing",
                "Arquivo de credencial do Google não encontrado no caminho configurado.",
            )

        try:
            from google.cloud import texttospeech
            from google.api_core import exceptions as google_exceptions
            from google.oauth2 import service_account
        except Exception as exc:
            raise TTSProviderError(
                "unknown_provider_error",
                "Dependência google-cloud-texttospeech não instalada no ambiente.",
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"google_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.mp3"
        file_path = output_dir / filename

        try:
            credentials = service_account.Credentials.from_service_account_file(str(credential_file))
        except PermissionError as exc:
            raise TTSProviderError(
                "credentials_file_not_visible_in_container",
                "O processo do container não consegue ler o JSON de credencial do Google.",
            ) from exc
        except Exception as exc:
            raise TTSProviderError(
                "invalid_service_account_json",
                "Arquivo de credencial do Google inválido ou malformado.",
            ) from exc

        try:
            client = texttospeech.TextToSpeechClient(credentials=credentials)

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=language or self.language_code or "pt-BR",
                name=voice or self.voice or "pt-BR-Neural2-B",
            )

            audio_encoding_name = self.audio_encoding or "MP3"
            audio_encoding = getattr(texttospeech.AudioEncoding, audio_encoding_name, texttospeech.AudioEncoding.MP3)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=audio_encoding,
                speaking_rate=speed,
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )

            with open(file_path, "wb") as audio_file:
                audio_file.write(response.audio_content)
        except TTSProviderError:
            raise
        except google_exceptions.PermissionDenied as exc:
            file_path.unlink(missing_ok=True)
            message = str(exc).lower()
            if "billing" in message:
                raise TTSProviderError(
                    "billing_not_enabled",
                    "Google TTS recusou a requisição. Verifique billing e permissões da service account.",
                ) from exc
            if "not been used" in message or "disabled" in message:
                raise TTSProviderError(
                    "api_not_enabled",
                    "Google TTS recusou a requisição. A API Cloud Text-to-Speech parece desabilitada no projeto.",
                ) from exc
            raise TTSProviderError(
                "permission_denied",
                "Google TTS recusou a requisição. Verifique permissões da service account.",
            ) from exc
        except google_exceptions.InvalidArgument as exc:
            file_path.unlink(missing_ok=True)
            raise TTSProviderError(
                "invalid_voice",
                "Google TTS rejeitou a voz ou o idioma informados.",
            ) from exc
        except (google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as exc:
            file_path.unlink(missing_ok=True)
            raise TTSProviderError(
                "network_error",
                "Google TTS indisponível no momento. Tente novamente.",
            ) from exc
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            raise TTSProviderError(
                "unknown_provider_error",
                "Falha ao gerar áudio com Google TTS. Verifique credencial, voz, idioma e conectividade.",
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
