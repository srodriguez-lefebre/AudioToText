#!/usr/bin/env python3
"""CLI utility to transcribe an audio file and save a cleaned text file."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Mapping

DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-transcribe"
DEFAULT_CLEANUP_MODEL = "gpt-4.1-mini"


def build_output_path(
    audio_path: Path,
    output_path: Path | None,
    output_dir: Path,
) -> Path:
    if output_path is not None:
        return output_path
    return output_dir / f"{audio_path.stem}.txt"


def _value_from_payload(payload: Any, key: str) -> Any:
    if isinstance(payload, Mapping):
        return payload.get(key)
    return getattr(payload, key, None)


def extract_transcript_text(payload: Any) -> str:
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
            else:
                lines.append(segment_text.strip())
        if lines:
            return "\n".join(lines)

    raise ValueError("No transcript text found in transcription response")


def write_transcript(output_path: Path, text: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _to_dict(payload: Any) -> Any:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    if isinstance(payload, Mapping):
        return payload
    return payload


def create_client(api_key: str) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - exercised in runtime only
        raise RuntimeError(
            "Missing dependency 'openai'. Install with: python3 -m pip install -r requirements.txt"
        ) from exc

    return OpenAI(api_key=api_key)


def transcribe_audio_file(client: Any, audio_path: Path, model: str) -> str:
    with audio_path.open("rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="json",
        )
    return extract_transcript_text(_to_dict(response))


def _extract_chat_content(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not choices and isinstance(response, Mapping):
        choices = response.get("choices")

    if not isinstance(choices, list) or not choices:
        raise ValueError("No cleanup completion choices returned")

    message = getattr(choices[0], "message", None)
    if message is None and isinstance(choices[0], Mapping):
        message = choices[0].get("message")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, Mapping):
        content = message.get("content")

    if isinstance(content, str) and content.strip():
        return content.strip()
    raise ValueError("No cleanup text found in completion response")


def restructure_transcript(client: Any, raw_text: str, model: str) -> str:
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
    return _extract_chat_content(completion)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe un archivo de audio y guarda la transcripcion en .txt"
    )
    parser.add_argument("--input", required=True, help="Ruta del archivo de audio")
    parser.add_argument(
        "--output",
        help="Ruta del .txt de salida (si no se define se usa --output-dir)",
    )
    parser.add_argument(
        "--output-dir",
        default="transcriptions",
        help="Carpeta de salida por defecto para el .txt",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="API key (si no se define usa OPENAI_API_KEY del entorno)",
    )
    parser.add_argument(
        "--transcription-model",
        default=DEFAULT_TRANSCRIPTION_MODEL,
        help=f"Modelo de transcripcion (default: {DEFAULT_TRANSCRIPTION_MODEL})",
    )
    parser.add_argument(
        "--cleanup-model",
        default=DEFAULT_CLEANUP_MODEL,
        help=f"Modelo para reestructurar texto (default: {DEFAULT_CLEANUP_MODEL})",
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Guardar la transcripcion cruda sin reestructurar",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audio_path = Path(args.input)
    if not audio_path.exists() or not audio_path.is_file():
        print(f"Archivo de audio no encontrado: {audio_path}", file=sys.stderr)
        return 1

    if not args.api_key:
        print(
            "Falta API key. Defini OPENAI_API_KEY o usa --api-key.",
            file=sys.stderr,
        )
        return 1

    output_path = build_output_path(
        audio_path=audio_path,
        output_path=Path(args.output) if args.output else None,
        output_dir=Path(args.output_dir),
    )

    try:
        client = create_client(args.api_key)
        raw_text = transcribe_audio_file(
            client=client,
            audio_path=audio_path,
            model=args.transcription_model,
        )
        final_text = (
            raw_text
            if args.skip_cleanup
            else restructure_transcript(
                client=client,
                raw_text=raw_text,
                model=args.cleanup_model,
            )
        )
        write_transcript(output_path, final_text)
        print(f"Transcripcion guardada en: {output_path}")
        return 0
    except Exception as exc:
        print(f"Error durante la transcripcion: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
