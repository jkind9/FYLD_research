"""Fused learned depth against ARCore's tracked points, split by ARCore depth support and distance."""

import numpy as np

from research.evaluation.depth_check import summarise


def test_summary_splits_by_support_and_distance():
    tracked = np.array([0.5, 0.5, 3.5, 3.5])
    learned = np.array([0.5, 0.55, 2.8, 3.5])
    supported = np.array([True, True, False, True])
    by = {(r["supported"], r["from_m"]): r for r in summarise(learned, tracked, supported, bins=(0, 1, 4))}
    assert by[(True, 0)]["count"] == 2 and np.isclose(by[(True, 0)]["median_ratio"], 1.05)
    assert np.isclose(by[(False, 1)]["median_ratio"], 0.8) and np.isclose(by[(True, 1)]["median_ratio"], 1.0)
    assert (False, 0) not in by  # empty groups are left out
