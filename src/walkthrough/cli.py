"""Recorded input entrypoint; software fixtures stay outside the command line."""

import argparse
import importlib
import json
from functools import partial
from pathlib import Path

from .config import STEP_NAMES, PipelineSpec
from .pipeline import run
from .steps.capture import PhoneExport, TumSequence
from .steps.depth import (
    DepthAnythingV2Metric,
    DepthMethod,
    RecordedSensorDepth,
    ScaledZipDepth,
)
from .steps.depth_scale import (
    AnchoredScale,
    OverlapChainScale,
    PoseTriangulatedScale,
    ReferenceFrameScale,
    ReferenceGlobalScale,
    ScaleCorrected,
    ScaleSource,
)
from .steps.mapping import GridFootprint, MappingMethod
from .steps.objects import (
    ClassicalAppearance,
    ClassicalSegmentation,
    ObjectSettings,
    Yolo26x,
)
from .steps.video_depth import MetricVideoDepthAnything
from .validation import ScoreRequest

pose_evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
# Local weights each depth choice uses when --depth-checkpoint is not given.
DEFAULT_DEPTH_CHECKPOINTS = {
    "depth-anything": Path("data/models/depth_anything_v2_metric_indoor_small"),
    "zipdepth-scaled": Path("data/models/ZipDepth/checkpoints/zipdepth_base_npu.pth"),
    "video-depth-anything": Path("data/models/Video-Depth-Anything/checkpoints/metric_video_depth_anything_vits.pth"),
}
SCALED_DEPTH_SOURCES = (
    "overlap-chain", "pose-triangulated", "overlap-chain-pose-anchor", "reference-frame", "reference-global"
)
REFERENCE_SCALES = ("pose-triangulated", "overlap-chain-pose-anchor", "reference-frame", "reference-global")
SCALED_DEPTH_BASES = ("depth-anything", "video-depth-anything")


def depth_choice(args: argparse.Namespace) -> DepthMethod | None:
    """The depth method named on the command line; None leaves the layer unavailable.

    `recorded` reads the dataset's own sensor depth, and `zipdepth-scaled` scales ZipDepth
    from a few of those recorded pixels per frame; both are labelled reference controls, so
    their runs never count as a measurement of a depth method.
    """
    checkpoint = args.depth_checkpoint or DEFAULT_DEPTH_CHECKPOINTS.get(args.depth)
    if args.depth in SCALED_DEPTH_BASES:
        if args.depth == "depth-anything":
            base: DepthMethod = DepthAnythingV2Metric(checkpoint, device=args.device)
        else:
            base = MetricVideoDepthAnything(checkpoint, device=args.device)
        scale = scale_choice(args)
        return base if scale is None else ScaleCorrected(base, scale)
    if args.depth == "zipdepth-scaled":
        return ScaledZipDepth(
            checkpoint, args.dataset, points_per_frame=args.points_per_frame, device=args.device
        )
    if args.depth == "recorded":
        return RecordedSensorDepth(args.dataset)
    return None


def scale_choice(args: argparse.Namespace) -> ScaleSource | None:
    """The per-frame scale correction named by --depth-scale, applied on top of the base depth.

    `overlap-chain` uses colour frames and the base depth only. The others read the dataset's
    sensor depth or motion-capture poses, so they are labelled reference controls.
    """
    chosen = getattr(args, "depth_scale", None)  # absent in argument sets built before this flag
    # Optional settings; None keeps each source's own default.
    smoothing = getattr(args, "chain_smoothing_frames", None)
    noise = getattr(args, "pose_noise_m", None)
    chain = OverlapChainScale() if smoothing is None else OverlapChainScale(smoothing_frames=smoothing)
    if chosen == "overlap-chain":
        return chain
    if chosen in ("pose-triangulated", "overlap-chain-pose-anchor"):
        groundtruth = args.dataset / "groundtruth.txt"
        triangulated = PoseTriangulatedScale(groundtruth) if noise is None else PoseTriangulatedScale(groundtruth, noise_m=noise)
        return triangulated if chosen == "pose-triangulated" else AnchoredScale(chain, triangulated)
    if chosen == "reference-frame":
        return ReferenceFrameScale(args.dataset)
    if chosen == "reference-global":
        return ReferenceGlobalScale(args.dataset)
    return None


