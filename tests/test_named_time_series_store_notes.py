import warnings
from pathlib import Path

from src.routix.metric_time_series import NamedTimeSeriesStore


def test_add_entry_with_note():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("series1", 0.0, 100.0, note="initial")
    ts = store.get_or_create("series1")

    assert ts.last_value == 100.0
    assert ts.timestamp_note_map[0.0] == "initial"


def test_add_if_stg_with_note():
    store = NamedTimeSeriesStore[float]()
    store.add_if_stg("max_series", 0.0, 10.0, note="start")
    store.add_if_stg("max_series", 1.0, 9.0, note="ignored")  # should not be added
    store.add_if_stg("max_series", 2.0, 20.0, note="better")

    notes = store.get_or_create("max_series").timestamp_note_map
    assert 1.0 not in notes
    assert notes[0.0] == "start"
    assert notes[2.0] == "better"


def test_add_if_stl_with_note():
    store = NamedTimeSeriesStore[float]()
    store.add_if_stl("min_series", 0.0, 10.0, note="init")
    store.add_if_stl("min_series", 1.0, 12.0, note="ignored")  # should not be added
    store.add_if_stl("min_series", 2.0, 5.0, note={"event": "drop"})

    ts = store.get_or_create("min_series")
    assert 1.0 not in ts.timestamp_note_map
    assert ts.timestamp_note_map[2.0]["event"] == "drop"


def test_repeat_last_with_note():
    store = NamedTimeSeriesStore[float]()
    store.add_entry("repeatable", 0.0, 123.0, note="first")
    store.repeat_last_value("repeatable", 1.0, note="copied")

    ts = store.get_or_create("repeatable")
    assert ts.values == [123.0, 123.0]
    assert ts.timestamp_note_map[1.0] == "copied"


def test_repeat_last_warns_on_missing_series():
    store = NamedTimeSeriesStore[float]()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        store.repeat_last_value("no_such", 1.0, note="ignored")

        assert len(w) == 1
        assert "No time series with name 'no_such'" in str(w[0].message)


def test_yaml_roundtrip_with_notes(tmp_path: Path):
    store = NamedTimeSeriesStore[float]()
    store.add_entry("obj_value", 0.0, 100.0, note="init")
    store.add_if_stl("obj_value", 1.0, 90.0, note="step 2")
    store.add_entry("obj_bound", 0.0, 200.0, note={"type": "bound", "phase": 1})

    file_path = tmp_path / "store_with_notes.yaml"
    store.save_yaml(file_path)

    loaded = NamedTimeSeriesStore[float].load_yaml(file_path)
    assert loaded.get_last_value_dict() == store.get_last_value_dict()
    assert loaded.get_or_create("obj_value").timestamp_note_map[0.0] == "init"
    assert loaded.get_or_create("obj_bound").timestamp_note_map[0.0]["type"] == "bound"
