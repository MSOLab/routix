import logging
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..type_defs import ParametersT, RunMode
from .single_instance_runner import SingleInstanceRunnerT


class MultiInstanceRunner(Generic[ParametersT, SingleInstanceRunnerT], ABC):
    """
    Abstract runner to orchestrate solving a set of instances with a given runner class.
    """

    mode: RunMode

    # Optional: only when mode is RESUME
    flow_resume_idx: int = 0

    def __init__(
        self,
        s_i_runner_class: type[SingleInstanceRunnerT],
        instances: Sequence[ParametersT],
        shared_param_dict: dict,
        subroutine_flow: Any,
        stopping_criteria: Any,
        output_dir: Path,
        output_metadata: dict[str, Any],
        mode: RunMode = RunMode.FULL_RUN,
        **kwargs: Any,
    ) -> None:
        self.e_timer = ElapsedTimer()
        """Elapsed timer for multi-instance run."""

        # Runner class
        self.s_i_runner_class = s_i_runner_class

        # Instance data
        self.instances = instances
        self.shared_param_dict = shared_param_dict

        # Algorithm data
        self.subroutine_flow = subroutine_flow
        self.stopping_criteria = stopping_criteria

        # Output configuration
        self.output_dir = output_dir
        self.output_metadata = output_metadata

        # Execution configuration
        self.mode = mode

        self.runners: list[SingleInstanceRunnerT] = []
        self.results: list[Any] = []

        self._set_start_dt()
        self._init_working_dir()
        self._init_single_instance_runners()
        # Resume mode: check for existing results
        if self.mode == RunMode.RESUME:
            # Check existence of result files that matches the instances provided
            try:
                self._load_resume_data()
            except Exception as e:
                logging.exception(f"Loading resume data failed: {e}", exc_info=True)

    def _set_start_dt(self) -> None:
        """
        Sets the start date-time for the elapsed timer.
        If the start date-time is already in output_metadata, it uses that.
        Otherwise, it initializes the start date-time from the elapsed timer.
        """
        if dt := self.output_metadata.get("start_dt"):
            self.e_timer.set_start_time(dt)
        else:
            self.output_metadata["start_dt"] = self.e_timer.start_dt

    def _init_working_dir(self) -> None:
        """
        Initialize the working directory for the multi-instance run.

        The working directory is the same as the output directory provided.
        """
        self.working_dir = self.output_dir
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def _init_single_instance_runners(self) -> None:
        """Initializes the single instance runners for each instance."""
        self.runners.clear()
        self.results.clear()

        # Pre-create all runner instances
        for instance in self.instances:
            runner = self.s_i_runner_class(
                instance=instance,
                shared_param_dict=self.shared_param_dict,
                subroutine_flow=self.subroutine_flow,
                stopping_criteria=self.stopping_criteria,
                output_dir=self.output_dir,
                output_metadata=self.output_metadata,
                mode=self.mode,
            )
            self.runners.append(runner)

    def _load_resume_data(self) -> None:
        self._check_file_existence()

    def _check_file_existence(self) -> None:
        """
        Load resume data and check the configured output directory
        for existing per-instance result files.
        """
        # Build filename formats with sensible defaults (can be overridden by output_metadata)
        summary_fn_format = self.output_metadata.get(
            "summary_fn_format", "{}_summary.csv"
        )
        solution_fn_format = self.output_metadata.get(
            "solution_fn_format", "{}_solution.yaml"
        )
        obj_log_fn_format = self.output_metadata.get(
            "obj_log_fn_format", "{}_obj_log.yaml"
        )
        # Resume directory
        if "resume_root" not in self.output_metadata:
            raise ValueError("Missing 'resume_root' in output_metadata")
        resume_dir = Path(self.output_metadata["resume_root"])

        missing: dict[str, list[str]] = {}

        for ins in self.instances:
            ins_name = (
                getattr(ins, "name", None)
                or getattr(ins, "instance_name", None)
                or str(ins)
            )
            inst_dir = resume_dir / str(ins_name) / "results"
            if not inst_dir.exists():
                raise ValueError(f"Resume directory does not exist: {inst_dir}")

            found: dict[str, str] = {}
            miss_list: list[str] = []

            # summary
            sum_files = (
                list(inst_dir.glob(summary_fn_format.format(ins_name)))
                if inst_dir.exists()
                else []
            )
            if sum_files:
                found["summary"] = str(sum_files[0])
            else:
                miss_list.append(summary_fn_format.format(ins_name))

            # solution
            sol_files = (
                list(inst_dir.glob(solution_fn_format.format(ins_name)))
                if inst_dir.exists()
                else []
            )
            if sol_files:
                found["solution"] = str(sol_files[0])
            else:
                miss_list.append(solution_fn_format.format(ins_name))

            # obj_log
            obj_files = (
                list(inst_dir.glob(obj_log_fn_format.format(ins_name)))
                if inst_dir.exists()
                else []
            )
            if obj_files:
                found["obj_log"] = str(obj_files[0])
            else:
                miss_list.append(obj_log_fn_format.format(ins_name))

            if miss_list:
                missing[str(ins_name)] = miss_list

        if missing:
            # Fail fast: if any instance lacks required files for resume, raise an error
            msg_lines = ["Missing resume result files for instances:"]
            for ins_name, files in missing.items():
                msg_lines.append(f"  {ins_name}: {', '.join(files)}")
            full_msg = "\n".join(msg_lines)
            raise RuntimeError(full_msg)

    def set_flow_resume_idx(self, flow_resume_idx: int) -> None:
        """Sets the index in the subroutine flow from which to resume execution.

        Args:
            flow_resume_idx (int): The index in the subroutine flow from which to resume execution.
        """
        if flow_resume_idx < 0:
            raise ValueError("flow_resume_idx must be non-negative")
        logging.info(f"Setting flow_resume_idx to {flow_resume_idx}")
        self.flow_resume_idx = flow_resume_idx
        for runner in self.runners:
            runner.flow_resume_idx = flow_resume_idx

    def run(self) -> Any:
        for idx, runner in enumerate(self.runners):
            try:
                result = runner.run()
            except Exception as e:
                logging.error(f"Error in instance {idx}: {e}")
                traceback.print_exc()
                result = None
            self.results.append(result)

        return self.post_run_process()

    @abstractmethod
    def post_run_process(self) -> Any:
        """
        Post-processes the results after running all instances.
        This method should be implemented in subclasses to handle specific post-run logic.
        """
        ...


MultiInstanceRunnerT = TypeVar("MultiInstanceRunnerT", bound=MultiInstanceRunner)
"""
Type variable for MultiInstanceRunner, allowing methods to specify
that they return or accept an instance of MultiInstanceRunner or its subclasses.
"""
