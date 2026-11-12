"""Controls for preserving inherited build inputs and selecting exact caches."""

import importlib.util
import json
import sys
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

import pytest

BUILD = Path(__file__).parents[1] / "build"
if str(BUILD) not in sys.path:
    sys.path.insert(0, str(BUILD))


def load_runner():
    path = Path(__file__).parents[1] / "build" / "warm.py"
    spec = importlib.util.spec_from_file_location("capture_warm", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scratch_must_not_contain_or_overlap_inputs(tmp_path):
    runner = load_runner()
    original = tmp_path / "original"
    original.mkdir()
    for scratch in (original, original / "child", tmp_path):
        with pytest.raises(ValueError, match="overlap"):
            runner.validate_scratch(scratch, [original])
    runner.validate_scratch(tmp_path / "independent", [original])


def test_scratch_existing_destination_is_rejected(tmp_path):
    with pytest.raises(FileExistsError):
        load_runner().validate_scratch(tmp_path, [])


def test_distribution_exact_recipe_matching(tmp_path):
    runner = load_runner()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    metadata = {
        "dist_name": config["dist_name"], "bootstrap": "sdl2",
        "archs": ["arm64-v8a"], "ndk_api": 24, "use_setup_py": False,
        "recipes": config["warm_recipes"], "python_version": "3.14",
    }
    runner.validate_distribution(metadata, config)
    with pytest.raises(ValueError, match="recipes"):
        runner.validate_distribution({**metadata, "recipes": ["python3"]}, config)


@pytest.mark.parametrize("key,value", [
    ("bootstrap", "webview"), ("archs", ["x86_64"]), ("ndk_api", 23),
    ("use_setup_py", True), ("python_version", "3.13"),
    ("dist_name", "other"),
])
def test_distribution_wrong_contract_rejected(key, value):
    runner = load_runner()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    metadata = {
        "dist_name": config["dist_name"], "bootstrap": "sdl2",
        "archs": ["arm64-v8a"], "ndk_api": 24, "use_setup_py": False,
        "recipes": config["warm_recipes"], "python_version": "3.14",
    }
    with pytest.raises(ValueError, match=key):
        runner.validate_distribution({**metadata, key: value}, config)


def test_packaging_arguments_keep_paths_and_force_compatible_warm_reuse(tmp_path):
    runner = load_runner()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    arguments = runner.packaging_arguments(config, tmp_path / "space ; $(unsafe)",
        tmp_path / "sdk", tmp_path / "ndk", tmp_path / "app", tmp_path / "storage")
    assert arguments[0] == str(tmp_path / "space ; $(unsafe)")
    assert "--requirements=" + ",".join(config["warm_recipes"]) in arguments
    assert "--require-perfect-match" in arguments
    assert "--no-allow-replace-dist" in arguments
    assert "--private=" + str(tmp_path / "app") in arguments
    assert "--dist-name=unnamed_dist_1" in arguments
    clean = runner.packaging_arguments(config, tmp_path / "p4a", tmp_path / "sdk",
        tmp_path / "ndk", tmp_path / "app", tmp_path / "storage", reuse_distribution=False)
    assert "--require-perfect-match" not in clean
    assert "--no-allow-replace-dist" not in clean


def test_camera_packaging_is_opt_in_and_declares_java_activity_permission(tmp_path):
    runner = load_runner()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    common = (config, tmp_path / "p4a", tmp_path / "sdk", tmp_path / "ndk",
              tmp_path / "app", tmp_path / "storage")
    smoke = runner.packaging_arguments(*common)
    assert not any(argument.startswith(("--android-entrypoint", "--add-source", "--permission"))
                   for argument in smoke)
    profile = {
        "package": "org.fyld.capturecheck",
        "name": "FYLD Camera Capture",
        "version": "0.1",
        "version_code": 10242,
        "activity_class_name": "org.fyld.capture.CameraActivity",
        "permissions": ["android.permission.CAMERA"],
    }
    camera_source = tmp_path / "camera java"
    camera = runner.packaging_arguments(*common, camera_profile=profile,
                                       java_source_root=camera_source)
    assert "--package=org.fyld.capturecheck" in camera
    assert "--android-entrypoint=org.fyld.capture.CameraActivity" in camera
    assert f"--add-source={camera_source}" in camera
    assert "--permission=android.permission.CAMERA" in camera
    assert "--numeric-version=10242" in camera


def test_camera_source_manifest_hashes_and_stages_immutable_sources(tmp_path):
    runner = load_runner()
    source_root = tmp_path / "source"
    java = source_root / "native/camera/java/org/fyld/capture/CameraActivity.java"
    java.parent.mkdir(parents=True)
    original = b"package org.fyld.capture;\n"
    java.write_bytes(original)
    manifest = tmp_path / "camera-sources.json"
    manifest.write_text(json.dumps({"schema_version": 1, "java_sources": [{
        "path": java.relative_to(source_root).as_posix(),
        "sha256": runner.digest(java),
    }]}), encoding="utf-8")
    staged = tmp_path / "staged camera java"
    runner.stage_camera_sources(source_root, manifest, staged)
    assert (staged / "org/fyld/capture/CameraActivity.java").read_bytes() == original
    assert java.read_bytes() == original


def test_camera_source_manifest_rejects_non_string_hash():
    runner = load_runner()
    payload = json.dumps({"schema_version": 1, "java_sources": [{
        "path": "native/camera/java/org/fyld/capture/CameraActivity.java",
        "sha256": 123,
    }]})
    with patch.object(Path, "read_text", return_value=payload), pytest.raises(ValueError, match="hash"):
        runner.checked_camera_sources(Path("source"), Path("manifest"))


@pytest.mark.parametrize("source_path", ["../escape.java", "C:/escape.java", "native\\escape.java"])
def test_camera_source_manifest_rejects_unsafe_paths(tmp_path, source_path):
    runner = load_runner()
    source_root = tmp_path / "source"
    source_root.mkdir()
    manifest = tmp_path / "camera-sources.json"
    manifest.write_text(json.dumps({"schema_version": 1, "java_sources": [{
        "path": source_path, "sha256": "0" * 64,
    }]}), encoding="utf-8")
    with pytest.raises(ValueError, match="source|path"):
        runner.stage_camera_sources(source_root, manifest, tmp_path / "staged")
    assert not (tmp_path / "staged").exists()


def test_offline_wrapper_changes_only_scratch(tmp_path):
    runner = load_runner()
    original = tmp_path / "original"
    scratch = tmp_path / "scratch"
    original.mkdir()
    scratch.mkdir()
    content = "#!/bin/sh\nexit 0\n"
    (original / "gradlew").write_text(content)
    (scratch / "gradlew").write_text(content)
    runner.install_offline_wrapper(scratch)
    assert (original / "gradlew").read_text() == content
    assert (scratch / "gradlew.real").read_text() == content
    assert '--offline "$@"' in (scratch / "gradlew").read_text()
    with pytest.raises(FileExistsError):
        runner.install_offline_wrapper(scratch)


def test_preservation_detects_changed_and_missing_original(tmp_path):
    runner = load_runner()
    original = tmp_path / "source"
    original.write_bytes(b"inherited")
    before = runner.hash_inputs([original])
    runner.assert_preserved(before)
    original.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        runner.assert_preserved(before)
    original.unlink()
    with pytest.raises(FileNotFoundError):
        runner.assert_preserved(before)


def test_gradle_contract_wrong_wrapper_and_plugin_rejected(tmp_path):
    runner = load_runner()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    project = tmp_path / "project"
    (project / "gradle/wrapper").mkdir(parents=True)
    properties = project / "gradle/wrapper/gradle-wrapper.properties"
    gradle = project / "build.gradle"
    properties.write_text("distributionUrl=https\\://services.gradle.org/distributions/gradle-8.14.3-all.zip\n")
    gradle.write_text("classpath 'com.android.tools.build:gradle:8.11.0'\ncompileSdkVersion 36\nbuildToolsVersion '35.0.0'\n")
    runner.validate_gradle(project, config)
    properties.write_text("distributionUrl=https://other.example/gradle-8.14.3-all.zip\n")
    with pytest.raises(ValueError, match="wrapper"):
        runner.validate_gradle(project, config)
    properties.write_text("distributionUrl=https\\://services.gradle.org/distributions/gradle-8.14.3-all.zip\n")
    gradle.write_text("classpath 'com.android.tools.build:gradle:8.10.0'\n")
    with pytest.raises(ValueError, match="Gradle"):
        runner.validate_gradle(project, config)


def test_warm_run_publishes_only_after_packaging_and_verification(tmp_path, monkeypatch):
    runner = load_runner()
    build = str(Path(__file__).parents[1] / "build")
    sys.path.insert(0, build) if build not in sys.path else None
    import export
    import verify

    settings = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())
    args = type("Args", (), {
        "p4a_env": tmp_path / "p4a", "sdk": tmp_path / "sdk",
        "predecessor_root": tmp_path / "predecessor", "gradle_cache": tmp_path / "gradle",
        "scratch": tmp_path / "scratch", "output_root": tmp_path / "output", "run_id": "control",
    })()
    args.scratch.mkdir()
    info = {"protected": {}, "cache_artifacts": {}, "hostpython": "/pinned/hostpython"}
    app, storage, environment = tmp_path / "app", tmp_path / "storage", {"PATH": "/bin"}
    apk = storage / "dists/unnamed_dist_1/build/outputs/apk/debug/unnamed_dist_1-debug.apk"
    monkeypatch.setattr(runner, "preflight", lambda *_: info)
    monkeypatch.setattr(runner, "prepare", lambda *_: (app, storage, environment))
    monkeypatch.setattr(runner, "native_control", lambda *_: {"format": "ELF64 little-endian AArch64"})
    monkeypatch.setattr(runner, "packaging_arguments", lambda *_, **__: ["fixture-p4a", "apk"])
    monkeypatch.setattr(runner, "validate_gradle", lambda *_: None)
    monkeypatch.setattr(runner, "assert_preserved", lambda _: None)
    monkeypatch.setattr(verify, "verify_apk", lambda *values, **kwargs: {
        "status": "verified", "settings": settings, "bytecode": {"filename": values[-1]},
    })
    published = tmp_path / "published"
    monkeypatch.setattr(export, "publish_bundle", lambda *values: published)

    def package(*_args, **_kwargs):
        apk.parent.mkdir(parents=True)
        apk.write_bytes(b"fixture APK bytes")
        return CompletedProcess([], 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", package)
    assert runner.run(args) == published
    receipt = json.loads((args.scratch / "build_receipt.json").read_text())
    assert receipt["status"] == "verified"
    assert receipt["build"]["packaging_exit_code"] == 0
    assert receipt["build"]["native_control"]["format"] == "ELF64 little-endian AArch64"
    assert receipt["bytecode"]["filename"] == str(args.scratch.resolve() / "app/main.py")


def test_warm_run_failure_records_exit_and_never_verifies_or_publishes(tmp_path, monkeypatch):
    runner = load_runner()
    build = str(Path(__file__).parents[1] / "build")
    sys.path.insert(0, build) if build not in sys.path else None
    import export
    import verify

    args = type("Args", (), {
        "p4a_env": tmp_path / "p4a", "sdk": tmp_path / "sdk",
        "predecessor_root": tmp_path / "predecessor", "gradle_cache": tmp_path / "gradle",
        "scratch": tmp_path / "scratch", "output_root": tmp_path / "output", "run_id": "failed",
    })()
    args.scratch.mkdir()
    monkeypatch.setattr(runner, "preflight", lambda *_: {"protected": {}, "cache_artifacts": {}, "hostpython": "/pinned/hostpython"})
    monkeypatch.setattr(runner, "prepare", lambda *_: (tmp_path / "app", tmp_path / "storage", {}))
    monkeypatch.setattr(runner, "native_control", lambda *_: {"format": "ELF64 little-endian AArch64"})
    monkeypatch.setattr(runner, "packaging_arguments", lambda *_, **__: ["fixture-p4a", "apk"])
    monkeypatch.setattr(runner, "assert_preserved", lambda _: None)
    monkeypatch.setattr(verify, "verify_apk", lambda *_: pytest.fail("failed build reached verifier"))
    monkeypatch.setattr(export, "publish_bundle", lambda *_: pytest.fail("failed build reached publication"))
    monkeypatch.setattr(runner.subprocess, "run", lambda *_args, **_kwargs: CompletedProcess([], 7, "", "build failed"))
    with pytest.raises(CalledProcessError, match="returned non-zero exit status 7"):
        runner.run(args)
    receipt = json.loads((args.scratch / "build_receipt.json").read_text())
    assert receipt["packaging_exit_code"] == 7
    assert receipt["status"] == "incomplete"


def test_prepare_copies_scratch_inputs_and_leaves_sources_unchanged(tmp_path):
    runner = load_runner()
    source_root = Path(__file__).parents[1]
    predecessor = tmp_path / "predecessor"
    original_project = predecessor / "p4a-storage/dists/unnamed_dist_1"
    original_project.mkdir(parents=True)
    (original_project / "gradlew").write_text("#!/bin/sh\nexit 0\n")
    original_gradle = tmp_path / "gradle-cache"
    original_gradle.mkdir()
    (original_gradle / "cached.jar").write_bytes(b"cached")
    args = type("Args", (), {
        "p4a_env": tmp_path / "p4a", "sdk": tmp_path / "sdk",
        "predecessor_root": predecessor, "gradle_cache": original_gradle,
        "scratch": tmp_path / "isolated scratch", "output_root": tmp_path / "output",
    })()
    original_wrapper = (original_project / "gradlew").read_bytes()
    config = json.loads((source_root / "build/toolchain.json").read_text())
    app, storage, environment = runner.prepare(args, config, {"project": str(original_project)}, source_root)
    scratch_project = storage / "dists/unnamed_dist_1"
    assert (app / "main.py").read_bytes() == (source_root / "app/main.py").read_bytes()
    assert (scratch_project / "gradlew.real").read_bytes() == original_wrapper
    assert "--offline \"$@\"" in (scratch_project / "gradlew").read_text()
    assert (args.scratch / "gradle/cached.jar").read_bytes() == b"cached"
    assert (original_project / "gradlew").read_bytes() == original_wrapper
    assert (original_gradle / "cached.jar").read_bytes() == b"cached"
    assert environment["ANDROID_HOME"] == str(args.sdk)
    assert environment["GRADLE_USER_HOME"] == str(args.scratch / "gradle")
    assert environment["HTTPS_PROXY"] == "http://127.0.0.1:9"
    assert environment["NO_PROXY"] == ""
    assert (args.scratch / "gradle/init.d/90-fyld-task24-offline.init.gradle").is_file()


def test_clean_prepare_starts_without_generated_distribution(tmp_path):
    runner = load_runner()
    source_root = Path(__file__).parents[1]
    predecessor = tmp_path / "predecessor"
    original_project = predecessor / "p4a-storage/dists/unnamed_dist_1"
    original_project.mkdir(parents=True)
    packages = predecessor / "p4a-storage/packages"
    packages.mkdir()
    (packages / "source.tar.gz").write_bytes(b"inherited package")
    gradle = tmp_path / "gradle"
    gradle.mkdir()
    (gradle / "cached.jar").write_bytes(b"cached")
    args = type("Args", (), {
        "p4a_env": tmp_path / "p4a", "sdk": tmp_path / "sdk",
        "predecessor_root": predecessor, "gradle_cache": gradle,
        "scratch": tmp_path / "cold scratch", "output_root": tmp_path / "output",
    })()
    config = json.loads((source_root / "build/toolchain.json").read_text())
    app, storage, _environment = runner.prepare(args, config,
        {"project": str(original_project)}, source_root, mode="cold")
    assert (app / "main.py").is_file()
    assert (storage / "packages/source.tar.gz").read_bytes() == b"inherited package"
    assert not (storage / "dists/unnamed_dist_1").exists()
    assert (args.scratch / "gradle/init.d/90-fyld-task24-offline.init.gradle").is_file()
    assert (gradle / "cached.jar").read_bytes() == b"cached"


def test_native_control_checks_elf_class_and_machine(tmp_path, monkeypatch):
    runner = load_runner()
    args = type("Args", (), {"sdk": tmp_path / "sdk", "scratch": tmp_path / "scratch"})()
    args.scratch.mkdir()
    config = json.loads((Path(__file__).parents[1] / "build/toolchain.json").read_text())

    def compile_native(arguments):
        output = Path(arguments[-1])
        header = bytearray(20)
        header[:6] = b"\x7fELF\x02\x01"
        header[18:20] = (183).to_bytes(2, "little")
        output.write_bytes(header)

    monkeypatch.setattr(runner, "command", compile_native)
    assert runner.native_control(args, config, Path(__file__).parents[1])["format"] == "ELF64 little-endian AArch64"
    monkeypatch.setattr(runner, "command", lambda values: Path(values[-1]).write_bytes(b"wrong ELF"))
    with pytest.raises(ValueError, match="ELF64 AArch64"):
        runner.native_control(args, config, Path(__file__).parents[1])


def test_revision_version_and_cache_controls(tmp_path, monkeypatch):
    runner = load_runner()
    properties = tmp_path / "source.properties"
    properties.write_text("Pkg.Revision = 35.0.0\n")
    runner.read_revision(properties, "35.0.0")
    with pytest.raises(ValueError, match="revision mismatch"):
        runner.read_revision(properties, "36.0.0")
    monkeypatch.setattr(runner, "command", lambda _: "Python 3.12.3")
    assert runner.checked_version(["python", "--version"], "3.12.3", "host Python") == "Python 3.12.3"
    with pytest.raises(ValueError, match="does not match"):
        runner.checked_version(["python", "--version"], "3.13.0", "host Python")
    (tmp_path / "library.jar").write_bytes(b"jar")
    (tmp_path / "plain.txt").write_text("skip")
    assert [p.name for p in runner.cached_artifacts(tmp_path)] == ["library.jar"]
