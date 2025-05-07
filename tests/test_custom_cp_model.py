import pytest

from src.clad.cpsat.custom_cp_model import CustomCpModel
from src.clad.cpsat.status import CpSatStatus
from src.clad.elapsed_timer import ElapsedTimer


@pytest.fixture
def model():
    """Fixture to create a CustomCpModel instance."""
    return CustomCpModel()


def test_init_solver(model: CustomCpModel):
    model.init_solver(computational_time=10.0, n_threads=4)
    assert model.solver.parameters.max_time_in_seconds == 10.0
    assert model.solver.parameters.num_workers == 4


def test_solve_and_get_status(model: CustomCpModel):
    model.init_solver(computational_time=10.0, n_threads=4)
    status, elapsed_time, ub, lb = model.solve_and_get_status(
        computational_time=10.0, n_threads=4
    )
    assert isinstance(status, int)
    assert isinstance(elapsed_time, float)
    assert isinstance(ub, float)
    assert isinstance(lb, float)


def test_change_domain(model: CustomCpModel):
    var = model.new_int_var(0, 10, "test_var")
    model.change_domain(var, [5, 15])
    assert var.Proto().domain == [5, 15]


def test_is_maximize(model: CustomCpModel):
    with pytest.raises(RuntimeError, match="Objective function has not been set."):
        model.is_maximize()


def test_freeze_base_constraints(model: CustomCpModel):
    # Create integer variables
    x = model.new_int_var(0, 10, "x")
    y = model.new_int_var(0, 10, "y")

    # Add a constraint
    model.add(x + y <= 15)

    # Freeze base constraints
    model.freeze_base_constraints()

    # Assert that the number of base constraints is updated correctly
    assert model.num_base_constraints == 1


def test_delete_added_constraints(model: CustomCpModel):
    # Create integer variables
    x = model.new_int_var(0, 10, "x")
    y = model.new_int_var(0, 10, "y")

    # Add a base constraint and freeze it
    model.add(x + y <= 15)
    model.freeze_base_constraints()

    # Add additional constraints
    model.add(x - y >= 5)  # Added constraint 1
    model.add(x + 2 * y == 20)  # Added constraint 2

    # Delete added constraints
    model.delete_added_constraints()

    # Assert that only the base constraints remain
    assert model.get_next_constr_idx() == model.num_base_constraints


def test_solve_with_prog_logger(model: CustomCpModel):
    timer = ElapsedTimer()
    model.init_solver(computational_time=10.0, n_threads=4)
    model.init_callback(timer)

    # Example CP model by Google
    num_vals = 3
    x = model.new_int_var(0, num_vals - 1, "x")
    y = model.new_int_var(0, num_vals - 1, "y")
    z = model.new_int_var(0, num_vals - 1, "z")
    model.add(x != y)

    status, elapsed_time, ub, lb = model.solve_with_prog_logger(
        computational_time=10.0, n_threads=4, timer=timer
    )
    assert isinstance(status, int)
    assert isinstance(elapsed_time, float)
    assert isinstance(ub, float)
    assert isinstance(lb, float)
    if CpSatStatus.found_feasible_solution(status):
        print(f"x = {model.solver.value(x)}")
        print(f"y = {model.solver.value(y)}")
        print(f"z = {model.solver.value(z)}")
    else:
        print("No solution found.")
