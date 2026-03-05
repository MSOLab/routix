import re
from pathlib import Path

from ..elapsed_timer import ElapsedTimer


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
