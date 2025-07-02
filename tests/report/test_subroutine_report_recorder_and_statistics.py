import pytest

from src.routix.report.subroutine_report import SubroutineReport
from src.routix.report.subroutine_report_recorder import SubroutineReportRecorder
from src.routix.report.subroutine_report_statistics import SubroutineReportStatistics
from src.routix.report.subroutine_report_statistics_serializer import (
    SubroutineReportStatisticsSerializer,
)


@pytest.fixture
def sample_reports():
    return [
        SubroutineReport(
            elapsed_time=1.0,
            obj_value=10.0,
            obj_bound=12.0,
            obj_progress_log=[(0.5, 11.0, 13.0)],
        ),
        SubroutineReport(
            elapsed_time=2.0,
            obj_value=8.0,
            obj_bound=10.0,
            obj_progress_log=[(1.0, 9.0, 11.0)],
        ),
        SubroutineReport(
            elapsed_time=1.5, obj_value=None, obj_bound=None, obj_progress_log=[]
        ),
        SubroutineReport(
            elapsed_time=3.0,
            obj_value=7.0,
            obj_bound=9.0,
            obj_progress_log=[(2.0, 8.0, 10.0)],
        ),
    ]


def test_report_recorder_counts_and_append(sample_reports):
    recorder = SubroutineReportRecorder("test_instance")
    recorder.increment_method_call_count("foo")
    recorder.increment_method_call_count("foo")
    recorder.increment_method_call_count("bar")
    assert recorder.method_call_counts == {"foo": 2, "bar": 1}
    for r in sample_reports:
        recorder.append_report(r)
    assert recorder.reports == sample_reports


def test_report_statistics_properties_and_methods(sample_reports):
    recorder = SubroutineReportRecorder("test_instance")
    for r in sample_reports:
        recorder.append_report(r)
    stats = SubroutineReportStatistics(recorder)
    assert stats.name == "test_instance"
    assert stats.reports == sample_reports
    assert stats.found_feasible() is True
    assert stats.get_first() == sample_reports[0]
    assert stats.get_last() == sample_reports[-1]
    min_report = stats.get_minimum()
    max_report = stats.get_maximum()
    assert min_report is not None and min_report.obj_value == 7.0
    assert max_report is not None and max_report.obj_value == 10.0
    assert stats.total_elapsed() == pytest.approx(7.5)
    # Improvement ratio (minimize)
    assert stats.improvement_ratio(is_maximize=False) == pytest.approx(
        (10.0 - 7.0) / 10.0
    )
    # Improvement ratio (maximize)
    assert stats.improvement_ratio(is_maximize=True) == pytest.approx(
        (10.0 - 10.0) / 10.0
    )


def test_report_statistics_serializer_to_dict(sample_reports, tmp_path):
    recorder = SubroutineReportRecorder("test_instance")
    for r in sample_reports:
        recorder.append_report(r)
    stats = SubroutineReportStatistics(recorder)
    serializer = SubroutineReportStatisticsSerializer(stats)
    d = serializer.to_dict(is_maximize=False)
    assert d["instanceName"] == "test_instance"
    assert d["foundFeasibleSol"] is True
    assert d["totalElapsedTime"] == pytest.approx(7.5)
    assert d["firstObj"] == 10.0
    assert d["bestObj"] == 7.0
    assert d["reportCount"] == 4
    # Test JSON/YAML serialization (file creation)
    json_path = tmp_path / "report.json"
    yaml_path = tmp_path / "report.yaml"
    serializer.to_json(json_path, is_maximize=False)
    serializer.to_yaml(yaml_path, is_maximize=False)
    assert json_path.exists()
    assert yaml_path.exists()