def mapping_choice(args: argparse.Namespace) -> MappingMethod | None:
    """The mapping method named on the command line; None leaves the layer unavailable."""
    return GridFootprint() if args.mapping == "grid-footprint" else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Six walkthrough layers; missing methods stay unavailable")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--report", type=Path)
    source.add_argument("--dataset", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--steps", nargs="+", choices=STEP_NAMES)
    # Object detector weights; --checkpoint is the original spelling and still works.
    parser.add_argument("--detector-checkpoint", "--checkpoint", dest="checkpoint", type=Path)
    parser.add_argument("--max-distance-m", type=float)
    parser.add_argument("--ambiguity-margin-m", type=float)
    parser.add_argument("--segmentation", choices=("rectangle", "grabcut", "canny"))
    parser.add_argument("--appearance", action="store_true")
    parser.add_argument("--depth", choices=("depth-anything", "video-depth-anything", "zipdepth-scaled", "recorded"))
    parser.add_argument("--depth-checkpoint", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--points-per-frame", type=int, default=50)
    parser.add_argument("--depth-scale", choices=SCALED_DEPTH_SOURCES)
    parser.add_argument("--pose-noise-m", type=float, help="pose-triangulated: translation noise per frame (default 0.005)")
    parser.add_argument("--chain-smoothing-frames", type=int, help="overlap-chain: causal median window (default 1, none)")
    parser.add_argument("--detector-device", choices=("cpu", "0"), default="cpu")
    parser.add_argument("--mapping", choices=("grid-footprint",))
    parser.add_argument("--report-pages", action="store_true", help="Build the interactive report pages after the run")
    args = parser.parse_args(argv)
    if (args.report is None) != (args.bundle is None):
        parser.error("Phone input requires both --report and --bundle")
    if args.depth in ("recorded", "zipdepth-scaled") and args.dataset is None:
        parser.error(f"--depth {args.depth} needs --dataset, because it reads that dataset's sensor depth")
    if args.depth_scale is not None and args.depth not in SCALED_DEPTH_BASES:
        parser.error(f"--depth-scale applies only to --depth {' or '.join(SCALED_DEPTH_BASES)}")
    if args.pose_noise_m is not None and args.depth_scale not in ("pose-triangulated", "overlap-chain-pose-anchor"):
        parser.error("--pose-noise-m applies only to --depth-scale pose-triangulated or overlap-chain-pose-anchor")
    if args.chain_smoothing_frames is not None and args.depth_scale not in ("overlap-chain", "overlap-chain-pose-anchor"):
        parser.error("--chain-smoothing-frames applies only to --depth-scale overlap-chain or overlap-chain-pose-anchor")
    if args.depth_scale in REFERENCE_SCALES and args.dataset is None:
        parser.error(f"--depth-scale {args.depth_scale} needs --dataset, because it reads that dataset's references")
    spec = PipelineSpec(
        args.run_root,
        Path(__file__).resolve().parents[2],
        (TumSequence(args.dataset) if args.dataset is not None else PhoneExport(args.report, args.bundle)),
        depth=depth_choice(args),
        mapping=mapping_choice(args),
        partial=args.partial,
        requested=tuple(args.steps) if args.steps else STEP_NAMES,
        objects=ObjectSettings(
            detector=Yolo26x(args.checkpoint, device=args.detector_device) if args.checkpoint is not None else None,
            max_distance_m=args.max_distance_m,
            ambiguity_margin_m=args.ambiguity_margin_m,
            segmentation=ClassicalSegmentation(args.segmentation) if args.segmentation else None,
            appearance=ClassicalAppearance() if args.appearance else None,
        ),
    )
    result = run(spec, scores=score_requests(args.dataset))
    summary = {"path": str(result.path), **result.to_dict()}
    if args.report_pages:
        run_pages = importlib.import_module("tools.demos.run_pages")
        summary["report"] = str(run_pages.write_report(result.path)[0].parent)
    print(json.dumps(summary, indent=2))
    return 0 if result.complete else 2


def score_requests(dataset: Path | None) -> tuple[ScoreRequest, ...]:
    """Scores against the recording's own answers: the measured camera path, and the
    sensor depth when the recording has it. Both are read only after predictions are sealed."""
    if dataset is None:
        return ()
    poses = dataset / "groundtruth.txt"
    requests = [ScoreRequest("tracking", partial(pose_evaluation.read_references, poses), reference_file=poses)]
    if (dataset / "depth.txt").is_file():
        requests.append(
            ScoreRequest(
                "depth",
                RecordedSensorDepth(dataset).load,
                reference_file=dataset / "depth.txt",
            )
        )
    return tuple(requests)


if __name__ == "__main__":
    raise SystemExit(main())
