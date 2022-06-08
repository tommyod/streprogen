#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import warnings
import inspect

from streprogen.utils import compose, escape_string, round_to_nearest, prioritized_not_None


class DynamicExercise(object):
    """Class for dynamic exercises."""

    def __init__(
        self,
        name,
        start_weight=None,
        final_weight=None,
        min_reps=None,
        max_reps=None,
        percent_inc_per_week=None,
        reps=None,
        intensity=None,
        round_to=None,
        shift=0,
    ):
        """Initialize a new dynamic exercise. A dynamic exercise is rendered by
        the program, and the set/rep scheme will vary from week to week.

        Parameters
        ----------
        name
            The name of the exercise, e.g. 'Squats'.

        start_weight
            Maximum weight you can lift at the start of the program, e.g. 80.

        final_weight
            The goal weight to work towards during the program. This should be
            set in relation to the duration of the training program, e.g. 90.
            If set, this overrides the optional `percent_inc_per_week` parameter.

        min_reps
            The minimum number of repetitions for this exercise, e.g. 3.

        max_reps
            The maximum number of repetitions for this exercise, e.g. 8.

        percent_inc_per_week
            If `final_weight` is not set, this value will be used. The increase is
            additive, not multipliactive. For instance, if the increase is set to
            `percent_inc_per_week=2`, then after 2 weeks the increase is 4, not
            (1.02 * 1.02 - 1) * 100 = 4.04. The `final_weight` parameter must be
            set to `None` for this parameter to have effect.

        reps
            The number of baseline repetitions for this exercise. If this
            parameter is set, it will override the global 'reps_per_exercise'
            parameter for the training program. The repetitions will still
            be scaled by the `rep_scaler_func` parameter in the training program.

        intensity
            The average intensity for this exercise. If set, this will
            override the `intensity` parameter in the training program.
            The intensity will still be scaled by the `intensity_scaler_func`
            parameter.

        round_to
            Round the output to the closest multiple of this number, e.g. 2.5.
            Alternatively, a callable can be passed. The callable must take
            a number as input and return a rounded number as output.

        shift
            Shift evaluation of repetitions, intensity and progress `shift`
            weeks ahead in time. An exercise shifted by 1 will have its reps,
            intensity and strength evalated at week i + 1 instead of in week i.


        Examples
        -------
        >>> bench = DynamicExercise('Bench press', 100, 120, 3, 8)
        >>> bench2 = DynamicExercise('Bench press', 100, 120, 3, 8)
        >>> bench == bench2
        True


        """
        self.name = escape_string(name)
        self.start_weight = start_weight
        self.final_weight = final_weight
        self._min_reps = min_reps
        self._max_reps = max_reps
        self.percent_inc_per_week = percent_inc_per_week
        self.reps = reps
        self.intensity = intensity
        self.day = None

        var_names = ["start_weight", "final_weight", "percent_inc_per_week"]
        num_specified = sum(1 if (getattr(self, var) is not None) else 0 for var in var_names)
        if num_specified == 3:
            raise ValueError(f"At most 2 out of 3 variables may be set: {var_names}")

        self.round_to = round_to

        assert isinstance(shift, int), "'shift' must be an integer"
        # assert shift >= 0, "'shift' must be non-negative"
        self.shift = shift

        # Use program value instead of exercise value
        if round_to is None:
            self.round = None

        # A callable
        elif callable(round_to):
            self.round = round_to
        else:
            self.round = functools.partial(round_to_nearest, nearest=round_to)

        if self.final_weight and self.start_weight:
            if self.start_weight > self.final_weight:
                msg = "'start_weight' larger than 'final_weight' for exercise '{}'."
                warnings.warn(msg.format(self.name))

        if self.min_reps and self.max_reps:
            if self.min_reps > self.max_reps:
                msg = "'min_reps' larger than 'max_reps' for exercise '{}'."
                raise ValueError(msg.format(self.name))

    def _simple_attributes(self):
        """Yield all simple parameters (ints, strings, etc)."""
        attributes = list(dir(self))  # round is a function
        attributes.remove("round")
        attributes.remove("day")
        attributes.remove("shift")

        for attr_name in attributes:

            # Skip private members
            if attr_name.startswith("_"):
                continue

            # Skip methods
            if inspect.ismethod(getattr(self, attr_name)):
                continue

            if getattr(self, attr_name):
                yield attr_name

    def serialize(self):
        """Export the object to a dictionary.

        Examples
        --------
        >>> bench = DynamicExercise('Bench press', start_weight=100)
        >>> bench.serialize() == {'start_weight': 100, 'name': 'Bench press'}
        True

        """
        result = {
            "name": self.name,
            "start_weight": self.start_weight,
            "final_weight": self.final_weight,
            "min_reps": self._min_reps,
            "max_reps": self._max_reps,
            "percent_inc_per_week": self.percent_inc_per_week,
            "reps": self.reps,
            "intensity": self.intensity,
            "round_to": self.round_to,
        }

        return {k: v for (k, v) in result.items() if v}

    def _progress_information(self):
        """Return a tuple (start_weight, final_weight, percent_inc_per_week).

        Can only be inferred in the context of a Program argument.

        """

        if self.day is None:
            raise Exception("Exercise {self.name} must be attached to a Day.")

        if self.day.program is None:
            raise Exception("Day {self.day.name} must be attached to a Program.")

        program = self.day.program

        # Get increase per week
        inc_week = prioritized_not_None(self.percent_inc_per_week, program.percent_inc_per_week)

        # Case 1: Start weight and final weight is given
        if (self.start_weight is not None) and (self.final_weight is not None):
            start_w, final_w = self.start_weight, self.final_weight
            inc_week = ((final_w / start_w) - 1) / program.duration * 100
            answer = (start_w, final_w, inc_week)

        # Case 2: Start weight and increase is given
        elif (self.start_weight is not None) and (inc_week is not None):
            factor = 1 + (inc_week / 100) * program.duration
            start_w = self.start_weight
            final_w = self.start_weight * factor
            answer = (start_w, final_w, inc_week)

        # Case 3: Final weight and increase is given
        elif (self.final_weight is not None) and (inc_week is not None):
            factor = 1 + (inc_week / 100) * program.duration
            start_w = self.final_weight / factor
            final_w = self.final_weight
            answer = (start_w, final_w, inc_week)

        else:
            raise Exception(f"Exercise {self} is overspecified.")

        rounder = functools.partial(round_to_nearest, nearest=0.01)

        return tuple(map(rounder, answer))

    @property
    def min_reps(self):
        """Return min reps. If a Program attribute it set and the exercise
        attribute is None, use the program attribute."""
        if (self.day is not None) and (self.day.program is not None):
            program = self.day.program
        else:
            return self._min_reps

        return prioritized_not_None(self._min_reps, program.min_reps)

    @min_reps.setter
    def min_reps(self):
        return self._min_reps

    @property
    def max_reps(self):
        """Return max reps. If a Program attribute it set and the exercise
        attribute is None, use the program attribute."""
        if (self.day is not None) and (self.day.program is not None):
            program = self.day.program
        else:
            return self._max_reps

        return prioritized_not_None(self._max_reps, program.max_reps)

    @max_reps.setter
    def max_reps(self):
        return self._max_reps

    def __repr__(self):
        """Representation."""
        return str(self)

    def __str__(self):
        """Human readable output.

        Examples
        --------
        >>> ex = DynamicExercise(name="Bench", start_weight=100)
        >>> str(ex)
        "DynamicExercise(name='Bench', start_weight=100)"
        """

        attr_names = self._simple_attributes()
        arg_str = ", ".join(["{}={}".format(attr, repr(getattr(self, attr))) for attr in attr_names])
        return "{}({})".format(type(self).__name__, arg_str)

    def __eq__(self, other):
        return all(getattr(self, attr) == getattr(other, attr) for attr in self._simple_attributes())

    def __hash__(self):
        attrs = ("name",)
        return hash(tuple(getattr(self, attr) for attr in attrs))

    @classmethod
    def deserialize(cls, data):
        """Create a new object from a dictionary."""
        return cls(**data)


