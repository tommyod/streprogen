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

    assert len(day.exercises) == 3

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

    # Variable reference to days are added
    assert bench.day is not None
    assert squats.day is not None

    assert len(day.exercises) == 3

    # Add day(s) to program and render it
    program.add_days(day)
    assert day.program is not None

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
        program.DynamicExercise("Bench press", 60, 65)
        program.DynamicExercise("Squats", 80, 85)
        program.StaticExercise("Curls", curl_func)

    assert len(program.days) == 1
    assert len(program.days[0].exercises) == 3

    assert program.days[0].program is not None
    assert program.days[0].exercises[0].day is not None

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


def test_dynamic_exercises_are_not_mutated():
    """Creating a program should not mutate an exercise."""

    # Create an exercise
    exercise = DynamicExercise("Bench press", start_weight=100)
    exercise_dict = exercise.serialize()

    # Create a program, add the day and render it
    program = Program()
    day = Day("Monday")
    day.add_exercises(exercise)
    program.add_days(day)
    program.render()

    assert exercise.serialize() == exercise_dict


def test_program_not_mutated_after_rendering():
    """Creating and rendering a program should not mutate its dict
    representations."""

    # Set some non-typical parameters
    program = Program(
        name="MyProgram",
        duration=5,
        min_reps=1,
        reps_per_exercise=31,
        round_to=10,
        rep_scaler_func=[0.99, 0.97, 0.96, 0.95, 0.98],
        intensity_scaler_func=[0.99, 0.97, 0.96, 0.95, 0.98],
        units="asdf",
    )
    with program.Day("A"):
        program.DynamicExercise("Squats", start_weight=100, final_weight=113, max_reps=12)

    program_serialized = program.serialize()
    program.render()
    program_dict = program.to_dict()

    # Rendering the program should not change the serialization
    assert program.serialize() == program_serialized

    # Serializing and de-serializing should not change the program dict reprs
    program = Program.deserialize(program.serialize())
    program.render()
    assert program.serialize() == program_serialized
    assert program_dict == program.to_dict()


class TestProgressInformation:
    def test_progress_information_override_weights(self):
        program = Program(name="MyProgram", duration=10, percent_inc_per_week=10)
        with program.Day("A"):
            squat = program.DynamicExercise("Squats", start_weight=100, final_weight=150)

        (start_w, final_w, inc_week) = squat._progress_information()
        assert start_w == 100
        assert final_w == 150
        assert inc_week == 5  # Weight override program default

    def test_progress_information_override_perc_inc(self):
        program = Program(name="MyProgram", duration=10, percent_inc_per_week=1)
        with program.Day("A"):
            squat = program.DynamicExercise("Squats", start_weight=100, percent_inc_per_week=10)

        (start_w, final_w, inc_week) = squat._progress_information()
        assert start_w == 100
        assert final_w == 200
        assert inc_week == 10  # Weight override program default

    def test_progress_information_calcs(self):
        program = Program(name="MyProgram", duration=10, percent_inc_per_week=123)

        # Three ways of saying the same thing
        with program.Day():
            a = program.DynamicExercise("a", start_weight=100, percent_inc_per_week=10)
            b = program.DynamicExercise("b", start_weight=100, final_weight=200)
            c = program.DynamicExercise("c", final_weight=200, percent_inc_per_week=10)

        a_info = a._progress_information()
        b_info = b._progress_information()
        c_info = c._progress_information()

        assert a_info == b_info
        assert b_info == c_info

    def test_progress_information_calcs_from_program(self):
        program = Program(name="MyProgram", duration=10, percent_inc_per_week=10)

        # Three ways of saying the same thing
        with program.Day():
            a = program.DynamicExercise("a", start_weight=100)
            b = program.DynamicExercise("b", start_weight=100, final_weight=200)
            c = program.DynamicExercise("c", final_weight=200)

        a_info = a._progress_information()
        b_info = b._progress_information()
        c_info = c._progress_information()

        assert a_info == b_info
        assert b_info == c_info

    def test_progress_information_overspecified(self):
        # Set some non-typical parameters
        program = Program(name="MyProgram", duration=10)
        with pytest.raises(ValueError, match="At most 2 out of 3 variables may be set"):
            with program.Day("A"):
                program.DynamicExercise("Squats", start_weight=100, final_weight=150, percent_inc_per_week=10)


def test_error_on_non_unique_exercise_names():
    """Test that using the same exercise name raises an error."""

    program1 = Program(duration=8, round_to=1)
    with program1.Day():
        program1.DynamicExercise("Bench press", start_weight=100, min_reps=4, max_reps=7)
        program1.DynamicExercise("Bench press", start_weight=90, min_reps=1, max_reps=7)

    with pytest.raises(ValueError, match="Exercise name not unique: Bench press"):
        program1.render()


