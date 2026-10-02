"""Pin reference clones; no blind pulls, installs or checkpoint downloads."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def git(arguments: list[str], cwd: Path | None = None) -> str:
    """Run Git as an argument list and propagate errors with stderr."""
    process = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.strip())
    return process.stdout.strip()


def fetch_repository(record: dict, directory: Path, allow_update: bool = False) -> None:
    """Verify existing origin, clean tree and revision before any checkout/update."""
    created = not directory.exists()
    if created:
        directory.parent.mkdir(parents=True, exist_ok=True)
        git(
            [
                "clone",
                "--depth",
                "1",
                "--branch",
                record["ref"],
                record["url"],
                str(directory),
            ]
        )
    else:
        if not (directory / ".git").exists():
            raise ValueError(f"Refusing existing non-repository directory: {directory}")
        origin = git(["remote", "get-url", "origin"], directory)
        if origin.rstrip("/") != record["url"].rstrip("/"):
            raise ValueError(f"Remote mismatch: {directory}")
        if git(["status", "--porcelain", "--untracked-files=all"], directory):
            raise ValueError(f"Local changes present; refusing checkout: {directory}")
    selected = record["commit"]
    previous = git(["rev-parse", "HEAD"], directory)
    resolved = git(["rev-parse", f"{selected}^{{commit}}"], directory)
    if resolved != selected:
        raise ValueError(
            "Pinned SHA must resolve to an actual commit, not an annotated tag"
        )
    if not created and previous != selected and not allow_update:
        raise ValueError(
            f"Existing revision {previous} differs from {selected}; inspect before enabling update"
        )
    if allow_update:
        desired = git(["ls-remote", record["url"], "HEAD"]).split()[0]
        if desired != selected:
            git(["fetch", "--depth", "1", "origin", desired], directory)
            record["update_history"].append(
                {"old": selected, "new": desired, "utc": datetime.now(UTC).isoformat()}
            )
            selected = desired
            record["commit"], record["ref"] = desired, desired
    git(["checkout", "--detach", selected], directory)
    if record["submodules_required_for_reference_checkout"]:
        git(["submodule", "update", "--init", "--recursive"], directory)
    if git(["rev-parse", "HEAD"], directory) != selected:
        raise ValueError("Checkout revision mismatch")
    record["setup_status"] = (
        "reference clone checked out at pinned SHA; binaries not built/installed"
    )
    record["resolved_commit"] = selected
    record["fetched_utc"] = datetime.now(UTC).isoformat()
    print(f"{record['name']}: {selected}; reference only, not executed", flush=True)


def main() -> None:
    """Default at most two deliberate reference checkouts; explicit update switch."""
    allow_update = False
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "research" / "repositories.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(manifest["selected"]) > 2:
        raise ValueError("Default fetch budget permits at most two repositories")
    for record in manifest["selected"]:
        try:
            fetch_repository(
                record, root / "third_party" / record["name"], allow_update
            )
        except (ValueError, RuntimeError, subprocess.SubprocessError) as error:
            record["last_error"] = str(error)
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            raise
        record.pop("last_error", None)
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
