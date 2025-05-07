import pytest

from src.clad.dynamic_data_object import DynamicDataObject
from src.clad.subroutine_controller import SubroutineController


class MockSubroutineController(SubroutineController):
    def is_stopping_condition(self) -> bool:
        return False

    def post_run_process(self):
        print("Post-run process executed.")

    def sample_method(self, param1, param2):
        print(f"Executing sample_method with param1={param1}, param2={param2}")


@pytest.fixture
def sample_controller():
    stopping_criteria = DynamicDataObject({"stop": False})
    subroutine_flow = DynamicDataObject.from_obj(
        [
            {"method_name": "sample_method", "param1": 1, "param2": 2},
            {"method_name": "sample_method", "param1": 3, "param2": 4},
        ]
    )
    controller = MockSubroutineController(
        "MockSubroutineController", stopping_criteria, subroutine_flow
    )
    return controller


def test_execute_routine(sample_controller):
    sample_controller.run()
    assert len(sample_controller._method_call_logs) == 2
    assert sample_controller._method_call_logs[0]["method_name"] == "sample_method"
    assert sample_controller._method_call_logs[1]["kwargs"] == {
        "param1": 3,
        "param2": 4,
    }


def test_call_method(sample_controller):
    sample_controller.call_method("sample_method", param1=10, param2=20)
    assert len(sample_controller._method_call_logs) == 1
    assert sample_controller._method_call_logs[0]["method_name"] == "sample_method"
    assert sample_controller._method_call_logs[0]["kwargs"] == {
        "param1": 10,
        "param2": 20,
    }


def test_repeat(sample_controller):
    sample_controller.repeat(3, sample_controller._subroutine_flow)
    assert len(sample_controller._method_call_logs) == 6  # 2 methods * 3 repeats
