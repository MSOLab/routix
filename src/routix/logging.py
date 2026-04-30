"""File handler lifecycle helpers and prefix/level record filter.

See `docs/20260429_artifact_manager.md` § 4.4 / § 4.5 / § 7.2 for design rationale.
"""

from __future__ import annotations

import logging
from pathlib import Path

__all__ = ["PrefixLevelFilter", "attach_fh_to_logger", "detach_fh_from_logger"]

_MANAGED_TAG = "_routix_managed"

_DEFAULT_FILE_FMT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


class PrefixLevelFilter(logging.Filter):
    """Pass records whose name starts with `prefix` only at WARNING+; drop INFO/DEBUG.

    Records are not mutated. Records from loggers outside the prefix namespace
    pass through untouched. Attach to an upstream file handler to shield it
    from a noisy sub-namespace while keeping WARNING+ from that namespace
    surfacing.
    """

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith(self._prefix):
            return record.levelno >= logging.WARNING
        return True


def attach_fh_to_logger(logger_name: str, file_path: Path) -> logging.Logger:
    """Attach a DEBUG-level file handler to `logger_name`.

    `propagate` is left untouched (Python default `True`). On entry, any stale
    handler tagged `_MANAGED_TAG` is closed and removed (defensive sweep), so a
    prior call that failed to detach does not leak file descriptors into this
    one.
    """
    log = logging.getLogger(logger_name)
    _sweep(log)
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(file_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_DEFAULT_FILE_FMT)
    setattr(fh, _MANAGED_TAG, True)
    log.addHandler(fh)
    return log


def detach_fh_from_logger(logger_name: str) -> None:
    """Close and remove handlers attached by `attach_fh_to_logger`. Idempotent."""
    _sweep(logging.getLogger(logger_name))


def _sweep(log: logging.Logger) -> None:
    for h in list(log.handlers):
        if getattr(h, _MANAGED_TAG, False):
            try:
                h.close()
            finally:
                log.removeHandler(h)
