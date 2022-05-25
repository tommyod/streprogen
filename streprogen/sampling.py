#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numbers
import itertools
import random
import bisect


def roll(container, k):
    """Roll elements in a container, wrapping around the boundary.

    Examples
    --------
    >>> x = list(range(10))
    >>> roll(x, 2)
    [8, 9, 0, 1, 2, 3, 4, 5, 6, 7]

    """
    size = len(container)
    return [container[(i - k) % size] for i in range(size)]


def sample(weights):
    """Yield integers corresponding to weighted samples taken with replacement."""
    weights = list(weights)
    assert all(isinstance(w_i, numbers.Number) for w_i in weights)
    assert all(w_i >= 0 for w_i in weights)

    cumsum = list(itertools.accumulate(weights))
    while True:
        pick = random.random() * cumsum[-1]
        yield bisect.bisect_left(cumsum, x=pick)


def sample_markov_loop(probabilities, structure=None):
    """Sample from a probability distribution over 0, 1, ..., n-1 given by
    a sequence of `probabilities`. The samples are generated using a Markov
    chain with structure that allows jumping forward.

    The first sample will always be 0. To start at a random state, run the
    chain for a while and discard the beginning of it.

    The `structure` argument determines both how many steps ahead it is
    possible to sample, and what relative preference is given to the steps.

    Examples
    --------
    >>> probabilities = [1, 2, 3, 4]
    >>> structure = [0.5, 0.5] # Either stay in state i, or jump to i+1
    >>> structure = [0.1, 0.9] # Same, but the chain mixes faster
    >>> structure = [1, 0] # Same, but edge case - chain never mixes
    >>>
    >>> structure = [0, 0.8, 0.2] # Allows jumping 1 or 2 states ahead
    >>> structure = [0, 0.1, 0.9] # Same, but jumps 2 states more often

    """
    # If no structure is given, then strongly prefer jumping one step ahead
    if structure is None:
        structure = [0.01, 0.99]

    # The structure can at most have the same length as the probability vector
    assert len(structure) <= len(probabilities)
    probabilities, structure = list(probabilities), list(structure)

    # Convert to lists just to be safe, then pad the structure with zeros
    structure = structure + [0] * (len(probabilities) - len(structure))

    # Normalize structure, then interpret it relative to min(probabilities)
    # We must have 0 <= s_1 + s_2 + ... <= min(probability)
    min_probability = min(probabilities)
    sum_structure = sum(structure)
    structure = [min_probability * s_i / sum_structure for s_i in structure]

    # On the diagonals we find S = s_1 + s_2 + s_3 + ..., and we store this
    # value of S on the 0'th index for convenience
    structure[0] = sum(structure[1:])

    # Start at state 0. To start at a random state, throw away initial samples
    state = 0
    yield state

    while True:
        # Compute the row in the transition matrix corresponding to the state
        to_draw_probs = roll(structure, state)
        # In the diagonal entry, we must subtract. P_ii = pi_i - S
        to_draw_probs[state] = probabilities[state] - to_draw_probs[state]
        # Divide every element by pi_i
        to_draw_probs = [p_i / probabilities[state] for p_i in to_draw_probs]

        state = next(sample(to_draw_probs))
        yield state


def sample_markov_ladder(probabilities, structure=None):
    """Sample from a probability distribution over 0, 1, ..., n-1 given by
    a sequence of `probabilities`. The samples are generated using a Markov
    chain with structure that allows jumping to neighboring states (but does
    NOT loop around).

    The first sample will always be 0. To start at a random state, run the
    chain for a while and discard the beginning of it.

    The `structure` argument determines both how many neighboring states it is
    possible to jump to, and what relative preference is given to the jumps.

    Examples
    --------
    >>> probabilities = [1, 2, 3, 4]
    >>> structure = [0.5, 0.5] # Either stay in state i, or jump to i-1 or i+1
    >>> structure = [0.1, 0.9] # Same, but the chain mixes faster
    >>> structure = [1, 0] # Same, but edge case - chain never mixes
    >>>
    >>> structure = [0, 0.8, 0.2] # Allows jumping 1 or 2 states back or forth
    >>> structure = [0, 0.1, 0.9] # Same, but jumps further away more often

    """
    if structure is None:
        structure = [0.01, 0.99]

    assert len(structure) <= len(probabilities)
    probabilities, structure = list(probabilities), list(structure)

    # Normalize structure
    sum_structure = sum(structure)
    min_probability = min(probabilities)
    structure = [min_probability * (s_i / sum_structure) / 2 for s_i in structure]

    # Future states
    future_states = list(range(len(probabilities)))

    structure[0] = sum(structure[1:])

    state = 0
    yield state

    k, n = len(structure), len(probabilities)
    while True:

        # Assemble probabilities
        left_probs = [structure[i] / probabilities[state] for i in reversed(range(1, min(k, state + 1)))]
        right_probs = [structure[i] / probabilities[state] for i in range(1, min(k, n - state))]
        center_prob = [1 - sum(left_probs) - sum(right_probs)]
        to_draw_probs = left_probs + center_prob + right_probs

        future_states_filtered = [s for s in future_states if abs(state - s) < k]

        # Draw the index of the weight, then map it to the state integer
        state_index = next(sample(to_draw_probs))
        state = future_states_filtered[state_index]

        yield state


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys", "-k", "markov"])
