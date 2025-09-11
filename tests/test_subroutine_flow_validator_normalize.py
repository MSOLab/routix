import pytest

from src.routix.dynamic_data_object import DynamicDataObject
from src.routix.subroutine_flow_validator import (
    SubroutineFlowValidator,
)


# 간단한 Mock 클래스 정의
class MockDynamicDataObject(DynamicDataObject):
    def __init__(self, data):
        self.data = data

    def to_obj(self):
        return self.data


class MockControllerClass:
    def __init__(self):
        self.some_method_called = False
        self.another_method_called = False

    def some_method(self):
        self.some_method_called = True

    def another_method(self):
        self.another_method_called = True


@pytest.fixture
def mock_controller_class():
    return MockControllerClass()


@pytest.fixture
def validator(mock_controller_class):
    return SubroutineFlowValidator(mock_controller_class)


def test_normalize_key_coercion_and_sequence(validator: SubroutineFlowValidator):
    # dict with mixed key types, tuple in sequence
    src = MockDynamicDataObject({"a": 1, 2: "num_key", (1, 2): [1, 2]})
    norm = validator.normalize(src)
    assert isinstance(norm, dict)
    assert norm["a"] == 1
    # numeric key should be coerced to string
    assert norm["2"] == "num_key"
    # tuple key coerced via str()
    assert norm[str((1, 2))] == [1, 2]


def test_normalize_tuple_to_list(validator: SubroutineFlowValidator):
    src = MockDynamicDataObject((1, (2, 3)))
    norm = validator.normalize(src)
    assert norm == [1, [2, 3]]


def test_normalize_cycle_detection(validator: SubroutineFlowValidator):
    d = {}
    d["self"] = d
    src = MockDynamicDataObject(d)
    norm = validator.normalize(src)
    assert "self" in norm
    assert isinstance(norm["self"], str) and norm["self"].startswith("<cycle:")


def test_normalize_to_obj_failure_propagates(validator: SubroutineFlowValidator):
    class BadDDO(DynamicDataObject):
        def __init__(self):
            # satisfy base constructor which requires a dict
            super().__init__({})

        def to_obj(self):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        validator.normalize(BadDDO())


def test_fill_method_defaults_adds_default_for_missing_kwarg():
    class C:
        def solve_base_cp_model(self, computational_time, solver_thread_cnt, is_initial_solution=False, draw_gantt=False):
            return None

    validator = SubroutineFlowValidator(C)
    step = {"method": "solve_base_cp_model", "computational_time": 10.0, "solver_thread_cnt": 8, "is_initial_solution": True}
    filled = validator._fill_method_defaults(step)
    assert filled["method"] == "solve_base_cp_model"
    assert filled["computational_time"] == 10.0
    assert filled["solver_thread_cnt"] == 8
    assert filled["is_initial_solution"] is True
    # draw_gantt should be added with default False
    assert "draw_gantt" in filled and filled["draw_gantt"] is False


def test_fill_method_defaults_preserves_provided_value():
    class C:
        def solve_base_cp_model(self, computational_time, solver_thread_cnt, is_initial_solution=False, draw_gantt=False):
            return None

    validator = SubroutineFlowValidator(C)
    step = {"method": "solve_base_cp_model", "computational_time": 5.0, "solver_thread_cnt": 4, "draw_gantt": True}
    filled = validator._fill_method_defaults(step)
    # provided draw_gantt True should be preserved
    assert filled["draw_gantt"] is True


def test_fill_method_defaults_raises_for_unknown_method():
    class C:
        def foo(self):
            pass

    validator = SubroutineFlowValidator(C)
    with pytest.raises(ValueError):
        validator._fill_method_defaults({"method": "nonexistent"})


def test_fill_method_defaults_handles_keyword_only_defaults():
    class C:
        def step(self, a, *, kw_only=True):
            return None

    validator = SubroutineFlowValidator(C)
    filled = validator._fill_method_defaults({"method": "step", "a": 1})
    assert filled["a"] == 1
    assert "kw_only" in filled and filled["kw_only"] is True


def test_validate_subroutine_flow_prefix_success(validator: SubroutineFlowValidator):
    # resume is a prefix of current
    resume = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
            {"method": "another_method"},
        ]
    )
    current = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
            {"method": "another_method"},
            {"method": "some_method"},
        ]
    )
    idx = validator.validate_subroutine_flow_prefix(resume, current)
    assert idx == 2


def test_validate_subroutine_flow_prefix_mismatch_raises(
    validator: SubroutineFlowValidator,
):
    resume = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
            {"method": "some_method"},
        ]
    )
    current = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
            {"method": "another_method"},
        ]
    )
    with pytest.raises(ValueError) as exc:
        validator.validate_subroutine_flow_prefix(resume, current)
    assert "Subroutine flow prefix mismatch" in str(exc.value)


def test_validate_subroutine_flow_prefix_resume_longer_raises(
    validator: SubroutineFlowValidator,
):
    resume = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
            {"method": "another_method"},
            {"method": "some_method"},
        ]
    )
    current = MockDynamicDataObject.from_obj(
        [
            {"method": "some_method"},
        ]
    )
    with pytest.raises(ValueError) as exc:
        validator.validate_subroutine_flow_prefix(resume, current)
    assert "greater than current flow length" in str(exc.value)
