from dataclasses import dataclass

import pytest

from src.routix.report.subroutine_report import SubroutineReport
from src.routix.solution_manager import SolutionManager


@dataclass
class SimpleSolution:
    """Simple solution object for testing."""
    value: float


class SimpleSolutionManager(SolutionManager[SubroutineReport, SimpleSolution]):
    """Concrete implementation of SolutionManager for testing."""

    def _get_obj_value(self, solution: SimpleSolution) -> float:
        return solution.value

    def _a_is_better_obj_value(self, value_a: float, value_b: float | None) -> bool:
        # Minimization problem
        if value_b is None:
            return True
        return value_a < value_b

    def _a_is_better_obj_bound(self, bound_a: float, bound_b: float | None) -> bool:
        # Minimization problem
        if bound_b is None:
            return True
        return bound_a < bound_b


@pytest.fixture
def manager() -> SimpleSolutionManager:
    return SimpleSolutionManager()


@pytest.fixture
def report1() -> SubroutineReport:
    return SubroutineReport(elapsed_time=1.0, obj_value=100.0, obj_bound=90.0)


@pytest.fixture
def report2() -> SubroutineReport:
    return SubroutineReport(elapsed_time=2.0, obj_value=80.0, obj_bound=75.0)


@pytest.fixture
def report3() -> SubroutineReport:
    return SubroutineReport(elapsed_time=3.0, obj_value=120.0, obj_bound=110.0)


class TestSolutionManagerInit:
    def test_history_initialized_empty(self, manager: SimpleSolutionManager):
        assert manager.history == []

    def test_best_solution_initialized_none(self, manager: SimpleSolutionManager):
        assert manager.best_solution is None

    def test_best_obj_value_initialized_none(self, manager: SimpleSolutionManager):
        assert manager.best_obj_value is None

    def test_best_obj_bound_initialized_none(self, manager: SimpleSolutionManager):
        assert manager.best_obj_bound is None

    def test_ref_solution_initialized_none(self, manager: SimpleSolutionManager):
        assert manager.ref_solution is None

    def test_ref_obj_value_initialized_none(self, manager: SimpleSolutionManager):
        assert manager.ref_obj_value is None


class TestRegister:
    def test_register_updates_history(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        assert len(manager.history) == 1
        assert manager.history[0].report == report1
        assert manager.history[0].solution == solution

    def test_register_none_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        result = manager.register(report1, None)

        assert len(manager.history) == 1
        assert result is False
        assert manager.best_solution is None

    def test_register_updates_best_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        assert manager.best_solution == solution
        assert manager.best_obj_value == 100.0

    def test_register_updates_best_obj_bound(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        assert manager.best_obj_bound == 90.0

    def test_register_improved_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport, report2: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution2 = SimpleSolution(value=80.0)

        manager.register(report1, solution1)
        manager.register(report2, solution2)

        assert manager.best_solution == solution2
        assert manager.best_obj_value == 80.0

    def test_register_returns_true_on_best_update(self, manager: SimpleSolutionManager, report1: SubroutineReport, report2: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution2 = SimpleSolution(value=80.0)

        result1 = manager.register(report1, solution1)
        result2 = manager.register(report2, solution2)

        assert result1 is True
        assert result2 is True

    def test_register_returns_false_when_not_improved(self, manager: SimpleSolutionManager, report1: SubroutineReport, report3: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution3 = SimpleSolution(value=120.0)

        manager.register(report1, solution1)
        result = manager.register(report3, solution3)

        assert result is False
        assert manager.best_solution == solution1
        assert manager.best_obj_value == 100.0

    def test_register_force_update_ref_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport, report3: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution3 = SimpleSolution(value=120.0)

        manager.register(report1, solution1)
        manager.register(report3, solution3, force_update_ref_sol=True)

        # ref_solution should be updated even though it's not better
        assert manager.ref_solution == solution3
        assert manager.ref_obj_value == 120.0

    def test_register_without_force_update_ref_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport, report3: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution3 = SimpleSolution(value=120.0)

        manager.register(report1, solution1)
        manager.register(report3, solution3, force_update_ref_sol=False)

        # ref_solution should NOT be updated since it's not better
        assert manager.ref_solution == solution1
        assert manager.ref_obj_value == 100.0

    def test_register_raises_on_inconsistent_obj_value(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=999.0)  # Different from report.obj_value (100.0)

        with pytest.raises(ValueError, match="Inconsistent objective value"):
            manager.register(report1, solution)


class TestGetters:
    def test_get_best_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport, report2: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution2 = SimpleSolution(value=80.0)

        manager.register(report1, solution1)
        manager.register(report2, solution2)

        assert manager.get_best_solution() == solution2

    def test_get_best_solution_empty(self, manager: SimpleSolutionManager):
        assert manager.get_best_solution() is None

    def test_has_best_solution_true(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        assert manager.has_best_solution() is True

    def test_has_best_solution_false(self, manager: SimpleSolutionManager):
        assert manager.has_best_solution() is False

    def test_get_ref_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        assert manager.get_ref_solution() == solution

    def test_get_ref_solution_empty(self, manager: SimpleSolutionManager):
        assert manager.get_ref_solution() is None

    def test_get_last_solution(self, manager: SimpleSolutionManager, report1: SubroutineReport, report2: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)
        solution2 = SimpleSolution(value=80.0)

        manager.register(report1, solution1)
        manager.register(report2, solution2)

        assert manager.get_last_solution() == solution2

    def test_get_last_solution_with_none_in_between(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution1 = SimpleSolution(value=100.0)

        manager.register(report1, solution1)
        manager.register(report1, None)  # No solution
        manager.register(report1, solution1)  # Same solution again

        assert manager.get_last_solution() == solution1

    def test_get_last_solution_empty(self, manager: SimpleSolutionManager):
        assert manager.get_last_solution() is None

    def test_get_last_report(self, manager: SimpleSolutionManager, report1: SubroutineReport, report2: SubroutineReport):
        manager.register(report1, SimpleSolution(value=100.0))
        manager.register(report2, SimpleSolution(value=80.0))

        assert manager.get_last_report() == report2

    def test_get_last_report_empty(self, manager: SimpleSolutionManager):
        assert manager.get_last_report() is None


class TestBestObjValueIsWorseThan:
    def test_worse_value(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # 120.0 is worse than 100.0 (for minimization)
        assert manager.best_obj_value_is_worse_than(120.0) is True

    def test_better_value(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # 80.0 is better than 100.0 (for minimization), so not worse
        assert manager.best_obj_value_is_worse_than(80.0) is False

    def test_equal_value(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # Equal value is not worse
        assert manager.best_obj_value_is_worse_than(100.0) is False

    def test_no_best_yet(self, manager: SimpleSolutionManager):
        # No best solution yet, return True by convention
        assert manager.best_obj_value_is_worse_than(100.0) is True


class TestBestObjBoundIsWorseThan:
    def test_worse_bound(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # 120.0 is worse than 90.0 (for minimization bound)
        assert manager.best_obj_bound_is_worse_than(120.0) is True

    def test_better_bound(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # 70.0 is better than 90.0 (for minimization), so not worse
        assert manager.best_obj_bound_is_worse_than(70.0) is False

    def test_equal_bound(self, manager: SimpleSolutionManager, report1: SubroutineReport):
        solution = SimpleSolution(value=100.0)
        manager.register(report1, solution)

        # Equal bound is not worse
        assert manager.best_obj_bound_is_worse_than(90.0) is False

    def test_no_bound_yet(self, manager: SimpleSolutionManager):
        # No best bound yet, return True by convention
        assert manager.best_obj_bound_is_worse_than(90.0) is True
