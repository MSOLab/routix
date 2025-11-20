import pytest

from src.routix.constants import SubroutineFlowKeys
from src.routix.dynamic_data_object import DynamicDataObject
from src.routix.subroutine_flow_validator import (
    SubroutineFlowValidator,
    is_static_or_instance_method,
    get_list_of_missing_required_arguments,
)


# Simple Mock class definition
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


def test_validate_valid_flow(validator: SubroutineFlowValidator):
    # 유효한 DynamicDataObject 생성
    valid_flow = MockDynamicDataObject({SubroutineFlowKeys.METHOD: "some_method"})

    # 예외가 발생하지 않는지 확인
    assert validator.validate(valid_flow)


def test_validate_invalid_flow_missing_method_name(validator: SubroutineFlowValidator):
    # "method" 키가 없는 DynamicDataObject 생성
    invalid_flow = MockDynamicDataObject({})

    with pytest.raises(ValueError, match=f"Missing {SubroutineFlowKeys.METHOD}"):
        validator.validate(invalid_flow)


def test_validate_invalid_flow_nonexistent_method(validator: SubroutineFlowValidator):
    # 존재하지 않는 메서드를 가진 DynamicDataObject 생성
    invalid_flow = MockDynamicDataObject(
        {SubroutineFlowKeys.METHOD: "nonexistent_method"}
    )

    with pytest.raises(ValueError, match="Method 'nonexistent_method' not found"):
        validator.validate(invalid_flow)


def test_validate_invalid_flow_non_callable_method(
    validator: SubroutineFlowValidator, mock_controller_class: MockControllerClass
):
    # create a DynamicDataObject with a non-callable attribute
    setattr(mock_controller_class, "non_callable_method", "not_callable")
    invalid_flow = MockDynamicDataObject(
        {SubroutineFlowKeys.METHOD: "non_callable_method"}
    )

    with pytest.raises(
        ValueError, match="Method 'non_callable_method' is not callable"
    ):
        validator.validate(invalid_flow)


def test_explain_valid_flow(validator: SubroutineFlowValidator):
    # create a valid DynamicDataObject
    valid_flow = MockDynamicDataObject({SubroutineFlowKeys.METHOD: "some_method"})

    result = validator.explain(valid_flow)
    assert result == "✅ Flow is valid."


def test_explain_invalid_flow(validator: SubroutineFlowValidator):
    # create an invalid DynamicDataObject
    invalid_flow = MockDynamicDataObject({})

    result = validator.explain(invalid_flow)
    assert "❌ Flow is invalid" in result


def test_is_static_or_instance_method_variants():
    class CallableObj:
        def __call__(self):
            pass

    class C:
        def inst(self):
            pass

        @staticmethod
        def stat():
            pass

        @classmethod
        def cm(cls):
            pass

        @property
        def prop(self):
            return 1

        callable_attr = CallableObj()

    assert is_static_or_instance_method(C, "inst") is True
    assert is_static_or_instance_method(C, "stat") is True
    # According to the docstring, classmethods should be treated as invalid
    assert is_static_or_instance_method(C, "cm") is False
    assert is_static_or_instance_method(C, "prop") is False
    # callable attribute (object with __call__) should be considered valid
    assert is_static_or_instance_method(C, "callable_attr") is True


def test_get_list_of_missing_required_arguments():
    class Ctrl:
        def method(self, a, b=2, *, c):
            return None

    # kwargs provided only for 'a' -> 'c' is still missing
    missing = get_list_of_missing_required_arguments(
        Ctrl, "method", {"a": MockDynamicDataObject(1)}
    )
    assert missing == ["c"]
