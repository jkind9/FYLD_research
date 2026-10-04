"""Publish one bounded integrated replay using the accepted YOLO26x checkpoint."""

from __future__ import annotations

from . import generation
from .generation import ROOT, execute

HYPERPARAMETERS = {**generation.HYPERPARAMETERS}


def main() -> None:
    path = execute(ROOT)
    print(path)


if __name__ == "__main__":
    main()
