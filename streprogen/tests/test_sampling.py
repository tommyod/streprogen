#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the sampling functions.
"""

import pytest
import itertools
import collections

from streprogen.sampling import sample_markov_ladder, sample_markov_loop


@pytest.mark.parametrize(
    "probabilities, structure",
    [
        ([1, 2, 3], [0.5, 0.5]),
        ([1, 2, 3], [0.7, 0.3]),
        ([1, 2, 3], [0.1, 0.9]),
        ([1, 2, 3, 7, 4], [0.2, 0.4, 0.4]),
        ([1, 2, 3, 7, 4], [0.5, 0.25, 0.25]),
        ([1, 2, 3, 7, 4], [1, 5]),
    ],
)
def test_markov_ladder(probabilities, structure):
    generator = sample_markov_ladder(probabilities, structure=structure)

    # Scale after calling sampling, to test that normalization is not needed
    probabilities = [p_i / sum(probabilities) for p_i in probabilities]

    # Draw samples and normalize output probabilities
    num_samples = 1_000_000
    samples = itertools.islice(generator, num_samples)
    counts = collections.Counter(samples)
    output_probabilities = [counts[k] / num_samples for k in sorted(counts.keys())]

    assert all((abs(p_i - y_i) / y_i) < 0.1 for p_i, y_i in zip(probabilities, output_probabilities))


@pytest.mark.parametrize(
    "probabilities, structure",
    [
        ([1, 2, 3], [0.5, 0.5]),
        ([1, 2, 3], [0.7, 0.3]),
        ([1, 2, 3], [0.1, 0.9]),
        ([1, 2, 3, 7, 4], [0.2, 0.4, 0.4]),
        ([1, 2, 3, 7, 4], [0.5, 0.25, 0.25]),
        ([1, 2, 3, 7, 4], [1, 5]),
    ],
)
def test_markov_loop(probabilities, structure):
    generator = sample_markov_loop(probabilities, structure=structure)

    # Scale after calling sampling, to test that normalization is not needed
    probabilities = [p_i / sum(probabilities) for p_i in probabilities]

    # Draw samples and normalize output probabilities
    num_samples = 1_000_000
    samples = itertools.islice(generator, num_samples)
    counts = collections.Counter(samples)
    output_probabilities = [counts[k] / num_samples for k in sorted(counts.keys())]

    assert all((abs(p_i - y_i) / y_i) < 0.1 for p_i, y_i in zip(probabilities, output_probabilities))


if __name__ == "__main__":
    # --durations=10  <- May be used to show potentially slow tests
    pytest.main(args=[".", "--doctest-modules", "--capture=sys", "-v", "-k", "markov"])
