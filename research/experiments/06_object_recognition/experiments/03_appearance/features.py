"""Pooled features from the sole authorised acquired detection checkpoint."""

import importlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np

from experiments.datasets.acquisition import sha256

from .adapter import CropEvidence

detector_api = importlib.import_module(
    "experiments.06_object_recognition.pilot.detector"
)


class FeatureExtractor:
    """Public GPU adapter for later detector-box trials, with real runtime receipts."""

    def __init__(self, checkpoint: Path) -> None:
        import torch

        if (
            importlib.metadata.version("ultralytics") != "8.4.172"
            or torch.__version__ != "2.11.0+cu128"
        ):
            raise ValueError("Pinned learned-feature runtime mismatch")
        if not torch.cuda.is_available():
            raise ValueError("Authorised CUDA0 feature trial requires an available GPU")
        started = time.perf_counter()
        self.checkpoint = checkpoint
        self.detector = detector_api.YoloDetector(checkpoint, "0")
        layers = self.detector.model.model.model
        self.layer_index = len(layers) - 2
        self.layer_type = type(layers[self.layer_index]).__name__
        self.load_seconds = time.perf_counter() - started
        self.calls = 0
        self.rows: list[dict] = []
        self.metadata: dict = {}

    def extract(self, crop: CropEvidence) -> list[float]:
        import torch

        if crop.rgb.shape != (128, 128, 3) or crop.mask.shape != (128, 128):
            raise ValueError("Embedding requires the declared 128-grid crop")
        if not np.any(crop.mask):
            return []
        # ndarray Ultralytics sources are BGR; predictor performs its RGB conversion.
        bgr = np.ascontiguousarray(crop.rgb[:, :, ::-1])
        torch.cuda.synchronize(0)
        started = time.perf_counter()
        result = self.detector.model.embed(
            bgr, device="0", embed=[self.layer_index], **detector_api.PREDICT_SETTINGS
        )
        torch.cuda.synchronize(0)
        elapsed = time.perf_counter() - started
        if len(result) != 1 or result[0].ndim != 1:
            raise ValueError("Single crop must yield one pooled vector")
        predictor = self.detector.model.predictor
        if str(predictor.model.device) != "cuda:0" or bool(predictor.model.fp16):
            raise ValueError("Feature inference must execute on CUDA0 FP32")
        if str(result[0].device) != "cuda:0" or result[0].dtype != torch.float32:
            raise ValueError("Feature tensor must be CUDA0 FP32")
        transfer_started = time.perf_counter()
        vector = result[0].detach().cpu().numpy().astype(float)
        transfer_seconds = time.perf_counter() - transfer_started
        if (
            vector.size == 0
            or not np.isfinite(vector).all()
            or np.linalg.norm(vector) == 0
        ):
            raise ValueError("Learned feature is empty, nonfinite or zero")
        self.rows.append(
            {
                "call": self.calls,
                "inference_seconds": elapsed,
                "transfer_seconds": transfer_seconds,
                "first_call_includes_full_model_warmup": self.calls == 0,
            }
        )
        self.calls += 1
        self.metadata = {
            "actual_device": str(predictor.model.device),
            "actual_fp16": bool(predictor.model.fp16),
            "tensor_dtype": str(result[0].dtype),
            "layer_index": self.layer_index,
            "layer_type": self.layer_type,
            "vector_length": int(vector.size),
            "effective_arguments": json.loads(
                json.dumps(vars(predictor.args), default=str)
            ),
            "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
            "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
        }
        return vector.tolist()

    def receipt(self) -> dict:
        if sha256(self.checkpoint) != detector_api.CHECKPOINT_SHA256:
            raise ValueError("Checkpoint changed during extraction")
        return {
            "checkpoint_sha256": detector_api.CHECKPOINT_SHA256,
            "model_load_seconds": self.load_seconds,
            "requested_embedding_count": self.calls,
            "first_call_cost_includes_extra_full_model_warmup": True,
            "costs": self.rows,
            **self.metadata,
        }
