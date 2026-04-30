import dataclasses
from datetime import datetime
from pathlib import Path

import pytest

from routix.elapsed_timer import ElapsedTimer
from routix.io.path import (
    RunRoot,
    extract_prefix_from_filename,
    init_run_root,
    init_timestamped_working_dir,
)


def test_init_timestamped_working_dir_creates_directory(tmp_path: Path):
    base_output_dir = tmp_path / "outputs"

    working_dir = init_timestamped_working_dir(base_output_dir)

    assert working_dir.exists()
    assert working_dir.is_dir()
    assert working_dir.parent == base_output_dir


def test_init_timestamped_working_dir_uses_existing_elapsed_timer_start_time(
    tmp_path: Path,
):
    base_output_dir = tmp_path / "outputs"
    timer = ElapsedTimer()
    fixed_start_dt = datetime(2026, 1, 2, 3, 4, 5, 678901)
    timer.set_start_time(fixed_start_dt)

    working_dir = init_timestamped_working_dir(base_output_dir, e_timer=timer)

    expected_dir_name = fixed_start_dt.strftime("%Y%m%dT%H%M%S_%f")
    assert working_dir == base_output_dir / expected_dir_name
    assert working_dir.exists()
    assert working_dir.is_dir()


def test_extract_prefix_from_filename_matches_and_extracts_prefix():
    result = extract_prefix_from_filename("{}_obj_log.yaml", "0_obj_log.yaml")
    assert result == "0"


def test_extract_prefix_from_filename_escapes_special_characters_in_pattern():
    result = extract_prefix_from_filename("run({})[x].yaml", "run(alpha)[x].yaml")
    assert result == "alpha"


def test_extract_prefix_from_filename_returns_none_for_non_matching_filename():
    result = extract_prefix_from_filename("{}_obj_log.yaml", "0_obj_log.json")
    assert result is None


def test_extract_prefix_from_filename_is_not_full_match():
    result = extract_prefix_from_filename("{}_obj_log.yaml", "0_obj_log.yaml.bak")
    assert result == "0"


def test_init_run_root_creates_dir_and_exposes_run_id(tmp_path: Path):
    base = tmp_path / "outputs"
    timer = ElapsedTimer()
    timer.set_start_time(datetime(2026, 1, 2, 3, 4, 5, 678901))
    expected_run_id = "20260102T030405_678901"

    rr = init_run_root(base, e_timer=timer)

    assert isinstance(rr, RunRoot)
    assert rr.run_id == expected_run_id
    assert rr.path == base / expected_run_id
    assert rr.path.is_dir()


def test_init_run_root_creates_default_timer_when_none(tmp_path: Path):
    rr = init_run_root(tmp_path)

    assert rr.path.is_dir()
    # run_id always equals the directory leaf
    assert rr.run_id == rr.path.name


def test_run_root_is_frozen():
    rr = RunRoot(path=Path("/tmp"), run_id="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        rr.run_id = "y"  # type: ignore[misc]  # ty: ignore[invalid-assignment]
