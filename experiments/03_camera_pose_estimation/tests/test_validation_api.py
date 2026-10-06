"""Validation exports the established tracking scorer without a runner."""

import importlib
import subprocess
import sys


def test_tracking_validation_exports_original_callables():
    package = "experiments.03_camera_pose_estimation.src"
    validation = importlib.import_module(f"{package}.validation")
    evaluation = importlib.import_module(f"{package}.evaluation")
    assert validation.evaluate is evaluation.evaluate
    assert validation.read_references is evaluation.read_references
    assert validation.evaluate([], []) == evaluation.evaluate([], [])


def test_tracking_validation_import_does_not_load_runner():
    script = (
        "import importlib, sys; "
        "importlib.import_module('experiments.03_camera_pose_estimation.src.validation'); "
        "assert 'experiments.03_camera_pose_estimation.src.run' not in sys.modules"
    )
    subprocess.run([sys.executable, "-B", "-c", script], check=True)
