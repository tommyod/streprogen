#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from streprogen.optimization import RepSchemeOptimizer
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
            list(range(15, 35 + 1, 1)),
            list(range(70, 90 + 1, 1)),
        )
    ),
)
def test_repscheme_optimizer(reps_to_intensity_func, reps_goal, intensities_goal):
    """For common settings, check that the optimization returns good results."""

    # Prepare data
    reps = tuple(range(1, 12 + 1))
    intensities = tuple(reps_to_intensity_func(r) for r in reps)

    # Default values make sense to use here
    optimizer = RepSchemeOptimizer()

    scheme = optimizer(sets=reps, intensities=intensities, reps_goal=reps_goal, intensity_goal=intensities_goal)
    assert scheme == sorted(scheme, reverse=True)

    intensities = list(map(reps_to_intensity_func, scheme))

    reps = sum(scheme)
    intensity = sum(r * i for r, i in zip(scheme, intensities)) / reps

    assert abs(reps - reps_goal) <= 3
    assert abs(intensity - intensities_goal) <= 3


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
