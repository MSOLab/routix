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

## 📁 Output Layout

Where flow-produced artifacts land on disk is governed by `ArtifactLayout`
(`routix.io.ArtifactLayout`) rather than ad-hoc path assembly.

- `SubroutineController.set_artifact_layout(layout, scenario_name=..., instance_name=...)`
  binds an instance-scoped layout to the controller. Helpers like
  `try_get_file_path_for_subroutine` then resolve step-log paths into the
  instance's `progress/` zone.
- Each instance directory is split into three zones:
  `final` (instance dir root — terminal artifacts like the manifest, solution,
  obj_log), `progress/` (per-step logs and intermediate phase artifacts), and
  `report/` (post-hoc visualizations).
- Project-specific artifact kinds register with the layout
  (yaml overlay or `register_kind(...)`) declaring scope, zone, and
  filename template; the layout handles directory creation and zone routing.

See `docs/20260429_artifact_manager.md` for the layout design.
