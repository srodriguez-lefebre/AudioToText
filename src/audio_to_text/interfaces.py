from collections.abc import Callable
from typing import Protocol


class TranscriptionsApiProtocol(Protocol):
    """Protocol for audio transcription calls."""

    def create(
        self,
        *,
        model: str,
        file: object,
        response_format: str,
    ) -> object: ...


class AudioApiProtocol(Protocol):
    """Protocol for audio endpoints."""

    transcriptions: TranscriptionsApiProtocol


class ChatCompletionsApiProtocol(Protocol):
    """Protocol for chat completion calls."""

    def create(
        self,
        *,
        model: str,
        temperature: int,
        messages: list[dict[str, str]],
    ) -> object: ...


class ChatApiProtocol(Protocol):
    """Protocol for chat endpoints."""

    completions: ChatCompletionsApiProtocol


class OpenAIClientProtocol(Protocol):
    """Protocol for the subset of the OpenAI client used by the service."""

    audio: AudioApiProtocol
    chat: ChatApiProtocol


type ClientFactory = Callable[[str], OpenAIClientProtocol]