class TestSerialization:
    def test_DynamicExercise(self):
        """Serialize and deserialize should be equal."""

        dynamic_ex = DynamicExercise("Bench", start_weight=100)
        dyn_ex_dict = dynamic_ex.serialize()
        assert dynamic_ex == DynamicExercise.deserialize(dyn_ex_dict)

    def test_StaticExercise(self):
        """Serialize and deserialize should be equal."""

        static_ex = StaticExercise("Dips", "4 x 10")
        static_ex_dict = static_ex.serialize()
        assert static_ex == StaticExercise.deserialize(static_ex_dict)

    def test_Day(self):
        """Serialize and deserialize should be equal."""

        bench = DynamicExercise("Bench", start_weight=100)
        deadlift = DynamicExercise("Deadlift", start_weight=100, final_weight=140)
        static_ex = StaticExercise("Dips", "4 x 10")

        day = Day("Monday", [bench, deadlift, static_ex])
        day_dict = day.serialize()

        assert day_dict == Day.deserialize(day_dict).serialize()

    def test_Program(self):
        """Serialize and deserialize should be equal."""

        program = Program(
            name="Beginner 5x5", duration=4, intensity=85, units="kg", round_to=2.5, rep_scaler_func=[1, 1, 1, 1]
        )

        with program.Day("A"):
            program.DynamicExercise(name="Squat", start_weight=100)

        program.render()

        # Create a new program by serializing and deserializing
        new_program = Program.deserialize(program.serialize())
        new_program.render()

        assert str(program) == str(new_program)


class TestWaysOfGivingRepAndIntensity:
    @pytest.mark.parametrize("format", ["tex", "txt", "html", "dict"])
    def test_rep_scalers_as_function_vs_list(self, format):
        """Test that both functions and lists work the same."""

        def rep_scaler_func(week):
            return 1 - week / 100

        rep_scalers = [(1 - week / 100) for week in range(1, 9)]

        program1 = Program("My first program!", duration=8, round_to=1, rep_scaler_func=rep_scaler_func)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        program2 = Program("My first program!", duration=8, round_to=1, rep_scaler_func=rep_scalers)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()

    @pytest.mark.parametrize("format", ["tex", "txt", "html", "dict"])
    def test_intensity_scalers_as_function_vs_list(self, format):
        """Test that both functions and lists work the same."""

        def intensity_scaler_func(week):
            return 1 - week / 100

        intensity_scalers = [(1 - week / 100) for week in range(1, 9)]

        program1 = Program("My first program!", duration=8, round_to=1, intensity_scaler_func=intensity_scaler_func)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        program2 = Program("My first program!", duration=8, round_to=1, intensity_scaler_func=intensity_scalers)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)
        program2.render()

        # Use .txt format to compare programs
        assert getattr(program1, f"to_{format}")() == getattr(program2, f"to_{format}")()


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

        # Use formats to compare programs
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

    def test_setting_optimization_params(self):
        """Test that setting via method works."""

        program1 = Program(duration=12, units="kg", round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        program2 = Program(duration=12, units="kg", round_to=1)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)

        program2.set_optimization_params(reps_slack=3, max_diff=1, max_unique=2)
        program2.render()

        # They should be different
        assert str(program1) != str(program2)


class TestShiftingDynExercises:
    def test_shifting_zero(self):
        program1 = Program("My first program!", duration=8, round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        program2 = Program("My first program!", duration=8, round_to=1)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100, shift=0)
        program2.render()

        assert str(program1) == str(program2)

    @pytest.mark.parametrize("shift", [-3, -2, -1, 0, 1, 2, 3])
    def test_shifting_k(self, shift):
        program1 = Program("My first program!", duration=8, round_to=1)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        program2 = Program("My first program!", duration=8, round_to=1)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100, shift=shift)
        program2.render()

        assert program1.to_dict()["rendered"][4] == program2.to_dict()["rendered"][4 - shift]

    def test_list_vs_function_arg(self):
        """Test that index 0 in the list corresponds to week=1."""

        def rep_scaler_func(week):
            return 1 + week / 10

        program1 = Program("My first program!", duration=8, rep_scaler_func=rep_scaler_func)
        with program1.Day():
            program1.DynamicExercise("Bench press", start_weight=100)
        program1.render()

        rep_scaler_list = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]

        program2 = Program("My first program!", duration=8, rep_scaler_func=rep_scaler_list)
        with program2.Day():
            program2.DynamicExercise("Bench press", start_weight=100)
        program2.render()

        assert str(program1) == str(program2)


class TestRounding:
    def test_rounding_func_exercise(self):
        """Test that both functions and numbers work for rounding."""

        def round_function(x):
            return round(x / 4) * 4

        # Create a 4-week program
        program = Program("My first program!", duration=8)

        with program.Day():
            program.DynamicExercise("Bench press", 60, 65, round_to=2.5)
            program.DynamicExercise("Squats", 80, 85, round_to=round_function)

        program.render()

        assert True

    def test_rounding_func_program(self):
        """Test that both functions and numbers work for rounding."""

        def round_function(x):
            return round(x / 4) * 4

        # Create a 4-week program
        program = Program("My first program!", duration=8, round_to=round_function)

        with program.Day():
            program.DynamicExercise("Bench press", 60, 65)
            program.DynamicExercise("Squats", 80, 85)

        program.render()

        for week in program.to_dict()["rendered"]:
            for day in week:
                for dyn_ex in day["exercises"]:
                    assert all(w % 4 == 0 for w in dyn_ex["weights"])

        assert True


if __name__ == "__main__":
    # --durations=10  <- May be used to show potentially slow tests
    pytest.main(args=[".", "--doctest-modules", "--capture=sys", "-v", "-k", "round"])
