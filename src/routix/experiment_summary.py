from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .solver_output_summary import SolverOutputSummary
from .solver_status import SolverStatus


@dataclass
class ExperimentSummary:
    """
    A high-level summary of a full CP-LNS experiment for a single instance.

    Accumulates multiple `SolverOutputSummary` objects
    (e.g., base CP solve + LNS iterations),
    tracks method call frequencies, and computes summary statistics
    such as total runtime, final solution status, and improvement ratio.

    Example usage:
        >>> summary = ExperimentSummary("instance_42")
        >>> summary.log_run("base_cp_solve",
        ...     SolverOutputSummary(
        ...         status="FEASIBLE",
        ...         elapsed_time=3.7,
        ...         objective_value=1200,
        ...         best_objective_bound=1100,
        ...         progress_log=[(0.5, 1400, 1300), (2.1, 1300, 1150)]
        ...     )
        ... )
        >>> summary.report()
        >>> summary.to_yaml(Path("logs/summary_instance_42.yaml"))
    """

    name: str
    """Identifier of the instance or experiment."""
    runs: list[SolverOutputSummary] = field(default_factory=list)
    """List of solver results."""
    method_call_counts: dict[str, int] = field(default_factory=dict)
    """Frequency of method invocations."""

    def log_run(self, method_name: str, summary: SolverOutputSummary) -> None:
        """Records a solver run and its associated method call."""
        self.record_method_call(method_name)
        self.add_run_summary(summary)

    def add_run_summary(self, summary: SolverOutputSummary) -> None:
        """Appends a solver run summary to the experiment."""
        self.runs.append(summary)

    def record_method_call(self, method_name: str) -> None:
        """Increments the count for a method call."""
        self.method_call_counts[method_name] = (
            self.method_call_counts.get(method_name, 0) + 1
        )

    def get_first_summary(self) -> Optional[SolverOutputSummary]:
        return self.runs[0] if self.runs else None

    def get_last_summary(self) -> Optional[SolverOutputSummary]:
        return self.runs[-1] if self.runs else None

    def get_summary_minimum_obj(self) -> Optional[SolverOutputSummary]:
        feasible_runs = [
            run for run in self.runs if SolverStatus.found_feasible_solution(run.status)
        ]
        if not feasible_runs:
            return None
        return min(
            feasible_runs,
            key=lambda run: run.objective_value
            if run.objective_value is not None
            else float("inf"),
        )

    def get_summary_maximum_obj(self) -> Optional[SolverOutputSummary]:
        feasible_runs = [
            run for run in self.runs if SolverStatus.found_feasible_solution(run.status)
        ]
        if not feasible_runs:
            return None
        return max(
            feasible_runs,
            key=lambda run: run.objective_value
            if run.objective_value is not None
            else float("-inf"),
        )

    def get_total_elapsed_time(self) -> float:
        return sum(run.elapsed_time for run in self.runs)

    def found_feasible_solution(self, is_maximize: bool = False) -> bool:
        if is_maximize:
            best = self.get_summary_maximum_obj()
        else:
            best = self.get_summary_minimum_obj()
        return SolverStatus.found_feasible_solution(best.status) if best else False

    def get_improvement_ratio(self, is_maximize: bool = False) -> Optional[float]:
        first = self.get_first_summary()
        if is_maximize:
            best = self.get_summary_maximum_obj()
        else:
            best = self.get_summary_minimum_obj()

        if not (
            first
            and best
            and first.objective_value is not None
            and best.objective_value is not None
        ):
            return None
        if first.objective_value == 0:
            return None

        if is_maximize:
            return (
                best.objective_value - first.objective_value
            ) / first.objective_value
        return (first.objective_value - best.objective_value) / first.objective_value

    def report(self, is_maximize: bool = False) -> None:
        print(f"\n=== Experiment Summary: {self.name} ===")
        print(f"Total elapsed time: {self.get_total_elapsed_time():.2f} sec")

        if is_maximize:
            best = self.get_summary_maximum_obj()
        else:
            best = self.get_summary_minimum_obj()
        print(f"Final status: {best.status if best else 'N/A'}")
        print(f"Final objective: {best.objective_value if best else 'N/A'}")

        ratio = self.get_improvement_ratio(is_maximize)
        print(
            f"Improvement ratio: {ratio:.2%}"
            if ratio is not None
            else "Improvement: N/A"
        )
        print("--- Method Call Counts ---")
        for method, count in sorted(self.method_call_counts.items()):
            print(f"{method}: {count} calls")
        print("====================================\n")

    def to_dict(self, is_maximize: bool = False) -> dict[str, Any]:
        if is_maximize:
            best = self.get_summary_maximum_obj()
        else:
            best = self.get_summary_minimum_obj()

        first_summary = self.get_first_summary()
        if first_summary:
            first_obj = first_summary.objective_value
        else:
            first_obj = best.objective_value if best else None

        return {
            "instance_name": self.name,
            "total_elapsed_time": self.get_total_elapsed_time(),
            "status": best.status if best else None,
            "first_obj": first_obj,
            "best_obj": best.objective_value if best else None,
            "improvement_ratio": self.get_improvement_ratio(is_maximize),
            "is_feasible": self.found_feasible_solution(is_maximize),
            "method_call_counts": self.method_call_counts,
            "num_runs": len(self.runs),
        }

    def to_yaml(self, file_path: Path) -> None:
        """Saves the summary to a YAML file."""
        import yaml

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.to_dict(), f, sort_keys=False, allow_unicode=True)
        except yaml.YAMLError as e:
            raise RuntimeError(
                f"YAML error while saving ExperimentSummary to {file_path}: {e}"
            )
        except Exception as e:
            raise RuntimeError(f"Error saving ExperimentSummary to {file_path}: {e}")
