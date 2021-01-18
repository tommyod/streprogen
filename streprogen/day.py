#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from streprogen.exercises import DynamicExercise, StaticExercise
from streprogen.utils import escape_string


class Day(object):
    """
    A day object is a container for exercises associated with the specific day.
    """

    def __init__(self, name=None, exercises=None):
        """Initialize a new day object.

        Parameters
        ----------
        name
            The name of the day, e.g. 'Day A'. If no name is given then the day
            will automatically be given a numeric name such as 'Day 1', 'Day 2', etc.

        exercises
            A list of exercises. Exercises can also be associated with a day using
            the 'add_exercises' method later on.


        Examples
        -------
        >>> monday = Day(name='Monday')
        >>> curls = StaticExercise('Curls', '3 x 12')
        >>> monday.add_exercises(curls)
        >>> curls in monday.static_exercises
        True
        """
        self.name = escape_string(name)
        self.dynamic_exercises = []
        self.static_exercises = []

        self.program = None

        if exercises is not None:
            self.add_exercises(*tuple(exercises))

    def __enter__(self):
        self.program.active_day = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.program.days.append(self)
        self.program.active_day = None

    def add_exercises(self, *exercises):
        """Add the exercises to the day. The method will automatically infer
        whether a static or dynamic exercise is passed to it.

        Parameters
        ----------
        *exercises
            An unpacked tuple of exercises.


        Examples
        -------
        >>> monday = Day(name='Monday')
        >>> curls = StaticExercise('Curls', '3 x 12')
        >>> pulldowns = StaticExercise('Pulldowns', '4 x 10')
        >>> monday.add_exercises(curls, pulldowns)
        >>> curls in monday.static_exercises
        True
        >>> pulldowns in monday.static_exercises
        True
        """
        for exercise in exercises:
            if isinstance(exercise, DynamicExercise):
                self.dynamic_exercises.append(exercise)
                exercise.day = self

            if isinstance(exercise, StaticExercise):
                self.static_exercises.append(exercise)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, str(self.__dict__)[:60])

    def __str__(self):
        """
        String formatting for readable human output.

        Examples
        -------
        >>> monday = Day(name = 'Monday')
        >>> curls = StaticExercise('Curls', '3 x 12')
        >>> pulldowns = StaticExercise('Pulldowns', '4 x 10')
        >>> monday.add_exercises(curls, pulldowns)
        >>> print(monday)
        Day(name = Monday, static_exercises = [Curls, Pulldowns])
        """
        dyn = ", ".join([d.name for d in self.dynamic_exercises])
        if len(dyn) > 0:
            dyn = "dynamic_exercises = [{}]".format(dyn)
        stat = ", ".join([d.name for d in self.static_exercises])
        if len(stat) > 0:
            stat = "static_exercises = [{}]".format(stat)

        out_str = "{}({})".format(
            type(self).__name__,
            ", ".join([s for s in ["name = {}".format(self.name), dyn, stat] if len(s) > 2]),
        )
        return out_str

    def serialize(self):
        """Export the object to a dictionary."""
        result = {"name": self.name}
        result["dynamic_exercises"] = [ex.serialize() for ex in self.dynamic_exercises]
        result["static_exercises"] = [ex.serialize() for ex in self.static_exercises]
        return result

    @classmethod
    def deserialize(cls, data):
        """Create a new object from a dictionary."""
        name = data["name"]
        exercises = [DynamicExercise.deserialize(ex) for ex in data["dynamic_exercises"]]
        exercises += [StaticExercise.deserialize(ex) for ex in data["static_exercises"]]
        return cls(name, exercises)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
