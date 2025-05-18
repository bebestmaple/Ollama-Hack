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
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.threadpool").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)


setup_logging(get_config())
