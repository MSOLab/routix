# Routix Runner Architecture and Best Practices

This document outlines the design philosophy, responsibilities, and best practices for the `Runner` classes within the Routix framework. The core principle guiding this architecture is the **Single Responsibility Principle (SRP)**.

## 1. Core Principle: Single Responsibility Principle (SRP)

Each class in the `routix.runner` module has a single, well-defined responsibility. This separation of concerns makes the framework modular, testable, and easy to extend.

- **`SubroutineController`**: The **Algorithm Executor**. Its sole responsibility is to execute the optimization algorithm and record raw data (e.g., objective values, timestamps) into a `SubroutineReportRecorder`. It does not handle file I/O, statistical analysis, or visualization.

- **`SingleInstanceRunner`**: The **Orchestrator and Reporter**. It orchestrates a single run for one problem instance. Its responsibilities are:
    1. Initialize and run the `SubroutineController`.
    2. After the run, create a `SubroutineReportStatistics` object from the controller's raw data recorder.
    3. Generate and save all detailed, instance-specific outputs (e.g., solution files, Gantt charts, progress plots, individual summary logs).

- **`MultiInstanceRunner`**: The **Instance-level Aggregator**. It manages the execution of multiple `SingleInstanceRunner`s for a single scenario. Its responsibilities are:
    1. Run multiple instances, collecting the `SubroutineReportStatistics` object from each.
    2. Aggregate these statistics to create a comprehensive summary report for the entire scenario (e.g., `scenario_summary.csv`).

- **`MultiScenarioRunner`**: The **Scenario-level Aggregator**. It manages the execution of multiple `MultiInstanceRunner`s, each representing a different experimental scenario. Its responsibilities are:
    1. Run multiple scenarios, collecting the summary data (e.g., a pandas DataFrame) from each.
    2. Aggregate these summaries to create a final, comparative analysis report across all scenarios (e.g., `all_scenarios_comparison.csv`).

---

## 2. Data Flow: A Bottom-Up Pipeline

The framework is designed around a bottom-up data pipeline. Raw data is generated at the lowest level and is progressively aggregated and transformed as it moves up to higher-level runners.

1. **`SubroutineController`**: Produces a `SubroutineReportRecorder` (containing raw log data) and a final `solution` object.

2. **`SingleInstanceRunner`**:
    - **Input**: Takes the `report_recorder` from the controller.
    - **Process**: Creates a `SubroutineReportStatistics` object.
    - **Output**: Saves detailed files (`gantt.png`, `solution.yaml`, etc.).
    - **Returns**: The `SubroutineReportStatistics` object.

3. **`MultiInstanceRunner`**:
    - **Input**: Collects a list of `SubroutineReportStatistics` objects from its child runners.
    - **Process**: Aggregates these statistics into a summary (e.g., a pandas DataFrame).
    - **Output**: Saves the scenario-level summary (`scenario_summary.csv`).
    - **Returns**: The aggregated summary DataFrame.

4. **`MultiScenarioRunner`**:
    - **Input**: Collects a list of summary DataFrames from its child runners.
    - **Process**: Concatenates the DataFrames to create a final comparison table.
    - **Output**: Saves the final, cross-scenario report (`all_scenarios_summary.csv`).
    - **Returns**: The final, combined DataFrame.

---

## 3. Execution Modes: `RunMode` Enum

To handle different use cases like full runs versus post-processing, runners should support explicit **Execution Modes**. This is preferable to boolean flags like `skip_run_do_post_process` as it is more explicit and extensible.

### Proposed `RunMode` Enum

```python
from enum import Enum, auto

class RunMode(Enum):
    """Defines the execution mode for a Runner."""
    FULL_RUN = auto()          # Execute the algorithm and then post-process the results.
    POST_PROCESS_ONLY = auto() # Skip algorithm execution and only run the post-processing step on existing data.
    # Future modes could be added, e.g., VALIDATE_ONLY
```

### Implementation in `SingleInstanceRunner`

The `run` method should be adapted to handle these modes:

```python
# In SingleInstanceRunner
def run(self, mode: RunMode = RunMode.FULL_RUN):
    """
    Runs the instance based on the specified execution mode.
    """
    if mode == RunMode.FULL_RUN:
        # 1. Execute the algorithm
        self.ctrlr = self.get_controller()
        self.ctrlr.set_working_dir(self.working_dir)
        self.ctrlr.run()

        # 2. Post-process from in-memory data
        self.post_run_process(run_mode=mode)

    elif mode == RunMode.POST_PROCESS_ONLY:
        # Skip execution, directly call post-processing
        self.post_run_process(run_mode=mode)

    else:
        raise ValueError(f"Unsupported run mode: {mode}")

def post_run_process(self, run_mode: RunMode):
    """
    Analyzes results and generates outputs. The source of the data depends on the run_mode.
    """
    # 1. Load data based on the mode
    if run_mode == RunMode.FULL_RUN:
        # Data comes from the controller that just ran
        stats = SubroutineReportStatistics(self.ctrlr.report_recorder)
        solution = self.ctrlr.get_incumbent_solution_dict()
    else: # POST_PROCESS_ONLY
        # Data is loaded from files
        stats = self.load_statistics_from_file()
        solution = self.load_solution_from_file()

    # 2. Perform analysis and save outputs (this part is now independent of the data source)
    self.generate_summary_file(stats)
    self.draw_gantt_chart(solution)
    # ...
```

### Benefits of this Approach

- **Clarity**: The code's intent becomes self-documenting (`mode=RunMode.POST_PROCESS_ONLY` is clearer than a boolean flag).
- **Maintainability**: The logic for execution and post-processing is cleanly separated.
- **Extensibility**: New modes can be added easily without refactoring existing `if/else` logic.
- **Robustness**: `post_run_process` can focus solely on its core responsibility of analysis and reporting, regardless of where the data comes from.
