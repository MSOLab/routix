"""Failure-contract tests for the runner hierarchy.

Covers the verified defects listed in docs/20260702_laadi_plan.md §3.1:

- SingleInstanceRunner.run() swallowed controller exceptions via
  ``finally: return post_run_process()``.
- MultiInstanceConcurrentRunner.run() had no per-instance exception
  isolation: one failing ``future.result()`` killed the whole scenario.

Classes are defined at module level so they can be pickled into
ProcessPoolExecutor workers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from routix.runner import (
    MultiInstanceConcurrentRunner,
    MultiInstanceRunner,
    SingleInstanceRunner,
)
from routix.type_defs import RunMode


@dataclass
class _Instance:
    name: str
    fail: bool = False


class _Controller:
    def __init__(self, fail: bool):
        self.fail = fail

    def set_working_dir(self, working_dir: Path) -> None:
        self.working_dir = working_dir

    def run(self) -> None:
        if self.fail:
            raise RuntimeError("controller boom")


class _Runner(SingleInstanceRunner):
    post_called: bool = False

    def get_controller(self) -> _Controller:
        return _Controller(fail=self.instance.fail)

    def post_run_process(self) -> str:
        self.post_called = True
        return f"ok-{self.ins_name}"


class _HookRunner(_Runner):
    """Records what the on_run_error hook receives."""

    hook_exc: Exception | None = None

    def on_run_error(self, exc: Exception) -> None:
        self.hook_exc = exc


class _FailingHookRunner(_Runner):
    """A hook that itself crashes must not mask the controller exception."""

    def on_run_error(self, exc: Exception) -> None:
        raise ValueError("hook boom")


class _MultiRunner(MultiInstanceRunner):
    def post_run_process(self) -> list[Any]:
        return list(self.results)


class _MultiConcurrentRunner(MultiInstanceConcurrentRunner):
    def post_run_process(self) -> list[Any]:
        return list(self.results)


def _make_single(
    tmp_path: Path,
    fail: bool,
    mode: RunMode = RunMode.FULL_RUN,
    runner_cls: type[_Runner] = _Runner,
) -> _Runner:
    return runner_cls(
        instance=_Instance(name="i1", fail=fail),
        shared_param_dict={},
        subroutine_flow=None,
        stopping_criteria=None,
        output_dir=tmp_path,
        output_metadata={},
        mode=mode,
    )


def _make_multi(
    runner_cls: type, tmp_path: Path, **kwargs: Any
) -> MultiInstanceRunner:
    instances = [_Instance("a"), _Instance("b", fail=True), _Instance("c")]
    return runner_cls(
        s_i_runner_class=_Runner,
        instances=instances,
        shared_param_dict={},
        subroutine_flow=None,
        stopping_criteria=None,
        output_dir=tmp_path,
        output_metadata={},
        **kwargs,
    )


# --- SingleInstanceRunner -------------------------------------------------


def test_single_runner_propagates_controller_exception(tmp_path):
    """A controller exception must reach the caller, not be swallowed."""
    runner = _make_single(tmp_path, fail=True)
    with pytest.raises(RuntimeError, match="controller boom"):
        runner.run()
    assert runner.post_called is False, (
        "post_run_process must not run on a failed controller"
    )


def test_single_runner_success_runs_post_process(tmp_path):
    runner = _make_single(tmp_path, fail=False)
    assert runner.run() == "ok-i1"
    assert runner.post_called is True


def test_single_runner_post_process_only_skips_controller(tmp_path):
    """POST_PROCESS_ONLY never builds a controller, so fail=True is inert."""
    runner = _make_single(tmp_path, fail=True, mode=RunMode.POST_PROCESS_ONLY)
    assert runner.run() == "ok-i1"


# --- on_run_error hook -------------------------------------------------------


def test_on_run_error_hook_receives_controller_exception(tmp_path):
    """On controller failure the hook gets the exception, then it propagates."""
    runner = _make_single(tmp_path, fail=True, runner_cls=_HookRunner)
    with pytest.raises(RuntimeError, match="controller boom"):
        runner.run()
    assert isinstance(runner.hook_exc, RuntimeError)
    assert runner.post_called is False


def test_on_run_error_hook_not_called_on_success(tmp_path):
    runner = _make_single(tmp_path, fail=False, runner_cls=_HookRunner)
    assert runner.run() == "ok-i1"
    assert runner.hook_exc is None


def test_on_run_error_hook_failure_does_not_mask_original(tmp_path):
    """A crashing hook is logged; the controller exception still propagates."""
    runner = _make_single(tmp_path, fail=True, runner_cls=_FailingHookRunner)
    with pytest.raises(RuntimeError, match="controller boom"):
        runner.run()


# --- MultiInstanceRunner (sequential) ---------------------------------------


def test_multi_runner_isolates_instance_failure(tmp_path):
    """One failing instance yields None; the others still run."""
    results = _make_multi(_MultiRunner, tmp_path).run()
    assert results == ["ok-a", None, "ok-c"]


# --- MultiInstanceConcurrentRunner ------------------------------------------


def test_concurrent_runner_isolates_instance_failure(tmp_path):
    """A failing worker must not kill the pool or the scenario."""
    results = _make_multi(
        _MultiConcurrentRunner, tmp_path, instance_worker_cnt=2
    ).run()
    assert sorted(r for r in results if r is not None) == ["ok-a", "ok-c"]
    assert results.count(None) == 1
