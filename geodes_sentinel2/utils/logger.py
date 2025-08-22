"""
Logging setup for Sentinel-2 processor.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    disable_existing: bool = False,
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name (None for root logger)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Custom format string
        disable_existing: Disable existing loggers

    Returns:
        Configured logger
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Clear existing handlers if requested
    if disable_existing:
        logger.handlers.clear()

    # Skip if already configured
    if logger.handlers:
        return logger

    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatter
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def setup_package_logging(
    level: str = "INFO", log_file: Optional[str] = None, format_string: Optional[str] = None
):
    """
    Set up logging for the entire package.

    Args:
        level: Logging level
        log_file: Optional log file path
        format_string: Custom format string
    """
    # Setup root logger for the package
    setup_logger(
        name="geodes_sentinel2",
        level=level,
        log_file=log_file,
        format_string=format_string,
        disable_existing=True,
    )

    # Also setup submodule loggers
    for module in ["core", "processing", "utils"]:
        setup_logger(
            name=f"geodes_sentinel2.{module}",
            level=level,
            log_file=log_file,
            format_string=format_string,
            disable_existing=True,
        )


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format with colors."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_colored_logger(
    name: Optional[str] = None, level: str = "INFO", log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with colored console output.

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path

    Returns:
        Configured logger with colors
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Colored console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    colored_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # Regular file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)

        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
