from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

_PACKAGE_LOGGERS = (
    "quote_assistant",
    "quote_assistant.background",
    "quote_assistant.extraction.vendor",
    "quote_assistant.startup",
)


def configure_logging(level: str = "INFO") -> None:
    """Make quote_assistant INFO logs visible, including background job failures.

    basicConfig is a no-op when the root logger already has handlers (pytest, uvicorn).
    Alembic's fileConfig also disables already-created loggers; re-enable ours so a
    same-process migration (缝 1) cannot silence background failures.
    """
    resolved = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=resolved, format=_FORMAT)
    for name in _PACKAGE_LOGGERS:
        logger = logging.getLogger(name)
        logger.disabled = False
        logger.setLevel(resolved)
        logger.propagate = True
