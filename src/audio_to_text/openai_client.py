from typing import cast

from openai import OpenAI

from audio_to_text.interfaces import OpenAIClientProtocol


def create_client(api_key: str) -> OpenAIClientProtocol:
    """Builds an OpenAI client with the provided API key."""

    return cast(OpenAIClientProtocol, OpenAI(api_key=api_key))
