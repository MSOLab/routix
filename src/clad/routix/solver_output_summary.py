from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SolverOutputSummary:
    """
    An immutable container for the result of a single solver run.

    Captures:
    - The final solver status (aligned with SolverStatus)
    - Total solving time in seconds
    - Final objective value, if a feasible solution was found
    - Best known bound at the time solving ended
    - An optional progress log of (time, objective, bound) entries

    This class does not mutate state and should be created immediately after solving,
    then passed to higher-level summary collectors (e.g., ExperimentSummary).
    """

    status: str
    """Final solver status."""
    elapsed_time: float
    """Solving time in seconds."""
    objective_value: Optional[float]
    """Objective value of final solution."""
    best_objective_bound: Optional[float]
    """Best bound returned by solver."""
    progress_log: Optional[list[tuple[float, float, float]]] = None
    """A list of tuples containing (elapsed time, objective value, best bound)."""

    def to_dict(self) -> dict:
        """Returns the summary as a serializable dictionary."""
        return {
            "status": self.status,
            "elapsed_time": self.elapsed_time,
            "objective_value": self.objective_value,
            "best_objective_bound": self.best_objective_bound,
            "progress_log": self.progress_log,
        }
