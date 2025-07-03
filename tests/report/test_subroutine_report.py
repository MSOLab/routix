from routix.report.subroutine_report import SubroutineReport


def test_subroutine_report_to_dict():
    report = SubroutineReport(
        elapsed_time=1.5,
        obj_value=42.0,
        obj_bound=100.0,
        obj_progress_log=[(0.1, 10.0, 20.0), (0.5, 30.0, 40.0)],
    )
    d = report.to_dict()
    assert d["elapsed_time"] == 1.5
    assert d["obj_value"] == 42.0
    assert d["obj_bound"] == 100.0
    assert d["obj_progress_log"] == [(0.1, 10.0, 20.0), (0.5, 30.0, 40.0)]
