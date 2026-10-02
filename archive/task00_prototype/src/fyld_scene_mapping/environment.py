"""Headless host and dependency snapshot, with optional actual CUDA kernel probe."""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import psutil


def snapshot(probe_cuda: bool = False) -> dict:
    """Record observed facts; driver CUDA version is not the installed toolkit."""
    packages: dict[str, str | None] = {}
    for name in [
        "numpy",
        "scipy",
        "Pillow",
        "open3d",
        "matplotlib",
        "psutil",
        "pytest",
        "torch",
    ]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "cpu_environment": os.environ.get("PROCESSOR_IDENTIFIER"),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_logical_cores": psutil.cpu_count(),
        "ram_bytes": psutil.virtual_memory().total,
        "packages": packages,
    }
    try:
        result["nvidia_smi"] = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        result["nvidia_smi_error"] = str(error)
    if probe_cuda and packages["torch"]:
        import torch

        cuda = {
            "build": torch.version.cuda,
            "available": torch.cuda.is_available(),
            "compiled_architectures": torch.cuda.get_arch_list(),
        }
        if torch.cuda.is_available():
            try:
                cuda["capability"] = list(torch.cuda.get_device_capability())
                a = torch.ones((32, 32), device="cuda")
                cuda["kernel_result"] = float((a @ a)[0, 0].item())
                torch.cuda.synchronize()
                cuda["kernel_test"] = "passed"
            except RuntimeError as error:
                cuda["kernel_test"] = str(error)
        result["torch_cuda"] = cuda
    return result


def main() -> None:
    """Save an inspectable snapshot; no installation or toolkit changes."""
    probe_cuda = True
    output = (
        Path(__file__).resolve().parents[2] / "environments" / "tested_environment.json"
    )
    result = snapshot(probe_cuda)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
