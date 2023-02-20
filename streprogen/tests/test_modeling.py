#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the modeling functions.
"""

import pytest

from streprogen import progression_sinh, progression_diffeq


@pytest.mark.parametrize("k, duration", [(0, 12), (0, 13), (3, 12), (3, 13)])
def test_progression_sinh(k, duration):
    # Test first and last points
    assert progression_sinh(1, 50, 100, 1, final_week=duration, k=k) == 50
    assert progression_sinh(duration, 50, 100, 1, final_week=duration, k=k) == 100

    # Test midpoint
    assert progression_sinh((duration + 1) / 2, 50, 100, 1, final_week=duration, k=k) == 75


@pytest.mark.parametrize("k, duration", [(0, 12), (0, 13), (3, 12), (3, 13)])
def test_progression_diffeq(k, duration):
    # Test first and last points
    assert progression_diffeq(1, 50, 100, 1, final_week=duration, k=k) == 50
    assert progression_diffeq(duration, 50, 100, 1, final_week=duration, k=k) == 100


if __name__ == "__main__":
    # --durations=10  <- May be used to show potentially slow tests
    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys", "-vv"])
