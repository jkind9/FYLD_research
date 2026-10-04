"""Synthetic controls; passing these tests is not evidence of a real APK build."""

import base64
import gzip
import hashlib
import importlib
import io
import json
import marshal
import struct
import sys
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from subprocess import CompletedProcess
from threading import Barrier

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))
recipe = importlib.import_module("recipe")
verify = importlib.import_module("verify")
export = importlib.import_module("export")
bytecode = importlib.import_module("verify_bytecode")
warm = importlib.import_module("warm")

SOURCE = b"print(42)\n"
FILENAME = "/scratch/app/main.py"
CERT = "ab" * 32
SIGNATURE = (
    "Verifies\nVerified using v1 scheme (JAR signing): true\n"
    "Verified using v2 scheme (APK Signature Scheme v2): true\n"
    f"Signer #1 certificate SHA-256 digest: {CERT}\n"
)
BADGING = (
    "package: name='org.fyld.toolchainsmoke' versionCode='10241' "
    "versionName='0.1' platformBuildVersionName='16'\n"
    "sdkVersion:'24'\ntargetSdkVersion:'36'\napplication-debuggable\n"
    "native-code: 'arm64-v8a'\n"
)


def private_tar(payload: bytes, name: str = "main.pyc", duplicate=False) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for _ in range(2 if duplicate else 1):
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    return stream.getvalue()


def pyc(source=SOURCE, filename=FILENAME):
    return importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, 0, len(source)) + marshal.dumps(
        compile(source, filename, "exec", optimize=2)
    )


def elf(machine=183, bits=2, encoding=1):
    header = bytearray(20)
    header[:7] = b"\x7fELF" + bytes((bits, encoding, 1))
    header[18:20] = machine.to_bytes(2, "little")
    return bytes(header)


def python_bundle(library):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for name in ("_python_bundle", "_python_bundle/modules"):
            directory = tarfile.TarInfo(name)
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
        member = tarfile.TarInfo("_python_bundle/modules/example.cpython-314-aarch64-linux-android.so")
        member.size = len(library)
        archive.addfile(member, io.BytesIO(library))
    return gzip.compress(stream.getvalue(), mtime=0)


@pytest.fixture
def settings():
    return dict(recipe.PINS)


@pytest.fixture
def apk(tmp_path):
    path = tmp_path / "synthetic.apk"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("lib/arm64-v8a/libpybundle.so", python_bundle(elf()))
        archive.writestr("assets/private.tar", private_tar(pyc()))
    return path


def tool_result(stdout, code=0):
    return CompletedProcess([], code, stdout, "")


def verifier_dir(evidence):
    return Path(evidence["manifest"]["command"][0]).parent


@pytest.fixture
def verified(apk, settings, tmp_path, monkeypatch):
    source = tmp_path / "main.py"
    source.write_bytes(SOURCE)
    configured = dict(settings, source_sha256=hashlib.sha256(SOURCE).hexdigest())
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("apksigner", "aapt"):
        (tools / name).write_text("fixture", encoding="utf-8")
    hostpython = tmp_path / "hostpython"
    hostpython.write_bytes(b"synthetic verifier executable")
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        if "apksigner" in Path(args[0]).name:
            return tool_result(SIGNATURE)
        if Path(args[0]).name == "aapt":
            return tool_result(BADGING)
        return tool_result(json.dumps({"status": "verified", "source_sha256": recipe.sha256(source),
                                      "python_version": "3.14.2", "filename": FILENAME,
                                      "optimize": 2, "main_pyc_sha256": hashlib.sha256(pyc()).hexdigest()}))

    monkeypatch.setattr(verify.subprocess, "run", run)
    evidence = verify.verify_apk(apk, configured, source, hostpython, tools, FILENAME)
    return apk, evidence, calls


def test_load_settings_pins_and_source_hash(tmp_path, settings):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    assert recipe.load_settings(path) == settings
    assert recipe.sha256(path) == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("key,value", [("package", "wrong.package"), ("abi", "x86_64"),
    ("p4a", "latest"), ("ndk", "27.0"), ("android_api", 35),
    ("min_sdk", True), ("version_code", "10241"), ("source_sha256", "0" * 64)])
def test_reject_changed_pins(tmp_path, settings, key, value):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(dict(settings, **{key: value})), encoding="utf-8")
    with pytest.raises(ValueError):
        recipe.load_settings(path)


