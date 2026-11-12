"""One COLMAP run through the official command-line build, with per-stage timing."""

from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .sequences import Sequence

FEATURES = {"sift": ("SIFT", "SIFT_BRUTEFORCE"), "aliked": ("ALIKED_N16ROT", "ALIKED_LIGHTGLUE")}
MAPPERS = {"incremental": ("mapper", "Mapper"), "global": ("global_mapper", "GlobalMapper")}


@dataclass(frozen=True)
class Settings:
    features: str
    overlap: int = 10
    quadratic_overlap: bool = True
    seed: int = 0
    refine_calibration: bool = False

    def __post_init__(self) -> None:
        if self.features not in FEATURES:
            raise ValueError(f"features must be one of {sorted(FEATURES)}")
        if self.overlap < 1:
            raise ValueError("Sequential overlap must be at least 1")

    def to_dict(self) -> dict:
        return asdict(self)


def _run(command: list[str], log: Path) -> float:
    started = time.perf_counter()
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-5:]
        raise RuntimeError(f"{command[1]} exited {result.returncode}: {' | '.join(tail)}")
    return time.perf_counter() - started


def features_and_matches(colmap: Path, sequence: Sequence, settings: Settings, work: Path) -> dict[str, float]:
    """Extract and match into work/database.db; returns seconds per stage."""
    work.mkdir(parents=True, exist_ok=True)
    database = work / "database.db"
    if database.exists():
        raise FileExistsError(f"{database} already exists; a run never reuses a database")
    image_list = work / "image_list.txt"
    image_list.write_text("\n".join(sequence.image_names) + "\n", encoding="utf-8")
    extractor, matcher = FEATURES[settings.features]
    params = ",".join(repr(float(v)) for v in sequence.camera_params)
    seconds = {
        "extract": _run([
            str(colmap), "feature_extractor", "--database_path", str(database), "--image_path", str(sequence.image_root),
            "--image_list_path", str(image_list), "--ImageReader.single_camera", "1",
            "--ImageReader.camera_model", sequence.camera_model, "--ImageReader.camera_params", params,
            "--FeatureExtraction.type", extractor, "--FeatureExtraction.use_gpu", "0",
        ], work / "extract.log"),
    }
    seconds["match"] = _run([
        str(colmap), "sequential_matcher", "--database_path", str(database),
        "--FeatureMatching.type", matcher, "--FeatureMatching.use_gpu", "0",
        "--SequentialMatching.overlap", str(settings.overlap),
        "--SequentialMatching.quadratic_overlap", str(int(settings.quadratic_overlap)),
        "--SequentialMatching.loop_detection", "0",
    ], work / "match.log")
    return seconds


def map_models(colmap: Path, sequence: Sequence, settings: Settings, work: Path, mapper: str) -> float:
    """Run one mapper on the shared database into work/<mapper>/<model>; returns seconds."""
    if mapper not in MAPPERS:
        raise ValueError(f"mapper must be one of {sorted(MAPPERS)}")
    command, section = MAPPERS[mapper]
    output = work / mapper
    output.mkdir(parents=True, exist_ok=False)
    refine = str(int(settings.refine_calibration))
    return _run([
        str(colmap), command, "--database_path", str(work / "database.db"), "--image_path", str(sequence.image_root),
        "--output_path", str(output), f"--{section}.random_seed", str(settings.seed),
        f"--{section}.ba_refine_focal_length", refine, f"--{section}.ba_refine_extra_params", refine,
        f"--{section}.multiple_models", "1",
    ], work / f"map_{mapper}.log")


def read_models(work: Path, mapper: str) -> dict[int, object]:
    """Every saved model of one mapper, keyed by its folder number."""
    import pycolmap

    models = {}
    for folder in sorted((work / mapper).iterdir(), key=lambda p: int(p.name) if p.name.isdigit() else -1):
        if folder.is_dir() and folder.name.isdigit():
            models[int(folder.name)] = pycolmap.Reconstruction(folder)
    return models
