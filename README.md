# routix

Routix is a lightweight Python toolkit for designing and executing structured algorithmic workflows.

It provides:

- Subroutine-based execution control (`SubroutineController`)
- Structured flow validation (`SubroutineFlowValidator`)
- Dot-accessible configuration trees (`DynamicDataObject`)
- Logging with routine-context traceability
- Experiment summary and timing support

## Subroutine Flow Data Format

Routix executes algorithmic workflows based on a structured and validated subroutine flow.
Each step in the flow is represented by a dictionary with clearly defined keys,
enabling modular orchestration, logging, and reproducibility.

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

For more details, refer to [subroutine_flow_data.md](./subroutine_flow_data.md).