@pytest.mark.parametrize("payload", ["null", "[]", "{}", "{", '{"package":"a","package":"b"}'])
def test_reject_invalid_settings(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        recipe.load_settings(path)


def test_signature_strict_success():
    assert verify.parse_signature(tool_result(SIGNATURE))["certificate_sha256"] == [CERT]


@pytest.mark.parametrize("output,code", [(SIGNATURE, 1), ("", 0), ("Not Verifies\n", 0),
    (SIGNATURE.replace(CERT, "bad"), 0), (SIGNATURE.replace("Verifies\n", "DOES NOT VERIFY\n"), 0),
    (SIGNATURE.replace(": true", ": false"), 0)])
def test_reject_signature_failure_or_fabricated_success(output, code):
    with pytest.raises(ValueError):
        verify.parse_signature(tool_result(output, code))


def test_manifest(settings):
    manifest = verify.parse_badging(tool_result(BADGING), settings)
    assert manifest["package"] == "org.fyld.toolchainsmoke"
    assert manifest["version_code"] == 10241
    assert manifest["debuggable"] is True


@pytest.mark.parametrize("old,new", [("org.fyld.toolchainsmoke", "org.other"),
    ("10241", "10242"), ("versionName='0.1'", "versionName='0.2'"),
    ("sdkVersion:'24'", "sdkVersion:'23'"), ("targetSdkVersion:'36'", "targetSdkVersion:'35'"),
    ("application-debuggable", ""), ("arm64-v8a", "x86_64"), ("sdkVersion:'24'", "sdkVersion:'x'")])
def test_manifest_rejects_mismatch(settings, old, new):
    with pytest.raises(ValueError):
        verify.parse_badging(tool_result(BADGING.replace(old, new)), settings)


@pytest.mark.parametrize("output", ["", BADGING + "sdkVersion:'24'\n", BADGING + BADGING])
def test_manifest_rejects_missing_or_duplicate(settings, output):
    with pytest.raises(ValueError):
        verify.parse_badging(tool_result(output), settings)


def test_camera_manifest_requires_declared_permission_and_custom_launch_activity():
    profile = {"activity_class_name": "org.fyld.capture.CameraActivity",
               "permissions": ["android.permission.CAMERA"]}
    valid = (
        "package: name='org.fyld.capturecheck' versionCode='10242' versionName='0.1'\n"
        "uses-permission: name='android.permission.CAMERA'\n"
        "launchable-activity: name='org.fyld.capture.CameraActivity' label='FYLD Camera Capture'\n"
    )
    assert verify.parse_camera_declarations(tool_result(valid), profile) == {
        "permission": "uses-permission: name='android.permission.CAMERA'",
        "launch_activity": "org.fyld.capture.CameraActivity",
    }
    for malformed in (
        valid.replace("uses-permission: name='android.permission.CAMERA'\n", ""),
        valid + "uses-permission: name='android.permission.CAMERA'\n",
        valid + "uses-permission: name='android.permission.RECORD_AUDIO'\n",
        valid + "uses-permission: name='android.permission.RECORD_AUDIO' maxSdkVersion='32'\n",
        valid + "uses-permission-sdk-23: name='android.permission.RECORD_AUDIO'\n",
        valid.replace("org.fyld.capture.CameraActivity", "org.kivy.android.PythonActivity"),
    ):
        with pytest.raises(ValueError):
            verify.parse_camera_declarations(tool_result(malformed), profile)


def test_verified_evidence_binds_files_and_uses_argument_arrays(verified):
    apk, evidence, calls = verified
    assert evidence["apk_sha256"] == recipe.sha256(apk)
    assert evidence["status"] == "verified"
    assert evidence["archive"]["abis"] == ["arm64-v8a"]
    assert len(calls) == 3
    assert all(isinstance(args, list) and kwargs.get("shell", False) is False for args, kwargs in calls)


@pytest.mark.parametrize("members", [{}, {"lib/x86/libx.so": b"x"},
    {"lib/arm64-v8a/libx.so": b"x", "lib/x86/libx.so": b"x"},
    {"lib/arm64-v8a/libx.so": b"x", "../escape": b"x"}])
def test_archive_rejects_missing_mixed_and_unsafe(apk, members):
    with zipfile.ZipFile(apk, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError):
        verify.inspect_archive(apk, "arm64-v8a")


def test_archive_rejects_duplicates_and_corruption(apk):
    with zipfile.ZipFile(apk, "a") as archive, pytest.warns(UserWarning):
        archive.writestr("assets/private.tar", private_tar(pyc()))
    with pytest.raises(ValueError):
        verify.inspect_archive(apk, "arm64-v8a")


@pytest.mark.parametrize("payload", [b"not ELF", elf(machine=62), elf(bits=1), elf(encoding=2)])
def test_archive_rejects_native_library_with_wrong_architecture(apk, payload):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", payload)
        archive.writestr("assets/private.tar", private_tar(pyc()))
    with pytest.raises(ValueError, match="ELF|architecture"):
        verify.inspect_archive(apk, "arm64-v8a")


def test_archive_rejects_unknown_abi(apk):
    with pytest.raises(ValueError, match="Unsupported Android ABI"):
        verify.inspect_archive(apk, "mips")


def test_archive_checks_elf_libraries_inside_python_bundle(apk):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("lib/arm64-v8a/libpybundle.so", python_bundle(elf()))
        archive.writestr("assets/private.tar", private_tar(pyc()))
    evidence = verify.inspect_archive(apk, "arm64-v8a")
    assert evidence["compressed_python_bundles"]["lib/arm64-v8a/libpybundle.so"]["member_count"] == 3
    assert evidence["native_elf"][
        "lib/arm64-v8a/libpybundle.so!_python_bundle/modules/example.cpython-314-aarch64-linux-android.so"
    ] == "ELF64 AArch64"


def test_archive_rejects_wrong_elf_inside_python_bundle(apk):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("lib/arm64-v8a/libpybundle.so", python_bundle(elf(machine=62)))
        archive.writestr("assets/private.tar", private_tar(pyc()))
    with pytest.raises(ValueError, match="ELF architecture"):
        verify.inspect_archive(apk, "arm64-v8a")


def test_archive_requires_compressed_python_bundle(apk):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("lib/arm64-v8a/libpybundle.so", elf())
        archive.writestr("assets/private.tar", private_tar(pyc()))
    with pytest.raises(ValueError, match="Missing compressed Python bundle"):
        verify.inspect_archive(apk, "arm64-v8a")


def test_archive_rejects_missing_python_bundle(apk):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("assets/private.tar", private_tar(pyc()))
    with pytest.raises(ValueError, match="Missing compressed Python bundle"):
        verify.inspect_archive(apk, "arm64-v8a")


def test_archive_rejects_corrupt_native_library_checksum(apk):
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("lib/arm64-v8a/libpython3.14.so", elf())
        archive.writestr("assets/private.tar", private_tar(pyc()))
    payload = bytearray(apk.read_bytes())
    payload[payload.index(b"\x7fELF") + 8] ^= 0x01
    apk.write_bytes(payload)
    with pytest.raises(ValueError, match="Invalid APK archive|ZIP checksum"):
        verify.inspect_archive(apk, "arm64-v8a")
    apk.write_bytes(b"not a ZIP")
    with pytest.raises(ValueError):
        verify.inspect_archive(apk, "arm64-v8a")


def test_bytecode_correspondence(tmp_path, monkeypatch):
    monkeypatch.setattr(bytecode, "require_python", lambda: None)
    source = tmp_path / "main.py"
    source.write_bytes(SOURCE)
    assert bytecode.check_bytecode(private_tar(pyc()), source, FILENAME)["status"] == "verified"


@pytest.mark.parametrize(("version", "reject"), [((3, 14, 2), False), ((3, 14, 1), True)])
def test_bytecode_python_version_gate(monkeypatch, version, reject):
    monkeypatch.setattr(bytecode, "sys", type("Runtime", (), {"version_info": version})())
    if reject:
        with pytest.raises(ValueError, match="Python 3.14.2"):
            bytecode.require_python()
    else:
        bytecode.require_python()


@pytest.mark.parametrize("archive", [private_tar(pyc(b"print(43)\n")),
    private_tar(pyc(filename="/wrong/main.py")), private_tar(b"short"),
    private_tar(pyc(), duplicate=True), private_tar(pyc(), "../main.pyc"),
    private_tar(pyc(), "other.pyc"), b"bad tar"])
def test_bytecode_rejects_wrong_source_headers_members(tmp_path, monkeypatch, archive):
    monkeypatch.setattr(bytecode, "require_python", lambda: None)
    source = tmp_path / "main.py"
    source.write_bytes(SOURCE)
    with pytest.raises(ValueError):
        bytecode.check_bytecode(archive, source, FILENAME)


@pytest.mark.parametrize("payload,match", [
    (pyc()[:4] + struct.pack("<I", 2) + pyc()[8:], "header flags"),
    (private_tar(b"x" * (4 * 1024 * 1024 + 1)), "exceeds"),
])
def test_bytecode_rejects_unsupported_flags_and_oversized_source(tmp_path, monkeypatch, payload, match):
    monkeypatch.setattr(bytecode, "require_python", lambda: None)
    source = tmp_path / "main.py"
    source.write_bytes(SOURCE)
    with pytest.raises(ValueError, match=match):
        bytecode.check_bytecode(private_tar(payload) if match == "header flags" else payload,
                                source, FILENAME)


def test_export_complete_bundle_and_refuse_overwrite(verified, tmp_path):
    apk, evidence, _ = verified
    output = tmp_path / "offline"
    published = export.publish_bundle(apk, evidence, output, "fixture-001", verifier_dir(evidence))
    assert published == output / "smoke_fixture-001"
    assert recipe.sha256(published / apk.name) == recipe.sha256(apk)
    assert json.loads((published / "verification.json").read_text())["apk_sha256"] == recipe.sha256(apk)
    assert (published / "README.md").is_file()
    before = (published / "verification.json").read_bytes()
    with pytest.raises(FileExistsError):
        export.publish_bundle(apk, evidence, output, "fixture-001", verifier_dir(evidence))
    assert (published / "verification.json").read_bytes() == before


def _camera_receipt(apk, evidence):
    """Re-shape verified smoke evidence as the Task08 camera APK's manifest receipt."""
    camera = json.loads(json.dumps(evidence))
    camera["manifest"].update({
        "package": "org.fyld.capturecheck",
        "version_code": 10242,
        "stdout": BADGING.replace("org.fyld.toolchainsmoke", "org.fyld.capturecheck")
        .replace("versionCode='10241'", "versionCode='10242'")
        + "uses-permission: name='android.permission.CAMERA'\n"
          "launchable-activity: name='org.fyld.capture.CameraActivity' label='FYLD Camera Capture'\n",
    })
    camera["camera_profile"] = warm.load_camera_profile(BUILD.parent)
    camera["camera_manifest"] = {
        "permission": "uses-permission: name='android.permission.CAMERA'",
        "launch_activity": "org.fyld.capture.CameraActivity",
    }
    return camera


def test_camera_export_revalidates_and_publishes_camera_receipt(verified, tmp_path, monkeypatch):
    apk, evidence, _ = verified
    camera = _camera_receipt(apk, evidence)
    actual_run = export.subprocess.run

    def camera_badging(args, **kwargs):
        if Path(args[0]).name == "aapt":
            return tool_result(camera["manifest"]["stdout"])
        return actual_run(args, **kwargs)

    monkeypatch.setattr(export.subprocess, "run", camera_badging)

    export.validate_evidence(apk, camera, verifier_dir(evidence))
    published = export.publish_bundle(apk, camera, tmp_path / "offline", "redmi-001",
                                      verifier_dir(evidence))

    assert published == tmp_path / "offline" / "camera_redmi-001"
    saved = json.loads((published / "verification.json").read_text(encoding="utf-8"))
    assert saved == camera
    assert "Camera2 capability checks" in (published / "README.md").read_text(encoding="utf-8")
    assert recipe.sha256(published / apk.name) == recipe.sha256(apk)


def test_camera_export_rejects_smoke_apk_with_forged_camera_receipt(verified):
    apk, evidence, _ = verified
    camera = _camera_receipt(apk, evidence)

    with pytest.raises(ValueError, match="manifest does not match"):
        export.validate_evidence(apk, camera, verifier_dir(evidence))


def test_null_camera_profile_cannot_label_smoke_bundle(verified, tmp_path):
    apk, evidence, _ = verified
    forged = dict(evidence, camera_profile=None)

    with pytest.raises(ValueError, match="profile is malformed"):
        export.publish_bundle(apk, forged, tmp_path / "offline", "forged",
                              verifier_dir(evidence))


def test_export_does_not_run_receipt_supplied_verifier(verified, tmp_path, monkeypatch):
    apk, evidence, _ = verified
    altered = json.loads(json.dumps(evidence))
    untrusted_dir = tmp_path / "untrusted"
    untrusted_dir.mkdir()
    forged_aapt = untrusted_dir / "aapt"
    forged_aapt.write_bytes(b"untrusted executable")
    altered["manifest"]["command"][0] = str(forged_aapt)
    altered["manifest"]["tool_sha256"] = recipe.sha256(forged_aapt)

    def forbid_untrusted_aapt(args, **kwargs):
        if Path(args[0]).name == "apksigner":
            return tool_result(SIGNATURE)
        raise AssertionError("receipt-supplied executable must not run")

    monkeypatch.setattr(export.subprocess, "run", forbid_untrusted_aapt)
    with pytest.raises(ValueError, match="verifier provenance"):
        export.validate_evidence(apk, altered, verifier_dir(evidence))


@pytest.mark.parametrize(("old", "new", "message"), [
    ("uses-permission: name='android.permission.CAMERA'",
     "uses-permission: name='android.permission.CAMERA'\n"
     "uses-permission: name='android.permission.RECORD_AUDIO'", "(?i)manifest"),
    ("org.fyld.capture.CameraActivity", "org.kivy.android.PythonActivity", "(?i)manifest"),
])
def test_camera_export_rejects_tampered_permission_or_activity(
        verified, old, new, message, monkeypatch):
    apk, evidence, _ = verified
    camera = _camera_receipt(apk, evidence)
    actual_manifest = camera["manifest"]["stdout"]
    camera["manifest"]["stdout"] = camera["manifest"]["stdout"].replace(old, new)

    def camera_badging(args, **kwargs):
        if Path(args[0]).name == "aapt":
            return tool_result(actual_manifest)
        return export.subprocess.CompletedProcess(args, 0, SIGNATURE, "")

    monkeypatch.setattr(export.subprocess, "run", camera_badging)

    with pytest.raises(ValueError, match=message):
        export.validate_evidence(apk, camera, verifier_dir(evidence))


@pytest.mark.parametrize("change", [{"status": "passed"}, {"apk_sha256": "0" * 64},
    {"source_sha256": "bad"}, {"signature": {}}, {"manifest": {}}, {"archive": {}},
    {"bytecode": {}}, {"schema_version": 99}])
def test_export_rejects_incomplete_or_unbound_receipts(verified, tmp_path, change):
    apk, evidence, _ = verified
    with pytest.raises(ValueError):
        export.publish_bundle(apk, dict(evidence, **change), tmp_path / "offline", "fixture",
                              verifier_dir(evidence))
    assert not list((tmp_path / "offline").glob("smoke_*"))


@pytest.mark.parametrize(("section", "key", "value", "match"), [
    ("signature", "certificate_sha256", ["00" * 32], "Signature transcript"),
    ("signature", "stdout", "forged transcript", "Signature transcript"),
    ("signature", "stderr", "forged diagnostic", "Signature transcript"),
    ("manifest", "debuggable", False, "Manifest transcript"),
    ("archive", "abis", ["x86_64"], "archive does not match"),
    ("bytecode", "optimize", 1, "embedded source verification"),
    ("bytecode", "filename", "", "embedded source filename"),
    ("signature", "tool_sha256", "missing", "verifier provenance"),
    ("bytecode", "hostpython_sha256", "missing", "source verifier provenance"),
])
def test_export_rejects_tampered_verification_claims(verified, section, key, value, match):
    apk, evidence, _ = verified
    altered = json.loads(json.dumps(evidence))
    altered[section][key] = value
    with pytest.raises(ValueError, match=match):
        export.validate_evidence(apk, altered, verifier_dir(evidence))


@pytest.mark.parametrize("run_id", ["", "../escape", "a/b", "a\\b", "CON", " a", "a."])
def test_export_rejects_unsafe_run_id(verified, tmp_path, run_id):
    apk, evidence, _ = verified
    with pytest.raises(ValueError):
        export.publish_bundle(apk, evidence, tmp_path / "offline", run_id,
                              verifier_dir(evidence))


def test_export_interruption_preserves_prior_bundle(verified, tmp_path, monkeypatch):
    apk, evidence, _ = verified
    output = tmp_path / "offline"
    prior = export.publish_bundle(apk, evidence, output, "prior", verifier_dir(evidence))
    before = (prior / apk.name).read_bytes()

    def interrupt(*args):
        raise OSError("simulated interruption before publication")

    monkeypatch.setattr(export, "_publish", interrupt)
    with pytest.raises(OSError, match="simulated interruption"):
        export.publish_bundle(apk, evidence, output, "interrupted", verifier_dir(evidence))
    assert not (output / "smoke_interrupted").exists()
    assert (prior / apk.name).read_bytes() == before
    assert not (output / ".publish.lock").exists()
    assert list(output.glob(".staging-*"))


def test_export_copy_failure_and_changed_bytes(verified, tmp_path, monkeypatch):
    apk, evidence, _ = verified
    monkeypatch.setattr(export.shutil, "copyfile", lambda src, dst: Path(dst).write_bytes(b"bad"))
    with pytest.raises(ValueError, match="hash"):
        export.publish_bundle(apk, evidence, tmp_path / "offline", "badcopy",
                              verifier_dir(evidence))
    assert not (tmp_path / "offline" / "smoke_badcopy").exists()


def test_export_stale_legacy_lock_does_not_block_recovery(verified, tmp_path):
    apk, evidence, _ = verified
    output = tmp_path / "offline"
    output.mkdir()
    stale_lock = output / ".publish.lock"
    stale_lock.write_text("owner process terminated")
    published = export.publish_bundle(apk, evidence, output, "recovered", verifier_dir(evidence))
    assert published.is_dir()
    assert (published / "verification.json").is_file()
    assert stale_lock.read_text() == "owner process terminated"


def test_export_same_run_race_has_one_complete_winner(verified, tmp_path, monkeypatch):
    apk, evidence, _ = verified
    output = tmp_path / "offline"
    barrier = Barrier(2, timeout=1)
    original_uuid = export.uuid.uuid4

    def synchronized_uuid():
        barrier.wait()
        return original_uuid()

    monkeypatch.setattr(export.uuid, "uuid4", synchronized_uuid)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(export.publish_bundle, apk, evidence, output, "race",
                               verifier_dir(evidence)) for _ in range(2)]
        published, errors = [], []
        for future in futures:
            try:
                published.append(future.result())
            except FileExistsError as error:
                errors.append(error)
    assert len(published) == len(errors) == 1
    assert (output / "smoke_race/verification.json").is_file()


