"""Download only the verified small TUM sequence; change variables in main deliberately."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fyld_scene_mapping.acquisition import download, extract_tar, write_metadata


def main() -> None:
    """Download with 2 GB archive and separate 2 GB expanded-data limits."""
    total_budget_bytes = 2_000_000_000
    expanded_budget_bytes = 2_000_000_000
    sequence = "rgbd_dataset_freiburg1_xyz"
    expected_bytes = 448_204_271  # Official HEAD verified 2026-10-01.
    source_url = f"https://cvg.cit.tum.de/rgbd/dataset/freiburg1/{sequence}.tgz"
    archive = ROOT / "data" / "archives" / f"{sequence}.tgz"
    provenance = download(source_url, archive, total_budget_bytes, expected_bytes)
    destination = ROOT / "data" / "tum"
    ready = destination / sequence / "provenance.json"
    if ready.exists():
        previous = json.loads(ready.read_text(encoding="utf-8"))
        if previous["local_sha256"] != provenance["local_sha256"]:
            raise ValueError("Extraction/cache hashes differ")
        print(f"Extraction already complete: {ready.parent}")
        return
    destination.mkdir(parents=True, exist_ok=True)
    if ready.parent.exists():
        raise FileExistsError(
            f"Sequence exists without completion provenance: {ready.parent}. Inspect or move it aside; it will not be overwritten."
        )
    # Publish a sequence only after extraction and provenance are complete.
    with tempfile.TemporaryDirectory(prefix="extract-", dir=destination) as temporary:
        staging = Path(temporary).resolve()
        if not staging.is_relative_to(destination.resolve()):
            raise ValueError("Extraction staging directory escaped destination")
        extract_tar(archive, staging, expanded_budget_bytes)
        staged_sequence = staging / sequence
        write_metadata(staged_sequence / "provenance.json", provenance)
        staged_sequence.rename(ready.parent)
    print(f"Ready: {ready.parent}")


if __name__ == "__main__":
    main()
