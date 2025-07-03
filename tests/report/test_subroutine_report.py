from routix.report.subroutine_report import SubroutineReport


def test_subroutine_report_to_dict():
    report = SubroutineReport(
        elapsed_time=1.5,
        obj_value=42.0,
        obj_bound=100.0,
    )
    d = report.to_dict()
    assert d["elapsed_time"] == 1.5
    assert d["obj_value"] == 42.0
    assert d["obj_bound"] == 100.0
