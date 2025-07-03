# routix

Routix is a lightweight Python toolkit for designing and executing structured algorithmic workflows.

## Key Features

- **Subroutine-based execution control**: Flexible workflow management via `SubroutineController`
  - **Context-aware logging**: Detailed logging with routine context traceability via `MethodContextManager`
- **Structured flow validation**: Validate workflow definitions with `SubroutineFlowValidator`
- **Dot-accessible configuration/data objects**: Manage hierarchical data and configuration with `DynamicDataObject`
- **Experiment timing**: Accurate experiment and subroutine timing with `ElapsedTimer` (start/stop, elapsed seconds, flexible checkpoints)
- **Metric time series management**: Collect and store time series data during experiments with `MetricTimeSeries` and `NamedTimeSeriesStore`
- **Experiment reporting and statistics**: Modular, SRP-compliant report system for experiment results
  - `SubroutineReport`: Immutable record of a subroutine run
  - `SubroutineReportRecorder`: Collects reports and method call counts
  - `SubroutineReportStatistics`: Computes statistics from collected reports and provides serialization (dict/JSON/YAML/CSV)
- **Extensible runner base classes**: Build custom workflow runners (single/multi/concurrent) in `src/routix/runner/`
- **Utilities**: Tools for saving results/configuration as YAML/JSON and more

## Subroutine Flow Data Format

Routix executes workflows defined as structured lists of dictionaries. Each step is clearly specified with method names and parameters.

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

See [`subroutine_flow_data.md`](./subroutine_flow_data.md) for details.

## Metric Time Series

- **MetricTimeSeries**: Manages (timestamp, value, note) time series data
- **NamedTimeSeriesStore**: Stores and manages multiple named MetricTimeSeries

This enables structured recording of experiment metrics, with export to YAML/JSON supported.

## Report System

Routix provides a modular, extensible reporting system for experiment results, replacing legacy summary classes with SRP-compliant components:

- **SubroutineReport**: Immutable record of a single subroutine execution (elapsed time, objective value, bound, progress log)
- **SubroutineReportRecorder**: Collects reports and tracks method call counts during workflow execution
- **SubroutineReportStatistics**: Computes statistics (min/max/first/last/total elapsed, improvement ratio, etc.) from collected reports, and provides serialization to dict, JSON, YAML, or CSV-friendly formats

This design enables flexible, testable, and maintainable experiment reporting and analytics.

## Runner Base Classes

- **SingleInstanceRunner**: Abstract base for running a single problem instance
- **MultiInstanceRunner**: Abstract base for running multiple instances in sequence
- **MultiInstanceConcurrentRunner**: Abstract base for running multiple instances concurrently (in parallel)

All runners are designed for subclassing and method overriding to fit your experiment patterns.

> **Note:** `InstanceSetRunner` is a deprecated name. Please use **`MultiInstanceRunner`** instead.

## Utilities

- `object_to_yaml`, `object_to_json`: Save experiment results and configuration to files
- Additional helpers for experiment management

## Testing

Unit tests for all major components are included in the `tests/` directory. Run all tests with pytest.

---
