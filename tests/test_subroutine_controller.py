import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from routix.constants import SubroutineFlowKeys
from routix.dynamic_data_object import DynamicDataObject
from routix.io import ArtifactLayout
from routix.report.subroutine_report import SubroutineReport
from routix.stopping_criteria import StoppingCriteria
from routix.subroutine_controller import SubroutineController


class MockSubroutineController(
    SubroutineController[StoppingCriteria, SubroutineReport]
):
    def __init__(
        self, name, subroutine_flow, stopping_criteria, start_dt=None, logger=None
    ):
        super().__init__(name, subroutine_flow, stopping_criteria, start_dt, logger)
        self._stop_condition_met = False
        self.mock_method = lambda **kwargs: None  # Default callable

    def is_stopping_condition(self, **kwargs) -> bool:
        return self._stop_condition_met

    def post_run_process(self):
        pass


@pytest.fixture
def mock_controller(tmp_path: Path) -> MockSubroutineController:
    subroutine_flow = DynamicDataObject.from_obj(
        [{SubroutineFlowKeys.METHOD: "mock_method"}]
    )
    stopping_criteria = StoppingCriteria({"criteria": "value"})
    ctrlr = MockSubroutineController(
        "test_experiment", subroutine_flow, stopping_criteria
    )
    ctrlr.set_working_dir(tmp_path)
    return ctrlr


def test_set_working_dir(mock_controller: MockSubroutineController):
    temp_dir = Path("temp_test_dir")
    mock_controller.set_working_dir(temp_dir)
    assert mock_controller._working_dir_path == temp_dir
    assert temp_dir.exists()
    temp_dir.rmdir()


def test_get_current_method_name(mock_controller: MockSubroutineController):
    mock_controller._method_context_mgr.push("step1")
    assert mock_controller.get_current_method_name() == "step1"


def test_get_current_method_name_multiple_push(
    mock_controller: MockSubroutineController,
):
    mock_controller._method_context_mgr.push("step1")
    mock_controller._method_context_mgr.push("step2")
    mock_controller._method_context_mgr.push("step3")
    assert mock_controller.get_current_method_name() == "step3"


def test_get_call_context_of_current_method(mock_controller: MockSubroutineController):
    mock_controller._method_context_mgr.push("step1")
    assert mock_controller._get_call_context_of_current_method() == "1-step1"


def test_get_file_path_for_subroutine(mock_controller: MockSubroutineController):
    temp_dir = Path("temp_test_dir")
    mock_controller.set_working_dir(temp_dir)
    mock_controller._method_context_mgr.push("step1")
    file_path = mock_controller.get_file_path_for_subroutine("_output.txt")
    assert file_path == temp_dir / "1-step1_output.txt"
    temp_dir.rmdir()


def test_run(mock_controller: MockSubroutineController):
    mock_controller.mock_method = MagicMock()
    mock_controller.run()
    mock_controller.mock_method.assert_called_once()


def test_call_method(mock_controller: MockSubroutineController):
    mock_controller.mock_method = MagicMock()
    mock_controller._call_method("mock_method", param1="value1")
    mock_controller.mock_method.assert_called_once_with(param1="value1")


def test_repeat(mock_controller: MockSubroutineController):
    mock_controller.mock_method = MagicMock()
    mock_controller.repeat(3, mock_controller._subroutine_flow)
    assert mock_controller.mock_method.call_count == 3


def test_is_stopping_condition(mock_controller: MockSubroutineController):
    assert not mock_controller.is_stopping_condition()
    mock_controller._stop_condition_met = True
    assert mock_controller.is_stopping_condition()


def test_set_random_seed(mock_controller: MockSubroutineController):
    mock_controller.set_random_seed(42)
    assert mock_controller.random_seed == 42


def test_default_logger_uses_hierarchical_name(
    mock_controller: MockSubroutineController,
):
    assert mock_controller.logger.name == "routix.MockSubroutineController"


def test_injected_logger_is_used():
    subroutine_flow = DynamicDataObject.from_obj(
        [{SubroutineFlowKeys.METHOD: "mock_method"}]
    )
    stopping_criteria = StoppingCriteria({"criteria": "value"})
    custom = logging.getLogger("test.custom.controller")
    ctrlr = MockSubroutineController(
        "test", subroutine_flow, stopping_criteria, logger=custom
    )
    assert ctrlr.logger is custom


def test_call_method_log_record_uses_controller_logger(
    mock_controller: MockSubroutineController, caplog: pytest.LogCaptureFixture
):
    mock_controller.mock_method = MagicMock()
    with caplog.at_level(logging.INFO, logger="routix.MockSubroutineController"):
        mock_controller._call_method("mock_method", param1="value1")
    assert any(rec.name == "routix.MockSubroutineController" for rec in caplog.records)


def test_artifact_layout_defaults_to_none(
    mock_controller: MockSubroutineController,
):
    assert mock_controller._artifact_layout is None
    assert mock_controller._artifact_scenario_name is None
    assert mock_controller._artifact_instance_name is None


def test_set_artifact_layout_stores_layout_and_coords(
    mock_controller: MockSubroutineController, tmp_path: Path
):
    layout = ArtifactLayout(run_root=tmp_path / "RUN", run_id="RUN")

    mock_controller.set_artifact_layout(
        layout, scenario_name="scA", instance_name="insX"
    )

    assert mock_controller._artifact_layout is layout
    assert mock_controller._artifact_scenario_name == "scA"
    assert mock_controller._artifact_instance_name == "insX"


def test_set_artifact_layout_requires_keyword_only_coords(
    mock_controller: MockSubroutineController, tmp_path: Path
):
    layout = ArtifactLayout(run_root=tmp_path / "RUN", run_id="RUN")

    with pytest.raises(TypeError):
        mock_controller.set_artifact_layout(layout, "scA", "insX")  # type: ignore[misc] # ty: ignore[missing-argument, too-many-positional-arguments]


def test_set_artifact_layout_does_not_replace_working_dir(
    mock_controller: MockSubroutineController, tmp_path: Path
):
    wd = tmp_path / "wd"
    mock_controller.set_working_dir(wd)
    layout = ArtifactLayout(run_root=tmp_path / "RUN", run_id="RUN")

    mock_controller.set_artifact_layout(layout, scenario_name="s", instance_name="i")

    # The two settings are independent: layout binding must not clobber working_dir.
    assert mock_controller._working_dir_path == wd
    assert mock_controller._artifact_layout is layout
