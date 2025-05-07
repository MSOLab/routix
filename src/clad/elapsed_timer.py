from datetime import datetime


class ElapsedTimer:
    _start_dt: datetime
    """Datetime object of start time"""
    _start_time_in_seconds: float
    """POSIX timestamp of start time"""

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

    def __init__(self):
        """Initializes the timer with the current time."""
        self.set_start_time_as_now()

    def get_formatted_start_dt(self) -> str:
        """
        Returns:
            str: Formatted start datetime string in the format YYYY-MM-DD HH:MM:SS.XX
        """
        return (
            self._start_dt.strftime("%Y-%m-%d %H:%M:%S.")
            + f"{int(self._start_dt.microsecond / 10000):02d}"
        )

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
        return self.get_current_time_in_seconds() - self._start_time_in_seconds
