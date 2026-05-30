from __future__ import annotations

import re
import uuid
from pathlib import Path

from datetime import datetime

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.db import add_history_item, delete_all_history, delete_history_item, get_history_item, init_db, list_history
from app.history import history_item_to_dict
from app.providers.azure_provider import AzureProvider
from app.providers.elevenlabs_provider import ElevenLabsProvider
from app.providers.google_provider import GoogleProvider
from app.providers.mock_provider import MockProvider
from app.providers.polly_provider import PollyProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.base import TTSProviderError


app = FastAPI(title="tts-api-switcher")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
GENERATED_DIR = settings.generated_dir
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class GenerateAudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    provider: str = Field(min_length=1, max_length=32)
    language: str = Field(default="pt-BR", min_length=2, max_length=20)
    voice: str = Field(default="", max_length=100)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


PROVIDERS = {
    "mock": MockProvider(),
    "openai": OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_tts_model,
        voice=settings.openai_tts_voice,
        audio_format=settings.openai_tts_format,
    ),
    "google": GoogleProvider(
        enabled=settings.google_tts_enabled,
        credentials_path=settings.google_application_credentials,
        voice=settings.google_tts_voice,
        language_code=settings.google_tts_language_code,
        audio_encoding=settings.google_tts_audio_encoding,
    ),
    "elevenlabs": ElevenLabsProvider(
        api_key=settings.elevenlabs_api_key,
        model=settings.elevenlabs_model,
        voice_id=settings.elevenlabs_voice_id,
        output_format=settings.elevenlabs_output_format,
    ),
    "azure": AzureProvider(
        key=settings.azure_speech_key,
        region=settings.azure_speech_region,
        endpoint=settings.azure_speech_endpoint,
        voice=settings.azure_speech_voice,
        output_format=settings.azure_speech_output_format,
    ),
    "polly": PollyProvider(
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        default_region=settings.aws_default_region,
        voice_id=settings.aws_polly_voice_id,
        engine=settings.aws_polly_engine,
        output_format=settings.aws_polly_output_format,
    ),
}

PROVIDER_ORDER = ["mock", "openai", "google", "elevenlabs", "azure", "polly"]


def sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return safe.strip("._") or "audio"


def build_unique_filename(prefix: str, extension: str = ".wav") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    token = uuid.uuid4().hex[:12]
    filename = f"{prefix}_{timestamp}_{token}{extension}"
    return sanitize_filename(filename)


def check_directory_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".healthcheck-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def check_sqlite_accessible() -> bool:
    try:
        import sqlite3

        db_path = DATA_DIR / "tts_history.sqlite3"
        if not db_path.exists():
            return False
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def provider_list_item(provider_id: str) -> dict[str, object]:
    provider = PROVIDERS[provider_id]
    disabled_reason = provider.disabled_reason()
    return {
        "id": provider.id,
        "name": provider.name,
        "enabled": provider.is_enabled(),
        "disabled_reason": disabled_reason,
        "supports_voice_list": provider.supports_voice_list,
    }


def error_payload(provider_id: str, error_code: str, error_message: str) -> dict[str, object]:
    return {
        "status": "error",
        "provider": provider_id,
        "error_code": error_code,
        "error": error_message,
        "detail": error_message,
    }


def add_error_history(
    *,
    provider: str,
    text: str,
    language: str,
    voice: str,
    speed: float,
    error_message: str,
) -> None:
    add_history_item(
        provider=provider,
        status="error",
        text=text,
        language=language,
        voice=voice,
        speed=speed,
        filename=None,
        audio_url=None,
        audio_format=None,
        error_message=error_message,
    )


