"""Tests for `routix.logging` file-handler lifecycle and prefix/level filter.

Scenarios mirror `docs/20260429_artifact_manager.md` § 7.2.
"""

import logging
from pathlib import Path

import pytest

from src.routix.logging import (
    PrefixLevelFilter,
    _MANAGED_TAG,
    attach_fh_to_logger,
    detach_fh_from_logger,
)


def _unique_logger_name(request: pytest.FixtureRequest, suffix: str = "") -> str:
    return f"test.routix.logging.{request.node.name}{suffix}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _managed_handlers(name: str) -> list[logging.Handler]:
    return [h for h in logging.getLogger(name).handlers if getattr(h, _MANAGED_TAG, False)]


@pytest.fixture(autouse=True)
def _cleanup_loggers():
    """Remove any leftover handlers from `test.*` loggers used by these tests."""
    yield
    manager = logging.Logger.manager
    for name in list(manager.loggerDict):
        if name.startswith("test.routix.logging") or name.startswith("test.parent."):
            log = logging.getLogger(name)
            for h in list(log.handlers):
                try:
                    h.close()
                finally:
                    log.removeHandler(h)
            log.setLevel(logging.NOTSET)
            for f in list(log.filters):
                log.removeFilter(f)


# --- doc § 7.2 scenario 1: normal exit → handler removed, fd closed ---------

def test_attach_then_detach_removes_handler(tmp_path, request):
    name = _unique_logger_name(request)
    log_path = tmp_path / "sc.log"

    log = attach_fh_to_logger(name, log_path)
    handlers_after_attach = _managed_handlers(name)
    assert len(handlers_after_attach) == 1
    assert isinstance(handlers_after_attach[0], logging.FileHandler)

    fh = handlers_after_attach[0]
    detach_fh_from_logger(name)

    assert _managed_handlers(name) == []
    assert fh.stream is None or fh.stream.closed
    # Logger object identity preserved across attach/detach
    assert logging.getLogger(name) is log


# --- doc § 7.2 scenario 2: exception during run → finally detach works ------

def test_detach_runs_in_finally_on_exception(tmp_path, request):
    name = _unique_logger_name(request)
    log_path = tmp_path / "sc.log"

    with pytest.raises(RuntimeError):
        try:
            attach_fh_to_logger(name, log_path)
            logging.getLogger(name).info("before-failure")
            raise RuntimeError("boom")
        finally:
            detach_fh_from_logger(name)

    assert _managed_handlers(name) == []
    # File should be closed and content flushed
    assert "before-failure" in _read(log_path)


# --- doc § 7.2 scenario 3: instance A leaked → instance B sweeps it ---------

def test_defensive_sweep_clears_stale_handler(tmp_path, request):
    name = _unique_logger_name(request)
    path_a = tmp_path / "A.log"
    path_b = tmp_path / "B.log"

    # Simulate instance A: attach but skip detach (leaked handler)
    attach_fh_to_logger(name, path_a)
    leaked = _managed_handlers(name)[0]

    # Instance B: attach should sweep A's handler before adding its own
    attach_fh_to_logger(name, path_b)

    handlers = _managed_handlers(name)
    assert len(handlers) == 1, "defensive sweep should leave exactly one managed handler"
    assert handlers[0] is not leaked
    assert Path(handlers[0].baseFilename) == path_b
    assert leaked.stream is None or leaked.stream.closed

    detach_fh_from_logger(name)


# --- doc § 7.2 scenario 4: per-instance logger name → isolation -------------

def test_per_instance_logger_isolation(tmp_path, request):
    name_a = _unique_logger_name(request, "_A")
    name_b = _unique_logger_name(request, "_B")
    path_a = tmp_path / "A.log"
    path_b = tmp_path / "B.log"

    attach_fh_to_logger(name_a, path_a)
    attach_fh_to_logger(name_b, path_b)

    logging.getLogger(name_a).info("a-record")
    logging.getLogger(name_b).info("b-record")

    detach_fh_from_logger(name_a)
    detach_fh_from_logger(name_b)

    text_a = _read(path_a)
    text_b = _read(path_b)
    assert "a-record" in text_a and "b-record" not in text_a
    assert "b-record" in text_b and "a-record" not in text_b


# --- doc § 7.2 scenarios 5 & 6: filter on parent file handler ---------------

