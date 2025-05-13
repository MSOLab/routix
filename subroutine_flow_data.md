# Subroutine Flow Data Format

Routix executes algorithmic workflows based on a structured and validated subroutine flow.
Each step in the flow is represented by a dictionary with clearly defined keys,
enabling modular orchestration, logging, and reproducibility.

## 📋 Example

```yaml
# my_flow.yaml
- method: initialize
- method: repeat
  params:
    n_repeats: 3
    routine_data:
      - method: sample_method
        params:
          value: 42
```

## 🧩 Flow Entry Format

Each step is expected to follow one of two forms:

### 1. Explicit form

```yaml
- method: sample_method
  params:
    value: 10
```

### 2. Flat form

```yaml
- method: sample_method
  value: 10
```

Both forms are interpreted equivalently.
The explicit form makes structure and validation clearer, especially for nested or complex configurations.

## ✅ Validation

All flows can be statically validated before execution using `SubroutineFlowValidator`.
Validation ensures:

- Required keys (`method`) are present
- The referenced method exists and is callable
- The provided arguments match the method signature
- Unexpected fields are caught early

## 🔍 Execution Semantics

- Each subroutine is invoked with a context-aware `routine_name` (e.g. `2_repeat2.1_sample_method`), which is automatically tracked.
- All logs, outputs, and artifacts are saved using this hierarchical naming convention for full traceability.
