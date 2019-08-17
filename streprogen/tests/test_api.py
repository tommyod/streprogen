#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the API. The API should be considered fixed in future releases and should
be equal for every implementation. Therefore it's important to have unit tests
for the API.
"""

import pytest
from streprogen import Program, Day, DynamicExercise, StaticExercise


def test_verbose_api():
    """The oldest, most verbose API."""

    def curl_func(week):
        return "{} x 10".format(week)

    # Create a 4-week program
    program = Program("My first program!", duration=8)

    # Create some dynamic and static exercises
    bench = DynamicExercise("Bench press", 60, 80)
    squats = DynamicExercise("Squats", 80, 95)
    curls = StaticExercise("Curls", curl_func)

    day = Day()
    day.add_exercises(bench, squats, curls)

    assert len(day.dynamic_exercises) == 2

    # Add day(s) to program and render it
    program.add_days(day)

    assert len(program.days) == 1

    assert not program._rendered
    program.render()
    assert program._rendered


def test_general_api():
    """The slightly more easy API."""

    def curl_func(week):
        return "{} x 10".format(week)

    # Create a 4-week program
    program = Program("My first program!", duration=8)

    # Create some dynamic and static exercises
    bench = DynamicExercise("Bench press", 60, 80)
    squats = DynamicExercise("Squats", 80, 95)
    curls = StaticExercise("Curls", curl_func)
    day = Day(exercises=[bench, squats, curls])

    assert len(day.dynamic_exercises) == 2

    # Add day(s) to program and render it
    program.add_days(day)

    assert len(program.days) == 1

    assert not program._rendered
    program.render()
    assert program._rendered


def test_decorator_api():
    """The new API."""

    def curl_func(week):
        return "{} x 10".format(week)

    # Create a 4-week program
    program = Program("My first program!", duration=8)

    with program.Day():

        DynamicExercise("Bench press", 60, 80)
        DynamicExercise("Squats", 80, 95)
        StaticExercise("Curls", curl_func)

    assert len(program.days) == 1

    assert not program._rendered
    program.render()
    assert program._rendered


# =============================================================================
#
#
# import numpy as np
# from KDEpy.FFTKDE import FFTKDE
# from KDEpy.NaiveKDE import NaiveKDE
# from KDEpy.TreeKDE import TreeKDE
# import itertools
# import pytest
# import matplotlib
#
# matplotlib.use("Agg")  # For testing on servers
#
# kernels = list(NaiveKDE._available_kernels.keys())
# kdes = [NaiveKDE, TreeKDE, FFTKDE]
# kde_pairs = list(itertools.combinations(kdes, 2))
#
#
# @pytest.mark.parametrize(
#     "kde1, kde2, bw, kernel",
#     [
#         (k[0], k[1], bw, ker)
#         for (k, bw, ker) in itertools.product(kde_pairs, [0.1, "silverman", 1], kernels)
#     ],
# )
# def test_api_models_kernels_bandwidths(kde1, kde2, bw, kernel):
#     """
#     Test the API. More specifically the chained version and the non-chained
#     version of the API. It's tested over every implementation, several
#     bandwidths and kernels.
#     """
#     data = np.array([-1, 0, 0.1, 3, 10])
#     weights = [1, 2, 1, 0.8, 2]
#
#     # Chained expression
#     x1, y1 = kde1(kernel=kernel, bw=bw).fit(data, weights).evaluate()
#
#     # Step by step, with previous grid
#     model = kde2(kernel=kernel, bw=bw)
#     model.fit(data, weights)
#     y2 = model.evaluate(x1)
#
#     # Mean error
#     err = np.sqrt(np.mean((y1 - y2) ** 2))
#     if kernel == "box":
#         assert err < 0.025
#     else:
#         assert err < 0.002
#
#
# =============================================================================


if __name__ == "__main__":
    if True:
        # --durations=10  <- May be used to show potentially slow tests
        pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
