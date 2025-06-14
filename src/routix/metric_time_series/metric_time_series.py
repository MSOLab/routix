from typing import Generic, Optional

from ..typevars import Numeric


class MetricTimeSeries(Generic[Numeric]):
    """
    A time series that stores values associated with timestamps.
    It allows adding new entries, retrieving values, and checking the latest value.
    """

    def __init__(self, name: str):
        self.name = name
        self._timestamp_value_map: dict[float, Numeric] = {}
        """
        timestamp -> value
        """
        self._latest_val: Optional[Numeric] = None
        """Latest value in the time series."""

    def __len__(self):
        return len(self._timestamp_value_map)

    def add(self, timestamp: float, value: Numeric):
        """Add a new entry to the time series.
        If the timestamp already exists, it will update the value.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        self._timestamp_value_map[timestamp] = value
        self._latest_val = value

    def items(self) -> list[tuple[float, Numeric]]:
        """Return the items in the time series as a list of tuples (timestamp, value)."""
        return sorted(self._timestamp_value_map.items())

    @property
    def timestamps(self) -> list[float]:
        """Return the timestamps in sorted order."""
        return sorted(self._timestamp_value_map.keys())

    @property
    def time_sorted_values(self) -> list[Numeric]:
        return [self._timestamp_value_map[t] for t in sorted(self.timestamps)]

    @property
    def values(self) -> list[Numeric]:
        return self.time_sorted_values

    @property
    def latest_value(self) -> Optional[Numeric]:
        """Return the latest value in the time series."""
        return self._latest_val

    def add_if_value_stg_latest(self, timestamp: float, value: Numeric):
        """
        Add if given value is *strictly greather than* the latest value.
        If the series is empty, it will add the value regardless.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        if self._latest_val is None or value > self._latest_val:
            self.add(timestamp, value)

    def add_if_value_stl_latest(self, timestamp: float, value: Numeric):
        """
        Add if given value is *strictly less than* the latest value.
        If the series is empty, it will add the value regardless.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        if self._latest_val is None or value < self._latest_val:
            self.add(timestamp, value)

    def repeat_latest(self, timestamp: float):
        """
        Add the latest value at the given timestamp.
        If the series is empty, it will not add anything.

        Args:
            timestamp (float): _timestamp_ of the entry.
        """
        if self._latest_val is not None:
            self.add(timestamp, self._latest_val)
