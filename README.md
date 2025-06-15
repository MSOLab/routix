# routix

Routix is a lightweight Python toolkit for designing and executing structured algorithmic workflows.

## Key Features

- **Subroutine-based execution control**: Flexible workflow management via `SubroutineController`
  - **Context-aware logging**: Detailed logging with routine context traceability via `MethodContextManager`
- **Structured flow validation**: Validate workflow definitions with `SubroutineFlowValidator`
- **Dot-accessible configuration/data objects**: Manage hierarchical data and configuration with `DynamicDataObject`
- **Experiment summary and timing**: Manage experiment results and timing with `ExperimentSummary`, `ElapsedTimer`, etc.
- **Extensible runner base classes**: Build custom workflow runners (single/multi/concurrent) in `src/routix/runner/`
- **Metric time series management**: Collect and store time series data during experiments with `MetricTimeSeries` and `NamedTimeSeriesStore`
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

## Runner Base Classes

- **SingleInstanceRunner**: Abstract base for running a single problem instance
- **MultiInstanceRunner**: Abstract base for running multiple instances in sequence
- **MultiInstanceConcurrentRunner**: Abstract base for running multiple instances concurrently (in parallel)

All runners are designed for subclassing and method overriding to fit your experiment patterns.

> **Note:** `InstanceSetRunner` is a deprecated name. Please use **`MultiInstanceRunner`** instead.

## Metric Time Series

- **MetricTimeSeries**: Manages (timestamp, value, note) time series data
- **NamedTimeSeriesStore**: Stores and manages multiple named MetricTimeSeries

This enables structured recording of experiment metrics, with export to YAML/JSON supported.

## Utilities

- `object_to_yaml`, `object_to_json`: Save experiment results and configuration to files
- Additional helpers for experiment management

## Testing

Unit tests for all major components are included in the `tests/` directory. Run all tests with pytest.

---
