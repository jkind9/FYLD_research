"""Read validated Camera2 exports without inventing depth or camera poses."""

from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class PhoneFrame:
    frame_id: str
    camera_id: str
    image_bytes: bytes
    image_width: int
    image_height: int
    timestamp_ns: int
    timestamp_source: str
    frame_number: int
    crop_region: tuple[int, int, int, int]
    rotation_degrees: int
    sensor_pixel_array_size: tuple[int, int]
    active_array_rect: tuple[int, int, int, int]
    pre_correction_active_array_rect: tuple[int, int, int, int]
    intrinsics: tuple[float, ...]
    intrinsics_pixel_grid: str
    lens_distortion: tuple[float, ...] | None
    distortion_correction_mode: int | None
    distortion_correction_mode_name: str
    geometry_ready: bool
    geometry_unavailable_reason: str | None
    sensor_to_image_crop_scale: tuple[float, float]
    depth_bytes: bytes | None
    depth_unavailable_reason: str | None
    pose: None
    pose_unavailable_reason: str
    world_id: None
    segment_id: None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _camera_for_frame(report: dict[str, Any], camera_id: str) -> dict[str, Any]:
    cameras = report.get("cameras")
    _require(isinstance(cameras, list), "Camera metadata list is missing")
    matches = [camera for camera in cameras
               if isinstance(camera, dict) and camera.get("id") == camera_id]
    _require(len(matches) == 1, f"camera metadata is missing or duplicated for camera {camera_id}")
    return matches[0]


def _rect(value: Any, field_name: str) -> tuple[int, int, int, int]:
    _require(isinstance(value, list) and len(value) == 4
             and all(type(item) is int for item in value),
             f"Camera {field_name} is invalid")
    left, top, right, bottom = value
    _require(0 <= left < right and 0 <= top < bottom,
             f"Camera {field_name} is invalid")
    return left, top, right, bottom


