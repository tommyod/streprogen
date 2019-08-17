#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from streprogen.day import Day
from streprogen.exercises import DynamicExercise, StaticExercise
from streprogen.modeling import (
    progression_diffeq,
    progression_sinusoidal,
    reps_to_intensity,
    reps_to_intensity_relaxed,
    reps_to_intensity_tight,
)
from streprogen.program import Program

__version__ = "2.0.1"

__all__ = [
    "StaticExercise",
    "DynamicExercise",
    "Day",
    "Program",
    "reps_to_intensity",
    "reps_to_intensity_tight",
    "reps_to_intensity_relaxed",
    "progression_diffeq",
    "progression_sinusoidal",
]
