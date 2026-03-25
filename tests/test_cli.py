from pathlib import Path

from typer.testing import CliRunner

from audio_to_text.cli import app
from audio_to_text.models import TranscriptionResult

runner = CliRunner()


def test_cli_runs_with_short_command_and_default_dirs(monkeypatch, tmp_path: Path) -> None:
    input_dir = tmp_path / "audio_inputs"
    output_dir = tmp_path / "transcriptions"
    input_dir.mkdir()
    output_dir.mkdir()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("INPUT_DIR", str(input_dir))
    monkeypatch.setenv("OUTPUT_DIR", str(output_dir))

    captured: dict[str, object] = {}

    def fake_run_transcription(
        *,
        file_reference: str,
        input_dir_override: Path | None,
        output_dir_override: Path | None,
        output_path: Path | None,
        skip_cleanup: bool,
        transcription_model: str | None,
        cleanup_model: str | None,
        api_key_override: str | None,
    ) -> TranscriptionResult:
        captured["file_reference"] = file_reference
        captured["input_dir_override"] = input_dir_override
        captured["output_dir_override"] = output_dir_override
        captured["output_path"] = output_path
        captured["skip_cleanup"] = skip_cleanup
        captured["transcription_model"] = transcription_model
        captured["cleanup_model"] = cleanup_model
        captured["api_key_override"] = api_key_override

        return TranscriptionResult(
            input_path=input_dir / "note.mp3",
            output_path=output_dir / "note.txt",
            raw_text="texto crudo",
            final_text="Texto limpio",
        )

    monkeypatch.setattr("audio_to_text.cli.run_transcription", fake_run_transcription)
    monkeypatch.setattr("audio_to_text.cli.resolve_env_file", lambda: tmp_path / ".env")

    result = runner.invoke(app, ["note"])

    assert result.exit_code == 0
    assert captured == {
        "file_reference": "note",
        "input_dir_override": None,
        "output_dir_override": None,
        "output_path": None,
        "skip_cleanup": False,
        "transcription_model": None,
        "cleanup_model": None,
        "api_key_override": None,
    }
    assert "note.txt" in result.stdout


def test_cli_uses_settings_loaded_from_resolved_env_file(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run_transcription(
        *,
        file_reference: str,
        input_dir_override: Path | None,
        output_dir_override: Path | None,
        output_path: Path | None,
        skip_cleanup: bool,
        transcription_model: str | None,
        cleanup_model: str | None,
        api_key_override: str | None,
    ) -> TranscriptionResult:
        captured["file_reference"] = file_reference

        return TranscriptionResult(
            input_path=tmp_path / "audio_inputs" / "note.mp3",
            output_path=tmp_path / "transcriptions" / "note.txt",
            raw_text="texto crudo",
            final_text="Texto limpio",
        )

    monkeypatch.setattr("audio_to_text.cli.run_transcription", fake_run_transcription)
    monkeypatch.setattr("audio_to_text.cli.resolve_env_file", lambda: env_file)

    result = runner.invoke(app, ["note"])

    assert result.exit_code == 0
    assert captured["file_reference"] == "note"
