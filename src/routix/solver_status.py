from __future__ import annotations

from enum import Enum, unique


@unique
class SolverStatus(Enum):
    MODEL_INVALID = "MODEL_INVALID"
    INFEASIBLE = "INFEASIBLE"
    FEASIBLE = "FEASIBLE"
    OPTIMAL = "OPTIMAL"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def all_statuses(cls) -> set[SolverStatus]:
        """Returns a set of all defined solver statuses."""
        return set(cls)

    def is_model_invalid(self) -> bool:
        """Checks if the given status indicates an invalid model."""
        return self is SolverStatus.MODEL_INVALID

    def is_infeasible(self) -> bool:
        """Checks if the given status represents an infeasible solution."""
        return self is SolverStatus.INFEASIBLE

    def found_feasible_solution(self) -> bool:
        """Checks if a feasible solution was found based on the status."""
        return self in {SolverStatus.FEASIBLE, SolverStatus.OPTIMAL}

    def is_optimal_solution(self) -> bool:
        """Checks if the given status represents an optimal solution."""
        return self is SolverStatus.OPTIMAL

    def is_unknown(self) -> bool:
        """Checks if the given status is unknown."""
        return self is SolverStatus.UNKNOWN

    @classmethod
    def raise_if_not_feasible(cls, status: SolverStatus) -> None:
        """Raises an exception if the status indicates infeasibility."""
        if status not in cls.all_statuses():
            raise ValueError(f"Unrecognized status: {status}")
        elif status.is_model_invalid():
            raise ValueError("The model is invalid.")
        elif status.is_infeasible():
            raise ValueError("The problem is infeasible.")
        elif status.is_unknown():
            raise ValueError("The status is unknown.")

    def __str__(self):
        return self.value
