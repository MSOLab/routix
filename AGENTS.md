# AGENTS.md

This file provides guidelines for Claude Code (and other AI agents) working on the `routix` project.

## Project Overview

`routix` is a lightweight Python toolkit for designing, executing, and analyzing structured algorithmic workflows. It is designed to systematically manage complex experiments and enhance reproducibility.

**Key Features:**

- **Subroutine-based Execution Control**: `SubroutineController` with detailed logging via `MethodContextManager`
- **Structured Flow Validation**: `SubroutineFlowValidator` for static validation of workflow definitions
- **Dynamic Data Objects**: `DynamicDataObject` for dot-accessible hierarchical data management
- **Accurate Time Measurement**: `ElapsedTimer` for experiment/subroutine timing
- **Time Series Data Management**: `MetricTimeSeries` and `NamedTimeSeriesStore` for metrics collection
- **Solution Management**: `SolutionManager` for tracking incumbent solutions during optimization
- **Modular Report System**: `SubroutineReport`, `SubroutineReportRecorder`, `SubroutineReportStatistics`, and `SubroutineReportStatisticsSerializer`
- **Extensible Runners**: `SingleInstanceRunner`, `MultiInstanceRunner`, `MultiInstanceConcurrentRunner`, `MultiScenarioRunner`

## Development Environment

- **Python Version**: >= 3.11
- **Testing Framework**: pytest
- **Dependencies**: pyyaml for YAML I/O

### Installation

```bash
pip install -e .
```

### Running Tests

```bash
uv run pytest
```

Tests are located in the `tests/` directory and cover all major components.

## Code Structure and Architecture

### Subroutine Flow Data Format

Workflows are defined as structured lists of dictionaries. Each step specifies a `method` name and optional `params`:

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

See [`subroutine_flow_data.md`](./subroutine_flow_data.md) for full details.

### Runner Architecture

The framework follows the **Single Responsibility Principle (SRP)** with a bottom-up data pipeline:

1. **`SubroutineController`**: Executes the algorithm, records raw data into `SubroutineReportRecorder`
2. **`SingleInstanceRunner`**: Orchestrates single runs, creates statistics, saves instance-specific outputs
3. **`MultiInstanceRunner`**: Aggregates statistics across multiple instances
4. **`MultiScenarioRunner`**: Aggregates results across different experimental scenarios

See [`src/routix/runner/README.md`](./src/routix/runner/README.md) for detailed architecture documentation.

### Execution Modes

Runners support explicit execution modes via `RunMode` enum:

- `RunMode.FULL_RUN`: Execute algorithm + post-process
- `RunMode.POST_PROCESS_ONLY`: Skip execution, only post-process existing data

## File I/O Utilities

- **`dump_json`**: Serialize Python objects to JSON
- **`init_timestamped_working_dir`**: Create timestamped directories for experiment outputs
- **`load_yaml` / `dump_yaml`**: YAML utilities with tuple key support

## Code Conventions

### Naming Conventions

- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use clear, descriptive names

### Design Principles

- Follow the **Single Responsibility Principle** in class design
- Co-locate related code; use the existing module structure as a guide
- Write tests for all new functionality

## File Organization

- **Source code**: `src/routix/`
- **Tests**: `tests/`
- **I/O utilities**: `src/routix/io/`
- **Report system**: `src/routix/report/`
- **Runner classes**: `src/routix/runner/`

## Common Commands

- Run all tests: `uv run pytest`
- Run specific test file: `uv run pytest tests/test_<filename>.py`
- Run specific test: `uv run pytest -k "<test_name>"`

## Pull Request Guidelines

- Run tests before committing - all tests must pass
- Ensure code follows existing patterns and conventions
- Update tests for any new or modified functionality
- PR title format: `[<module_name>] <description>`

## Important Notes

- **Test-Driven Development** - write or update tests when adding/modifying functionality
- **Reproducibility** - ensure experiments are reproducible with proper logging and output serialization
