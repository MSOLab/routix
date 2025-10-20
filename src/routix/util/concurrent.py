import os
import threading
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Callable

import yaml


def platform_lock(f: TextIOWrapper) -> tuple[Callable[[], None], Callable[[], None]]:
    """Creates platform-specific file lock and unlock functions.

    Args:
        f (TextIOWrapper): an open text file object (e.g. opened with open(path, "a", encoding="utf-8"))

    Returns:
        A (lock, unlock) tuple of functions.
    """
    if os.name == "nt":
        import msvcrt

        def lock():
            # Lock 1 byte at the start of the file (locking 0 bytes is not supported)
            f.seek(0, os.SEEK_SET)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

        def unlock():
            f.seek(0, os.SEEK_SET)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
    else:
        import fcntl

        def lock():
            fcntl.flock(f, fcntl.LOCK_EX)

        def unlock():
            fcntl.flock(f, fcntl.LOCK_UN)

    return lock, unlock


_file_lock = threading.Lock()


def append_data_to_yaml(
    yaml_path: Path, row: dict[str, Any], encoding: str = "utf-8"
) -> None:
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    with _file_lock:
        with open(yaml_path, "a", encoding=encoding) as f:
            lock, unlock = platform_lock(f)
            lock()
            try:
                yaml.safe_dump(row, f)
                f.flush()
                os.fsync(f.fileno())
            finally:
                unlock()


def batch_write_data_to_yaml(
    yaml_path: Path, rows: list[dict[str, Any]], encoding: str = "utf-8"
) -> None:
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    with _file_lock:
        with open(yaml_path, "w", encoding=encoding) as f:
            lock, unlock = platform_lock(f)
            lock()
            try:
                yaml.safe_dump_all(rows, f)
                f.flush()
                os.fsync(f.fileno())
            finally:
                unlock()


def append_data_to_csv(
    csv_path: Path,
    row: dict[str, Any],
    header: list[str],
    encoding: str = "utf-8",
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with _file_lock:
        file_exists = csv_path.is_file()
        with open(csv_path, "a", encoding=encoding, newline="") as f:
            lock, unlock = platform_lock(f)
            lock()
            try:
                if not file_exists and header is not None:
                    f.write(",".join(header) + "\n")
                f.write(",".join(str(row.get(col, "")) for col in header) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                unlock()


def batch_write_data_to_csv(
    csv_path: Path,
    rows: list[dict[str, Any]],
    header: list[str],
    encoding: str = "utf-8",
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with _file_lock:
        with open(csv_path, "w", encoding=encoding, newline="") as f:
            lock, unlock = platform_lock(f)
            lock()
            try:
                lines: list[str] = []
                if header is not None:
                    lines.append(",".join(header))
                for row in rows:
                    lines.append(",".join(str(row.get(col, "")) for col in header))
                f.write("\n".join(lines) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                unlock()
