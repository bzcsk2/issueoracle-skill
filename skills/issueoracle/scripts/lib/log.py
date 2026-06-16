from __future__ import annotations

import logging
import os
import sys


def get_logger(name: str = "issueoracle") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = logging.DEBUG if os.environ.get("ISSUEORACLE_DEBUG") else logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[issueoracle] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    return logger


def set_debug(enabled: bool = True) -> None:
    level = logging.DEBUG if enabled else logging.INFO
    logger = logging.getLogger("issueoracle")
    logger.setLevel(level)
    for h in logger.handlers:
        h.setLevel(level)
