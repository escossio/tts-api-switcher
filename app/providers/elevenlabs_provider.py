from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

from .base import TTSProvider, TTSProviderError, TTSResult, normalize_voice


class ElevenLabsProvider(TTSProvider):
    id = "elevenlabs"
    name = "ElevenLabs"
    default_extension = ".mp3"
    supports_voice_list = True

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

    def list_voices(self) -> list[dict[str, object]]:
        if not self.api_key:
            return []

        voices = self._fetch_voices()
        default_voice = (self.voice_id or "").strip()
        normalized: list[dict[str, object]] = []
        for item in voices:
            voice_id = str(item.get("voice_id") or item.get("id") or "").strip()
            if not voice_id:
                continue
            name = str(item.get("name") or voice_id).strip()
            labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
            language = str(item.get("language") or labels.get("language") or "").strip()
            gender = str(item.get("gender") or labels.get("gender") or "").strip()
            description = str(item.get("description") or item.get("category") or "").strip()
            normalized.append(
                normalize_voice(
                    voice_id,
                    name=name,
                    language=language,
                    gender=gender,
                    description=description,
                    default=voice_id == default_voice,
                )
            )
        return normalized

    def _fetch_voices(self) -> list[dict[str, object]]:
        url = "https://api.elevenlabs.io/v1/voices"
        req = request.Request(
            url,
            headers={
                "xi-api-key": self.api_key,
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            code, message = self._classify_http_error(exc)
            raise TTSProviderError(code, message) from exc
        except error.URLError as exc:
            raise TTSProviderError("network_error", "Falha ao listar vozes da ElevenLabs: erro de rede.") from exc
        except Exception as exc:
            raise TTSProviderError("unknown_provider_error", "Falha ao listar vozes da ElevenLabs.") from exc

        if isinstance(payload, dict):
            voices = payload.get("voices", [])
            if isinstance(voices, list):
                return [item for item in voices if isinstance(item, dict)]
        return []

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
            raise TTSProviderError("missing_api_key", "ELEVENLABS_API_KEY não configurada no .env.")

        effective_voice = voice or self.voice_id
        if not effective_voice:
            raise TTSProviderError(
                "missing_voice_id",
                "ElevenLabs requer ELEVENLABS_VOICE_ID ou um voice_id no request.",
            )

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
            if hasattr(exc, "status_code") or hasattr(exc, "code"):
                code, message = self._classify_http_error(exc)
                raise TTSProviderError(code, message) from exc
            if "connection" in str(exc).lower() or "network" in str(exc).lower():
                raise TTSProviderError(
                    "network_error",
                    "Falha ao gerar áudio com ElevenLabs: erro de rede.",
                ) from exc
            raise TTSProviderError(
                "unknown_provider_error",
                "Falha ao gerar áudio com ElevenLabs. Verifique a chave, voice_id, modelo e conectividade.",
            ) from exc

        return TTSResult(filename=filename, file_path=file_path)

    @staticmethod
    def _classify_http_error(exc: Exception) -> tuple[str, str]:
        status_code = int(getattr(exc, "status_code", None) or getattr(exc, "code", 0) or 0)
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")  # type: ignore[attr-defined]
        except Exception:
            body = ""
        message = f"{str(exc)}\n{body}".lower()

        if any(token in message for token in ("missing_permissions", "voices_read")):
            return "forbidden_403", "ElevenLabs negou a requisição por permissão voices_read ausente."
        if any(
            token in message
            for token in (
                "invoice",
                "billing",
                "payment_required",
                "payment issue",
                "payment",
                "subscription",
                "blocked",
                "suspended",
            )
        ):
            return "unpaid_invoice_or_account_block", "ElevenLabs bloqueou a requisição por cobrança ou conta."
        if status_code == 401:
            return "unauthorized_401", "ElevenLabs API key inválida, revogada ou sem permissão."
        if status_code == 403:
            return "forbidden_403", "ElevenLabs negou a requisição por permissão insuficiente."
        if status_code in (400, 404, 422):
            return "invalid_voice_id", "ElevenLabs rejeitou o voice_id informado."
        if status_code == 429:
            return "network_error", "ElevenLabs indisponível no momento. Tente novamente."
        return "unknown_provider_error", "Falha ao listar vozes da ElevenLabs."
