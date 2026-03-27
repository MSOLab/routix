import os
import subprocess
import sys
import threading
import time
import types
from io import TextIOWrapper
from typing import TextIO, cast

import yaml

from routix.util.concurrent import (
    append_data_to_csv,
    append_data_to_yaml,
    batch_write_data_to_csv,
    batch_write_data_to_yaml,
    platform_lock,
)


# --- Helpers ------------------------------------------------------------------
class _FakeFile:
    """Minimal file-like object for platform_lock tests."""

    def __init__(self):
        self._pos = 0
        self._fileno = 42
        self.seek_calls = []

    def seek(self, offset, whence=os.SEEK_SET):
        self._pos = offset
        self.seek_calls.append((offset, whence))

    def fileno(self):
        return self._fileno


# --- platform_lock tests ------------------------------------------------------
def test_platform_lock_posix(monkeypatch):
    # Force POSIX branch
    monkeypatch.setattr(os, "name", "posix", raising=False)

    # Provide fake fcntl
    calls = []
    fake_fcntl = types.SimpleNamespace(
        LOCK_EX=1,
        LOCK_UN=2,
        flock=lambda f, flag: calls.append(("flock", f, flag)),
    )
    monkeypatch.setitem(sys.modules, "fcntl", fake_fcntl)

    fake = _FakeFile()
    f_for_sig = cast(TextIOWrapper, fake)
    lock, unlock = platform_lock(f_for_sig)

    lock()
    unlock()

    # Expect exclusive lock then unlock on the same object
    assert calls == [
        ("flock", fake, fake_fcntl.LOCK_EX),
        ("flock", fake, fake_fcntl.LOCK_UN),
    ]


def test_platform_lock_windows(monkeypatch):
    # Force Windows branch
    monkeypatch.setattr(os, "name", "nt", raising=False)

    # Capture msvcrt.locking calls
    calls = []

    def fake_locking(fd, mode, nbytes):
        calls.append(("locking", fd, mode, nbytes))

    fake_msvcrt = types.SimpleNamespace(LK_LOCK=1, LK_UNLCK=2, locking=fake_locking)
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)

    fake = _FakeFile()
    f_for_sig = cast(TextIOWrapper, fake)
    lock, unlock = platform_lock(f_for_sig)

    lock()
    unlock()

    # Seek(0, SEEK_SET) was used before each locking call
    assert fake.seek_calls == [(0, os.SEEK_SET), (0, os.SEEK_SET)]
    # 1 byte locking used with fileno()
    assert calls == [
        ("locking", fake.fileno(), fake_msvcrt.LK_LOCK, 1),
        ("locking", fake.fileno(), fake_msvcrt.LK_UNLCK, 1),
    ]


