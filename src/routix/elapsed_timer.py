import time
from datetime import datetime, timedelta
from typing import Any
from warnings import warn


class ElapsedTimer:
    """Utility class to track elapsed time and provide formatted timestamps."""

    __slots__ = ("_start_dt", "_start_monotonic")

    _start_dt: datetime
    """Datetime object of start time"""
    _start_monotonic: float
    """Monotonic timer value at start"""
    _dir_name_format: str = "%Y%m%dT%H%M%S_%f"
    """Format for directory names based on start time"""

    def __init__(self):
        """Initializes the timer with the current time."""
        self.set_start_time_as_now()

    def __str__(self):
        return f"ElapsedTimer started @ {self.get_formatted_start_dt()}"

    def set_start_time(self, start_dt: datetime) -> None:
        """Sets the start time of the timer.

        Args:
            start_dt (datetime): Datetime object of start time
        """
        self._start_dt = start_dt
        self._start_monotonic = time.monotonic()

    def set_start_time_as_now(self):
        """Sets the start time of the timer to the current time."""
        self.set_start_time(datetime.now())

    def reset(self) -> None:
        """Resets the timer to the current time."""
        self.set_start_time_as_now()

    # Start datetime

    @property
    def start_dt(self) -> datetime:
        """
        Returns:
            datetime: The start datetime of the timer.
        """
        return self._start_dt

    def get_formatted_start_dt(self) -> str:
        """
        Returns:
            str:the start time as an ISO 8601 string with milliseconds.
        """
        return self.get_start_dt_isoformatted()

    def get_start_dt_isoformatted(
        self, isoformat_kwargs: dict[str, Any] | None = None
    ) -> str:
        """Returns the start datetime formatted as an ISO 8601 string.

        Args:
            isoformat_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the isoformat method.
                If None, use {"timespec": "milliseconds"}.

        Returns:
            str: Formatted start datetime string.
        """
        if isoformat_kwargs is None:
            isoformat_kwargs = {"timespec": "milliseconds"}
        return self._start_dt.isoformat(**isoformat_kwargs)

    def get_start_dt_strftime(
        self, strftime_format: str = "%Y-%m-%dT%H:%M:%S.%f"
    ) -> str:
        """
        Returns the start datetime formatted as a string using strftime.

        Args:
            strftime_format (str, optional): Format string for strftime. Defaults to "%Y-%m-%dT%H:%M:%S.%f".

        Returns:
            str: Formatted start datetime string.
        """
        return self._start_dt.strftime(strftime_format)

    def get_start_dt_for_dir_name(self) -> str:
        """
        Returns the start datetime formatted for use in a directory name.

        Returns:
            str: Formatted start datetime string suitable for directory names.
        """
        return self.get_start_dt_strftime(self._dir_name_format)

    def set_start_dt_from_dir_name(self, dir_name: str) -> None:
        """
        Sets the start datetime from a directory name formatted as _dir_name_format.

        Args:
            dir_name (str): Directory name containing the start datetime.
        """
        try:
            self._start_dt = datetime.strptime(dir_name, self._dir_name_format)
            # compute how much time has already elapsed since dt
            elapsed_since_dt = datetime.now().timestamp() - self._start_dt.timestamp()
            # adjust monotonic baseline so that elapsed_sec reflects dt-origin
            self._start_monotonic = time.monotonic() - elapsed_since_dt
        except ValueError as e:
            raise ValueError(
                f"Invalid directory name format for start datetime: {dir_name}"
            ) from e

    # Elapsed time

    @property
    def elapsed_sec(self) -> float:
        """
        Returns:
            float: Seconds elapsed since the timer was initiated.
        """
        return time.monotonic() - self._start_monotonic

    def get_elapsed_sec(self) -> float:
        """
        Returns:
            float: Seconds elapsed since the handler was initiated
        """
        warn(
            "get_elapsed_sec() is deprecated, use elapsed_sec property instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.elapsed_sec

    def get_formatted_elapsed_time(self) -> str:
        """Returns the elapsed time since the timer was started, formatted as a string."""
        elapsed_time = timedelta(seconds=self.elapsed_sec)
        return str(elapsed_time)

    def get_remaining_sec(self, timelimit: float) -> float:
        """
        Returns the remaining time (in seconds) until the timelimit is reached.

        Args:
            timelimit (float): Time limit in seconds.

        Returns:
            float: Remaining seconds (never negative).
        """
        return max(timelimit - self.elapsed_sec, 0.0)

    def time_over(self, timelimit: float) -> bool:
        """
        Checks if the elapsed time exceeds the given time limit.

        Args:
            timelimit (float): Time limit in seconds.

        Returns:
            bool: True if the elapsed time exceeds the time limit, False otherwise.
        """
        return self.elapsed_sec > timelimit
