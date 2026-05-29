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
from app.providers.google_provider import GoogleProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider


app = FastAPI(title="tts-api-switcher")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
GENERATED_DIR = settings.generated_dir
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class GenerateAudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    provider: str = Field(pattern="^(mock|openai|google)$")
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
}


def sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return safe.strip("._") or "audio"


def build_unique_filename(prefix: str, extension: str = ".wav") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    token = uuid.uuid4().hex[:12]
    filename = f"{prefix}_{timestamp}_{token}{extension}"
    return sanitize_filename(filename)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/providers")
def list_providers() -> JSONResponse:
    providers = [
        {
            "id": "mock",
            "name": "Mock Provider",
            "enabled": True,
        },
        {
            "id": "openai",
            "name": "OpenAI TTS",
            "enabled": PROVIDERS["openai"].is_enabled(),
        },
        {
            "id": "google",
            "name": "Google Text-to-Speech",
            "enabled": PROVIDERS["google"].is_enabled(),
        },
    ]
    return JSONResponse({"providers": providers})


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
        add_history_item(
            provider=payload.provider,
            status="error",
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            filename=None,
            audio_url=None,
            audio_format=None,
            error_message="Provider inválido.",
        )
        return JSONResponse(
            status_code=400,
            content={"status": "error", "provider": payload.provider, "detail": "Provider inválido."},
        )

    if not provider.is_enabled():
        detail = "Provider desativado ou não configurado."
        if payload.provider == "openai":
            detail = "OPENAI_API_KEY não configurada no .env."
        elif payload.provider == "google":
            detail = "Google TTS desativado ou sem credenciais."
        add_history_item(
            provider=payload.provider,
            status="error",
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            filename=None,
            audio_url=None,
            audio_format=None,
            error_message=detail,
        )
        return JSONResponse(
            status_code=400,
            content={"status": "error", "provider": payload.provider, "detail": detail},
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
        add_history_item(
            provider=payload.provider,
            status="error",
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            filename=None,
            audio_url=None,
            audio_format=None,
            error_message=str(exc),
        )
        return JSONResponse(
            status_code=400,
            content={"status": "error", "provider": payload.provider, "detail": str(exc)},
        )
    except Exception:
        add_history_item(
            provider=payload.provider,
            status="error",
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            filename=None,
            audio_url=None,
            audio_format=None,
            error_message="Falha ao gerar áudio.",
        )
        return JSONResponse(
            status_code=500,
            content={"status": "error", "provider": payload.provider, "detail": "Falha ao gerar áudio."},
        )


app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
