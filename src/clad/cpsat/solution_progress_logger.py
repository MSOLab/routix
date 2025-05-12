from typing import Optional

from ortools.sat.python import cp_model

from ..routix import ElapsedTimer


class SolutionProgressLogger(cp_model.CpSolverSolutionCallback):
    """
    A lightweight logger for tracking the progress of solution discovery
    during CP-SAT solving.

    This class is designed to be used as a callback with the OR-Tools CpSolver.
    It logs a timestamped record of each feasible solution found, capturing:

    - Elapsed time since solving began
    - Objective value of the current solution
    - Best known objective bound at that moment

    The logger does **not** analyze or interpret results.
    It only accumulates raw progress data, which can be retrieved later
    (e.g., for plotting, reporting, or summary generation).

    Example usage:
        >>> logger = SolutionProgressLogger(timer)
        >>> solver.SolveWithSolutionCallback(model, logger)
        >>> progress = logger.get_log()
    """

    __elapsed_timer: ElapsedTimer
    __log: list[tuple[float, float, float]]
    __print_on_solution_callback: bool

    def __init__(
        self,
        elapsed_timer: Optional[ElapsedTimer] = None,
        print_on_solution_callback: bool = False,
    ) -> None:
        super().__init__()
        self.__log = []
        if elapsed_timer is None:
            self.__elapsed_timer = ElapsedTimer()
            self.__elapsed_timer.set_start_time_as_now()
        else:
            self.__elapsed_timer = elapsed_timer
        self.__print_on_solution_callback = print_on_solution_callback

    def is_verbose(self) -> bool:
        """
        Returns:
            bool: True if the logger prints on each solution callback.
        """
        return self.__print_on_solution_callback

    def on_solution_callback(self) -> None:
        elapsed = self.__elapsed_timer.get_elapsed_sec()
        objective = self.ObjectiveValue()
        best_bound = self.BestObjectiveBound()
        self.__log.append((elapsed, objective, best_bound))
        if self.__print_on_solution_callback:
            print(
                f"Time: {elapsed:.2f} sec"
                f", Objective: {objective}, Best Bound: {best_bound}"
            )

    def get_log(self) -> list[tuple[float, float, float]]:
        """Returns the log list.

        Returns:
            list[tuple[float, float, float]]: a list of tuples
                containing (elapsed time, objective value, best bound)
        """
        return self.__log.copy()
