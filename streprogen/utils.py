#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 20:29:09 2017

@author: tommy
"""

import random
import functools
import math
import statistics
import operator


def chunker(iterable, size=5, fill=''):
    """
    """

    for i in range(0, len(iterable) // size + 1):
        to_yield = iterable[i * size: (i + 1) * size]
        if len(to_yield) == 0:
            break
        if len(to_yield) < size:
            yield to_yield + [fill] * (size - len(to_yield))
        else:
            yield to_yield

def prioritized_not_None(*args):
    """Return the first argument which is not None.

    Parameters
    ----------
    *args
        Arguments to the function.

    Returns
    -------
    argument
        The first argument which is not None.


    Examples
    -------
    >>> prioritized_not_None(None, None, 2, 5)
    2
    """
    for arg in list(args):
        if arg is None:
            continue
        return arg
    return None


def round_to_nearest(number, nearest = 1):
    """Round 'number' to the nearest multiple of 'nearest'.

    Parameters
    ----------
    number
        A real number to round.
    nearest
        Number to round to closes multiple of.

    Returns
    -------
    rounded
        A rounded number.


    Examples
    -------
    >>> round_to_nearest(6.8, nearest = 2.5)
    7.5
    """
    return nearest * round(number / nearest)


def all_equal(iterable):
    """Checks whether all items in an iterable are equal.

    Parameters
    ----------
    iterable
        An iterable, e.g. a string og a list.

    Returns
    -------
    boolean
        True or False.
    
    Examples
    -------
    >>> all_equal([2, 2, 2])
    True
    >>> all_equal([1, 2, 3])
    False
    """
    first = iterable[0]
    return all([first == i for i in iterable[1:]])


def min_between(min_reps = 3, max_reps = 8, percentile = 0.33):
    """
    Function to decide the minimum number of reps to perform
    given `min_reps` and `max_rep`.
    
    Examples
    -------
    >>> min_between(min_reps = 3, max_reps = 8, percentile = 0.33)
    (3, 5)
    """
    higher_limit = min_reps + (max_reps - min_reps) * percentile
    return min_reps, math.ceil(higher_limit)


def generate_reps(min_reps = 3, max_reps = 8, total = 25, existing = None):
    """Generate 'total' repetitions between 'min_reps' and 'max_reps',
    if existing is given (not None), then some repetitions are already
    drawn.

    Parameters
    ----------
    min_reps
        Lower limit for the repetitions dawing, e.g. 3.
        
    max_reps
        Upper limit for the repetitions dawing, e.g. 8.
        
    total
        The total number of repetitions to return.
        
    existing
        A list of prior reps drawn.

    Returns
    -------
    reps_list
        A list of repetitions between 'min_reps' and 'max_reps', summing to 'total'
        or a number close to it.


    Examples
    -------
    >>> total = 20
    >>> reps_list = generate_reps(3, 8, total)
    >>> sum(reps_list) == total
    True
    """
    
    # Attempt to generate desired number of repetitions 10 times
    attempt = _generate_reps(min_reps, max_reps, total, existing)
    for i in range(10):
        attempt = _generate_reps(min_reps, max_reps, total, existing)
        if sum(attempt) == total:
            return list(map(int, attempt))

    # Convert to integer so there are no int/float mixups
    return list(map(int, attempt))
    

def _generate_reps(min_reps = 3, max_reps = 8, total = 25, existing = None):
    """
    Helper function to generate repetitions.
    """
    
    # Make a copy so as not to change the input variable
    if existing is None:
        existing = []
    else:
        existing = existing.copy()
        
    # While the sum is low, keep adding
    while sum(existing) + max_reps <= total:
        existing.append(random.randint(min_reps, max_reps))
    
    # If the missing number is between limits, add it to get the total
    missing = total - sum(existing)
    if min_reps <=  missing <= max_reps:
        existing.append(missing)

    # Sort the result
    existing.sort(reverse = True)

    return existing

def spread(iterable):
    """Returns the maximal spread of a sorted list of numbers.

    Parameters
    ----------
    iterable
        A list of numbers.

    Returns
    -------
    max_diff
        The maximal difference when the iterable is sorted.


    Examples
    -------
    >>> spread([1, 11, 13, 15])
    10
    
    >>> spread([1, 15, 11, 13])
    10
    """
    if len(iterable) == 1:
        return 0
    
    iterable = iterable.copy()
    iterable.sort()
    
    max_diff = max(abs(i-j) for (i, j) in zip(iterable[1:], iterable[:-1]))

    return max_diff


    
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        
        