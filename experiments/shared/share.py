"""Export a verified inspection as one portable offline HTML file."""

# hyperparams n/a: visual export only; source display geometry remains unchanged.
import argparse
import base64
import html
import io
import json
import logging
import os
import re
from pathlib import Path, PurePosixPath
from uuid import uuid4

from PIL import Image

from experiments.datasets.acquisition import sha256

from .runs import verify_run
from .visualization import render_viewer

SCENE_FIELDS = (
    "title",
    "note",
    "units",
    "full_count",
    "display_count",
    "display_cap",
    "frustum_length_m",
    "reference_points",
)
FRAME_FIELDS = (
    "id",
    "order",
    "segment",
    "camera",
    "reference_camera",
    "points",
    "colours",
    "display_count",
    "full_count",
    "status",
    "caption",
)


def _preview(source: Path, relative: str, files: dict, max_edge: int) -> str:
    if (
        not isinstance(relative, str)
        or "\\" in relative
        or ":" in relative
        or PurePosixPath(relative).is_absolute()
        or ".." in PurePosixPath(relative).parts
        or relative not in files
    ):
        raise ValueError("Preview must reference a manifest-listed relative image")
    image_path = (source / relative).resolve()
    if not image_path.is_relative_to(source):
        raise ValueError("Preview path escapes source run")
    with Image.open(image_path) as original:
        image = original.convert("RGB")
        image.thumbnail((max_edge, max_edge), Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(
        "ascii"
    )


def _caption(source: Path, image: dict, files: dict) -> str:
    """Keep numerical colour scales readable without sidecar dependencies."""
    relative = PurePosixPath(image["path"])
    legend_path = (relative.parent / "legends.json").as_posix()
    caption = image["caption"]
    legend = None
    if legend_path in files:
        legends = json.loads((source / legend_path).read_text(encoding="utf-8"))
        legend = legends.get(relative.name)
    if legend is None:
        if "see per-frame legend" in caption:
            raise ValueError("Preview requires its manifest-listed colour legend")
        return caption
    low, high = legend["minimum"], legend["maximum"]
    scale = (
        "no finite values"
        if low is None or high is None
        else f"{low:.6g} to {high:.6g} {legend['units']}"
    )
    return caption.replace("; see per-frame legend", "") + (
        f". Per-frame scale: {scale}. {legend['encoding']}."
    )


def _embedded_scene(source: Path, scene: dict, files: dict, max_edge: int) -> dict:
    previews: dict[str, str] = {}
    frames = []
    for frame in scene["frames"]:
        images = []
        for image in frame.get("images", []):
            relative = image["path"]
            if relative not in previews:
                previews[relative] = _preview(source, relative, files, max_edge)
            images.append(
                {
                    "path": previews[relative],
                    "raw": previews[relative],
                    "raw_label": "Reduced display preview",
                    "caption": _caption(source, image, files),
                }
            )
        frames.append(
            {**{k: frame[k] for k in FRAME_FIELDS if k in frame}, "images": images}
        )
    return {**{k: scene[k] for k in SCENE_FIELDS if k in scene}, "frames": frames}


def _share_page(scene: dict, run_id: str, manifest_hash: str, max_edge: int) -> str:
    notice = (
        '<p id="share-notice">Shareable display edition. All images and scene data '
        f"are included in this file. Image previews have a maximum edge of {max_edge} "
        "pixels, with nearest-neighbour resizing and no upscaling. Original raw "
        "measurements and repository metadata are not included. Geometry uses the "
        "original inspection sampling; this export performs no inference or scoring."
        f"</p><p>Source run: {html.escape(run_id)}. Manifest SHA256: "
        f"{html.escape(manifest_hash)}.</p>"
    )
    page, count = re.subn(
        r'<p><a href="review\.html">.*?</p>',
        lambda _: notice,
        render_viewer(scene),
        count=1,
    )
    if count != 1:
        raise ValueError("Viewer navigation changed; standalone export needs updating")
    return page


def export_share(source: Path, output: Path, max_edge: int = 320) -> Path:
    """Publish one self-contained display file without modifying its source run."""
    if isinstance(max_edge, bool) or not isinstance(max_edge, int) or max_edge < 1:
        raise ValueError("Preview edge must be a positive integer")
    source, output = source.resolve(), output.resolve()
    if output.is_relative_to(source) or output.suffix.lower() != ".html":
        raise ValueError("Shared output must be an HTML file outside the source run")
    verify_run(source)
    manifest_path = source / "metadata/manifest.json"
    manifest_hash = sha256(manifest_path)
    files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    if "debug/scene.json" not in files:
        raise ValueError("Source run has no verified inspection scene")
    scene = json.loads((source / "debug/scene.json").read_text(encoding="utf-8"))
    embedded = _embedded_scene(source, scene, files, max_edge)
    page = _share_page(embedded, source.name, manifest_hash, max_edge)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + "." + uuid4().hex + ".part")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(page)
            stream.flush()
            os.fsync(stream.fileno())
        verify_run(source)
        if sha256(manifest_path) != manifest_hash:
            raise ValueError("Source manifest changed during export")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-edge", type=int, default=320)
    args = parser.parse_args()
    output = export_share(args.source, args.output, args.max_edge)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info(
        "Shareable viewer: %s (%s bytes)", output, output.stat().st_size
    )


if __name__ == "__main__":
    main()
