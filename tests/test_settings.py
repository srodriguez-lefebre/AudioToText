from pathlib import Path

from audio_to_text.config.settings import (
    DEFAULT_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    Settings,
    resolve_env_file,
)


def test_settings_load_from_explicit_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=test-key",
                "INPUT_DIR=custom-inputs",
                "OUTPUT_DIR=custom-outputs",
                "LOG_LEVEL=DEBUG",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.OPENAI_API_KEY is not None
    assert settings.OPENAI_API_KEY.get_secret_value() == "test-key"
    assert Path("custom-inputs") == settings.INPUT_DIR
    assert Path("custom-outputs") == settings.OUTPUT_DIR
    assert settings.LOG_LEVEL == "DEBUG"


def test_settings_defaults_are_runtime_relative_paths() -> None:
    settings = Settings()

    assert settings.INPUT_DIR == DEFAULT_INPUT_DIR
    assert settings.OUTPUT_DIR == DEFAULT_OUTPUT_DIR


def test_resolve_env_file_uses_current_working_directory(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key", encoding="utf-8")

    assert resolve_env_file(tmp_path) == env_file
