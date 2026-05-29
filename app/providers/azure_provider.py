from __future__ import annotations

from html import escape
from pathlib import Path

from .base import TTSProvider, TTSResult


class AzureProvider(TTSProvider):
    id = "azure"
    name = "Azure Speech"
    default_extension = ".mp3"

    def __init__(self, key: str, region: str, endpoint: str, voice: str, output_format: str) -> None:
        self.key = key
        self.region = region
        self.endpoint = endpoint
        self.voice = voice
        self.output_format = (output_format or "audio-16khz-128kbitrate-mono-mp3").lower()

    def is_enabled(self) -> bool:
        return bool(self.key) and (bool(self.region) or bool(self.endpoint))

    def disabled_reason(self) -> str | None:
        if not self.key:
            return "AZURE_SPEECH_KEY não configurada no .env."
        if not (self.region or self.endpoint):
            return "Defina AZURE_SPEECH_REGION ou AZURE_SPEECH_ENDPOINT no .env."
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
        if not self.key:
            raise RuntimeError("AZURE_SPEECH_KEY não configurada no .env.")
        if not (self.region or self.endpoint):
            raise RuntimeError("Defina AZURE_SPEECH_REGION ou AZURE_SPEECH_ENDPOINT no .env.")

        try:
            import azure.cognitiveservices.speech as speechsdk
        except Exception as exc:
            raise RuntimeError("Dependência azure-cognitiveservices-speech não instalada no ambiente.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or f"azure_output{self.default_extension}"
        stem = Path(target_name).stem
        filename = f"{stem}.mp3"
        file_path = output_dir / filename

        format_map = {
            "audio-16khz-128kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,
            "audio-16khz-32kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            "audio-16khz-64kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3,
            "audio-24khz-48kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3,
            "audio-24khz-96kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3,
            "audio-24khz-160kbitrate-mono-mp3": speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,
        }
        output_format = format_map.get(self.output_format)
        if output_format is None:
            raise RuntimeError(
                f"Formato de saída do Azure inválido: {self.output_format}. Use um formato mp3 compatível."
            )

        effective_voice = voice or self.voice
        if not effective_voice:
            raise RuntimeError("AZURE_SPEECH_VOICE não configurada e voice ausente no request.")

        rate = f"{int(round(speed * 100))}%"
        safe_text = escape(text)
        safe_language = language or "pt-BR"
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xml:lang="{safe_language}">'
            f'<voice name="{escape(effective_voice)}">'
            f'<prosody rate="{rate}">{safe_text}</prosody>'
            f"</voice>"
            f"</speak>"
        )

        try:
            if self.endpoint:
                speech_config = speechsdk.SpeechConfig(subscription=self.key, endpoint=self.endpoint)
            else:
                speech_config = speechsdk.SpeechConfig(subscription=self.key, region=self.region)

            speech_config.set_speech_synthesis_output_format(output_format)
            speech_config.speech_synthesis_voice_name = effective_voice
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(file_path))
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = synthesizer.speak_ssml_async(ssml).get()

            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                cancellation = result.cancellation_details
                detail = "Falha ao gerar áudio com Azure Speech."
                if cancellation is not None:
                    error_details = getattr(cancellation, "error_details", "") or ""
                    if error_details:
                        detail = f"{detail} {error_details}"
                raise RuntimeError(detail)

            if not file_path.exists() or file_path.stat().st_size == 0:
                raise RuntimeError("Azure Speech não gerou um arquivo de áudio válido.")
        except RuntimeError:
            file_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Falha ao gerar áudio com Azure Speech. Verifique chave, região/endpoint, voz e conectividade."
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)
