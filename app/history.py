from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


TEXT_PREVIEW_LIMIT = 300


@dataclass(slots=True)
class HistoryItem:
    id: int
    created_at: str
    provider: str
    status: str
    text_preview: str
    text_length: int
    language: str | None
    voice: str | None
    speed: float | None
    filename: str | None
    audio_url: str | None
    audio_format: str | None
    error_message: str | None


def build_text_preview(text: str, limit: int = TEXT_PREVIEW_LIMIT) -> str:
    preview = text[:limit]
    return preview


def normalize_created_at(value: str | None = None) -> str:
    return value or datetime.utcnow().isoformat(timespec="seconds") + "Z"


def row_to_history_item(row: Any) -> HistoryItem:
    return HistoryItem(
        id=row["id"],
        created_at=row["created_at"],
        provider=row["provider"],
        status=row["status"],
        text_preview=row["text_preview"],
        text_length=row["text_length"],
        language=row["language"],
        voice=row["voice"],
        speed=row["speed"],
        filename=row["filename"],
        audio_url=row["audio_url"],
        audio_format=row["audio_format"],
        error_message=row["error_message"],
    )


def history_item_to_dict(item: HistoryItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "created_at": item.created_at,
        "provider": item.provider,
        "status": item.status,
        "text_preview": item.text_preview,
        "text_length": item.text_length,
        "language": item.language,
        "voice": item.voice,
        "speed": item.speed,
        "filename": item.filename,
        "audio_url": item.audio_url,
        "audio_format": item.audio_format,
        "error_message": item.error_message,
    }
