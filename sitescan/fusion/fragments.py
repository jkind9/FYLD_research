"""TSDF fragments tied to corrected recording anchors."""

import numpy as np
import open3d as o3d

TRUNCATION_VOXELS = 4
DEPTH_RANGE_M = (0.1, 4.0)
KEYFRAMES_PER_FRAGMENT = 10


def _rgbd(depth_m: np.ndarray, colour: np.ndarray):
    """Open3D RGB and metre-depth images with the adopted fusion range."""
    near_m, far_m = DEPTH_RANGE_M
    depth = np.where(np.isfinite(depth_m) & (depth_m >= near_m), depth_m, 0.0).astype(np.float32)
    return o3d.geometry.RGBDImage.create_from_color_and_depth(
        o3d.geometry.Image(np.ascontiguousarray(colour)),
        o3d.geometry.Image(depth),
        depth_scale=1.0,
        depth_trunc=far_m,
        convert_rgb_to_intensity=False,
    )


class Fragments:
    """Volumes, extracted surfaces and current anchors retained between frames."""

    def __init__(self, *, voxel_m: float, keyframes_per_fragment: int = KEYFRAMES_PER_FRAGMENT):
        self.voxel_m = voxel_m
        self.keyframes_per_fragment = keyframes_per_fragment
        self._anchors: dict[int, np.ndarray] = {}
        self._fragment_anchors: dict[int, int] = {}
        self._volumes: dict[int, o3d.pipelines.integration.ScalableTSDFVolume] = {}
        self._points: dict[int, np.ndarray] = {}
        self._colours: dict[int, np.ndarray] = {}
        self._world: dict[int, tuple[bytes, np.ndarray]] = {}
        self._counts: dict[int, int] = {}

    def set_anchor(self, keyframe: int, world_from_anchor: np.ndarray) -> None:
        """Store the current anchor transform used to place a fragment in the world."""
        self._anchors[keyframe] = np.asarray(world_from_anchor, dtype=np.float64)

    def integrate(
        self,
        depth_m: np.ndarray,
        colour: np.ndarray,
        intrinsics,
        world_from_camera: np.ndarray,
        keyframe: int,
    ) -> None:
        """Fuse one scaled depth image relative to its fragment's placing anchor."""
        fragment = keyframe // self.keyframes_per_fragment
        if fragment not in self._fragment_anchors:
            first = fragment * self.keyframes_per_fragment
            # A saved slice may begin after the group's first anchor event.
            self._fragment_anchors[fragment] = first if first in self._anchors else keyframe
        anchor = self._anchors[self._fragment_anchors[fragment]]
        anchor_from_camera = np.linalg.inv(anchor) @ world_from_camera
        if fragment not in self._volumes:
            self._volumes[fragment] = o3d.pipelines.integration.ScalableTSDFVolume(
                voxel_length=self.voxel_m,
                sdf_trunc=TRUNCATION_VOXELS * self.voxel_m,
                color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,
            )
        height, width = depth_m.shape
        camera = o3d.camera.PinholeCameraIntrinsic(width, height, *intrinsics)
        self._volumes[fragment].integrate(
            _rgbd(depth_m, colour), camera, np.linalg.inv(anchor_from_camera)
        )
        self._points.pop(fragment, None)
        self._counts[fragment] = self._counts.get(fragment, 0) + 1

    def placing_anchor(self, keyframe: int) -> np.ndarray:
        """The current transform of the anchor placing this keyframe's fragment."""
        fragment = keyframe // self.keyframes_per_fragment
        return self._anchors[self._fragment_anchors[fragment]]

    def surface(self) -> np.ndarray:
        """World surface points in fragment order, following current anchor corrections."""
        parts = []
        for fragment, volume in self._volumes.items():
            anchor = self._anchors[self._fragment_anchors[fragment]]
            if fragment not in self._points:
                local = volume.extract_point_cloud()
                self._points[fragment] = np.asarray(local.points, dtype=np.float64)
                self._colours[fragment] = np.asarray(local.colors, dtype=np.float64)
                self._world.pop(fragment, None)
            stamp = anchor.tobytes()
            if self._world.get(fragment, (None,))[0] != stamp:
                points = self._points[fragment] @ anchor[:3, :3].T + anchor[:3, 3]
                self._world[fragment] = (stamp, points)
            parts.append(self._world[fragment][1])
        return np.concatenate(parts) if parts else np.zeros((0, 3))

    def colours(self) -> np.ndarray:
        """RGB values from 0 to 1 in the same order as surface points."""
        self.surface()
        if not self._volumes:
            return np.zeros((0, 3))
        return np.concatenate([self._colours[fragment] for fragment in self._volumes])

    def frames_per_fragment(self) -> dict[int, int]:
        """Integrated-frame counts keyed by fragment ID."""
        return dict(self._counts)
