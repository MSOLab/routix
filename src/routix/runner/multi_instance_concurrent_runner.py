import concurrent.futures
import logging
from pathlib import Path
from typing import Any, Callable, Generic, Sequence

from ..type_defs import ParametersT, RunMode
from .multi_instance_runner import MultiInstanceRunner
from .single_instance_runner import SingleInstanceRunnerT


class MultiInstanceConcurrentRunner(
    MultiInstanceRunner, Generic[ParametersT, SingleInstanceRunnerT]
):
    """
    Orchestrates solving a set of instances concurrently using a specified runner class.
    This class extends the InstanceSetRunner to allow for concurrent execution of
    multiple instances of a problem using a multiprocessing approach.
    It uses a ProcessPoolExecutor to manage the concurrent execution of runners.
    """

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
        instance_worker_cnt: int = 2,
        logger: logging.Logger | None = None,
        pool_initializer: Callable[..., None] | None = None,
        pool_initargs: tuple = (),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            s_i_runner_class,
            instances,
            shared_param_dict,
            subroutine_flow,
            stopping_criteria,
            output_dir,
            output_metadata,
            mode,
            logger=logger,
        )
        self.set_instance_worker_cnt(instance_worker_cnt)
        self._pool_initializer = pool_initializer
        self._pool_initargs = pool_initargs

    def get_instance_worker_cnt(self) -> int:
        """
        Retrieves the number of workers for concurrent execution.

        Raises:
            ValueError: If instance_worker_cnt is set to a value less than 1.

        Returns:
            int: The number of workers for concurrent execution.
                If not set, returns the default value of 2.
        """
        if self._instance_worker_cnt < 1:
            raise ValueError(
                f"instance_worker_cnt must be at least 1, but is {self._instance_worker_cnt}"
            )
        return self._instance_worker_cnt

    def set_instance_worker_cnt(self, instance_worker_cnt: int) -> None:
        """Sets the number of workers for concurrent execution.

        Args:
            instance_worker_cnt (int): The number of workers for concurrent execution.
        """
        if instance_worker_cnt < 1:
            self.logger.warning(
                f"Given instance_worker_cnt {instance_worker_cnt} is less than 1. "
                "Setting instance_worker_cnt to 1."
            )
            self._instance_worker_cnt = 1
        else:
            self.logger.info(f"Setting instance_worker_cnt to {instance_worker_cnt}")
            self._instance_worker_cnt = instance_worker_cnt

    def run(self) -> Any:
        instance_worker_cnt = min(self.get_instance_worker_cnt(), len(self.instances))
        if instance_worker_cnt == 1:
            return super().run()

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=instance_worker_cnt,
            initializer=self._pool_initializer,
            initargs=self._pool_initargs,
        ) as executor:
            # Submit the run method of each pre-created runner instance
            futures = {executor.submit(runner.run): runner for runner in self.runners}
            for future in concurrent.futures.as_completed(futures):
                self.results.append(future.result())

        return self.post_run_process()
