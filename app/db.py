from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.history import HistoryItem, build_text_preview, normalize_created_at, row_to_history_item


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tts_history.sqlite3"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                text_preview TEXT NOT NULL,
                text_length INTEGER NOT NULL,
                language TEXT,
                voice TEXT,
                speed REAL,
                filename TEXT,
                audio_url TEXT,
                audio_format TEXT,
                error_message TEXT
            )
            """
        )
        conn.commit()


def add_history_item(
    *,
    provider: str,
    status: str,
    text: str,
    language: str | None,
    voice: str | None,
    speed: float | None,
    filename: str | None,
    audio_url: str | None,
    audio_format: str | None,
    error_message: str | None,
    created_at: str | None = None,
) -> int:
    preview = build_text_preview(text)
    text_length = len(text)
    created_value = normalize_created_at(created_at)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generation_history (
                created_at,
                provider,
                status,
                text_preview,
                text_length,
                language,
                voice,
                speed,
                filename,
                audio_url,
                audio_format,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_value,
                provider,
                status,
                preview,
                text_length,
                language,
                voice,
                speed,
                filename,
                audio_url,
                audio_format,
                error_message,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_history(limit: int = 20) -> list[HistoryItem]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                provider,
                status,
                text_preview,
                text_length,
                language,
                voice,
                speed,
                filename,
                audio_url,
                audio_format,
                error_message
            FROM generation_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_history_item(row) for row in rows]


def get_history_item(item_id: int) -> HistoryItem | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                created_at,
                provider,
                status,
                text_preview,
                text_length,
                language,
                voice,
                speed,
                filename,
                audio_url,
                audio_format,
                error_message
            FROM generation_history
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return row_to_history_item(row)


def delete_history_item(item_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM generation_history WHERE id = ?", (item_id,))
        conn.commit()
    return cursor.rowcount > 0


def delete_all_history() -> int:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM generation_history")
        conn.commit()
    return cursor.rowcount
