from pathlib import Path
from unittest.mock import ANY

import pytest

from audio_to_text.config.settings import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, Settings
from audio_to_text.models import TranscriptionResult
from audio_to_text.transcription_service import (
    TranscriptionService,
    build_output_path,
    extract_transcript_text,
    resolve_audio_path,
)


def test_extract_transcript_text_prefers_top_level_text() -> None:
    payload = {"text": "hola mundo"}

    assert extract_transcript_text(payload) == "hola mundo"


def test_extract_transcript_text_uses_segments_when_text_is_missing() -> None:
    payload = {
        "segments": [
            {"speaker": "S1", "text": "Hola"},
            {"speaker": "S2", "text": "Como estas?"},
        ]
    }

    assert extract_transcript_text(payload) == "S1: Hola\nS2: Como estas?"


def test_build_output_path_uses_audio_stem_in_output_directory() -> None:
    audio_path = Path("audio_inputs/nota.mp3")

    assert build_output_path(audio_path, None, Path("transcriptions")) == Path(
        "transcriptions/nota.txt"
    )


def test_settings_defaults_are_runtime_relative_paths() -> None:
    settings = Settings()

    assert settings.INPUT_DIR == DEFAULT_INPUT_DIR
    assert settings.OUTPUT_DIR == DEFAULT_OUTPUT_DIR


def test_resolve_audio_path_finds_exact_file_in_configured_input_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    input_dir.mkdir()
    expected_path = input_dir / "nota-reunion.mp3"
    expected_path.write_bytes(b"fake-audio")

    assert resolve_audio_path("nota-reunion.mp3", input_dir) == expected_path


def test_resolve_audio_path_finds_unique_stem_when_extension_is_omitted(tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    input_dir.mkdir()
    expected_path = input_dir / "idea.m4a"
    expected_path.write_bytes(b"fake-audio")

    assert resolve_audio_path("idea", input_dir) == expected_path


def test_resolve_audio_path_raises_when_stem_matches_multiple_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    input_dir.mkdir()
    (input_dir / "nota.mp3").write_bytes(b"fake-audio")
    (input_dir / "nota.wav").write_bytes(b"fake-audio")

    with pytest.raises(ValueError, match="Multiple audio files match"):
        resolve_audio_path("nota", input_dir)


def test_service_transcribes_cleans_and_writes_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    output_dir = tmp_path / "transcriptions"
    input_dir.mkdir()
    output_dir.mkdir()
    audio_path = input_dir / "daily-note.mp3"
    audio_path.write_bytes(b"fake-audio")

    settings = Settings(
        OPENAI_API_KEY="test-key",
        INPUT_DIR=input_dir,
        OUTPUT_DIR=output_dir,
        TRANSCRIPTION_MODEL="test-transcribe-model",
        CLEANUP_MODEL="test-cleanup-model",
    )

    transcription_calls: list[dict[str, object]] = []
    cleanup_calls: list[dict[str, object]] = []

    class FakeTranscriptionsApi:
        @staticmethod
        def create(**kwargs: object) -> dict[str, str]:
            transcription_calls.append(kwargs)
            return {"text": "texto crudo"}

    class FakeAudioApi:
        transcriptions = FakeTranscriptionsApi()

    class FakeChatCompletionsApi:
        @staticmethod
        def create(**kwargs: object) -> dict[str, list[dict[str, dict[str, str]]]]:
            cleanup_calls.append(kwargs)
            return {"choices": [{"message": {"content": "Texto limpio"}}]}

    class FakeChatApi:
        completions = FakeChatCompletionsApi()

    class FakeClient:
        audio = FakeAudioApi()
        chat = FakeChatApi()

    service = TranscriptionService(settings=settings, client_factory=lambda _: FakeClient())

    result = service.transcribe("daily-note")

    assert isinstance(result, TranscriptionResult)
    assert result.input_path == audio_path
    assert result.output_path == output_dir / "daily-note.txt"
    assert result.raw_text == "texto crudo"
    assert result.final_text == "Texto limpio"
    assert result.output_path.read_text(encoding="utf-8") == "Texto limpio"
    assert transcription_calls == [
        {
            "model": "test-transcribe-model",
            "file": ANY,
            "response_format": "json",
        }
    ]
    assert cleanup_calls == [
        {
            "model": "test-cleanup-model",
            "temperature": 0,
            "messages": ANY,
        }
    ]


def test_service_can_skip_cleanup(tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    output_dir = tmp_path / "transcriptions"
    input_dir.mkdir()
    output_dir.mkdir()
    audio_path = input_dir / "brainstorm.wav"
    audio_path.write_bytes(b"fake-audio")

    settings = Settings(
        OPENAI_API_KEY="test-key",
        INPUT_DIR=input_dir,
        OUTPUT_DIR=output_dir,
    )

    class FakeTranscriptionsApi:
        @staticmethod
        def create(**_: object) -> dict[str, str]:
            return {"text": "texto crudo"}

    class FakeAudioApi:
        transcriptions = FakeTranscriptionsApi()

    class FakeChatCompletionsApi:
        @staticmethod
        def create(**_: object) -> dict[str, object]:
            raise AssertionError("Cleanup should not be called when skip_cleanup is enabled")

    class FakeChatApi:
        completions = FakeChatCompletionsApi()

    class FakeClient:
        audio = FakeAudioApi()
        chat = FakeChatApi()

    service = TranscriptionService(settings=settings, client_factory=lambda _: FakeClient())

    result = service.transcribe("brainstorm", skip_cleanup=True)

    assert result.input_path == audio_path
    assert result.final_text == "texto crudo"
    assert result.output_path.read_text(encoding="utf-8") == "texto crudo"
