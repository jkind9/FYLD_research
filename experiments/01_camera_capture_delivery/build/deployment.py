"""Stage the capture build in the repository's single APK handoff folder."""

import argparse
import re
import subprocess
from pathlib import Path

from export import publish_capture


def apk_version(apk: Path, aapt: Path) -> str:
    badging = subprocess.check_output([str(aapt), "dump", "badging", str(apk)], text=True)
    match = re.search(r"versionName='([^']+)'", badging)
    if match is None:
        raise ValueError("APK has no versionName")
    return match[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--aapt", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3] / "mobile_deployments"
    print(publish_capture(args.apk, root, apk_version(args.apk, args.aapt)))


if __name__ == "__main__":
    main()
