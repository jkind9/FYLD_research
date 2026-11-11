"""The README function index lists public code and matches the code as it is now."""

import ast

from tools import function_index


def test_rows_list_public_functions_classes_and_methods(tmp_path, monkeypatch):
    module = tmp_path / "pkg" / "stage.py"
    module.parent.mkdir()
    module.write_text(
        'def fit(model, valid, *, minimum=50):\n    """One scale.\n\n    More text."""\n\n\n'
        "def _helper():\n    pass\n\n\n"
        'class Track:\n    """Objects so far."""\n\n    def __init__(self, distance):\n        pass\n\n'
        '    def counts(self):\n        """By label."""\n\n    def _private(self):\n        pass\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(function_index, "ROOT", tmp_path)
    assert function_index.rows(module) == [
        "| [`fit(model, valid, *, minimum)`](pkg/stage.py#L1) | One scale. |",
        "| [`Track(distance)`](pkg/stage.py#L11) (class) | Objects so far. |",
        "| [`Track.counts()`](pkg/stage.py#L17) | By label. |",
    ]
    assert function_index.arguments(ast.parse("def f(a, *rest, b): pass").body[0]) == "a, *rest, b"
    record = ast.parse("class Settings:\n    far_m: float = 4.0\n    voxel_m: float = 0.02\n").body[0]
    assert function_index.constructor(record) == "far_m, voxel_m"


def test_readme_index_is_current():
    assert function_index.main(["--check"]) == 0
