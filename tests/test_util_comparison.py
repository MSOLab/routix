import pytest

from routix.util.comparison import (
    float_equals,
    float_a_leq_b,
    float_a_stl_b,
)


@pytest.mark.parametrize(
    "a,b,rel,abs,expected",
    [
        (1.0, 1.0, 1e-9, 0.0, True),
        (1.0, 1.0 + 1e-10, 1e-9, 0.0, True),
        (0.0, 1e-6, 1e-9, 1e-5, True),
        (0.0, 1e-6, 1e-9, 0.0, False),
        (1.0, 2.0, 1e-9, 0.0, False),
        (0.8, 0.7999999999999999, 1e-9, 0.0, True),  # edge case for floating point
    ],
)
def test_float_equals_various(a, b, rel, abs, expected):
    assert float_equals(a, b, rel_tol=rel, abs_tol=abs) is expected


def test_float_equals_nan():
    nan = float("nan")
    # math.isclose returns False if either argument is NaN
    assert float_equals(nan, nan) is False


@pytest.mark.parametrize(
    "a,b,rel,abs,expected",
    [
        (1.0, 2.0, 1e-9, 0.0, True),  # a < b
        (2.0, 2.0, 1e-9, 0.0, True),  # equal
        (2.0 + 1e-10, 2.0, 1e-9, 0.0, True),  # effectively equal within tol
        (3.0, 2.0, 1e-9, 0.0, False),
        (0.8, 0.7999999999999999, 1e-9, 0.0, True),  # edge case for floating point
    ],
)
def test_float_a_leq_b(a, b, rel, abs, expected):
    assert float_a_leq_b(a, b, rel_tol=rel, abs_tol=abs) is expected


@pytest.mark.parametrize(
    "a,b,rel,abs,expected",
    [
        (1.0, 2.0, 1e-9, 0.0, True),  # strictly less
        (2.0, 2.0, 1e-9, 0.0, False),  # equal -> not strictly less
        (2.0 - 1e-12, 2.0, 1e-9, 0.0, False),  # within tolerance -> not strictly less
        (3.0, 2.0, 1e-9, 0.0, False),
        (0.8, 0.7999999999999999, 1e-9, 0.0, False),  # edge case for floating point
    ],
)
def test_float_a_stl_b(a, b, rel, abs, expected):
    assert float_a_stl_b(a, b, rel_tol=rel, abs_tol=abs) is expected


def test_integer_inputs():
    # integers should work as well
    assert float_equals(1, 1) is True
    assert float_a_leq_b(1, 2) is True
    assert float_a_stl_b(1, 2) is True
