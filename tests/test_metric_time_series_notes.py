from pathlib import Path

from src.routix.metric_time_series import MetricTimeSeries


def test_add_with_note():
    mts = MetricTimeSeries[float]("noted_series")
    mts.add(0.0, 100.0, note="init guess")
    mts.add(1.0, 90.0, note={"source": "heuristic", "level": 1})

    assert mts.timestamp_note_map[0.0] == "init guess"
    assert mts.timestamp_note_map[1.0]["source"] == "heuristic"
    assert mts.timestamp_note_map[1.0]["level"] == 1


def test_add_without_note_does_not_override():
    mts = MetricTimeSeries[float]("note_protect")
    mts.add(0.0, 100.0, note="init")
    mts.add(0.0, 200.0)  # same timestamp, no note update

    assert mts.timestamp_note_map[0.0] == "init"
    assert mts.last_value == 200.0


def test_repeat_last_with_note():
    mts = MetricTimeSeries[float]("repeat_test")
    mts.add(1.0, 123.0, note="original")
    mts.repeat_last_value(2.0, note="reapplied")

    assert mts.timestamp_note_map[2.0] == "reapplied"
    assert mts.values == [123.0, 123.0]


def test_conditional_add_with_notes():
    mts = MetricTimeSeries[float]("stg_test")
    mts.add_if_value_stg_last(0.0, 100.0, note="start")
    mts.add_if_value_stg_last(1.0, 90.0, note="should_ignore")
    mts.add_if_value_stg_last(2.0, 120.0, note="improved")

    notes = mts.timestamp_note_map
    assert 1.0 not in notes
    assert notes[0.0] == "start"
    assert notes[2.0] == "improved"


def test_dict_roundtrip_with_notes():
    mts = MetricTimeSeries[float]("note_roundtrip")
    mts.add(0.0, 1.0, note="a")
    mts.add(1.0, 2.0, note={"tag": "b"})

    d = mts.to_dict()
    recovered = MetricTimeSeries.from_dict(d)

    assert recovered.timestamp_note_map[0.0] == "a"
    assert recovered.timestamp_note_map[1.0] == {"tag": "b"}
    assert recovered.items() == [(0.0, 1.0), (1.0, 2.0)]


def test_yaml_save_and_load_with_notes(tmp_path: Path):
    mts = MetricTimeSeries[float]("yaml_note_test")
    mts.add(5.0, 42.0, note="original")
    mts.add(6.0, 44.0, note={"meta": "info", "step": 2})

    file_path = tmp_path / "mts_with_notes.yaml"
    mts.save_yaml(file_path)

    loaded = MetricTimeSeries.load_yaml(file_path)
    assert loaded.name == "yaml_note_test"
    assert loaded.timestamp_note_map[5.0] == "original"
    assert loaded.timestamp_note_map[6.0]["step"] == 2
