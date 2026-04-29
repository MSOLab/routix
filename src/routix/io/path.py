import re
from dataclasses import dataclass
from pathlib import Path

from ..elapsed_timer import ElapsedTimer


@dataclass(frozen=True)
class RunRoot:
    """Run-level root directory paired with its identifier.

    `path` is the directory created by `init_run_root`. `run_id` is the
    identifier used both as the directory name and as the prefix in
    log/artifact file templates resolved by `ArtifactLayout`.
    """

    path: Path
    run_id: str


def init_timestamped_working_dir(
    base_output_dir: Path, e_timer: ElapsedTimer | None = None
) -> Path:
    """
    Creates and returns a timestamped working directory.

    If an ElapsedTimer instance is provided, it uses its start time.
    Otherwise, it creates a new ElapsedTimer instance.

    Args:
        base_output_dir (Path): The base directory where the new timestamped directory will be created.
        e_timer (ElapsedTimer | None, optional): An optional existing timer. Defaults to None.

    Returns:
        Path: The path to the created timestamped working directory.
    """
    if e_timer is None:
        e_timer = ElapsedTimer()
    working_dir = base_output_dir / e_timer.get_start_dt_for_dir_name()
    working_dir.mkdir(parents=True, exist_ok=True)
    return working_dir


def init_run_root(
    base_output_dir: Path, e_timer: ElapsedTimer | None = None
) -> RunRoot:
    """Create a timestamped run root and return both its path and run_id.

    Equivalent in side-effect to `init_timestamped_working_dir`, but exposes
    the directory name as `run_id` so callers can construct an
    `ArtifactLayout(run_root=..., run_id=...)` without re-deriving it.

    Args:
        base_output_dir: Base directory under which the run root is created.
        e_timer: Optional caller-owned timer whose start time names the run.
            If None, a fresh `ElapsedTimer` is created locally and used only
            to derive `run_id`.

    Returns:
        RunRoot: The created directory and its identifier.
    """
    if e_timer is None:
        e_timer = ElapsedTimer()
    run_id = e_timer.get_start_dt_for_dir_name()
    run_root = base_output_dir / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    return RunRoot(path=run_root, run_id=run_id)


def extract_prefix_from_filename(pattern: str, filename: str) -> str | None:
    """Extracts the prefix from a filename based on a given pattern.

    For example, pattern `{}_obj_log.yaml` will match filename `0_obj_log.yaml` and extract "0".

    Args:
        pattern (str): Pattern to match the filename, with {} for the prefix.
        filename (str): Filename to extract the prefix from.

    Returns:
        str | None: The extracted prefix or None if not matched.
    """
    # Escape special regex chars except {}
    regex = re.escape(pattern).replace(r"\{\}", "(.+?)")
    match = re.match(regex, filename)
    if match:
        return match.group(1)
    return None
