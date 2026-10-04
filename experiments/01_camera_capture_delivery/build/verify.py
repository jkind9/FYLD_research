"""Verify actual APK bytes using installed Android tools and target hostpython."""

import gzip
import io
import json
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from recipe import sha256, unique_object, validate_settings

ABI_ELF = {
    "armeabi-v7a": (1, 40, "ELF32 ARM"),
    "arm64-v8a": (2, 183, "ELF64 AArch64"),
    "x86": (1, 3, "ELF32 x86"),
    "x86_64": (2, 62, "ELF64 x86-64"),
}
PYTHON_BUNDLE_LIMIT = 64 * 1024 * 1024


def _record_elf(name: str, header: bytes, abi: str, native_elf: dict[str, str]) -> None:
    elf_class, machine, description = ABI_ELF[abi]
    if (len(header) != 20 or header[:4] != b"\x7fELF" or header[4] != elf_class
            or header[5] != 1 or int.from_bytes(header[18:20], "little") != machine):
        raise ValueError(f"APK native library ELF architecture does not match {abi}: {name}")
    native_elf[name] = description


def _inspect_python_bundle(name: str, payload: bytes, abi: str,
                           native_elf: dict[str, str]) -> dict:
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as compressed:
            unpacked = compressed.read(PYTHON_BUNDLE_LIMIT + 1)
        if len(unpacked) > PYTHON_BUNDLE_LIMIT:
            raise ValueError("Compressed Python bundle exceeds the verification size limit")
        with tarfile.open(fileobj=io.BytesIO(unpacked), mode="r:") as bundle:
            members = bundle.getmembers()
            names = [member.name for member in members]
            if not members or len(names) != len(set(names)):
                raise ValueError("Empty or duplicate compressed Python bundle entries")
            libraries = []
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts or "\\" in member.name:
                    raise ValueError("Unsafe compressed Python bundle entry")
                if not (member.isfile() or member.isdir()):
                    raise ValueError("Links and special compressed Python bundle entries are unsupported")
                if member.isfile() and member.name.endswith(".so"):
                    stream = bundle.extractfile(member)
                    if stream is None:
                        raise ValueError(f"Cannot read bundled native library: {member.name}")
                    with stream:
                        header = stream.read(20)
                    library = f"{name}!{member.name}"
                    _record_elf(library, header, abi, native_elf)
                    libraries.append(member.name)
            if not libraries:
                raise ValueError("Compressed Python bundle contains no native libraries")
    except (gzip.BadGzipFile, EOFError, OSError, tarfile.TarError) as error:
        raise ValueError("Invalid compressed Python bundle") from error
    return {"format": "gzip-compressed tar", "member_count": len(members),
            "native_libraries": libraries}


def parse_signature(result: subprocess.CompletedProcess) -> dict:
    output = result.stdout
    if result.returncode != 0 or not isinstance(output, str):
        raise ValueError("APK signature verifier failed")
    if output.splitlines().count("Verifies") != 1 or "DOES NOT VERIFY" in output:
        raise ValueError("Malformed or failed APK signature verification")
    certificates = re.findall(r"^Signer #[1-9]\d* certificate SHA-256 digest: ([0-9a-fA-F]{64})$",
                              output, re.MULTILINE)
    digest_lines = [line for line in output.splitlines() if "certificate SHA-256 digest:" in line]
    schemes = re.findall(r"^Verified using (v\d(?:\.\d)?).*: (true|false)$", output, re.MULTILINE)
    if not certificates or len(certificates) != len(digest_lines) or not schemes:
        raise ValueError("Signature verification lacks certificates or signature schemes")
    if len(schemes) != len(dict(schemes)) or not any(value == "true" for _, value in schemes):
        raise ValueError("No verified APK signing scheme")
    return {"certificate_sha256": [value.lower() for value in certificates],
            "schemes": dict(schemes), "stdout": output, "stderr": result.stderr}


