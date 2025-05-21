import pytest

from src.routix.experiment_summary import ExperimentSummary
from src.routix.solver_output_summary import SolverOutputSummary
from src.routix.solver_status import SolverStatus


def make_summary(status, obj):
    return SolverOutputSummary(
        status=status,
        elapsed_time=1.0,
        objective_value=obj,
        best_objective_bound=None,
    )


def test_improvement_ratio_minimize():
    es = ExperimentSummary("test")
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 200))
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 100))
    assert es.get_improvement_ratio(is_maximize=False) == pytest.approx(0.5)


def test_improvement_ratio_maximize():
    es = ExperimentSummary("test")
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 100))
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 150))
    assert es.get_improvement_ratio(is_maximize=True) == pytest.approx(0.5)


def test_zero_first_objective_returns_none():
    es = ExperimentSummary("test")
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 0))
    es.add_run_summary(make_summary(SolverStatus.FEASIBLE, 10))
    assert es.get_improvement_ratio(is_maximize=True) is None
