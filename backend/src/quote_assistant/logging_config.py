from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Make quote_assistant INFO logs visible, including background job failures.

    basicConfig is a no-op when the root logger already has handlers (pytest, uvicorn).
    The package logger is still raised to the configured level so vendor / background
    messages are not swallowed by the default WARNING root.
    """
    resolved = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=resolved, format=_FORMAT)
    logging.getLogger("quote_assistant").setLevel(resolved)
