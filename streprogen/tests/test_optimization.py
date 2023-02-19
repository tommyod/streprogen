#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from streprogen.optimization import RepSchemeOptimizer, RepSchemeGenerator
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
            list(range(10, 35 + 1, 2)),
            list(range(70, 95 + 1, 2)),
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
    assert scheme

    intensities = list(map(reps_to_intensity_func, scheme))

    reps = sum(scheme)
    intensity = sum(r * i for r, i in zip(scheme, intensities)) / reps

    assert abs(reps - reps_goal) <= 3
    assert abs(intensity - intensities_goal) <= 3.5


@pytest.mark.parametrize("reps_slack", [0, 1, 2, 3, 4])
def test_repscheme_generator_reps_slack(reps_slack):
    generator = RepSchemeGenerator(reps_slack=reps_slack)
    sets = [3, 4, 5, 6, 7, 8]
    for reps_goal in [15, 20, 25, 30]:
        for scheme in generator.generate(sets=sets, reps_goal=reps_goal):
            assert scheme
            assert abs(sum(scheme) - reps_goal) <= reps_slack


@pytest.mark.parametrize("max_unique", [1, 2, 3, 4])
def test_repscheme_generator_max_unique(max_unique):
    generator = RepSchemeGenerator(max_unique=max_unique)
    sets = [3, 4, 5, 6, 7, 8]
    for reps_goal in [15, 20, 25, 30]:
        for scheme in generator.generate(sets=sets, reps_goal=reps_goal):
            assert scheme
            assert len(set(scheme)) <= max_unique


@pytest.mark.parametrize("max_diff", [0, 1, 2, 3, 4])
def test_repscheme_generator_max_diff(max_diff):
    generator = RepSchemeGenerator(max_diff=max_diff)
    sets = [3, 4, 5, 6, 7, 8]
    for reps_goal in [15, 20, 25, 30]:
        for scheme in generator.generate(sets=sets, reps_goal=reps_goal):
            assert scheme
            if len(scheme) < 2:
                continue
            for s_j, s_i in zip(scheme[1:], scheme):
                assert s_j >= s_i
                assert s_j - s_i <= max_diff


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
