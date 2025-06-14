from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, Optional

from ..type_hints import Numeric


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
        self._timestamp_note_map: dict[float, Any] = {}
        """
        timestamp -> note

        This can be used to store additional information about the entry.
        For example, it can be used to store the source of the value.
        """

    def __len__(self):
        return len(self._timestamp_value_map)

    def add(self, timestamp: float, value: Numeric, note: Any = None):
        """Add a new entry to the time series.
        If the timestamp already exists, it will update the value.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """

        self._timestamp_value_map[timestamp] = value
        self._latest_val = value
        if note is not None:
            self._timestamp_note_map[timestamp] = note

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

    @property
    def timestamp_note_map(self) -> dict[float, Any]:
        """Return the timestamp to note map."""
        return self._timestamp_note_map.copy()

    def add_if_value_stg_latest(
        self, timestamp: float, value: Numeric, note: Any = None
    ):
        """
        Add if given value is *strictly greather than* the latest value.
        If the series is empty, it will add the value regardless.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        if self._latest_val is None or value > self._latest_val:
            self.add(timestamp, value, note=note)

    def add_if_value_stl_latest(
        self, timestamp: float, value: Numeric, note: Any = None
    ):
        """
        Add if given value is *strictly less than* the latest value.
        If the series is empty, it will add the value regardless.

        Args:
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        if self._latest_val is None or value < self._latest_val:
            self.add(timestamp, value, note=note)

    def repeat_latest(self, timestamp: float, note: Any = None):
        """
        Add the latest value at the given timestamp.
        If the series is empty, it will not add anything.

        Args:
            timestamp (float): _timestamp_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        if self._latest_val is not None:
            self.add(timestamp, self._latest_val, note=note)

    # I/O from/to dict

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data": {str(ts): val for ts, val in self._timestamp_value_map.items()},
            "notes": {str(ts): note for ts, note in self._timestamp_note_map.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricTimeSeries:
        """Create a MetricTimeSeries instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary representation of a MetricTimeSeries.
                It should contain the keys "name", "data", and optionally "notes".

        Raises:
            KeyError: If the required keys are not present in the dictionary.
            TypeError: If the "data" key does not contain a dictionary of timestamp-value pairs.

        Returns:
            MetricTimeSeries: A MetricTimeSeries instance created from the provided dictionary.
        """

        if "name" not in data or "data" not in data:
            raise KeyError("The dictionary must contain 'name' and 'data' keys.")
        if not isinstance(data["data"], dict):
            raise TypeError("'data' must be a dictionary with timestamp-value pairs.")
        name = data["name"]
        src_timestamp_value_map = data["data"]
        timestamp_value_map = {
            float(ts): val for ts, val in src_timestamp_value_map.items()
        }
        sorted_timestamp = sorted(timestamp_value_map.keys())
        instance = cls(name)
        for ts in sorted_timestamp:
            instance.add(ts, timestamp_value_map[ts])
        src_timestamp_note_map = data.get("notes", {})
        instance._timestamp_note_map = {
            float(ts): note for ts, note in src_timestamp_note_map.items()
        }
        return instance

    # I/O from/to YAML

    def save_yaml(self, file_path: Path | str):
        """
        Save the MetricTimeSeries to a YAML file.

        Args:
            file_path (Path | str): Path to the YAML file.
        """
        import yaml

        with open(file_path, "w") as file:
            yaml.dump(self.to_dict(), file)

    @classmethod
    def load_yaml(cls, file_path: Path | str) -> MetricTimeSeries:
        """
        Load a MetricTimeSeries from a YAML file.

        Args:
            file_path (Path | str): Path to the YAML file.

        Returns:
            MetricTimeSeries: The loaded MetricTimeSeries instance.
        """
        import yaml

        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return cls.from_dict(data)
