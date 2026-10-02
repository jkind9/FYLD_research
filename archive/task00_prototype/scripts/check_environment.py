"""Record host, dependency versions and an actual optional CUDA kernel test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fyld_scene_mapping.environment import main

if __name__ == "__main__":
    main()
