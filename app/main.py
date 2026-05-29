from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
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
    ),
    "google": GoogleProvider(
        enabled=settings.google_tts_enabled,
        credentials_path=settings.google_application_credentials,
        voice=settings.google_tts_voice,
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
            "enabled": bool(settings.openai_api_key),
        },
        {
            "id": "google",
            "name": "Google Text-to-Speech",
            "enabled": bool(settings.google_tts_enabled and settings.google_application_credentials),
        },
    ]
    return JSONResponse({"providers": providers})


@app.post("/api/generate-audio")
def generate_audio(payload: GenerateAudioRequest) -> JSONResponse:
    provider = PROVIDERS.get(payload.provider)
    if provider is None:
        raise HTTPException(status_code=400, detail={"error": "Provider inválido."})

    try:
        safe_prefix = sanitize_filename(payload.provider)
        unique_filename = build_unique_filename(safe_prefix)
        result = provider.generate(
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            output_dir=GENERATED_DIR,
            filename=unique_filename,
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
        raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "Falha ao gerar áudio."}) from exc


app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
