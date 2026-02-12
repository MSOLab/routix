# SolutionManager API Changes

This document summarizes the breaking and behavioral changes to `SolutionManager`.

## Renamed Methods and Attributes

| Old Name | New Name |
|----------|----------|
| `incumbent_solution` | `best_solution` |
| `get_incumbent()` | `get_best_solution()` |
| `has_incumbent()` | `has_best_solution()` |

## New Attributes

| Attribute | Description |
|-----------|-------------|
| `ref_solution` | Current reference solution (e.g., for Simulated Annealing) |
| `ref_obj_value` | Objective value of the reference solution |

## New Methods (from 663e4c6)

| Method | Description |
|--------|-------------|
| `get_ref_solution() -> SolutionT \| None` | Returns current reference solution |
| `get_last_solution() -> SolutionT \| None` | Returns most recently generated solution from history |
| `has_best_solution() -> bool` | Checks if best solution exists |

## New Methods (from 1c0eb98)

| Method | Description |
|--------|-------------|
| `sync_ref_to_best() -> None` | Sets reference solution to the current best solution |
| `set_ref_solution(solution) -> None` | Manually sets the reference solution to a given solution |

## Renamed Comparison Methods

| Old Name | New Name |
|----------|----------|
| `current_obj_value_is_worse_than(value)` | `best_obj_value_is_worse_than(value)` |
| `current_obj_bound_is_worse_than(bound)` | `best_obj_bound_is_worse_than(bound)` |

### New Behavior

- Returns `True` when `best_obj_value`/`best_obj_bound` is `None` (no best set yet)
- Returns `False` when new value equals current best (equal is not worse)
- Returns `False` when new value is better than current best
- Returns `True` only when new value is strictly worse

## Changed `register()` Parameters

| Parameter | Old | New |
|-----------|-----|-----|
| `update_if_equal_obj` | `False` | Removed |
| `force_update_ref_sol` | N/A | `False` (default) |

### New `force_update_ref_sol` Behavior

- `True`: `ref_solution` is always updated to the new solution
- `False` (default): `ref_solution` is only updated when `best_solution` improves

## `register()` Return Value Change

| Version | Behavior |
|---------|----------|
| Before | Returns `True` if `best_solution` was updated |
| After | Returns `True` if `ref_solution` was updated by a better solution |

### Meaning of Return Value

- `True`: Reference solution was updated because the new solution is better than the current best
- `False`: Reference solution was not updated (either `force_update_ref_sol=False` and solution wasn't better, or `force_update_ref_sol=True` but solution wasn't better than current ref)

## New Abstract Methods

Subclasses must implement:

1. `_a_is_better_obj_value(value_a: float, value_b: float | None) -> bool`
   - Returns `True` if value_a is better than value_b
   - `value_b` can be `None` (no best set yet)

2. `_a_is_better_obj_bound(bound_a: float, bound_b: float | None) -> bool`
   - Returns `True` if bound_a is better than bound_b
   - `bound_b` can be `None` (no best set yet)

## Migration Guide

### Before
```python
manager = MySolutionManager()
# ... run optimization ...
incumbent = manager.get_incumbent()
manager.register(report, solution, update_if_equal_obj=True)
```

### After
```python
manager = MySolutionManager()
# ... run optimization ...
best = manager.get_best_solution()
manager.register(report, solution, force_update_ref_sol=True)

# New: access reference solution
ref = manager.get_ref_solution()
```

### Update comparison logic

```python
# Before
if manager.current_obj_value_is_worse_than(new_value):
    # do something

# After
if manager.best_obj_value_is_worse_than(new_value):
    # do something
```
