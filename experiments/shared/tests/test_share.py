"""Portable display editions preserve geometry and source evidence."""

import base64
import io
import json
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run, write_json
from experiments.shared.visualization import write_viewer


def seal(root: Path) -> None:
    files = {
        p.relative_to(root).as_posix(): {"sha256": sha256(p), "bytes": p.stat().st_size}
        for p in root.rglob("*")
        if p.is_file() and p.name not in {"manifest.json", "status.json"}
    }
    write_json(root / "metadata/manifest.json", {"schema_version": 1, "files": files})
    write_json(
        root / "metadata/status.json",
        {
            "status": "complete",
            "manifest_sha256": sha256(root / "metadata/manifest.json"),
        },
    )


def make_source(root: Path) -> dict:
    root.mkdir(parents=True)
    Image.new("RGB", (640, 320), (10, 20, 30)).save(root / "colour.png")
    depth = Image.new("RGB", (640, 320), (0, 0, 0))
    depth.paste((0, 100, 255), (320, 0, 640, 320))
    depth.save(root / "depth.png")
    Image.new("RGB", (8, 4), (50, 70, 90)).save(root / "small.png")
    scene = {
        "title": "Surface </script><script>alert(1)</script> café __SCRIPT__ __SCENE__ __TITLE__",
        "note": "Evaluated output, display only",
        "units": "metres",
        "full_count": 100,
        "display_count": 4,
        "roles": [{"path": "private/raw.npy", "sources": ["C:/private/source"]}],
        "reference_points": {
            "points": [[0, 1, 0], [1, 0, 1]],
            "colours": [[100, 0, 0]] * 2,
        },
        "frames": [
            {
                "id": str(i),
                "order": i,
                "segment": "world",
                "camera": None,
                "reference_camera": None,
                "status": "supplied",
                "caption": "Ground truth camera",
                "points": [[i, i / 2, 0], [i, 0, i + 1]],
                "colours": [[0, 0, 255], [0, 255, 0]],
                "images": [
                    {
                        "path": name,
                        "raw": "private/raw.npy",
                        "caption": "Ground truth depth",
                    }
                    for name in ("colour.png", "depth.png", "small.png")
                ],
            }
            for i in range(2)
        ],
    }
    write_viewer(root, scene)
    seal(root)
    return scene


def scene_from(page: str) -> dict:
    return json.loads(
        re.search(
            r'<script id="scene-data" type="application/json">(.*?)</script>',
            page,
            re.DOTALL,
        )[1]
    )


def test_portable_export_preserves_source_and_geometry(tmp_path):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    original = make_source(source)
    before = {p: p.read_bytes() for p in source.rglob("*") if p.is_file()}
    output = tmp_path / "shared.html"
    export_share(source, output)
    page = output.read_text(encoding="utf-8")
    exported = scene_from(page)
    for key in ("title", "units", "full_count", "display_count", "reference_points"):
        assert exported[key] == original[key]
    for frame, expected in zip(exported["frames"], original["frames"], strict=True):
        for key in ("points", "colours", "camera", "caption", "status"):
            assert frame[key] == expected[key]
        for image, size in zip(
            frame["images"], [(320, 160), (320, 160), (8, 4)], strict=True
        ):
            assert image["path"].startswith("data:image/png;base64,")
            assert image["raw"] == image["path"]
            assert image["raw_label"] == "Reduced display preview"
            with Image.open(
                io.BytesIO(base64.b64decode(image["path"].split(",")[1]))
            ) as decoded:
                assert decoded.size == size and decoded.mode == "RGB"
                if size == (320, 160) and image == frame["images"][1]:
                    assert {tuple(p) for p in np.array(decoded).reshape(-1, 3)} == {
                        (0, 0, 0),
                        (0, 100, 255),
                    }
    assert "private/raw.npy" not in page and "C:/private" not in page
    assert "</script><script>alert" not in page
    assert not re.findall(r'(?:href|src)="(?!data:|#)[^"]+"', page)
    assert "Original raw input" not in exported["frames"][0]["images"][0]["raw_label"]
    assert {p: p.read_bytes() for p in before} == before
    assert verify_run(source)["status"] == "complete"


@pytest.mark.parametrize(
    "path",
    [
        "../escape.png",
        "/absolute.png",
        "C:/private/a.png",
        "https://example.com/a.png",
        "missing.png",
        "a\\b.png",
    ],
)
def test_invalid_image_paths_do_not_replace_output(tmp_path, path):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    scene = make_source(source)
    scene["frames"][0]["images"][0]["path"] = path
    write_json(source / "debug/scene.json", scene)
    seal(source)
    output = tmp_path / "shared.html"
    output.write_text("old edition")
    with pytest.raises(ValueError):
        export_share(source, output)
    assert output.read_text() == "old edition"


