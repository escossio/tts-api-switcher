from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    app_host: str = "127.0.0.1"
    app_port: int = 8090
    generated_dir: Path = Path("app/generated")

    openai_api_key: str = ""
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    openai_tts_format: str = "mp3"

    google_tts_enabled: bool = False
    google_application_credentials: str = ""
    google_tts_voice: str = "pt-BR-Neural2-B"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    import os

    return Settings(
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8090")),
        generated_dir=Path(os.getenv("GENERATED_DIR", "app/generated")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        openai_tts_format=os.getenv("OPENAI_TTS_FORMAT", "mp3"),
        google_tts_enabled=os.getenv("GOOGLE_TTS_ENABLED", "false").lower() == "true",
        google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        google_tts_voice=os.getenv("GOOGLE_TTS_VOICE", "pt-BR-Neural2-B"),
    )


settings = get_settings()
