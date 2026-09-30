import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure a compact process-wide log format."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