def test_export_cli_reruns_verifiers_before_offline_handoff(verified, tmp_path, monkeypatch, capsys):
    apk, evidence, _ = verified
    source = tmp_path / "main.py"
    source.write_bytes(SOURCE)
    prior = dict(evidence, build={"preflight": {
        "hostpython": str(tmp_path / "hostpython"),
        "build_tools_dir": str(tmp_path / "tools"),
    }})
    receipt = tmp_path / "verification.json"
    receipt.write_text(json.dumps(prior))
    calls = []

    def reverify(*args, **kwargs):
        calls.append((args, kwargs))
        return evidence

    monkeypatch.setattr(export, "verify_apk", reverify)
    monkeypatch.setattr(sys, "argv", ["export.py", str(apk), str(receipt), str(source),
                                       str(tmp_path / "offline"), "cli-run", "--hostpython",
                                       str(tmp_path / "hostpython"), "--build-tools",
                                       str(tmp_path / "tools")])
    export.main()
    target = tmp_path / "offline/smoke_cli-run"
    assert len(calls) == 1
    assert calls[0][0][0:3] == (apk, evidence["settings"], source)
    assert calls[0][1] == {"camera_profile": None}
    assert target.is_dir()
    assert recipe.sha256(target / apk.name) == recipe.sha256(apk)
    assert str(target) in capsys.readouterr().out


def test_wsl_windows_mount_uses_encoded_no_replace_directory_move(monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if args[0] == "wslpath":
            return CompletedProcess(args, 0, "C:\\work\\bundle with space\n", "")
        script = base64.b64decode(args[-1]).decode("utf-16le")
        assert "[System.IO.Directory]::Move" in script
        assert "bundle with space" in script
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(export.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(export.subprocess, "run", run)
    export._publish_windows_mount(Path("/mnt/c/work/staging"), Path("/mnt/c/work/bundle"))
    assert [args[0] for args in calls] == ["wslpath", "wslpath", "powershell.exe"]


def test_wsl_windows_mount_reports_destination_race(monkeypatch):
    results = iter([
        CompletedProcess([], 0, "C:\\work\\stage\n", ""),
        CompletedProcess([], 0, "C:\\work\\bundle\n", ""),
        CompletedProcess([], 1, "", "destination exists"),
    ])
    monkeypatch.setattr(export.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(export.subprocess, "run", lambda *args, **kwargs: next(results))
    monkeypatch.setattr(Path, "exists", lambda _: True)
    with pytest.raises(FileExistsError, match="already exists"):
        export._publish_windows_mount(Path("/mnt/c/work/stage"), Path("/mnt/c/work/bundle"))
