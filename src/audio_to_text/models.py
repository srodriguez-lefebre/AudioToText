from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TranscriptionResult:
    """Holds the important outputs of a transcription run."""

    input_path: Path
    output_path: Path
    raw_text: str
    final_text: str
