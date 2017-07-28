#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import functools
import math
import statistics
import operator


class RepellentGenerator(object):
    """
    Generates objects from a domain,
    each time an object is drawn,
    the probability of it being drawn again
    is determined by the probability function.
    """

    def __init__(self, domain, probability_func=None, generated=None):
        """Initialize a RepellentGenerator, which is a generator
        where when an object is generated, the probability of it 
        begin generated changes.
    
        Parameters
        ----------
        domain
            A list of objects to generate from, e.g. [1, 2, 3].
        probability_func
            A probability function, it should be decreasing, e.g. lambda x: 1 / 2**x. 
        generated
            A user specified dictionary of the form {element1: num1, element2: num2, ...}
            where num1, num2, ... are the initial states descriping how many times
            the elements element1, element2, ... have been generated. Supplying
            this argument changes the initial probability distribution.
    
    
        Returns
        -------
        RepellentGenerator
            A RepellentGenerator object.
    
    
        Examples
        -------
        >>> domain = [1, 2, 3]
        >>> generator = RepellentGenerator(domain)
        >>> generator.generate_one() in domain
        True
        """

        # Initialize the domain
        self.domain = domain

        # If no probability function is given, default to exponential
        if probability_func is None:
            self.probability_func = lambda x: 1 / 2 ** x
        else:
            self.probability_func = probability_func

        # If no seed values are given, default to zeros
        if generated is None:
            self.generated = {element: 0 for element in domain}
        else:
            self.generated = generated

    def generate_one(self):
        """Generate a single element.
    
        Returns
        -------
        element
            An element from the domain.
    
    
        Examples
        -------
        >>> generator = RepellentGenerator(['a', 'b'])
        >>> gen_item = generator.generate_one()
        >>> gen_item in ['a', 'b']
        True
        """
        # Get the weights for all items in the domain
        weights = [self.probability_func(self.generated[element])
                   for element in self.domain]

        # Sample from the domain using the weights
        element = random.choices(self.domain, weights=weights)[0]

        # Update the generated values and return
        self.generated[element] += 1

        return element

    def yield_from_domain(self, num=1):
        """Yield 'num' elements from the domain.
    
        Yields
        -------
        A sequence of elements from the domain.
    
    
        Examples
        -------
        >>> domain = ['a', 1]
        >>> generator = RepellentGenerator(domain)
        >>> for element in generator.yield_from_domain(3):
        ...     print(element in domain)
        True
        True
        True
        """
        # Yield the appropriate number of elements
        for i in range(num):
            yield self.generate_one()


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


def progression_linear(week, start_weight, end_weight, start_week, end_week):
    """A linear progression function going through the points
    ('start_week', 'start_weight') and ('end_week', 'end_weight'), evaluated
    in 'week'.

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
    >>> progression_linear(week = 2, start_weight = 100, end_weight = 120, 
    ...                    start_week = 1, end_week = 3)
    110.0
    
    >>> progression_linear(3, 100, 140, 1, 5)
    120.0
    """
    # Calculate the slope of the linear function
    slope = (start_weight - end_weight) / (start_week - end_week)

    # Return the answer y = slope (x - x_0) + y_0
    return slope * (week - start_week) + start_weight


def progression_sinusoidal(week, start_weight, end_weight, start_week, end_week,
                           periods=2, scale=0.025, offset=0):
    """
    """
    # Get the linear model
    linear = progression_linear(week, start_weight, end_weight, start_week, end_week)

    # Calculate the time period and the argument to the sine function
    time_period = end_week - start_week
    sine_argument = (week - offset - start_week) * (math.pi * 2) / (time_period / periods)

    linear_with_sinusoidal = linear * (1 + scale * math.sin(sine_argument))
    return linear_with_sinusoidal


reps_to_intensity_tight = functools.partial(reps_to_intensity, slope=-4)
reps_to_intensity_relaxed = functools.partial(reps_to_intensity, slope=-5.6)

if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
