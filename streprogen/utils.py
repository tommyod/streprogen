#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import math
import random
from functools import wraps


def compose(first_func, second_func):
    """
    Compose two functions. Documentation is retrieved from the first one.

    Parameters
    ----------
    first_func
        The first, main, function.

    second_func
        The second, (less important) function.

    Returns
        function
        A new function.
    -------

    """

    @wraps(first_func)
    def composed_func(*args, **kwargs):
        return second_func((first_func(*args, **kwargs)))

    return composed_func

def escape_string(text):
    """Remove problematic characters.

    Parameters
    ----------
    text
        A string with potentially problematic characters.

    Returns
    -------
    string
        The text with characters removed.


    Examples
    -------
    >>> s = r'hello_world$here'
    >>> escape_string(s) == r'helloworldhere'
    True
    """
    if text is None:
        return text


    TO_REMOVE = [r'&', r'%', r'$', r'#', r'_', r'{', r'}',
                 r'~', r'^', r'\\']

    for char in TO_REMOVE:
        text = text.replace(char, '')
    return text


def chunker(iterable, size=5, fill=''):
    """Chunk the iterable.

    Parameters
    ----------
    iterable
        A list.

    size
        The size of the chunks.

    fill
        Fill value if the chunk is not of length 'size'.

    Yields
    -------
    chunk
        A chunk of length 'size'.


    Examples
    -------
    >>> l = list(range(6))
    >>> chunks = list(chunker(l, size=4, fill=''))
    >>> chunks == [[0, 1, 2, 3], [4, 5, '', '']]
    True
    """

    for index in range(0, len(iterable) // size + 1):
        to_yield = iterable[index * size: (index + 1) * size]

        # Stop yielding if empty
        if len(to_yield) == 0:
            break

        # Add fill values if there are too few elements
        if len(to_yield) < size:
            yield to_yield + [fill] * (size - len(to_yield))
        else:
            # Yield
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


def round_to_nearest(number, nearest=1):
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
    result = nearest * round(number / nearest)
    if result % 1 == 0:
        return int(result)

    if nearest % 1 == 0:
        return round(result)
    if nearest % 0.1 == 0:
        return round(result, 1)
    if nearest % 0.01 == 0:
        return round(result, 2)
    return result


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
    if len(iterable) in [0, 1]:
        return False

    first = iterable[0]
    return all([first == i for i in iterable[1:]])


def min_between(min_reps=3, max_reps=8, percentile=0.33):
    """Function to decide the minimum number of reps to perform
    given `min_reps` and `max_rep`.

    Parameters
    ----------
    min_reps
        The minimum number of repeitions.

    max_reps
        The maximum number of repetitions.

    percentile
        The percentile to cap at.

    Return
    -------
    (low, high)
        A tuple containing a new rep range.


    Examples
    -------
    >>> min_between(min_reps = 3, max_reps = 8, percentile = 0.33)
    (3, 5)
    """
    higher_limit = min_reps + (max_reps - min_reps) * percentile
    return min_reps, math.ceil(higher_limit)


def generate_reps(min_reps=3, max_reps=8, total=25, existing=None):
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
    """

    # If no existing repetitions exist, start from empty list
    if existing is None:
        existing = []

    # List of possible rep strings to return
    possible = []

    for _ in range(3):

        # Fill list with randomly drawn reptitions
        created = existing.copy()
        while sum(created) < (total - min_reps):
            generated = random.randint(min_reps, max_reps)
            created.append(generated)

        # Sort and append to the list of lists
        created.sort(reverse=True)
        possible.append(created)

    # Return the list of reps which is closest to the total desired number
    return min(possible, key=lambda l: abs(total - sum(l)))


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

    max_diff = max(abs(i - j) for (i, j) in zip(iterable[1:], iterable[:-1]))

    return max_diff


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
