import logging
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).parent.parent.parent / "log"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
ROTATION = "5 MB"
RETENTION = "1 days"


class InterceptHandler(logging.Handler):
    """Intercept standard library logging and redirect to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    logger.add(
        LOG_DIR / "debug.log",
        level="DEBUG",
        filter=lambda record: record["level"].name == "DEBUG",
        format=LOG_FORMAT,
        rotation=ROTATION,
        retention=RETENTION,
        encoding="utf-8",
        enqueue=True,
    )

    logger.add(
        LOG_DIR / "info.log",
        level="INFO",
        filter=lambda record: record["level"].name == "INFO",
        format=LOG_FORMAT,
        rotation=ROTATION,
        retention=RETENTION,
        encoding="utf-8",
        enqueue=True,
    )

    logger.add(
        LOG_DIR / "warn.log",
        level="WARNING",
        filter=lambda record: record["level"].name == "WARNING",
        format=LOG_FORMAT,
        rotation=ROTATION,
        retention=RETENTION,
        encoding="utf-8",
        enqueue=True,
    )

    logger.add(
        LOG_DIR / "error.log",
        level="ERROR",
        filter=lambda record: record["level"].name in ("ERROR", "CRITICAL"),
        format=LOG_FORMAT,
        rotation=ROTATION,
        retention=RETENTION,
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers = [InterceptHandler()]
