from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_FILE_NAME = ".env"
DEFAULT_INPUT_DIR = Path("audio_inputs")
DEFAULT_OUTPUT_DIR = Path("transcriptions")
DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-transcribe"
DEFAULT_CLEANUP_MODEL = "gpt-4.1-mini"


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    OPENAI_API_KEY: SecretStr | None = None
    INPUT_DIR: Path = DEFAULT_INPUT_DIR
    OUTPUT_DIR: Path = DEFAULT_OUTPUT_DIR
    TRANSCRIPTION_MODEL: str = DEFAULT_TRANSCRIPTION_MODEL
    CLEANUP_MODEL: str = DEFAULT_CLEANUP_MODEL
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=None, env_file_encoding="utf-8")


def resolve_env_file(current_dir: Path | None = None) -> Path | None:
    """Resolves a local .env file from the current working directory."""

    search_dir = current_dir or Path.cwd()
    env_file = search_dir / DEFAULT_ENV_FILE_NAME
    if env_file.is_file():
        return env_file

    return None


@lru_cache(maxsize=4)
def get_settings(env_file: Path | None = None) -> Settings:
    """Returns cached settings for a given runtime env file."""

    resolved_env_file = env_file.resolve() if env_file is not None else None
    return Settings(_env_file=resolved_env_file)  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    """Clears the cached settings instance."""

    get_settings.cache_clear()
