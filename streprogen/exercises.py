#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import warnings

from streprogen.utils import (round_to_nearest, escape_string, compose)


class DynamicExercise(object):
    """
    Class for dynamic exercises.
    """

    def __init__(self, name, start_weight, final_weight, min_reps=3, max_reps=8,
                 reps=None, intensity=None, round_to=None):
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
            
        min_reps
            The minimum number of repetitions for this exercise, e.g. 3.
            
        max_reps
            The maximum number of repetitions for this exercise, e.g. 8.
            
        reps
            The number of baseline repetitions for this exercise. If this
            parameter is set, it will override the global 'reps_per_exercise'
            parameter for the training program. The repetitions will still
            be scaled by the 'reps_scalers' parameter in the training program.
            
        intensity
            The average intensity for this exercise. If set, this will
            override the 'intensity' parameter in the training program.
            The intensity will still be scaled by the 'intensity_scalers'
            parameter.
            
        round_to
            Round the output to the closest multiple of this number, e.g. 2.5.
            
    
        Returns
        -------
        DynamicExercise
            A DynamicExercise object.
    
    
        Examples
        -------
        >>> bench = DynamicExercise('Bench press', 100, 120, 3, 8)
        """
        self.name = escape_string(name)
        self.start_weight = start_weight
        self.final_weight = final_weight
        self.min_reps = min_reps
        self.max_reps = max_reps
        self.reps = reps
        self.intensity = intensity

        if round_to is None:
            self.round = None
        else:
            self.round = functools.partial(round_to_nearest, nearest=round_to)

        if self.start_weight > self.final_weight:
            msg = "Start weight larger than end weight for exericse '{}'."
            warnings.warn(msg.format(self.name))

        if self.min_reps > self.max_reps:
            msg = "'min_reps' larger than 'max_reps' for exercise '{}'."
            raise ValueError(msg.format(self.name))

    def weekly_growth(self, weeks):
        """Calculate the weekly growth in percentage, and rounds
        to one digit.
    
        Parameters
        ----------
        weeks
            Number of weeks to calculate growth over.

        Returns
        -------
        growth_factor
            A real number such that start * growth_factor** weeks = end.
    
    
        Examples
        -------
        >>> bench = DynamicExercise('Bench press', 100, 120, 3, 8)
        >>> bench.weekly_growth(8)
        2.3
        >>> bench.weekly_growth(4)
        4.7
        """
        start, end = self.start_weight, self.final_weight
        growth_factor = ((end / start) ** (1 / weeks) - 1) * 100
        return round(growth_factor, 1)

    def __repr__(self):
        """
        Representation.
        """
        return '{}({})'.format(type(self).__name__, str(self.__dict__)[:60])

    def __str__(self):
        """
        Human readable output.
        """

        strvar = ['name', 'start_weight', 'final_weight', 'min_reps',
                  'max_reps', 'reps', 'intensity']

        arg_str = ', '.join(['{} = {}'.format(k, self.__dict__[k]) for k
                             in strvar if self.__dict__[k] is not None])

        return '{}({})'.format(type(self).__name__, arg_str)


class StaticExercise(object):
    """
    Class for static exercises.
    """

    def __init__(self, name, sets_reps='4 x 10'):
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
        if isinstance(sets_reps, str):
            self.sets_reps = self._function_from_string(sets_reps)
        else:
            self.sets_reps = sets_reps

        # Escape after function evaluation
        self.sets_reps = compose(self.sets_reps, escape_string)



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
        return '{}({})'.format(type(self).__name__, str(self.__dict__)[:60])

    def __str__(self):
        """
        String formatting for readable human output.
        """

        strvar = ['name', 'sets_reps']

        arg_str = ', '.join(['{} = {}'.format(k, self.__dict__[k]) for k
                             in strvar if self.__dict__[k] is not None])

        return '{}({})'.format(type(self).__name__, arg_str)


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