@pytest.mark.parametrize(
    "damage", ["image", "missing", "extra", "manifest", "incomplete"]
)
def test_damaged_source_is_rejected(tmp_path, damage):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    make_source(source)
    if damage == "image":
        (source / "colour.png").write_bytes(b"damage")
    elif damage == "missing":
        (source / "colour.png").unlink()
    elif damage == "extra":
        (source / "extra").write_text("extra")
    elif damage == "manifest":
        (source / "metadata/manifest.json").write_text("{}")
    else:
        write_json(source / "metadata/status.json", {"status": "running"})
    with pytest.raises((ValueError, FileNotFoundError)):
        export_share(source, tmp_path / "shared.html")
    assert not (tmp_path / "shared.html").exists()


@pytest.mark.parametrize("edge", [0, -1, True, 1.5])
def test_invalid_preview_edge(tmp_path, edge):
    from experiments.shared.share import export_share

    with pytest.raises(ValueError):
        export_share(tmp_path, tmp_path / "shared.html", edge)


@pytest.mark.parametrize("relative", ["new.html", "metadata/status.json"])
def test_export_never_changes_source(tmp_path, relative):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    make_source(source)
    with pytest.raises(ValueError):
        export_share(source, source / relative)
    assert verify_run(source)["status"] == "complete"


@pytest.mark.parametrize("failure", ["replace", "fsync"])
def test_atomic_failure_keeps_previous_edition(tmp_path, monkeypatch, failure):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    make_source(source)
    output = tmp_path / "shared.html"
    output.write_text("previous")

    def fail_replace(*args):
        raise OSError("injected replace failure")

    if failure == "replace":
        monkeypatch.setattr(Path, "replace", fail_replace)
    else:
        monkeypatch.setattr("experiments.shared.share.os.fsync", fail_replace)
    with pytest.raises(OSError, match="injected"):
        export_share(source, output)
    assert output.read_text() == "previous"
    assert not list(tmp_path.glob("*.part"))


def test_conversion_mutation_rejected_before_publication(tmp_path, monkeypatch):
    from experiments.shared import share

    source = tmp_path / "source"
    make_source(source)
    renderer = share.render_viewer

    def mutate(scene):
        page = renderer(scene)
        (source / "colour.png").write_bytes(b"changed during conversion")
        return page

    monkeypatch.setattr(share, "render_viewer", mutate)
    with pytest.raises(ValueError):
        share.export_share(source, tmp_path / "shared.html")
    assert not (tmp_path / "shared.html").exists()


def test_distance_legend_scales_are_embedded(tmp_path):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    scene = make_source(source)
    for index, frame in enumerate(scene["frames"]):
        directory = source / str(index)
        directory.mkdir()
        (directory / "distance.png").write_bytes((source / "depth.png").read_bytes())
        write_json(
            directory / "legends.json",
            {
                "distance.png": {
                    "minimum": 0,
                    "maximum": 0.01 if index == 0 else 1.0,
                    "units": "metres",
                    "encoding": "black invalid; grayscale 1 minimum to 255 maximum",
                }
            },
        )
        frame["images"] = [
            {
                "path": f"{index}/distance.png",
                "raw": "raw.npy",
                "caption": "Evaluated output distance; see per-frame legend",
            }
        ]
    write_json(source / "debug/scene.json", scene)
    seal(source)
    output = export_share(source, tmp_path / "shared.html")
    frames = scene_from(output.read_text(encoding="utf-8"))["frames"]
    assert "0 to 0.01 metres" in frames[0]["images"][0]["caption"]
    assert "0 to 1 metres" in frames[1]["images"][0]["caption"]
    assert "black invalid" in frames[0]["images"][0]["caption"]
    assert "see per-frame legend" not in output.read_text(encoding="utf-8")


def test_missing_required_legend_rejected(tmp_path):
    from experiments.shared.share import export_share

    source = tmp_path / "source"
    scene = make_source(source)
    scene["frames"][0]["images"][0]["caption"] = (
        "Evaluated distance; see per-frame legend"
    )
    write_json(source / "debug/scene.json", scene)
    seal(source)
    with pytest.raises(ValueError, match="colour legend"):
        export_share(source, tmp_path / "shared.html")


def test_cli_overwrites_previous_complete_edition(tmp_path, monkeypatch):
    from experiments.shared.share import main

    source = tmp_path / "source"
    make_source(source)
    output = tmp_path / "shared.html"
    output.write_text("old edition")
    monkeypatch.setattr(
        "sys.argv", ["share", "--source", str(source), "--output", str(output)]
    )
    main()
    assert len(scene_from(output.read_text(encoding="utf-8"))["frames"]) == 2
