#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the API. The API should be considered fixed in future releases and should
be equal for every implementation. Therefore it's important to have unit tests
for the API.
"""

import pytest

from streprogen import Day, DynamicExercise, Program, StaticExercise
from streprogen import progression_sawtooth, progression_sinusoidal


@pytest.mark.parametrize("duration", list(range(2, 9)))
def test_verbose_api(duration):
    """The oldest, most verbose API."""

    def curl_func(week):
        return "{} x 10".format(week)

    # Create a 4-week program
    program = Program("My first program!", duration=duration)

    # Create some dynamic and static exercises
    bench = DynamicExercise("Bench press", 60, 60 * (1 + 0.01 * duration))
    squats = DynamicExercise("Squats", 80, 80 * (1 + 0.01 * duration))
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
    bench = DynamicExercise("Bench press", 60, 70)
    squats = DynamicExercise("Squats", 80, 90)
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


@pytest.mark.parametrize("period", [0, 1])
def test_progression_periods(period):

    for week in range(1, 8 + 1):

        ans = progression_sawtooth(
            week,
            start_weight=1.0,
            final_weight=1.0,
            start_week=1,
            final_week=8,
            period=period,
            scale=1.0,  # Does not matter
            offset=0,  # Does not matter
            k=0,  # Does not matter
        )
        assert abs(ans - 1.0) < 1e-6

        ans = progression_sinusoidal(
            week,
            start_weight=1.0,
            final_weight=1.0,
            start_week=1,
            final_week=8,
            period=period,
            scale=1.0,  # Does not matter
            offset=0,  # Does not matter
            k=0,  # Does not matter
        )
        assert abs(ans - 1.0) < 1e-6


if __name__ == "__main__":
    if True:
        # --durations=10  <- May be used to show potentially slow tests
        pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
