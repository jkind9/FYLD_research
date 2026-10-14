"""Stage the capture build in the repository's single APK handoff folder."""

import argparse
from pathlib import Path

from export import publish_capture


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3] / "mobile_deployments"
    print(publish_capture(args.apk, root))


if __name__ == "__main__":
    main()