def _one(pattern: str, output: str, label: str) -> str:
    matches = re.findall(pattern, output, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Missing or ambiguous APK manifest {label}")
    return matches[0]


def parse_badging(result: subprocess.CompletedProcess, settings: dict) -> dict:
    if result.returncode != 0 or not isinstance(result.stdout, str):
        raise ValueError("APK manifest tool failed")
    output = result.stdout
    package_line = _one(r"^package: (.*)$", output, "package")
    package = _one(r"(?:^| )name='([^']*)'", package_line, "package name")
    version_name = _one(r"(?:^| )versionName='([^']*)'", package_line, "version name")
    version_code = _one(r"(?:^| )versionCode='([0-9]+)'", package_line, "version code")
    minimum = _one(r"^sdkVersion:'([0-9]+)'$", output, "minimum API")
    target = _one(r"^targetSdkVersion:'([0-9]+)'$", output, "target API")
    native_line = _one(r"^native-code: (.*)$", output, "native ABI")
    abis = re.findall(r"'([^']+)'", native_line)
    if native_line.strip() != " ".join(f"'{abi}'" for abi in abis):
        raise ValueError("Malformed native ABI declaration")
    manifest = {"package": package, "version": version_name, "version_code": int(version_code),
                "min_sdk": int(minimum), "target_api": int(target), "abis": abis,
                "debuggable": output.splitlines().count("application-debuggable") == 1}
    expected = {"package": settings["package"], "version": settings["version"],
                "version_code": settings["version_code"], "min_sdk": settings["min_sdk"],
                "target_api": settings["android_api"], "abis": [settings["abi"]], "debuggable": True}
    if manifest != expected:
        raise ValueError("APK manifest does not match inherited smoke build settings")
    return {**manifest, "stdout": output, "stderr": result.stderr}


def parse_camera_declarations(result: subprocess.CompletedProcess, profile: dict) -> dict:
    if result.returncode != 0 or not isinstance(result.stdout, str):
        raise ValueError("Camera APK manifest tool failed")
    output = result.stdout
    permission_lines = [line for line in output.splitlines()
                        if re.match(r"^uses-permission(?:-sdk-\d+)?:", line)]
    declarations = []
    for line in permission_lines:
        match = re.fullmatch(r"(uses-permission(?:-sdk-\d+)?): name='([^']+)'", line)
        if match is None:
            raise ValueError("Camera APK permissions do not match the reviewed package profile")
        declarations.append((match.group(1), match.group(2)))
    expected = [("uses-permission", permission) for permission in profile["permissions"]]
    if declarations != expected:
        raise ValueError("Camera APK permissions do not match the reviewed package profile")
    permission = "uses-permission: name='android.permission.CAMERA'"
    activities = re.findall(r"^launchable-activity: name='([^']+)'", output, re.MULTILINE)
    if activities != [profile["activity_class_name"]]:
        raise ValueError("Camera APK launch activity does not match its pinned profile")
    return {"permission": permission, "launch_activity": activities[0]}


def inspect_archive(apk: Path, abi: str) -> dict:
    if abi not in ABI_ELF:
        raise ValueError(f"Unsupported Android ABI: {abi}")
    try:
        with zipfile.ZipFile(apk) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate APK ZIP entries")
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
                    raise ValueError("Unsafe APK ZIP entry")
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("APK ZIP symlink is unsupported")
            native = sorted(name for name in names if name.startswith("lib/") and name.endswith(".so"))
            abis = sorted({PurePosixPath(name).parts[1] for name in native})
            if not native or abis != [abi] or any(len(PurePosixPath(name).parts) != 3 for name in native):
                raise ValueError("Missing or mismatched APK native libraries")
            native_elf = {}
            compressed_bundles = {}
            for name in native:
                with archive.open(name) as library:
                    header = library.read(20)
                if name == f"lib/{abi}/libpybundle.so":
                    if not header.startswith(b"\x1f\x8b"):
                        raise ValueError("Missing compressed Python bundle")
                    compressed_bundles[name] = _inspect_python_bundle(
                        name, archive.read(name), abi, native_elf)
                else:
                    _record_elf(name, header, abi, native_elf)
            if f"lib/{abi}/libpybundle.so" not in compressed_bundles:
                raise ValueError("Missing compressed Python bundle")
            if names.count("assets/private.tar") != 1:
                raise ValueError("Missing embedded first-party source archive")
            if archive.getinfo("assets/private.tar").file_size > 16 * 1024 * 1024:
                raise ValueError("Private archive exceeds smoke verification size limit")
            failed = archive.testzip()
            if failed:
                raise ValueError(f"APK ZIP checksum failure: {failed}")
    except (zipfile.BadZipFile, EOFError, OSError) as error:
        raise ValueError("Invalid APK archive") from error
    return {"abis": abis, "native_libraries": sorted(native_elf), "native_elf": native_elf,
            "compressed_python_bundles": compressed_bundles,
            "private_archive": "assets/private.tar"}


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=False, capture_output=True, text=True, shell=False,
                          timeout=120, encoding="utf-8")


