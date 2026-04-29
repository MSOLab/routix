from pathlib import Path

import pytest

from routix.io import ArtifactLayout


RUN_ID = "20260429T120000_000000"


def _make_layout(tmp_path: Path) -> ArtifactLayout:
    return ArtifactLayout(run_root=tmp_path / RUN_ID, run_id=RUN_ID)


def test_zone_routing_final_vs_progress(tmp_path: Path):
    layout = _make_layout(tmp_path)

    final_path = layout.artifact_path(
        "instance_result_manifest",
        scenario_name="sc1",
        instance_name="ins1",
    )
    progress_path = layout.artifact_path(
        "step_log",
        scenario_name="sc1",
        instance_name="ins1",
        step_idx="3",
        method="run_neh",
    )

    instance_dir = tmp_path / RUN_ID / "sc1" / "ins1"
    assert final_path == instance_dir / "ins1_instance_result.yaml"
    assert progress_path == instance_dir / "progress" / "ins1_3-run_neh_step_log.yaml"


def test_scope_paths_for_run_and_scenario_kinds(tmp_path: Path):
    layout = _make_layout(tmp_path)

    summary = layout.artifact_path("summary_csv")
    benchmark = layout.artifact_path("benchmark_log", scenario_name="sc1")

    run_dir = tmp_path / RUN_ID
    assert summary == run_dir / f"{RUN_ID}_summary.csv"
    assert benchmark == run_dir / "sc1" / "sc1_benchmark.log"


def test_log_path_for_each_role(tmp_path: Path):
    layout = _make_layout(tmp_path)
    run_dir = tmp_path / RUN_ID

    assert layout.log_path("main") == run_dir / f"{RUN_ID}_main.log"
    assert (
        layout.log_path("multi_scenario_runner")
        == run_dir / f"{RUN_ID}_MultiScenarioRunner.log"
    )
    assert (
        layout.log_path("multi_instance_runner", scenario_name="sc1")
        == run_dir / "sc1" / f"{RUN_ID}_MultiInstanceRunner.log"
    )
    sir = layout.log_path(
        "single_instance_runner", scenario_name="sc1", instance_name="ins1"
    )
    sc = layout.log_path(
        "subroutine_controller", scenario_name="sc1", instance_name="ins1"
    )
    algo = layout.log_path(
        "algorithm", scenario_name="sc1", instance_name="ins1"
    )
    assert sir == run_dir / "sc1" / "ins1" / f"{RUN_ID}_SingleInstanceRunner.log"
    assert sc == run_dir / "sc1" / "ins1" / f"{RUN_ID}_SubroutineController.log"
    assert algo == sc, "algorithm role must share the SubroutineController.log file"


def test_register_kind_routes_to_zone(tmp_path: Path):
    layout = _make_layout(tmp_path)
    layout.register_kind(
        "phase_schedule",
        scope="instance",
        zone="progress",
        file_template="{instance_name}_{phase}.yaml",
    )

    path = layout.artifact_path(
        "phase_schedule",
        scenario_name="sc1",
        instance_name="ins1",
        phase="lb1",
    )

    assert (
        path
        == tmp_path / RUN_ID / "sc1" / "ins1" / "progress" / "ins1_lb1.yaml"
    )


