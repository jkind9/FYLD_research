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


def test_cli_depth_choice_reaches_the_depth_layer(tmp_path):
    """--depth swaps the method; a missing local checkpoint is reported by that layer."""
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
            "--depth",
            "depth-anything",
            "--depth-checkpoint",
            str(tmp_path / "missing-checkpoint"),
            "--device",
            "cpu",
        ]
    )
    assert result.returncode == 2, result.stderr
    assert '"method": "depth_anything_v2_metric_indoor_small"' in result.stdout
    assert "Local model checkpoint directory not found" in result.stdout


def test_cli_refuses_recorded_depth_without_a_dataset(tmp_path):
    run_root = tmp_path / "runs"
    result = invoke(
        [
            "-m",
            "src.walkthrough.cli",
            "--report",
            "report.json",
            "--bundle",
            "bundle",
            "--run-root",
            str(run_root),
            "--depth",
            "recorded",
        ]
    )
    assert result.returncode == 2
    assert "--depth recorded needs --dataset" in result.stderr
    assert not run_root.exists()


def _depth_args(**overrides):
    import argparse

    settings = {"depth": "depth-anything", "depth_checkpoint": None, "dataset": Path("tum"), "device": "cpu",
                "points_per_frame": 50, "depth_scale": None, "pose_noise_m": None, "chain_smoothing_frames": None}
    return argparse.Namespace(**{**settings, **overrides})


@pytest.mark.parametrize(
    "scale,source,control",
    [
        ("overlap-chain", "OverlapChainScale", None),
        ("pose-triangulated", "PoseTriangulatedScale", "reference"),
        ("reference-frame", "ReferenceFrameScale", "reference"),
        ("reference-global", "ReferenceGlobalScale", "reference"),
    ],
)
def test_cli_depth_scale_wraps_depth_anything_on_the_cpu(scale, source, control):
    from src.walkthrough.cli import depth_choice
    from src.walkthrough.steps.depth import DepthAnythingV2Metric
    from src.walkthrough.steps.depth_scale import ScaleCorrected

    method = depth_choice(_depth_args(depth_scale=scale))

    assert isinstance(method, ScaleCorrected)
    assert isinstance(method.base, DepthAnythingV2Metric) and method.base.device == "cpu"
    assert type(method.scale).__name__ == source
    assert method.control == control


def test_cli_chain_anchored_to_poses_combines_the_two_sources():
    from src.walkthrough.cli import depth_choice
    from src.walkthrough.steps.depth_scale import (
        AnchoredScale,
        OverlapChainScale,
        PoseTriangulatedScale,
    )

    method = depth_choice(_depth_args(depth_scale="overlap-chain-pose-anchor", pose_noise_m=0.0))

    assert isinstance(method.scale, AnchoredScale)
    assert isinstance(method.scale.consistent, OverlapChainScale)
    assert isinstance(method.scale.metric, PoseTriangulatedScale) and method.scale.metric.noise_m == 0.0
    assert method.control == "reference"


def test_cli_pose_triangulated_reads_the_datasets_groundtruth():
    from src.walkthrough.cli import depth_choice

    method = depth_choice(_depth_args(depth_scale="pose-triangulated"))

    assert method.scale.groundtruth == Path("tum") / "groundtruth.txt"


def test_cli_pose_noise_and_chain_smoothing_reach_their_scale_sources():
    from src.walkthrough.cli import depth_choice

    noisy = depth_choice(_depth_args(depth_scale="pose-triangulated", pose_noise_m=0.0))
    smoothed = depth_choice(_depth_args(depth_scale="overlap-chain", chain_smoothing_frames=5))
    default = depth_choice(_depth_args(depth_scale="pose-triangulated"))

    assert noisy.scale.noise_m == 0.0
    assert smoothed.scale.smoothing_frames == 5
    assert default.scale.noise_m == 0.005  # unchanged when the flag is absent


def test_cli_refuses_scale_settings_without_their_scale_source(tmp_path):
    run_root = tmp_path / "runs"
    result = invoke(["-m", "src.walkthrough.cli", "--dataset", "tum", "--run-root", str(run_root),
                     "--depth", "depth-anything", "--depth-scale", "overlap-chain", "--pose-noise-m", "0"])
    assert result.returncode == 2
    assert "--pose-noise-m applies only to --depth-scale pose-triangulated" in result.stderr
    assert not run_root.exists()


def test_cli_refuses_depth_scale_on_other_depth_choices(tmp_path):
    run_root = tmp_path / "runs"
    result = invoke(["-m", "src.walkthrough.cli", "--dataset", "tum", "--run-root", str(run_root),
                     "--depth", "recorded", "--depth-scale", "overlap-chain"])
    assert result.returncode == 2
    assert "--depth-scale applies only to" in result.stderr
    assert not run_root.exists()


def test_cli_refuses_reference_scale_without_a_dataset(tmp_path):
    run_root = tmp_path / "runs"
    result = invoke(["-m", "src.walkthrough.cli", "--report", "report.json", "--bundle", "bundle",
                     "--run-root", str(run_root), "--depth", "depth-anything", "--depth-scale", "pose-triangulated"])
    assert result.returncode == 2
    assert "--depth-scale pose-triangulated needs --dataset" in result.stderr
    assert not run_root.exists()
