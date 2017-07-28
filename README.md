# Streprogen - A strength program generator
[![PyPI version](https://badge.fury.io/py/streprogen.svg)](https://badge.fury.io/py/streprogen)
[![Documentation Status](https://readthedocs.org/projects/streprogen/badge/?version=latest)](http://streprogen.readthedocs.io/en/latest/?badge=latest)
## Description

Sick of static `3 x 12` schemes? Streprogen (short for **Str**ength **Pro**gram **Gen**erator) is a Python package that allows you to write flexible, powerful strength training programs in no time. Streprogen is **simple to get started with** and has **sensible default values**, but advanced users can **change the underlying algorithms** easily too. The training programs **scale extremely well**, any number of days, exercises and training program durations is possible.

## Simple example

```python
from streprogen import Program, Day, DynamicExercise, StaticExercise

# Create a 4-week program with 25 repetitions per exercise
program = Program('My first program!', duration = 4, reps_per_exercise = 25)

# Create some dynamic and static exercises, add to the day
bench = DynamicExercise('Bench press', start_weight = 60, end_weight = 80)
squats = DynamicExercise('Squats', start_weight = 80, end_weight = 95)
curls = StaticExercise('Curls', '3 x 12')
day = Day(exercises = [bench, squats, curls])

# Add day(s) to program and render it
program.add_days(day)
program.render()
print(program)
```

```
----------------------------------------------------------------
Program: My first program! 

Parameters
  duration: 4
  reps_per_exercise: 25
  avg_intensity: 75
  reps_scalers: [1, 1.2, 1.2, 0.8]
  intensity_scalers: [0.95, 1, 1, 0.95]
  units: kg
----------------------------------------------------------------
Days and exercises
  Day 1
   Bench press    60kg ->  80kg   reps: [3, 8]     weekly inc.: 7.5%
   Squats         80kg ->  95kg   reps: [3, 8]     weekly inc.: 4.4%
   Curls         3 x 12           
----------------------------------------------------------------
Week 1
 Day 1
   Bench press    7 x 42.5kg  7 x 42.5kg  6 x 45kg    5 x 47.5kg  
   Squats         7 x 57.5kg  7 x 57.5kg  6 x 60kg    5 x 62.5kg  
   Curls          3 x 12

Week 2
 Day 1
   Bench press    8 x 42.5kg  7 x 45kg    6 x 50kg    5 x 52.5kg  4 x 55kg    
   Squats         8 x 55kg    7 x 57.5kg  6 x 62.5kg  5 x 65kg    4 x 70kg    
   Curls          3 x 12

Week 3
 Day 1
   Bench press    8 x 50kg    7 x 52.5kg  6 x 55kg    5 x 60kg    4 x 62.5kg  
   Squats         8 x 60kg    7 x 65kg    6 x 67.5kg  5 x 72.5kg  4 x 77.5kg  
   Curls          3 x 12


Week 4
 Day 1
   Bench press    7 x 57.5kg  7 x 57.5kg  6 x 60kg    
   Squats         7 x 67.5kg  7 x 67.5kg  6 x 70kg    
   Curls          3 x 12

----------------------------------------------------------------
```


## Project structure

Information about project structure here.

## TODO

* Write export to HTML
* Write export to LaTeX