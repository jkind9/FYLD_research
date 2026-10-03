"""Immutable CPU-only visual editions of complete numerical runs."""

# hyperparams n/a: visual publication only; no inference or scoring.
import argparse
import importlib
import json
import logging
import re
import shutil
from pathlib import Path

from experiments.datasets.acquisition import sha256

from .inspection import computation_metadata, tracking_view
from .runs import Run, verify_run, write_json


def copy_inventory(source: Path, destination: Path, manifest: dict) -> None:
    for relative, receipt in manifest["files"].items():
        original = source / relative
        target = destination / (
            "metadata/computation/" + relative.removeprefix("metadata/")
            if relative.startswith("metadata/")
            else relative
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        if sha256(target) != receipt["sha256"] or sha256(original) != receipt["sha256"]:
            raise ValueError(f"Source changed from initial inventory: {relative}")


def publish(source: Path, runs: Path, repo: Path, stage: str) -> Path:
    if stage not in {"03", "04"}:
        raise ValueError("Inspection stage must be 03 or 04")
    verify_run(source)
    manifest = json.loads((source / "metadata/manifest.json").read_text())
    with Run(
        runs,
        repo,
        {
            "publication_only": True,
            "source_run": str(source.resolve()),
            "stage": stage,
            "device": "CPU",
            "numerical_rerun": False,
        },
    ) as run, run.measure("visual_publication"):
        copy_inventory(source, run.path, manifest)
        write_json(run.path / "metadata/computation/manifest.json", manifest)
        numerical_timing = (
            (computation_metadata(run.path) / "timing.json")
            .relative_to(run.path)
            .as_posix()
        )
        write_json(
            run.path / "metadata/publication.json",
            {
                "source_run": str(source.resolve()),
                "source_manifest_sha256": sha256(source / "metadata/manifest.json"),
                "timing_scope": "visual publication only; original numerical timing is archived separately",
                "numerical_timing_path": numerical_timing,
                "processing_fps": None,
                "numerical_rerun": False,
            },
        )
        if stage == "03":
            tracking_view(run.path)
        else:
            module = importlib.import_module(
                "experiments.04_surface_reconstruction.src.review"
            )
            metrics = json.loads((run.path / "output/metrics.json").read_text())
            frames = json.loads((run.path / "output/surface.json").read_text())[
                "shards"
            ]
            module.build_review(run.path, metrics, frames)
        page = (run.path / "review.html").read_text(encoding="utf-8")
        page = re.sub(
            r'<p><a href="viewer.html">Open labelled interactive 3D inspection</a>.*?</p>',
            "",
            page,
        )
        page = re.sub(
            r'<p><a href="[^"]+">Original computation timing and throughput</a>.*?</p>',
            "",
            page,
        )
        page = page.replace(
            "Supplied depth; estimated poses.",
            "Observed input: measured Kinect depth. Predicted output: estimated camera poses.",
        )
        page = page.replace(
            "<th>RGB</th><th>Depth</th>",
            "<th>Observed input RGB</th><th>Observed input depth</th>",
        )
        if stage == "03" and (run.path / "debug/scene.json").exists():
            for frame in json.loads((run.path / "debug/scene.json").read_text())[
                "frames"
            ]:
                page = page.replace(
                    f"debug/{frame['id']}_depth.png",
                    f"debug/{frame['id']}_depth_metres.png",
                )
            page = page.replace(
                "Depth thumbnails show",
                "Observed input depth: blue near, yellow far, black missing. No smoothing or hole filling. Scale:",
            )
            page = re.sub(
                r"metadata/(?:computation/)*timing\.json", numerical_timing, page
            )

        link = '<p><a href="viewer.html">Open labelled interactive 3D inspection</a> · <a href="metadata/artifact_roles.json">Artifact roles</a></p>'
        link += f'<p><a href="{numerical_timing}">Original computation timing and throughput</a> · <a href="metadata/timing.json">Visual publication timing</a></p>'
        (run.path / "review.html").write_text(
            page.replace("</html>", link + "</html>"), encoding="utf-8"
        )
        verify_run(source)
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--stage", choices=["03", "04"], required=True)
    parser.add_argument("--runs", type=Path, required=True)
    args = parser.parse_args()
    path = publish(
        args.source, args.runs, Path(__file__).resolve().parents[2], args.stage
    )
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("Inspection: %s", path / "viewer.html")


if __name__ == "__main__":
    main()
