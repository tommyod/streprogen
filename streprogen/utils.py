#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import wraps


def compose(first_func, second_func):
    """Compose two functions. Documentation is retrieved from the first one.

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

    TO_REMOVE = [r"&", r"%", r"$", r"#", r"_", r"{", r"}", r"~", r"^", r"\\"]

    for char in TO_REMOVE:
        text = text.replace(char, "")
    return text


def chunker(iterable, size=5, fill=""):
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
        to_yield = iterable[index * size : (index + 1) * size]

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
    """Return the first argument that is not None.

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
    >>> round_to_nearest(6.8, nearest=2.5)
    7.5
    >>> round_to_nearest(6.8, nearest=1)
    7
    >>> round_to_nearest(6.8, nearest=5)
    5
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


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
