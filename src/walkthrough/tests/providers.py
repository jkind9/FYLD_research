"""Software-only arrays and pair transforms; no real depth or area method."""

import importlib

import numpy as np


def depth(row, calibration):
    shape = calibration.height, calibration.width
    return np.full(shape, 2.0), np.ones(shape, dtype=bool)


def mapping(surface):
    return {
        "status": "fixture_only",
        "physical_dimensions": None,
        "physical_area": None,
    }


class Backend:
    def estimate(self, source, target):
        owner = importlib.import_module(
            "experiments.03_camera_pose_estimation.src.backend"
        )
        return owner.PairResult(True, np.eye(4), "software_control_identity_transform")


class Detector:
    def predict(self, image):
        from PIL import Image

        owner = importlib.import_module(
            "experiments.06_object_recognition.pilot.localisation"
        )
        with Image.open(image) as pixels:
            width, height = pixels.size
        return [owner.Detection((0, 0, width, height), "fixture", 0, 1.0)], {
            "image_shape_hw": [height, width],
            "source": "software_control",
        }
