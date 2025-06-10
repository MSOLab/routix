import warnings

from .multi_instance_concurrent_runner import MultiInstanceConcurrentRunner
from .multi_instance_runner import MultiInstanceRunner
from .single_instance_runner import SingleInstanceRunner


class InstanceSetRunner(MultiInstanceRunner):
    """(Deprecated) Use MultiInstanceRunner instead."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "InstanceSetRunner is deprecated, use MultiInstanceRunner instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = [
    "SingleInstanceRunner",
    "MultiInstanceRunner",
    "InstanceSetRunner",  # Deprecated, use MultiInstanceRunner instead
    "MultiInstanceConcurrentRunner",
]
