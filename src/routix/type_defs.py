from enum import Enum, auto
from typing import TypeVar

NumericT = TypeVar("NumericT", int, float)
"""TypeVar for numeric types: int and float"""

ParametersT = TypeVar("ParametersT")
"""TypeVar for parameters, can be any type"""

SolutionT = TypeVar("SolutionT")
"""A generic type variable representing any solution object."""


class RunMode(Enum):
    """Defines the execution mode for a Runner."""

    FULL_RUN = auto()
    """Execute the algorithm and then post-process the results."""

    POST_PROCESS_ONLY = auto()
    """Skip algorithm execution and only run the post-processing step on existing data."""
