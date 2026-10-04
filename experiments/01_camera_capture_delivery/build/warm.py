"""Reproduce cached p4a packaging without changing the inherited installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def hash_inputs(paths: list[Path]) -> dict[str, str]:
    return {str(path.resolve()): digest(path) for path in paths}


def assert_preserved(before: dict[str, str]) -> None:
    for path, expected in before.items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Inherited input changed: {path}")


def validate_scratch(scratch: Path, protected: list[Path]) -> None:
    target = scratch.resolve()
    for path in protected:
        source = path.resolve()
        if target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError(f"Scratch/input overlap: {target}, {source}")
    if target.exists():
        raise FileExistsError(f"Scratch must be a new directory: {target}")


def load_camera_profile(source_root: Path) -> dict[str, Any]:
    from recipe import unique_object

    profile_path = Path(source_root) / "build/camera-profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    expected = {"schema_version", "package", "name", "version", "version_code",
                "activity_class_name", "permissions", "java_sources"}
    if (not isinstance(profile, dict) or set(profile) != expected
            or type(profile["schema_version"]) is not int or profile["schema_version"] != 1):
        raise ValueError("Malformed camera package profile")
    strings = ("package", "name", "version", "activity_class_name")
    if any(not isinstance(profile[key], str) or not profile[key].strip() for key in strings):
        raise ValueError("Camera package identity fields must be non-empty strings")
    if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", profile["package"])
            or not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+",
                                profile["activity_class_name"])):
        raise ValueError("Unsafe camera package or activity name")
    if type(profile["version_code"]) is not int or profile["version_code"] <= 0:
        raise ValueError("Camera version code must be a positive integer")
    if profile["permissions"] != ["android.permission.CAMERA"]:
        raise ValueError("Camera package must request only the reviewed CAMERA permission")
    if not isinstance(profile["java_sources"], list) or not profile["java_sources"]:
        raise ValueError("Camera package must pin at least one Java source")
    return profile


def checked_camera_sources(source_root: Path, manifest_source: Path | dict) -> list[tuple[Path, PurePosixPath]]:
    from recipe import unique_object

    source_root = Path(source_root)
    if isinstance(manifest_source, dict):
        manifest = manifest_source
    else:
        manifest = json.loads(Path(manifest_source).read_text(encoding="utf-8"),
                              object_pairs_hook=unique_object)
    entries = manifest.get("java_sources") if isinstance(manifest, dict) else None
    if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int
            or manifest["schema_version"] != 1 or not isinstance(entries, list) or not entries):
        raise ValueError("Malformed camera source manifest")
    checked: list[tuple[Path, PurePosixPath]] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("Malformed camera source entry")
        relative = entry["path"]
        source_hash = entry["sha256"]
        if (not isinstance(relative, str) or not isinstance(source_hash, str)
                or "\\" in relative or
                not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise ValueError("Unsafe camera source path or hash")
        posix = PurePosixPath(relative)
        if posix.is_absolute() or ".." in posix.parts or "." in posix.parts or not relative.startswith("native/camera/java/") or posix.suffix != ".java":
            raise ValueError("Unsafe camera Java source path")
        source = source_root.joinpath(*posix.parts)
        if any(part.is_symlink() for part in [source_root, *source.parents]):
            raise ValueError("Camera source path may not contain symlinks")
        if source.is_symlink() or not source.is_file() or digest(source) != entry["sha256"]:
            raise ValueError(f"Camera source missing or hash mismatch: {relative}")
        checked.append((source, PurePosixPath(*posix.parts[3:])))
    return checked


def stage_camera_sources(source_root: Path, manifest_source: Path | dict, destination: Path) -> Path:
    checked = checked_camera_sources(source_root, manifest_source)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Camera source staging destination exists: {destination}")
    destination.mkdir(parents=True)
    for source, relative in checked:
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if digest(target) != digest(source):
            raise ValueError(f"Staged camera source changed during copy: {source}")
    return destination


def validate_distribution(metadata: dict[str, Any], config: dict[str, Any]) -> None:
    expected = {
        "dist_name": config["dist_name"], "bootstrap": config["bootstrap"],
        "archs": [config["abi"]], "ndk_api": config["ndk_api"],
        "use_setup_py": False, "python_version": ".".join(config["android_python"].split(".")[:2]),
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"Incompatible cached distribution: {key}")
    if sorted(metadata.get("recipes", [])) != sorted(config["warm_recipes"]):
        raise ValueError("Incompatible cached distribution: recipes")


def validate_gradle(project: Path, config: dict[str, Any]) -> None:
    text = (project / "build.gradle").read_text()
    required = (
        f"classpath 'com.android.tools.build:gradle:{config['android_gradle_plugin']}'",
        f"compileSdkVersion {config['android_api']}",
        f"buildToolsVersion '{config['build_tools']}'",
    )
    if not all(value in text for value in required):
        raise ValueError("Cached Android Gradle settings differ from pins")
    properties = (project / "gradle/wrapper/gradle-wrapper.properties").read_text()
    url = f"https\\://services.gradle.org/distributions/gradle-{config['gradle']}-all.zip"
    if properties.count("distributionUrl=") != 1 or f"distributionUrl={url}\n" not in properties:
        raise ValueError("Cached Gradle wrapper differs from pin")


def install_offline_wrapper(project: Path) -> None:
    original = project / "gradlew"
    renamed = project / "gradlew.real"
    if renamed.exists():
        raise FileExistsError(renamed)
    original.rename(renamed)
    original.write_text('#!/bin/sh\nexec "$(dirname "$0")/gradlew.real" --offline "$@"\n')
    original.chmod(0o755)


def install_gradle_offline_init(gradle_home: Path) -> Path:
    init_directory = gradle_home / "init.d"
    init_directory.mkdir(parents=True, exist_ok=True)
    init_script = init_directory / "90-fyld-task24-offline.init.gradle"
    if init_script.exists():
        raise FileExistsError(init_script)
    init_script.write_text("allprojects { gradle.startParameter.offline = true }\n")
    return init_script


def packaging_arguments(config: dict[str, Any], p4a: Path, sdk: Path,
                        ndk: Path, app: Path, storage: Path,
                        reuse_distribution: bool = True,
                        camera_profile: dict[str, Any] | None = None,
                        java_source_root: Path | None = None) -> list[str]:
    values = {
        "sdk-dir": sdk, "ndk-dir": ndk, "storage-dir": storage,
        "dist-name": config["dist_name"], "bootstrap": config["bootstrap"],
        "requirements": ",".join(config["warm_recipes"]), "arch": config["abi"],
        "android-api": config["android_api"], "ndk-api": config["ndk_api"],
        "private": app, "package": config["package"], "name": config["name"],
        "version": config["version"], "numeric-version": config["version_code"],
        "minsdk": config["min_sdk"], "java-build-tool": "gradle",
    }
    if camera_profile is not None:
        if java_source_root is None:
            raise ValueError("Camera profile requires staged Java sources")
        values.update({"package": camera_profile["package"], "name": camera_profile["name"],
                       "version": camera_profile["version"],
                       "numeric-version": camera_profile["version_code"]})
    arguments = [str(p4a), "apk", *(f"--{key}={value}" for key, value in values.items()),
                 "--ignore-setup-py"]
    if camera_profile is not None:
        arguments.append(f"--activity-class-name={camera_profile['activity_class_name']}")
        arguments.append(f"--add-source={java_source_root}")
        arguments.extend(f"--permission={permission}" for permission in camera_profile["permissions"])
    if reuse_distribution:
        arguments.extend(("--require-perfect-match", "--no-allow-replace-dist"))
    return arguments


def command(arguments: list[str], *, cwd: Path | None = None,
            env: dict[str, str] | None = None) -> str:
    result = subprocess.run(arguments, cwd=cwd, env=env, check=True,
                            text=True, capture_output=True)
    return result.stdout + result.stderr


def checked_version(arguments: list[str], expected: str, label: str) -> str:
    output = command(arguments)
    if not re.search(r"(?<![\d.])" + re.escape(expected) + r"(?![\d.])", output):
        raise ValueError(f"{label} version does not match {expected}: {output}")
    return output.strip()


def read_revision(path: Path, expected: str) -> None:
    properties = path.read_text()
    if not re.search(r"^Pkg.Revision\s*=\s*" + re.escape(expected) + r"\s*$", properties, re.MULTILINE):
        raise ValueError(f"SDK revision mismatch: {path}")


def cached_artifacts(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*")
                  if path.is_file() and path.suffix in {".zip", ".jar", ".pom", ".gz", ".xz", ".bz2"})


def preflight(args: argparse.Namespace, config: dict[str, Any], source_root: Path,
              camera_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    p4a = args.p4a_env / "bin/p4a"
    ndk = args.sdk / "ndk" / config["ndk"]
    project = args.predecessor_root / "p4a-storage/dists" / config["dist_name"]
    metadata = json.loads((project / "dist_info.json").read_text())
    validate_distribution(metadata, config)
    validate_gradle(project, config)
    hostpython = Path(metadata["hostpython"])
    checks = {
        "p4a": checked_version([str(p4a), "--version"], config["p4a"], "p4a"),
        "host_python": checked_version([str(args.p4a_env / "bin/python"), "--version"], config["host_python"], "host Python"),
        "android_python": checked_version([str(hostpython), "--version"], config["android_python"], "Android hostpython"),
        "java": checked_version(["java", "-version"], config["java"], "Java"),
    }
    if f"Ubuntu {config['ubuntu']} LTS" not in Path("/etc/os-release").read_text():
        raise ValueError("Ubuntu release differs from inherited pin")
    read_revision(ndk / "source.properties", config["ndk"])
    read_revision(args.sdk / "build-tools" / config["build_tools"] / "source.properties", config["build_tools"])
    read_revision(args.sdk / "platform-tools/source.properties", config["platform_tools"])
    if not (args.sdk / "platforms" / f"android-{config['android_api']}" / "android.jar").is_file():
        raise FileNotFoundError("Pinned Android platform is unavailable")
    sources = {"source_sha256": source_root / "app/main.py", "native_source_sha256": source_root / "native/smoke.c"}
    camera_sources = []
    if camera_profile is not None:
        manifest = source_root / "build/camera-profile.json"
        checked_camera_sources(source_root, camera_profile)
        camera_sources = [source_root / entry["path"] for entry in camera_profile["java_sources"]]
        camera_sources.append(manifest)
    for key, path in sources.items():
        if digest(path) != config[key]:
            raise ValueError(f"Recovered source hash mismatch: {path}")
    predecessor = args.predecessor_root / "app/unnamed_dist_1-debug-0.1.apk"
    if digest(predecessor) != config["predecessor_apk_sha256"]:
        raise ValueError("Predecessor APK changed")
    archives = {
        "p4a_wheel_sha256": args.predecessor_root / "python_for_android-2026.5.9-py3-none-any.whl",
        "gradle_sha256": args.predecessor_root / f"gradle-{config['gradle']}-all.zip",
    }
    for key, path in archives.items():
        if digest(path) != config[key]:
            raise ValueError(f"Pinned archive hash mismatch: {path}")
    protected = [*sources.values(), *camera_sources, args.predecessor_root / "app/main.py",
                 args.predecessor_root / "smoke.c", predecessor,
                 project / "dist_info.json", project / "build.gradle", project / "gradlew",
                 project / "gradle/wrapper/gradle-wrapper.properties", *archives.values()]
    artifacts = cached_artifacts(args.predecessor_root / "p4a-storage/packages")
    artifacts += cached_artifacts(args.gradle_cache)
    return {"checks": checks, "sdk_dir": str(args.sdk.resolve()),
            "build_tools_dir": str((args.sdk / "build-tools" / config["build_tools"]).resolve()),
            "protected": hash_inputs(protected),
            "cache_artifacts": hash_inputs(artifacts), "hostpython": str(hostpython),
            "dist_metadata": metadata, "project": str(project)}


def copy_snapshot(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if path.is_symlink() and not path.resolve().is_relative_to(source.resolve()):
            raise ValueError(f"Cache symlink escapes its source: {path}")
    shutil.copytree(source, target, symlinks=True)


def prepare(args: argparse.Namespace, config: dict[str, Any], info: dict[str, Any],
            source_root: Path, mode: str = "warm",
            camera_profile: dict[str, Any] | None = None) -> tuple[Path, Path, dict[str, str]]:
    scratch = args.scratch.resolve()
    validate_scratch(scratch, [args.sdk, args.p4a_env, args.predecessor_root,
                              args.gradle_cache, source_root, args.output_root])
    scratch.mkdir(parents=True)
    app = scratch / "app"
    app.mkdir()
    shutil.copyfile(source_root / "app/main.py", app / "main.py")
    if camera_profile is not None:
        stage_camera_sources(source_root, camera_profile, scratch / "camera-java")
    storage = scratch / "storage"
    if mode == "warm":
        project = storage / "dists" / config["dist_name"]
        copy_snapshot(Path(info["project"]), project)
    elif mode == "cold":
        copy_snapshot(args.predecessor_root / "p4a-storage/packages", storage / "packages")
    else:
        raise ValueError(f"Unsupported build scope: {mode}")
    copy_snapshot(args.gradle_cache, scratch / "gradle")
    if mode == "warm":
        install_offline_wrapper(project)
    install_gradle_offline_init(scratch / "gradle")
    environment = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "JAVA_HOME", "SYSTEMROOT") if key in os.environ}
    environment.update({"HOME": str(scratch / "home"), "GRADLE_USER_HOME": str(scratch / "gradle"),
                        "ANDROID_USER_HOME": str(scratch / "android"), "ANDROID_HOME": str(args.sdk),
                        "ANDROID_SDK_ROOT": str(args.sdk), "ANDROID_NDK_HOME": str(args.sdk / "ndk" / config["ndk"]),
                        "PYTHONNOUSERSITE": "1",
                        "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
                        "ALL_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9",
                        "https_proxy": "http://127.0.0.1:9", "all_proxy": "http://127.0.0.1:9",
                        "NO_PROXY": "", "no_proxy": ""})
    Path(environment["HOME"]).mkdir()
    Path(environment["ANDROID_USER_HOME"]).mkdir()
    return app, storage, environment


def native_control(args: argparse.Namespace, config: dict[str, Any], source_root: Path) -> dict[str, str]:
    clang = args.sdk / "ndk" / config["ndk"] / "toolchains/llvm/prebuilt/linux-x86_64/bin" / f"aarch64-linux-android{config['ndk_api']}-clang"
    output = args.scratch / "libsmoke.so"
    invocation = [str(clang), "-shared", "-fPIC", str(source_root / "native/smoke.c"), "-o", str(output)]
    command(invocation)
    header = output.read_bytes()[:20]
    if header[:6] != b"\x7fELF\x02\x01" or int.from_bytes(header[18:20], "little") != 183:
        raise ValueError("Native compile did not emit ELF64 AArch64")
    return {"sha256": digest(output), "format": "ELF64 little-endian AArch64", "command": invocation}


def run(args: argparse.Namespace) -> Path:
    # Imports are local so guard helpers remain usable without optional test tooling.
    from export import publish_bundle
    from recipe import load_settings
    from verify import verify_apk

    source_root = Path(__file__).resolve().parents[1]
    config = load_settings(source_root / "build/toolchain.json")
    mode = getattr(args, "mode", "warm")
    camera_profile = load_camera_profile(source_root) if getattr(args, "camera", False) else None
    started = time.monotonic()
    info = preflight(args, config, source_root, camera_profile)
    app, storage, environment = prepare(args, config, info, source_root, mode, camera_profile)
    assert_preserved(info["protected"])
    receipt_path = args.scratch / "build_receipt.json"
    scope = "warm_cached_camera_packaging" if camera_profile and mode == "warm" else (
        "fresh_camera_dependency_build" if camera_profile else
        "warm_cached_packaging" if mode == "warm" else "fresh_dependency_build")
    receipt = {"schema_version": 1, "status": "incomplete", "build_scope": scope,
               "preflight": info, "pins": config, "scratch": str(args.scratch),
               "created_utc": datetime.now(timezone.utc).isoformat()}
    receipt_path.write_text(json.dumps(receipt, indent=2))
    try:
        native = native_control(args, config, source_root)
        invocation = packaging_arguments(config, args.p4a_env / "bin/p4a", args.sdk,
                                        args.sdk / "ndk" / config["ndk"], app, storage,
                                        reuse_distribution=mode == "warm",
                                        camera_profile=camera_profile,
                                        java_source_root=args.scratch / "camera-java" if camera_profile else None)
        log = args.scratch / "packaging.log"
        with log.open("w") as stream:
            result = subprocess.run(invocation, cwd=app, env=environment, stdout=stream,
                                    stderr=subprocess.STDOUT, check=False)
        receipt = {**receipt, "packaging_command": invocation, "packaging_exit_code": result.returncode,
                   "native_control": native, "elapsed_seconds": time.monotonic() - started}
        receipt_path.write_text(json.dumps(receipt, indent=2))
        result.check_returncode()
        project = storage / "dists" / config["dist_name"]
        validate_gradle(project, config)
        apk = project / "build/outputs/apk/debug" / f"{config['dist_name']}-debug.apk"
        evidence = verify_apk(apk, config, source_root / "app/main.py", Path(info["hostpython"]),
                              args.sdk / "build-tools" / config["build_tools"],
                              str(args.scratch.resolve() / "app/main.py"), camera_profile=camera_profile)
        assert_preserved(info["protected"])
        assert_preserved(info["cache_artifacts"])
        evidence = {**evidence, "build": {**receipt, "status": "verified",
                    "preserved_predecessor": True, "elapsed_seconds": time.monotonic() - started}}
        receipt_path.write_text(json.dumps(evidence, indent=2))
        return publish_bundle(apk, evidence, args.output_root, args.run_id)
    finally:
        assert_preserved(info["protected"])
        assert_preserved(info["cache_artifacts"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("p4a-env", "sdk", "predecessor-root", "gradle-cache", "scratch", "output-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=("warm", "cold"), default="warm")
    parser.add_argument("--camera", action="store_true",
                        help="build the isolated native Camera2 package profile")
    args = parser.parse_args()
    print(run(args))


if __name__ == "__main__":
    main()
