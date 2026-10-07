"""Fresh-process imports, recorded-input CLI and historical entrypoints."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.walkthrough.tests.test_adapters import bundle

ROOT = Path(__file__).resolve().parents[3]


def invoke(args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-B", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_importing_root_has_no_models_or_output(tmp_path):
    result = invoke(
        [
            "-c",
            (
                "import sys; from src.walkthrough import pipeline,cli; "
                "assert not any(n in sys.modules for n in ('torch','ultralytics','open3d'))"
            ),
        ],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert tuple(tmp_path.iterdir()) == ()


def test_methods_import_without_root_package(tmp_path):
    result = invoke(
        [
            "-c",
            (
                "import importlib,sys; "
                "names=('experiments.03_camera_pose_estimation.src.tracking',"
                "'experiments.04_surface_reconstruction.src.metric_surface',"
                "'experiments.06_object_recognition.pilot.association'); "
                "[importlib.import_module(n) for n in names]; "
                "assert 'src.walkthrough' not in sys.modules"
            ),
        ],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert tuple(tmp_path.iterdir()) == ()


@pytest.mark.parametrize(
    "module",
    [
        "src.walkthrough.cli",
        "experiments.03_camera_pose_estimation.src.run",
        "experiments.04_surface_reconstruction.src.run",
        "experiments.06_object_recognition.pilot.replay",
        "experiments.06_object_recognition.experiments.04_geometry_identity.run",
    ],
)
def test_existing_and_root_entrypoints_remain_standalone(module):
    result = invoke(["-m", module, "--help"])
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_cli_reports_real_depth_unavailable_and_returns_failure(tmp_path):
    report = bundle(tmp_path / "bundle")
    result = invoke(
        [
            "-m",
            "src.walkthrough.cli",
            "--report",
            str(report),
            "--bundle",
            str(report.parent),
            "--run-root",
            str(tmp_path / "runs"),
        ]
    )
    assert result.returncode == 2, result.stderr
    assert '"name": "depth"' in result.stdout
    assert "Task54" in result.stdout
    assert '"complete": false' in result.stdout


@pytest.mark.parametrize(
    "flags",
    [
        ["--report", "report.json"],
        ["--dataset", "dataset", "--bundle", "bundle"],
    ],
)
def test_cli_refuses_incomplete_or_mixed_source_before_creating_run(tmp_path, flags):
    run_root = tmp_path / "runs"
    result = invoke(["-m", "src.walkthrough.cli", *flags, "--run-root", str(run_root)])
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "--report and --bundle" in result.stderr
    assert not run_root.exists()
