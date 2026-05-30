from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TTSResult:
    filename: str
    file_path: Path


class TTSProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TTSProvider:
    id: str = ""
    name: str = ""
    default_extension: str = ".wav"
    supports_voice_list: bool = False

    def generate(
        self,
        text: str,
        language: str,
        voice: str,
        speed: float,
        output_dir: Path,
        filename: str | None = None,
    ) -> TTSResult:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return True

    def disabled_reason(self) -> str | None:
        return None

    def list_voices(self) -> list[dict[str, Any]]:
        return []


def normalize_voice(
    voice_id: str,
    *,
    name: str,
    language: str = "",
    gender: str = "",
    description: str = "",
    default: bool = False,
) -> dict[str, Any]:
    return {
        "id": voice_id,
        "name": name,
        "language": language,
        "gender": gender,
        "description": description,
        "default": default,
    }
