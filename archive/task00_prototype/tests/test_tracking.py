import numpy as np

from fyld_scene_mapping.geometry import Intrinsics
from fyld_scene_mapping.reconstruction import (
    ReconstructionSettings,
    depth_overlap,
    estimate_motion,
    rgbd_image,
)


def test_overlap_uses_configured_depth_range() -> None:
    k = Intrinsics(64, 48, 50.0, 50.0, 31.5, 23.5)
    depth = np.full((48, 64), 5.0)
    assert depth_overlap(depth, depth, np.eye(4), k, 0.2, 6.0) == 1.0
    assert depth_overlap(depth, depth, np.eye(4), k, 0.2, 4.0) == 0.0


def test_textureless_plane_is_rejected_without_claiming_motion() -> None:
    k = Intrinsics(64, 48, 50.0, 50.0, 31.5, 23.5)
    depth = np.ones((48, 64))
    image = rgbd_image(np.full((48, 64, 3), 128, dtype=np.uint8), depth)
    motion, diagnostic = estimate_motion(
        image, image, depth, depth, k, ReconstructionSettings()
    )
    assert motion is None and "unobservable" in diagnostic["reason"]
