from datetime import datetime, timedelta
from typing import Any, Optional


class ElapsedTimer:
    """Utility class to track elapsed time and provide formatted timestamps."""

    __slots__ = ("_start_dt", "_start_time_in_seconds")

    _start_dt: datetime
    """Datetime object of start time"""
    _start_time_in_seconds: float
    """POSIX timestamp of start time"""

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
        self._start_time_in_seconds = start_dt.timestamp()

    def set_start_time_as_now(self):
        """Sets the start time of the timer to the current time."""
        self.set_start_time(datetime.now())

    def reset(self) -> None:
        """Resets the timer to the current time."""
        self.set_start_time_as_now()

    def get_formatted_start_dt(self) -> str:
        """
        Returns:
            str:the start time as an ISO 8601 string with milliseconds.
        """
        return self.get_start_dt_isoformatted()

    def get_start_dt_isoformatted(
        self, isoformat_kwargs: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Returns the start datetime formatted as an ISO 8601 string.

        Args:
            isoformat_kwargs (dict[str, Any], optional): Additional keyword arguments for the isoformat method.
                                                         If None, defaults to {"timespec": "milliseconds"}.

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

    @property
    def start_dt(self) -> datetime:
        """
        Returns:
            datetime: The start datetime of the timer.
        """
        return self._start_dt

    @property
    def elapsed_sec(self) -> float:
        """
        Returns:
            float: Seconds elapsed since the timer was initiated.
        """
        return self.get_current_time_in_seconds() - self._start_time_in_seconds

    @staticmethod
    def get_current_time_in_seconds() -> float:
        """
        Returns:
            float: datetime.datetime.now().timestamp()
        """
        return datetime.now().timestamp()

    def get_elapsed_sec(self) -> float:
        """
        Returns:
            float: Seconds elapsed since the handler was initiated
        """
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
        return max(timelimit - self.get_elapsed_sec(), 0.0)

    def time_over(self, timelimit: float) -> bool:
        """
        Checks if the elapsed time exceeds the given time limit.

        Args:
            timelimit (float): Time limit in seconds.

        Returns:
            bool: True if the elapsed time exceeds the time limit, False otherwise.
        """
        return self.get_elapsed_sec() > timelimit