@pytest.fixture
def parent_with_filter(tmp_path):
    """Build a parent logger + file handler with `PrefixLevelFilter` attached.

    Returns (parent_name, parent_path, sc_name, sc_path). Caller is responsible
    for cleanup via the autouse fixture matching the `test.parent.` prefix.
    """
    parent_name = "test.parent.sir"
    sc_name = "test.parent.sir.controller.inst1"
    parent_path = tmp_path / "sir.log"
    sc_path = tmp_path / "sc.log"

    parent_log = logging.getLogger(parent_name)
    parent_log.setLevel(logging.DEBUG)
    parent_fh = logging.FileHandler(parent_path, mode="a", encoding="utf-8")
    parent_fh.setLevel(logging.DEBUG)
    parent_fh.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    parent_fh.addFilter(PrefixLevelFilter("test.parent.sir.controller"))
    parent_log.addHandler(parent_fh)

    return parent_name, parent_path, sc_name, sc_path


def test_sc_info_recorded_in_sc_log_only(parent_with_filter):
    parent_name, parent_path, sc_name, sc_path = parent_with_filter
    attach_fh_to_logger(sc_name, sc_path)
    try:
        logging.getLogger(sc_name).info("sc-info-only")
    finally:
        detach_fh_from_logger(sc_name)

    assert "sc-info-only" in _read(sc_path)
    assert "sc-info-only" not in _read(parent_path)


def test_sc_error_surfaces_in_parent_log(parent_with_filter):
    parent_name, parent_path, sc_name, sc_path = parent_with_filter
    attach_fh_to_logger(sc_name, sc_path)
    try:
        logging.getLogger(sc_name).error("sc-error-surface")
    finally:
        detach_fh_from_logger(sc_name)

    assert "sc-error-surface" in _read(sc_path)
    assert "sc-error-surface" in _read(parent_path)


# --- doc § 7.2 scenario 7: non-prefix logger INFO passes through ------------

def test_filter_passes_unrelated_logger_info(parent_with_filter):
    parent_name, parent_path, _sc_name, _sc_path = parent_with_filter

    # An unrelated logger that propagates into the same parent
    unrelated = logging.getLogger("test.parent.sir.other.module")
    unrelated.setLevel(logging.DEBUG)
    unrelated.info("unrelated-info")

    assert "unrelated-info" in _read(parent_path)


# --- additional unit tests --------------------------------------------------

def test_attach_twice_keeps_single_handler(tmp_path, request):
    name = _unique_logger_name(request)
    path1 = tmp_path / "first.log"
    path2 = tmp_path / "second.log"

    attach_fh_to_logger(name, path1)
    attach_fh_to_logger(name, path2)

    handlers = _managed_handlers(name)
    assert len(handlers) == 1
    assert Path(handlers[0].baseFilename) == path2

    detach_fh_from_logger(name)


def test_detach_without_attach_is_noop(request):
    name = _unique_logger_name(request)
    # Should not raise even though nothing was attached
    detach_fh_from_logger(name)
    assert _managed_handlers(name) == []


def test_filter_does_not_mutate_record():
    flt = PrefixLevelFilter("foo.bar")
    record = logging.LogRecord(
        name="foo.bar.sub",
        level=logging.WARNING,
        pathname=__file__,
        lineno=42,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    original_name = record.name
    original_level = record.levelno
    original_lineno = record.lineno

    assert flt.filter(record) is True
    assert record.name == original_name
    assert record.levelno == original_level
    assert record.lineno == original_lineno


def test_filter_drops_prefix_info_and_debug():
    flt = PrefixLevelFilter("ffc.controller")

    def make(name: str, level: int) -> logging.LogRecord:
        return logging.LogRecord(
            name=name, level=level, pathname=__file__, lineno=1,
            msg="m", args=(), exc_info=None,
        )

    assert flt.filter(make("ffc.controller.x", logging.DEBUG)) is False
    assert flt.filter(make("ffc.controller.x", logging.INFO)) is False
    assert flt.filter(make("ffc.controller.x", logging.WARNING)) is True
    assert flt.filter(make("ffc.controller.x", logging.ERROR)) is True
    assert flt.filter(make("ffc.controller.x", logging.CRITICAL)) is True
    # Non-matching prefix passes through at any level
    assert flt.filter(make("other.namespace", logging.DEBUG)) is True
    assert flt.filter(make("other.namespace", logging.INFO)) is True


def test_attach_does_not_change_propagate(tmp_path, request):
    name = _unique_logger_name(request)
    log = logging.getLogger(name)
    initial_propagate = log.propagate  # Python default: True

    attach_fh_to_logger(name, tmp_path / "sc.log")
    assert log.propagate is initial_propagate

    detach_fh_from_logger(name)
    assert log.propagate is initial_propagate