def provider_voice_response(provider_id: str) -> JSONResponse:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        return JSONResponse(status_code=404, content={"detail": "Provider não encontrado."})

    enabled = provider.is_enabled()
    voices: list[dict[str, object]] = []
    message: str | None = None

    if provider_id == "elevenlabs" and not enabled:
        message = provider.disabled_reason() or "Provider desabilitado. Configure as credenciais no .env."
        return JSONResponse(
            {
                "provider": provider.id,
                "enabled": False,
                "voices": [],
                "message": message,
            }
        )

    try:
        voices = provider.list_voices()
    except TTSProviderError as exc:
        message = exc.message
        voices = []
        return JSONResponse(
            {
                "provider": provider.id,
                "enabled": enabled,
                "voices": voices,
                "error_code": exc.code,
                "error": message,
                "message": message,
            },
            status_code=400,
        )
    except RuntimeError as exc:
        message = str(exc)
        voices = []
    except Exception:
        message = "Falha ao listar vozes. Tente novamente ou use o campo manual."
        voices = []

    if not enabled and message is None:
        message = provider.disabled_reason() or "Provider desabilitado. Configure as credenciais no .env."

    content: dict[str, object] = {
        "provider": provider.id,
        "enabled": enabled,
        "voices": voices,
    }
    if message:
        content["message"] = message
        content["error_code"] = "unknown_provider_error"
        content["error"] = message
    return JSONResponse(content)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> JSONResponse:
    generated_ok = check_directory_writable(GENERATED_DIR)
    data_ok = check_directory_writable(DATA_DIR)
    db_ok = check_sqlite_accessible()

    response = {
        "status": "ok" if generated_ok and data_ok and db_ok else "degraded",
        "app": "tts-api-switcher",
        "generated_dir": "ok" if generated_ok else "degraded",
        "data_dir": "ok" if data_ok else "degraded",
        "history_db": "ok" if db_ok else "degraded",
    }
    status_code = 200 if response["status"] == "ok" else 503
    if status_code != 200:
        response["message"] = "Um ou mais componentes essenciais não estão prontos."
    return JSONResponse(response, status_code=status_code)


@app.get("/api/providers")
def list_providers() -> JSONResponse:
    providers = [provider_list_item(provider_id) for provider_id in PROVIDER_ORDER]
    return JSONResponse({"providers": providers})


@app.get("/api/providers/{provider_id}/voices")
def list_provider_voices(provider_id: str) -> JSONResponse:
    return provider_voice_response(provider_id)


@app.get("/api/history")
def api_list_history(limit: int = Query(default=20, ge=1, le=100)) -> JSONResponse:
    items = [history_item_to_dict(item) for item in list_history(limit=limit)]
    return JSONResponse({"items": items})


@app.get("/api/history/{item_id}")
def api_get_history_item(item_id: int) -> JSONResponse:
    item = get_history_item(item_id)
    if item is None:
        return JSONResponse(status_code=404, content={"detail": "Item de histórico não encontrado."})
    return JSONResponse(history_item_to_dict(item))


@app.delete("/api/history/{item_id}")
def api_delete_history_item(item_id: int) -> JSONResponse:
    deleted = delete_history_item(item_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"detail": "Item de histórico não encontrado."})
    return JSONResponse({"status": "ok", "deleted": True, "file_preserved": True})


@app.delete("/api/history")
def api_delete_all_history() -> JSONResponse:
    deleted_count = delete_all_history()
    return JSONResponse({"status": "ok", "deleted": deleted_count})


@app.post("/api/generate-audio")
def generate_audio(payload: GenerateAudioRequest) -> JSONResponse:
    provider = PROVIDERS.get(payload.provider)
    if provider is None:
        error_message = "Provider inválido."
        add_error_history(
            provider=payload.provider,
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            error_message=error_message,
        )
        return JSONResponse(
            status_code=400,
            content=error_payload(payload.provider, "unknown_provider_error", error_message),
        )

    if not provider.is_enabled():
        detail = provider.disabled_reason() or "Provider desativado ou não configurado."
        add_error_history(
            provider=payload.provider,
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            error_message=detail,
        )
        return JSONResponse(
            status_code=400,
            content=error_payload(payload.provider, "provider_disabled", detail),
        )

    try:
        safe_prefix = sanitize_filename(payload.provider)
        unique_filename = build_unique_filename(safe_prefix, extension=provider.default_extension)
        result = provider.generate(
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            output_dir=GENERATED_DIR,
            filename=unique_filename,
        )

        add_history_item(
            provider=payload.provider,
            status="ok",
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            filename=result.filename,
            audio_url=f"/generated/{result.filename}",
            audio_format=result.file_path.suffix.lstrip(".") or None,
            error_message=None,
        )

        return JSONResponse(
            {
                "status": "ok",
                "provider": payload.provider,
                "audio_url": f"/generated/{result.filename}",
                "filename": result.filename,
            }
        )
    except RuntimeError as exc:
        error_message = str(exc)
        add_error_history(
            provider=payload.provider,
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            error_message=error_message,
        )
        return JSONResponse(
            status_code=400,
            content=error_payload(payload.provider, "unknown_provider_error", error_message),
        )
    except TTSProviderError as exc:
        add_error_history(
            provider=payload.provider,
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            error_message=exc.message,
        )
        return JSONResponse(
            status_code=400,
            content=error_payload(payload.provider, exc.code, exc.message),
        )
    except Exception:
        error_message = "Falha ao gerar áudio."
        add_error_history(
            provider=payload.provider,
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            error_message=error_message,
        )
        return JSONResponse(
            status_code=500,
            content=error_payload(payload.provider, "unknown_provider_error", error_message),
        )


app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
