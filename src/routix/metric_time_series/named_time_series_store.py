import warnings
from typing import Generic, Optional

from ..typevars import Numeric
from .metric_time_series import MetricTimeSeries


class NamedTimeSeriesStore(Generic[Numeric]):
    """
    A store for named time series, allowing to manage multiple MetricTimeSeries instances.
    It provides methods to add entries, retrieve time series by name,
    and manage the latest values across all time series.
    It is a generic class that can work with any numeric type defined in the typevars module.
    """

    _store: dict[str, MetricTimeSeries[Numeric]]
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

    def names(self) -> list[str]:
        """
        Returns:
            list[str]: List of names of all MetricTimeSeries in the store.
        """
        return list(self._store.keys())

    def _get(self, name: str) -> Optional[MetricTimeSeries[Numeric]]:
        """
        Args:
            name (str): Name of the MetricTimeSeries to retrieve.

        Returns:
            Optional[MetricTimeSeries[Numeric]]: The MetricTimeSeries instance if found,
                otherwise None.
        """
        return self._store.get(name, None)

    def get_or_create(self, name: str) -> MetricTimeSeries[Numeric]:
        """
        Retrieve a MetricTimeSeries by name,
        or create a new one if it does not exist.

        Args:
            name (str): Name of the MetricTimeSeries to retrieve or create.

        Returns:
            MetricTimeSeries[Numeric]: The MetricTimeSeries instance associated with the name.
        """
        if name not in self._store:
            self._store[name] = MetricTimeSeries[Numeric](name)
        return self._store[name]

    def add_entry(self, name: str, timestamp: float, value: Numeric):
        """
        Add a new entry to the MetricTimeSeries with the given name.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        self.get_or_create(name).add(timestamp, value)

    def add_if_stg(self, name: str, timestamp: float, value: Numeric):
        """
        Add an entry to the MetricTimeSeries if the value is *strictly greater than* the latest value.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        self.get_or_create(name).add_if_value_stg_latest(timestamp, value)

    def add_if_stl(self, name: str, timestamp: float, value: Numeric):
        """
        Add an entry to the MetricTimeSeries if the value is *strictly less than* the latest value.
        If the MetricTimeSeries does not exist, it will be created.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
            value (Numeric): _value_ of the entry.
        """
        self.get_or_create(name).add_if_value_stl_latest(timestamp, value)

    def repeat_latest(self, name: str, timestamp: float):
        """
        Repeat the latest value in the MetricTimeSeries with the given name.
        If the MetricTimeSeries does not exist, nothing happens.

        Args:
            name (str): Name of the MetricTimeSeries to which the entry will be added.
            timestamp (float): _timestamp_ of the entry.
        """
        if name in self._store:
            self._store[name].repeat_latest(timestamp)
        else:
            warnings.warn(f"No time series with name '{name}' to repeat_latest.")

    def latest_values(self) -> dict[str, Optional[Numeric]]:
        """
        Get the latest values of all MetricTimeSeries in the store.
        This method returns a dictionary where the keys are the names of the MetricTimeSeries
        and the values are their latest values. If a MetricTimeSeries has no entries,
        the value will be None.

        Returns:
            dict[str, Optional[Numeric]]: names -> their latest values.
        """
        return {name: ts.latest_value for name, ts in self._store.items()}

    def clear(self):
        """Remove all MetricTimeSeries in the store."""
        self._store.clear()
