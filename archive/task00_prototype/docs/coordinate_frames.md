# Coordinate frames and measurement meaning

The desktop experiment uses metres and right-handed rigid transforms. The map has a declared up direction. That direction has not been checked against gravity or a site survey, so the output is not a level site map.

## Camera and depth

Camera axes are +X right, +Y down and +Z forward. Depth is distance along optical +Z, not distance along a viewing ray. For pixel column `u`, row `v` and depth `z`:

```text
x = (u - cx) * z / fx
y = (v - cy) * z / fy
```

The TUM PNG sample stores 5,000 units per metre. Zero or nonfinite depth is invalid. The reconstruction defaults to retaining 0.2–4 m. The publisher's depth correction is already applied; it must not be applied again.

The RGB and depth images are pre-registered by the publisher. This experiment uses the publisher's recommended ROS intrinsics: `fx=fy=525`, `cx=319.5`, `cy=239.5`, at 640×480. These are an approximation for the sample camera. It performs no additional undistortion. See the [TUM format and calibration specification](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats). A phone adapter must provide its own calibration; these values are not transferable to phone video.

## Poses and composition

`T_world_camera` maps camera column vectors into world coordinates. Translation is in metres. Saved trajectory quaternions use `qx,qy,qz,qw`. TUM timestamps are Unix seconds. A homogeneous point obeys `p_world = T_world_camera @ p_camera`.

| Branch | First camera transform | Subsequent transforms |
|---|---|---|
| Supplied-pose control | Identity after normalization | `inverse(GT_first) @ GT_current` |
| Estimated-pose branch | Identity, without ground truth | `previous_pose @ inverse(T_current_previous)` |

Open3D estimates a transform from the previous camera into the current camera. Its inverse is therefore needed when accumulating camera-to-world poses. Ground truth enters the estimated branch only after reconstruction, for evaluation.

Trajectory evaluation fits a rotation and translation, called rigid alignment (SE(3)). It does not fit scale. A similarity fit (Sim(3)) would also change scale and could hide a scale error. Metric scale here comes from supplied RGB-D depth. Image-only phone reconstruction requires a declared metric scale source before metre-valued measurements are accepted.

## Map frame and rasters

`plane_alignment(normal, offset)` converts an explicitly declared plane `normal · p + offset = 0` into `Z=0`, with the normal pointing up. The default normal is `(0,-1,0)` and offset is zero in first-camera coordinates. It yields map axes +X = camera right, +Y = camera forward and +Z = camera up. This is a declaration, not a fitted ground plane. `gravity_verified` remains false.

Array indices are `[row, column] = [y, x]`. Increasing columns follow +X; increasing rows follow +Y. PNG previews flip the array vertically, so their downward row direction follows -Y. Read `map_metadata.json` for the grid origin, bounds, resolution and display scale. Bounds include the outer edge of the final cell.

| Product | Meaning |
|---|---|
| `height_map.npy` | Default maximum observed height relative to the declared plane |
| `height_min.npy`, `height_max.npy` | Lowest and highest retained sample in each cell |
| `vertical_range.npy` | Maximum minus minimum; may include multiple surfaces or noise |
| `sample_count.npy` | Retained fused voxel centres per cell |
| `observed_mask.png` | A retained sample exists in that cell |
| `topdown_colour.png` | RGB of the highest retained sample |

NaN heights and zero counts mean unobserved. Black colour can also be an observed surface; use the mask. An observed cell does not prove empty space above or below it. A maximum-height map may hide a trench under an overhang. Voxel averaging and filtering can remove or blur thin structures. Do not fill unknown cells or call the counts confidence without a separately validated method.

For phone captures, record image rotation/crop, intrinsics at stored resolution, distortion treatment, depth alignment, pose direction, units and clock association. Resizing requires adjusted intrinsics; rotating the image requires a corresponding coordinate transformation. A future gravity or surveyed-plane alignment must record its source and error, rather than relabel the current declared frame.
