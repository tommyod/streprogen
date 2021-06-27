#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the modeling functions.
"""

import pytest
import itertools
import statistics

from streprogen import progression_sinh


@pytest.mark.parametrize("k, duration", [(0, 12), (0, 13), (3, 12), (3, 13)])
def test_progression_sinh(k, duration):

    # Test first and last points
    assert progression_sinh(0, 50, 100, 1, final_week=duration, k=k) == 0


if __name__ == "__main__":
    if True:
        # --durations=10  <- May be used to show potentially slow tests
        pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys", "-vv"])