def verify_apk(apk: Path, settings: dict, source: Path, hostpython: Path,
               build_tools: Path, expected_filename: str,
               camera_profile: dict | None = None) -> dict:
    settings = validate_settings(settings)
    apk, source = Path(apk), Path(source)
    if apk.is_symlink() or source.is_symlink() or not apk.is_file() or not source.is_file():
        raise ValueError("APK and source must be regular non-symlink inputs")
    original_hash = sha256(apk)
    source_hash = sha256(source)
    if source_hash != settings["source_sha256"]:
        raise ValueError("Recovered source hash mismatch")
    tools = {name: Path(build_tools) / name for name in ("apksigner", "aapt")}
    if not Path(hostpython).is_file() or not all(path.is_file() for path in tools.values()):
        raise ValueError("Missing installed APK verification prerequisite")
    signature_command = [str(tools["apksigner"]), "verify", "--verbose", "--print-certs", str(apk)]
    manifest_command = [str(tools["aapt"]), "dump", "badging", str(apk)]
    signature = {**parse_signature(_run(signature_command)), "command": signature_command,
                 "tool_sha256": sha256(tools["apksigner"])}
    expected_settings = dict(settings)
    if camera_profile is not None:
        expected_settings.update({"package": camera_profile["package"], "name": camera_profile["name"],
                                  "version": camera_profile["version"],
                                  "version_code": camera_profile["version_code"]})
    manifest_result = _run(manifest_command)
    manifest = {**parse_badging(manifest_result, expected_settings), "command": manifest_command,
                "tool_sha256": sha256(tools["aapt"])}
    camera = parse_camera_declarations(manifest_result, camera_profile) if camera_profile else None
    archive = inspect_archive(apk, settings["abi"])
    bytecode_command = [str(hostpython), str(Path(__file__).with_name("verify_bytecode.py")),
                        str(apk), str(source), expected_filename]
    bytecode_result = _run(bytecode_command)
    if bytecode_result.returncode != 0:
        raise ValueError(f"Embedded source verifier failed: {bytecode_result.stderr}")
    bytecode = json.loads(bytecode_result.stdout, object_pairs_hook=unique_object)
    if not isinstance(bytecode, dict) or any(bytecode.get(key) != expected for key, expected in
        (("status", "verified"), ("source_sha256", source_hash),
         ("python_version", settings["android_python"]), ("filename", expected_filename))):
        raise ValueError("Malformed embedded source verification result")
    if sha256(apk) != original_hash or sha256(source) != source_hash:
        raise ValueError("APK or source changed during verification")
    return {"schema_version": 1, "status": "verified", "apk_sha256": original_hash,
            "source_sha256": source_hash, "settings": settings, "signature": signature,
            "manifest": manifest, "archive": archive,
            **({"camera_profile": camera_profile, "camera_manifest": camera}
               if camera is not None else {}),
            "bytecode": {**bytecode, "command": bytecode_command,
                         "stdout": bytecode_result.stdout, "stderr": bytecode_result.stderr,
                         "hostpython_sha256": sha256(hostpython)}}
