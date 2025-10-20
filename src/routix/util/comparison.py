import math

from ..type_defs import NumericT

REL_TOL = 1e-9
ABS_TOL = 0.0


def float_equals(
    a: NumericT, b: NumericT, rel_tol: float | None = None, abs_tol: float | None = None
) -> bool:
    """Check if two floating-point numbers are approximately equal.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float | None, optional): Relative tolerance for comparison.
            Defaults to REL_TOL.
        abs_tol (float | None, optional): Absolute tolerance for comparison.
            Defaults to ABS_TOL.

    Returns:
        bool: True if the numbers are approximately equal, False otherwise.
    """
    rel_tol = REL_TOL if rel_tol is None else rel_tol
    abs_tol = ABS_TOL if abs_tol is None else abs_tol
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def float_a_leq_b(
    a: NumericT, b: NumericT, rel_tol: float | None = None, abs_tol: float | None = None
) -> bool:
    """Check if a is less than or approximately equal to b.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float | None, optional): Relative tolerance for comparison.
            Defaults to REL_TOL.
        abs_tol (float | None, optional): Absolute tolerance for comparison.
            Defaults to ABS_TOL.

    Returns:
        bool: True if a is less than or approximately equal to b, False otherwise.
    """
    rel_tol = REL_TOL if rel_tol is None else rel_tol
    abs_tol = ABS_TOL if abs_tol is None else abs_tol
    return a < b or float_equals(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def float_a_stl_b(
    a: NumericT, b: NumericT, rel_tol: float | None = None, abs_tol: float | None = None
) -> bool:
    """Check if a is strictly less than b, considering floating-point precision.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float | None, optional): Relative tolerance for comparison.
            Defaults to REL_TOL.
        abs_tol (float | None, optional): Absolute tolerance for comparison.
            Defaults to ABS_TOL.

    Returns:
        bool: True if a is strictly less than b, False otherwise.
    """
    rel_tol = REL_TOL if rel_tol is None else rel_tol
    abs_tol = ABS_TOL if abs_tol is None else abs_tol
    return a < b and not float_equals(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
