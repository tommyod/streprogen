#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import math
import random


def reps_to_intensity(reps, slope=-4.8, constant=97.5, quadratic=True):
    """A function mapping from repetitions in the range 1 to 12
    to intensities in the range 0 to 100.

    Parameters
    ----------
    reps
        The number of repetitions to map to the intensity range.
    slope
        Slope for the linear function.
    constant
        Constant for the linear function
    quadratic
        If 'True', add a slight quadratic offset.


    Returns
    -------
    intensity
        An intensity value in the range from 0 to 100.


    Examples
    -------
    >>> reps_to_intensity(5, slope = -5, constant = 100, quadratic = False)
    80
    
    >>> reps_to_intensity(8, slope = -5, constant = 100, quadratic = True)
    67.45
    
    >>> reps_to_intensity(8, slope = -5, constant = 100, quadratic = False)
    65
    """
    intensity = constant + slope * (reps - 1)
    if quadratic:
        return intensity + 0.05 * (reps - 1) ** 2
    else:
        return intensity


def progression_linear(week, start_weight, final_weight, start_week, end_week):
    """A linear progression function going through the points
    ('start_week', 'start_weight') and ('end_week', 'final_weight'), evaluated
    in 'week'.

    Parameters
    ----------
    week
        The week to evaluate the linear function at.
    start_weight
        The weight at 'start_week'.
    final_weight
        The weight at 'end_week'.
    start_week
        The number of the first week, typically 1.
    end_week
        The number of the final week, e.g. 8.


    Returns
    -------
    weight
        The weight at 'week'.


    Examples
    -------
    >>> progression_linear(week = 2, start_weight = 100, final_weight = 120,
    ...                    start_week = 1, end_week = 3)
    110.0
    
    >>> progression_linear(3, 100, 140, 1, 5)
    120.0
    """
    # Calculate the slope of the linear function
    slope = (start_weight - final_weight) / (start_week - end_week)

    # Return the answer y = slope (x - x_0) + y_0
    return slope * (week - start_week) + start_weight


def progression_sinusoidal(
    week,
    start_weight,
    final_weight,
    start_week,
    end_week,
    periods=2,
    scale=0.025,
    offset=0,
    k=0,
):
    """A sinusoidal progression function going through the points
    ('start_week', 'start_weight') and ('end_week', 'final_weight'), evaluated
    in 'week'. This function calls a linear progression function
    and multiplies it by a sinusoid.

    Parameters
    ----------
    week
        The week to evaluate the linear function at.
    start_weight
        The weight at 'start_week'.
    final_weight
        The weight at 'end_week'.
    start_week
        The number of the first week, typically 1.
    end_week
        The number of the final week, e.g. 8.
    periods
        Number of sinusoidal periods in the time range.
    scale
        The scale (amplitude) of the sinusoidal term.
    offset
        The offset (shift) of the sinusoid.
    k
        Exponential growth. Higher results in more exponential growth.


    Returns
    -------
    weight
        The weight at 'week'.


    Examples
    -------
    >>> progression_sinusoidal(1, 100, 100, 1, 8, periods=4)
    100.0
    >>> progression_sinusoidal(3, 100, 100, 1, 8, periods=4)
    100.0
    >>> progression_sinusoidal(5, 100, 100, 1, 8, periods=4)
    100.0
    """
    # Get the base model
    base = progression_diffeq(week, start_weight, final_weight, start_week, end_week, k)

    # Calculate the time period and the argument to the sine function
    time_period = end_week - start_week + 1
    sine_argument = (
        (week - offset - start_week) * (math.pi * 2) / (time_period / periods)
    )

    base_with_sinusoidal = base * (1 + scale * math.sin(sine_argument))
    return base_with_sinusoidal


def progression_diffeq(week, start_weight, final_weight, start_week, end_week, k):
    """
    Returns the current strength level from linearly adjusted differential eq.
    """
    S_i = start_weight
    S_m = final_weight
    t = week
    t_i = start_week
    t_m = end_week

    a = (t_i - t) / (t_m - t_i)
    return (S_i - S_m) * math.exp(a * k) + S_m + a * (S_i - S_m) * math.exp(-k)


reps_to_intensity_tight = functools.partial(reps_to_intensity, slope=-4)
reps_to_intensity_relaxed = functools.partial(reps_to_intensity, slope=-5.6)

if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
