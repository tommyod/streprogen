#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections.abc
import functools
import math


def reps_to_intensity(reps, slope=-3.5, constant=97.5, quadratic=True):
    """A mapping from repetitions in range [1, 12] to intensities in range [0, 100].

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
    >>> reps_to_intensity(5, slope=-5, constant=100, quadratic=False)
    80
    >>> reps_to_intensity(8, slope=-5, constant=100, quadratic=True)
    67.45
    >>> reps_to_intensity(8, slope=-5, constant=100, quadratic=False)
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
    week, start_weight, final_weight, start_week, final_week, period=4, scale=0.025, offset=0, k=0,
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
            progression_sinusoidal(w, start_weight, final_weight, start_week, final_week, period, scale, offset, k,)
            for w in week
        )

    # Get the base model
    base = progression_diffeq(week, start_weight, final_weight, start_week, final_week, k)
    if period <= 1:
        period = 1

    sine_argument = (week - offset - start_week) * (math.pi * 2) / period

    base_with_sinusoidal = base * (1 + scale * math.sin(sine_argument))
    return base_with_sinusoidal


def progression_sawtooth(
    week, start_weight, final_weight, start_week, final_week, period=4, scale=0.025, offset=0, k=0,
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
    >>> progression_sawtooth(1, 100, 100, 1, 8, period=8, scale=0.1)
    90.0
    >>> x = progression_sawtooth(8, 100, 100, 1, 8, period=8, scale=0.1)
    >>> int(x)
    110
    """
    if isinstance(week, collections.abc.Iterable):
        return list(
            progression_sawtooth(w, start_weight, final_weight, start_week, final_week, period, scale, offset, k,)
            for w in week
        )

    # Get the base model
    base = progression_diffeq(week, start_weight, final_weight, start_week, final_week, k)
    if period <= 1:
        period = 1

    if period > 1:
        x = (week - offset - start_week) / period
        # https://en.wikipedia.org/wiki/Sawtooth_wave
        x = x - math.floor(x)

        # Due to the discrete nature of the sawtooth, the max is p-1 / p, not 1
        wave_amplitude = (period - 1) / period
        # Change the output to be in range: scale * [-1, 1]. The scaling ensures
        # that `scale` means the same thing in sinusoidal and triangle waveforms.
        saw = (2 / wave_amplitude) * x - 1
    else:
        saw = 0

    base_with_sinusoidal = base * (1 + scale * saw)
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
        return list(progression_diffeq(w, start_weight, final_weight, start_week, final_week, k) for w in week)

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


reps_to_intensity_tight = functools.partial(reps_to_intensity, slope=-3.25)
reps_to_intensity_relaxed = functools.partial(reps_to_intensity, slope=-3.75)


def wilks(lifted_kg, bodyweight_kg, gender="male"):
    """Compute Wilks points in kilograms. 
    
    Parameters
    ----------
    lifted_kg : float
        Weight lifted.
    bodyweight_kg : float
        Bodyweight.
    gender : string, optional
        Gender of the lifter, either "male" or "female". The default is "male".

    Returns
    -------
    float
        The wilks score.
        
    Examples
    --------
    >>> round(wilks(500, 100, gender="male"), 2)
    304.29
    >>> round(wilks(400, 70, gender="female"), 2)
    397.94

    """
    if gender not in ("male", "female"):
        raise ValueError("`gender` must be 'male' or 'female'")

    # https://en.wikipedia.org/wiki/Wilks_Coefficient

    # Validated against https://wilkscalculator.com/kg
    # The result is not perfect. There might be a difference in coefficients
    # between the calculator and the wikipedia article. Correct to one decimal.
    if gender == "male":
        a = -216.0475144
        b = 16.2606339
        c = -0.002388645
        d = -0.00113732
        e = 7.01863e-6
        f = -1.291e-8
    if gender == "female":
        a = 594.31747775582
        b = -27.23842536447
        c = 0.82112226871
        d = -0.00930733913
        e = 4.731582e-5
        f = -9.054e-8

    x = bodyweight_kg
    coeff = 500 / (a + b * x + c * x ** 2 + d * x ** 3 + e * x ** 4 + f * x ** 5)

    return round(coeff * lifted_kg, 2)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
