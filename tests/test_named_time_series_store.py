import warnings
from pathlib import Path

from src.routix.metric_time_series import NamedTimeSeriesStore


def test_add_and_retrieve():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("obj_val", 0.0, 100.0)
    store.add_entry("obj_val", 1.0, 90.0)
    store.add_entry("obj_bound", 0.0, 200.0)

    assert "obj_val" in store
    assert len(store) == 2
    assert store.get_last_value_dict()["obj_val"] == 90.0
    assert store.get_last_value_dict()["obj_bound"] == 200.0


def test_add_if_stg():
    store = NamedTimeSeriesStore[float]()
    store.add_if_stg("score", 0.0, 10.0)
    store.add_if_stg("score", 1.0, 8.0)  # ignored
    store.add_if_stg("score", 2.0, 15.0)  # added

    ts = store.get_or_create("score")
    assert ts.timestamps == [0.0, 2.0]
    assert ts.values == [10.0, 15.0]


def test_add_if_stl():
    store = NamedTimeSeriesStore[float]()
    store.add_if_stl("cost", 0.0, 50.0)
    store.add_if_stl("cost", 1.0, 55.0)  # ignored
    store.add_if_stl("cost", 2.0, 30.0)  # added

    ts = store.get_or_create("cost")
    assert ts.timestamps == [0.0, 2.0]
    assert ts.values == [50.0, 30.0]


def test_repeat_last_with_existing_series():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("time", 0.0, 100.0)
    store.repeat_last_value("time", 1.0)

    ts = store.get_or_create("time")
    assert ts.timestamps == [0.0, 1.0]
    assert ts.values == [100.0, 100.0]


def test_repeat_last_warns_if_missing():
    store = NamedTimeSeriesStore[float]()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        store.repeat_last_value("nonexistent", 1.0)

        assert len(w) == 1
        assert "No time series with name 'nonexistent'" in str(w[0].message)


def test_clear_and_names():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("x", 0.0, 1.0)
    store.add_entry("y", 0.0, 2.0)
    assert set(store.name_set()) == {"x", "y"}

    store.clear()
    assert len(store) == 0


def test_dict_roundtrip():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("a", 0.0, 1.1)
    store.add_entry("b", 1.0, 2.2)

    d = store.to_dict()
    loaded = NamedTimeSeriesStore.from_dict(d)
    assert loaded.get_last_value_dict() == store.get_last_value_dict()


def test_yaml_roundtrip(tmp_path: Path):
    store = NamedTimeSeriesStore[float]()
    store.add_entry("obj_val", 0.0, 123.0)
    store.add_entry("obj_val", 1.0, 111.0)
    store.add_entry("obj_bound", 0.0, 1000.0)

    file_path = tmp_path / "store.yaml"
    store.save_yaml(file_path)

    loaded = NamedTimeSeriesStore[float].load_yaml(file_path)
    assert loaded.get_last_value_dict() == store.get_last_value_dict()
    assert loaded.name_set() == store.name_set()


def test_json_roundtrip(tmp_path: Path):
    store = NamedTimeSeriesStore[float]()
    store.add_entry("obj_val", 0.0, 123.0)
    store.add_entry("obj_val", 1.0, 111.0)
    store.add_entry("obj_bound", 0.0, 1000.0)

    file_path = tmp_path / "store.json"
    store.save_json(file_path)

    loaded = NamedTimeSeriesStore[float].load_json(file_path)
    assert loaded.get_last_value_dict() == store.get_last_value_dict()
    assert loaded.name_set() == store.name_set()
