"""Packaging contract tests (docs/20260702_laadi_plan.md §3.1)."""

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_pyyaml_declared_as_runtime_dependency():
    """routix imports yaml at runtime (routix.io.yaml, routix.util.concurrent),
    so pyyaml must be declared in [project].dependencies — otherwise a clean
    install fails on import."""
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    assert any(d.lower().replace("-", "").startswith("pyyaml") for d in deps)
