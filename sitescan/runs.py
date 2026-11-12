"""Where a run writes its outputs, and the run.json that records what made them.

Every run writes one folder, `outputs/<recording>/<tool>/<yyyymmdd-hhmm>_<label>/`. The recording is a
short name from recordings.toml; the tool is what ran (room, live, compare, ...); the label is one to four
lowercase words joined by hyphens saying what is different. run.json in the folder holds the command,
every setting, the options typed on the command line, the git commit with any uncommitted code changes
(saved beside it as source.diff), the runs it read, and, once finished, its status and headline numbers.
"""

import hashlib
import json
import re
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUTS = Path("outputs")
RECORDINGS = REPO / "recordings.toml"
LABEL = re.compile(r"[a-z0-9]+(-[a-z0-9]+){0,3}")
MAX_RUN_PATH = 80  # characters under the outputs folder, so Windows paths stay short
CODE = ("*.py", "*.js", "*.toml")


def recordings(path: Path = RECORDINGS) -> dict[str, dict]:
    """Recording name -> {"path": folder relative to the repository, "private": bool}."""
    return tomllib.loads(path.read_text(encoding="utf-8"))


def session_path(name: str) -> Path:
    """The recording folder for a recording name, or the argument itself when it is a path."""
    known = recordings()
    return REPO / known[name]["path"] if name in known else Path(name)


def recording_name(folder: Path) -> str:
    """The recording's short name, or its folder name when recordings.toml does not list it."""
    for name, entry in recordings().items():
        if (REPO / entry["path"]).resolve() == Path(folder).resolve():
            return name
    return Path(folder).name


def _git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=REPO, capture_output=True, text=True, check=True).stdout


def code_state(folder: Path) -> dict | None:
    """The commit, whether code differs from it, and the untracked code files; writes source.diff if it does."""
    try:
        commit = _git("rev-parse", "HEAD").strip()
        diff = _git("diff", "HEAD", "--", *CODE)
        untracked = _git("ls-files", "--others", "--exclude-standard", "--", *CODE).split()
    except (OSError, subprocess.CalledProcessError):
        return None
    if diff:
        (folder / "source.diff").write_text(diff, encoding="utf-8", newline="\n")
    return {"commit": commit, "changed": bool(diff), "untracked": {
        name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in untracked}}


def typed_options(argv: list[str], values: dict) -> dict:
    """The options typed on the command line with their parsed values, except the ones that place the run."""
    names = {token[2:].split("=")[0].replace("-", "_") for token in argv if token.startswith("--")}
    return {name: values[name] for name in sorted(names - {"session", "label", "root"}) if name in values}


def new_run(recording: str, tool: str, label: str, settings: dict, typed: dict | None = None, *,
            root: Path = OUTPUTS, inputs: tuple = ()) -> Path:
    """Make the run's folder and write run.json with status "running"; refuses a folder that exists."""
    if not LABEL.fullmatch(label):
        raise ValueError(f"label {label!r}: use one to four lowercase words joined by hyphens, e.g. sweep-jump125")
    started = datetime.now().astimezone()
    relative = Path(recording) / tool / f"{started:%Y%m%d-%H%M}_{label}"
    if len(relative.as_posix()) > MAX_RUN_PATH:
        raise ValueError(f"{relative.as_posix()} is over {MAX_RUN_PATH} characters; shorten the label")
    folder = Path(root) / relative
    folder.mkdir(parents=True)
    known = recordings().get(recording)
    record = {"recording": recording, "tool": tool, "label": label, "status": "running",
              "started": started.isoformat(timespec="seconds"), "command": " ".join(sys.argv),
              "private": True if known is None else known["private"], "typed": typed or {},
              "settings": settings, "inputs": [str(path) for path in inputs], "code": code_state(folder)}
    _write(folder, record)
    return folder


def finish_run(folder: Path, numbers: dict | None = None, status: str = "complete") -> None:
    """Record how the run ended and its headline numbers."""
    record = json.loads((Path(folder) / "run.json").read_text(encoding="utf-8"))
    record |= {"status": status, "finished": datetime.now().astimezone().isoformat(timespec="seconds"),
               "numbers": numbers or {}}
    _write(Path(folder), record)


def _write(folder: Path, record: dict) -> None:
    text = json.dumps(record, indent=1, default=str) + "\n"
    (folder / "run.json").write_text(text, encoding="utf-8", newline="\n")
