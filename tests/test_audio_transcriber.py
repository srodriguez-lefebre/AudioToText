import tempfile
import unittest
from pathlib import Path

from audio_transcriber import (
    build_output_path,
    extract_transcript_text,
    write_transcript,
)


class TestExtractTranscriptText(unittest.TestCase):
    def test_uses_text_field_when_present(self) -> None:
        payload = {"text": "hola mundo"}
        self.assertEqual(extract_transcript_text(payload), "hola mundo")

    def test_falls_back_to_segments_when_text_missing(self) -> None:
        payload = {
            "segments": [
                {"speaker": "S1", "text": "Hola"},
                {"speaker": "S2", "text": "Como estas?"},
            ]
        }
        self.assertEqual(
            extract_transcript_text(payload),
            "S1: Hola\nS2: Como estas?",
        )

    def test_raises_when_payload_has_no_text(self) -> None:
        with self.assertRaises(ValueError):
            extract_transcript_text({})


class TestOutputPath(unittest.TestCase):
    def test_builds_default_txt_path_in_output_dir(self) -> None:
        audio_path = Path("audio_inputs/nota.mp3")
        output_dir = Path("transcriptions")
        self.assertEqual(
            build_output_path(audio_path, None, output_dir),
            Path("transcriptions/nota.txt"),
        )

    def test_respects_explicit_output_file(self) -> None:
        audio_path = Path("audio_inputs/nota.mp3")
        explicit = Path("custom/salida.txt")
        self.assertEqual(
            build_output_path(audio_path, explicit, Path("transcriptions")),
            explicit,
        )


class TestWriteTranscript(unittest.TestCase):
    def test_writes_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "out.txt"
            write_transcript(output_path, "Linea 1\nLinea 2")
            self.assertEqual(output_path.read_text(encoding="utf-8"), "Linea 1\nLinea 2")


if __name__ == "__main__":
    unittest.main()
