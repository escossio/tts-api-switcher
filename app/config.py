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
    google_tts_language_code: str = "pt-BR"
    google_tts_audio_encoding: str = "MP3"

    elevenlabs_api_key: str = ""
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_voice_id: str = ""
    elevenlabs_output_format: str = "mp3_44100_128"

    azure_speech_key: str = ""
    azure_speech_region: str = ""
    azure_speech_endpoint: str = ""
    azure_speech_voice: str = "pt-BR-FranciscaNeural"
    azure_speech_output_format: str = "audio-16khz-128kbitrate-mono-mp3"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"
    aws_polly_voice_id: str = "Camila"
    aws_polly_engine: str = "neural"
    aws_polly_output_format: str = "mp3"


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
        google_tts_language_code=os.getenv("GOOGLE_TTS_LANGUAGE_CODE", "pt-BR"),
        google_tts_audio_encoding=os.getenv("GOOGLE_TTS_AUDIO_ENCODING", "MP3"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        elevenlabs_model=os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", ""),
        elevenlabs_output_format=os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
        azure_speech_key=os.getenv("AZURE_SPEECH_KEY", ""),
        azure_speech_region=os.getenv("AZURE_SPEECH_REGION", ""),
        azure_speech_endpoint=os.getenv("AZURE_SPEECH_ENDPOINT", ""),
        azure_speech_voice=os.getenv("AZURE_SPEECH_VOICE", "pt-BR-FranciscaNeural"),
        azure_speech_output_format=os.getenv(
            "AZURE_SPEECH_OUTPUT_FORMAT", "audio-16khz-128kbitrate-mono-mp3"
        ),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        aws_default_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_polly_voice_id=os.getenv("AWS_POLLY_VOICE_ID", "Camila"),
        aws_polly_engine=os.getenv("AWS_POLLY_ENGINE", "neural"),
        aws_polly_output_format=os.getenv("AWS_POLLY_OUTPUT_FORMAT", "mp3"),
    )


settings = get_settings()
