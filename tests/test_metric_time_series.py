from pathlib import Path

from src.routix.metric_time_series import MetricTimeSeries


def test_add_and_last_value():
    mts = MetricTimeSeries[float]("test_series")
    assert len(mts) == 0
    assert mts.last_value is None

    mts.add(0.0, 100.0)
    assert len(mts) == 1
    assert mts.last_value == 100.0

    mts.add(1.0, 90.0)
    assert mts.last_value == 90.0
    assert mts.timestamps == [0.0, 1.0]
    assert mts.values == [100.0, 90.0]


def test_add_if_value_stg_last():
    mts = MetricTimeSeries[float]("inc_series")
    mts.add_if_value_stg_last(0.0, 100.0)
    mts.add_if_value_stg_last(1.0, 90.0)  # ignored
    mts.add_if_value_stg_last(2.0, 110.0)  # added

    assert mts.timestamps == [0.0, 2.0]
    assert mts.values == [100.0, 110.0]


def test_add_if_value_stl_last():
    mts = MetricTimeSeries[float]("dec_series")
    mts.add_if_value_stl_last(0.0, 100.0)
    mts.add_if_value_stl_last(1.0, 110.0)  # ignored
    mts.add_if_value_stl_last(2.0, 90.0)  # added

    assert mts.timestamps == [0.0, 2.0]
    assert mts.values == [100.0, 90.0]


def test_repeat_last():
    mts = MetricTimeSeries[float]("repeat_test")
    mts.repeat_last_value(0.0)  # nothing happens

    mts.add(1.0, 42.0)
    mts.repeat_last_value(2.0)
    assert mts.timestamps == [1.0, 2.0]
    assert mts.values == [42.0, 42.0]


def test_items_sorted():
    mts = MetricTimeSeries[float]("item_test")
    mts.add(10.0, 1.0)
    mts.add(5.0, 2.0)
    mts.add(7.0, 3.0)
    assert mts.items() == [(5.0, 2.0), (7.0, 3.0), (10.0, 1.0)]


def test_to_dict_and_from_dict_roundtrip():
    mts = MetricTimeSeries[float]("roundtrip")
    mts.add(0.0, 1.0)
    mts.add(2.0, 3.5)

    d = mts.to_dict()
    loaded = MetricTimeSeries.from_dict(d)
    assert loaded.name == "roundtrip"
    assert loaded.items() == [(0.0, 1.0), (2.0, 3.5)]


def test_yaml_save_and_load(tmp_path: Path):
    mts = MetricTimeSeries[float]("yaml_test")
    mts.add(1.0, 10.0)
    mts.add(2.0, 20.0)

    filepath = tmp_path / "series.yaml"
    mts.save_yaml(filepath)

    loaded = MetricTimeSeries.load_yaml(filepath)
    assert loaded.name == "yaml_test"
    assert loaded.items() == [(1.0, 10.0), (2.0, 20.0)]


def test_json_save_and_load(tmp_path: Path):
    mts = MetricTimeSeries[float]("json_test")
    mts.add(1.0, 10, note="first")
    mts.add(2.0, 20, note={"info": "second"})

    filepath = tmp_path / "series.json"
    mts.save_json(filepath)

    loaded = MetricTimeSeries.load_json(filepath)
    assert loaded.name == "json_test"
    assert loaded.items() == [(1.0, 10.0), (2.0, 20.0)]
