#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from streprogen.day import Day
from streprogen.diet import Food, Meal
from streprogen.exercises import DynamicExercise, StaticExercise
from streprogen.mealplan import Mealplan
from streprogen.modeling import (
    progression_diffeq,
    progression_sinusoidal,
    progression_sawtooth,
    reps_to_intensity,
    reps_to_intensity_relaxed,
    reps_to_intensity_tight,
)
from streprogen.optimization import RepSchemeGenerator, RepSchemeOptimizer
from streprogen.program import Program

__version__ = "3.0.3"

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
    "progression_sawtooth",
    "Food",
    "Meal",
    "Mealplan",
    "RepSchemeGenerator",
    "RepSchemeOptimizer",
]
