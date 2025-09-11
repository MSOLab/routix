import math

from ..type_defs import NumericT


def float_equals(
    a: NumericT, b: NumericT, rel_tol: float = 1e-9, abs_tol: float = 0.0
) -> bool:
    """Check if two floating-point numbers are approximately equal.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float, optional): Relative tolerance for comparison. Defaults to 1e-9.
        abs_tol (float, optional): Absolute tolerance for comparison. Defaults to 0.0.

    Returns:
        bool: True if the numbers are approximately equal, False otherwise.
    """
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def float_a_leq_b(
    a: NumericT, b: NumericT, rel_tol: float = 1e-9, abs_tol: float = 0.0
) -> bool:
    """Check if a is less than or approximately equal to b.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float, optional): Relative tolerance for comparison. Defaults to 1e-9.
        abs_tol (float, optional): Absolute tolerance for comparison. Defaults to 0.0.

    Returns:
        bool: True if a is less than or approximately equal to b, False otherwise.
    """
    return a < b or float_equals(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def float_a_stl_b(
    a: NumericT, b: NumericT, rel_tol: float = 1e-9, abs_tol: float = 0.0
) -> bool:
    """Check if a is strictly less than b, considering floating-point precision.

    Args:
        a (NumericT): First number to compare.
        b (NumericT): Second number to compare.
        rel_tol (float, optional): Relative tolerance for comparison. Defaults to 1e-9.
        abs_tol (float, optional): Absolute tolerance for comparison. Defaults to 0.0.

    Returns:
        bool: True if a is strictly less than b, False otherwise.
    """
    return a < b and not float_equals(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
