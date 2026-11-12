"""Inherited Task24 pins and input hashing; no dependency acquisition."""

import hashlib
import json
from pathlib import Path

PINS = {
    "schema_version": 1,
    "ubuntu": "24.04.4",
    "host_python": "3.12.3",
    "java": "17.0.20.1",
    "p4a": "2026.05.09",
    "p4a_commit": "58d21141f17c889bf8585f5665921d72028f8831",
    "p4a_wheel_sha256": "79a58606a78ed3cec1aba110876a414d4aa988f082385d68393e208d009e1e94",
    "android_api": 36,
    "build_tools": "35.0.0",
    "platform_tools": "37.0.1",
    "ndk": "28.2.13676358",
    "ndk_api": 24,
    "android_python": "3.14.2",
    "gradle": "8.14.3",
    "gradle_sha256": "ed1a8d686605fd7c23bdf62c7fc7add1c5b23b2bbc3721e661934ef4a4911d7c",
    "android_gradle_plugin": "8.11.0",
    "bootstrap": "sdl2",
    "abi": "arm64-v8a",
    "dist_name": "unnamed_dist_1",
    "warm_recipes": ["hostpython3", "libffi", "openssl", "sdl2_image", "sdl2_mixer",
                     "sdl2_ttf", "sqlite3", "python3", "sdl2"],
    "package": "org.fyld.toolchainsmoke",
    "name": "FYLDToolchainSmoke",
    "version": "0.1",
    "version_code": 10241,
    "min_sdk": 24,
    "source_sha256": "58a44735ffdfa6b14977516ad6e6e642d477999cd361537028f2d6b99e07ad68",
    "native_source_sha256": "23cf718c49184de97b2e966b9426178d82ba04d4f3b591c7ed5fcb6b623f7afb",
    "predecessor_apk_sha256": "b54aee1b73cb1e80539e61e57fa6881fb47c5007ddcd9870df61f9751089fdcf",
}


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject ambiguous JSON rather than retaining the last repeated field."""
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate JSON fields")
    return dict(pairs)


def validate_settings(settings: dict) -> dict:
    if not isinstance(settings, dict) or set(settings) != set(PINS):
        raise ValueError("Toolchain settings must contain exactly the inherited pin fields")
    for key, expected in PINS.items():
        actual = settings[key]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"Inherited toolchain pin mismatch: {key}")
    return {key: list(value) if isinstance(value, list) else value for key, value in settings.items()}


def load_settings(path: Path) -> dict:
    settings = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    return validate_settings(settings)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
