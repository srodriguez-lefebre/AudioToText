from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from audio_to_text.config.settings import (
    Settings,
    clear_settings_cache,
    get_settings,
    resolve_env_file,
)
from audio_to_text.logging_config import configure_logging
from audio_to_text.models import TranscriptionResult
from audio_to_text.openai_client import create_client
from audio_to_text.transcription_service import TranscriptionService

app = typer.Typer(
    no_args_is_help=True,
)


def load_runtime_settings() -> Settings:
    """Loads settings for the current CLI execution context."""

    return get_settings(resolve_env_file())


def run_transcription(
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
    """Runs a transcription using the configured service."""

    service = TranscriptionService(settings=load_runtime_settings(), client_factory=create_client)
    return service.transcribe(
        file_reference,
        input_dir=input_dir_override,
        output_dir=output_dir_override,
        output_path=output_path,
        skip_cleanup=skip_cleanup,
        transcription_model=transcription_model,
        cleanup_model=cleanup_model,
        api_key=api_key_override,
    )


@app.callback(invoke_without_command=True)
def main(
    file_reference: Annotated[
        str,
        typer.Argument(help="Filename, stem, or full path to the audio file."),
    ],
    input_dir: Annotated[
        Path | None,
        typer.Option(
            "--input-dir",
            "-i",
            help="Directory to search when using a filename or stem.",
        ),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Directory where the .txt file will be saved.",
        ),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Explicit output file path. Overrides --output-dir.",
        ),
    ] = None,
    skip_cleanup: Annotated[
        bool,
        typer.Option(
            "--skip-cleanup",
            help="Save the raw transcript without restructuring it.",
        ),
    ] = False,
    transcription_model: Annotated[
        str | None,
        typer.Option(
            "--transcription-model",
            help="Override the transcription model for this run.",
        ),
    ] = None,
    cleanup_model: Annotated[
        str | None,
        typer.Option(
            "--cleanup-model",
            help="Override the cleanup model for this run.",
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help="OpenAI API key override for this run.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Transcribe audio from a short command such as `text note`."""

    clear_settings_cache()
    configure_logging(load_runtime_settings(), verbose=verbose)

    try:
        result = run_transcription(
            file_reference=file_reference,
            input_dir_override=input_dir,
            output_dir_override=output_dir,
            output_path=output_path,
            skip_cleanup=skip_cleanup,
            transcription_model=transcription_model,
            cleanup_model=cleanup_model,
            api_key_override=api_key,
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.error(str(exc))
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        logger.exception("Unexpected error while transcribing audio")
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Saved transcription to {result.output_path}",
        fg=typer.colors.GREEN,
        bold=True,
    )
