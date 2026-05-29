from dataclasses import dataclass
from pathlib import Path


@dataclass
class TTSResult:
    filename: str
    file_path: Path


class TTSProvider:
    id: str = ""
    name: str = ""
    default_extension: str = ".wav"

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
