"""The fused surface as fragments that follow ARCore's pose corrections.

A *fragment* is one Open3D signed-distance volume holding the frames of a group of consecutive keyframes
(10 by default, about 10 s), stored relative to a received keyframe anchor in that group. When ARCore moves that
anchor, the fragment's points move with it; nothing is re-fused. A frame's pose is taken relative to the
anchor's pose as known when the frame is fused, so world = anchor_now @ inverse(anchor_then) @ camera pose.
"""

from __future__ import annotations

import numpy as np
import open3d as o3d

TRUNCATION_VOXELS = 4  # Open3D tutorial convention, as in experiments/sfm/run_dense.py
DEPTH_RANGE_M = (0.1, 4.0)  # inherited RGBD_MAX_DEPTH_M, as in experiments/sfm/run_dense.py


class Fragments:
    def __init__(self, *, voxel_m: float, keyframes_per_fragment: int = 10):
        self.voxel_m = voxel_m
        self.keyframes_per_fragment = keyframes_per_fragment
        self._anchors: dict[int, np.ndarray] = {}  # keyframe id -> world_from_anchor now
        self._fragment_anchors: dict[int, int] = {}
        self._volumes: dict[int, o3d.pipelines.integration.ScalableTSDFVolume] = {}
        self._points: dict[int, np.ndarray] = {}  # fragment -> points in its anchor's frame, when extracted
        self._world: dict[int, tuple[bytes, np.ndarray]] = {}  # fragment -> (anchor used, points in the world)
        self._frames: dict[int, int] = {}

    def set_anchor(self, keyframe: int, world_from_anchor: np.ndarray) -> None:
        self._anchors[keyframe] = np.asarray(world_from_anchor, dtype=np.float64)

    def integrate(self, depth_m: np.ndarray, colour: np.ndarray, intrinsics, world_from_camera: np.ndarray,
                  keyframe: int) -> None:
        """Fuses one sized depth image; world_from_camera uses OpenCV camera axes."""
        fragment = keyframe // self.keyframes_per_fragment
        if fragment not in self._fragment_anchors:
            first = fragment * self.keyframes_per_fragment
            # A camera session can start after the group's first anchor was created.
            self._fragment_anchors[fragment] = first if first in self._anchors else keyframe
        anchor_from_camera = np.linalg.inv(self._anchors[self._fragment_anchors[fragment]]) @ world_from_camera
        if fragment not in self._volumes:
            self._volumes[fragment] = o3d.pipelines.integration.ScalableTSDFVolume(
                voxel_length=self.voxel_m, sdf_trunc=TRUNCATION_VOXELS * self.voxel_m,
                color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
        h, w = depth_m.shape
        near, far = DEPTH_RANGE_M
        depth = np.where(np.isfinite(depth_m) & (depth_m >= near), depth_m, 0.0).astype(np.float32)
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(np.ascontiguousarray(colour)), o3d.geometry.Image(depth),
            depth_scale=1.0, depth_trunc=far, convert_rgb_to_intensity=False)
        fx, fy, cx, cy = intrinsics
        self._volumes[fragment].integrate(rgbd, o3d.camera.PinholeCameraIntrinsic(w, h, fx, fy, cx, cy),
                                          np.linalg.inv(anchor_from_camera))
        self._points.pop(fragment, None)
        self._frames[fragment] = self._frames.get(fragment, 0) + 1

    def surface(self) -> np.ndarray:
        """All fragments' surface points in the world as ARCore now sees it (N x 3, metres)."""
        parts = []
        for fragment, volume in self._volumes.items():
            anchor = self._anchors[self._fragment_anchors[fragment]]
            if fragment not in self._points:
                self._points[fragment] = np.asarray(volume.extract_point_cloud().points, dtype=np.float64)
                self._world.pop(fragment, None)
            if self._world.get(fragment, (None,))[0] != anchor.tobytes():
                self._world[fragment] = (anchor.tobytes(), self._points[fragment] @ anchor[:3, :3].T + anchor[:3, 3])
            parts.append(self._world[fragment][1])
        return np.concatenate(parts) if parts else np.zeros((0, 3))

    def frames_per_fragment(self) -> dict[int, int]:
        return dict(self._frames)