# --- YAML write tests ---------------------------------------------------------
def test_append_data_to_yaml_appends_multiple_docs(tmp_path, monkeypatch):
    # Avoid real fsync overhead but ensure it was invoked
    fsync_called = {"n": 0}
    monkeypatch.setattr(
        os, "fsync", lambda fd: fsync_called.__setitem__("n", fsync_called["n"] + 1)
    )

    ypath = tmp_path / "out" / "data.yaml"
    rows = [{"a": 1}, {"b": 2}]

    # Write twice with append
    append_data_to_yaml(ypath, rows[0])
    append_data_to_yaml(ypath, rows[1])

    with open(ypath, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    # Both docs present
    assert loaded == {"a": 1, "b": 2}
    # fsync called twice (once per write)
    assert fsync_called["n"] == 2


def test_batch_write_data_to_yaml_overwrites_and_writes_all(tmp_path, monkeypatch):
    fsync_called = {"n": 0}
    monkeypatch.setattr(
        os, "fsync", lambda fd: fsync_called.__setitem__("n", fsync_called["n"] + 1)
    )

    ypath = tmp_path / "out" / "data.yaml"
    first = [{"x": 1}]
    second = [{"a": 1}, {"b": 2}, {"c": 3}]

    # initial content
    batch_write_data_to_yaml(ypath, first)
    # overwrite with more rows
    batch_write_data_to_yaml(ypath, second)

    with open(ypath, "r", encoding="utf-8") as f:
        loaded = list(yaml.safe_load_all(f))

    assert loaded == second
    # fsync called once per batch call
    assert fsync_called["n"] == 2


# --- CSV write tests ----------------------------------------------------------
def test_append_data_to_csv_writes_header_once_and_rows(tmp_path, monkeypatch):
    fsync_called = {"n": 0}
    monkeypatch.setattr(
        os, "fsync", lambda fd: fsync_called.__setitem__("n", fsync_called["n"] + 1)
    )

    cpath = tmp_path / "csvs" / "data.csv"
    header = ["id", "name", "age"]
    r1 = {"id": 1, "name": "Ada", "age": 30}
    r2 = {"id": 2, "name": "Bob"}  # missing age -> empty string

    append_data_to_csv(cpath, r1, header)
    append_data_to_csv(cpath, r2, header)

    with open(cpath, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f.readlines()]

    assert lines == [
        "id,name,age",
        "1,Ada,30",
        "2,Bob,",
    ]
    # fsync twice (two appends)
    assert fsync_called["n"] == 2


def test_batch_write_data_to_csv_overwrites_with_header_and_rows(tmp_path, monkeypatch):
    fsync_called = {"n": 0}
    monkeypatch.setattr(
        os, "fsync", lambda fd: fsync_called.__setitem__("n", fsync_called["n"] + 1)
    )

    cpath = tmp_path / "csvs" / "batch.csv"
    header = ["col1", "col2"]
    rows = [{"col1": "a", "col2": "b"}, {"col1": "1"}]

    # pre-fill with something to ensure overwrite
    append_data_to_csv(cpath, {"col1": "old", "col2": "old"}, header)

    batch_write_data_to_csv(cpath, rows, header)

    content = cpath.read_text(encoding="utf-8").splitlines()
    assert content == ["col1,col2", "a,b", "1,"]
    # fsync once for batch write
    assert fsync_called["n"] >= 2  # at least once for pre-fill + once for batch


# --- Concurrency smoke test (internal lock usage) -----------------------------
def test_append_data_to_csv_thread_safety(tmp_path, monkeypatch):
    """
    Ensure internal _file_lock serializes writes so we don't interleave lines.
    We bypass platform-level locking by stubbing platform_lock to no-op.
    """
    cpath = tmp_path / "concurrent" / "t.csv"
    header = ["i", "val"]

    N = 50

    def worker(i):
        append_data_to_csv(cpath, {"i": i, "val": f"v{i}"}, header)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = cpath.read_text(encoding="utf-8").splitlines()
    # First line is header
    assert lines[0] == "i,val"
    # We should have exactly N data lines
    assert len(lines) == N + 1
    # Each data line should be a complete row (no partial interleaving)
    for ln in lines[1:]:
        assert ln.count(",") == 1


def test_platform_lock_exclusive(tmp_path):
    path = tmp_path / "lock_test.txt"
    path.write_text("")

    if os.name == "nt":
        code = """
import time, sys, msvcrt, os
f = open(sys.argv[1], 'a')
# msvcrt.locking does not support 0-byte locks, so always use 1-byte lock
f.seek(0, os.SEEK_SET)
msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
print("locked", flush=True)
time.sleep(2)
f.seek(0, os.SEEK_SET)
try:
    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
except OSError:
    pass
"""
    else:
        code = """
import time, sys, fcntl
f = open(sys.argv[1], 'a')
fcntl.flock(f, fcntl.LOCK_EX)
print("locked", flush=True)
time.sleep(2)
fcntl.flock(f, fcntl.LOCK_UN)
"""

    # First process holds the lock for 2 seconds
    p1 = subprocess.Popen(
        [sys.executable, "-c", code, str(path)], stdout=subprocess.PIPE, text=True
    )
    assert p1.stdout is not None
    stdout = cast("TextIO", p1.stdout)
    stdout.readline()  # wait until "locked"

    # Second process immediately tries to acquire lock -> blocked until released
    start = time.time()
    subprocess.run([sys.executable, "-c", code, str(path)], check=True)
    elapsed = time.time() - start

    # Second process must wait at least 2 seconds for lock to be released
    assert elapsed >= 2.0


def test_thread_lock_blocks(tmp_path):
    path = tmp_path / "test.yaml"
    path.write_text("")  # empty file

    # Events for synchronization
    main_holds_lock = threading.Event()  # Main thread signals it holds the lock
    worker_reached_lock = threading.Event()  # Worker signals it tried to acquire lock

    with open(path, "a", encoding="utf-8") as f:
        lock, unlock = platform_lock(f)

        def worker():
            with open(path, "a", encoding="utf-8") as g:
                l2, u2 = platform_lock(g)
                # Wait until main thread confirms it holds the lock
                main_holds_lock.wait(timeout=2.0)
                assert main_holds_lock.is_set(), "Main thread did not acquire lock"

                t0 = time.monotonic()
                l2()  # This should block since main thread holds the lock
                u2()
                elapsed = time.monotonic() - t0
                assert elapsed >= 0.4  # Should have been blocked for at least 0.4s

        # Acquire the lock in the main thread first
        lock()
        main_holds_lock.set()  # Signal to worker that we hold the lock

        t = threading.Thread(target=worker)
        t.start()

        # Give worker time to reach its lock attempt
        worker_reached_lock.wait(timeout=2.0)

        # Sleep to ensure blocking duration, then unlock
        time.sleep(0.6)
        unlock()
        t.join()
