from collections.abc import Mapping
from pathlib import Path

from loguru import logger

from audio_to_text.config.settings import Settings
from audio_to_text.interfaces import ClientFactory, OpenAIClientProtocol
from audio_to_text.models import TranscriptionResult


def build_output_path(
    audio_path: Path,
    output_path: Path | None,
    output_dir: Path,
) -> Path:
    """Builds the final text output path."""

    if output_path is not None:
        return output_path

    return output_dir / f"{audio_path.stem}.txt"


def resolve_audio_path(reference: str, input_dir: Path) -> Path:
    """Resolves an audio reference from a direct path or the configured input directory."""

    candidate_path = Path(reference).expanduser()
    if candidate_path.is_absolute() or candidate_path.parent != Path("."):
        if candidate_path.exists() and candidate_path.is_file():
            return candidate_path
        raise FileNotFoundError(f"Audio file not found: {candidate_path}")

    exact_match = input_dir / reference
    if exact_match.exists() and exact_match.is_file():
        return exact_match

    if Path(reference).suffix:
        raise FileNotFoundError(f"Audio file not found: {exact_match}")

    matches = sorted(path for path in input_dir.glob(f"{reference}.*") if path.is_file())
    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise ValueError(
            f"Multiple audio files match '{reference}' in {input_dir}. Use the exact filename."
        )

    raise FileNotFoundError(f"Audio file not found: {input_dir / reference}")


def write_transcript(output_path: Path, text: str) -> None:
    """Writes the transcription to disk as UTF-8 text."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _value_from_payload(payload: object, key: str) -> object | None:
    if isinstance(payload, Mapping):
        return payload.get(key)

    return getattr(payload, key, None)


def extract_transcript_text(payload: object) -> str:
    """Extracts plain text from a transcription response payload."""

    text = _value_from_payload(payload, "text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    segments = _value_from_payload(payload, "segments")
    if isinstance(segments, list):
        lines: list[str] = []
        for segment in segments:
            if not isinstance(segment, Mapping):
                continue

            segment_text = segment.get("text")
            if not isinstance(segment_text, str) or not segment_text.strip():
                continue

            speaker = segment.get("speaker")
            if isinstance(speaker, str) and speaker.strip():
                lines.append(f"{speaker.strip()}: {segment_text.strip()}")
                continue

            lines.append(segment_text.strip())

        if lines:
            return "\n".join(lines)

    raise ValueError("No transcript text found in transcription response")


def _extract_chat_content(response: object) -> str:
    choices = _value_from_payload(response, "choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("No cleanup completion choices returned")

    message = _value_from_payload(choices[0], "message")
    content = _value_from_payload(message, "content")

    if isinstance(content, str) and content.strip():
        return content.strip()

    raise ValueError("No cleanup text found in completion response")


class TranscriptionService:
    """Coordinates input resolution, OpenAI calls, cleanup, and file output."""

    def __init__(self, settings: Settings, client_factory: ClientFactory) -> None:
        self._settings = settings
        self._client_factory = client_factory

    def transcribe(
        self,
        file_reference: str,
        *,
        input_dir: Path | None = None,
        output_dir: Path | None = None,
        output_path: Path | None = None,
        skip_cleanup: bool = False,
        transcription_model: str | None = None,
        cleanup_model: str | None = None,
        api_key: str | None = None,
    ) -> TranscriptionResult:
        """Transcribes an audio file and writes the final text output."""

        resolved_input_dir = input_dir or self._settings.INPUT_DIR
        resolved_output_dir = output_dir or self._settings.OUTPUT_DIR
        resolved_api_key = api_key or self._resolve_api_key()
        resolved_transcription_model = transcription_model or self._settings.TRANSCRIPTION_MODEL
        resolved_cleanup_model = cleanup_model or self._settings.CLEANUP_MODEL

        try:
            audio_path = resolve_audio_path(file_reference, resolved_input_dir)
            final_output_path = build_output_path(audio_path, output_path, resolved_output_dir)

            logger.info("Resolved input file: {path}", path=audio_path)
            client = self._client_factory(resolved_api_key)

            raw_text = self._transcribe_audio_file(
                client=client,
                audio_path=audio_path,
                model=resolved_transcription_model,
            )
            final_text = (
                raw_text
                if skip_cleanup
                else self._cleanup_transcript(
                    client=client,
                    raw_text=raw_text,
                    model=resolved_cleanup_model,
                )
            )

            write_transcript(final_output_path, final_text)
            logger.success("Saved transcription to {path}", path=final_output_path)

            return TranscriptionResult(
                input_path=audio_path,
                output_path=final_output_path,
                raw_text=raw_text,
                final_text=final_text,
            )
        except Exception as exc:
            logger.error(
                "Transcription failed for {reference}: {exc}",
                reference=file_reference,
                exc=exc,
            )
            raise

    def _resolve_api_key(self) -> str:
        if self._settings.OPENAI_API_KEY is None:
            raise ValueError("Missing API key. Set OPENAI_API_KEY or pass --api-key.")

        return self._settings.OPENAI_API_KEY.get_secret_value()

    def _transcribe_audio_file(
        self,
        *,
        client: OpenAIClientProtocol,
        audio_path: Path,
        model: str,
    ) -> str:
        logger.info("Uploading audio to OpenAI with model {model}", model=model)
        logger.info("Waiting for transcription response")

        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="json",
            )

        logger.info("Received transcription response")
        return extract_transcript_text(response)

    def _cleanup_transcript(
        self,
        *,
        client: OpenAIClientProtocol,
        raw_text: str,
        model: str,
    ) -> str:
        logger.info("Cleaning transcript text with model {model}", model=model)
        logger.info("Waiting for cleanup response")

        completion = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Restructura esta transcripcion a texto claro y legible en espanol. "
                        "Corrige puntuacion y saltos de linea, sin inventar contenido nuevo."
                    ),
                },
                {"role": "user", "content": raw_text},
            ],
        )

        logger.info("Received cleanup response")
        return _extract_chat_content(completion)
