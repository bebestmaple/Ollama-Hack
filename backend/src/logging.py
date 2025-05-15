import logging

from src.config import Config, get_config


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(config: Config) -> None:
    """
    Setup the logging.
    """
    logging.basicConfig(
        level=config.app.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


setup_logging(get_config())
