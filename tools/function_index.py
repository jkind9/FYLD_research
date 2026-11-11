"""Write the function index in README.md: every public function and class in sitescan/ and apps/.

    python -B -m tools.function_index          rewrite the index between the markers in README.md
    python -B -m tools.function_index --check  exit 1 if the index is out of date

Each row names the function, its arguments, the first line of its docstring and a link to its definition.
"""

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PACKAGES = ("sitescan", "apps")
START = "<!-- function-index:start -->"
END = "<!-- function-index:end -->"


def arguments(node: ast.FunctionDef) -> str:
    """Argument names as a caller writes them; keyword-only ones after a bare star."""
    names = [a.arg for a in node.args.posonlyargs + node.args.args if a.arg not in ("self", "cls")]
    if node.args.vararg:
        names.append(f"*{node.args.vararg.arg}")
    elif node.args.kwonlyargs:
        names.append("*")
    names += [a.arg for a in node.args.kwonlyargs]
    return ", ".join(names)


def constructor(node: ast.ClassDef) -> str:
    """What creating one takes: the __init__ arguments, else the annotated fields of a dataclass."""
    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            return arguments(item)
    return ", ".join(item.target.id for item in node.body if isinstance(item, ast.AnnAssign))


def summary(node) -> str:
    doc = ast.get_docstring(node)
    return doc.strip().splitlines()[0].replace("|", "\\|") if doc else ""


def public(name: str) -> bool:
    return not name.startswith("_")


def rows(path: Path) -> list[str]:
    """One table row per public top-level function and class, then each class's public methods."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    link = path.relative_to(ROOT).as_posix()
    found = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and public(node.name):
            found.append(f"| [`{node.name}({arguments(node)})`]({link}#L{node.lineno}) | {summary(node)} |")
        elif isinstance(node, ast.ClassDef) and public(node.name):
            found.append(f"| [`{node.name}({constructor(node)})`]({link}#L{node.lineno}) (class) | {summary(node)} |")
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and public(item.name):
                    found.append(f"| [`{node.name}.{item.name}({arguments(item)})`]({link}#L{item.lineno}) | {summary(item)} |")
    return found


def index() -> str:
    """Markdown tables, one per module that defines public code."""
    sections = []
    for package in PACKAGES:
        for path in sorted((ROOT / package).rglob("*.py")):
            found = [] if "tests" in path.parts else rows(path)
            if found:
                module = path.relative_to(ROOT).with_suffix("").as_posix().replace("/", ".")
                sections.append(f"**`{module}`**\n\n| Function | What it does |\n|---|---|\n" + "\n".join(found))
    return "\n\n".join(sections)


def with_index(text: str) -> str:
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n\n{index()}\n\n{END}{tail}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report an out-of-date index instead of writing it")
    args = parser.parse_args(argv)
    text = README.read_text(encoding="utf-8")
    updated = with_index(text)
    if args.check:
        if updated != text:
            print("README.md function index is out of date: run python -B -m tools.function_index", file=sys.stderr)
            return 1
        return 0
    README.write_text(updated, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
