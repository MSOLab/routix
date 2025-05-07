import pytest

from src.clad.cpsat.cp_model_with_optional_interval import CpModelWithOptionalInterval


@pytest.fixture
def model():
    """Fixture to create a CpModelWithOptionalInterval instance."""
    return CpModelWithOptionalInterval(horizon=100)


def test_initialization(model: CpModelWithOptionalInterval):
    """Test that the model initializes correctly."""
    assert model.horizon == 100
    assert isinstance(model.var_op_start, dict)
    assert isinstance(model.var_op_end, dict)
    assert isinstance(model.var_op_is_present, dict)
    assert isinstance(model.var_op_intvl, dict)


def test_define_optional_interval_var(model: CpModelWithOptionalInterval):
    """Test the define_optional_interval_var method."""
    job_idx = "job1"
    stage_idx = "stage1"
    mc_idx = "mc1"
    processing_time = 10

    model.define_optional_interval_var(job_idx, stage_idx, mc_idx, processing_time)

    # Check that variables are created and stored correctly
    assert job_idx in model.var_op_start
    assert stage_idx in model.var_op_start[job_idx]
    assert mc_idx in model.var_op_start[job_idx][stage_idx]

    start_var = model.var_op_start[job_idx][stage_idx][mc_idx]
    end_var = model.var_op_end[job_idx][stage_idx][mc_idx]
    is_present_var = model.var_op_is_present[job_idx][stage_idx][mc_idx]
    interval_var = model.var_op_intvl[job_idx][stage_idx][mc_idx]

    assert start_var is not None
    assert end_var is not None
    assert is_present_var is not None
    assert interval_var is not None

    # Check variable properties
    assert start_var.Name() == "start_job1_stage1_mc1"
    assert end_var.Name() == "end_job1_stage1_mc1"
    assert is_present_var.Name() == "is_present_job1_stage1_mc1"
    assert interval_var.Name() == "interval_job1_stage1_mc1"


def test_multiple_operations(model: CpModelWithOptionalInterval):
    """Test adding multiple operations to the model."""
    operations = [
        ("job1", "stage1", "mc1", 10),
        ("job1", "stage2", "mc2", 15),
        ("job2", "stage1", "mc1", 20),
    ]

    for job_idx, stage_idx, mc_idx, processing_time in operations:
        model.define_optional_interval_var(job_idx, stage_idx, mc_idx, processing_time)

    # Check that all operations are added correctly
    for job_idx, stage_idx, mc_idx, _ in operations:
        assert job_idx in model.var_op_start
        assert stage_idx in model.var_op_start[job_idx]
        assert mc_idx in model.var_op_start[job_idx][stage_idx]
        assert mc_idx in model.var_op_end[job_idx][stage_idx]
        assert mc_idx in model.var_op_is_present[job_idx][stage_idx]
        assert mc_idx in model.var_op_intvl[job_idx][stage_idx]
