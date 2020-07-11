#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections.abc
import functools
import math


def reps_to_intensity(reps, slope=-4.0, constant=97.5, quadratic=True):
    """A function mapping from repetitions in the range 1 to 12
    to intensities in the range 0 to 100.

    Parameters
    ----------
    reps
        The number of repetitions to map to the intensity range.
    slope
        Slope for the linear function.
    constant
        Constant for the linear function.
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
    if isinstance(reps, collections.abc.Iterable):
        return list(reps_to_intensity(rep, slope, constant, quadratic) for rep in reps)

    intensity = constant + slope * (reps - 1)
    if quadratic:
        return intensity + 0.05 * (reps - 1) ** 2
    else:
        return intensity


def progression_sinusoidal(
    week,
    start_weight,
    final_weight,
    start_week,
    final_week,
    periods=None,
    period=4,
    scale=0.025,
    offset=0,
    k=0,
):
    """A sinusoidal progression function going through the points
    ('start_week', 'start_weight') and ('final_week', 'final_weight'), evaluated
    in 'week'. This function calls a linear progression function
    and multiplies it by a sinusoid.

    Parameters
    ----------
    week
        The week to evaluate the linear function at.
    start_weight
        The weight at 'start_week'.
    final_weight
        The weight at 'final_week'.
    start_week
        The number of the first week, typically 1.
    final_week
        The number of the final week, e.g. 8.
    period
        The length of a period (cycle) in weeks.
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
    >>> progression_sinusoidal(1, 123, 123, 1, 8, period=4)
    123.0
    >>> progression_sinusoidal(7, 123, 123, 1, 8, period=4)
    123.0
    """
    if isinstance(week, collections.abc.Iterable):
        return list(
            progression_sinusoidal(
                w,
                start_weight,
                final_weight,
                start_week,
                final_week,
                periods,
                period,
                scale,
                offset,
                k,
            )
            for w in week
        )

    # Get the base model
    base = progression_diffeq(
        week, start_weight, final_weight, start_week, final_week, k
    )

    # If the deprecated, old `periods` is given
    if periods is not None:
        time_period = final_week - start_week
        x = week - offset - start_week
        sine_argument = x * (math.pi * 2) / (time_period / periods)
    else:
        sine_argument = (week - offset - start_week) * (math.pi * 2) / period

    base_with_sinusoidal = base * (1 + scale * math.sin(sine_argument))
    return base_with_sinusoidal


def progression_sawtooth(
    week,
    start_weight,
    final_weight,
    start_week,
    final_week,
    period=4,
    scale=0.025,
    offset=0,
    k=0,
):
    """A sawtooth progression function going through the points
    ('start_week', 'start_weight') and ('final_week', 'final_weight'), evaluated
    in 'week'. This function calls a linear progression function
    and multiplies it by a sawtooth.

    Parameters
    ----------
    week
        The week to evaluate the linear function at.
    start_weight
        The weight at 'start_week'.
    final_weight
        The weight at 'final_week'.
    start_week
        The number of the first week, typically 1.
    final_week
        The number of the final week, e.g. 8.
    period
        The length of a period (cycle) in weeks.
    scale
        The scale (amplitude) of the sawtooth term.
    offset
        The offset (shift) of the sawtooth.
    k
        Exponential growth. Higher results in more exponential growth.


    Returns
    -------
    weight
        The weight at 'week'.


    Examples
    -------
    >>> # 100 - 10
    >>> progression_sawtooth(1, 100, 100, 1, 8, period=8, scale=0.1)
    90.0
    >>> # 90 + (7 / 8) * 2 * 10
    >>> progression_sawtooth(8, 100, 100, 1, 8, period=8, scale=0.1)
    107.5
    """
    if isinstance(week, collections.abc.Iterable):
        return list(
            progression_sawtooth(
                w,
                start_weight,
                final_weight,
                start_week,
                final_week,
                period,
                scale,
                offset,
                k,
            )
            for w in week
        )

    # Get the base model
    base = progression_diffeq(
        week, start_weight, final_weight, start_week, final_week, k
    )

    x = (week - offset - start_week) / period

    # https://en.wikipedia.org/wiki/Sawtooth_wave
    x = x - math.floor(x)

    # Change the output to be in range: scale * [-1, 1]. The scaling ensures
    # that `scale` means the same thing in sinusoidal and triangle waveforms.
    saw = scale * (2 * x - 1)

    base_with_sinusoidal = base * (1 + saw)
    return base_with_sinusoidal


def progression_diffeq(week, start_weight, final_weight, start_week, final_week, k=0):
    """A linear/exponential progression function going through the points
    ('start_week', 'start_weight') and ('end_week', 'final_weight'), evaluated
    in 'week'.

    Parameters
    ----------
    week
        The week to evaluate the linear function at.
    start_weight
        The weight at 'start_week'.
    final_weight
        The weight at 'final_week'.
    start_week
        The number of the first week, typically 1.
    final_week
        The number of the final week, e.g. 8.
    k
        How much the function "bends". k=0 is linear, k>0 bends it.

    Returns
    -------
    weight
        The weight at 'week'.


    Examples
    -------
    >>> progression_diffeq(week = 2, start_weight = 100, final_weight = 120,
    ...                    start_week = 1, final_week = 3)
    110.0
    >>> progression_diffeq(3, 100, 140, 1, 5)
    120.0
    """
    if isinstance(week, collections.abc.Iterable):
        return list(
            progression_diffeq(w, start_weight, final_weight, start_week, final_week, k)
            for w in week
        )

    assert week <= final_week
    assert week >= start_week

    S_i = start_weight
    S_m = final_weight
    t = week
    t_i = start_week
    t_m = final_week
    assert k >= 0

    # Normalize the time
    a = (t_i - t) / (t_m - t_i)

    # Return the answer
    return (S_i - S_m) * math.exp(a * k) + S_m + a * (S_i - S_m) * math.exp(-k)


reps_to_intensity_tight = functools.partial(reps_to_intensity, slope=-3.5)
reps_to_intensity_relaxed = functools.partial(reps_to_intensity, slope=-4.5)

if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