def _inside(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> bool:
    return (outer[0] <= inner[0] < inner[2] <= outer[2]
            and outer[1] <= inner[1] < inner[3] <= outer[3])


def _camera_geometry(camera: dict[str, Any], capture: dict[str, Any]
                     ) -> tuple[tuple[int, int], tuple[int, int, int, int],
                                tuple[int, int, int, int], tuple[float, ...],
                                tuple[float, ...] | None, int | None, str,
                                bool, str | None]:
    pixel_size = camera.get("pixel_array_size")
    _require(isinstance(pixel_size, list) and len(pixel_size) == 2
             and all(type(value) is int and value > 0 for value in pixel_size),
             "Camera sensor pixel array size is invalid")
    width, height = pixel_size
    active_array = _rect(camera.get("active_array_rect"), "active array rectangle")
    pre_correction_array = _rect(
        camera.get("pre_correction_active_array_rect"), "pre-correction active array rectangle"
    )
    _require(_inside(active_array, (0, 0, width, height))
             and _inside(pre_correction_array, (0, 0, width, height))
             and _inside(active_array, pre_correction_array),
             "Active-array rectangle falls outside the sensor pixel array")
    _require(camera.get("intrinsic_calibration_grid") == "pre_correction_active_array",
             "Intrinsic calibration grid is missing or unknown")

    calibration = camera.get("intrinsic_calibration")
    _require(isinstance(calibration, dict) and calibration.get("available") is True,
             "Camera intrinsic calibration is unavailable")
    values = calibration.get("value")
    _require(isinstance(values, list) and len(values) >= 5
             and all(type(value) in (int, float) for value in values),
             "Camera intrinsic calibration is invalid")
    intrinsics = tuple(float(value) for value in values)
    _require(all(math.isfinite(value) for value in intrinsics)
             and intrinsics[0] > 0 and intrinsics[1] > 0,
             "Camera intrinsic calibration contains invalid values")
    mode = capture.get("distortion_correction_mode")
    mode_name = capture.get("distortion_correction_mode_name")
    _require(mode is None or (type(mode) is int and mode >= 0),
             "Capture distortion-correction mode is invalid")
    expected_mode_name = {0: "OFF", 1: "FAST", 2: "HIGH_QUALITY"}.get(
        mode, "UNAVAILABLE" if mode is None else f"UNKNOWN_{mode}"
    )
    _require(mode_name == expected_mode_name,
             "Capture distortion-correction mode name disagrees with its value")
    crop = tuple(capture["crop_region"])
    geometry_ready = mode == 0
    if mode == 0:
        _require(_inside(crop, pre_correction_array),
                 "Capture crop falls outside the selected active array rectangle")
        geometry_reason = None
    elif mode is None:
        geometry_reason = "Distortion-correction mode is unavailable, so the calibration grid is unknown."
    else:
        _require(_inside(crop, active_array),
                 "Capture crop falls outside the selected active array rectangle")
        geometry_reason = "Distortion correction is enabled; raw pre-correction intrinsics need conversion."
    lens_distortion = camera.get("lens_distortion")
    distortion_values = None
    if isinstance(lens_distortion, dict) and lens_distortion.get("available") is True:
        values = lens_distortion.get("value")
        _require(isinstance(values, list) and values
                 and all(type(value) in (int, float) and math.isfinite(value) for value in values),
                 "Camera lens-distortion metadata is invalid")
        distortion_values = tuple(float(value) for value in values)
    return ((width, height), active_array, pre_correction_array, intrinsics,
            distortion_values, mode, mode_name, geometry_ready, geometry_reason)


def _read_image(bundle_root: Path, report: dict[str, Any], capture: dict[str, Any]) -> bytes:
    name = capture["file"]
    relative = PurePosixPath(name)
    _require(not relative.is_absolute() and all(part not in {".", ".."} for part in relative.parts),
             "Invalid capture path")
    root = Path(bundle_root).resolve(strict=True)
    path = root.joinpath(*relative.parts).resolve(strict=True)
    _require(path.is_relative_to(root) and path.is_file(), "Capture path escapes the session")
    payload = path.read_bytes()
    expected = report["files"][name]
    _require(len(payload) == expected["bytes"]
             and hashlib.sha256(payload).hexdigest() == expected["sha256"],
             f"Capture changed after export validation: {name}")
    try:
        with Image.open(io.BytesIO(payload)) as image:
            size = image.size
            image.load()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ValueError(f"Capture is not a readable image: {name}") from error
    _require(size == (capture["width"], capture["height"]),
             f"Decoded image grid disagrees with capture metadata: {name}")
    return payload


def read_phone_session(report: dict[str, Any], bundle_root: Path,
                       validate_export: Callable[[Any, Path], dict[str, Any]]
                       ) -> tuple[PhoneFrame, ...]:
    """Validate and read a Camera2 export using its phone-session validator."""
    report = validate_export(report, bundle_root)
    checks = {check["id"]: check for check in report["checks"]}
    sensor_check = checks.get("arcore_depth_and_pose")
    unavailable_reason = (
        sensor_check["reason"] if sensor_check and sensor_check["reason"]
        else "The camera recording contains no depth or pose payload."
    )
    frames: list[PhoneFrame] = []
    for capture in report["captures"]:
        camera = _camera_for_frame(report, capture["camera_id"])
        (sensor_size, active_array, pre_correction_array, intrinsics, lens_distortion,
         mode, mode_name, geometry_ready, geometry_reason) = _camera_geometry(camera, capture)
        image_bytes = _read_image(bundle_root, report, capture)
        crop = capture["crop_region"]
        frames.append(PhoneFrame(
            frame_id=f"{report['session_id']}:{capture['camera_id']}:{capture['frame_number']}",
            camera_id=capture["camera_id"],
            image_bytes=image_bytes,
            image_width=capture["width"],
            image_height=capture["height"],
            timestamp_ns=capture["sensor_timestamp_ns"],
            timestamp_source=capture["timestamp_source"],
            frame_number=capture["frame_number"],
            crop_region=tuple(capture["crop_region"]),
            rotation_degrees=capture["rotation_degrees"],
            sensor_pixel_array_size=sensor_size,
            active_array_rect=active_array,
            pre_correction_active_array_rect=pre_correction_array,
            intrinsics=intrinsics,
            intrinsics_pixel_grid="pre_correction_active_array",
            lens_distortion=lens_distortion,
            distortion_correction_mode=mode,
            distortion_correction_mode_name=mode_name,
            geometry_ready=geometry_ready,
            geometry_unavailable_reason=geometry_reason,
            sensor_to_image_crop_scale=(
                capture["width"] / (crop[2] - crop[0]),
                capture["height"] / (crop[3] - crop[1]),
            ),
            depth_bytes=None,
            depth_unavailable_reason=unavailable_reason,
            pose=None,
            pose_unavailable_reason=unavailable_reason,
            world_id=None,
            segment_id=None,
        ))
    return tuple(frames)
