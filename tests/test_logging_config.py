from audio_to_text.config.settings import Settings
from audio_to_text.logging_config import configure_logging


def test_configure_logging_enables_colorized_output(monkeypatch) -> None:
    removed = False
    captured: dict[str, object] = {}

    def fake_remove() -> None:
        nonlocal removed
        removed = True

    def fake_add(*args: object, **kwargs: object) -> int:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return 1

    monkeypatch.setattr("audio_to_text.logging_config.logger.remove", fake_remove)
    monkeypatch.setattr("audio_to_text.logging_config.logger.add", fake_add)

    configure_logging(Settings(LOG_LEVEL="INFO"))

    assert removed is True
    assert captured["kwargs"]["colorize"] is True