def test_register_kind_duplicate_raises(tmp_path: Path):
    layout = _make_layout(tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        layout.register_kind(
            "instance_result_manifest",
            scope="instance",
            zone="final",
            file_template="dup.yaml",
        )


def test_register_kind_instance_without_zone_raises(tmp_path: Path):
    layout = _make_layout(tmp_path)

    with pytest.raises(ValueError, match="zone is required"):
        layout.register_kind(
            "missing_zone",
            scope="instance",
            file_template="{instance_name}_x.yaml",
        )


def test_register_kind_run_or_scenario_with_zone_raises(tmp_path: Path):
    layout = _make_layout(tmp_path)

    with pytest.raises(ValueError, match="does not support zone"):
        layout.register_kind(
            "bogus_run_with_zone",
            scope="run",
            zone="final",
            file_template="{run_id}_x.yaml",
        )

    with pytest.raises(ValueError, match="does not support zone"):
        layout.register_kind(
            "bogus_scenario_with_zone",
            scope="scenario",
            zone="progress",
            file_template="{scenario_name}_x.yaml",
        )


def test_schema_load_instance_without_zone_raises(tmp_path: Path):
    bad_schema = tmp_path / "bad.yaml"
    bad_schema.write_text(
        "schema_version: 1\n"
        "scopes: []\n"
        "zones:\n"
        "  instance: {final: '', progress: progress, report: report}\n"
        "logs: []\n"
        "artifacts:\n"
        "  - scope: instance\n"
        "    kind: missing_zone\n"
        "    file_template: '{instance_name}_x.yaml'\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="zone is required"):
        ArtifactLayout(
            run_root=tmp_path / RUN_ID, run_id=RUN_ID, schema_path=bad_schema
        )


def test_schema_load_run_with_zone_raises(tmp_path: Path):
    bad_schema = tmp_path / "bad.yaml"
    bad_schema.write_text(
        "schema_version: 1\n"
        "scopes: []\n"
        "zones:\n"
        "  instance: {final: '', progress: progress, report: report}\n"
        "logs: []\n"
        "artifacts:\n"
        "  - scope: run\n"
        "    zone: final\n"
        "    kind: bogus_run_zone\n"
        "    file_template: '{run_id}_x.yaml'\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not support zone"):
        ArtifactLayout(
            run_root=tmp_path / RUN_ID, run_id=RUN_ID, schema_path=bad_schema
        )


def test_stamp_restore_roundtrip(tmp_path: Path):
    original = _make_layout(tmp_path)
    original.register_kind(
        "phase_schedule",
        scope="instance",
        zone="progress",
        file_template="{instance_name}_{phase}.yaml",
    )

    stamped_path = original.stamp()
    assert stamped_path.exists()
    assert stamped_path.name == f"{RUN_ID}_artifact_layout.yaml"

    restored = ArtifactLayout(
        run_root=tmp_path / RUN_ID, run_id=RUN_ID, schema_path=stamped_path
    )

    for kind, kwargs in [
        ("instance_result_manifest", dict(scenario_name="sc1", instance_name="ins1")),
        ("step_log", dict(scenario_name="sc1", instance_name="ins1",
                          step_idx="0", method="m")),
        ("benchmark_log", dict(scenario_name="sc1")),
        ("summary_csv", dict()),
        ("phase_schedule", dict(scenario_name="sc1", instance_name="ins1",
                                phase="lb1")),
    ]:
        assert original.artifact_path(kind, **kwargs) == restored.artifact_path(
            kind, **kwargs
        )

    for role, kwargs in [
        ("main", dict()),
        ("multi_instance_runner", dict(scenario_name="sc1")),
        ("subroutine_controller", dict(scenario_name="sc1", instance_name="ins1")),
        ("algorithm", dict(scenario_name="sc1", instance_name="ins1")),
    ]:
        assert original.log_path(role, **kwargs) == restored.log_path(
            role, **kwargs
        )


def test_scenario_dir_duplicate_raises(tmp_path: Path):
    layout = _make_layout(tmp_path)
    layout.scenario_dir("sc1")

    with pytest.raises(ValueError, match="sc1"):
        layout.scenario_dir("sc1")


def test_find_artifacts_globs_free_placeholders(tmp_path: Path):
    layout = _make_layout(tmp_path)
    progress = layout.zone_dir(
        "progress", scenario_name="sc1", instance_name="ins1"
    )
    files = [
        progress / "ins1_0-init_step_log.yaml",
        progress / "ins1_1-improve_step_log.yaml",
        progress / "ins1_2-finalize_step_log.yaml",
    ]
    for f in files:
        f.write_text("data", encoding="utf-8")
    (progress / "unrelated.yaml").write_text("noise", encoding="utf-8")

    found = layout.find_artifacts(
        "step_log", scenario_name="sc1", instance_name="ins1"
    )

    assert sorted(found) == sorted(files)


def test_find_artifacts_does_not_create_directories(tmp_path: Path):
    layout = _make_layout(tmp_path)

    result = layout.find_artifacts(
        "step_log", scenario_name="sc1", instance_name="ins1"
    )

    assert result == []
    assert not (tmp_path / RUN_ID / "sc1" / "ins1" / "progress").exists()


def test_zone_dir_creates_directory(tmp_path: Path):
    layout = _make_layout(tmp_path)

    progress = layout.zone_dir(
        "progress", scenario_name="sc1", instance_name="ins1"
    )
    report = layout.zone_dir(
        "report", scenario_name="sc1", instance_name="ins1"
    )

    assert progress.is_dir()
    assert progress.name == "progress"
    assert report.is_dir()
    assert report.name == "report"
