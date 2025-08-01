# routix

`routix` is a lightweight Python toolkit for designing, executing, and analyzing structured algorithmic workflows.
It is designed to systematically manage complex experiments and enhance reproducibility.

## Key Features

- **Subroutine-based Execution Control**: Flexibly manage workflows with `SubroutineController` and support detailed logging by tracking context with `MethodContextManager`.
- **Structured Flow Validation**: Validate workflow definitions in advance using `SubroutineFlowValidator`.
- **Dynamic Data Objects**: Conveniently manage hierarchical data and configurations as dot-accessible objects with `DynamicDataObject`.
- **Accurate Time Measurement**: Accurately measure and manage the execution time of experiments and each subroutine with `ElapsedTimer`.
- **Time Series Data Management**: Collect and store various metrics generated during experiments as time series data using `MetricTimeSeries` and `NamedTimeSeriesStore`.
- **Solution Management**: Systematically manage solutions found during the optimization process and track the incumbent solution with `SolutionManager`.
- **Experiment Reporting and Statistics**: A modular system to record, analyze, and serialize experiment results.
- **Extensible Runners**: Abstract base classes to easily implement various experimental patterns (e.g., single, multiple, concurrent execution).
- **File I/O Utilities**: Simplified serialization of Python objects to YAML or JSON, and creation of timestamped directories for experiment outputs.

## Subroutine Flow Data Format

`routix` executes workflows defined as a structured list of dictionaries. Each step is clearly specified with a method name and parameters.

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

For more details, see [`subroutine_flow_data.md`](./subroutine_flow_data.md).

## Report System

`routix` provides a modular and extensible reporting system designed with the Single Responsibility Principle in mind.

- **`SubroutineReport`**: An immutable `dataclass` that records the results of a single subroutine execution, including elapsed time, objective value, and objective bound.
- **`SubroutineReportRecorder`**: Collects `SubroutineReport` instances and tracks method call counts during a workflow run.
- **`SubroutineReportStatistics`**: Computes summary statistics (e.g., total time, best objective, improvement ratio) from the reports collected by a recorder.
- **`SubroutineReportStatisticsSerializer`**: Serializes a collection of `SubroutineReportStatistics` objects into various formats, including dictionaries, CSV, JSON, and YAML, making it easy to export and analyze results from multiple runs.

## Runner Base Classes

Build custom workflow runners by extending these abstract base classes to fit your experimental patterns.

- **`SingleInstanceRunner`**: The foundation for running a workflow on a single problem instance. Subclasses must implement `get_controller()` to set up the `SubroutineController` and `post_run_process()` to handle results.
- **`MultiInstanceRunner`**: Orchestrates running a set of instances sequentially. It uses a specified `SingleInstanceRunner` subclass for each instance.
- **`MultiInstanceConcurrentRunner`**: Extends `MultiInstanceRunner` to execute multiple instances in parallel using a process pool, significantly speeding up large-scale experiments.
- **`MultiScenarioRunner`**: Manages experiments across multiple scenarios, where each scenario may have a different configuration (e.g., a different subroutine flow). It uses a `MultiInstanceRunner` subclass to execute the instances within each scenario.

## File I/O Utilities

`routix` includes helper functions to streamline file I/O for experiments.

- **`object_to_yaml` / `object_to_json`**: Serialize Python objects (including those with `to_dict()` methods and `pathlib.Path` objects) into clean and readable YAML or JSON files.
- **`init_timestamped_working_dir`**: Creates a unique, timestamped directory for storing experiment outputs, helping to keep results organized.

## Installation

```bash
pip install routix
```

## Testing

Unit tests for all major components of the project are included in the `tests/` directory. You can run all tests using `pytest`.

```bash
pytest
```
