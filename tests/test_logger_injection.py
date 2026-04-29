"""Tests for `self.logger` injection hooks across routix base classes."""

import logging
from pathlib import Path
from typing import Any

import pytest

from routix.runner.multi_instance_concurrent_runner import (
    MultiInstanceConcurrentRunner,
)
from routix.runner.multi_instance_runner import MultiInstanceRunner
from routix.runner.multi_scenario_runner import MultiScenarioRunner
from routix.runner.single_instance_runner import SingleInstanceRunner
from routix.solution_manager import SolutionManager


class _DummySingleInstanceRunner(SingleInstanceRunner):
    def get_controller(self):  # pragma: no cover - not exercised here
        raise NotImplementedError

    def post_run_process(self):  # pragma: no cover - not exercised here
        return None


class _DummyMultiInstanceRunner(MultiInstanceRunner):
    def post_run_process(self):  # pragma: no cover - not exercised here
        return None


class _DummyMultiInstanceConcurrentRunner(MultiInstanceConcurrentRunner):
    def post_run_process(self):  # pragma: no cover - not exercised here
        return None


class _DummyMultiScenarioRunner(MultiScenarioRunner):
    def post_run_process(self):  # pragma: no cover - not exercised here
        return None


class _DummySolutionManager(SolutionManager):
    def _get_obj_value(self, solution: Any) -> float:  # pragma: no cover
        return 0.0

    def _a_is_better_obj_value(self, value_a, value_b) -> bool:  # pragma: no cover
        return False

    def _a_is_better_obj_bound(self, bound_a, bound_b) -> bool:  # pragma: no cover
        return False


@pytest.fixture
def single_instance_kwargs(tmp_path: Path) -> dict:
    return {
        "instance": object(),
        "shared_param_dict": {},
        "subroutine_flow": [],
        "stopping_criteria": None,
        "output_dir": tmp_path,
        "output_metadata": {},
    }


@pytest.fixture
def multi_instance_kwargs(tmp_path: Path) -> dict:
    return {
        "s_i_runner_class": _DummySingleInstanceRunner,
        "instances": [],
        "shared_param_dict": {},
        "subroutine_flow": [],
        "stopping_criteria": None,
        "output_dir": tmp_path,
        "output_metadata": {},
    }


@pytest.fixture
def multi_scenario_kwargs(tmp_path: Path) -> dict:
    return {
        "m_i_runner_class": _DummyMultiInstanceRunner,
        "s_i_runner_class": _DummySingleInstanceRunner,
        "instances": [],
        "shared_param_dict": {},
        "scenario_configs": [],
        "output_dir": tmp_path,
        "base_output_metadata": {},
    }


def test_single_instance_runner_default_logger_name(single_instance_kwargs):
    runner = _DummySingleInstanceRunner(**single_instance_kwargs)
    assert runner.logger.name == "routix._DummySingleInstanceRunner"


def test_single_instance_runner_logger_injection(single_instance_kwargs):
    custom = logging.getLogger("test.custom.sir")
    runner = _DummySingleInstanceRunner(**single_instance_kwargs, logger=custom)
    assert runner.logger is custom


def test_multi_instance_runner_default_logger_name(multi_instance_kwargs):
    runner = _DummyMultiInstanceRunner(**multi_instance_kwargs)
    assert runner.logger.name == "routix._DummyMultiInstanceRunner"


def test_multi_instance_runner_logger_injection(multi_instance_kwargs):
    custom = logging.getLogger("test.custom.mir")
    runner = _DummyMultiInstanceRunner(**multi_instance_kwargs, logger=custom)
    assert runner.logger is custom


def test_multi_instance_concurrent_runner_default_logger_name(multi_instance_kwargs):
    runner = _DummyMultiInstanceConcurrentRunner(**multi_instance_kwargs)
    assert runner.logger.name == "routix._DummyMultiInstanceConcurrentRunner"


def test_multi_instance_concurrent_runner_logger_injection(multi_instance_kwargs):
    custom = logging.getLogger("test.custom.micr")
    runner = _DummyMultiInstanceConcurrentRunner(
        **multi_instance_kwargs, logger=custom
    )
    assert runner.logger is custom


def test_multi_scenario_runner_default_logger_name(multi_scenario_kwargs):
    runner = _DummyMultiScenarioRunner(**multi_scenario_kwargs)
    assert runner.logger.name == "routix._DummyMultiScenarioRunner"


def test_multi_scenario_runner_logger_injection(multi_scenario_kwargs):
    custom = logging.getLogger("test.custom.msr")
    runner = _DummyMultiScenarioRunner(**multi_scenario_kwargs, logger=custom)
    assert runner.logger is custom


def test_solution_manager_default_logger_name():
    sm = _DummySolutionManager()
    assert sm.logger.name == "routix._DummySolutionManager"


def test_solution_manager_logger_injection():
    custom = logging.getLogger("test.custom.sm")
    sm = _DummySolutionManager(logger=custom)
    assert sm.logger is custom
