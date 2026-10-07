"""Create method-labelled, display-only views from saved walkthrough outputs."""

import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

from experiments.shared.runs import write_json
from experiments.shared.visualization import depth_preview, sample_points

from .records import StepResult
from .steps.artifacts import (
    CaptureOutput,
    DepthOutput,
    MappingOutput,
    ObjectsOutput,
    SurfaceOutput,
    TrackingOutput,
)

STAGE_ORDER = ("capture", "depth", "tracking", "surface", "mapping", "objects")
DISPLAY_POINT_CAP = 20_000


def _visual_root(run_path: Path) -> Path:
    return run_path / "output/visualizations"


def _method_text(methods: dict[str, str]) -> str:
    return "; ".join(f"{name}: {method}" for name, method in methods.items())


def _wrap_text(text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _label_png(
    path: Path,
    stage: str,
    methods: dict[str, str],
    note: str | None = None,
) -> None:
    method_text = _method_text(methods)
    with Image.open(path) as source:
        image = source.convert("RGB")
    font = ImageFont.load_default()
    footer_text = f"Method: {method_text}"
    if note:
        footer_text = f"{note}  |  {footer_text}"
    lines = _wrap_text(footer_text, font, image.width - 16)
    line_height = 16
    labelled = Image.new("RGB", (image.width, image.height + line_height * len(lines)))
    labelled.paste(image, (0, 0))
    draw = ImageDraw.Draw(labelled)
    draw.rectangle(
        (0, image.height, image.width, labelled.height), fill=(24, 34, 45)
    )
    for index, line in enumerate(lines):
        draw.text(
            (8, image.height + index * line_height + 2),
            line,
            fill=(245, 247, 250),
            font=font,
        )
    png_info = PngInfo()
    png_info.add_text("stage", stage)
    png_info.add_text("producer_methods", json.dumps(methods, sort_keys=True))
    labelled.save(path, pnginfo=png_info)


def _artifact(
    path: str,
    kind: str,
    label: str,
    source: str,
    producer_method: str,
    display_method: str | None = None,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "path": path,
        "kind": kind,
        "label": label,
        "source": source,
        "producer_method": producer_method,
        "display_method": display_method,
        "details": details,
    }


def _artifact_markup(run_path: Path, artifact: dict[str, Any]) -> str:
    relative_path = Path(artifact["path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Visual artifact paths must stay inside the run folder")
    saved_path = (run_path / relative_path).resolve()
    if not saved_path.is_relative_to(run_path.resolve()):
        raise ValueError("Visual artifact paths must stay inside the run folder")
    link = html.escape(
        quote(Path("..", "..", relative_path).as_posix(), safe="/"), quote=True
    )
    label = html.escape(artifact["label"])
    source = html.escape(artifact["source"])
    producer = html.escape(artifact["producer_method"])
    display = artifact["display_method"]
    display_text = ""
    if display:
        display_text = f"<br>Display method: {html.escape(display)}"
    if artifact["kind"] == "image":
        details = ""
        if artifact["details"] is not None:
            payload = html.escape(
                json.dumps(artifact["details"], indent=2, sort_keys=True)
            )
            details = f"<details><summary>Image details</summary><pre>{payload}</pre></details>"
        return (
            f'<figure><a href="{link}"><img loading="lazy" src="{link}" '
            f'alt="{label}"></a><figcaption>{label}<br>Source: {source}'
            f"<br>Producer method: {producer}{display_text}</figcaption>{details}</figure>"
        )
    if artifact["kind"] == "data":
        details = html.escape(json.dumps(artifact["details"], indent=2, sort_keys=True))
        return (
            f"<details><summary>{label} · {source}</summary><pre>{details}</pre>"
            f"<p>Producer method: {producer}{display_text}</p></details>"
        )
    details = ""
    if artifact["details"] is not None:
        payload = html.escape(
            json.dumps(artifact["details"], indent=2, sort_keys=True)
        )
        details = f"<details><summary>Export details</summary><pre>{payload}</pre></details>"
    return (
        f'<p><a href="{link}">{label}</a> · source: {source} · '
        f"producer method: {producer}{display_text}</p>{details}"
    )


def _stage_markup(run_path: Path, stage: dict[str, Any]) -> str:
    methods = html.escape(_method_text(stage["methods"]) or "No method ran")
    content = "".join(
        _artifact_markup(run_path, artifact) for artifact in stage["artifacts"]
    )
    reason = html.escape(stage["reason"])
    return (
        f'<section><h2>{html.escape(stage["stage"].title())}</h2>'
        f'<p class="status">{html.escape(stage["status"])}: {reason}</p>'
        f"<p>Methods: {methods}</p><div class=assets>{content}</div></section>"
    )


def _write_index(run_path: Path, stages: list[dict[str, Any]]) -> None:
    visual_root = _visual_root(run_path)
    stages_by_name = {stage["stage"]: stage for stage in stages}
    sections = [
        _stage_markup(run_path, stages_by_name[name])
        for name in STAGE_ORDER
        if name in stages_by_name
    ]
    page = """<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Walkthrough stage visuals</title>
<style>
body{font:16px system-ui;max-width:1200px;margin:28px auto;padding:0 18px;color:#17242c}
section{border-top:1px solid #9aa8b2;padding:16px 0}.status{font-weight:700}
.assets{display:flex;flex-wrap:wrap;gap:16px}figure{margin:0;max-width:640px}
img{display:block;max-width:100%;height:auto}figcaption,details{font-size:14px}
pre{white-space:pre-wrap;background:#f1f4f6;padding:12px}
</style>
<h1>Walkthrough stage visuals</h1>
<p>Images and point displays are for inspection. They do not change the saved numeric
predictions or scores. Each item names its producing method and source.</p>
__STAGES__
</html>"""
    page = page.replace("__STAGES__", "\n".join(sections))
    (visual_root / "index.html").write_text(page, encoding="utf-8")


def _publish_stage(
    run_path: Path,
    status: StepResult,
    methods: dict[str, str],
    artifacts: list[dict[str, Any]],
) -> None:
    visual_root = _visual_root(run_path)
    manifest_path = visual_root / "manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"stages": []}
    stages_by_name = {stage["stage"]: stage for stage in existing["stages"]}
    stages_by_name[status.name] = {
        "stage": status.name,
        "status": status.status,
        "reason": status.reason,
        "methods": methods,
        "artifacts": artifacts,
    }
    stages = [stages_by_name[name] for name in STAGE_ORDER if name in stages_by_name]
    write_json(manifest_path, {"stages": stages})
    _write_index(run_path, stages)


def capture(
    run_path: Path, status: StepResult, output: CaptureOutput | None
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if output is not None and status.status == "complete":
        for frame in output["frames"]:
            artifacts.append(
                _artifact(
                    frame["image"],
                    "image",
                    f"Recorded RGB frame {frame['source_frame_id']}",
                    frame["source_frame_id"],
                    methods["input"],
                )
            )
    _publish_stage(run_path, status, methods, artifacts)


def depth(
    run_path: Path,
    status: StepResult,
    capture_output: CaptureOutput | None,
    output: DepthOutput | None,
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if output is not None and capture_output is not None and status.status == "complete":
        capture_by_id = {
            frame["frame_id"]: frame for frame in capture_output["frames"]
        }
        for index, frame in enumerate(output["frames"]):
            artifacts.extend(
                _depth_frame(
                    run_path,
                    index,
                    frame,
                    methods,
                    capture_by_id,
                    capture_output["methods"],
                )
            )
    _publish_stage(run_path, status, methods, artifacts)


def _depth_frame(
    run_path: Path,
    index: int,
    frame: dict[str, Any],
    methods: dict[str, str],
    capture_by_id: dict[str, dict[str, Any]],
    capture_methods: dict[str, str],
) -> list[dict[str, Any]]:
    arrays_path = run_path / frame["arrays"]
    with np.load(arrays_path, allow_pickle=False) as arrays:
        depth_values = arrays["depth"]
        valid = arrays["valid"]
        display_depth = np.where(valid, depth_values, np.nan)
    maximum = float(np.max(depth_values[valid])) if valid.any() else 1.0
    preview_path = _visual_root(run_path) / "depth" / f"frame_{index:06d}.png"
    legend = depth_preview(
        display_depth,
        preview_path,
        "predicted_output",
        frame["arrays"],
        maximum=max(maximum, np.finfo(float).eps),
    )
    legend["producer_method"] = methods["depth"]
    legend["display_method"] = "experiments.shared.visualization.depth_preview"
    legend["source_frame_id"] = frame["frame_id"]
    write_json(preview_path.with_suffix(".json"), legend)
    _label_png(preview_path, "depth", methods)
    mask_path = preview_path.with_name(preview_path.stem + "_valid.png")
    source_frame = capture_by_id[frame["frame_id"]]
    valid_count = int(valid.sum())
    total_count = int(valid.size)
    valid_fraction = valid_count / total_count
    valid_label = (
        f"Valid depth pixels: {valid_fraction:.1%} "
        f"({valid_count}/{total_count})"
    )
    coverage_label = f"Coverage overlay: green is valid, red is invalid - {valid_label}"
    _label_png(mask_path, "depth_validity", methods, valid_label)
    coverage_path = preview_path.with_name(preview_path.stem + "_coverage.png")
    _draw_depth_coverage(run_path / source_frame["image"], valid, coverage_path)
    _label_png(coverage_path, "depth_coverage", methods, coverage_label)
    return [
        _artifact(
            preview_path.relative_to(run_path).as_posix(),
            "image",
            f"Predicted depth · {frame['frame_id']}",
            frame["arrays"],
            methods["depth"],
            "experiments.shared.visualization.depth_preview",
            {"units": "metres", "minimum_m": 0, "display_maximum_m": maximum},
        ),
        _artifact(
            mask_path.relative_to(run_path).as_posix(),
            "image",
            f"Valid depth pixels · {frame['frame_id']}",
            frame["arrays"],
            methods["depth"],
            "experiments.shared.visualization.depth_preview",
            {"valid_pixels": valid_count, "total_pixels": total_count},
        ),
        _artifact(
            coverage_path.relative_to(run_path).as_posix(),
            "image",
            f"Depth coverage over RGB - {frame['frame_id']}",
            source_frame["image"],
            methods["depth"],
            "Green means valid depth; red means invalid depth",
            {
                "valid_pixels": valid_count,
                "total_pixels": total_count,
                "valid_fraction": valid_fraction,
            },
        ),
        _artifact(
            source_frame["image"],
            "image",
            f"RGB source for depth · {frame['frame_id']}",
            source_frame["source_frame_id"],
            capture_methods["input"],
        ),
    ]


def _draw_depth_coverage(source_path: Path, valid: np.ndarray, destination: Path) -> None:
    with Image.open(source_path) as source:
        rgb = np.asarray(source.convert("RGB"), dtype=np.float32)
    if valid.shape != rgb.shape[:2]:
        raise ValueError("Depth validity mask must match its RGB source dimensions")
    tint = np.where(valid[..., None], (20, 190, 95), (220, 45, 55))
    coverage = (rgb * 0.68 + tint * 0.32).clip(0, 255).astype(np.uint8)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(coverage).save(destination)


def tracking(
    run_path: Path, status: StepResult, output: TrackingOutput | None
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if output is not None and status.status == "complete":
        preview_path = _visual_root(run_path) / "tracking" / "trajectory.png"
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        _draw_trajectory(preview_path, output)
        _label_png(preview_path, "tracking", methods)
        artifacts.append(
            _artifact(
                preview_path.relative_to(run_path).as_posix(),
                "image",
                "Estimated camera path in world X-Z coordinates",
                "output/predictions/tracking.json",
                methods["tracking"],
                "Pillow world X-Z projection; no gravity alignment",
            )
        )
    _publish_stage(run_path, status, methods, artifacts)


def _draw_trajectory(path: Path, output: TrackingOutput) -> None:
    width, height, margin = 900, 620, 64
    image = Image.new("RGB", (width, height), (250, 251, 252))
    draw = ImageDraw.Draw(image)
    paths: dict[tuple[str, str], list[np.ndarray]] = {}
    for row in output["records"]:
        pose = row["pose"]
        if pose is None:
            continue
        origin = (pose["world_id"], pose["segment_id"])
        position = np.asarray(pose["T_world_camera"], dtype=float)[:3, 3]
        paths.setdefault(origin, []).append(position)
    positions = [position for points in paths.values() for position in points]
    xs = [float(position[0]) for position in positions]
    zs = [float(position[2]) for position in positions]
    draw.text((margin, 18), "Estimated camera path · world X-Z (metres)", fill="#17242c")
    if not positions:
        draw.text((margin, height // 2), "No estimated poses", fill="#17242c")
        image.save(path)
        return
    low_x, high_x = min(xs), max(xs)
    low_z, high_z = min(zs), max(zs)
    span = max(high_x - low_x, high_z - low_z, 1e-6)
    scale = (min(width, height) - 2 * margin) / span
    centre_x, centre_z = (low_x + high_x) / 2, (low_z + high_z) / 2
    for path_points in paths.values():
        pixels = [
            (
                round(width / 2 + (position[0] - centre_x) * scale),
                round(height / 2 - (position[2] - centre_z) * scale),
            )
            for position in path_points
        ]
        if len(pixels) > 1:
            draw.line(pixels, fill="#1466a8", width=3)
        for index, point in enumerate(pixels):
            colour = "#187d5c" if index == 0 else "#bd3b22" if index == len(pixels) - 1 else "#1466a8"
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=colour)
    draw.text((margin, height - 32), "Start: green - latest: red - separate origins are not joined", fill="#17242c")
    image.save(path)


def surface(
    run_path: Path,
    status: StepResult,
    capture_output: CaptureOutput | None,
    depth_output: DepthOutput | None,
    output: SurfaceOutput | None,
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if (
        output is not None
        and capture_output is not None
        and depth_output is not None
        and status.status == "complete"
    ):
        artifacts = _surface_frames(
            run_path, output, capture_output, depth_output, methods
        )
    _publish_stage(run_path, status, methods, artifacts)


def _surface_frames(
    run_path: Path,
    output: SurfaceOutput,
    capture_output: CaptureOutput,
    depth_output: DepthOutput,
    methods: dict[str, str],
) -> list[dict[str, Any]]:
    from experiments.shared.exporting import _cloud_preview

    capture_by_id = {frame["frame_id"]: frame for frame in capture_output["frames"]}
    depth_by_id = {frame["frame_id"]: frame for frame in depth_output["frames"]}
    artifacts = []
    display_by_origin: dict[
        tuple[str, str], tuple[list[list[float]], list[list[float]], list[str]]
    ] = {}
    display_count = max(1, DISPLAY_POINT_CAP // max(1, len(output["shards"])))
    for index, shard in enumerate(output["shards"]):
        image_frame = capture_by_id[shard["frame_id"]]
        depth_frame = depth_by_id[shard["frame_id"]]
        points = np.load(run_path / shard["points"], allow_pickle=False, mmap_mode="r")
        with np.load(run_path / depth_frame["arrays"], allow_pickle=False) as arrays:
            valid = arrays["valid"]
        with Image.open(run_path / image_frame["image"]) as source_image:
            rgb = np.asarray(source_image.convert("RGB"))
        colours = rgb[valid]
        if len(points) != len(colours):
            raise ValueError("Surface points do not match their source RGB pixels")

        frame_root = _visual_root(run_path) / "surface"
        frame_root.mkdir(parents=True, exist_ok=True)
        ply_path = frame_root / f"frame_{index:06d}.ply"
        _write_ply(ply_path, points, colours, methods["surface"], shard["frame_id"])
        sampled = sample_points(points, colours, display_count)
        origin = (shard["world_id"], shard["segment_id"])
        points_for_origin, colours_for_origin, sources = display_by_origin.setdefault(
            origin, ([], [], [])
        )
        points_for_origin.extend(sampled["points"])
        colours_for_origin.extend(sampled["colours"])
        sources.append(shard["points"])
        details = {
            "full_point_count": sampled["full_count"],
            "display_sample_count": sampled["display_count"],
            "units": "metres",
            "world_id": shard["world_id"],
            "segment_id": shard["segment_id"],
        }
        artifacts.extend(
            [
                _artifact(
                    ply_path.relative_to(run_path).as_posix(),
                    "download",
                    f"Full coloured point cloud · {shard['frame_id']}",
                    shard["points"],
                    methods["surface"],
                    "Binary little-endian PLY writer; no point sampling",
                    details,
                ),
            ]
        )
    for index, (origin, display) in enumerate(display_by_origin.items()):
        world_id, segment_id = origin
        display_points, display_colours, sources = display
        preview_path = _visual_root(run_path) / "surface" / f"origin_{index:06d}.png"
        _cloud_preview(
            preview_path,
            np.asarray(display_points, dtype=float).reshape((-1, 3)),
            np.asarray(display_colours, dtype=np.uint8).reshape((-1, 3)),
        )
        _label_png(preview_path, "surface", methods)
        artifacts.append(
            _artifact(
                preview_path.relative_to(run_path).as_posix(),
                "image",
                f"Point cloud preview - world {world_id}, segment {segment_id}",
                ", ".join(sources),
                methods["surface"],
                "experiments.shared.exporting._cloud_preview; evenly spaced display sample",
                {
                    "full_point_count": sum(
                        shard["point_count"]
                        for shard in output["shards"]
                        if (shard["world_id"], shard["segment_id"]) == origin
                    ),
                    "preview_point_count": len(display_points),
                    "preview_sampling": (
                        f"up to {DISPLAY_POINT_CAP} evenly spaced points; display only"
                    ),
                    "world_id": world_id,
                    "segment_id": segment_id,
                    "units": "metres",
                },
            )
        )
    return artifacts


def _write_ply(
    path: Path,
    points: np.ndarray,
    colours: np.ndarray,
    method: str,
    frame_id: str,
) -> None:
    if points.ndim != 2 or points.shape[1] != 3 or colours.shape != points.shape:
        raise ValueError("Coloured PLY needs one RGB colour for each XYZ point")
    if not np.isfinite(points).all():
        raise ValueError("Coloured PLY points must be finite")
    method = method.replace("\n", " ").replace("\r", " ")
    frame_id = frame_id.replace("\n", " ").replace("\r", " ")
    vertices = np.empty(
        len(points),
        dtype=np.dtype(
            [
                ("x", "<f4"),
                ("y", "<f4"),
                ("z", "<f4"),
                ("red", "u1"),
                ("green", "u1"),
                ("blue", "u1"),
            ]
        ),
    )
    vertices["x"], vertices["y"], vertices["z"] = points.T
    vertices["red"], vertices["green"], vertices["blue"] = colours.T
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"comment producer_method {method}\ncomment source_frame {frame_id}\n"
        f"element vertex {len(vertices)}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(header.encode("ascii", errors="replace"))
        vertices.tofile(stream)


def mapping(
    run_path: Path, status: StepResult, output: MappingOutput | None
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if output is not None and status.status == "complete":
        artifacts.append(
            _artifact(
                "output/predictions/mapping.json",
                "data",
                "Mapping measurements (no map geometry is currently supplied)",
                "output/predictions/surface.json",
                methods["mapping"],
                details=output["measurements"],
            )
        )
    _publish_stage(run_path, status, methods, artifacts)


def objects(
    run_path: Path,
    status: StepResult,
    capture_output: CaptureOutput | None,
    output: ObjectsOutput | None,
) -> None:
    methods = {} if output is None else output["methods"]
    artifacts = []
    if output is not None and capture_output is not None and status.status == "complete":
        capture_by_id = {
            frame["frame_id"]: frame for frame in capture_output["frames"]
        }
        for index, observation in enumerate(output["frames"]):
            artifacts.append(
                _object_overlay(
                    run_path,
                    index,
                    observation,
                    capture_by_id[observation["frame_id"]],
                    methods,
                    output["synthetic_detector"],
                )
            )
    _publish_stage(run_path, status, methods, artifacts)


def _object_overlay(
    run_path: Path,
    index: int,
    observation: dict[str, Any],
    capture_frame: dict[str, Any],
    methods: dict[str, str],
    synthetic_detector: bool,
) -> dict[str, Any]:
    with Image.open(run_path / capture_frame["image"]) as source_image:
        image = source_image.convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for proposal in observation["proposals"]:
        _draw_proposal(draw, proposal, font)

    proposal_count = len(observation["proposals"])
    overlay_note = (
        f"SOFTWARE CONTROL - {proposal_count} synthetic box(es)"
        if synthetic_detector
        else f"Detector proposals: {proposal_count}"
    )
    draw.rectangle((0, 0, image.width, 22), fill="#17242c")
    draw.text((8, 6), overlay_note, fill="#ffffff", font=font)

    path = _visual_root(run_path) / "objects" / f"frame_{index:06d}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    _label_png(path, "objects", methods, overlay_note)
    return _artifact(
        path.relative_to(run_path).as_posix(),
        "image",
        f"Object detections and provisional IDs - {observation['frame_id']}",
        capture_frame["image"],
        "; ".join(
            (
                f"detection: {methods['detection']}",
                f"localisation: {methods['localisation']}",
                f"counting: {methods['counting']}",
            )
        ),
        "Pillow bounding-box overlay; no image resizing",
        {
            "frame_id": observation["frame_id"],
            "proposal_count": proposal_count,
            "software_control": synthetic_detector,
            "object_ids": [
                proposal["object_id"] for proposal in observation["proposals"]
            ],
        },
    )


def _draw_proposal(
    draw: ImageDraw.ImageDraw,
    proposal: dict[str, Any],
    font: ImageFont.ImageFont,
) -> None:
    x1, y1, x2, y2 = proposal["xyxy"]
    colour = "#18a56b" if proposal["object_id"] is not None else "#e58a24"
    box = (x1, y1, x2, y2)
    draw.rectangle(box, outline="#ffffff", width=7)
    draw.rectangle(box, outline=colour, width=3)
    identity = proposal["object_id"] or proposal["association"]
    label = f"{proposal['label']} - {identity}"
    label_position = (max(2, x1 + 6), max(24, y1 + 6))
    text_bounds = draw.textbbox(label_position, label, font=font)
    draw.rectangle(text_bounds, fill="#17242c")
    draw.text(label_position, label, fill=colour, font=font)