class StaticExercise(object):
    """
    Class for static exercises.
    """

    def __init__(self, name, sets_reps="4 x 10"):
        """Initialize a new static exercise. A static exercise
        is simply a placeholder for some text.

        Parameters
        ----------
        name
            The name of the exercise, e.g. 'Curls'.

        sets_reps
            A static set/rep scheme, e.g. '4 x 10', or '10 minutes'.
            This paramter can also be a function of one parameter,
            the current week. The function must return a string
            for that specific week.


        Returns
        -------
        StaticExercise
            A StaticExercise object.


        Examples
        -------
        >>> curls = StaticExercise('Curls', '4 x 10')
        >>> stretching = StaticExercise('Stretching', '10 minutes')
        """
        self.name = escape_string(name)
        self.sets_reps = sets_reps
        if isinstance(sets_reps, str):
            self.sets_reps_func = self._function_from_string(sets_reps)
        else:
            self.sets_reps_func = sets_reps

        # Escape after function evaluation
        self.sets_reps_func = compose(self.sets_reps_func, escape_string)

    @staticmethod
    def _function_from_string(string):
        """
        Static method that takes a string and returns a function which returns
        the string.
        """

        def function(*args, **kwargs):
            return string

        return function

    def __repr__(self):
        """
        Representation.
        """
        return "{}({})".format(type(self).__name__, str(self.__dict__)[:60])

    def __eq__(self, other):
        return self.name == other.name and self.sets_reps == other.sets_reps

    def __str__(self):
        """
        String formatting for readable human output.
        """

        strvar = ["name", "sets_reps"]

        arg_str = ", ".join(["{}={}".format(k, self.__dict__[k]) for k in strvar if self.__dict__[k] is not None])

        return "{}({})".format(type(self).__name__, arg_str)

    def serialize(self):
        if callable(self.sets_reps):
            raise ValueError(f"Cannot serialize {repr(self)} because `sets_reps` is a function.")
        return {"name": self.name, "sets_reps": self.sets_reps}

    @classmethod
    def deserialize(cls, data):
        return cls(**data)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-vv", "--capture=sys", "-k "])
    bench = DynamicExercise("Bench", start_weight=100)
    print(bench.serialize())
