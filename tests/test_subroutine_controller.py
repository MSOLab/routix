import unittest

from clad.dynamic_data_object import DynamicDataObject
from clad.subroutine_controller import SubroutineController


class DummySubController(SubroutineController):
    def __init__(
        self,
        stopping_criteria: DynamicDataObject,
        subroutine_flow: DynamicDataObject,
        stopping_flag: bool = False,
    ):
        super().__init__(stopping_criteria, subroutine_flow)
        self.stopping_flag = stopping_flag

    def is_stopping_condition(self) -> bool:
        return self.stopping_flag

    def test_routine(self, **kwargs):
        # This routine does not record extra data;
        # the base class _called_routines captures the call details.
        pass


class TestSubroutineController(unittest.TestCase):
    """Tests verify that:
    - A single routine is executed correctly and its keyword arguments are recorded in _called_routines.
    - A sequence (list) of routines is handled appropriately.
    - An AttributeError is raised when the routine lacks a "name" attribute.
    - An AttributeError is raised when the routine name does not match any method.
    - A true stopping condition prevents execution (and recording) of any routine.
    """  # noqa: E501

    def test_run_single_routine(self):
        # Test a single routine execution with stopping condition set to False.
        routine = DynamicDataObject({"name": "test_routine", "value": 100})
        controller = DummySubController(
            stopping_criteria=DynamicDataObject({}),
            subroutine_flow=routine,
            stopping_flag=False,
        )
        controller.run()
        # Verify that the routine call was recorded via _called_routines.
        self.assertEqual(len(controller._called_routines), 1)
        recorded = controller._called_routines[0]
        self.assertEqual(recorded.get("value"), 100)
        self.assertEqual(recorded.get("name"), "test_routine")

    def test_run_sequence_routine(self):
        # Test executing a sequence of routines.
        routine1 = DynamicDataObject({"name": "test_routine", "value": 1})
        routine2 = DynamicDataObject({"name": "test_routine", "value": 2})
        routine_list = [routine1, routine2]
        controller = DummySubController(
            stopping_criteria=DynamicDataObject({}),
            subroutine_flow=routine_list,
            stopping_flag=False,
        )
        controller.run()
        # Verify that both routines were recorded.
        self.assertEqual(len(controller._called_routines), 2)
        self.assertEqual(controller._called_routines[0].get("value"), 1)
        self.assertEqual(controller._called_routines[1].get("value"), 2)

    def test_missing_name_attribute(self):
        # A routine without a 'name' attribute should raise an AttributeError.
        routine = DynamicDataObject({"value": 200})
        controller = DummySubController(
            stopping_criteria=DynamicDataObject({}),
            subroutine_flow=routine,
            stopping_flag=False,
        )
        with self.assertRaises(AttributeError) as context:
            controller.run()
        self.assertIn(
            "Subroutine data must have a 'name' attribute", str(context.exception)
        )

    def test_nonexistent_routine_method(self):
        # A routine with a 'name' that does not correspond to an existing method
        # should raise an AttributeError.
        routine = DynamicDataObject({"name": "nonexistent_method", "value": 300})
        controller = DummySubController(
            stopping_criteria=DynamicDataObject({}),
            subroutine_flow=routine,
            stopping_flag=False,
        )
        with self.assertRaises(AttributeError) as context:
            controller.run()
        self.assertIn(
            "SubroutineController has no attribute nonexistent_method",
            str(context.exception),
        )

    def test_stopping_condition_prevents_execution(self):
        # When is_stopping_condition returns True,
        # routine execution should be prevented.
        routine = DynamicDataObject({"name": "test_routine", "value": 400})
        controller = DummySubController(
            stopping_criteria=DynamicDataObject({}),
            subroutine_flow=routine,
            stopping_flag=True,  # stopping condition active
        )
        controller.run()
        self.assertEqual(len(controller._called_routines), 0)


if __name__ == "__main__":
    unittest.main()
