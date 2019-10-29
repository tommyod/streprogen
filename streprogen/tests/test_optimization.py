#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from streprogen.optimization import optimize_sets
from streprogen.modeling import (
    reps_to_intensity,
    reps_to_intensity_relaxed,
    reps_to_intensity_tight,
)
import itertools
import pytest


@pytest.mark.parametrize(
    "reps_to_intensity_func, reps_goal, intensities_goal",
    list(
        itertools.product(
            [reps_to_intensity, reps_to_intensity_relaxed, reps_to_intensity_tight],
            [15, 20, 25, 30, 35],
            [0.70, 0.75, 0.80, 0.85, 0.90],
        )
    ),
)
def test_optimize_sets(reps_to_intensity_func, reps_goal, intensities_goal):
    """For common settings, check that the optimization returns good results."""

    reps = list(range(1, 12 + 1))
    intensities = [reps_to_intensity_func(r) / 100 for r in reps]

    x, data = optimize_sets(
        tuple(reps), tuple(intensities), reps_goal, intensities_goal
    )
    assert abs(data["reps"] - reps_goal) <= 2
    assert abs(data["intensity"] - intensities_goal) < 0.01


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
