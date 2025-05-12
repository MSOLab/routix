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


def test_execute_routine(sample_controller: SubroutineController):
    sample_controller.run()
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 2
    assert method_call_log[0]["method_name"] == "sample_method"
    assert method_call_log[1]["kwargs"] == {
        "param1": 3,
        "param2": 4,
    }


def test_call_method(sample_controller: SubroutineController):
    sample_controller.call_method("sample_method", param1=10, param2=20)
    method_call_log = sample_controller.get_method_call_log()
    assert len(method_call_log) == 1
    assert method_call_log[0]["method_name"] == "sample_method"
    assert method_call_log[0]["kwargs"] == {
        "param1": 10,
        "param2": 20,
    }


@pytest.fixture
def sample_repeat_controller():
    stopping_criteria = DynamicDataObject({"stop": False})
    subroutine_flow = DynamicDataObject.from_obj(
        {
            "method_name": "repeat",
            "n_repeats": 3,
            "routine_data": [
                {"method_name": "sample_method", "param1": 1, "param2": 2},
                {"method_name": "sample_method", "param1": 3, "param2": 4},
            ],
        }
    )
    controller = MockSubroutineController(
        "MockSubroutineController", stopping_criteria, subroutine_flow
    )
    return controller


def test_repeat(sample_repeat_controller: SubroutineController):
    sample_repeat_controller.run()
    method_call_log = sample_repeat_controller.get_method_call_log()
    assert len(method_call_log) == 7  # 1(repeat) + 2 methods * 3 repeats
