"""Logging configuration with --verbose / --quiet control."""
import logging
import sys


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging to stderr with level based on flags."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    ))
    root = logging.getLogger("arcgis_agent")
    root.setLevel(level)
    # Clear existing handlers to avoid duplicate output on repeated calls
    root.handlers.clear()
    root.addHandler(handler)
