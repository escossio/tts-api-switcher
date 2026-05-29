from __future__ import annotations

from pathlib import Path

from .base import TTSProvider, TTSResult


class GoogleProvider(TTSProvider):
    id = "google"
    name = "Google Text-to-Speech"
    default_extension = ".mp3"

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
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS não configurada no .env.")

        credential_file = Path(self.credentials_path).expanduser()
        if not credential_file.exists():
            raise RuntimeError("Arquivo de credencial do Google não encontrado no caminho configurado.")

        try:
            from google.cloud import texttospeech
            from google.oauth2 import service_account
        except Exception as exc:
            raise RuntimeError("Dependência google-cloud-texttospeech não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"google_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.mp3"
        file_path = output_dir / filename

        try:
            credentials = service_account.Credentials.from_service_account_file(str(credential_file))
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
        except RuntimeError:
            raise
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Falha ao gerar áudio com Google TTS. Verifique credencial, voz, idioma e conectividade."
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
