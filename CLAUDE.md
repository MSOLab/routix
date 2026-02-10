# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Architecture Concepts

### Subroutine Flow System
Routix executes algorithmic workflows defined as structured lists of dictionaries (subroutine flows). Each step has a `method` key and optional `params` (or flat kwargs):

```yaml
- method: initialize
- method: repeat
  params:
    n_repeats: 3
    routine_data:
      - method: sample_method
        params:
          value: 42
```

Use `SubroutineFlowValidator` to statically validate flows before execution.

### Core Components

**SubroutineController**: Base class for executing subroutine flows. Manages:
- Method call context stack via `MethodContextManager` (generates hierarchical routine names like `1-init.2-repeat1.1-sample_method`)
- Elapsed time tracking via `ElapsedTimer`
- Stopping condition checking
- File path generation per subroutine via `get_file_path_for_subroutine()`

**SolutionManager**: Abstract base for managing optimization solutions:
- Tracks history of all subroutine executions (`SolutionRecord`)
- Maintains `best_solution`, `best_obj_value`, `best_obj_bound`
- Maintains `ref_solution`, `ref_obj_value` (current reference, e.g., for SA)
- Requires subclassing to implement `_get_obj_value()` and `_a_is_better_obj_value()`/`_a_is_better_obj_bound()`
- Key methods: `register()`, `get_best_solution()`, `has_best_solution()`, `get_ref_solution()`, `get_last_solution()`
- Utility methods: `best_obj_value_is_worse_than()`, `best_obj_bound_is_worse_than()` for comparison logic

**MetricTimeSeries** & **NamedTimeSeriesStore**: Time series management:
- `MetricTimeSeries`: Single named time series with timestamp-value pairs
- `NamedTimeSeriesStore`: Collection of multiple time series, keyed by name

### Report System
- **SubroutineReport**: Immutable dataclass recording elapsed time, objective value, and objective bound
- **SubroutineReportRecorder**: Collects `SubroutineReport` instances and tracks method call counts
- **SubroutineReportStatistics**: Computes aggregates (total time, min/max obj, improvement ratio) from reports
- Serialization methods for CSV/JSON/YAML export

### Runner Hierarchy
- **SingleInstanceRunner**: Execute workflow on one instance. Subclasses implement `get_controller()` and `post_run_process()`
- **MultiInstanceRunner**: Sequential execution of multiple instances
- **MultiInstanceConcurrentRunner**: Parallel execution using `ProcessPoolExecutor`
- **MultiScenarioRunner**: Run multiple scenarios (each with different flow/config) using a MultiInstanceRunner

### Type Variables
- `NumericT`: int or float
- `ParametersT`: Instance parameters
- `SolutionT`: Solution objects
- `SubroutineReportT`: SubroutineReport or subclass
- `StoppingCriteriaT`: StoppingCriteria or subclass
- `DynamicDataObjectT`: DynamicDataObject or subclass

## Common Commands

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_subroutine_controller.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/routix --cov-report=html
```

## Development Notes

- Python 3.11+ required
- Uses `hatchling` build system
- Dependencies are minimal (pytest, pyyaml for dev)
- All source code in `src/routix/`
- Tests in `tests/`
