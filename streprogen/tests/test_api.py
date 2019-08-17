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


if __name__ == "__main__":
    if True:
        # --durations=10  <- May be used to show potentially slow tests
        pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
