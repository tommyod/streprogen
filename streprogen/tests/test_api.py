#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the API. The API should be considered fixed in future releases and should
be equal for every implementation. Therefore it's important to have unit tests
for the API.
"""

import pytest
import itertools
import statistics

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


@pytest.mark.parametrize(
    "func, period",
    list(itertools.product([progression_sawtooth, progression_sinusoidal], [1, 2, 3, 4, 5])),
)
def test_progression_means(func, period):

    weeks = list(range(1, period + 1))
    target = 42

    values = [
        func(
            w,
            start_weight=target,
            final_weight=target,
            start_week=1,
            final_week=8,
            period=period,
            scale=1.0,  # Does not matter
            offset=1.0,  # Does not matter
            k=0,  # Does not matter
        )
        for w in weeks
    ]

    assert abs(statistics.mean(values) - target) <= 1e-6


def test_error_on_non_unique_names():
    """Test that using the same exercise name raises an error."""

    program1 = Program(duration=8, round_to=1)
    with program1.Day():
        program1.DynamicExercise("Bench press", start_weight=100, min_reps=4, max_reps=7)
        program1.DynamicExercise("Bench press", start_weight=90, min_reps=1, max_reps=7)

    with pytest.raises(ValueError, match="Exercise name not unique: Bench press"):
        program1.render()


class TestWaysOfGivingProgress:
    @pytest.mark.parametrize("format", ["tex", "txt", "html"])
    def test_rep_range_exercise_vs_program(self, format):
        """Test that giving rep range in program or exercise is the same."""

        program1 = Program("My first program!", duration=8, round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100, min_reps=4, max_reps=7)
        program1.render()

        program2 = Program("My first program!", duration=8, round_to=1, min_reps=4, max_reps=7)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()

    @pytest.mark.parametrize("format", ["tex", "txt", "html"])
    def test_inc_week_program_vs_exercise(self, format):
        """Test that giving progress in program or exercise is the same."""

        program1 = Program(duration=8, round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100, percent_inc_per_week=2)
        program1.render()

        program2 = Program(duration=8, round_to=1, percent_inc_per_week=2)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()

    @pytest.mark.parametrize("format", ["tex", "txt", "html"])
    def test_inc_per_week_vs_endpoints(self, format):
        """Test that giving progress in program or exercise is the same."""

        program1 = Program(duration=3, units="kg", round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100, percent_inc_per_week=2)
        program1.render()

        program2 = Program(duration=3, units="kg", round_to=1)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100, final_weight=106)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()

    @pytest.mark.parametrize("format", ["tex", "txt", "html"])
    def test_start_weight_vs_final_weight(self, format):
        """Test that giving progress in program or exercise is the same."""

        program1 = Program(duration=3, units="kg", round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100, percent_inc_per_week=2)
        program1.render()

        program2 = Program(duration=3, units="kg", round_to=1)
        with program2.Day():
            program2.DynamicExercise("Bench press", percent_inc_per_week=2, final_weight=106)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()


if __name__ == "__main__":
    if True:
        # --durations=10  <- May be used to show potentially slow tests
        pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys", "-vv"])
