"""Publish an offline smoke APK bundle after rechecking its evidence and bytes."""

import argparse
import base64
import ctypes
import errno
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from recipe import sha256, unique_object, validate_settings
from verify import inspect_archive, parse_badging, parse_signature, verify_apk


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_evidence(apk: Path, evidence: dict) -> None:
    if not isinstance(evidence, dict) or type(evidence.get("schema_version")) is not int:
        raise ValueError("Malformed APK verification receipt")
    if evidence.get("schema_version") != 1 or evidence.get("status") != "verified":
        raise ValueError("Receipt does not contain accepted APK verification")
    if not _digest(evidence.get("apk_sha256")) or sha256(apk) != evidence["apk_sha256"]:
        raise ValueError("APK hash does not match verification receipt")
    settings = validate_settings(evidence.get("settings"))
    if evidence.get("source_sha256") != settings["source_sha256"]:
        raise ValueError("Receipt source hash does not match inherited source")
    for key in ("signature", "manifest", "archive", "bytecode"):
        if not isinstance(evidence.get(key), dict) or not evidence[key]:
            raise ValueError(f"Incomplete APK verification evidence: {key}")
    signature, manifest, code = evidence["signature"], evidence["manifest"], evidence["bytecode"]
    parsed_signature = parse_signature(subprocess.CompletedProcess([], 0, signature.get("stdout"),
                                                                  signature.get("stderr", "")))
    for key in ("certificate_sha256", "schemes"):
        if signature.get(key) != parsed_signature[key]:
            raise ValueError("Signature transcript does not match receipt claims")
    parsed_manifest = parse_badging(subprocess.CompletedProcess([], 0, manifest.get("stdout"),
                                                               manifest.get("stderr", "")), settings)
    if any(manifest.get(key) != value for key, value in parsed_manifest.items()):
        raise ValueError("Manifest transcript does not match receipt claims")
    if evidence["archive"] != inspect_archive(apk, settings["abi"]):
        raise ValueError("APK archive does not match receipt claims")
    for key, expected in (("status", "verified"), ("source_sha256", settings["source_sha256"]),
                          ("python_version", settings["android_python"]), ("optimize", 2)):
        if type(code.get(key)) is not type(expected) or code.get(key) != expected:
            raise ValueError("Incomplete embedded source verification evidence")
    if not isinstance(code.get("filename"), str) or not code["filename"]:
        raise ValueError("Missing verified embedded source filename")
    for tool in (signature, manifest):
        if not _digest(tool.get("tool_sha256")) or not isinstance(tool.get("command"), list):
            raise ValueError("Missing installed verifier provenance")
    if not _digest(code.get("hostpython_sha256")) or not _digest(code.get("main_pyc_sha256")):
        raise ValueError("Missing embedded source verifier provenance")


def _publish(staging: Path, destination: Path) -> None:
    """Atomic rename that never replaces a destination, including an empty directory."""
    if os.name == "nt":
        os.rename(staging, destination)
        return
    if not sys.platform.startswith("linux"):
        raise OSError("Atomic no-replace publication requires Windows or Linux")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise OSError("Linux renameat2 is required for atomic no-replace publication")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    result = rename(-100, os.fsencode(staging), -100, os.fsencode(destination), 1)
    if result:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise FileExistsError(code, os.strerror(code), str(destination))
        if code in (errno.EINVAL, errno.ENOSYS, errno.EOPNOTSUPP) and str(destination).startswith("/mnt/"):
            _publish_windows_mount(staging, destination)
            return
        raise OSError(code, os.strerror(code), str(destination))


def _publish_windows_mount(staging: Path, destination: Path) -> None:
    """Use NTFS directory move on WSL mounts where renameat2(RENAME_NOREPLACE) is unsupported."""
    executable = shutil.which("powershell.exe")
    if executable is None:
        raise OSError("Windows PowerShell is required to publish atomically to a mounted Windows folder")
    source_result = subprocess.run(["wslpath", "-w", str(staging)], check=True,
                                   capture_output=True, text=True, shell=False, timeout=15)
    target_result = subprocess.run(["wslpath", "-w", str(destination)], check=True,
                                   capture_output=True, text=True, shell=False, timeout=15)
    source = source_result.stdout.strip().replace("'", "''")
    target = target_result.stdout.strip().replace("'", "''")
    script = ("$ErrorActionPreference = 'Stop'; "
              f"[System.IO.Directory]::Move('{source}', '{target}')")
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    result = subprocess.run([executable, "-NoLogo", "-NoProfile", "-NonInteractive",
                             "-EncodedCommand", encoded], check=False, capture_output=True,
                            text=True, shell=False, timeout=30, encoding="utf-8")
    if result.returncode != 0:
        if destination.exists():
            raise FileExistsError(f"Bundle already exists: {destination}")
        raise OSError(f"Windows atomic directory move failed: {result.stderr.strip()}")


def _write_synced(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def publish_bundle(apk: Path, evidence: dict, output_root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Unsafe or empty export run ID")
    if run_id.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                          *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("Reserved export run ID")
    apk, root = Path(apk), Path(output_root).absolute()
    if apk.is_symlink() or not apk.is_file() or apk.suffix.lower() != ".apk":
        raise ValueError("Export requires a regular non-symlink APK")
    if root.resolve() != root:
        raise ValueError("Export root cannot contain escaping symlinks")
    validate_evidence(apk, evidence)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"smoke_{run_id}"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Bundle already exists: {destination}")
    staging = root / f".staging-{run_id}-{uuid.uuid4().hex}"
    staging.mkdir()
    copied = staging / apk.name
    shutil.copyfile(apk, copied)
    if sha256(copied) != evidence["apk_sha256"]:
        raise ValueError("Copied APK hash mismatch")
    _write_synced(staging / "verification.json", json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    _write_synced(staging / "README.md",
                  "# Offline smoke app\n\n"
                  f"APK: `{apk.name}`. SHA-256: `{evidence['apk_sha256']}`.\n\n"
                  "This app checks packaging. It does not test phone cameras. "
                  "The verification record describes its source, signature and Android settings.\n\n"
                  "Transfer the APK to the phone and open it to install. Allow installation from "
                  "the transfer app when Android requests it. Device installation and execution "
                  "remain separate checks.\n")
    saved = json.loads((staging / "verification.json").read_text(encoding="utf-8"),
                       object_pairs_hook=unique_object)
    if saved != evidence or not (staging / "README.md").is_file():
        raise ValueError("Incomplete staged publication")
    validate_evidence(copied, saved)
    _publish(staging, destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("run_id")
    args = parser.parse_args()
    previous = json.loads(args.evidence.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    build = previous.get("build", {})
    preflight = build.get("preflight", {})
    bytecode = previous.get("bytecode", {})
    if previous.get("status") != "verified" or not preflight.get("hostpython") or \
            not preflight.get("build_tools_dir") or not bytecode.get("filename"):
        raise ValueError("Receipt lacks actual build paths for re-verification")
    evidence = verify_apk(args.apk, previous.get("settings"), args.source,
                          Path(preflight["hostpython"]), Path(preflight["build_tools_dir"]),
                          bytecode["filename"])
    evidence = {**evidence, "build": build}
    sys.stdout.write(str(publish_bundle(args.apk, evidence, args.output_root, args.run_id)) + "\n")


if __name__ == "__main__":
    main()
