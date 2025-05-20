from pathlib import Path

import pytest

from src.routix.constants import SubroutineFlowKeys
from src.routix.dynamic_data_object import DynamicDataObject
from src.routix.subroutine_controller import SubroutineController


class MockSubroutineController(SubroutineController):
    def __init__(self, name, subroutine_flow, stopping_criteria, start_dt=None):
        super().__init__(name, subroutine_flow, stopping_criteria, start_dt)
        self._stopping_condition = False

    def is_stopping_condition(self) -> bool:
        return self._stopping_condition

    def post_run_process(self):
        print("Post-run process executed.")

    def sample_method(self, value: int):
        print(f"Executing sample_method with value={value}")


@pytest.fixture
def sample_controller(tmp_path: Path):
    stopping_criteria = DynamicDataObject({"stop": False})
    subroutine_flow = DynamicDataObject.from_obj(
        [
            {SubroutineFlowKeys.METHOD: "sample_method", "value": 10},
            {SubroutineFlowKeys.METHOD: "sample_method", "value": 20},
        ]
    )
    controller = MockSubroutineController(
        "MockExperiment", subroutine_flow, stopping_criteria
    )
    controller.set_working_dir(tmp_path)
    return controller


def test_execute_routine(sample_controller: MockSubroutineController):
    sample_controller.run()
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 2
    assert method_call_log[0][SubroutineFlowKeys.METHOD] == "sample_method"
    assert method_call_log[0]["kwargs"]["value"] == 10
    assert method_call_log[1][SubroutineFlowKeys.METHOD] == "sample_method"
    assert method_call_log[1]["kwargs"]["value"] == 20


def test_call_method(sample_controller: MockSubroutineController):
    sample_controller.call_method("sample_method", value=42)
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 1
    assert method_call_log[0][SubroutineFlowKeys.METHOD] == "sample_method"
    assert method_call_log[0]["kwargs"]["value"] == 42


def test_repeat(sample_controller: MockSubroutineController):
    sample_controller.repeat(3, sample_controller._subroutine_flow)
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 6  # 2 methods * 3 repeats


def test_stopping_condition(sample_controller: MockSubroutineController):
    sample_controller._stopping_condition = True
    sample_controller.run()
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 0  # No methods executed


def test_get_file_path_for_subroutine(
    sample_controller: MockSubroutineController, tmp_path: Path
):
    routine_name = "test_routine"
    filename_suffix = "_result.txt"
    sample_controller._routine_name_stack.append(
        routine_name
    )  # Set current routine name
    expected_path = tmp_path / f"{routine_name}{filename_suffix}"
    file_path = sample_controller.get_file_path_for_subroutine(filename_suffix)
    assert file_path == expected_path
