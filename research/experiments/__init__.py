"""Trials and their evidence, outside the product.

Source files pinned by hash in runs made before 12 November 2026 import this package by its
old top-level name, ``experiments``. The alias keeps those files byte-identical and importable.
"""

import sys

sys.modules.setdefault("experiments", sys.modules[__name__])
