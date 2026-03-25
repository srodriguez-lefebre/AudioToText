import sys

from loguru import logger

from audio_to_text.config.settings import Settings


def configure_logging(settings: Settings, *, verbose: bool = False) -> None:
    """Configures console logging for the CLI."""

    level = "DEBUG" if verbose else settings.LOG_LEVEL.upper()

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        backtrace=False,
        diagnose=False,
        colorize=True,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        ),
    )
