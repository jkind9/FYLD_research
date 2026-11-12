"""Validation exports use the existing scorers and control implementation."""

import importlib


def test_surface_validation_exports_existing_callables():
    validation = importlib.import_module(
        "experiments.04_surface_reconstruction.src.validation"
    )
    evaluation = importlib.import_module(
        "experiments.04_surface_reconstruction.src.evaluation"
    )
    for name in (
        "validate_points",
        "nearest",
        "distance_summary",
        "DistanceTotals",
        "SurfaceScorer",
    ):
        assert getattr(validation, name) is getattr(evaluation, name)


def test_fault_control_compatibility_import_is_same_callable():
    controls = importlib.import_module(
        "experiments.04_surface_reconstruction.src.validation.controls"
    )
    backend = importlib.import_module(
        "experiments.04_surface_reconstruction.src.backend"
    )
    assert backend.fault_points is controls.fault_points
