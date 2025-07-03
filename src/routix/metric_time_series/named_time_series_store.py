from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Generic

from ..type_defs import NumericT
from .metric_time_series import MetricTimeSeries


class NamedTimeSeriesStore(Generic[NumericT]):
    """
    A store for named time series, allowing to manage multiple MetricTimeSeries instances.
    It provides methods to add entries, retrieve time series by name,
    and manage the last values across all time series.
    It is a generic class that can work with any numeric type defined in the typevars module.
    """

    _store: dict[str, MetricTimeSeries[NumericT]]
    """Mapping from name to MetricTimeSeries instance"""

    def __init__(self):
        self._store = {}

    def __contains__(self, name: str) -> bool:
        return name in self._store

    def __len__(self) -> int:
        """
        Returns:
            int: Number of MetricTimeSeries in the store.
        """
        return len(self._store)

    def name_set(self) -> set[str]:
        """
        Returns:
            set[str]: Set of names of all MetricTimeSeries in the store.
        """
        return set(self._store.keys())

    def _get(self, name: str) -> MetricTimeSeries[NumericT] | None:
        """
        Args:
            name (str): Name of the MetricTimeSeries to retrieve.

        Returns:
            MetricTimeSeries[Numeric] | None: The MetricTimeSeries instance if found,
                otherwise None.
        """
        return self._store.get(name, None)

    def get_or_create(self, name: str) -> MetricTimeSeries[NumericT]:
        """
        Retrieve a MetricTimeSeries by name,
        or create a new one if it does not exist.

        Args:
            name (str): Name of the MetricTimeSeries to retrieve or create.

        Returns:
            MetricTimeSeries[Numeric]: The MetricTimeSeries instance associated with the name.
        """
        if name not in self._store:
            self._store[name] = MetricTimeSeries[NumericT](name)
        return self._store[name]

    def add_entry(self, name: str, timestamp: float, value: NumericT, note: Any = None):
        """
        Add a new entry to the MetricTimeSeries with the given name.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        self.get_or_create(name).add(timestamp, value, note=note)

    def add_if_stg(
        self, name: str, timestamp: float, value: NumericT, note: Any = None
    ):
        """
        Add an entry to the MetricTimeSeries if the value is *strictly greater than* the last value.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        self.get_or_create(name).add_if_value_stg_last(timestamp, value, note=note)

    def add_if_stl(
        self, name: str, timestamp: float, value: NumericT, note: Any = None
    ):
        """
        Add an entry to the MetricTimeSeries if the value is *strictly less than* the last value.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
            note (Any, optional): Additional information about the entry.
        """
        self.get_or_create(name).add_if_value_stl_last(timestamp, value, note=note)

    def repeat_last_value(
        self,
        name: str,
        timestamp: float,
        note: Any = None,
        overwrite_note: bool = False,
    ):
        """
        Repeat the last value in the MetricTimeSeries with the given name.
        If the MetricTimeSeries does not exist, nothing happens.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            note (Any, optional): Additional information about the entry.
            overwrite_note (bool, optional): If True, the last value will be overwritten.
                Defaults to False, meaning it will not overwrite if the last value already exists.
        """
        if name in self._store:
            self._store[name].repeat_last_value(
                timestamp, note=note, overwrite_note=overwrite_note
            )
        else:
            warnings.warn(f"No time series with name '{name}' to repeat_last.")

    def get_last_value_dict(self) -> dict[str, NumericT | None]:
        """
        Get the last values of all MetricTimeSeries in the store.
        This method returns a dictionary where the keys are the names of the MetricTimeSeries
        and the values are their last values. If a MetricTimeSeries has no entries,
        the value will be None.

        Returns:
            dict[str, Numeric | None]: names -> their last values.
        """
        return {name: ts.last_value for name, ts in self._store.items()}

    def clear(self):
        """Remove all MetricTimeSeries in the store."""
        self._store.clear()

    # I/O from/to dict

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Convert the store to a dictionary representation.

        Returns:
            dict[str, dict[str, Any]]: A dictionary where keys are names of MetricTimeSeries
                and values are their serialized forms.
        """
        return {name: ts.to_dict() for name, ts in self._store.items()}

    @classmethod
    def from_dict(
        cls, data: dict[str, dict[str, Any]]
    ) -> NamedTimeSeriesStore[NumericT]:
        """Create a NamedTimeSeriesStore from a dictionary representation.

        Args:
            data (dict[str, dict[str, Any]]): A dictionary where keys are names of MetricTimeSeries
                and values are their serialized forms.

        Returns:
            NamedTimeSeriesStore[Numeric]: An instance of NamedTimeSeriesStore populated with the data.
        """
        store = cls()
        for name, ts_data in data.items():
            store._store[name] = MetricTimeSeries.from_dict(ts_data)
        return store

    # I/O from/to YAML

    def save_yaml(self, file_path: Path | str, encoding: str = "utf-8"):
        """Save the store to a YAML file.

        Args:
            file_path (str): Path to the YAML file where the store will be saved.
            encoding (str, optional): Encoding to use when writing the file.
                Defaults to "utf-8".
        """
        from ..utils import object_to_yaml

        path = Path(file_path)
        object_to_yaml(self.to_dict(), path, encoding=encoding)

    @classmethod
    def load_yaml(
        cls, file_path: Path | str, encoding: str = "utf-8"
    ) -> NamedTimeSeriesStore[NumericT]:
        """Load a NamedTimeSeriesStore from a YAML file.

        Args:
            file_path (str): Path to the YAML file from which the store will be loaded.
            encoding (str, optional): Encoding to use when writing the file.
                Defaults to "utf-8".

        Returns:
            NamedTimeSeriesStore[Numeric]: An instance of NamedTimeSeriesStore populated with the data.
        """
        import yaml

        with open(file_path, "r", encoding=encoding) as file:
            data = yaml.safe_load(file)
        return cls.from_dict(data)

    # I/O from/to JSON

    def save_json(self, file_path: Path | str, encoding: str = "utf-8"):
        """Save the store to a JSON file.

        Args:
            file_path (str): Path to the JSON file where the store will be saved.
            encoding (str, optional): Encoding to use when writing the file.
                Defaults to "utf-8".
        """
        from ..utils import object_to_json

        path = Path(file_path)
        object_to_json(self.to_dict(), path, encoding=encoding)

    @classmethod
    def load_json(
        cls, file_path: Path | str, encoding: str = "utf-8"
    ) -> NamedTimeSeriesStore[NumericT]:
        """Load a NamedTimeSeriesStore from a JSON file.

        Args:
            file_path (str): Path to the JSON file from which the store will be loaded.
            encoding (str, optional): Encoding to use when writing the file.
                Defaults to "utf-8".

        Returns:
            NamedTimeSeriesStore[Numeric]: An instance of NamedTimeSeriesStore populated with the data.
        """
        import json

        with open(file_path, "r", encoding=encoding) as file:
            data = json.load(file)
        return cls.from_dict(data)
