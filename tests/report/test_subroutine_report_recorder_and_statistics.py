import pytest

from routix.report.subroutine_report import SubroutineReport
from routix.report.subroutine_report_statistics import SubroutineReportStatistics


@pytest.fixture
def sample_reports():
    return [
        SubroutineReport(elapsed_time=1.0, obj_value=10.0, obj_bound=12.0),
        SubroutineReport(elapsed_time=2.0, obj_value=8.0, obj_bound=10.0),
        SubroutineReport(elapsed_time=1.5, obj_value=None, obj_bound=None),
        SubroutineReport(elapsed_time=3.0, obj_value=7.0, obj_bound=9.0),
    ]


@pytest.fixture
def sample_method_call_counts():
    return {"foo": 2, "bar": 1}


def test_report_statistics(sample_reports, sample_method_call_counts, tmp_path):
    stats = SubroutineReportStatistics(
        name="test_instance",
        reports=sample_reports,
        method_call_counts=sample_method_call_counts,
    )
    assert stats.name == "test_instance"
    assert stats.reports == sample_reports
    assert stats.method_call_counts == sample_method_call_counts
    assert stats.has_valid_objective_value is True
    assert stats.first_report == sample_reports[0]
    assert stats.last_report == sample_reports[-1]
    min_report = stats.min_obj_report
    max_report = stats.max_obj_report
    assert min_report is not None and min_report.obj_value == 7.0
    assert max_report is not None and max_report.obj_value == 10.0
    assert stats.total_elapsed_time == pytest.approx(7.5)
    # Improvement ratio (minimize)
    assert stats.get_improvement_ratio(is_maximize=False) == pytest.approx(
        (10.0 - 7.0) / 10.0
    )
    # Improvement ratio (maximize)
    assert stats.get_improvement_ratio(is_maximize=True) == pytest.approx(
        (10.0 - 10.0) / 10.0
    )

    # Test serialization
    stats_dict = stats.to_dict()
    assert "methodCallCounts" in stats_dict
    assert stats_dict["methodCallCounts"] == f'"{sample_method_call_counts}"'

    # Test JSON/YAML serialization (file creation)
    json_path = tmp_path / "report.json"
    yaml_path = tmp_path / "report.yaml"
    stats.to_json(json_path, is_maximize=False)
    stats.to_yaml(yaml_path, is_maximize=False)
    assert json_path.exists()
    assert yaml_path.exists()
