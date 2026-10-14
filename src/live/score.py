"""Score a live run's surface against the ICL living-room reference, as experiments/sfm/run_dense.py does.

    python -m src.live.score --run <live run folder> --icl data/icl_nuim
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import open3d as o3d

references = importlib.import_module("experiments.sfm.src.references")
surface_evaluation = importlib.import_module("experiments.04_surface_reconstruction.src.evaluation")
THRESHOLD_M = 0.05  # inherited experiment 04 reporting threshold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--icl", type=Path, required=True, help="the ICL folder holding reference_surface/ and conventions.json")
    args = parser.parse_args(argv)
    points = np.asarray(o3d.io.read_point_cloud(str(args.run / "surface.ply")).points, dtype=np.float64)
    scorer = surface_evaluation.SurfaceScorer(references.icl_reference(args.icl), THRESHOLD_M)
    scorer.observe(points)
    scores = scorer.summary()
    (args.run / "scores.json").write_text(json.dumps({"surface": scores, "reference": "ICL publisher surface model"}, indent=2),
                                          encoding="utf-8")
    print(json.dumps(scores["accuracy"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
